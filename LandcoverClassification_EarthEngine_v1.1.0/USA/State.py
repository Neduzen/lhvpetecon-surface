import ee
from mongoengine import *
from Constants import ASSETPATH_US
from Constants import CLIMATESHAPE_US


# US State local mongoDB object, containing the information needed to run the state.
class StateDB(Document):
    name = StringField(required=True, max_length=200)
    shapefile = StringField(required=True)
    gridCells = ListField()
    prio = IntField(0, 200)
    hasStarted = BooleanField()
    isFinished = BooleanField()
    hasImages = BooleanField()
    trainSize = IntField(50,600)

# State object containing the data to run the state.
class State:
    def __init__(self, name, feature):
        self.name = name
        self.feature = feature

    def __init__(self, stateDB):
        self.stateDB = stateDB

    # Returns the state name
    def GetName(self):
        return self.stateDB.name

    # Returns the state asset name in the earth engine platform
    def GetAssetName(self):
        return (ASSETPATH_US + self.GetName() + '/').replace(" ", "-")

    # Returns the path of the grid asset name in GEE.
    def GetGridAssetName(self):
        return self.GetAssetName() + "GridState"

    # Returns the training asset name in GEE.
    def GetTrainingAssetName(self):
        return self.GetAssetName() + "Training/"

    # Returns the priority of execution.
    def GetPrio(self):
        return self.stateDB.prio

    # Returns the size limit of training data.
    # Corresponds to the amount of satelitte image per year per region which is considered.
    # Done to not get computation error.
    def GetTrainSize(self):
        if self.stateDB.trainSize is None:
            self.stateDB.trainSize = 600
            self.Save()
        return self.stateDB.trainSize

    # Decreases the training size limitation.
    def DecreaseTrainSize(self):
        self.stateDB.trainSize -= 20
        self.Save()

    # Returns whether the state execution has already been started once.
    def hasStarted(self):
        return self.stateDB.hasStarted

    # Returns whether the state is fully finished (all images exported).
    def hasFinished(self):
        return self.stateDB.isFinished

    # Returns whether the state has already some images.
    def hasImages(self):
        if self.stateDB.hasImages is None:
            self.stateDB.hasImages = False
            self.Save()
        return self.stateDB.hasImages

    # Returns the feature (shapefile) of the state in GEE.
    def GetFeature(self):
        # Get the german region in order to get trainings points within the countries' territory.
        region = ee.FeatureCollection('TIGER/2018/States').filter(ee.Filter.eq('NAME', self.stateDB.shapefile))
        if region is not None:
            return region
        else:
            raise Exception("State.GetFeature(): No Feature for the State was found: {}".format(self.GetName()))

    # Returns the grids cells of the state.
    def GetGridCells(self):
        return self.stateDB.gridCells

    # Returns whether the grid cells exist or not.
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

    # Saves the state data in the mongoDB.
    def Save(self):
        self.stateDB.save()

    # Calculates the percentage of climate zones within the state. Needed for the training data generation.
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

