import logging
import ee
from ee import EEException
from GridSplitter import GridSplitter
from USA.ImageExporter import ImageExporter
from USA.TrainingUSA import TrainingUSA


class ExecuterUSA:
    def __init__(self, states, startYear=1982, endYear=2021):
        ee.Initialize()
        self.states = states
        self.startYear = startYear
        self.endYear = endYear

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
            if not s.hasFinished() and s.stateDB.prio < minPrio:
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
            print("{} of {} finished".format(truen, celln))

            return False

        # Create setup, if data not yet exist
        doesTrainingsDataExist, trynumber = self.DoesTrainingDataExist(state)
        if not doesTrainingsDataExist:
            # Execute Training for classification, if data does not yet exist
            self.RunTraining(state, trynumber)
            return None

        # Execute next step
        if state is not None and state.hasStarted():
            if len(state.GetGridCells()) == 0 or not state.DoGridCellsExist():
                # Split grid cells if not existing
                self.reportStep("Country: {}, split grid".format(state.GetName()))
                cells = GridSplitter().SplitGrid(state.GetFeature(), state.GetAssetName())
                state.stateDB.gridCells = cells
                state.Save()
                return None
            else:
                # Next classification tasks if no all finished
                if not state.hasImages():
                    imager = ImageExporter()
                    imager.RunImage(state, self.GetTrainingsData(True, state), self.startYear, self.endYear)
                    return None
                else:
                    # Finish state
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
    def RunTraining(self, state, tryNumber):
        b_perc, c_perc, d_perc, e_perc = state.CalculateClimatePercentage()
        trainingCorine = TrainingUSA()
        trainingCorine.ProduceTrainingDataClimate(1990, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber)
        trainingCorine.ProduceTrainingDataClimate(2000, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber)
        trainingCorine.ProduceTrainingDataClimate(2006, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber)
        trainingCorine.ProduceTrainingDataClimate(2012, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber)
        trainingCorine.ProduceTrainingDataClimate(2018, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, tryNumber)

    # If all 5 training data files exist, return true.
    def DoesTrainingDataExist(self, state):
            trainingAssetPath = state.GetTrainingAssetName()
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
            return False, run

    # Gets the trainings data, if they exist, and returns classifier.
    def GetTrainingsData(self, newTraining, state):
        trainingAssets = self.GetAssetList(state.GetTrainingAssetName())
        if not trainingAssets:
            print("no training data available, stop")
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
