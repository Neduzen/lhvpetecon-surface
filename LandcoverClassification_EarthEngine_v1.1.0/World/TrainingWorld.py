import ee
import random
from ee.batch import Export
from CorineImages import Corine
from SatelliteImages import Satellite


# Creates the training data for a given region (country).
class TrainingWorld:
    def __init__(self):
        ee.Initialize()

    # Generates a satellite image of region of the given year and gets the corine landcover for this year.
    # Generates 1000 sample points for each class divide into the percentage of the climate classes
    # and exports their bands values to a csv document.
    # This document can then be used from the Main program to training the classifier.
    def ProduceTrainingDataClimate(self, year, testPoints, assetName, b_perc, c_perc, d_perc, e_perc, imageLimit, trainingAssets):
        # Total 1000, divide into categories based on input percentage
        b1co = ee.FeatureCollection('users/emap1/climateShapeB1-eu')
        b2co = ee.FeatureCollection('users/emap1/climateShapeB2-eu')
        b3co = ee.FeatureCollection('users/emap1/climateShapeB3-eu')
        c1co = ee.FeatureCollection('users/emap1/climateShapeC1-eu')
        c2co = ee.FeatureCollection('users/emap1/climateShapeC2-eu')
        c3co = ee.FeatureCollection('users/emap1/climateShapeC3-eu')
        c4co1 = ee.FeatureCollection('users/emap1/climateShapeC4_1-eu')
        c4co2 = ee.FeatureCollection('users/emap1/climateShapeC4_1-eu')
        c5co1 = ee.FeatureCollection('users/emap1/climateShapeC5_1-eu')
        c5co2 = ee.FeatureCollection('users/emap1/climateShapeC5_2-eu')
        d1co = ee.FeatureCollection('users/emap1/climateShapeD1-eu')
        d2co = ee.FeatureCollection('users/emap1/climateShapeD2-eu')
        d3co = ee.FeatureCollection('users/emap1/climateShapeD3-eu')
        d4co = ee.FeatureCollection('users/emap1/climateShapeD4-eu')
        d5co1 = ee.FeatureCollection('users/emap1/climateShapeD5_1-eu')
        d5co2 = ee.FeatureCollection('users/emap1/climateShapeD5_2-eu')
        e1co = ee.FeatureCollection('users/emap1/climateShapeE1-eu')
        e2co = ee.FeatureCollection('users/emap1/climateShapeE2-eu')
        e3co = ee.FeatureCollection('users/emap1/climateShapeE3-eu')

        trainingAssetsNames = []
        for a in trainingAssets["assets"]:
            trainingAssetsNames.append(a["id"])

        # Exports the training data to GEE.
        def exportAsset(year, data, nameExtension):
            name = 'train' + str(year) + nameExtension
            assetId = assetName + "Training/" + name
            if testPoints is None and assetId not in trainingAssetsNames:
                print("Export asset: " + assetId)
                # Exports the data of all necessary bands for every data point.
                task = Export.table.toAsset(
                    collection=data,
                    description=name,
                    assetId=assetId)
                task.start()
                return task

        # Determines the amount of sample points per climate class based on the climate zone area distribution.
        def defineNumberOfPoints(b, c, d, e):
            b_tot = b[0]+b[1]+b[2]
            c_tot = c[0]+c[1]+c[2]+c[3]+c[4]+c[5]+c[6]
            d_tot = d[0]+d[1]+d[2]+d[3]+d[4]+d[5]
            e_tot = e[0]+e[1]+e[2]

            pointsClass = 1000
            bs = []
            cs = []
            ds = []
            es = []
            for be in b:
                bs.append(round(be / b_tot * b_perc * pointsClass))
            for ce in c:
                cs.append(round(ce / c_tot * c_perc * pointsClass))
            for de in d:
                ds.append(round(de / d_tot * d_perc * pointsClass))
            for en in e:
                es.append(round(en / e_tot * e_perc * pointsClass))

            b = bs[0]+bs[1]+bs[2]
            c = cs[0]+cs[1]+cs[2]+cs[3]+cs[4]+cs[5]+cs[6]
            d = ds[0]+ds[1]+ds[2]+ds[3]+ds[4]+ds[5]
            e = es[0]+es[1]+es[2]
            tot = b + c + d + e

            difference = 1
            if tot == 1002 or tot == 998:
                difference = 2
            if tot > 1000:
                if e_perc > b_perc and e_perc > c_perc and e_perc > d_perc:
                    es[0] -= difference
                elif b_perc > c_perc and b_perc > d_perc and b_perc > e_perc:
                    bs[0] -= difference
                elif c_perc > b_perc and c_perc > d_perc and c_perc > e_perc:
                    cs[0] -= difference
                elif d_perc > c_perc and d_perc > b_perc and d_perc > e_perc:
                    ds[0] -= difference
            elif tot < 1000:
                if e_perc > b_perc and e_perc > c_perc and e_perc > d_perc:
                    es[0] += difference
                elif b_perc > c_perc and b_perc > d_perc and b_perc > e_perc:
                    bs[0] += difference
                elif c_perc > b_perc and c_perc > d_perc and c_perc > e_perc:
                    cs[0] += difference
                elif d_perc > c_perc and d_perc > b_perc and d_perc > e_perc:
                    ds[0] += difference

            b = bs[0]+bs[1]+bs[2]
            c = cs[0]+cs[1]+cs[2]+cs[3]+cs[4]+cs[5]+cs[6]
            d = ds[0]+ds[1]+ds[2]+ds[3]+ds[4]+ds[5]
            e = es[0]+es[1]+es[2]
            tot = b + c + d + e
            if tot != 1000:
                print("Wrong amount of training points: {}, expected 1000".format(tot))
            print("Training points b: {}".format(bs))
            print("Training points c: {}".format(cs))
            print("Training points d: {}".format(ds))
            print("Training points e: {}".format(es))
            return bs,cs,ds,es

        # Corine landcover (2000, 2006, 2012, 2018) cells divided into climate zones.
        # B: 498k, C: 2123k,  D: 2917k, E: 218k.
        # List shows the divide number (as the area had to be split to not get computation overflow)
        b = [86, 227, 185]
        c = [318, 586, 424, 194, 130, 249, 222]
        d = [387, 1065, 736, 424, 193, 112]
        e = [95, 91, 32]
        if year == 1990:
            # Not all countries had already 1990 corine coverage, thus, different climate number for the year of 1990
            # only e1, d2 not, d3-60k, d1-25k, c1 (only ireland) 74k instead of 318, c3-29k
            b = [86, 227, 185]
            c = [74, 586, 395, 194, 130, 249, 222]
            d = [362, 0, 676, 424, 193, 112]
            e = [0, 0, 32]
        # Calculate the number of training points per climate zones based on the countries climate zones.
        bs, cs, ds, es = defineNumberOfPoints(b, c, d, e)

        # Generates the training data for a given climate zone of a subset shape feature.
        def runSubClass(region, number, name, data):
            if number > 0:
                # Run training data for the climate area of a specific year
                data1 = self.RunTrainingDataClimate(region, year, testPoints, assetName, number, imageLimit)
                exportAsset(year, data1, "-"+name)
                if data is None and testPoints is None:
                    data = data1
                else:
                    data = data.merge(data1)
            return data

        # Run all training data
        data = runSubClass(b1co, bs[0], "b1", None)
        data = runSubClass(b2co, bs[1], "b2", data)
        data = runSubClass(b3co, bs[2], "b3", data)
        data = runSubClass(c1co, cs[0], "c1", data)
        data = runSubClass(c2co, cs[1], "c2", data)
        data = runSubClass(c3co, cs[2], "c3", data)
        data = runSubClass(c4co1, cs[3], "c4_1", data)
        data = runSubClass(c4co2, cs[4], "c4_2", data)
        data = runSubClass(c5co1, cs[5], "c5_1", data)
        data = runSubClass(c5co2, cs[6], "c5_2", data)
        data = runSubClass(d1co, ds[0], "d1", data)
        data = runSubClass(d2co, ds[1], "d2", data)
        data = runSubClass(d3co, ds[2], "d3", data)
        data = runSubClass(d4co, ds[3], "d4", data)
        data = runSubClass(d5co1, ds[4], "d5_1", data)
        data = runSubClass(d5co2, ds[5], "d5_2", data)
        data = runSubClass(e1co, es[0], "e1", data)
        data = runSubClass(e2co, es[1], "e2", data)
        data = runSubClass(e3co, es[2], "e3", data)

        return data

    # Generates the training data of a climate subarea for a specific year with the defined number of sample points.
    def RunTrainingDataClimate(self, region, trainyear, testPoints, assetName, sampleNumber, imageLimit):
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
        totalSize = comp.size().getInfo()
        def orderColumn(img):
            img = img.set("orderRC", ee.Number(img.get('CLOUD_COVER_LAND')).multiply(random.random()))
            return img
        comp = comp.map(orderColumn)

        # Limit the number of images to avoid computation error
        comp = comp.sort('orderRC').limit(imageLimit)
        print("total size {} limit to {}".format(totalSize, comp.size().getInfo()))

        # Calculate difference to mean brightness
        mean = comp.select('brightness').mean()
        def addMSD(img):
            return img.addBands(mean.subtract(img.select('brightness')).pow(2).multiply(-1).rename('MSD'))
        comp = comp.map(addMSD)

        # Generate greenest pixel image (Highest NDVI values).
        col = comp.qualityMosaic('NDVI')

        # Second best pixel image with least difference to mean brightness
        brightnessCol = comp.qualityMosaic('MSD')

        # If a pixel is identified as bad, get the pixel with the least difference to the mean brightness
        col = col.where(col.select('Bad').eq(1), brightnessCol)

        # Get training data of the specific year for the given points.
        trainingDataCV = col.select(bandNamesToTrain).sampleRegions(collection=testPoints, properties=['landcover'], scale=30)

        # Get training data of the specific year of a stratified sample.
        col = col.select(bandNamesToTrain).addBands(landcover).updateMask(texture)

        # Generate a stratified sample with a given number of datapoints per classification category.
        trainingData = col.stratifiedSample(
            numPoints=sampleNumber,
            classBand="landcover",
            region=region.geometry(),
            scale=30,
            seed=0,
            geometries=True)

        # In order to differentiate between testing and real run. Testing has certain sample points.
        data = ee.FeatureCollection(ee.Algorithms.If(testPoints, trainingDataCV, trainingData))

        # Returns the training data
        return data