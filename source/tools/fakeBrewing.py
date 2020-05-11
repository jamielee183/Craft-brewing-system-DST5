import os
import sys
import numpy as np
import time

sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
from source.tools.sqlBrewingComms import *
HOST = "192.168.0.17"
USER = "jamie"
PASSWORD = "beer"
LOGIN = [HOST,USER,PASSWORD]


#Brew recipe
brewName = "Alpha dog"
mashTime = "90"
mashTemp = "68"
boilTime = "60"
boilTemp = "95"
hop1 = ("Simcoe","60")
hop2 = ("Citra","30")
hop3 = ("Chinook","20")
hop4 = ("Columbus","10")
fermentTemp = "19"
fermentationTankNo = "1"
startG = "1.062"
endG =  "1.020"
fermtime = "600"

# brewName = "Simcoe IPA"
# mashTime = "60"
# mashTemp = "75"
# boilTime = "60"
# boilTemp = "100"
# hop1 = ("Simcoe","60")
# hop2 = ("Simcoe","30")
# hop3 = ("Simcoe","20")
# hop4 = ("Simcoe","10")
# fermentTemp = "22"
# fermentationTankNo = "2"
# startG = "1.050"
# endG =  "1.030"
# fermtime = "600"

# brewName = "Tennents"
# mashTime = "60"
# mashTemp = "60"
# boilTime = "60"
# boilTemp = "100"
# hop1 = ("Special","60")
# hop2 = ("Snaz","30")
# hop3 = ("SomeHop","20")
# hop4 = ("Hiphops","5")
# fermentTemp = "22"
# fermentationTankNo = "3"
# startG = "1.060"
# endG =  "1.045"
# fermtime = "60"

# brewName = "Tennents"
# mashTime = "60"
# mashTemp = "50"
# boilTime = "60"
# boilTemp = "90"
# hop1 = ("Special","60")
# hop2 = ("Snaz","30")
# hop3 = ("SomeHop","20")
# hop4 = ("Hiphops","5")
# fermentTemp = "23"
# fermentationTankNo = "4"
# startG = "1.050"
# endG =  "1.010"
# fermtime = "600"


# brewName = "Tennents"
# mashTime = "60"
# mashTemp = "40"
# boilTime = "60"
# boilTemp = "95"
# hop1 = ("Special","60")
# hop2 = ("Snaz","30")
# hop3 = ("SomeHop","20")
# hop4 = ("Hiphops","5")
# fermentTemp = "23"
# fermentationTankNo = "5"
# startG = "1.050"
# endG =  "1.00"
# fermtime = "600"




brew = SQLNewBrew(LOGIN=LOGIN, brewName=brewName, 
        mashTime=mashTime, mashTemp=mashTemp, 
        boilTemp=boilTemp, boilTime=boilTime,
        hop1=hop1, hop2=hop2, hop3=hop3, hop4=hop4,
        fermentTemp=fermentTemp)
batchID = brew.getCurrentBrew()

mash = SQLMashMonitor(LOGIN=LOGIN)

mashtemps = np.zeros(0)
mashtemps = np.append(mashtemps, np.linspace(0,int(mashTemp)*0.8,int(mashTime)/12))
mashtemps = np.append(mashtemps, np.linspace(int(mashTemp)*0.8,int(mashTemp),int(mashTime)/12))
mashtemps = np.append(mashtemps, [int(mashTemp) for _ in range(int(10*int(mashTime)/12)+10)])


boiltemps = np.zeros(0)
boiltemps = np.append(boiltemps, np.linspace(0,int(boilTemp)*0.8,int(boilTime)/12))
boiltemps = np.append(boiltemps, np.linspace(int(boilTemp)*0.8,int(boilTemp),int(boilTime)/12))
boiltemps = np.append(boiltemps, [int(boilTemp) for _ in range(int(10*int(boilTime)/12)+10)])

fermentG = np.zeros(0)
fermentG = np.append(fermentG, np.linspace(float(startG), float(endG), int(fermtime)*0.8))
fermentG = np.append(fermentG, np.linspace(float(endG), float(endG), int(fermtime)*0.2))


print(mashtemps)
for i in range(int(mashTime)):
    mash.record(temp=float(mashtemps[i]), volume=0, pH=0, SG=0)
    time.sleep(60)
print(f"Fake Mash Complete: BatchID - {batchID}")


boil = SQLBoil(LOGIN=LOGIN)
boilMonitor = SQLBoilMonitor(LOGIN=LOGIN)



boil.startTimer()
for i in range(int(boilTime)):
    time.sleep(60)
    boilMonitor.record(temp=float(boiltemps[i]), volume=0)
    if int(boilTime)-i == int(hop1[1]):
        boil.hop1Timer()
    if int(boilTime)-i == int(hop2[1]):
        boil.hop2Timer()
    if int(boilTime)-i == int(hop3[1]):
        boil.hop3Timer()
    if int(boilTime)-i == int(hop4[1]):
        boil.hop4Timer()

boil.endTimer()
print(f"Fake boil Complete: BatchID - {batchID}")

ferment = SQLFermentMonitor(LOGIN=LOGIN, batchID=batchID ,fermenterID=int(fermentationTankNo))
ferment.record(specificG=None,temp=None,volume=None)


for i in range(int(fermtime)):
    time.sleep(60)
    ferment.record(specificG=float(fermentG[i]), temp=int(fermentTemp), volume=0)
print(f"Fake Fermentation complete: BatchID - {batchID}")


