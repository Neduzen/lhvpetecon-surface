import ee
from ee import EEException
from ee.batch import Export
from mongoengine import *
import DriveApi
import logging
from Constants import ASSETPATH_US
from Constants import CLIMATESHAPE_US

class StateDB(Document):
    name = StringField(required=True, max_length=200)
    shapefile = StringField(required=True)
    gridCells = ListField()
    prio = IntField(0, 200)
    hasStarted = BooleanField()
    isFinished = BooleanField()
    hasImages = BooleanField()
    trainSize = IntField(50,600)

class State:
    def __init__(self, name, feature):
        self.name = name
        self.feature = feature

    def __init__(self, stateDB):
        self.stateDB = stateDB

    def GetName(self):
        return self.stateDB.name

    def GetAssetName(self):
        return (ASSETPATH_US + self.GetName() + '/').replace(" ", "-")

    def GetGridAssetName(self):
        return self.GetAssetName() + "GridState"

    def GetTrainingAssetName(self):
        return self.GetAssetName() + "Training/"

    def GetPrio(self):
        return self.stateDB.prio

    def GetTrainSize(self):
        if self.stateDB.trainSize is None:
            self.stateDB.trainSize = 600
            self.Save()
        return self.stateDB.trainSize

    def DecreaseTrainSize(self):
        self.stateDB.trainSize -= 20
        self.Save()

    def hasStarted(self):
        return self.stateDB.hasStarted

    def hasFinished(self):
        return self.stateDB.isFinished

    def hasImages(self):
        if self.stateDB.hasImages is None:
            self.stateDB.hasImages = False
            self.Save()
        return self.stateDB.hasImages

    def GetFeature(self):
        # Get the german region in order to get trainings points within the countries' territory.
        region = ee.FeatureCollection('TIGER/2018/States').filter(ee.Filter.eq('NAME', self.stateDB.shapefile))
        if region is not None:
            return region
        else:
            raise Exception("State.GetFeature(): No Feature for the State was found: {}".format(self.GetName()))

    def GetGridCells(self):
        return self.stateDB.gridCells

    def GetCrossValidation(self):
        return False

    def DoesCrossValidationExist(self):
        return True

    def DoGridCellsExist(self):
        gridCells = self.GetGridCells()
        if gridCells is None:
            return False
        expectedGridCount = len(gridCells)
        if expectedGridCount == 0:
            return False

        try:
            gridFeature = ee.FeatureCollection(self.GetGridAssetName())
            if len(gridFeature.getInfo()["features"]) == expectedGridCount:
                return True
            print("Expected Gridcells: {}, Actual Gridcells: {}".format(expectedGridCount, len(gridFeature.getInfo()["features"])))
        except:
            print("Grid Cells not available")
            return False
        return False

    def Save(self):
        self.stateDB.save()

    def CalculateClimatePercentage(self):
        climateShape = ee.FeatureCollection(CLIMATESHAPE_US)
        stateShape = ee.Feature(self.GetFeature().first())

        climateShapeB = climateShape.filter(ee.Filter.eq('zone', 1))
        climateShapeC = climateShape.filter(ee.Filter.eq('zone', 2))
        climateShapeD = climateShape.filter(ee.Filter.eq('zone', 3))
        climateShapeE = climateShape.filter(ee.Filter.eq('zone', 4))

        def intersection(feature):
            return feature.intersection(stateShape)

        def addArea(feature):
            return feature.set("areaHa", feature.geometry().area().divide(1000 * 1000))

        climateShapeB = climateShapeB.map(intersection).filterBounds(stateShape.geometry())
        climateShapeC = climateShapeC.map(intersection).filterBounds(stateShape.geometry())
        climateShapeD = climateShapeD.map(intersection).filterBounds(stateShape.geometry())
        climateShapeE = climateShapeE.map(intersection).filterBounds(stateShape.geometry())

        climateShapeB = climateShapeB.map(addArea)
        b = climateShapeB.aggregate_sum("areaHa").getInfo()
        climateShapeC = climateShapeC.map(addArea)
        c = climateShapeC.aggregate_sum("areaHa").getInfo()
        climateShapeD = climateShapeD.map(addArea)
        d = climateShapeD.aggregate_sum("areaHa").getInfo()
        climateShapeE = climateShapeE.map(addArea)
        e = climateShapeE.aggregate_sum("areaHa").getInfo()

        tot = b + c + d + e
        return b/tot, c/tot, d/tot, e/tot

