import logging
import ee
from Classify import Classify
from Training import Training
from CrossValidation import CrossValidation
from ImageExporter import ImageExporter

class Executer:
    def __init__(self, countries, imageExportMode, yearFrom=1982, yearTo=2021):
        ee.Initialize()
        self.countries = countries
        self.imageExportMode = imageExportMode
        self.yearFrom = yearFrom
        self.yearTo = yearTo

    RUNPARALLEL = 12

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

    def RunNextTask(self):
        country = self.GetActualCountry()
        #self.RemoveEmptyCells(country)
        logging.info("Country: {}, run next task".format(country.GetName()))

        if not self.AreTasksFinished():
            # If tasks are still in progress, sleep (nothing to do)
            self.reportStep("Country: {}, tasks still pending, ... Wait".format(country.GetName()))
            self.reportPendingTasks()
            return False

        if country.hasStarted():
            if not country.DoesTrainingDataExist():
                # If no trainingsdata exist, run generation of training data
                self.reportStep("Country: {}, run training".format(country.GetName()))
                self.RunTraining(country)
            else:
                #self.RemoveEmptyCells(country)
                # TRAINING FINISHED, do next task
                if len(country.GetGridCells()) == 0 or not country.DoGridCellsExist():
                    # Split the grid cells
                    self.reportStep("Country: {}, split grid".format(country.GetName()))
                    country.SplitGrid10km()
                else:
                    # next classification tasks if no all finished
                    if self.imageExportMode and country.IsImageExportFinished() is False:
                        # Run image export of classification
                        self.reportStep("Country: {}, run image export".format(country.GetName()))
                        self.RunImageExport(country)
                    elif self.imageExportMode is False and country.IsClassificationFinished() is False:
                        # Generate summary csv files of classification
                        self.reportStep("Country: {}, run classification".format(country.GetName()))
                        self.RunNextClassification(country)
                    else:
                        if not country.DoesCrossValidationExist():
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
        trainingCorine = Training()
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

    def RunNextClassification(self, country):
        classify = Classify()
        classifier = country.GetTrainingsData()
        rasterCells = country.GetGridCells()
        tasks = []
        runs = 0
        numbFirstCell = 0.001
        count = 0
        for rcell in rasterCells:
            if rcell[1] is False and runs <= self.RUNPARALLEL:
                if count == 0:
                    # Check for empty cell export in first run of classification and remove them
                    self.RemoveEmptyCells(country)

                smallGrid = ee.FeatureCollection(country.GetAssetName() + 'Grid/grid-' + str(rcell[0]))
                smallGrid = smallGrid.distinct('SmallCellId')
                runs += 1
                subtasks = classify.DoClassification(smallGrid, classifier, rcell[0], 'SmallCellId', self.yearFrom, self.yearTo, country.GetName(), True)
                tasks.append(subtasks)
            else:
                if rcell[1] is True:
                    numbFirstCell += 1
            count += 1

        if runs != 0:
            procentFinished = int(numbFirstCell / len(rasterCells) * 100)
            procentInProgress = runs / len(rasterCells) * 100
            print("{}% of classification is progress and {}% finished".format(procentInProgress, procentFinished))
        return tasks

    def RunImageExport(self, country):
        country.ManageImageExport()
        imager = ImageExporter()
        # Get next grid cell to export
        for g in country.GetGridCells():
            if g[1] is False:
                cellname = g[0]
                # Get cell area of export
                smallGrid = ee.FeatureCollection(country.GetAssetName() + 'Grid/grid-' + str(cellname))
                smallGrid = smallGrid.distinct('SmallCellId')
                imager.ExportCellImage(country, country.GetTrainingsData(), cellname, smallGrid, self.yearFrom, self.yearTo)
                return None
        print("No grid cell left to export image")
        self.RunNextTask()
        return None

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

    def RemoveEmptyCells(self, country):
        # Message:      Error: Table is empty.
        tasks = ee.data.getTaskList()
        count = 0
        for t in tasks:
            count += 1
            if count > len(country.countryDB.gridCells) + 500:
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



