import logging
import ee
from ee import EEException
from ee.batch import Export

import CorineImages
import SatelliteImages
from Executer import Executer
from Classify import Classify
from Training import Training
from CrossValidation import CrossValidation
import DriveApi
from Country import Country
import gee_asset_manager



#image = ee.Image('srtm90_v4')
# #print(image.getInfo())

class ExecuterMunicipality(Executer):

    RUNPARALLEL = 7

    def RunNextTask(self):
        country = self.GetActualCountry()
        #self.RemoveEmptyCells(country)
        print("ExecuterMunicipality")
        logging.info("Country: {}, run next task".format(country.GetName()))

        if not self.AreTasksFinished():
            # Tasks are still in progress, sleep (nothing to do)
            self.reportStep("Country: {}, tasks still pending, ... Wait".format(country.GetName()))
            self.reportPendingTasks()
            return False

        if country.hasStarted():
            if not country.DoesTrainingDataExist():
                self.reportStep("Country: {}, run training".format(country.GetName()))
                self.RunTraining(country)
            else:
                #self.RemoveEmptyCells(country)
                # TRAINING FINISHED, do next task
                if len(country.GetGridCells()) == 0:
                    self.reportStep("No split of Country: {} available".format(country.GetName()))
                else:
                    # next classification tasks if no all finished
                    if country.IsClassificationFinished() is False:
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
                        # else:
                        #     raise Exception("No valid amount of classification results for country {}.".format(country.name))
                    # else:
                    #     raise Exception("No valid amount of cross validation results for country {}.".format(country.name))
                # else:
                #     raise Exception("No valid amount of grid cells for country {}.".format(country.name))
        else:
            logging.WARNING("No country for next run found")
            raise Exception("NO COUNTRY FOR NEXT RUN")
        self.reportPendingTasks()
        return None

    def RunNextClassification(self, country):
        classify = Classify()
        classifier = country.GetTrainingsData()
        rasterCells = country.GetGridCells()
        tasks = []
        runs = 0
        numbFirstCell = 0.001
        count = 0
        precell = 0
        municipalities = ee.FeatureCollection(country.countryDB.shapefile)
                                              #ee.FeatureCollection("users/emap1/Landcover/Switzerland-Municipality/municipalities-ch")
        # country.GetAssetName() + 'Municipalities')

        for rcell in rasterCells:
            if rcell[1] is False and runs <= self.RUNPARALLEL:
                # TODO SwissMunicipality
                # municipalitiesRun = municipalities.filter(ee.Filter.gt('ZLEVEL', precell))
                # municipalitiesRun = municipalitiesRun.filter(ee.Filter.lte('ZLEVEL', int(rcell[0])))
                # TODO German Municipality
                municipalitiesRun = municipalities.filter(ee.Filter.eq('RUN', rcell[0]))
                # print(municipalitiesRun.size().getInfo())
                runs += 1
                precell = int(rcell[0])
                # TODO gemeinde identifier 1984
                subtasks = classify.DoClassification(municipalitiesRun, classifier, rcell[0], 'DEBKG', 1984, 2021, country.GetName(), True)
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


#