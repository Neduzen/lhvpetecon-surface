import ee
from ee import EEException
from ee.batch import Export
from mongoengine import *
import DriveApi
from Constants import *


class CountryWDB(Document):
    name = StringField(required=True, max_length=200)
    shapefile = StringField(required=True)
    gridCells = ListField()
    prio = IntField(0, 200)
    hasManualGridCells = BooleanField()
    hasStarted = BooleanField()
    isFinished = BooleanField()
    hasImages = BooleanField()

class Country:
    def __init__(self, name, feature):
        self.name = name
        self.feature = feature

    def __init__(self, countryWDB):
        self.CountryWDB = countryWDB

    def GetName(self):
        return self.CountryWDB.name

    def GetAssetName(self):
        return (self.ASSETPATH + self.GetName() + '/').replace(" ", "-")

    def GetGridPath(self):
        return self.GetAssetName() + "Grid"

    def GetPrio(self):
        return self.CountryWDB.prio

    def hasStarted(self):
        return self.CountryWDB.hasStarted

    def hasFinished(self):
        return self.CountryWDB.isFinished

    def hasImages(self):
        if self.CountryWDB.hasImages is None:
            self.CountryWDB.hasImages = False
            self.Save()
        return self.CountryWDB.hasImages

    def GetFeature(self):
        # Get the country shapefile and union to one in case it is split to many parts (like US and Russia).
        region = ee.FeatureCollection(STATES_SHAPE_EENGINE).filter(ee.Filter.eq('country_na', self.CountryWDB.shapefile)).union()
        if region is not None:
            return region
        else:
            raise Exception("Country.GetFeature(): No Feature for the Country was found: {}. Country has to be in the ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017') with property country_na".format(self.GetName()))

    def GetGridCells(self):
        return self.CountryWDB.gridCells

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

    def IsClassificationFinished(self):
        self.CountryWDB.GridCells, finished = DriveApi.CheckClassificationProgress(self.GetName(), self.GetGridCells())
        self.Save()
        return finished

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
