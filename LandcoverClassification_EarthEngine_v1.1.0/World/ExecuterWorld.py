import logging
import ee
from ee import EEException
from GridSplitter import GridSplitter
from World.ImageExporter import ImageExporter
from World.TrainingWorld import TrainingWorld


# Class for automatic executing of the classification of the given countries.
class ExecuterWorld:
    def __init__(self, states, start_year=1982, end_year=2024):
        ee.Initialize()
        self.states = states
        self.assetPath = 'users/patricklehnert/Landcover-World/'
        self.classifiersCrossValAssetPath = self.assetPath + 'TrainCrossVal/'
        self.start_year = start_year
        self.end_year = end_year

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

    # Gets the actual country to execute next tasks.
    # Next state to execute is the country with the lowest priority which is not yet finished.
    def GetActualState(self):
        actualState = None
        minPrio = 100
        for s in self.states:
            if not (s.hasFinished() and s.hasImages()) and s.CountryWDB.prio < minPrio:
                minPrio = s.CountryWDB.prio
                actualState = s

        if actualState is None:
            logging.warning("No country found to execute")
            return None
        print("Actual state: {}".format(actualState.GetName()))
        actualState.CountryWDB.hasStarted = True
        actualState.Save()
        return actualState

    # Get the ongoing country and executes the next tasks according to the procedure.
    # Are no tasks ongoing, create training data, split grid, classify next cells.
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
            print("{} of {} finished".format(truen, celln))
            return False

        # Create training data, if data not yet exist
        if self.DoesTrainingDataExist(country) == False:
            country.CreateAsset()
            # Execute Training for classification, if data does not yet exist
            self.RunTraining(country)
            return None

        # Split country into different lat/long grid cells, if grid cells do not yet exist
        if len(country.GetGridCells()) == 0 or not country.DoGridCellsExist():
            self.reportStep("Country: {}, split grid".format(country.GetName()))
            manualCells = []
            if country.CountryWDB.hasManualGridCells:
                manualCells = country.GetGridCells
            country.CountryWDB.gridCells = GridSplitter().SplitGrid(country.GetFeature(), country.GetGridPath(), manualCells)
            country.Save()
            return None

        # Classify the next grid cells, if country not all images exist.
        if not country.hasImages():
            imageExporter = ImageExporter()
            imageExporter.RunImage(country, self.GetTrainingsData(country), self.start_year, self.end_year)
            return None

        # If everything of a country exists, mark it as finished
        else:
            self.reportStep("Country: {}, is finished".format(country.GetName()))
            country.CountryWDB.isFinished = True
            country.Save()
            self.RunNextTask()

        self.reportPendingTasks()
        print('END')
        return None

    # Creates trainings data for the country and export training values for the
    # five reference years (1990, 2000, 2006, 2012, 2018).
    def RunTraining(self, country, extension='', seed=0):
        trainingAssets = self.GetAssetList(country.GetAssetName() + "Training/")
        # Gets the limit of satelite images per year (due to GEE overflow problem), will be decreased after every failed run.
        imageLimit = country.GetTrainSize()
        # Calculates the percentage of the climate zones of the country
        b_perc, c_perc, d_perc, e_perc = country.CalculateClimatePercentage()

        # Produces training data for the five years based with corine
        trainingCorine = TrainingWorld()
        trainingCorine.ProduceTrainingDataClimate(1990, None, country.GetAssetName(), b_perc, c_perc, d_perc, e_perc, imageLimit, trainingAssets)
        trainingCorine.ProduceTrainingDataClimate(2000, None, country.GetAssetName(), b_perc, c_perc, d_perc, e_perc, imageLimit, trainingAssets)
        trainingCorine.ProduceTrainingDataClimate(2006, None, country.GetAssetName(), b_perc, c_perc, d_perc, e_perc, imageLimit, trainingAssets)
        trainingCorine.ProduceTrainingDataClimate(2012, None, country.GetAssetName(), b_perc, c_perc, d_perc, e_perc, imageLimit, trainingAssets)
        trainingCorine.ProduceTrainingDataClimate(2018, None, country.GetAssetName(), b_perc, c_perc, d_perc, e_perc, imageLimit, trainingAssets)

        # Decreases the train size, so that if execution fails, next time less images are analyzed and potentially no failure occurs.
        country.DecreaseTrainsSize()

        return None

    # If all training data files exist, return true.
    # 30'000 data points are needed.
    def DoesTrainingDataExist(self, country):
        trainingAssetPath = country.GetAssetName() + "Training/"
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

    # Gets the trainings data, if they exist, and generates a random forest classifier.
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
        # Create random forest classifier based on training data of the selected channels.
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

    # Checks how many task are pending and reports it.
    def reportPendingTasks(self):
        tasks = ee.data.getTaskList()
        count = 0
        for t in tasks:
            if t.get("state") == 'RUNNING' or t.get("state") == 'READY':
                count += 1
        self.reportStep("{} tasks in progress".format(count))

    # Logs and reports the given text.
    def reportStep(self, text):
        print(text)
        logging.info(text)
