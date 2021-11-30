import ee
from ee import EEException
from ee.batch import Export
from mongoengine import *
import DriveApi
import logging

class CountryDB(Document):
    name = StringField(required=True, max_length=200)
    shapefile = StringField(required=True)
    gridCells = ListField()
    prio = IntField(0,200)
    hasStarted = BooleanField()
    isFinished = BooleanField()
    isEu = BooleanField()
    hasAllCorine = BooleanField()

class Country:
    def __init__(self, name, feature):
        self.name = name
        self.feature = feature

    def __init__(self, countryDB):
        self.countryDB = countryDB

    def GetName(self):
        return self.countryDB.name

    def GetAssetName(self):
        return ('users/patricklehnert/Landcover/' + self.GetName() + '/').replace(" ", "-")

    def GetPrio(self):
        return self.countryDB.prio

    def hasStarted(self):
        return self.countryDB.hasStarted

    def hasFinished(self):
        return self.countryDB.isFinished

    def hasAllCorine(self):
        return self.countryDB.hasAllCorine

    def GetFeature(self):
        # Get the german region in order to get trainings points within the countries' territory.
        region = ee.FeatureCollection('USDOS/LSIB_SIMPLE/2017').filter(ee.Filter.eq('country_na', self.countryDB.shapefile))
        if region is not None:
            return region
        else:
            raise Exception("Country.GetFeature(): No Feature for the country was found: {}".format(self.GetName()))

    def GetGridCells(self):
        return self.countryDB.gridCells

    def GetCrossValidation(self):
        # ToDo, download and get data.
        finished = DriveApi.CheckCrossValidationData(self.GetName(), self.hasAllCorine())
        return finished

    def DoesCrossValidationExist(self):
        finished = DriveApi.CheckCrossValidationData(self.GetName(), self.hasAllCorine())
        return finished

    # If all 5 training data files exist, return true.
    def DoesTrainingDataExist(self):
        trainingAssetPath = self.GetAssetName() + 'Training/'
        try:
            trainingAssets = ee.data.listAssets(
                {"parent": "projects/earthengine-legacy/assets/" + self.GetAssetName() + "Training"})
            allExist = 0
            trainlist = [trainingAssetPath + "train2000", trainingAssetPath + "train2006",
                         trainingAssetPath + "train2012", trainingAssetPath + "train2018"]
            if self.hasAllCorine():
                trainlist.append(trainingAssetPath + "train1990", )
            assetlist = trainingAssets["assets"]
            for a in assetlist:
                if a["id"] in trainlist:
                    allExist += 1
            if allExist == 5 and self.hasAllCorine():
                return True
            if allExist == 4 and not self.hasAllCorine():
                # If country has no corine data for 1990, return True if the others exist
                return True
        except EEException:
            # If asset does not exist, create one
            try:
                ee.data.createAsset({'type': 'Folder'}, trainingAssetPath[:-1])
            except EEException:
                return False
        return False

    # Gets the trainings data, if they exist, and returns classifier.
    def GetTrainingsData(self):
        if not self.DoesTrainingDataExist():
            return None

        trainingAssetPath = self.GetAssetName() + 'Training/'

        train2000 = ee.FeatureCollection(trainingAssetPath+"train2000")
        train2006 = ee.FeatureCollection(trainingAssetPath+"train2006")
        train2012 = ee.FeatureCollection(trainingAssetPath+"train2012")
        train2018 = ee.FeatureCollection(trainingAssetPath+"train2018")
        trainAll = train2018.merge(train2012).merge(train2006).merge(train2000)

        if self.hasAllCorine():
            # If country has corine data for 1990, add it as well
            trainAll = trainAll.merge(ee.FeatureCollection(trainingAssetPath+"train1990"))

        bandNamesToTrain = ee.List(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'NDVI', 'NDBI', 'WI'])
        classifierCorine = ee.Classifier.smileRandomForest(10).train(trainAll, 'landcover', bandNamesToTrain)

        return classifierCorine

    def DoGridCellsExist(self):
        gridAssetPath = self.GetAssetName() + 'Grid/'
        try:
            gridAssets = ee.data.listAssets({"parent": "projects/earthengine-legacy/assets/" + self.GetAssetName() + "Grid"})
            allExist = 0
            gridCellFileList = []
            for g in self.GetGridCells():
                gridCellFileList.append(gridAssetPath + "grid-" + str(g[0]))
            assetlist = gridAssets["assets"]
            for a in assetlist:
                if a["id"] in gridCellFileList:
                    allExist += 1
            if allExist > 0 and allExist == len(self.GetGridCells()):
                return True
        except EEException:
            logging.WARNING("Exception raised in DoGridCellsExist {}".format(EEException))
            return False
        return False

    def IsClassificationFinished(self):
        self.countryDB.GridCells, finished = DriveApi.CheckClassificationProgress(self.GetName(), self.GetGridCells())
        self.Save()
        return finished

    def IsImageExportFinished(self):
        for g in self.GetGridCells():
            if g[1] is False:
                return False
        return True

    def ManageImageExport(self):
        # Manage image folders on the drive, move files to subfolders
        DriveApi.ManageImageFolders(self.GetName())
        # Get Update about progress
        imageProgress = DriveApi.CheckImageProgress(self.GetName(), self.GetGridCells(), yearFrom=2000, yearTo=2020, fails=1)

        # Set cells to progress
        for g in self.GetGridCells():
            if g[0] in imageProgress[0]:
                g[1] = False
            else:
                g[1] = True
        self.Save()

        print("Total cells: {} , finished: {}: , todo: {}".format(len(self.GetGridCells()),
                                                                      len(self.GetGridCells()) - len(
                                                                          imageProgress[0]),
                                                                      len(imageProgress[0])))

    def IsEU(self):
        if self.countryDB.isEu is None:
            return True
        return self.countryDB.isEu

    def Save(self):
        self.countryDB.save()

    # Takes the Feature Country border, calculates the area and splits it into smaller cells.
    def SplitGrid(self):
        # 100 km^2 Grid
        grid100 = ee.FeatureCollection("users/patricklehnert/grid_eu25_etrs_laea_100k")
        grid100 = grid100.filterBounds(self.GetFeature())

        def getSubCells(obj):
          #  area = obj.geometry().area(10)  # Get official total area
            c1 = ee.String(ee.Feature(obj).get('cell_id')).slice(0, 2)
            c2 = ee.String(ee.Feature(obj).get('cell_id')).slice(3, 5)
            #cell = ee.Number.parse(c1)
            #split big cell into two
            cell_id = ee.Number.parse(c1.cat(c2).cat('0'))

            # ee.Number.parse(ee.String(ee.Feature(obj).get('cell_id')).slice(0, 4) + ee.String(ee.Feature(obj).get('cell_id')).slice(5,9))
            # rasters = raster.filterBounds(ee.Feature(obj))
            # run = 0 # Define a run number in order the Gemeindes are split to smaller runs
            # Export small cells
            # Save Cell_Id
            dictionary = ee.Dictionary({"CellId": cell_id})  # , "CellId": cell_id, "AREA": area})

            return ee.Feature(obj.geometry(), dictionary)  # (obj.geometry(), dictionary)

        def addSecondHalfSub(obj):
            c1 = ee.String(ee.Feature(obj).get('cell_id')).slice(0, 2)
            c2 = ee.String(ee.Feature(obj).get('cell_id')).slice(3, 5)
            #split big cell into two
            cell_id = ee.Number.parse(c1.cat(c2).cat('1'))
            dictionary = ee.Dictionary({"CellId": cell_id})  # , "CellId": cell_id, "AREA": area})
            return ee.Feature(obj.geometry(), dictionary)  # (obj.geometry(), dictionary)

            # #  area = obj.geometry().area(10)  # Get official total area
            # c1 = ee.String(ee.Feature(obj).get('CellId'))
            # # split big cell into two (change 0 to 1 in cellId
            # cell_id = ee.Number.parse(c1.slice(0, 4).cat('1'))
            # dictionary = ee.Dictionary({"CellId": cell_id})
            # return ee.Feature(None, dictionary)

        grid100_0 = grid100.map(getSubCells)
        grid100_1 = grid100.map(addSecondHalfSub)
        grid100 = grid100_0.merge(grid100_1)
        gridInfo = grid100.getInfo()
        gridCells = []

        # Get list of all big cells
        for gtext in gridInfo['features']:
            gridCells.append((gtext['properties']['CellId'], False))

        # Aaign big cell id to the small cells.
        def cutSmallGrid(obj):
            eoId = ee.String(ee.Feature(obj).get('CELLCODE')).slice(4, 6)
            noId = ee.String(ee.Feature(obj).get('CELLCODE')).slice(9, 11)
            eoSmallId = ee.String(ee.Feature(obj).get('CELLCODE')).slice(4, 8)
            noSmallId = ee.String(ee.Feature(obj).get('CELLCODE')).slice(9, 13)
            smallCellId = ee.Number.parse(eoSmallId.cat(noSmallId))

            #Split grid in half:
            halfNumber = ee.Algorithms.If(ee.Number.parse(eoSmallId.slice(2,4)).lt(50), "0", "1")

            cell_id = ee.Number.parse(eoId.cat(noId).cat(halfNumber))

            #old cell id
            # c1 = ee.String(ee.Feature(obj).get('cell_id')).slice(0, 2)
            # c2 = ee.String(ee.Feature(obj).get('cell_id')).slice(5, 7)
            # csmall1 = ee.String(ee.Feature(obj).get('cell_id')).slice(0, 4)
            # csmall2 = ee.String(ee.Feature(obj).get('cell_id')).slice(5, 9)
            # sCellId = ee.Number.parse(csmall1.cat(csmall2))
            # cell_id = ee.Number.parse(c1.cat(c2))
            return ee.Feature(obj.geometry(), obj.toDictionary().set('CellId', cell_id).set('SmallCellId', smallCellId))

        smallGrid = ee.FeatureCollection(self.GetAssetName() + 'Grid/grid_etrs_laea_1k')
        smallGrid = smallGrid.filterBounds(self.GetFeature())

        # print("TEST NEW split method")
        # print(smallGrid.limit(5).getInfo())
        # gridList = []
        # gridIndexList = []
        # for g in gridCells:
        #     gridList.append([])

        smallGrid = smallGrid.map(cutSmallGrid)

        #TES



        # removeCells = []
        for g in gridCells:
            # Check if big cell id is equal to the small cell_id
            bigCell = grid100.filter(ee.Filter.eq('CellId', g[0]))
            smallGridRegion = smallGrid.filterBounds(bigCell)
            smallGridRegion = smallGridRegion.filter(ee.Filter.eq('CellId', g[0]))

            # Test: TODO:
            smallGrid = smallGrid.filter(ee.Filter.neq('CellId', g[0]))
            print("Grid: {}".format(g))
           # count = smallGridRegion.size().getInfo()
           #  if 0 == 0:#count > 0:
            smallGridRegion = smallGridRegion.distinct('SmallCellId') # Only one small cell per SmallCellID, no duplicates
            name = "grid-" + str(g[0])
            task = Export.table.toAsset(
                collection=smallGridRegion,
                description=name,
                assetId=self.GetAssetName() + "Grid/" + name)
            task.start()
            print("Split grid : {}".format(name))
            # else:
            #     print("false")
            #     removeCells.append(g)

        # for rg in removeCells:
        #     gridCells.remove(rg)

        self.countryDB.gridCells = gridCells
        self.Save()
        return None

    # Splits the 10km europe grid into the subcell of the current country and exports them as asset files
    def SplitGrid10km(self):
        # 100 km^2 Grid
        grid100 = ee.FeatureCollection("users/patricklehnert/europe_100km")
        grid100 = grid100.filterBounds(self.GetFeature())

        # 10km^2 Grid
        smallGrid = ee.FeatureCollection('users/patricklehnert/europe_10km')
        smallGrid = smallGrid.filterBounds(self.GetFeature())

        # Get first half
        def getSubCells(obj):
            eString = ee.String(ee.String(ee.Feature(obj).get("CellCode")).split('[A-Z]').get(1))
            nString = ee.String(ee.String(ee.Feature(obj).get("CellCode")).split('[A-Z]').get(2))
            c1 = ee.String(ee.Algorithms.If(eString.length().eq(1), ee.String("0").cat(eString), eString))
            c2 = ee.String(ee.Algorithms.If(nString.length().eq(1), ee.String("0").cat(nString), nString))
            # split big cell into two
            cell_id = c1.cat(c2).cat('0')#ee.Number.parse(c1.cat(c2).cat('0'))
            # Save Cell_Id
            dictionary = ee.Dictionary({"CellId": cell_id})  # , "CellId": cell_id, "AREA": area})
            return ee.Feature(obj.geometry(), dictionary)  # (obj.geometry(), dictionary)

        # Get second half
        def addSecondHalfSub(obj):
            eString = ee.String(ee.String(ee.Feature(obj).get("CellCode")).split('[A-Z]').get(1))
            nString = ee.String(ee.String(ee.Feature(obj).get("CellCode")).split('[A-Z]').get(2))
            c1 = ee.String(ee.Algorithms.If(eString.length().eq(1), ee.String("0").cat(eString), eString))
            c2 = ee.String(ee.Algorithms.If(nString.length().eq(1), ee.String("0").cat(nString), nString))
            # split big cell into two
            cell_id = c1.cat(c2).cat('1')#ee.Number.parse(c1.cat(c2).cat('1'))
            dictionary = ee.Dictionary({"CellId": cell_id})
            return ee.Feature(obj.geometry(), dictionary)

        grid100_0 = grid100.map(getSubCells)
        grid100_1 = grid100.map(addSecondHalfSub)
        grid100 = grid100_0.merge(grid100_1)
        gridInfo = grid100.getInfo()
        gridCells = []

        # Get list of all big cells
        for gtext in gridInfo['features']:
            gridCells.append((gtext['properties']['CellId'], False))

        # Asign big cell id to the small cells.
        def cutSmallGrid(obj):
            eString = ee.String(ee.String(ee.Feature(obj).get("CellCode")).split('[A-Z]').get(1))
            nString = ee.String(ee.String(ee.Feature(obj).get("CellCode")).split('[A-Z]').get(2))
            eoSmallId = ee.Algorithms.If(eString.length().eq(1),
                                         ee.String("00").cat(eString),
                                         ee.Algorithms.If(eString.length().eq(2),
                                                          ee.String("0").cat(eString),
                                                          eString))
            noSmallId = ee.Algorithms.If(nString.length().eq(1),
                                         ee.String("00").cat(nString),
                                         ee.Algorithms.If(nString.length().eq(2),
                                                          ee.String("0").cat(nString),
                                                          nString))

            eoId = ee.String(eoSmallId).slice(0, 2)
            noId = ee.String(noSmallId).slice(0, 2)
            smallCellId = ee.String(eoSmallId).cat(noSmallId)#ee.Number.parse(eoSmallId.cat(noSmallId))

            # Split grid in half:
            halfNumber = ee.Algorithms.If(ee.Number.parse(ee.String(eoSmallId).slice(2, 3)).lt(5), "0", "1")

            cell_id = ee.String(ee.String(eoId).cat(noId)).cat(halfNumber)#ee.Number.parse(eoId.cat(noId).cat(halfNumber))

            return ee.Feature(obj.geometry(), obj.toDictionary().set('CellId', cell_id).set('SmallCellId', smallCellId))

        smallGrid = smallGrid.map(cutSmallGrid)

        removeCells = []
        for g in gridCells:
            # Check if big cell id is equal to the small cell_id
            bigCell = grid100.filter(ee.Filter.eq('CellId', g[0]))
            smallGridRegion = smallGrid.filterBounds(bigCell)
            smallGridRegion = smallGridRegion.filter(ee.Filter.eq('CellId', g[0]))

            smallGrid = smallGrid.filter(ee.Filter.neq('CellId', g[0]))
            print("Grid: {}".format(g))

            if smallGridRegion.size().getInfo() > 0:
                # Only one small cell per SmallCellID, no duplicates
                smallGridRegion = smallGridRegion.distinct('SmallCellId')
                name = "grid-" + str(g[0])
                task = Export.table.toAsset(
                    collection=smallGridRegion,
                    description=name,
                    assetId=self.GetAssetName() + "Grid/" + name)
                task.start()
                print("Split grid : {}".format(name))
            else:
                print("Empty cell grid : {}".format(g[0]))
                removeCells.append(g)

        for rg in removeCells:
            gridCells.remove(rg)

        self.countryDB.gridCells = gridCells
        self.Save()
        return None

