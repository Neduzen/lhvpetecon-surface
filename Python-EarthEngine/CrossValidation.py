# The CrossValidation Script generates 5 subsets for all five years of corine data
# (1990, 2000, 2006, 2012, 2018). For every year 4 of the subsets are used to train the classifier and
# 1 for validation. This is executed 5 times, so that every subset is once a validation subset.
# The results of the cross validation are exported as csv file to the google drive in the "crossValidation" folder.
import ee
from ee.batch import Export

from CorineImages import Corine
from Training import Training
from Classify import Classify
from SatelliteImages import Satellite


class CrossValidation:
    def __init__(self, country):
        self.country = country

    # Generates a stratified sample of the corine classes of the year with the given seed.
    def getStratifiedSample(self, img, year, seed):
        samplePoints = img.select(ee.Number(year).format("%4d")).rename('landcover').stratifiedSample(
            numPoints=250,
            classBand="landcover",
            region=self.country.GetFeature().geometry(),
            scale=30,
            seed=seed,
            geometries=True
        ).set('year', year)
        return samplePoints

    # Get 250 random samples for each class for each year based on corine landcover.
    def generateSubset(self, subset):
        samplePoints1990 = self.getStratifiedSample(self.corineImages, 1990, 1 + subset)
        samplePoints2000 = self.getStratifiedSample(self.corineImages, 2000, 2 + subset)
        samplePoints2006 = self.getStratifiedSample(self.corineImages, 2006, 3 + subset)
        samplePoints2012 = self.getStratifiedSample(self.corineImages, 2012, 4 + subset)
        samplePoints2018 = self.getStratifiedSample(self.corineImages, 2018, 5 + subset)
        return ee.List([samplePoints1990, samplePoints2000, samplePoints2006, samplePoints2012, samplePoints2018])

    # Gets the generated samples for the given year.
    def getTrainingSampleOfYear(self, s1, s2, s3, s4, year):
        index = self.years.indexOf(year)
        sample = ee.FeatureCollection(s1.get(index)).merge(s2.get(index)).merge(s3.get(index)).merge(s4.get(index))
        return sample

    # Validates the classification for the five reference years
    def validateClassifiedYear(self, valSub, img, year, run):
        img = ee.ImageCollection(img).filterBounds(self.country.GetFeature())
        yearString = ee.Number(year).format("%4d")
        # Get correct corine and classified image
        valImg = img.filterMetadata('year', 'equals', year).first().select('classified')
        valImg = valImg.addBands(self.corineImages.select(yearString))
        # Check corine and our classification for the given validation subset
        samples = ee.FeatureCollection(valSub.get(self.years.indexOf(year)))

        validation = valImg.select([yearString, 'classified']).sampleRegions(
            tileScale = 1,
            # projection: 'EPSG:3665',
            scale = 30,
            collection = samples  # .geometry()
        )
        # Generate error matrix
        errorMatrix = validation.errorMatrix("classified", yearString)
        exportAccuracy = ee.Feature(None, ee.Dictionary
            ({
            'overallacc': errorMatrix.accuracy(),
            'kappa': errorMatrix.kappa(),
            'matrix': errorMatrix.array(),
            'year': year
        }))

        # Export year accuracy of classification
        filename = 'crossVal' + str(year) + "-subset" + str(run)
        foldername = self.country.GetName() + "-CrossValidation"
        task = Export.table.toDrive(
            collection= ee.FeatureCollection([exportAccuracy]),
            description= filename,
            folder= foldername,
            fileFormat= 'CSV'
        )
        task.start()

    # Does a validation round with 1 validation sample and 4 training samples.
    def subsetValidation(self, valSub, trainSub1, trainSub2, trainSub3, trainSub4, run):
        # Combine subsets for each training year
        if self.country.hasAllCorine():
            trainingPoints1990 = self.getTrainingSampleOfYear(trainSub1, trainSub2, trainSub3, trainSub4, 1990)
        trainingPoints2000 = self.getTrainingSampleOfYear(trainSub1, trainSub2, trainSub3, trainSub4, 2000)
        trainingPoints2006 = self.getTrainingSampleOfYear(trainSub1, trainSub2, trainSub3, trainSub4, 2006)
        trainingPoints2012 = self.getTrainingSampleOfYear(trainSub1, trainSub2, trainSub3, trainSub4, 2012)
        trainingPoints2018 = self.getTrainingSampleOfYear(trainSub1, trainSub2, trainSub3, trainSub4, 2018)
        # Create training data for each year
        if self.country.hasAllCorine():
            train1990 = self.trainingCorine.ProduceTrainingDataEu(self.country.GetFeature(), 1990, trainingPoints1990, None, 0)
        train2000 = self.trainingCorine.ProduceTrainingDataEu(self.country.GetFeature(), 2000, trainingPoints2000, None, 0)
        train2006 = self.trainingCorine.ProduceTrainingDataEu(self.country.GetFeature(), 2006, trainingPoints2006, None, 0)
        train2012 = self.trainingCorine.ProduceTrainingDataEu(self.country.GetFeature(), 2012, trainingPoints2012, None, 0)
        train2018 = self.trainingCorine.ProduceTrainingDataEu(self.country.GetFeature(), 2018, trainingPoints2018, None, 0)
        # Merge training data
        trainAll = train2018.merge(train2012).merge(train2006).merge(train2000)
        if self.country.hasAllCorine():
            trainAll = trainAll.merge(train1990)
        bandNamesToTrain = ee.List(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'NDVI', 'NDBI', 'WI'])
        # Create classifier from all years of training data
        classifierCorine = ee.Classifier.smileRandomForest(10).train(trainAll, 'landcover', bandNamesToTrain)
        # Classify satelite data per year based on the classifier
        if self.country.hasAllCorine():
            points = ee.FeatureCollection(valSub.get(self.years.indexOf(1990)))
            result1990 = self.classify.DoClassification(points, classifierCorine, 90, "CrossVall",
                                  1990, 1990, self.country.GetName(), False)
        points = ee.FeatureCollection(valSub.get(self.years.indexOf(2000)))
        result2000 = self.classify.DoClassification(points, classifierCorine, 91, "CrossVall",
                                  2000, 2000, self.country.GetName(), False)
        points = ee.FeatureCollection(valSub.get(self.years.indexOf(2006)))
        result2006 = self.classify.DoClassification(points, classifierCorine, 92, "CrossVall",
                                  2006, 2006, self.country.GetName(), False)
        points = ee.FeatureCollection(valSub.get(self.years.indexOf(2012)))
        result2012 = self.classify.DoClassification(points, classifierCorine, 93, "CrossVall",
                                  2012, 2012, self.country.GetName(), False)
        points = ee.FeatureCollection(valSub.get(self.years.indexOf(2018)))
        result2018 = self.classify.DoClassification(points, classifierCorine, 94, "CrossVall",
                                  2018, 2018, self.country.GetName(), False)
        # Validate the classification with the validation subset
        if self.country.hasAllCorine():
            self.validateClassifiedYear(valSub, result1990, 1990, run)
        self.validateClassifiedYear(valSub, result2000, 2000, run)
        self.validateClassifiedYear(valSub, result2006, 2006, run)
        self.validateClassifiedYear(valSub, result2012, 2012, run)
        self.validateClassifiedYear(valSub, result2018, 2018, run)

    # Runs the cross validation
    def RunCrossValidation(self):
        # Define variables
        print("Cross Validation")
        self.years = ee.List([1990, 2000, 2006, 2012, 2018])
        self.trainingCorine = Training()
        self.classify = Classify()
        self.corineImages = Corine().getCorineImages()

        # Get five subsets for cross-validation
        subset1 = self.generateSubset(1)
        subset2 = self.generateSubset(2)
        subset3 = self.generateSubset(3)
        subset4 = self.generateSubset(4)
        subset5 = self.generateSubset(5)

        # Run 5 times validation. Each one with a different validation set and the other four for training data
        self.subsetValidation(subset1, subset2, subset3, subset4, subset5, 1)
        self.subsetValidation(subset2, subset1, subset3, subset4, subset5, 2)
        self.subsetValidation(subset3, subset2, subset1, subset4, subset5, 3)
        self.subsetValidation(subset4, subset2, subset3, subset1, subset5, 4)
        self.subsetValidation(subset5, subset2, subset3, subset4, subset1, 5)

        print('End CrossValidation')