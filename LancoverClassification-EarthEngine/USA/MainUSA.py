#RUN MONGo db
#brew services start mongodb-community@3.6
#wait shortly
#CHECKMONGODB

#RUN MONGO in new terminal:
from USA.State import *
import logging
import ee
from apscheduler.schedulers.blocking import BlockingScheduler
from USA.ExecuterUSA import ExecuterUSA

################################################################
# SETUP PARAMETERS
start_year = 2005
end_year = 2021
assetName = ""
################################################################

ee.Initialize()
logging.basicConfig(filename='main.log', level=logging.INFO, format='%(asctime)s %(message)s')
logging.info("------   Start    ------")
#client = MongoClient()
connect('landcover-USA', host='localhost', port=27017)

states = []

for obj in StateDB.objects:
    states.append(State(obj))

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
print("Initialize all states:")
i = 0
for c in states:
    #c.stateDB.isFinished = False
    #c.stateDB.hasImages = False
    c.Save()
    if c.GetName() == 'Florida':
        c.stateDB.prio = 8
    elif c.GetName() == 'New York':
        c.stateDB.prio= 3
    elif c.GetName() == 'California':
        c.stateDB.prio = 2
    elif c.GetName() == 'Massachusetts':
        c.stateDB.prio = 12
    elif c.GetName() == 'Connecticut':
        c.stateDB.prio = 4
    elif c.GetName() == 'Pennsylvania':
        c.stateDB.prio = 5
    elif c.GetName() == 'New Jersey':
        c.stateDB.prio = 6
    elif c.GetName() == 'Illinois':
        c.stateDB.prio = 7
    elif c.GetName() == 'North Carolina':
        c.stateDB.prio = 8
    elif c.GetName() == 'Maryland':
        c.stateDB.prio = 9
    elif c.GetName() == 'Tennessee':
        c.stateDB.prio = 1
    elif c.GetName() == 'Ohio':
        c.stateDB.prio = 10
    elif c.GetName() == 'Utah':
        c.stateDB.prio = 11
    elif c.GetName() == 'Texas':
        c.stateDB.prio = 0
        c.stateDB.hasImages = True
        c.stateDB.isFinished = True
        c.Save()
    elif c.GetName() == 'Michigan':
        c.stateDB.prio = 11
    elif c.GetName() == 'Colorado':
        c.stateDB.prio = 13
    elif c.GetName() == 'Arizona':
        c.stateDB.prio = 14
    elif c.GetName() == 'Virginia':
        c.stateDB.prio = 15
    elif c.GetName() == 'Wisconsin':
        c.stateDB.prio = 16
    elif c.GetName() == 'Indiana':
        c.stateDB.prio = 17
    elif c.GetName() == 'Minnesota':
        c.stateDB.prio = 18
    elif c.GetName() == 'Missouri':
        c.stateDB.prio = 19
    elif c.GetName() == 'Kansas':
        c.stateDB.prio = 20
    elif c.GetName() == 'Georgia':
        c.stateDB.prio = 21
    elif c.GetName() == 'Alabama':
        c.stateDB.prio = 22
    elif c.GetName() == 'Louisiana':
        c.stateDB.prio = 23
    elif c.GetName() == 'Arkansas':
        c.stateDB.prio = 24
    elif c.GetName() == 'Mississippi':
        c.stateDB.prio = 25
    elif c.GetName() == 'West Virginia':
        c.stateDB.prio = 26
    elif c.GetName() == 'Alabama':
        c.stateDB.prio = 27
    elif c.GetName() == 'South Carolina':
        c.stateDB.prio = 28
    elif c.GetName() == 'Kentucky':
        c.stateDB.prio = 29
    elif c.GetName() == 'Hawaii':
        c.stateDB.prio = 51
    elif c.stateDB.prio <= 29:
        c.stateDB.prio = 30
    elif c.stateDB.name == "Alaska":
        c.stateDB.isFinished = True

        #c.stateDB.gridCells = [('17RKP', False),( '17RKN', False),( '17RLM', False),( '17RLL', False),( '17RLK', False),( '17RLH', False),( '17RLP', False),( '17RLN', False),( '16RDV', False),( '16RDU', False),( '17RMM', False),( '17RML', False),( '17RMK', False),( '17RMJ', False),( '17RMH', False),( '17RMQ', False),( '17RMP', False),( '17RMN', False),( '16REV', False),( '16REU', False),( '17RNM', False),( '17RNL', False),( '17RNK', False),( '17RNJ', False),( '17RNH', False),( '17RNN', False),( '16RFV', False),( '16RFU', False),( '16RFT', False),( '16RGV', False),( '16RGU', False),( '16RGT', False)]
        # c.stateDB.prio = 52
        # c.stateDB.save()
        # # gridlist = []
        #c.IsClassificationFinished()
        # c.countryDB.hasAllCorine = True
        # c.Save()
        # c.countryDB.shapefile = "GM"
        # cell100Id =[4028, 4029, 4030, 4031, 4032, 4033, 4127, 4128, 4129, 4130, 4131, 4132, 4133, 4134, 4227, 4228, 4229, 4230, 4231, 4232, 4233, 4234, 4235, 4326, 4327, 4328, 4329, 4330, 4331, 4332, 4333, 4334, 4335, 4426, 4427, 4428, 4429, 4430, 4431, 4432, 4433, 4434, 4527, 4528, 4529, 4530, 4531, 4532, 4533, 4534, 4535, 4628, 4630, 4631, 4632, 4633, 4634];
        # for g in c.countryDB.gridCells:
        #        g[1] = False
        # c.countryDB.gridCells = []
        #c.countryDB.isFinished =
        #c.Save()
    # elif c.GetName() == "United Kingdom":
    #     c.countryDB.delete()
    else:
        gridlist = []
        c.stateDB.prio = 52
        # c.countryDB.hasAllCorine = False
        c.Save()
    c.Save()
    print("- {}, prio:{} has started {}, has finished {}".format(c.GetName(), c.GetPrio(), c.hasStarted(), c.hasFinished()))

def printProgress(states):
    print("Fully executed states:")
    count = 0
    for c in states:
        if c.hasFinished() and c.hasImages():
            count += 1
            print(c.GetName())
    print("{} of 51 states finished".format(count))

printProgress(states)

executer = ExecuterUSA(states)
executer.RunNextTask()

def runNext():
    print("... Wake up, schedule next tasks")
    executer.RunNextTask()
    print("Tasks scheduled. Sleep ...")

scheduler = BlockingScheduler()
scheduler.add_job(runNext, 'interval', hours=0.5)
scheduler.start()

# Creates an Asset for the country.
def addNewState(name, prio):
    def createStateAsset(stateName):
        assetName = ('users/emap1/Landcover-USA/' + stateName).replace(" ", "-")
        try:
            trainingAssets = ee.data.listAssets(
                {"parent": "projects/earthengine-legacy/assets/" + assetName})
        except EEException:
            # If asset does not exist, create one
            ee.data.createAsset({'type': 'Folder'}, assetName)
            ee.data.createAsset({'type': 'Folder'}, assetName + "/Grid")
        return None

    post_1 = StateDB(
        name=name,
        shapefile=name,
        gridCells=[],
        prio=prio,
        hasStarted=False,
        isFinished=False,
    )
    post_1.save()       # This will perform an insert
    createStateAsset(name)
    print("state: {} added".format(name))

# addNewState('Alabama', 4)
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
