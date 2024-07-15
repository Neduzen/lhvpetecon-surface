import ee

class Corine:
    def __init__(self):
        ee.Initialize()
    # Summarizes the corine classes to six important classes.
    def remapCorineToLandcover(self, img, bandname):
        # 0: urban, 1: gras, 2: crops, 3: forest, 4: novegetation, 5: water, 8: unclassified
        img = img.remap(
            [111, 112, 121, 122, 123, 124, 131, 132, 133, 141, 142, 211, 212, 213, 221, 222, 223, 231, 241, 242, 243, 244,
             311, 312, 313, 321, 322, 323, 324, 331, 332, 333, 334, 335, 411, 412, 421, 422, 423, 511, 512, 521, 522, 523,
             999, 990, 995],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 3, 3, 3, 1, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5,
             5, 5, 5, 5, 5, 5, 5, 8, 8, 5],
            8).rename(bandname);
        img = img.updateMask(img.lte(5));
        return img

    # Loads the corine landcover datasets from the engine catalog, converts them to our six classes and returns it.
    def getCorineImages(self):
        dataset = ee.Image('COPERNICUS/CORINE/V20/100m/1990').select('landcover').rename('1990');
        landCover = self.remapCorineToLandcover(dataset, '1990');
        dataset = ee.Image('COPERNICUS/CORINE/V20/100m/2000').select('landcover').rename('2000');
        landCover = landCover.addBands(self.remapCorineToLandcover(dataset, '2000'));
        dataset = ee.Image('COPERNICUS/CORINE/V20/100m/2006').select('landcover').rename('2006');
        landCover = landCover.addBands(self.remapCorineToLandcover(dataset, '2006'));
        dataset = ee.Image('COPERNICUS/CORINE/V20/100m/2012').select('landcover').rename('2012');
        landCover = landCover.addBands(self.remapCorineToLandcover(dataset, '2012'));
        dataset = ee.Image('COPERNICUS/CORINE/V20/100m/2018').select('landcover').rename('2018');
        landCover = landCover.addBands(self.remapCorineToLandcover(dataset, '2018'));
        return landCover

    # Returns the corine landcover images of the years 1990, 2000, 2006, 2012 and 2018.
    # Does not combine the corine classes, returns its raw values.
    def getRawCorineImages(self):
        # Load the Corine Landcover datasets
        dataset = ee.Image('COPERNICUS/CORINE/V20/100m/1990');
        landCover = dataset.select('landcover').rename('1990');
        dataset = ee.Image('COPERNICUS/CORINE/V20/100m/2000');
        landCover = landCover.addBands(dataset.select('landcover').rename('2000'));
        dataset = ee.Image('COPERNICUS/CORINE/V20/100m/2006');
        landCover = landCover.addBands(dataset.select('landcover').rename('2006'));
        dataset = ee.Image('COPERNICUS/CORINE/V20/100m/2012');
        landCover = landCover.addBands(dataset.select('landcover').rename('2012'));
        dataset = ee.Image('COPERNICUS/CORINE/V20/100m/2018');
        landCover = landCover.addBands(dataset.select('landcover').rename('2018'));
        return landCover
