#RUN MONGo db
#brew services start mongodb-community@3.6
#wait shortly
#CHECKMONGODB

#RUN MONGO in new terminal:
from ee import EEException
from pymongo import MongoClient
from mongoengine import *
import logging
import ee
from apscheduler.schedulers.blocking import BlockingScheduler
from World.Country import CountryWDB
from World.Country import Country
from World.ExecuterWorld import ExecuterWorld
from Constants import *

# SETUP PARAMETERS
start_year = 1982
end_year = 2024

ee.Initialize()
logging.basicConfig(filename='main.log', level=logging.INFO, format='%(asctime)s %(message)s')
logging.info("------   Start    ------")
client = MongoClient()
connect('landcover-World', host='localhost', port=27017)

# Creates an Asset for the country.
def addNewCountry(name, prio, manualGridCell = []):
    def createStateAsset(countryName):
        assetName = ('users/emap1/Landcover-World/' + countryName).replace(" ", "-").replace("(", "").replace(")", "").replace("'", "").replace("&", "-and-").replace(".", "").replace(",", "")
        try:
            trainingAssets = ee.data.listAssets(
                {"parent": "projects/earthengine-legacy/assets/" + assetName})
        except EEException:
            # If asset does not exist, create one
            ee.data.createAsset({'type': 'Folder'}, assetName)
            ee.data.createAsset({'type': 'Folder'}, assetName + "/Training")
        return None

    post_1 = CountryWDB(
        name=name,
        shapefile=name,
        gridCells=manualGridCell,
        prio=prio,
        hasManualGridCells= (len(manualGridCell)>0),
        hasStarted=False,
        isFinished=False,
    )
    post_1.save()       # This will perform an insert
    createStateAsset(name)
    print("country: {} added".format(name))

#addNewCountry("Barbados", 0)
#addNewCountry("Costa Rica", 1)
#addNewCountry("Nicaragua", 2)
#addNewCountry("Mexico", 3)
#addNewCountry("Honduras", 4)
#addNewCountry("Guatemala", 5)
#addNewCountry("Brazil_Rondonia", 2)
#addNewCountry("Brazil_Acre", 3)
#addNewCountry("Brazil_Amazonas", 4)
#addNewCountry("Brazil_Roraima", 5)
#addNewCountry("Brazil_Para", 6)
#addNewCountry("Brazil_Amapa", 7)
#addNewCountry("Brazil_Tocantins", 8)
#addNewCountry("Brazil_Maranhao", 9)
#addNewCountry("Brazil_Piaui", 10)
#addNewCountry("Brazil_Ceara", 11)
#addNewCountry("Brazil_Rio Grande do Norte", 12)
#addNewCountry("Brazil_Paraiba", 13)
#addNewCountry("Brazil_Pernambuco", 14)
#addNewCountry("Brazil_Alagoas", 15)
#addNewCountry("Brazil_Sergipe", 16)
#addNewCountry("Brazil_Bahia", 17)
#addNewCountry("Brazil_Minas Gerais", 18)
#addNewCountry("Brazil_Espirito Santo", 19)
#addNewCountry("Brazil_Rio de Janeiro", 20)
#addNewCountry("Brazil_Sao Paulo", 21)
#addNewCountry("Brazil_Parana", 1)
#addNewCountry("Brazil_Santa Catarina", 0)
#addNewCountry("Brazil_Rio Grande do Sul", 22)
#addNewCountry("Brazil_Mato Grosso do Sul", 23)
#addNewCountry("Brazil_Mato Grosso", 24)
#addNewCountry("Brazil_Goias", 25)
#addNewCountry("Brazil_Distrito Federal", 26)




countries = []

print(CountryWDB)
for obj in CountryWDB.objects:
    countries.append(Country(obj))

def latlongCellList(long1, long2, lat1, lat2):
    # Get max and min lat and long (in real numbers)
    if lat1 <= lat2:
        n1 = int(lat1)

        n2 = int(lat2)
    else:
        n1 = int(lat2)
        n2 = int(lat1)
    if n1 < 0:
        n1 -= 1
    if n2 > 0:
        n2 += 1
            #ee.Number(ee.Algorithms.If(e1t.gte(e2t), e2t, e1t)).int()
    if long1 <= long2:
        e1 = int(long1)
        e2 = int(long2)
    else:
        e1 = int(long2)
        e2 = int(long1)
    if e1 < 0:
        e1 -= 1
    if n2 > 0:
        e2 += 1

    cellList = []
    i = n1
    while i < n2:
        j = e1
        while j < e2:
            cellList.append("Long:"+str(j)+",Lat:"+str(i))
            j += 1
        i+=1

    return cellList


print("Initialize all countries:")
i = 0
for c in countries:
    # Entries for Brazil offer are an example for region-level classification within a country using a shapefile
    # manually uploaded as an asset to GEE. The shapefile coordinates in GEE have to be manually inserted in the
    # Constants.py file. In addition, in the World/Country.py file, reference to the shapefile has to be added (see
    # line 86 for the example of Brazil. The classification procedure and data output is equivalent to a region-level
    # classification as the one set up as an example in the USA code version.
    if c.GetName() == "Brazil_Rondonia":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'RO'
        c.Save()
    elif c.GetName() == "Brazil_Acre":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'AC'
        c.Save()
    elif c.GetName() == "Brazil_Amazonas":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'AM'
        c.Save()
    elif c.GetName() == "Brazil_Roraima":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'RR'
        c.Save()
    elif c.GetName() == "Brazil_Para":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'PA'
        c.Save()
    elif c.GetName() == "Brazil_Amapa":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'AP'
        c.Save()
    elif c.GetName() == "Brazil_Tocantins":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'TO'
        c.Save()
    elif c.GetName() == "Brazil_Maranhao":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'MA'
        c.Save()
    elif c.GetName() == "Brazil_Piaui":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'PI'
        c.Save()
    elif c.GetName() == "Brazil_Ceara":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'CE'
        c.Save()
    elif c.GetName() == "Brazil_Rio Grande do Norte":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'RN'
        c.Save()
    elif c.GetName() == "Brazil_Paraiba":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'PB'
        c.Save()
    elif c.GetName() == "Brazil_Pernambuco":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'PE'
        c.Save()
    elif c.GetName() == "Brazil_Alagoas":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'AL'
        c.Save()
    elif c.GetName() == "Brazil_Sergipe":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'SE'
        c.Save()
    elif c.GetName() == "Brazil_Bahia":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'BA'
        c.Save()
    elif c.GetName() == "Brazil_Minas Gerais":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'MG'
        c.Save()
    elif c.GetName() == "Brazil_Espirito Santo":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'ES'
        c.Save()
    elif c.GetName() == "Brazil_Rio de Janeiro":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'RJ'
        c.Save()
    elif c.GetName() == "Brazil_Sao Paulo":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'SP'
        c.Save()
    elif c.GetName() == "Brazil_Parana":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'PR'
        c.Save()
    elif c.GetName() == "Brazil_Santa Catarina":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'SC'
        c.Save()
    elif c.GetName() == "Brazil_Rio Grande do Sul":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'RS'
        c.Save()
    elif c.GetName() == "Brazil_Mato Grosso do Sul":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'MS'
        c.Save()
    elif c.GetName() == "Brazil_Mato Grosso":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'MT'
        c.Save()
    elif c.GetName() == "Brazil_Goias":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'GO'
        c.Save()
    elif c.GetName() == "Brazil_Distrito Federal":
        c.SetManualShapefile(SHAPE_STATES_BRAZIL)
        c.CountryWDB.shapefile = 'DF'
        c.Save()
    elif c.GetName() == "Mexico":
        c.CountryWDB.prio = 27
        c.Save()
    elif c.GetName() == "Guatemala":
        c.CountryWDB.prio = 28
        c.Save()
    print("- {}, prio:{} has started {}, has finished {}".format(c.GetName(), c.GetPrio(), c.hasStarted(), c.hasFinished()))

print(countries)

def printProgress(countries):
    print("Fully executed countries:")
    count = 0
    for c in countries:
        if c.hasFinished() and c.hasImages():
            count += 1
            print(c.GetName())
    print("{} countries finished".format(count))

printProgress(countries)

executer = ExecuterWorld(countries, start_year, end_year)
executer.RunNextTask()

def runNext():
    print("... Wake up, schedule next tasks")
    executer.RunNextTask()
    print("Tasks scheduled. Sleep ...")

print("Set scheduler")
scheduler = BlockingScheduler()
scheduler.add_job(runNext, 'interval', hours=0.2)
scheduler.start()



def uploadCountryGrid(path):
    return None


logging.info("------   End    ------")
