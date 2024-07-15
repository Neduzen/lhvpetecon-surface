import ee

# Access to the landsat images. Gets the image for the area, adds bands, mask clouds.
class Satellite:
    def __init__(self):
        ee.Initialize()
        self.bandNamesLandsat = ee.List(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'pixel_qa']);

    # Computes the NDVI and adds it as a new band.
    def addNDVI(self, image):
        ndvi = image.normalizedDifference(['nir', 'red']).rename('NDVI')
        return image.addBands(ndvi)

    # Computes the NDBI (Normalized Built-up index and adds it as  a new band).
    def addNDBI(self, image):
        ndbi = image.normalizedDifference(['swir1', 'nir']).rename('NDBI')
        return image.addBands(ndbi)

    # Computes the WI (Water-Index) and adds it as a new band.
    def addNDWI(self, image):
        ndwi = image.normalizedDifference(['green', 'swir1']).rename('WI')
        return image.addBands(ndwi)

    # Masks the clouds and cloud shadows for landsat 8 images, through the tagged bits in the band pixel quality.
    # Filter more strict as there are anyway enough good pixels available.
    def maskClouds_new(self, image):
        # Bits 3 and 4 are cloud shadow and cloud, respectively.
        cloudShadowBitMask = (1 << 3)
        cloudsBitMask = (1 << 4)
        # Get the pixel_qa band.
        qa = image.select('pixel_qa')
        # Both flags should be set to zero, indicating clear conditions.
        mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0).And(qa.bitwiseAnd(cloudsBitMask).eq(0))
        return image.updateMask(mask)

    # Mask clouds and cloud shadows in Landsat 4, 5 and 7 imagery, by using the
    # corresponding pixel quality bits.
    # Do only throw away bad pixels if confidence is high due to sparse coverage of early years.
    def maskClouds(self, image):
        qa = image.select('pixel_qa')
        # If the cloud bit(3) is set and the cloud confidence(9) is high
        # or the cloud shadow bit is set(4), then it's a bad pixel.
        cloud = qa.bitwiseAnd(1 << 3).And(qa.bitwiseAnd(1 << 9)).Or(qa.bitwiseAnd(1 << 4))
        # Remove edge pixels that don't occur in all bands
        mask2 = image.mask().reduce(ee.Reducer.min())
        image = image.updateMask(cloud.Not()).updateMask(mask2)
        return image

    # Tags bad pixels which are mainly white cloudpixels or black cloud shadow pixels.
    # (But still keep the dark water and dark tree pixel). Either very bright pixels are
    # tagged or very dark pixels with a small WI and a small NDVI.
    def tagBadPixels(self, image):
        # Determine bad pixels
        badPix = image.select('brightness').lte(0.35).And(image.select('WI').lte(0.1)).And(image.select('NDVI').lte(0.8)).And(
            image.select('brightness').gte(1.0))
        image = image.addBands(badPix.rename('Bad'))

        # TODO: Switch for excluding bad pixels
        # Mask all bad pixels
        #image = image.updateMask(image.select('Bad').eq(0))

        return image

    # Adds a new band 'brightness' to the image.VIS, NIR and SWIR bands are summed up.
    def addBrightness(self, image):
        score = image.select('red').add(image.select('green')).add(image.select('blue')).add(image.select('nir')).add(
            image.select('swir1')).add(image.select('swir2'))
        return image.addBands(score.rename('brightness'))

    # Masks pixels with values out of range. (> 1 or < 0 are invalid values).
    def maskInvalidPix(self, img):
        img = img.updateMask(img.select('red').gt(0))
        img = img.updateMask(img.select('green').gt(0))
        img = img.updateMask(img.select('blue').gt(0))
        img = img.updateMask(img.select('red').lte(1))
        img = img.updateMask(img.select('green').lte(1))
        img = img.updateMask(img.select('blue').lte(1))
        img = img.updateMask(img.select('nir').gt(0))
        img = img.updateMask(img.select('swir1').gt(0))
        img = img.updateMask(img.select('swir2').gt(0))
        img = img.updateMask(img.select('nir').lte(1))
        img = img.updateMask(img.select('swir1').lte(1))
        img = img.updateMask(img.select('swir2').lte(1))
        return img

    def mapLandsat(self, image):
        bandNamesLandsatToDivide = ee.List(['blue', 'green', 'red', 'nir', 'swir1', 'swir2'])
        bandNamesLandsatNotToDivide = ee.List(['pixel_qa'])
        t = image.select(bandNamesLandsatToDivide).multiply(0.0000275).add(-0.2)
        image = image.select(bandNamesLandsatNotToDivide).addBands(t).select(self.bandNamesLandsat)
        return image

    # Depending on world latitude region, the image are loaded in different time periods.
    # For North and South spring until late autumn. For equatorial whole year.
    # In order to not include snow and leafless trees at winters.
    def GetTimePeriod(self, latitudeRegion):
        start_day = 0
        end_day = 365
        start_day2 = 365
        end_day2 = 365
        if latitudeRegion == "North":
            start_day = 60
            end_day = 334
        elif latitudeRegion == "South":
            start_day = 0
            end_day = 152
            start_day2 = 244
            end_day2 = 365
        return start_day, start_day2, end_day, end_day2

    # Gets the satellite image for the given time period and the given region and returns it.
    # This class gets the image data for the given region and for the given time period.
    # It generates indices, adds scores and filters clouds.
    # Start_year: Date from when on the yearly composites should begin.
    # End_year: Date when the yearly composites should end.
    # Region: Area to generate satelite composites from.
    def GetSatelliteImages(self, startyear, endyear, region, latitudeRegion="North"):
        # Load Landsat SR collection for the region and for the time period.
        start_Date = ee.Date.fromYMD(startyear, 1, 1)
        end_Date = ee.Date.fromYMD(endyear, 12, 31)

        # Get image time period of the year.
        start_day, start_day2, end_day, end_day2 = self.GetTimePeriod(latitudeRegion)

        # Map and get bands of different satellites by id
        sensorBandDictLandsat = ee.Dictionary({
            'L9': ee.List([1, 2, 3, 4, 5, 6, 17]),
            'L8': ee.List([1, 2, 3, 4, 5, 6, 17]),
            'L7': ee.List([0, 1, 2, 3, 4, 5, 17]),
            'L5': ee.List([0, 1, 2, 3, 4, 5, 17]),
            'L4': ee.List([0, 1, 2, 3, 4, 5, 17])
            })


        # Load Landsat 9 images
        LS9_SR = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')\
            .filterDate(start_Date, end_Date)\
            .filter(ee.Filter.Or(ee.Filter.calendarRange(start_day, end_day), ee.Filter.calendarRange(start_day2, end_day2)))\
            .filterBounds(region)\
            .filterMetadata('CLOUD_COVER', 'less_than', 50)\
            .filterMetadata('IMAGE_QUALITY_OLI', 'equals', 9)\
            .select(sensorBandDictLandsat.get('L9'), self.bandNamesLandsat)\
            .map(self.mapLandsat) \
            .map(self.maskClouds_new) \
            .map(self.maskInvalidPix) \
            .map(self.addNDVI) \
            .map(self.addNDWI) \
            .map(self.addNDBI) \
            .map(self.addBrightness) \
            .map(self.tagBadPixels)

        # Load Landsat 8 images
        LS8_SR = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')\
            .filterDate(start_Date, end_Date)\
            .filter(ee.Filter.Or(ee.Filter.calendarRange(start_day, end_day),ee.Filter.calendarRange(start_day2, end_day2)))\
            .filterBounds(region)\
            .filterMetadata('CLOUD_COVER', 'less_than', 50)\
            .filterMetadata('IMAGE_QUALITY_OLI', 'equals', 9)\
            .select(sensorBandDictLandsat.get('L8'), self.bandNamesLandsat)\
            .map(self.mapLandsat) \
            .map(self.maskClouds_new) \
            .map(self.maskInvalidPix) \
            .map(self.addNDVI) \
            .map(self.addNDWI) \
            .map(self.addNDBI) \
            .map(self.addBrightness) \
            .map(self.tagBadPixels)

        # Load Landsat 7 images
        LS7_SR = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')\
            .filterDate(start_Date, end_Date)\
            .filter(ee.Filter.Or(ee.Filter.calendarRange(start_day, end_day),ee.Filter.calendarRange(start_day2, end_day2)))\
            .filterBounds(region)\
            .filterMetadata('CLOUD_COVER', 'less_than', 50)\
            .filterMetadata('IMAGE_QUALITY', 'equals', 9)\
            .select(sensorBandDictLandsat.get('L7'), self.bandNamesLandsat)\
            .map(self.mapLandsat)\
            .map(self.maskClouds) \
            .map(self.maskInvalidPix) \
            .map(self.addNDVI) \
            .map(self.addNDWI) \
            .map(self.addNDBI) \
            .map(self.addBrightness) \
            .map(self.tagBadPixels)

        # Load Landst 5 images
        LS5_SR = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')\
            .filterDate(start_Date, end_Date)\
            .filter(ee.Filter.Or(ee.Filter.calendarRange(start_day, end_day),ee.Filter.calendarRange(start_day2, end_day2)))\
            .filterBounds(region)\
            .filterMetadata('CLOUD_COVER', 'less_than', 50)\
            .filterMetadata('IMAGE_QUALITY', 'equals', 9)\
            .select(sensorBandDictLandsat.get('L5'), self.bandNamesLandsat)\
            .map(self.mapLandsat)\
            .map(self.maskClouds) \
            .map(self.maskInvalidPix) \
            .map(self.addNDVI) \
            .map(self.addNDWI) \
            .map(self.addNDBI) \
            .map(self.addBrightness) \
            .map(self.tagBadPixels)

        # Load Landsat 4 images
        LS4_SR = ee.ImageCollection('LANDSAT/LT04/C02/T1_L2') \
            .filterDate(start_Date, end_Date) \
            .filter(ee.Filter.Or(ee.Filter.calendarRange(start_day, end_day),ee.Filter.calendarRange(start_day2, end_day2)))\
            .filterBounds(region) \
            .filterMetadata('CLOUD_COVER', 'less_than', 50) \
            .filterMetadata('IMAGE_QUALITY', 'equals', 9) \
            .select(sensorBandDictLandsat.get('L4'), self.bandNamesLandsat) \
            .map(self.mapLandsat) \
            .map(self.maskClouds) \
            .map(self.maskInvalidPix) \
            .map(self.addNDVI) \
            .map(self.addNDWI) \
            .map(self.addNDBI) \
            .map(self.addBrightness) \
            .map(self.tagBadPixels)

        # Merge all Landsat collection to one collection and return it
        ls_collection = ee.ImageCollection(LS9_SR.merge(LS8_SR).merge(LS7_SR).merge(LS5_SR).merge(LS4_SR))
        ls_collection = ls_collection.sort('system:time_start')
        return ls_collection
