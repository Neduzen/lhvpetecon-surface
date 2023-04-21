# Classifies the given regions into the landcover classes adapted from corine.
# region: FeatureCollection, where landcover should be classified.
# classifier: Trained classifier to use for landcover classification.
# number: Run number of current execution.
# id_name: Name of the unique property of the FeatureCollection, in order to define the export table.
# star_year: First year to classify.
# end_year: Last year to classify.
import ee
from ee.batch import Export
from SatelliteImages import Satellite


# Generates a classified image of a given area for all years.
class Classify:
    def __init__(self):
        ee.Initialize()

    # Runs the classification
    def DoClassification(self, features, classifier, number, id_name, start_year, end_year, countryName, doExport, latitudeRegion="North"):
        print("Classification of country: {} and for asset {}".format(countryName, number))
        bandNamesClassify = ee.List(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'NDVI', 'NDBI', 'WI'])
        years = ee.List.sequence(start_year, end_year, 1)

        # Load Landsat SR collection for the given features from start to end date
        satellite = Satellite()
        ls_collection = ee.ImageCollection(satellite.GetSatelliteImages(start_year, end_year, features, latitudeRegion))
        # Calculate greenest Pixel (highest NDVI) for the yearly composites
        def ndviComposite(y):
            start = ee.Date.fromYMD(y, 1, 1)
            stop = ee.Date.fromYMD(y, 12, 31)
            # Limit amount of images, otherwise exceeds the server
            col = ls_collection.filterDate(start, stop) \
                .sort('CLOUD_COVER_LAND').limit(75) \
                .qualityMosaic('NDVI') \
                .set({'system:time_start': start.millis(), 'year': y})
            bandnames = col.bandNames()
            col = col.set({'num_bands': bandnames.size()})
            col = col.set({'count': ls_collection.filterDate(start, stop).size()})
            col = col.addBands(ee.Image(0).rename('MSD'))
            return col
        # NDVI composite.
        coll_year = ee.ImageCollection(years.map(ndviComposite).flatten()).filterMetadata('num_bands', 'greater_than', 0)

        # Generate a composite from the smallest difference to the medium brighness per pixel (no clouds, no shadows) for the yearly composites.
        def cloudFreeComposite(y):
            start = ee.Date.fromYMD(y, 1, 1)
            stop = ee.Date.fromYMD(y, 12, 31)
            col = ls_collection.filterDate(start, stop).sort('CLOUD_COVER_LAND').limit(75) # Limit amount of images, otherwise exceeds the server
            mean = col.select('brightness').mean()
            def addBrighnessDifference(img):
                # Add new band to the image, which is the negative squared difference from the mean of the brighness band
                return img.addBands(mean.subtract(img.select('brightness')).pow(2).multiply(-1).rename('MSD'))
            col = col.map(addBrighnessDifference)
            # Mosaic of the composite from the mean standard difference band
            col = col.qualityMosaic('MSD').set({'system:time_start': start.millis(), 'year': y})
            bandnames = col.bandNames()
            col = col.set({'num_bands': bandnames.size()})
            return col
        # Cloudfree composite.
        coll_year_cloudfree = ee.ImageCollection(years.map(cloudFreeComposite).flatten()).filterMetadata('num_bands', 'greater_than', 0);

        # Creates the best composite for all pixels of all years.
        # If the NDVI Pixel is identified as potential cloud oder cloud shadow pixel, then cloudfree pixel is taken.
        def bestPixelComposite(img):
            year = img.get('year')
            # Get less cloudiest pixel (smallest deviation from mean brightness), if the pixel is identified as bad.
            img = img.where(img.select('Bad').eq(1), coll_year_cloudfree.filter(ee.Filter.eq('year', year)).first())
            return img
        # Best Pixel composite
        coll_year = coll_year.map(bestPixelComposite)

        # Classifies the satellite image of the best pixel composite into landcover classes.
        def classifyImages(img):
            # Classifies the satellite images with the corine classifier.
            classifiedCorine = img.select(bandNamesClassify).classify(classifier).rename('classified')
            # Cloudfree mask
            all = classifiedCorine.lte(7)
            all = all.set({'year': img.get('year')})
            all = all.set({'system:time_start': img.get('system:time_start')})
            all = all.updateMask(all).rename("cloudfree")
            # Total pixel area mask
            all = all.addBands(ee.Image(1).rename('totalPixel'))
            # Generate masked bands per landcover
            all = all.addBands(classifiedCorine.eq(0).rename('urban'))
            all = all.addBands(classifiedCorine.eq(1).rename('gras'))
            all = all.addBands(classifiedCorine.eq(2).rename('crops'))
            all = all.addBands(classifiedCorine.eq(3).rename('forest'))
            all = all.addBands(classifiedCorine.eq(4).rename('noveg'))
            all = all.addBands(classifiedCorine.eq(5).rename('water'))
            # Add classification in one band
            all = all.addBands(classifiedCorine)
            return all
        # Classified composite
        coll_year_class = coll_year.map(classifyImages)

        # Returns the classified imagecollection.
        return coll_year_class


