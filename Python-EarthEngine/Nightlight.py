# Our night-time lights input dataset consists of annual composites of the stable lights band
# from DMSP-OLS Nighttime Lights Time Series Version 4, spanning 1992–2013 [2]. In years
# ith two annual composites, we use data from newer satellites. For the year 2002, data have
# not been composited north of a latitude of ~58˚N—impacted regions are omitted from the
# final dataset for that single year (see S1 Table).
from ee.batch import Export

# start_year = 1992;
# end_year = 2013;
# years = ee.List.sequence(start_year, end_year, 1);
#
# german_muncipalities = ee.FeatureCollection('users/emap1/VG250_GEM_DEBKG');
# dataset = ee.ImageCollection('NOAA/DMSP-OLS/NIGHTTIME_LIGHTS');
# nighttimeLights = dataset.select('stable_lights');
#
# # Get nightlight pictures for  each year
# nightlightYear = ee.ImageCollection(years.map(function(y)
# {
#     start = ee.Date.fromYMD(y, 1, 1);
#     stop = ee.Date.fromYMD(y, 12, 31);
#
#     col = dataset \
#     .filterDate(start, stop) \
#     .reduce(ee.Reducer.mean()) \
#     .set({'system:time_start': start.millis(), 'year': y});
#     return col;
#
# }).flatten()
# ).filterMetadata('year', 'greater_than', 1990);
#
# # Format a table of triplets into a 2D table of rowId x colId.
# # Features need to be reorganized in order to do a proper output.
# format = function(table, rowId, colId, propertyName)
# {
#     # Get a FeatureCollection with unique row IDs.
#     rows = table.distinct(rowId);
#     # Join the table to the unique IDs to get a collection in which
#     # each feature stores a list of all features having a common row ID.
#     joined = ee.Join.saveAll('matches').apply({
#         primary: rows,
#         secondary: table,
#         condition: ee.Filter.equals({
#             leftField: rowId,
#             rightField: rowId
#         })
#     })
#
#     return joined.map(function(row)
# {
#     # Get the list of all features with a unique row ID.
#     values = ee.List(row.get('matches'))
#     # Map a function over the list of rows to return a list of column ID and value.
#     .map(function(feature)
# {
#     feature = ee.Feature(feature);
# # feature = ee.Feature(null,feature);
# # return [ee.String(feature.get(colId)), ee.String(feature.get(propertyName))]; # Save the Values from the Property name ('perc' or 'kartiert')
# return [feature.get(colId),
#         ee.String(feature.get(propertyName))];  # Save the Values from the Property name ('perc' or 'kartiert')
# });
# # Return the row with its ID property and properties for
# # all matching columns IDs storing the output of the reducer.
# # The Dictionary constructor is using a list of key, value pairs.
# return row.select([rowId]).set(ee.Dictionary(values.flatten()));
# });
# };
#
# # Get mean light value per Gemeinde
# var
# meanLight = ee.FeatureCollection(nightlightYear.map(function(img)
# {
# # mean sable lights for all features
# var
# gemeindeMeanLight = img.select('stable_lights_mean').reduceRegions
# ({
#     collection: german_muncipalities,
#     reducer: ee.Reducer.mean(),
#     tileScale: 1
# });
# # Add year to the gemeinde features
# gemeindeMeanLight = gemeindeMeanLight.map(function(feat)
# {
#     feat = feat.set("year", ee.Number(img.get("year")).format("%4d"));
# feat = feat.set("mean", ee.String(feat.get("mean")));
# return ee.Feature(null, feat.toDictionary());
# });
# return gemeindeMeanLight;
# }));
#
# # Get area in percentage, where the 'stable_lights' value lies between the upper and lower limit.
# var
# calcImageMeanPercentage = function(image, german_muncipalities, name, gtenumb, ltnumb)
# {
#     var
# imageMean = ee.FeatureCollection(nightlightYear.map(function(img)
# {
#     var
# lightClass = img.select('stable_lights_mean').gte(gtenumb). and (img.select('stable_lights_mean').lt(ltnumb)).rename(
#     name);
# var
# gemeindeLightClass = lightClass.select(name).reduceRegions \
#         ({
#         collection: german_muncipalities,
#         reducer: ee.Reducer.mean(),
#         tileScale: 1
#     });
# # Add year to the gemeinde features
# gemeindeLightClass = gemeindeLightClass.map(function(feat)
# {
#     feat = feat.set("year", ee.Number(img.get("year")).format("%4d"));
# feat = feat.set(name, ee.String(feat.get("mean")));
# return ee.Feature(null, feat.toDictionary());
# });
# return gemeindeLightClass;
# }));
#
#
# # Generate export format
# tableOutput = format(imageMean.flatten(), 'DEBKG_num', 'year', name)
#
# Export.table.toDrive
#         ({
#         collection: tableOutput,
#         description: name,
#         folder: 'nighlight',
#         fileFormat: 'CSV'
#     })
#
# tableOutputMean = format(meanLight.flatten(), 'DEBKG_num', 'year', 'mean')
# # Exports the mean light per muncipality
# expNameMean = 'meanLight'
# Export.table.toDrive \
#         ({
#         collection: tableOutputMean,
#         folder: 'nighlight',
#         description: expNameMean,
#         fileFormat: 'CSV'
#     });
#
# # Calculates and exports the mean percentage of area per municipality of all the seven light classes
# calcImageMeanPercentage(nightlightYear, german_muncipalities, 'unlit', 0, 0.5)
# calcImageMeanPercentage(nightlightYear, german_muncipalities, 'lightClass1', 0.5, 2.5)
# calcImageMeanPercentage(nightlightYear, german_muncipalities, 'lightClass2', 2.5, 5.5)
# calcImageMeanPercentage(nightlightYear, german_muncipalities, 'lightClass3', 5.5, 10.5)
# calcImageMeanPercentage(nightlightYear, german_muncipalities, 'lightClass4', 10.5, 20.5)
# calcImageMeanPercentage(nightlightYear, german_muncipalities, 'lightClass5', 20.5, 62.5)
# calcImageMeanPercentage(nightlightYear, german_muncipalities, 'lightClass6', 62.5, 100)



#############
import ee
from ee.batch import Export
from SatelliteImages import Satellite

class Nightlight:
    def __init__(self):
        ee.Initialize()
        #self.DoNightlight(ee.FeatureCollection("TIGER/2018/Counties"), "COUNTYNS", 1992, 2013, "United-States")
        #self.DoNightlight(ee.FeatureCollection("users/emap1/us_county_500k_2019"), "COUNTYNS", 1992, 2013, "United-States")
        featCol = ee.FeatureCollection("users/emap1/VG250-KRS-dbgk-id");
        self.DoNightlight(featCol, "debkg-kr_1", 1992, 2013, "Germany2")

    def DoNightlight(self, features, identifier, start_year, end_year, countryName):
        print("DoNightlight")
        start_year = start_year
        end_year = end_year
        years = ee.List.sequence(start_year, end_year, 1)

        dataset = ee.ImageCollection('NOAA/DMSP-OLS/NIGHTTIME_LIGHTS')

        # Get nightlight pictures for  each year
        def nightlightComposite(y):
            start = ee.Date.fromYMD(y, 1, 1)
            stop = ee.Date.fromYMD(y, 12, 31)

            col = dataset \
                .filterDate(start, stop) \
                .reduce(ee.Reducer.mean()) \
                .set({'system:time_start': start.millis(), 'year': y})
            return col
        nightlightYear = ee.ImageCollection(years.map(nightlightComposite).flatten()).filterMetadata('year', 'greater_than', 1990)

        print(nightlightYear.getInfo())
        # Get mean light value per area
        def summarize(img):
            # mean sable lights for all features
            areaMeanLight = img.select('stable_lights_mean').reduceRegions(
                collection= features,
                reducer= ee.Reducer.mean(),
                scale= img.projection().nominalScale())
            # print("proj: "+str(img.select('stable_lights_mean').getInfo()))
            # print("scale: "+str(img.getInfo().projection().nominalScale().getInfo()))

            # Add year to the area features
            def configureFeature(feat):
                feat = feat.set("year", ee.Number(img.get("year")).format("%4d"))
                feat = feat.set("mean", ee.String(feat.get("mean")))
                return ee.Feature(None, feat.toDictionary())
            meanLight = areaMeanLight.map(configureFeature)

            return meanLight

        meanLight = ee.FeatureCollection(nightlightYear.map(summarize))

        # Get area in percentage, where the 'stable_lights' value lies between the upper and lower limit.
        def calcPercentageLightClass(image, name, gtenumb, ltnumb):
            def prepareLightClass(img):
                # Get pixels between lower and higher light value
                lightClassPixels = img.select('stable_lights_mean').gte(gtenumb).And(
                    img.select('stable_lights_mean').lt(ltnumb)).rename(name)
                lightClassReduced = lightClassPixels.select(name).reduceRegions(
                        collection= features,
                        reducer= ee.Reducer.mean(),
                        tileScale= 1)
                # Add year to the area features
                def configureFeatures(feat):
                    feat = feat.set("year", ee.Number(img.get("year")).format("%4d"))
                    feat = feat.set(name, ee.String(feat.get("mean")))
                    return ee.Feature(None, feat.toDictionary())
                regionLightClass = lightClassReduced.map(configureFeatures)
                return regionLightClass
            percentageLightClass = ee.FeatureCollection(image.map(prepareLightClass))
            outputData = format(percentageLightClass.flatten(), identifier, 'year', name)
            exportFeatures(outputData, name)
            return percentageLightClass

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
        def exportFeatures(features, name):
            filename = name + "-kreise"
            foldername = countryName + "-Nightlight"
            task = Export.table.toDrive(features, description=filename, fileNamePrefix=filename, folder=foldername,
                                        fileFormat='CSV')
            task.start()

        # Exports the mean light per feature area
        tableOutputMean = format(meanLight.flatten(), identifier, 'year', 'mean')
        exportFeatures(tableOutputMean, 'meanLight')

        # Calculates and exports the mean percentage of area per municipality of all the seven light classes
        calcPercentageLightClass(nightlightYear, 'unlit', 0, 0.5)
        calcPercentageLightClass(nightlightYear, 'lightClass1', 0.5, 2.5)
        calcPercentageLightClass(nightlightYear, 'lightClass2', 2.5, 5.5)
        calcPercentageLightClass(nightlightYear, 'lightClass3', 5.5, 10.5)
        calcPercentageLightClass(nightlightYear, 'lightClass4', 10.5, 20.5)
        calcPercentageLightClass(nightlightYear, 'lightClass5', 20.5, 62.5)
        calcPercentageLightClass(nightlightYear, 'lightClass6', 62.5, 100)

        print("Nightlight finished")

Nightlight()