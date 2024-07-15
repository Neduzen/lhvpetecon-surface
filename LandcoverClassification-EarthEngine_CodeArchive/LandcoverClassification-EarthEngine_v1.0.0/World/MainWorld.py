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
start_year = 1982
end_year = 2022

ee.Initialize()
logging.basicConfig(filename='main.log', level=logging.INFO, format='%(asctime)s %(message)s')
logging.info("------   Start    ------")
#client = MongoClient()
connect('landcover-World', host='localhost', port=27017)

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
    print("country: {} added".format(name))

#addNewCountry("Chad", 0)
#addNewCountry("Botswana", 0)
#addNewCountry("Namibia", 0)
#addNewCountry("South Africa", 0)
#addNewCountry("Swaziland", 0)
#addNewCountry("Mayotte", 0)
#addNewCountry("Niger", 0)
#addNewCountry("Sudan", 0)
#addNewCountry("Libya", 0)
#addNewCountry("Koualou Area", 0)
#addNewCountry("Tunisia", 0)
#addNewCountry("Egypt", 0)
#addNewCountry("Bir Tawil", 0)
#addNewCountry("Halaib Triangle", 0)
#addNewCountry("Eritrea", 0)
#addNewCountry("Djibouti", 0)
#addNewCountry("Somalia", 0)
#addNewCountry("South Sudan", 0)
#addNewCountry("Abyei Area", 0)
#addNewCountry("Comoros", 0)
#addNewCountry("Madagascar", 0)
#addNewCountry("Cabo Verde", 0)
#addNewCountry("Western Sahara", 0)
#addNewCountry("Mauritania", 0)
#addNewCountry("Morocco", 0)
#addNewCountry("Mali", 0)
#addNewCountry("Cote d’Ivoire", 0)
#addNewCountry("Guinea-Bissau", 0)
#addNewCountry("Liberia", 0)
#addNewCountry("Equatorial Guinea", 0)
#addNewCountry("Sao Tome & Principe", 0)
#addNewCountry("Gabon", 0)
#addNewCountry("Rep of the Congo", 0)
#addNewCountry("Central African Rep", 0)
#addNewCountry("Dem Rep of the Congo", 0)

#addNewCountry("Ukraine", 0)
#addNewCountry("Moldova", 0)
#addNewCountry("Belarus", 0)
#addNewCountry("Afghanistan",1)
#addNewCountry("Armenia",2)
#addNewCountry("Azerbaijan",3)
#addNewCountry("Georgia",4)
#addNewCountry("Kazakhstan",5)
#addNewCountry("Kyrgyzstan",6)
#addNewCountry("Syria",7)
#addNewCountry("Lebanon",8)
#addNewCountry("Guinea", 1)
#addNewCountry("Togo", 2)
#addNewCountry("Uganda", 3)
#addNewCountry("Zimbabwe", 4)
#addNewCountry("Senegal", 0)
#addNewCountry("Nepal", 0)
#addNewCountry("Kenia", 0)
#addNewCountry("Vietnam", 0)
#addNewCountry("Argentina", 0)
#addNewCountry("Nigeria", 0)
#addNewCountry("Cambodia", 0)
#addNewCountry("Mexico", 0)
#addNewCountry("Algeria", 99)
#addNewCountry("Thailand", 0)
#addNewCountry("Uruguay", 0)
#addNewCountry("Mali", 0)
##addNewCountry("Gambia, The", 1)
#addNewCountry("Sierra Leone", 1)
#addNewCountry("Burkina Faso", 1)
##addNewCountry("Côte d’Ivoire", 1)
#addNewCountry("Ghana", 0)
#addNewCountry("Benin", 0)
#addNewCountry("Nigeria", 0)
#addNewCountry("Cameroon", 0)
##addNewCountry("Congo (Kinshasa)", 1)
#addNewCountry("Angola", 0)
#addNewCountry("Ethiopia", 0)
#addNewCountry("Rwanda", 0)
#addNewCountry("Tanzania", 0)
#addNewCountry("Zambia", 0)
#addNewCountry("Burundi", 0)
#addNewCountry("Malawi", 0)
#addNewCountry("Mozambique", 0)
#addNewCountry("Lesotho", 0)
#addNewCountry("Eswatini", 0)
#addNewCountry("Kenya", 2)
#addNewCountry("Qatar", 0)
#addNewCountry("Malaysia", 0)
#addNewCountry("Singapore", 0)
#addNewCountry("Japan", 0)
#addNewCountry("Oman", 0)
#addNewCountry("Bahrain", 2)
#addNewCountry("Kuwait", 2)
#addNewCountry("Yemen", 2)
#addNewCountry("Jordan", 2)
#addNewCountry("Iraq", 0)
#addNewCountry("Iran", 2)
#addNewCountry("Venezuela", 2)
#addNewCountry("Panama", 2)
#addNewCountry("Cuba", 2)
#addNewCountry("Haiti", 1)


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
    elif c.GetName() == "Yemen":
        c.CountryWDB.prio = 1
    elif c.GetName() == "Syria":
        #c.CountryWDB.prio = 99
        c.Save()
    elif c.GetName() == "Burkina Faso":
        c.CountryWDB.prio = 2
        c.Save()
    elif c.GetName() == "Argentina" or c.GetName() == "Cambodia" or c.GetName() == "Mexico":
        #c.CountryWDB.prio = 3
        c.Save()
    elif c.GetName() == "South Africa":
        c.CountryWDB.prio = 2
        c.Save()
    elif c.GetName() == "Japan":
        c.CountryWDB.prio = 2
        c.Save()
    elif c.GetName() == "Kazakhstan":
        c.CountryWDB.prio = 99
        #c.CountryWDB.prio = 99
        c.Save()
    elif c.GetName() == "Gambia":
        c.CountryWDB.prio = 0
        # c.CountryWDB.prio = 99
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
