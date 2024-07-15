import logging
import ee
from ee import EEException
from GridSplitter import GridSplitter
from USA.ImageExporter import ImageExporter
from USA.TrainingUSA import TrainingUSA


# Class for automatic executing of the classification of the given US states.
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

        self.reportProgress(state)

        # Wait, if tasks are still pending
        if not self.AreTasksFinished():
            # Tasks are still in progress, sleep (nothing to do)
            name = 'us'
            if state is not None:
                name = state.GetName()
            self.reportStep("State: {}, tasks still pending, ... Wait".format(name))
            self.reportPendingTasks()

            return False

        if state is None or state.hasStarted() is False:
            logging.WARNING("No state for next run found")
            raise Exception("NO state FOR NEXT RUN")

        # Execute Training for classification, if data does not yet exist
        if not self.DoesTrainingDataExist(state):
            self.RunTraining(state)
            return None

        # Split state into grid cells if not existing
        if len(state.GetGridCells()) == 0 or not state.DoGridCellsExist():
            self.reportStep("Country: {}, split grid".format(state.GetName()))
            cells = GridSplitter().SplitGrid(state.GetFeature(), state.GetGridAssetName())
            state.stateDB.gridCells = cells
            state.Save()
            return None

        # Classify next grid cell, if not all are finished
        if not state.hasImages():
            imager = ImageExporter()
            retVal = imager.RunImage(state, self.GetTrainingsData(state), self.startYear, self.endYear)
            if retVal == 0:
                self.RunNextTask()
            return None
        # Finish state
        else:
            self.reportStep("Country: {}, is finished".format(state.GetName()))
            state.stateDB.isFinished = True
            state.Save()
            self.RunNextTask()

        self.reportPendingTasks()
        print('END')
        return None

    # Run Training Data, export training values for the five reference years.
    def RunTraining(self, state):
        size = state.GetTrainSize()
        b_perc, c_perc, d_perc, e_perc = state.CalculateClimatePercentage()
        trainingCorine = TrainingUSA()
        trainingCorine.ProduceTrainingDataClimate(1990, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, size)
        trainingCorine.ProduceTrainingDataClimate(2000, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, size)
        trainingCorine.ProduceTrainingDataClimate(2006, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, size)
        trainingCorine.ProduceTrainingDataClimate(2012, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, size)
        trainingCorine.ProduceTrainingDataClimate(2018, None, state.GetAssetName(), b_perc, c_perc, d_perc, e_perc, size)
        state.DecreaseTrainSize()

    # If all 6000 training sample points per year exist (total 30'000), return true.
    def DoesTrainingDataExist(self, state):
            trainingAssetPath = state.GetTrainingAssetName()
            trainingAssets = self.GetAssetList(trainingAssetPath)
            if not trainingAssets:
                return False
            featureCol = None
            for a in trainingAssets["assets"]:
                if featureCol is None:
                    featureCol = ee.FeatureCollection(a["id"])
                else:
                    featureCol = featureCol.merge(ee.FeatureCollection(a["id"]))

            try:
                trainingSize = featureCol.size().getInfo()
                print("training data size: {}".format(trainingSize))
                if trainingSize == 30000:
                    return True
                    # All finished
                print("Not all trainings exist. {}".format(trainingSize))
            except:
                return False
                print("Not all trainings exist. {}".format(trainingSize))
            return False

    # Gets the trainings data, if they exist, and returns the classifier.
    def GetTrainingsData(self, state):
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

    # Reports the amount of pending tasks
    def reportPendingTasks(self):
        tasks = ee.data.getTaskList()
        count = 0
        for t in tasks:
            if t.get("state") == 'RUNNING' or t.get("state") == 'READY':
                count += 1
        self.reportStep("{} tasks in progress".format(count))

    # Reports a certain text
    def reportStep(self, text):
        print(text)
        logging.info(text)

    # Reports the progress of the state.
    def reportProgress(self, state):
        # report state classification
        celln = 0
        truen = 0
        for cell in state.GetGridCells():
            celln += 1
            if cell[1] is True:
                truen += 1
        print("{} of {} finished".format(truen, celln))
