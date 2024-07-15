import ee
from ee import EEException
from mongoengine import *
import DriveApi
from Constants import *


# Contains the country information locally.
# Information about the execution progress, grid cells, shapefiles and further info.
class CountryWDB(Document):
    name = StringField(required=True, max_length=200)
    shapefile = StringField(required=True)
    hasManualShapefile = BooleanField()
    manualShapefile = StringField()
    gridCells = ListField()
    prio = IntField(0, 999)
    hasManualGridCells = BooleanField()
    hasStarted = BooleanField()
    isFinished = BooleanField()
    hasImages = BooleanField()
    trainSize = IntField(50, 600)


# Class for running the country's classification process.
class Country:
    def __init__(self, name, feature):
        self.name = name
        self.feature = feature

    def __init__(self, countryWDB):
        self.CountryWDB = countryWDB

    # Returns the country name
    def GetName(self):
        return self.CountryWDB.name

    # Returns name of files without apostrophes (inserted after Cote d'Ivoire)
    def GetExportName(self):
        return self.CountryWDB.name.replace("'", "")

    # Returns the country asset name in the earth engine platform
    def GetAssetName(self):
        return (ASSETPATH + self.GetName() + '/').replace(" ", "-").replace("(", "").replace(")", "").replace("'", "").replace("&", "-and-").replace(".", "").replace(",", "")

    # Returns the path of the grid file in GEE.
    def GetGridPath(self):
        return self.GetAssetName() + "Grid"

    # Returns the execution priority of the country
    def GetPrio(self):
        return self.CountryWDB.prio

    # Returns whether the execution of the country was already initialized.
    def hasStarted(self):
        return self.CountryWDB.hasStarted

    # Returns whether the execution of the country is already finished.
    def hasFinished(self):
        return self.CountryWDB.isFinished

    # Returns whether there are already some images exported of the given country.
    def hasImages(self):
        if self.CountryWDB.hasImages is None:
            self.CountryWDB.hasImages = False
            self.Save()
        return self.CountryWDB.hasImages

    # Returns the size limit of training data.
    # Corresponds to the amount of satelitte image per year per region which is considered.
    # Done to not get computation error.
    def GetTrainSize(self):
        if self.CountryWDB.trainSize is None:
            self.CountryWDB.trainSize = 600
            self.Save()
        return self.CountryWDB.trainSize

    # Decreases the training size by 20.
    def DecreaseTrainsSize(self):
        self.CountryWDB.trainSize -= 20
        self.Save()

    # Gets the country shapefile from GEE and combines it to one feature.
    def GetFeature(self):
        if self.CountryWDB.hasManualShapefile:
            # this is specific for Brazil
            region = ee.FeatureCollection(SHAPE_STATES_BRAZIL).filter(ee.Filter.eq('SIGLA', self.CountryWDB.shapefile)).union()
            #region = ee.FeatureCollection(self.CountryWDB.manualShapefile).filter(ee.Filter.eq('region_na', self.CountryWDB.shapefile)).union()
        else:
            # Get the country shapefile and union to one in case it is split to many parts (like US and Russia).
            region = ee.FeatureCollection(STATES_SHAPE_EENGINE).filter(ee.Filter.eq('country_na', self.CountryWDB.shapefile)).union()
        if region is not None:
            return region
        else:
            raise Exception("Country.GetFeature(): No Feature for the Country was found: {}. Country has to be in the ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017') with property country_na".format(self.GetName()))

    # Returns the grid cell.
    def GetGridCells(self):
        return self.CountryWDB.gridCells

    # Returns whether the grid cell shapefile exists.
    def DoGridCellsExist(self):
        gridCells = self.GetGridCells()
        if gridCells is None:
            return False
        expectedGridCount = len(gridCells)
        if expectedGridCount == 0:
            return False
        try:
            gridFeature = ee.FeatureCollection(self.GetGridPath())
            if len(gridFeature.getInfo()["features"]) == expectedGridCount:
                return True
            print("Expected Gridcells: {}, Actual Gridcells: {}".format(expectedGridCount, len(gridFeature.getInfo()["features"])))
        except:
            print("Exception raised in DoGridCellsExist")
            return False
        return False

    # Returns whether the classification is already finished.
    def IsClassificationFinished(self):
        self.CountryWDB.GridCells, finished = DriveApi.CheckClassificationProgress(self.GetName(), self.GetGridCells())
        self.Save()
        return finished

    # Saves the mongo db object of the country
    def Save(self):
        self.CountryWDB.save()

    # Calculates the areas in percentage of the country for the five climate classes (b, c, d, e)
    # Zone a is added to zone c.
    def CalculateClimatePercentage(self):
        print("Calculates percentage of climate region of country")
        countryShape = ee.Feature(self.GetFeature().first())

        def intersects(feature):
            return ee.Feature(None, feature.set("isContained", feature.intersects(countryShape)).toDictionary())

        def intersection(feature):
            return feature.intersection(countryShape)

        def addArea(feature):
            return feature.set("areaHa", feature.geometry().area().divide(1000 * 1000))

        def getClimateShape():
            def contained(shape):
                for feat in shape.getInfo()["features"]:
                    if feat["properties"]["isContained"]:
                        return True
                return False

            isAsia = contained(ee.FeatureCollection(SHAPE_AS).map(intersects))
            isEuAfr = contained(ee.FeatureCollection(SHAPE_EA).map(intersects))
            isAmer = contained(ee.FeatureCollection(SHAPE_AM).map(intersects))
            isOcea = contained(ee.FeatureCollection(SHAPE_OC).map(intersects))

            shape = ee.FeatureCollection([])
            if isAsia:
                shape = ee.FeatureCollection(CLIMATESHAPE_AS)
            if isOcea:
                shape = shape.merge(ee.FeatureCollection(CLIMATESHAPE_OC))
            if isAmer:
                shape = shape.merge(ee.FeatureCollection(CLIMATESHAPE_AM))
            if isEuAfr:
                shape = shape.merge(ee.FeatureCollection(CLIMATESHAPE_EA))
            return shape

        climateShape = getClimateShape()

        # Get zone shapes
        climateShapeA = climateShape.filter(ee.Filter.eq('zone', 0))
        climateShapeB = climateShape.filter(ee.Filter.eq('zone', 1))
        climateShapeC = climateShape.filter(ee.Filter.eq('zone', 2))
        climateShapeD = climateShape.filter(ee.Filter.eq('zone', 3))
        climateShapeE = climateShape.filter(ee.Filter.eq('zone', 4))

        # Intersect zones with country to get zones of country
        climateShapeA = climateShapeA.map(intersection).filterBounds(countryShape.geometry())
        climateShapeB = climateShapeB.map(intersection).filterBounds(countryShape.geometry())
        climateShapeC = climateShapeC.map(intersection).filterBounds(countryShape.geometry())
        climateShapeD = climateShapeD.map(intersection).filterBounds(countryShape.geometry())
        climateShapeE = climateShapeE.map(intersection).filterBounds(countryShape.geometry())

        # Calculate area per zone
        climateShapeA = climateShapeA.map(addArea)
        a = climateShapeA.aggregate_sum("areaHa").getInfo()
        climateShapeB = climateShapeB.map(addArea)
        b = climateShapeB.aggregate_sum("areaHa").getInfo()
        climateShapeC = climateShapeC.map(addArea)
        c = climateShapeC.aggregate_sum("areaHa").getInfo()
        climateShapeD = climateShapeD.map(addArea)
        d = climateShapeD.aggregate_sum("areaHa").getInfo()
        climateShapeE = climateShapeE.map(addArea)
        e = climateShapeE.aggregate_sum("areaHa").getInfo()

        # In europe no tropical zone exist. Usually tropical zone is strongly vegetated, similar to c (if winter is omitted)
        c = a+c
        # Calculate percentage of the zones
        tot = b + c + d + e
        return b/tot, c/tot, d/tot, e/tot

    # Creates the asset in GEE
    def CreateAsset(self):
        assetName = self.GetAssetName()
        try:
            trainingAssets = ee.data.listAssets(
                {"parent": "projects/earthengine-legacy/assets/" + assetName})
        except EEException:
            # If asset does not exist, create one
            ee.data.createAsset({'type': 'Folder'}, assetName[0:len(assetName)-1])
            ee.data.createAsset({'type': 'Folder'}, assetName + "/Training")
        return None

    # Sets certain grid cells for the country to execute
    def SetManualGridCells(self, cellNameList):
        if len(cellNameList) > 0 and not self.DoGridCellsExist():
            self.CountryWDB.hasManualGridCells = True
            list = []
            for c in cellNameList:
                list.append((c, False))
            self.CountryWDB.gridCells = list

    def SetManualShapefile(self, ShapefileName):
        self.CountryWDB.hasManualShapefile = True
        self.CountryWDB.ManualShapefile = ShapefileName
