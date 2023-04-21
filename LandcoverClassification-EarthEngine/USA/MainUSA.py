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
from Constants import ASSETPATH_US

################################################################
# SETUP PARAMETERS
start_year = 1983
end_year = 2021
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
        # c.stateDB.gridCells = []
        # c.stateDB.hasImages = False
        # c.stateDB.isFinished = False
    elif c.GetName() == 'Massachusetts':
        c.stateDB.prio = 12
    elif c.GetName() == 'Connecticut':
        c.stateDB.prio = 4
        c.stateDB.hasStarted = True
        c.stateDB.hasImages = True
        c.stateDB.isFinished = True
    elif c.GetName() == 'Pennsylvania':
        c.stateDB.prio = 5
        c.stateDB.hasStarted = True
        c.stateDB.hasImages = True
        c.stateDB.isFinished = True
    elif c.GetName() == 'Tennessee2':
        c.stateDB.hasStarted = True
        c.stateDB.hasImages = True
        c.stateDB.isFinished = True
        c.Save()
    elif c.GetName() == 'New Jersey':
        c.stateDB.prio = 6
        c.stateDB.hasStarted = True
        c.stateDB.hasImages = True
        c.stateDB.isFinished = True
    elif c.GetName() == 'Illinois':
        c.stateDB.prio = 7
        c.stateDB.hasStarted = True
        c.stateDB.hasImages = True
        c.stateDB.isFinished = True
    elif c.GetName() == 'North Carolina':
        c.stateDB.prio = 8
    elif c.GetName() == 'Maryland':
        c.stateDB.prio = 9
    elif c.GetName() == 'Tennessee':
        c.stateDB.prio = 1
        c.stateDB.hasStarted = True
        c.stateDB.hasImages = True
        c.stateDB.isFinished = True
    elif c.GetName() == 'Ohio':
        c.stateDB.prio = 10
    elif c.GetName() == 'Utah':
        c.stateDB.prio = 11
    elif c.GetName() == 'Texas':
        c.stateDB.prio = 0
        c.stateDB.hasStarted = True
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
        c.stateDB.prio = 60
    elif c.stateDB.prio <= 29:
        c.stateDB.prio = 30
    elif c.stateDB.name == "Alaska":
        c.stateDB.isFinished = False
        c.stateDB.prio = 0
        c.stateDB.hasStarted = False
        c.stateDB.hasImages = False
        c.Save()
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
scheduler.add_job(runNext, 'interval', hours=0.15)
print("Sleep")
scheduler.start()


#--------------- Fill up database ----------------------#
# Creates an Asset for the country.
def addNewState(name, prio):
    def createStateAsset(stateName):
        assetName = (ASSETPATH_US + stateName).replace(" ", "-")
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

# stateList = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming']
# for s in stateList:
#   addNewState(s, i)
#   i = i+1
list=[('Alaska', 52), ('Arizona', 14), ('Arkansas', 24), ('California', 2), ('Colorado', 13), ('Connecticut', 4), ('Delaware', 52), ('Florida', 8), ('Georgia', 21), ('Hawaii', 51), ('Idaho', 52), ('Illinois', 7), ('Indiana', 17), ('Iowa', 52), ('Kansas', 20), ('Kentucky', 29), ('Louisiana', 23), ('Maine', 52), ('Maryland', 9), ('Massachusetts', 12), ('Michigan', 11), ('Minnesota', 18), ('Mississippi', 25), ('Missouri', 19), ('Montana', 52), ('Nebraska', 52), ('Nevada', 52), ('New Hampshire', 52), ('New Jersey', 6), ('New Mexico', 52), ('New York', 3), ('North Carolina', 8), ('North Dakota', 52), ('Ohio', 10), ('Oklahoma', 52), ('Oregon', 52), ('Pennsylvania', 5), ('Rhode Island', 52), ('South Carolina', 28), ('South Dakota', 52), ('Tennessee', 1), ('Texas', 0), ('Utah', 11), ('Vermont', 52), ('Virginia', 15), ('Washington', 52), ('West Virginia', 26), ('Wisconsin', 16), ('Wyoming', 52), ('Alabama', 22)]
for i in list:
    i
    #addNewState(i[0],i[1])




logging.info("------   End    ------")
