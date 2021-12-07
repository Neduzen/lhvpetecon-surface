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


class Classify:
    def __init__(self):
        ee.Initialize()

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

        # Function to calculate the area for a specific landcover (0/1 mask) for each feature
        def calculateArea(image, features):
            year = ee.Number(image.get("year")).format("%4d")
            image = image.updateMask(image)

            areaOfFeature = image.reduceRegions(collection=features, reducer=ee.Reducer.count(), scale=30, tileScale=1)
            def countPixel(feat):
                feat = feat.set("count", ee.String(feat.get("count")))
                return ee.Feature(None, feat.set("year", year).toDictionary())
            return areaOfFeature.map(countPixel)

        # Format a table of triplets into a 2D table of rowId x colId.
        # Features need to be reorganized in order to do a proper output.
        def format(table, rowId, colId, propertyName):
            # Get a FeatureCollection with unique row IDs.
            rows = table.distinct(rowId);
            # Join the table to the unique IDs to get a collection in which
            # each feature stores a list of all features having a common row ID.
            joined = ee.Join.saveAll('matches').apply(primary=rows, secondary=table,
                condition=ee.Filter.equals(
                    leftField=rowId,
                    rightField=rowId))

            def mapFeatures(feat):
                feature = ee.Feature(feat)
                return [feature.get(colId), ee.String(feature.get(propertyName))]
            def mapValues(row):
                # Map a function over the list of rows to return a list of column ID and value.
                values = ee.List(row.get('matches')).map(mapFeatures)
                # Save the Values from the Property name ('perc' or 'kartiert')
                # Returns the row with its ID property and properties for
                # all matching columns IDs storing the output of the reducer.
                # The Dictionary constructor is using a list of key, value pairs.
                return row.select([rowId]).set(ee.Dictionary(values.flatten()));

            return joined.map(mapValues)

        # Export the landcover of the features per year as csv file in the corresponding google drive folder and names it right
        def exportFeatures(features, landcover, number, tasks):
            filename = landcover + '-' + str(number) #+ 'b'
            foldername = countryName + "-Classification"
            task = Export.table.toDrive(features, description=filename, fileNamePrefix=filename, folder=foldername, fileFormat='CSV')
            task.start()
            tasks.append(task)
            return task, foldername, filename

        # Measure the landcover per feature per year and exports the data.
        def measureLandcover(img, features):
            # Measures the area for each landcover type per Gemeinde
            def mapArea(img):
                return calculateArea(img.select(bandname), features)

            bandname = 'cloudfree'
            cloudfreeCoverArea = img.map(mapArea)
            bandname = 'urban'
            builtupCoverArea = img.map(mapArea)
            bandname = 'gras'
            grasCoverArea = img.map(mapArea)
            bandname = 'crops'
            cropsCoverArea = img.map(mapArea)
            bandname = 'forest'
            forestCoverArea = img.map(mapArea)
            bandname = 'noveg'
            novegCoverArea = img.map(mapArea)
            bandname = 'water'
            waterCoverArea = img.map(mapArea)
            bandname = 'totalPixel'
            totalPixelCoverArea = img.map(mapArea)

            tasks = []
            # Export feature list
            task = exportFeatures(features, 'features', number, tasks)
            tasks.append(task)
            # Export Cloud-free coverage data per year per feature
            tableOutputCloudfree = format(cloudfreeCoverArea.flatten(), id_name, 'year', 'count')
            task = exportFeatures(tableOutputCloudfree, 'cloudfree', number, tasks)
            tasks.append(task)
            # Export Builtup coverage data per year per feature
            tableOutputBuiltup = format(builtupCoverArea.flatten(), id_name, 'year', 'count')
            task = exportFeatures(tableOutputBuiltup, 'builtup', number, tasks)
            tasks.append(task)
            # Export Gras coverage data per year per feature
            tableOutputGras = format(grasCoverArea.flatten(), id_name, 'year', 'count')
            task = exportFeatures(tableOutputGras, 'gras', number, tasks)
            tasks.append(task)
            # Export Crops coverage data per year per feature
            tableOutputCrops = format(cropsCoverArea.flatten(), id_name, 'year', 'count')
            task = exportFeatures(tableOutputCrops, 'crops', number, tasks)
            tasks.append(task)
            # Export Forest coverage data per year per feature
            tableOutputForest = format(forestCoverArea.flatten(), id_name, 'year', 'count')
            task = exportFeatures(tableOutputForest, 'forest', number, tasks)
            tasks.append(task)
            # Export No Vegetation coverage data per year per feature
            tableOutputNoVeg = format(novegCoverArea.flatten(), id_name, 'year', 'count')
            task = exportFeatures(tableOutputNoVeg, 'noveg', number, tasks)
            tasks.append(task)
            # Export Water coverage data per year per feature
            tableOutputWater = format(waterCoverArea.flatten(), id_name, 'year', 'count')
            task = exportFeatures(tableOutputWater, 'water', number, tasks)
            tasks.append(task)
            # Export Cloud-free coverage data per year per feature
            tableOutputTotalPixel = format(totalPixelCoverArea.flatten(), id_name, 'year', 'count')
            task = exportFeatures(tableOutputTotalPixel, 'totalPixel', number, tasks)
            tasks.append(task)

            return tasks

        if doExport:
            # Measures the landcover per class per feature and exports it.
            tasks = measureLandcover(coll_year_class, features)
            print("Classify end")
            return tasks
        else:
            # Returns the classified imagecollection.
            return coll_year_class


