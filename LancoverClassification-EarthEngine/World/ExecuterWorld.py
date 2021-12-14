import logging
import ee
from ee import EEException

from GridSplitter import GridSplitter
from World.ImageExporter import ImageExporter
from World.TrainingWorld import TrainingWorld
from World.CrossValidationWorld import CrossValidationWorld


class ExecuterWorld:
    def __init__(self, states, start_year=1983, end_year=2021):
        ee.Initialize()
        self.states = states
        self.assetPath = 'users/emap1/Landcover-World/'
        self.classifiersCrossValAssetPath = self.assetPath + 'TrainCrossVal/'
        self.start_year = start_year
        self.end_year = end_year
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
            if not (s.hasFinished() and s.hasImages()) and s.CountryWDB.prio < minPrio:
                minPrio = s.CountryWDB.prio
                actualState = s
        if actualState is None:
            logging.warning("No actual state found")
            return None
        print("Actual state: {}".format(actualState.GetName()))
        actualState.CountryWDB.hasStarted = True
        actualState.Save()
        return actualState

    # Runs the next tasks for the actual state and actual progress. Identifies and launches next tasks.
    def RunNextTask(self):
        country = self.GetActualState()
        if country is not None:
            logging.info("Country: {}, run next task".format(country.GetName()))
        else:
            self.reportStep('No actual country found.')

        self.GetAssetList(self.assetPath)

        # Wait, if tasks are still pending
        if not self.AreTasksFinished():
            # Tasks are still in progress, sleep (nothing to do)
            name = 'No country'
            if country is not None:
                name = country.GetName()
            self.reportStep("State: {}, tasks still pending, ... Wait".format(name))
            self.reportPendingTasks()

            # report country classification
            celln = 0
            truen = 0
            for cell in country.GetGridCells():
                celln += 1
                if cell[1] is True:
                    truen += 1
            print("{} of {} finished, {} in progress".format(truen, celln, self.RUNPARALLEL))
            return False

        # Create setup, if data not yet exist
        doesTrainingsDataExist, trynumber = self.DoesTrainingDataExist(country)
        if not doesTrainingsDataExist:
            country.CreateAsset()
            # Execute Training for classification, if data does not yet exist
            self.RunTraining(country, trynumber)
            return None
        if len(country.GetGridCells()) == 0 or not country.DoGridCellsExist():
            self.reportStep("Country: {}, split grid".format(country.GetName()))
            manualCells = []
            if country.CountryWDB.hasManualGridCells:
                manualCells = country.GetGridCells
            country.CountryWDB.gridCells = GridSplitter().SplitGrid(country.GetFeature(), country.GetGridPath, manualCells)
            country.Save()
            return None
        # If country has not yet all images, export further cells
        if not country.hasImages():
            imageExporter = ImageExporter()
            imageExporter.RunImage(country, self.GetTrainingsData(country), self.start_year, self.end_year)
            return None
        if False:#not self.DoClassifiersExistCrossVal():
            # Execute Training for CrossValidation, if does not yet exist.
            self.RunTrainingCrossVal()
            return None
        # Run CrossValidation if Classification for country is finished
        elif False:#not country.DoesCrossValidationExist()
            # :
            self.reportStep("Country: {}, run cross validation".format(country.GetName()))
            self.RunCrossValidation(country)
        # State is finished
        else:
            self.reportStep("Country: {}, is finished".format(country.GetName()))
            country.CountryWDB.isFinished = True
            country.Save()
            self.RunNextTask()

        self.reportPendingTasks()
        print('END')
        return None

    # Run Training Data, export training values for the five reference years.
    def RunTraining(self, country, tryNumber, extension='', seed=0):
        trainingAssets = self.GetAssetList(country.GetAssetName() + "Training/")
        b_perc, c_perc, d_perc, e_perc = country.CalculateClimatePercentage()
        trainingCorine = TrainingWorld()
        trainingCorine.ProduceTrainingDataClimate(1990, None, country.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber, trainingAssets)
        trainingCorine.ProduceTrainingDataClimate(2000, None, country.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber, trainingAssets)
        trainingCorine.ProduceTrainingDataClimate(2006, None, country.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber, trainingAssets)
        trainingCorine.ProduceTrainingDataClimate(2012, None, country.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber, trainingAssets)
        trainingCorine.ProduceTrainingDataClimate(2018, None, country.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber, trainingAssets)

    # Runs the Training Data 5 times independently, in order 5 training classifiers exist for the cross validation
    def RunTrainingCrossVal(self):
        self.RunTraining(None, self.classifiersCrossValAssetPath, '-a', 1)
        self.RunTraining(None, self.classifiersCrossValAssetPath, '-b', 2)
        self.RunTraining(None, self.classifiersCrossValAssetPath, '-c', 3)
        self.RunTraining(None, self.classifiersCrossValAssetPath, '-d', 4)
        self.RunTraining(None, self.classifiersCrossValAssetPath, '-e', 5)

    # If all training data files exist, return true.
    def DoesTrainingDataExist(self, country):
        trainingAssetPath = country.GetAssetName() + "Training/"
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
                # All finished
            if trainingSize > 29000:
                run = 6
            elif trainingSize > 28000:
                run = 5
            elif trainingSize > 27000:
                run = 4
            elif trainingSize > 24000:
                run = 3
            elif trainingSize > 20000:
                run = 2
            else:
                run = 1
            print("Not all trainings exist. {}".format(trainingSize))
        except:
            return False, run
        return False, run

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
    def GetTrainingsData(self, state):
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
    # def RunNextClassification(self, country):
    #     classify = Classify()
    #     classifier = self.GetTrainingsData()
    #     country.CountryWDB.gridCells = DriveApi.CheckClassificationProgress(country.GetName(), country.GetGridCells())[0]
    #     rasterCells = country.GetGridCells()
    #     tasks = []
    #     runs = 0
    #     numbFirstCell = 0.001
    #     count = 0
    #     for rcell in rasterCells:
    #         if rcell[1] is False and runs <= self.RUNPARALLEL:
    #             if count == 0:
    #                 # Check for empty cell export in first run of classification and remove them
    #                 self.RemoveEmptyCells(country)
    #             cellID = rcell[0]
    #             gridShape = ee.FeatureCollection(country.GetAssetName() + 'Grid/Grid')
    #             gridShape = gridShape.filter(ee.Filter.eq('CellID', cellID))
    #             runs += 1
    #             subtasks = classify.DoClassification(gridShape, classifier, cellID, 'MGRS', 1982, 2019, country.GetName(), True)
    #             tasks.append(subtasks)
    #             print("{} of {}".format(runs, self.RUNPARALLEL+1))
    #         else:
    #             if rcell[1] is True:
    #                 numbFirstCell += 1
    #         count += 1
    #     if runs != 0:
    #         # Report Progress
    #         procentFinished = int(numbFirstCell / len(rasterCells) * 100)
    #         procentInProgress = runs / len(rasterCells) * 100
    #         print("{}% of classification is progress and {}% finished".format(procentInProgress, procentFinished))
    #     return tasks

    # Runs the CrossValidation for the given state.
    def RunCrossValidation(self, country):
        classifiers = self.GetClassifiersCrossVal()
        crossVal = CrossValidationWorld(country)
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
