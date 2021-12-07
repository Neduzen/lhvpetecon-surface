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

# SETUP PARAMETERS
start_year = 2005
end_year = 2021

ee.Initialize()
logging.basicConfig(filename='main.log', level=logging.INFO, format='%(asctime)s %(message)s')
logging.info("------   Start    ------")
#client = MongoClient()
connect('landcover-World', host='localhost', port=27017)

countries = []

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


# sset = "projects/earthengine-legacy/assets/users/emap1/Landcover-USA/Training"
# sset2 = "projects/earthengine-legacy/assets/users/emap1/Landcover-USA/Train2"
# for i in ["2000", "2006", "2012", "2018"]:
#     for j in range(1,9):
#         # if j <= 6:
#         #     print(sset+"/Train"+i+"-"+str(j))
#         #     print(ee.data.deleteAsset(sset+"/train"+i+"-"+str(j)))
#         if j > 6:
#             print(ee.data.deleteAsset(sset2+"/train"+i+"-"+str(j)))
# sset = "projects/earthengine-legacy/assets/users/emap1/Landcover-USA/EuGrid"
# for x in range(1,9):
#     print(ee.data.deleteAsset(sset + "/eugrid-" + str(x)))
#     if x <= 6:
#         print(ee.data.deleteAsset(sset + "/europe-" + str(x)))
# print(ee.data.deleteAsset(sset))
#
#
# print(ee.data.deleteAsset(sset2))
# Delete Asset
# print(ee.data.deleteAsset(sset))
# print(ee.data.deleteAsset("projects/earthengine-legacy/assets/users/emap1/Landcover/"+c.GetName().replace(" ", "-")))

# imageEx = ImageExporter()
# imageEx.RunImage(states)
print("Initialize all countries:")
i = 0
for c in countries:
    if c.GetName() == "Brazil":
        #c.SetManualGridCells(latlongCellList(-54.8, -48.4, -26.5, -22.4))
        # c.CountryWDB.hasImages = False
        # c.CountryWDB.isFinished = False
        # for gc in c.GetGridCells():
        #     gc = (gc[0], False)
        # print(c.GetGridCells())
        c.Save()
    print("- {}, prio:{} has started {}, has finished {}".format(c.GetName(), c.GetPrio(), c.hasStarted(), c.hasFinished()))


def printProgress(countries):
    print("Fully executed states:")
    count = 0
    for c in countries:
        if c.hasFinished() and c.hasImages():
            count += 1
            print(c.GetName())
    print("{} of 51 countries finished".format(count))

printProgress(countries)

executer = ExecuterWorld(countries, start_year, end_year)
executer.RunNextTask()

def runNext():
    print("... Wake up, schedule next tasks")
    executer.RunNextTask()
    print("Tasks scheduled. Sleep ...")

print("Set scheduler")
scheduler = BlockingScheduler()
scheduler.add_job(runNext, 'interval', hours=0.5)
scheduler.start()

# Creates an Asset for the country.
def addNewCountry(name, prio, manualGridCell = []):
    def createStateAsset(countryName):
        assetName = ('users/emap1/Landcover-World/' + countryName).replace(" ", "-")
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
    print("state: {} added".format(name))

#addNewCountry("Guinea", 1)
#addNewCountry("Togo", 2)
#addNewCountry("Uganda", 3)
#addNewCountry("Zimbabwe", 4)
#addNewCountry('Brasil', 1, ["Long-52-Lat-23", "Long-51-Lat-23", "Long-52-Lat-24", "Long-51-Lat-24"])
# stateList = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming']
# i = 4
# for s in stateList:
#     if s == 'California':
#         addNewState(s, 2)
#     elif s == 'Florida':
#         addNewState(s, 1)
#     elif s == 'Illinois':
#         addNewState(s, 3)
#     elif s == 'New York':
#         addNewState(s, 0)
#     else:
#         addNewState(s, i)
#         i = i+1



def uploadCountryGrid(path):
    return None

#addNewCountry('Netherlands', 8)
#addNewCountry('Sweden', 9)
# addNewCountry('Italy', 7)
# addNewCountry('Switzerland', 1)
# addNewCountry('United Kingdom', 2)


# class CountryDB(Document):
#     name = StringField(required=True, max_length=200)
#     shapefile = StringField(required=True)
#     GridCells = StringField(required=True, max_length=50)
#
# print(CountryDB.objects[1].name)
#uk_pages = CountryDB.objects(author__country='uk')

# post_1 = CountryDB(
#     name='Switzerland',
#     shapefile='Switzerland',
#     GridCells='t'
# )
# post_1.save()       # This will perform an insert
# print(post_1.name)
# client = MongoClient()
# db = client['landcover']
#
# posts = db.posts
# post_data = {
#     'name': 'Germany',
#     'shapefile': 'Germany',
#     'GridCells': ''
# }
# result = posts.insert_one(post_data)
# print('One post: {0}'.format(result.inserted_id))

# bills_post = posts.find_one({'name': 'Germany'})
# print(bills_post)

logging.info("------   End    ------")
