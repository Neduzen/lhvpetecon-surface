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

print("Initialize all states:")
i = 0
for c in states:
    gridlist = []
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

list=[('Alaska', 52), ('Arizona', 14), ('Arkansas', 24), ('California', 2), ('Colorado', 13), ('Connecticut', 4), ('Delaware', 52), ('Florida', 8), ('Georgia', 21), ('Hawaii', 51), ('Idaho', 52), ('Illinois', 7), ('Indiana', 17), ('Iowa', 52), ('Kansas', 20), ('Kentucky', 29), ('Louisiana', 23), ('Maine', 52), ('Maryland', 9), ('Massachusetts', 12), ('Michigan', 11), ('Minnesota', 18), ('Mississippi', 25), ('Missouri', 19), ('Montana', 52), ('Nebraska', 52), ('Nevada', 52), ('New Hampshire', 52), ('New Jersey', 6), ('New Mexico', 52), ('New York', 3), ('North Carolina', 8), ('North Dakota', 52), ('Ohio', 10), ('Oklahoma', 52), ('Oregon', 52), ('Pennsylvania', 5), ('Rhode Island', 52), ('South Carolina', 28), ('South Dakota', 52), ('Tennessee', 1), ('Texas', 0), ('Utah', 11), ('Vermont', 52), ('Virginia', 15), ('Washington', 52), ('West Virginia', 26), ('Wisconsin', 16), ('Wyoming', 52), ('Alabama', 22)]
for i in list:
    i
    #addNewState(i[0],i[1])




logging.info("------   End    ------")
