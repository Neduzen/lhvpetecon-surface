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

    # Asset paths
    ASSET = "users/patricklehnert/"
    ASSETNAME = ASSET + "Landcover/"

    def GetName(self):
        return self.countryDB.name

    def GetAssetName(self):
        return (self.ASSETNAME + self.GetName() + '/').replace(" ", "-")

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

    def IsEU(self):
        if self.countryDB.isEu is None:
            return True
        return self.countryDB.isEu

    def Save(self):
        self.countryDB.save()