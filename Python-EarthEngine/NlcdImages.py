import ee

class NlcdImages:
    def __init__(self):
        ee.Initialize()
    # Summarizes the corine classes to six important classes.
    def remapNlcdToLandcover(self, img, bandname):
        # 0: urban, 1: gras, 2: crops, 3: forest, 4: novegetation, 5: water, 8: unclassified
        img = img.remap(
            [11, 12, 21, 22, 23, 24, 31, 32, 41, 42, 43, 51, 52, 71, 72, 73, 74, 81, 82, 90, 95],
            [5, 4, 1, 0, 0, 0, 4, 5, 3, 3, 3, 3, 3, 1, 1, 3, 3, 1, 2, 3, 5],
            8).rename(bandname)
        img = img.updateMask(img.lte(5))
        return img

    # Loads the NLCD landcover datasets from the engine catalog, converts them to our six classes and returns it.
    def getNlcdImages(self):
        dataset = ee.ImageCollection('USGS/NLCD')

        tempdata = dataset.filter(ee.Filter.eq('system:index', 'NLCD1992')).first().select('landcover')
        landCover = self.remapNlcdToLandcover(tempdata, '1992')

        tempdata = dataset.filter(ee.Filter.eq('system:index', 'NLCD2001')).first().select('landcover')
        landCover = landCover.addBands(self.remapNlcdToLandcover(tempdata, '2001'))

        tempdata = dataset.filter(ee.Filter.eq('system:index', 'NLCD2004')).first().select('landcover')
        landCover = landCover.addBands(self.remapNlcdToLandcover(tempdata, '2004'))

        tempdata = dataset.filter(ee.Filter.eq('system:index', 'NLCD2006')).first().select('landcover')
        landCover = landCover.addBands(self.remapNlcdToLandcover(tempdata, '2006'))

        tempdata = dataset.filter(ee.Filter.eq('system:index', 'NLCD2008')).first().select('landcover')
        landCover = landCover.addBands(self.remapNlcdToLandcover(tempdata, '2008'))

        tempdata = dataset.filter(ee.Filter.eq('system:index', 'NLCD2011')).first().select('landcover')
        landCover = landCover.addBands(self.remapNlcdToLandcover(tempdata, '2011'))

        tempdata = dataset.filter(ee.Filter.eq('system:index', 'NLCD2013')).first().select('landcover')
        landCover = landCover.addBands(self.remapNlcdToLandcover(tempdata, '2013'))

        tempdata = dataset.filter(ee.Filter.eq('system:index', 'NLCD2016')).first().select('landcover')
        landCover = landCover.addBands(self.remapNlcdToLandcover(tempdata, '2016'))

        return landCover

    # Returns the nlcd landcover images of the available years.
    # Does not combine the combined classes, returns its raw values.
    def getRawNlcdImages(self):
        # Load the Corine Landcover datasets
        dataset = ee.ImageCollection('USGS/NLCD')
        landcover = dataset.filter(ee.Filter.eq('system:index', 'NLCD1992')).first().select('landcover').rename('1992')
        landcover = landcover.addBands(dataset.filter(ee.Filter.eq('system:index', 'NLCD2001')).first().select('landcover').rename('2001'))
        landcover = landcover.addBands(dataset.filter(ee.Filter.eq('system:index', 'NLCD2004')).first().select('landcover').rename('2004'))
        landcover = landcover.addBands(dataset.filter(ee.Filter.eq('system:index', 'NLCD2006')).first().select('landcover').rename('2006'))
        landcover = landcover.addBands(dataset.filter(ee.Filter.eq('system:index', 'NLCD2008')).first().select('landcover').rename('2008'))
        landcover = landcover.addBands(dataset.filter(ee.Filter.eq('system:index', 'NLCD2011')).first().select('landcover').rename('2011'))
        landcover = landcover.addBands(dataset.filter(ee.Filter.eq('system:index', 'NLCD2013')).first().select('landcover').rename('2013'))
        landcover = landcover.addBands(dataset.filter(ee.Filter.eq('system:index', 'NLCD2016')).first().select('landcover').rename('2016'))
        return landcover


