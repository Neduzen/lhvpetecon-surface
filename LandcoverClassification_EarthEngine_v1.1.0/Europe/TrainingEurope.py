import ee
from ee.batch import Export
from CorineImages import Corine
from SatelliteImages import Satellite


# This class is responsible for the generation of trainings data.
class TrainingEurope:
    def __init__(self):
        ee.Initialize()

    def ProduceTrainingDataEu(self, region, trainyear, testPoints, assetName, sampleNumber, seed=0):
        return self.ProduceTrainingData(region, trainyear, testPoints, assetName, sampleNumber, '', seed)

    # Generates a satellite image of region of the given year and gets the corine landcover for this year.
    # Takes x amount of sample points for each class and exports their bands values to the asset.
    # This document can then be used from the Main program to training the classifier.
    def ProduceTrainingData(self, region, trainyear, testPoints, assetName, sampleNumber, namePart, seed=0):
        print("Corine Training of year: {} and for asset {}".format(trainyear, assetName))
        # Get the corine landcover data for the training year.
        corine = Corine().getCorineImages().clip(region.geometry())
        landcover = corine.select(ee.Number(trainyear).format("%4d")).rename('landcover')

        # Compute standard deviation (SD) of the corine classification, in order to exclude the class border,
        # because there is high probability for wrong corine class. 100 meter border region.
        texture = landcover.reduceNeighborhood(reducer=ee.Reducer.stdDev(), kernel=ee.Kernel.cross(100, "meters"))
        texture = texture.eq(0)
        texture = texture.updateMask(texture)
        landcover = landcover.updateMask(texture)

        bandNamesToTrain = ee.List(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'NDVI', 'NDBI', 'WI'])

        # Get Landsat composite for the training year.
        satellite = Satellite()
        comp = ee.ImageCollection(satellite.GetSatelliteImages(trainyear, trainyear, region))

        # Limit amount of images, otherwise exceeds the server
        print(comp.size().getInfo())
        # Limit Images randomly if more are available
        comp = ee.ImageCollection(comp.randomColumn('random', 13).sort('random').limit(460))
        print(comp.size().getInfo())

        # Calculate difference to mean brightness
        mean = comp.select('brightness').mean()

        def addMSD(img):
            return img.addBands(mean.subtract(img.select('brightness')).pow(2).multiply(-1).rename('MSD'))
        comp = comp.map(addMSD)

        # Generate greenest pixel image (Highest NDVI values).
        col = comp.qualityMosaic('NDVI')

        # Second best pixel image with least difference to mean brightness
        brightnessCol = comp.qualityMosaic('MSD')

        # If Pixel is identified as bad, get the pixel with the least difference to the mean brightness
        col = col.where(col.select('Bad').eq(1), brightnessCol)

        # Get trainingsdata of the specific year for the given points.
        trainingDataCV = col.select(bandNamesToTrain).sampleRegions(collection=testPoints, properties=['landcover'], scale=30)

        # Get trainingsdata of the specific year of a stratified sample.
        col = col.select(bandNamesToTrain).addBands(landcover).updateMask(texture)

        trainingData = col.stratifiedSample(
            numPoints=sampleNumber,
            classBand="landcover",
            region=region.geometry(),
            scale=30,
            seed=seed,
            geometries=True)

        # In order to differentiate between testing and real run. Testing has certain sample points.
        data = ee.FeatureCollection(ee.Algorithms.If(testPoints, trainingDataCV, trainingData))

        if testPoints is None:
            print("Export training data")
            # Exports the data of all necessary bands for every data point.
            name = 'train' + str(trainyear) + namePart
            task = Export.table.toAsset(
                collection=data,
                description=name,
                assetId=assetName + name)
            task.start()
            return task

        # Returns the training data
        return data
