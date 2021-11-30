# The CrossValidation Script generates 5 subsets for all five years of corine data
# (1990, 2000, 2006, 2012, 2018). For every year 4 of the subsets are used to train the classifier and
# 1 for validation. This is executed 5 times, so that every subset is once a validation subset.
# The results of the cross validation are exported as csv file to the google drive in the "crossValidation" folder.
import ee
from ee.batch import Export

from NlcdImages import NlcdImages
from CorineImages import Corine
from Training import Training
from Classify import Classify
from SatelliteImages import Satellite


class CrossValidationUSA:
    def __init__(self, state):
        self.state = state

    # Generates a stratified sample of the corine classes of the year with the given seed.
    def getStratifiedSample(self, img, year, seed):
        img= img.select(["landcover", "classified"])
        samplePoints = img.stratifiedSample(
            numPoints=1000,
            classBand="landcover",
            region=self.state.GetFeature().geometry(),
            scale=30,
            seed=seed,
            geometries=True
        ).set('year', year)
        return samplePoints

    # Gets the generated samples for the given year.
    def getTrainingSampleOfYear(self, s1, s2, s3, s4, year):
        index = self.years.indexOf(year)
        sample = ee.FeatureCollection(s1.get(index)).merge(s2.get(index)).merge(s3.get(index)).merge(s4.get(index))
        return sample

    # Validates the classification for the five reference years
    def validateClassifiedYear(self, validation, img, year, run):
        yearString = ee.Number(year).format("%4d")
        # Get correct corine and classified image
        # valImg = img.filterMetadata('year', 'equals', year).first().select('classified')
        # valImg = valImg.addBands(self.corineImages.select(yearString))
        # Check corine and our classification for the given validation subset
        # samples = ee.FeatureCollection(valSub.get(self.years.indexOf(year)))

        # validation = valImg.select([yearString, 'classified']).sampleRegions(
        #     tileScale = 1,
        #     # projection: 'EPSG:3665',
        #     scale = 30,
        #     collection = samples  # .geometry()
        # )
        # Generate error matrix
        errorMatrix = validation.errorMatrix("classified", "landcover")
        # print(errorMatrix.getInfo())
        exportAccuracy = ee.Feature(None, ee.Dictionary
            ({
            'overallacc': errorMatrix.accuracy(),
            'kappa': errorMatrix.kappa(),
            'matrix': errorMatrix.array(),
            'year': year
        }))

        # Export year accuracy of classification
        filename = 'crossVal' + str(year)
        foldername = self.state.GetName() + "-CrossValidation"
        task = Export.table.toDrive(
            collection=ee.FeatureCollection([exportAccuracy]),
            description=filename,
            folder=foldername,
            fileFormat='CSV')
        task.start()

    def crossValRaw(self, result, year, run):
        rawValImg = self.rawNlcdImages.select(ee.Number(year).format("%4d")).rename("landcover")
        rawValImg = rawValImg.addBands(result.filterMetadata('year', 'equals', year).first().select('classified'))
        rawPoints = self.getStratifiedSample(rawValImg, year, run)

        errorMatrix = rawPoints.errorMatrix("classified", "landcover")
        # print(errorMatrix.getInfo())
        exportAccuracy = ee.Feature(None, ee.Dictionary
            ({
            'matrix': errorMatrix.array(),
            }))

        # Export year accuracy of classification
        filename = 'crossVal' + str(year) + '-' + str(run)
        foldername = self.state.GetName() + "-CrossValidationRaw"
        task = Export.table.toDrive(
            collection=ee.FeatureCollection([exportAccuracy]),
            description=filename,
            folder=foldername,
            fileFormat='CSV'
        )
        task.start()


    def validateYear(self, classifier, year, run):
        # print("Classifier: {}".format(classifier.getInfo()))
        validationImage = self.nlcdImages.select(ee.Number(year).format("%4d")).rename("landcover")
        result = self.classify.DoClassification(self.state.GetFeature(), classifier, run, "CrossVall",
                                                    year, year, self.state.GetName(), False)

        validationImage = validationImage.addBands(result.filterMetadata('year', 'equals', year).first().select('classified'))
        # print(result.getInfo())

        # print(validationImage.getInfo())

        points = self.getStratifiedSample(validationImage, year, run)

        # print(points.size().getInfo())
        # print(points.limit(2).getInfo())

        self.validateClassifiedYear(points, result, year, run)

        #self.crossValRaw(result, year, run)



    # Does a validation round with 1 validation sample and 4 training samples.
    def subsetValidation(self, valSub, classifier, run):
        # Combine subsets for each training year
        # trainingPoints1990 = self.getTrainingSampleOfYear(trainSub1, trainSub2, trainSub3, trainSub4, 1990)
        # trainingPoints2000 = self.getTrainingSampleOfYear(trainSub1, trainSub2, trainSub3, trainSub4, 2000)
        # trainingPoints2006 = self.getTrainingSampleOfYear(trainSub1, trainSub2, trainSub3, trainSub4, 2006)
        # trainingPoints2012 = self.getTrainingSampleOfYear(trainSub1, trainSub2, trainSub3, trainSub4, 2012)
        # trainingPoints2018 = self.getTrainingSampleOfYear(trainSub1, trainSub2, trainSub3, trainSub4, 2018)
        # # Create training data for each year
        # train1990 = self.trainingCorine.ProduceTrainingData(self.country.GetFeature(), 1990, trainingPoints1990, None, 0)
        # train2000 = self.trainingCorine.ProduceTrainingData(self.country.GetFeature(), 2000, trainingPoints2000, None, 0)
        # train2006 = self.trainingCorine.ProduceTrainingData(self.country.GetFeature(), 2006, trainingPoints2006, None, 0)
        # train2012 = self.trainingCorine.ProduceTrainingData(self.country.GetFeature(), 2012, trainingPoints2012, None, 0)
        # train2018 = self.trainingCorine.ProduceTrainingData(self.country.GetFeature(), 2018, trainingPoints2018, None, 0)
        # # Merge training data
        # trainAll = train2018.merge(train2012).merge(train2006).merge(train2000).merge(train1990)
        # bandNamesToTrain = ee.List(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'NDVI', 'NDBI', 'WI'])
        # Create classifier from all years of training data
        #classifierCorine = ee.Classifier.randomForest(10).train(trainAll, 'landcover', bandNamesToTrain)
        # Classify satelite data per year based on the classifier


        # points = ee.FeatureCollection(valSub.get(self.years.indexOf(2001)))
        # result1990 = self.classify.DoClassification(points, classifier, 90, "CrossVall",
        #                           2001, 2001, self.state.GetName(), False)
        # points = ee.FeatureCollection(valSub.get(self.years.indexOf(2000)))
        # result2000 = self.classify.DoClassification(points, classifier, 91, "CrossVall",
        #                           2004, 2004, self.state.GetName(), False)
        # points = ee.FeatureCollection(valSub.get(self.years.indexOf(2006)))
        # result2006 = self.classify.DoClassification(points, classifier, 92, "CrossVall",
        #                           2006, 2006, self.state.GetName(), False)
        # points = ee.FeatureCollection(valSub.get(self.years.indexOf(2008)))
        # result2012 = self.classify.DoClassification(points, classifier, 93, "CrossVall",
        #                           2008, 2008, self.state.GetName(), False)
        # points = ee.FeatureCollection(valSub.get(self.years.indexOf(2011)))
        # result2018 = self.classify.DoClassification(points, classifier, 94, "CrossVall",
        #                           2011, 2011, self.state.GetName(), False)
        # # Validate the classification with the validation subset
        # self.validateClassifiedYear(valSub, result1990, 2001, run)
        # self.validateClassifiedYear(valSub, result2000, 2004, run)
        # self.validateClassifiedYear(valSub, result2006, 2006, run)
        # self.validateClassifiedYear(valSub, result2012, 2008, run)
        # self.validateClassifiedYear
        self.validateYear(classifier, 1992, run)
        self.validateYear(classifier, 2001, run)
        self.validateYear(classifier, 2004, run)
        self.validateYear(classifier, 2006, run)
        self.validateYear(classifier, 2008, run)
        self.validateYear(classifier, 2011, run)
        self.validateYear(classifier, 2013, run)
        self.validateYear(classifier, 2016, run)


    # Runs the cross validation
    def RunCrossValidation(self, classifiers):
        # Define variables
        print("Cross Validation")
        self.years = ee.List([1990, 2000, 2006, 2012, 2018])
        self.trainingCorine = Training()
        self.classify = Classify()
        self.corineImages = Corine().getCorineImages()
        self.nlcdImages = NlcdImages().getNlcdImages()
        self.rawNlcdImages = NlcdImages().getRawNlcdImages()


        # Get five states
        # subset1 = self.generateSubset(1)
        # subset2 = self.generateSubset(2)
        # subset3 = self.generateSubset(3)
        # subset4 = self.generateSubset(4)
        # subset5 = self.generateSubset(5)

        # Run 5 times validation. Each one with a different validation set and the other four for training data
        self.subsetValidation(None, classifiers[0], 1)
        self.subsetValidation(None, classifiers[1], 2)
        self.subsetValidation(None, classifiers[2], 3)
        self.subsetValidation(None, classifiers[3], 4)
        self.subsetValidation(None, classifiers[4], 5)
        # self.subsetValidation(subset2, subset1, subset3, subset4, subset5, 2)
        # self.subsetValidation(subset3, subset2, subset1, subset4, subset5, 3)
        # self.subsetValidation(subset4, subset2, subset3, subset1, subset5, 4)
        # self.subsetValidation(subset5, subset2, subset3, subset4, subset1, 5)

        print('End CrossValidation')