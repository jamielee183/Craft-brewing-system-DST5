import os
import sys
import numpy as np
import time

sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
from source.tools.sqlBrewingComms import *
HOST = "192.168.10.223"
USER = "jamie"
PASSWORD = "beer"
LOGIN = [HOST,USER,PASSWORD]


#Brew recipe
brewName = "Simcoe IPA"
mashTime = "60"
mashTemp = "80"
boilTime = "60"
boilTemp = "100"
hop1 = ("Simcoe","60")
hop2 = ("Simcoe","40")
hop3 = ("Simcoe","20")
hop4 = ("Simcoe","1")
fermentTemp = "20"
fermentationTankNo = 4
startG = 1.053
endG =  1.045
fermtime = 600



SQLNewBrew(LOGIN=LOGIN, brewName=brewName, 
        mashTime=mashTime, mashTemp=mashTemp, 
        boilTemp=boilTemp, boilTime=boilTime,
        hop1=hop1, hop2=hop2, hop3=hop3, hop4=hop4,
        fermentTemp=fermentTemp)

mash = SQLMashMonitor(LOGIN=LOGIN)

mashtemps = np.zeros(0)
mashtemps = np.append(mashtemps, np.linspace(0,int(mashTemp)*0.8,int(mashTime)/12))
mashtemps = np.append(mashtemps, np.linspace(int(mashTemp)*0.8,int(mashTemp),int(mashTime)/12))
mashtemps = np.append(mashtemps, [int(mashTemp) for _ in range(int(10*int(mashTime)/12))])


print(mashtemps)
for i in range(int(mashTime)):
    mash.record(temp=float(mashtemps[i]), volume=0, pH=0, SG=0)
    time.sleep(1)
print("Fake Mash Complete")


boil = SQLBoil(LOGIN=LOGIN)
boilMonitor = SQLBoilMonitor(LOGIN=LOGIN)

boiltemps = np.zeros(0)
boiltemps = np.append(boiltemps, np.linspace(0,int(boilTemp)*0.8,int(boilTime)/12))
boiltemps = np.append(boiltemps, np.linspace(int(boilTemp)*0.8,int(boilTemp),int(boilTime)/12))
boiltemps = np.append(boiltemps, [int(boilTemp) for _ in range(int(10*int(boilTime)/12))])



boil.startTimer()
for i in range(int(boilTime)):
    time.sleep(1)
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
print("Fake boil Complete")

batchID= boil.getCurrentBrew()
ferment = SQLFermentMonitor(LOGIN=LOGIN, batchID=batchID ,fermenterID=fermentationTankNo)
ferment.record(specificG=None,temp=None,volume=None)


fermentG = np.zeros(0)
fermentG = np.append(fermentG, np.linspace(startG, endG, fermtime*0.8))
fermentG = np.append(fermentG, np.linspace(endG, endG, fermtime*0.2))
for i in range(fermtime):
    time.sleep(1)
    ferment.record(specificG=fermentG[i], temp=int(fermentTemp), volume=0)


