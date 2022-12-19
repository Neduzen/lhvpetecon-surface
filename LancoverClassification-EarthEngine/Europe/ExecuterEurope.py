import logging
import ee
from Europe.TrainingEurope import TrainingEurope
from CrossValidation import CrossValidation
from Europe.ImageExporter import ImageExporter
from GridSplitter import GridSplitter


class ExecuterEurope:
    def __init__(self, countries, imageExportMode, yearFrom=1982, yearTo=2021):
        ee.Initialize()
        self.countries = countries
        self.imageExportMode = imageExportMode
        self.yearFrom = yearFrom
        self.yearTo = yearTo

    # Get country to execute
    def GetActualCountry(self):
        actualCountry = None
        minPrio = 100
        for c in self.countries:
            if not c.hasFinished() and c.countryDB.prio < minPrio:
                minPrio = c.countryDB.prio
                actualCountry = c
        if actualCountry is None:
            logging.warning("No actual country found")
            return None

        actualCountry.countryDB.hasStarted = True
        actualCountry.Save()
        return actualCountry

    # Run next task for the country
    def RunNextTask(self):
        country = self.GetActualCountry()
        logging.info("Country: {}, run next task".format(country.GetName()))

        if not self.AreTasksFinished():
            # If tasks are still in progress, sleep (nothing to do)
            self.reportStep("Country: {}, tasks still pending, ... Wait".format(country.GetName()))
            self.reportPendingTasks()
            return False

        if country.hasStarted():
            if not country.DoesTrainingDataExist():
                # If no trainings data exist, run generation of training data
                self.reportStep("Country: {}, run training".format(country.GetName()))
                self.RunTraining(country)
            else:
                # TRAINING FINISHED, do next task
                if len(country.GetGridCells()) == 0 or not country.DoGridCellsExist():
                    # Split grid cells if not existing
                    self.reportStep("Country: {}, split grid".format(country.GetName()))
                    cells = GridSplitter().SplitGrid(country.GetFeature(), country.GetGridName())
                    country.countryDB.gridCells = cells
                    country.Save()
                    return None
                else:
                    if country.IsImageExportFinished() is False:
                        # Run image export of classification
                        imageExporter = ImageExporter()
                        imageExporter.RunImage(country, self.GetTrainingsData(country), self.start_year, self.end_year)
                        return None
                    else:
                        if not country.DoesCrossValidationExist():
                            # Run cross validation
                            self.reportStep("Country: {}, run cross validation".format(country.GetName()))
                            self.RunCrossValidation(country)
                        else:
                            # Country is finished
                            self.reportStep("Country: {}, is finished".format(country.GetName()))
                            country.countryDB.isFinished = True
                            country.Save()
                            self.GetActualCountry()
                            self.RunNextTask()
        else:
            logging.WARNING("No country for next run found")
            raise Exception("NO COUNTRY FOR NEXT RUN")
        self.reportPendingTasks()
        return None

    def RunTraining(self, country):
        tasks = []
        trainingCorine = TrainingEurope()
        trainingAssetName = country.GetAssetName() + "Training/"
        # Run Training Data, export training values for the five reference years.
        if country.hasAllCorine():
            sampleNumbers = 1000
            tasks.append(trainingCorine.ProduceTrainingDataEu(country.GetFeature(), 1990, None, trainingAssetName, sampleNumbers))
            tasks.append(trainingCorine.ProduceTrainingDataEu(country.GetFeature(), 2000, None, trainingAssetName, sampleNumbers))
            tasks.append(trainingCorine.ProduceTrainingDataEu(country.GetFeature(), 2006, None, trainingAssetName, sampleNumbers))
            tasks.append(trainingCorine.ProduceTrainingDataEu(country.GetFeature(), 2012, None, trainingAssetName, sampleNumbers))
            tasks.append(trainingCorine.ProduceTrainingDataEu(country.GetFeature(), 2018, None, trainingAssetName, sampleNumbers))
        else:
            sampleNumbers = 1250
            tasks.append(trainingCorine.ProduceTrainingDataEu(country.GetFeature(), 2000, None, trainingAssetName, sampleNumbers))
            tasks.append(trainingCorine.ProduceTrainingDataEu(country.GetFeature(), 2006, None, trainingAssetName, sampleNumbers))
            tasks.append(trainingCorine.ProduceTrainingDataEu(country.GetFeature(), 2012, None, trainingAssetName, sampleNumbers))
            tasks.append(trainingCorine.ProduceTrainingDataEu(country.GetFeature(), 2018, None, trainingAssetName, sampleNumbers))
            return tasks

    def RunCrossValidation(self, country):
        crossVal = CrossValidation(country)
        crossVal.RunCrossValidation()
        return None

    # True if no open tasks are pending. Else false.
    def AreTasksFinished(self):
        tasks = ee.data.getTaskList()
        count = 0
        for t in tasks:
            if t.get("state") == 'RUNNING' or t.get("status") == 'READY':
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



