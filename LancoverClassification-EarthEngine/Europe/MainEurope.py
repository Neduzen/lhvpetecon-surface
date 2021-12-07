#RUN MONGo db
#brew services start mongodb-community@3.6
#wait shortly
#CHECKMONGODB

#RUN MONGO in new terminal:
from ee import EEException
from mongoengine import *
from Europe.Country import *
from Europe.ExecuterEurope import *
import logging
import ee
from apscheduler.schedulers.blocking import BlockingScheduler

ee.Initialize()
logging.basicConfig(filename='main.log', level=logging.INFO, format='%(asctime)s %(message)s')
logging.info("------   Start    ------")
connect('landcover', host='localhost', port=27017)

countries = []

for obj in CountryDB.objects:
    countries.append(Country(obj))

print("Initialize all countries:")


# Changes some things
def InitialSetup():
    for c in countries:
        if c.GetName() == 'Switzerland' or c.GetName() == 'Germany' or c.GetName() == 'United Kingdom' or c.GetName() == 'Spain' or c.GetName() == 'Andorra' or c.GetName() == 'France' or c.GetName() == 'Italy' or c.GetName() == 'Netherlands' or c.GetName() == 'Luxembourg':
            gridlist = []
            # c.countryDB.prio = 9
            # c.Save()
            # Rerun whole country: Remove files from drive, set country to not finished, set all gridcells to false
            # c.countryDB.hasStarted = True
            # c.countryDB.isFinished = False
            # for g in c.countryDB.gridCells:
            #     g[1] = False
            # c.Save()
        elif c.GetName() == 'Germany':
            gridlist = []
            # Rerun whole country: Remove files from drive, set country to not finished, set all gridcells to false
            # c.countryDB.isFinished = False
            # for g in c.countryDB.gridCells:
            #     g[1] = False
            # c.Save()
        elif c.GetName() == 'United Kingdom':
            gridlist = []
            # c.countryDB.prio = 2
            #c.countryDB.GridCells.remove(['29400', False])
            # Rerun whole country: Remove files from drive, set country to not finished, set all gridcells to false
            # c.countryDB.isFinished = False
            # for g in c.countryDB.gridCells:
            #     g[1] = False
            # c.Save()
        elif c.GetName() == 'Bosnia Herzegovina':
            #c.countryDB.shapefile = "Bosnia & Herzegovina"
            a = 0
            # c.countryDB.isFinished = True
            # for e in c.GetGridCells():
            #     e[1] = False
            #c.Save()
            # print(c.GetGridCells())
        else:
            gridlist = []
            # c.countryDB.hasAllCorine = False
            # c.Save()
        print("- {}, prio:{} has started {}, has finished {}".format(c.GetName(), c.GetPrio(), c.hasStarted(), c.hasFinished()))

InitialSetup()

executer = ExecuterEurope(countries, True, 1984, 2021)
executer.RunNextTask()

def runNext():
    print("... Wake up, schedule next tasks")
    executer.RunNextTask()
    print("Tasks scheduled. Sleep ...")

scheduler = BlockingScheduler()
scheduler.add_job(runNext, 'interval', hours=0.2)
scheduler.start()

def addNewCountry(name, prio):
    hasAllCorineYears = True
    notAllCorine = ['Switzerland', 'United Kingdom', 'Norway', 'Sweden', 'Iceland', 'Finland', 'Bosnia & Herzegovina', 'Albania', 'Macedonia', 'Kosovo']
    if name in notAllCorine:
        hasAllCorineYears = False
    post_1 = CountryDB(
        name=name,
        shapefile=name,
        gridCells=[],
        prio=prio,
        hasStarted=False,
        isFinished=False,
        isEu=True,
        hasAllCorine=hasAllCorineYears
    )
    post_1.save()       # This will perform an insert
    createCountryAsset(name)
    print("country: {} added".format(name))

# Creates an Asset for the country.
def createCountryAsset(countryName):
    assetName = ('users/patricklehnert/Landcover/' + countryName).replace(" ", "-")
    try:
        trainingAssets = ee.data.listAssets(
            {"parent": "projects/earthengine-legacy/assets/" + assetName})
    except EEException:
        # If asset does not exist, create one
        ee.data.createAsset({'type': 'Folder'}, assetName)
    return None

# addNewCountry('Switzerland', 0)
# addNewCountry('Germany', 1)
# addNewCountry('United Kingdom', 2)
# addNewCountry('Portugal', 3)
# addNewCountry('Spain', 4)
# addNewCountry('Andorra',5)
# addNewCountry('France', 6)
# addNewCountry('Italy', 7)
# addNewCountry('Netherlands', 8)
# addNewCountry('Sweden', 9)
# addNewCountry('Belgium', 10)
# addNewCountry('Luxembourg', 11)
# addNewCountry('Liechtenstein', 12)
# addNewCountry('Austria', 13)
# addNewCountry('Denmark', 14)
# addNewCountry('Norway', 15)
# addNewCountry('Iceland', 16)
# addNewCountry('Ireland', 17)
# addNewCountry('Finland', 18)
# addNewCountry('Poland', 19)
# addNewCountry('Czechia', 20)
# addNewCountry('San Marino', 21)
# addNewCountry('Lithuania', 22)
# addNewCountry('Estonia', 23)
# addNewCountry('Latvia', 24)
# addNewCountry('Croatia', 25)
# addNewCountry('Greece', 26)
# addNewCountry('Malta', 27)
# addNewCountry('Slovakia', 28)
# addNewCountry('Hungary', 29)
# addNewCountry('Slovenia', 30)
# addNewCountry('Bosnia Herzegovina', 31)
# addNewCountry('Serbia', 32)
# addNewCountry('Montenegro', 33)
# addNewCountry('Kosovo', 34)
# addNewCountry('Albania', 35)
# addNewCountry('Macedonia', 36)
# addNewCountry('Bulgaria', 37)
# addNewCountry('Romania', 38)
# addNewCountry('Cyprus', 39)
# addNewCountry('Faroe Is', 40)
# addNewCountry('Gibraltar', 41)
# addNewCountry('Turkey', 42)


logging.info("------   End    ------")
