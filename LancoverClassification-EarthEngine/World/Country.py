import ee
from ee import EEException
from ee.batch import Export
from mongoengine import *
import DriveApi
import logging

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

    # Asset paths
    ASSET = "users/emap1/"
    ASSETPATH = ASSET+"Landcover-World/"
    SHAPE_AS = ASSET + "asia_shape"
    SHAPE_EA = ASSET + "europe_africa_shape"
    SHAPE_AM = ASSET + "america_shape"
    SHAPE_OC = ASSET + "oceania_shape"

    CLIMATESHAPE_EA = ASSET + "climateShape-europe_africa"
    CLIMATESHAPE_AS = ASSET + "climateShape-asia"
    CLIMATESHAPE_AM = ASSET + "climateShape-america"
    CLIMATESHAPE_OC = ASSET + "climateShape-oceania"

    def GetName(self):
        return self.CountryWDB.name

    def GetAssetName(self):
        return (self.ASSETPATH + self.GetName() + '/').replace(" ", "-")

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
        region = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filter(ee.Filter.eq('country_na', self.CountryWDB.shapefile)).union()
        if region is not None:
            return region
        else:
            raise Exception("Country.GetFeature(): No Feature for the Country was found: {}. Country has to be in the ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017') with property country_na".format(self.GetName()))

    def GetGridCells(self):
        return self.CountryWDB.gridCells

    def GetCrossValidation(self):
        # TODO: do
        print("Crossvalidation of World is not implemented. Skip")
        finished = DriveApi.CheckUSACrossValidationData(self.GetName())
        return finished

    def DoesCrossValidationExist(self):
        # TODO: Crossvalidation
        print("Crossvalidation of World is not implemented. Skip")
        return True
        #finished = DriveApi.CheckUSACrossValidationData(self.GetName())
        #return finished

    def DoGridCellsExist(self):
        gridCells = self.GetGridCells()
        if gridCells is None:
            return False
        expectedGridCount = len(gridCells)
        if expectedGridCount == 0:
            return False

        try:
            gridFeature = ee.FeatureCollection(self.GetAssetName()+"Grid")
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

    def IsEU(self):
        if self.CountryWDB.isEu is None:
            return True
        return self.CountryWDB.isEu

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

            isAsia = contained(ee.FeatureCollection(self.SHAPE_AS).map(intersects))
            isEuAfr = contained(ee.FeatureCollection(self.SHAPE_EA).map(intersects))
            isAmer = contained(ee.FeatureCollection(self.SHAPE_AM).map(intersects))
            isOcea = contained(ee.FeatureCollection(self.SHAPE_OC).map(intersects))

            shape = ee.FeatureCollection([])
            if isAsia:
                shape = ee.FeatureCollection(self.CLIMATESHAPE_AS)
            if isOcea:
                shape = shape.merge(ee.FeatureCollection(self.CLIMATESHAPE_OC))
            if isAmer:
                shape = shape.merge(ee.FeatureCollection(self.CLIMATESHAPE_AM))
            if isEuAfr:
                shape = shape.merge(ee.FeatureCollection(self.CLIMATESHAPE_EA))
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

    # Takes the Feature Country border, calculates the area and splits it into smaller cells.
    def SplitGrid(self):
        gridCells = ee.FeatureCollection(ee.List([]))

        def latlongCellList(long1, long2, lat1, lat2):
            # Get max and min lat and long (in real numbers)
            if lat1 <= lat2:
                n1 = int(lat1)

                n2 = int(lat2)
            else:
                n1 = int(lat2)
                n2 = int(lat1)
            if n1 < 0:
                n1 -= 1
            if n2 > 0:
                n2 += 1
                # ee.Number(ee.Algorithms.If(e1t.gte(e2t), e2t, e1t)).int()
            if long1 <= long2:
                e1 = int(long1)
                e2 = int(long2)
            else:
                e1 = int(long2)
                e2 = int(long1)
            if e1 < 0:
                e1 -= 1
            if n2 > 0:
                e2 += 1

            cellList = []
            i = n1
            while i < n2:
                j = e1
                while j < e2:
                    cellList.append("Long:" + str(j) + ",Lat:" + str(i))
                    j += 1
                i += 1

            return cellList

        if not self.CountryWDB.hasManualGridCells:
            coords = ee.List(self.GetFeature().geometry().bounds().coordinates().get(0))
            n1t = ee.Number(ee.List(coords.get(0)).get(0))
            e1t = ee.Number(ee.List(coords.get(0)).get(1))
            n2t = ee.Number(ee.List(coords.get(2)).get(0))
            e2t = ee.Number(ee.List(coords.get(2)).get(1))
            # Get max and min lat and long (in real numbers)
            e1 = ee.Number(ee.Algorithms.If(e1t.gte(e2t), e2t, e1t)).int().getInfo()
            e2 = ee.Number(ee.Algorithms.If(e1t.gte(e2t), e1t, e2t))
            n1 = ee.Number(ee.Algorithms.If(n1t.gte(n2t), n2t, n1t)).int().getInfo()
            n2 = ee.Number(ee.Algorithms.If(n1t.gte(n2t), n1t, n2t))
            n2 = ee.Number(n2).int().add(1).getInfo()
            e2 = ee.Number(e2).int().add(1).getInfo()
            self.CountryWDB.gridCells = []
            for c in latlongCellList(n1, n2, e1, e2):
                self.CountryWDB.gridCells.append((c, False))
            self.Save()

        polygonList = ee.List([])
        for g in self.GetGridCells():
            long = ee.Number(int(g[0].split(",")[0].split(":")[1]))  # .slice(4))
            lat = ee.Number(int(g[0].split(",")[1].split(":")[1]))  # .slice(3))
            lat1 = lat.add(1)
            long1 = long.add(1)
            coords = ee.List([[long1, lat], [long, lat], [long, lat1], [long1, lat1], [long1, lat]])
            poly = ee.Geometry.Polygon(coords)
            feat = ee.Feature(poly).set("Long", long).set("Lat", lat).set("CellID", g[0])
            polygonList = polygonList.add(feat)
        gridCells = ee.FeatureCollection(polygonList)

        gridCells = gridCells.filterBounds(self.GetFeature())
        gridCells = gridCells.distinct('CellID')  # Only one CellID, no duplicates

        gridInfo = gridCells.getInfo()
        # Add 1 degree lat long grid cells to country
        self.CountryWDB.gridCells = []
        for gtext in gridInfo['features']:
            fullCellId = gtext['properties']['CellID']
            if (fullCellId, False) not in self.GetGridCells() and (fullCellId, True) not in self.GetGridCells():
                self.CountryWDB.gridCells.append((fullCellId, False))
        self.Save()

        # Export grid cells
        task = Export.table.toAsset(
            collection=gridCells,
            description="grid",
            assetId=self.GetAssetName() + "Grid")
        task.start()

        print("1'degree cells for country: {}".format(self.GetGridCells()))
        return None

    # Sets certain gridcells for the country to execute
    def SetManualGridCells(self, cellNameList):
        if len(cellNameList) > 0 and not self.DoGridCellsExist():
            self.CountryWDB.hasManualGridCells = True
            list = []
            for c in cellNameList:
                list.append((c, False))
            self.CountryWDB.gridCells = list
