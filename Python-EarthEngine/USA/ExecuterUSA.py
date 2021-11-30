import logging
import ee
from ee import EEException
from ee.batch import Export

import CorineImages
import SatelliteImages
from USA.ImageExporter import ImageExporter
from USA.State import State
from Classify import Classify
from Training import Training
from USA.CrossValidationUSA import CrossValidationUSA
import DriveApi
from USA.TrainingUSA import TrainingUSA


class ExecuterUSA:
    def __init__(self, states):
        ee.Initialize()
        self.states = states
        self.assetPath = 'users/emap1/Landcover-USA/'
        self.trainingAssetPath = self.assetPath + 'Training/'
        self.classifiersCrossValAssetPath = self.assetPath + 'TrainCrossVal/'

    RUNPARALLEL = 8

    # Returns a list of all assets for the given asset directory.
    @staticmethod
    def GetAssetList(subdirectory):
        try:
            assetlist = ee.data.listAssets(
                {"parent": "projects/earthengine-legacy/assets/" + subdirectory})
            return assetlist
        except EEException:
            # If asset does not exist, create one
            try:
                ee.data.createAsset({'type': 'Folder'}, subdirectory[:-1])
            except EEException:
                print("Asset folder does not exist, error raise")
                return False
        return False

    # Gets the actual state to execute next tasks.
    def GetActualState(self):
        actualState = None
        minPrio = 100
        for s in self.states:
            #TODO: Image change
            if not (s.hasFinished() and s.hasImages()) and s.stateDB.prio < minPrio:
                minPrio = s.stateDB.prio
                actualState = s
        if actualState is None:
            logging.warning("No actual state found")
            return None
        print("Actual state: {}".format(actualState.GetName()))
        actualState.stateDB.hasStarted = True
        actualState.Save()
        return actualState

    # Runs the next tasks for the actual state and actual progress. Identifies and launches next tasks.
    def RunNextTask(self):
        state = self.GetActualState()
        if state is not None:
            logging.info("State: {}, run next task".format(state.GetName()))
        else:
            self.reportStep('No actual state found.')

        # Wait, if tasks are still pending
        if not self.AreTasksFinished():
            # Tasks are still in progress, sleep (nothing to do)
            name = 'us'
            if state is not None:
                name = state.GetName()
            self.reportStep("State: {}, tasks still pending, ... Wait".format(name))
            self.reportPendingTasks()

            # report state classification
            celln = 0
            truen = 0
            for cell in state.GetGridCells():
                celln += 1
                if cell[1] is True:
                    truen += 1
            print("{} of {} finished, {} in progress".format(truen, celln, self.RUNPARALLEL))
            #print(DriveApi.CheckClassificationProgress(state.GetName(), state.GetGridCells()))

            return False

        # Create setup, if data not yet exist
        doesTrainingsDataExist, trynumber = self.DoesTrainingDataExist(True, state)
        if not doesTrainingsDataExist:
            # Execute Training for classification, if data does not yet exist
            self.RunTraining(state, True, self.trainingAssetPath, trynumber)
            return None
        # If state is finished, but images not yet exported, do so
        if not state.hasImages():#state.hasFinished() and state.hasImages() is False:
            imager = ImageExporter()
            imager.RunImage(state, self.GetTrainingsData(True, state))
            return None
        if not self.DoClassifiersExistCrossVal():
            # Execute Training for CrossValidation, if does not yet exist.
            self.RunTrainingCrossVal()
            return None

        # Execute next step (CrossVal or Classify)
        if state is not None and state.hasStarted():
            # Run CrossValidation first, if not yet executed
            # self.RemoveEmptyCells(state)
            # If grid is not splited, then  split it.
            if len(state.GetGridCells()) == 0 or not state.DoGridCellsExist():
                self.reportStep("Country: {}, split grid".format(state.GetName()))
                state.SplitGrid()
            else:
                # Next classification tasks if no all finished
                if state.IsClassificationFinished() is False:
                    self.reportStep("Country: {}, run classification".format(state.GetName()))
                    self.RunNextClassification(state)
                # Run CrossValidation if Classification for state is finished
                elif not state.DoesCrossValidationExist():
                    self.reportStep("Country: {}, run cross validation".format(state.GetName()))
                    self.RunCrossValidation(state)
                # State is finished
                else:
                    self.reportStep("Country: {}, is finished".format(state.GetName()))
                    state.stateDB.isFinished = True
                    state.Save()
                    self.RunNextTask()
        else:
            logging.WARNING("No state for next run found")
            raise Exception("NO state FOR NEXT RUN")
        self.reportPendingTasks()
        print('END')
        return None

    # Run Training Data, export training values for the five reference years.
    def RunTraining(self, state, newTraining, assetPath, tryNumber, extension='', seed=0):
        if newTraining:
            b_perc, c_perc, d_perc, e_perc = state.CalculateClimatePercentage()
            trainingCorine = TrainingUSA()
            trainingCorine.ProduceTrainingDataClimate(1990, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber)
            trainingCorine.ProduceTrainingDataClimate(2000, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber)
            trainingCorine.ProduceTrainingDataClimate(2006, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber)
            trainingCorine.ProduceTrainingDataClimate(2012, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber)
            trainingCorine.ProduceTrainingDataClimate(2018, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber)
        else:
            self.RunTrainingOld(assetPath, extension, seed)

    def RunTrainingOld(self, assetpath, extension='', seed=0):
        trainingCorine = Training()

        # Runs for one part of europe the training data sampling and saves it as asset.
        def runTrainingPart(extension, part, number, number1990, assetPath, seed):
            # Get EU-Region as Feature
            euRegion = ee.FeatureCollection(self.assetPath + 'Europe10/' + 'europe' + part)
            # Gather training data per year for the region
            trainingCorine.ProduceTrainingData(euRegion, 1990, None, assetPath, number1990, extension + part, seed)
            trainingCorine.ProduceTrainingData(euRegion, 2000, None, assetPath, number, extension + part, seed)
            trainingCorine.ProduceTrainingData(euRegion, 2006, None, assetPath, number, extension + part, seed)
            trainingCorine.ProduceTrainingData(euRegion, 2012, None, assetPath, number, extension + part, seed)
            trainingCorine.ProduceTrainingData(euRegion, 2018, None, assetPath, number, extension + part, seed)

        # Run the training sample for all 10 europe regions.
        runTrainingPart(extension, '-1', 86, 119, assetpath, seed)
        runTrainingPart(extension, '-2', 95, 131, assetpath, seed)
        runTrainingPart(extension, '-3', 89, 113, assetpath, seed)
        runTrainingPart(extension, '-4', 105, 145, assetpath, seed)
        runTrainingPart(extension, '-5', 135, 186, assetpath, seed)
        runTrainingPart(extension, '-6', 131, 0, assetpath, seed)
        runTrainingPart(extension, '-7', 92, 111, assetpath, seed)
        runTrainingPart(extension, '-8', 94, 118, assetpath, seed)
        runTrainingPart(extension, '-9', 85, 35, assetpath, seed)
        runTrainingPart(extension, '-10', 88, 42, assetpath, seed)

    # Runs the Training Data 5 times independently, in order 5 training classifiers exist for the cross validation
    def RunTrainingCrossVal(self):
        self.RunTraining(None, False, self.classifiersCrossValAssetPath, '-a', 1)
        self.RunTraining(None, False, self.classifiersCrossValAssetPath, '-b', 2)
        self.RunTraining(None, False, self.classifiersCrossValAssetPath, '-c', 3)
        self.RunTraining(None, False, self.classifiersCrossValAssetPath, '-d', 4)
        self.RunTraining(None, False, self.classifiersCrossValAssetPath, '-e', 5)

    # If all 5 training data files exist, return true.
    def DoesTrainingDataExist(self, newTraining, state):
        if newTraining:
            trainingAssetPath = state.GetAssetName() + "Training/"
            trainingAssets = self.GetAssetList(trainingAssetPath)
            if not trainingAssets:
                return False, 0
            featureCol = None
            for a in trainingAssets["assets"]:
                if featureCol is None:
                    featureCol = ee.FeatureCollection(a["id"])
                else:
                    featureCol = featureCol.merge(ee.FeatureCollection(a["id"]))

            run = 0
            try:
                trainingSize = featureCol.size().getInfo()
                print("training data size: {}".format(trainingSize))
                if trainingSize == 30000:
                    return True, run
                # if trainingSize > 1:
                #     run = 1
                # elif trainingSize > 20000:
                #     run = 2
                if trainingSize > 29000:
                    run = 4
                elif trainingSize > 27000:
                    run = 3
                elif trainingSize > 20000:
                    run = 2
                else:
                    run = 1
                print("Not all trainings exist. {}".format(trainingSize))
            except:
                return False, run
            #     if a["id"] in trlist:
            #         allExist += 1
            # if allExist == 5:
                #return True
            return False, run
        else:
            # Old overall US training classifier
            trainingAssets = self.GetAssetList(self.trainingAssetPath)
            if not trainingAssets:
                return False, 0
            allExist = 0
            trlist = [self.trainingAssetPath + "train1990", self.trainingAssetPath + "train2000", self.trainingAssetPath + "train2006",
                         self.trainingAssetPath + "train2012", self.trainingAssetPath + "train2018"]
            trainlist = []
            # Create a list with all needed files.
            for ta in trlist:
                for i in range(1, 11):
                    if i == 6 and "1990" in ta:
                        continue
                        # for train1990-6 region no data available
                    trainlist.append(ta+'-' + str(i))
            assetlist = trainingAssets["assets"]

            for a in assetlist:
                if a["id"] in trainlist:
                    allExist += 1
            if allExist == 49:
                return True, 0
            return False, 0

    # If classifiers for US CrossValidation exists, true. Else false,.
    def DoClassifiersExistCrossVal(self):
        classifiersAssets = self.GetAssetList(self.classifiersCrossValAssetPath)
        if not classifiersAssets:
            return False

        allExist = 0
        # 5 classifiers need to exist (-a, -b, -c, -d, -e). Each divided in 1990, 2000, 2006, 2012, 2019 and
        # 10 parts of europe. Except year 1990 of region 6, where no data is available due to no Corine data.
        trlist = [self.classifiersCrossValAssetPath + "train1990", self.classifiersCrossValAssetPath + "train2000",
                  self.classifiersCrossValAssetPath + "train2006", self.classifiersCrossValAssetPath + "train2012",
                  self.classifiersCrossValAssetPath + "train2018"]
        trainlist = []
        # Create a list with all needed files.
        for ta in trlist:
            for i in range(1, 11):
                for j in ["a", "b", "c", "d", "e"]:
                    if i == 6 and "1990" in ta:
                        continue
                        # for train1990-6 region no data available
                    trainlist.append(ta + '-' + j + '-' + str(i))
        assetlist = classifiersAssets["assets"]

        for a in assetlist:
            if a["id"] in trainlist:
                trainlist.remove(a["id"])
                allExist += 1
        if allExist == 245:  # 5classifier * (4years * 10 region + 1year * 9regions)
            return True
        return False

    # Gets the trainings data, if they exist, and returns classifier.
    def GetTrainingsData(self, newTraining, state):
        if newTraining:
            trainingAssets = self.GetAssetList(state.GetAssetName() + "Training/")
            if not trainingAssets:
                print("no trainingsdata available, stop")
                return False
            featureCol = None
            for a in trainingAssets["assets"]:
                if featureCol is None:
                    featureCol = ee.FeatureCollection(a["id"])
                else:
                    featureCol = featureCol.merge(ee.FeatureCollection(a["id"]))
            if featureCol.size().getInfo() != 30000:
                print("not all trainingsdata available, stop")
                return False
            bandNamesToTrain = ee.List(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'NDVI', 'NDBI', 'WI'])
            classifierCorine = ee.Classifier.smileRandomForest(10).train(featureCol, 'landcover', bandNamesToTrain)
            return classifierCorine
        else:
            if not self.DoesTrainingDataExist():
                return None

            def getTrainingYearData(year):
                train = ee.FeatureCollection(self.trainingAssetPath+"train"+year+'-1')
                train = train.merge(ee.FeatureCollection(self.trainingAssetPath+"train"+year+'-2'))
                train = train.merge(ee.FeatureCollection(self.trainingAssetPath+"train"+year+'-3'))
                train = train.merge(ee.FeatureCollection(self.trainingAssetPath+"train"+year+'-4'))
                train = train.merge(ee.FeatureCollection(self.trainingAssetPath+"train"+year+'-5'))
                if year != '1990':
                    train = train.merge(ee.FeatureCollection(self.trainingAssetPath+"train"+year+'-6'))
                train = train.merge(ee.FeatureCollection(self.trainingAssetPath+"train"+year+'-7'))
                train = train.merge(ee.FeatureCollection(self.trainingAssetPath+"train"+year+'-8'))
                train = train.merge(ee.FeatureCollection(self.trainingAssetPath+"train"+year+'-9'))
                train = train.merge(ee.FeatureCollection(self.trainingAssetPath+"train"+year+'-10'))

                return train

            train1990 = getTrainingYearData('1990')
            train2000 = getTrainingYearData('2000')
            train2006 = getTrainingYearData('2006')
            train2012 = getTrainingYearData('2012')
            train2018 = getTrainingYearData('2018')

            trainAll = train2018.merge(train2012).merge(train2006).merge(train2000).merge(train1990)

            bandNamesToTrain = ee.List(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'NDVI', 'NDBI', 'WI'])
            classifierCorine = ee.Classifier.smileRandomForest(10).train(trainAll, 'landcover', bandNamesToTrain)

            return classifierCorine

        # Gets the trainings data, if they exist, and returns classifier.

    # Loads 5 classifiers, all created by europe trainings data and Corine landcover. Used in CrossValidation.
    def GetClassifiersCrossVal(self):
        # If classifiers do not exist, return None
        if not self.DoClassifiersExistCrossVal():
            return None

        # Gets the training data for the given seed and given year.
        def getTrainingYearData(year, seed):
            train = ee.FeatureCollection(self.classifiersCrossValAssetPath + "train" + year + seed + '-1')
            train = train.merge(ee.FeatureCollection(self.classifiersCrossValAssetPath + "train" + year + seed + '-2'))
            train = train.merge(ee.FeatureCollection(self.classifiersCrossValAssetPath + "train" + year + seed + '-3'))
            train = train.merge(ee.FeatureCollection(self.classifiersCrossValAssetPath + "train" + year + seed + '-4'))
            train = train.merge(ee.FeatureCollection(self.classifiersCrossValAssetPath + "train" + year + seed + '-5'))
            if year != '1990':
                train = train.merge(ee.FeatureCollection(self.classifiersCrossValAssetPath + "train" + year + seed + '-6'))
            train = train.merge(ee.FeatureCollection(self.classifiersCrossValAssetPath + "train" + year + seed + '-7'))
            train = train.merge(ee.FeatureCollection(self.classifiersCrossValAssetPath + "train" + year + seed + '-8'))
            train = train.merge(ee.FeatureCollection(self.classifiersCrossValAssetPath + "train" + year + seed + '-9'))
            train = train.merge(ee.FeatureCollection(self.classifiersCrossValAssetPath + "train" + year + seed + '-10'))

            return train

        # Creates the classifier for trainings data from all years of a given seed.
        def createClassifier(seed):
            train1990 = getTrainingYearData('1990', seed)
            train2000 = getTrainingYearData('2000', seed)
            train2006 = getTrainingYearData('2006', seed)
            train2012 = getTrainingYearData('2012', seed)
            train2018 = getTrainingYearData('2018', seed)
            trainAll = train2018.merge(train2012).merge(train2006).merge(train2000).merge(train1990)

            bandNamesToTrain = ee.List(['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'NDVI', 'NDBI', 'WI'])
            classifierCorine = ee.Classifier.smileRandomForest(10).train(trainAll, 'landcover', bandNamesToTrain)
            return classifierCorine

        classifiers = []
        classifiers.append(createClassifier("-a"))
        classifiers.append(createClassifier("-b"))
        classifiers.append(createClassifier("-c"))
        classifiers.append(createClassifier("-d"))
        classifiers.append(createClassifier("-e"))

        return classifiers

    # Classifies and exports the data of the next grid cells for the current state.
    def RunNextClassification(self, state):
        classify = Classify()
        classifier = self.GetTrainingsData()
        state.stateDB.gridCells = DriveApi.CheckClassificationProgress(state.GetName(), state.GetGridCells())[0]
        rasterCells = state.GetGridCells()
        tasks = []
        runs = 0
        numbFirstCell = 0.001
        count = 0
        for rcell in rasterCells:
            if rcell[1] is False and runs <= self.RUNPARALLEL:
                if count == 0:
                    # Check for empty cell export in first run of classification and remove them
                    self.RemoveEmptyCells(state)

                smallGrid = ee.FeatureCollection(state.GetAssetName() + 'Grid/grid-' + str(rcell[0]))
                smallGrid = smallGrid.distinct('MGRS')
                runs += 1
                subtasks = classify.DoClassification(smallGrid, classifier, rcell[0], 'MGRS', 1982, 2019, state.GetName(), True)
                tasks.append(subtasks)
                print("{} of {}".format(runs, self.RUNPARALLEL+1))
            else:
                if rcell[1] is True:
                    numbFirstCell += 1
            count += 1
        if runs != 0:
            # Report Progress
            procentFinished = int(numbFirstCell / len(rasterCells) * 100)
            procentInProgress = runs / len(rasterCells) * 100
            print("{}% of classification is progress and {}% finished".format(procentInProgress, procentFinished))
        return tasks

    # Runs the CrossValidation for the given state.
    def RunCrossValidation(self, state):
        classifiers = self.GetClassifiersCrossVal()
        crossVal = CrossValidationUSA(state)
        crossVal.RunCrossValidation(classifiers)
        return None

    # True if no open tasks are pending. Else false.
    def AreTasksFinished(self):
        tasks = ee.data.getTaskList()
        count = 0
        for t in tasks:
            if t.get("state") == 'RUNNING' or t.get("state") == 'READY':
                return False
            count += 1
            if count >= 400:
                return True
        return True

    def RemoveEmptyCells(self, country):
        # Message:      Error: Table is empty.
        tasks = ee.data.getTaskList()
        count = 0
        for t in tasks:
            count += 1
            if count > len(country.stateDB.gridCells) + 500:
                country.Save()
                return False
            elif 'grid-' in t.get("description"):
                if t.get("state") == 'FAILED' and t.get("error_message") == "Table is empty.":
                    cellId = int(t.get("description").split('-')[1])
                    if [cellId, False] in country.countryDB.gridCells:
                        print("Remove Empty Cell {}".format(cellId))
                        country.countryDB.gridCells.remove([cellId, False])
                    else:
                        print("Try to delete Empty Cell {}, but was not found".format(cellId))
        country.Save()
        return True

    def reportPendingTasks(self):
        tasks = ee.data.getTaskList()
        count = 0
        for t in tasks:
            if t.get("state") == 'RUNNING' or t.get("state") == 'READY':
                count += 1
        self.reportStep("{} tasks in progress".format(count))

    def reportStep(self, text):
        print(text)
        logging.info(text)
