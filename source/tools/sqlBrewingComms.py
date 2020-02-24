import sys
import os

import numpy as np
from datetime import datetime
from abc import ABCMeta, abstractmethod
import logging

sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
import source.tools.exceptionLogging
from source.tools.sqlHandler import SqlTableHandler as Sql

class SQLBrewingComms(metaclass=ABCMeta):

    _logname = 'SQLBrewingComms'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN:list):
        self.LOGIN = LOGIN
        self.dbName = "Brewing"
        self.db = Sql(self.LOGIN, self.dbName)
        # self.batchID = self.getCurrentBrew()
        
    def _custom(self, sql: str, val=None ):
        # db = Sql(self.LOGIN, self.dbName)
        self.db.flushTables()
        if val is None:
            self.db.custom(sql)
        elif val is not None:
            self.db.custom(sql,val)

    def getCurrentBrew(self):
        # db = Sql(self.LOGIN, self.dbName)
        self.db.flushTables()
        return self.db.maxIdFromTable("Brews")

    def getBrewData(self, batchID):
        # db = Sql(self.LOGIN, self.dbName)
        self.db.flushTables()
        sql = f"SELECT * FROM Brews WHERE id = '{batchID}'"
        query = self.db.custom(sql)
        data = {}

        data["recipeName"] = query[0][1]
        data["recipeDate"] = query[0][2]
        data["mashTemp"]   = query[0][3]
        data["mashTime"]  = query[0][4]
        data["boilTemp"]  = query[0][5]
        data["boilTime"]  = query[0][6]
        data["hop1"]       = (query[0][7],query[0][8])
        data["hop2"]       = (query[0][9],query[0][10])
        data["hop3"]       = (query[0][11],query[0][12])
        data["hop4"]       = (query[0][13],query[0][14])
        data["fermenttemp"]= query[0][15]
        return data

    @abstractmethod
    def record(self):
        pass

class SQLBoilMonitor(SQLBrewingComms):

    _logname = 'SQLBoilMonitor'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN:list):
       super().__init__(LOGIN)

    
    def record(self, temp, volume):
        self.batchID = self.getCurrentBrew()
        insert = []
        insert.append(("BatchID", "TimeStamp", "Temp", "Volume"))
        insert.append((self.batchID, datetime.now(), temp, volume))
        self._log.debug(f"Batch ID:{self.batchID}, Time Stamp: {datetime.now()}, Temp: {temp}, Volume:{volume}")
        # db = Sql(self.LOGIN, self.dbName)
        self.db.insertToTable("BoilMonitor", insert)
        self.db.flushTables()

class SQLBoil(SQLBrewingComms):

    _logname = 'SQLBoil'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN:list):
       super().__init__(LOGIN)
       self.hop1timer = None
       self.hop2timer = None
       self.hop3timer = None
       self.hop4timer = None

       self.activeFlag = False
       self.hop1Flag = False
       self.hop2Flag = False
       self.hop3Flag = False
       self.hop4Flag = False


    def startTimer(self):
        self.starttime = datetime.now()
        self.activeFlag = True
        return datetime.time(datetime.now())

    def endTimer(self):
        self.endtime = datetime.now()
        self.activeFlag = False
        self.record()
        return datetime.time(datetime.now())

    def hop1Timer(self):
        self.hop1timer = datetime.time(datetime.now())
        self._log.info("Hop 1 added")
        self.hop1Flag = True
        return datetime.time(datetime.now())

    def hop2Timer(self):
        self.hop2timer = datetime.time(datetime.now())
        self._log.info("Hop 2 added")
        self.hop2Flag = True
        return datetime.time(datetime.now())

    def hop3Timer(self):
        self.hop3timer = datetime.time(datetime.now())
        self._log.info("Hop 3 added")
        self.hop3Flag = True
        return datetime.time(datetime.now())

    def hop4Timer(self):
        self.hop4timer = datetime.time(datetime.now())
        self._log.info("Hop 4 added")
        self.hop4Flag = True
        return datetime.time(datetime.now())

    def record(self):
        self.batchID = self.getCurrentBrew()
        insert = []
        insert.append(("BatchID", "BoilStart", "Hop1", "Hop2", "Hop3", "Hop4", "BoilFinish"))
        insert.append((self.batchID, self.starttime, self.hop1timer,self.hop2timer,self.hop3timer,self.hop4timer, self.endtime))
        # db = Sql(self.LOGIN, self.dbName)
        self.db.insertToTable("Boil", insert)
        self.db.flushTables()

class SQLNewBrew(SQLBrewingComms):

    _logname = 'SQLNewBrew'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN:list, brewName:str, mashTime:str, mashTemp:str, boilTime:str, boilTemp:str,hop1:tuple, hop2:tuple, hop3:tuple, hop4:tuple, fermentTemp):
        super().__init__(LOGIN)
        self.brewName = brewName
        self.mashTime = mashTime
        self.mashTemp = mashTemp
        self.boilTime = boilTime
        self.boilTemp = boilTemp
        self.hop1Name, self.hop1Time = hop1
        self.hop2Name, self.hop2Time = hop2
        self.hop3Name, self.hop3Time = hop3
        self.hop4Name, self.hop4Time = hop4
        self.fermentTemp = fermentTemp


        self.record()
        # self.batchID = self.getCurrentBrew()

    def record(self):
        
        insert = []
        insert.append(("Recipe", "Date","MashTime", "MashTemp","BoilTime",\
        "BoilTemp","Hop1Name", "Hop1Time","Hop2Name", "Hop2Time",\
        "Hop3Name", "Hop3Time","Hop4Name", "Hop4Time", "FermentTemp"))
        insert.append((self.brewName,
            datetime.date(datetime.now()),
            self.mashTime, self.mashTemp,
            self.boilTime, self.boilTemp,
            self.hop1Name, self.hop1Time,
            self.hop2Name, self.hop2Time,
            self.hop3Name, self.hop3Time,
            self.hop4Name, self.hop4Time,
            self.fermentTemp
            ))
        
        # db = Sql(self.LOGIN, self.dbName)
        self.db.insertToTable("Brews", insert)
        self.db.flushTables()
        self.batchID = self.getCurrentBrew()
        self._log.info(f"Recipe:{self.brewName}, "
                     f"Batch ID: {self.batchID}, " 
                     f"MashTime: {self.mashTime}, "
                     f"MashTemp: {self.mashTemp}, "
                     f"BoilTime: {self.boilTime}, "
                     f"BoilTemp: {self.boilTemp}, "
                     f"Hop1Time: {self.hop1Time}, Hop1Name: {self.hop1Name}, "
                     f"Hop2Time: {self.hop2Time}, Hop2Name: {self.hop2Name}, "
                     f"Hop3Time: {self.hop3Time}, Hop3Name: {self.hop3Name}, "
                     f"Hop4Time: {self.hop4Time}, Hop4Name: {self.hop4Name}, "
                     f"FermentTemp: {self.fermentTemp}"
                     )
        


class SQLFermentMonitor(SQLBrewingComms):

    _logname = 'SQLFermentMonitor'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN:list, batchID:int,fermenterID:int):
        super().__init__(LOGIN)
        self.fermenterID = fermenterID
        self.batchID = batchID

    def newBatch(self):
        self.batchID = self.getCurrentBrew()

    def record(self, specificG, temp, volume):
        insert = []
        insert.append(("BatchID", "TimeStamp", "Fermenter", "Sg", "Temp", "Volume"))
        insert.append((self.batchID, datetime.now(), self.fermenterID, specificG, temp, volume))
        self._log.debug(f"Fermenter:{self.fermenterID}, Batch:{self.batchID}, SG:{specificG},Temp:{temp}, Volume:{volume}")
        # db = Sql(self.LOGIN, self.dbName)
        self.db.insertToTable("Ferment", insert)
        self.db.flushTables()


if __name__ == '__main__':

    import time
    import logging
    _logname = 'SQLBrewingComms'
    _log = logging.getLogger(f'{_logname}')
    

    HOST = "localhost"
    USER = "Test"
    PASSWORD = "BirraMosfeti"
    LOGIN = [HOST,USER,PASSWORD]

    # brewName:str, mashTime:str, \
    #             mashTemp:str, boilTime:str, boilTemp:str. \
    #             hop1:tuple, hop2:tuple, hop3:tuple, hop4:tuple, fermentTemp):


    hop1 = ("Citra","0")
    hop2 = ("Simcoe","1")
    hop3 = ("Saaz","2")
    hop4 = ("HoppidyHop","3")

    # brew = SQLNewBrew(LOGIN, "Tennents", "60","-20","69","-2",hop1,hop2,hop3,hop4, "112" )
    # fermenter1=SQLFermentMonitor(LOGIN, 1)
    # boilMonitor = SQLBoilMonitor(LOGIN)
    # boil = SQLBoil(LOGIN)
    
    # boil.startTimer()
    # boilMonitor.record(20,10.2)
    # time.sleep(1)
    # boilMonitor.record(40,10)
    # time.sleep(1)
    # boil.hop1Timer()
    # boilMonitor.record(90,10)
    # time.sleep(1)
    # boil.hop2Timer()
    # boilMonitor.record(90,9)
    # time.sleep(1)
    # boil.hop3Timer()
    # boilMonitor.record(90,8)
    # time.sleep(1)
    # boil.hop4Timer()
    # boilMonitor.record(90,7)
    # time.sleep(1)
    # boil.endTimer()
    # boil.record()
    

    # brew = SQLNewBrew(LOGIN, "Not Tennents")
    # boilMonitor = SQLBoilMonitor(LOGIN)
    # boil = SQLBoil(LOGIN)

    # boil.startTimer()
    # boilMonitor.record(20,10.2)
    # time.sleep(1)
    # boilMonitor.record(40,10)
    # time.sleep(1)
    # #boil.hop1Timer()
    # boilMonitor.record(90,10)
    # time.sleep(1)
    # boil.hop2Timer()
    # boilMonitor.record(90,9)
    # time.sleep(1)
    # boil.hop3Timer()
    # boilMonitor.record(90,8)
    # time.sleep(1)
    # #boil.hop4Timer()
    # boilMonitor.record(90,7)
    # time.sleep(1)
    # boil.endTimer()
    # boil.record()

    brew = SQLNewBrew(LOGIN, "Tennents", "60","-20","69","5",hop1,hop2,hop3,hop4, "112" )
    fermenter1=SQLFermentMonitor(LOGIN, brew.getCurrentBrew(), 1)
    fermenter1.record(specificG=10, temp=26, volume=90)
    fermenter1.record(specificG=50, temp=36, volume=91)
    fermenter1.record(specificG=30, temp=56, volume=92)
    fermenter1.record(specificG=60, temp=76, volume=93)
    fermenter1.record(specificG=140, temp=59, volume=100)
    fermenter1.record(specificG=106, temp=57, volume=100)

    # brew = SQLNewBrew(LOGIN, "Not Tennents", "50","-60","68","200",hop1,hop2,hop3,hop4, "202" )
    # fermenter2=SQLFermentMonitor(LOGIN, brew.getCurrentBrew(), 2)
    # fermenter2.record(specificG=10, temp=56, volume=90)
    # fermenter2.record(specificG=34, temp=35, volume=91)
    # fermenter2.record(specificG=63, temp=87, volume=92)
    # fermenter2.record(specificG=23, temp=23, volume=100)
    # fermenter2.record(specificG=75, temp=74, volume=90)

    # brew = SQLNewBrew(LOGIN, "BirraMosfetti ", "40","1000","67","2",hop1,hop2,hop3,hop4, "12" )
    # fermenter3=SQLFermentMonitor(LOGIN, brew.getCurrentBrew(), 3)
    # fermenter3.record(specificG=11, temp=56, volume=90)
    # fermenter3.record(specificG=12, temp=56, volume=96)
    # fermenter3.record(specificG=13, temp=53, volume=90)
    # fermenter3.record(specificG=14, temp=56, volume=30)
    # fermenter3.record(specificG=15, temp=56, volume=90)

    
    # brew = SQLNewBrew(LOGIN, "Not BirraMosfetti ", "40","1000","67","2",hop1,hop2,hop3,hop4, "12" )
    # fermenter3=SQLFermentMonitor(LOGIN, brew.getCurrentBrew(), 3)
    # fermenter3.record(specificG=10, temp=6, volume=3)
    # fermenter3.record(specificG=20, temp=56, volume=9)
    # fermenter3.record(specificG=30, temp=56, volume=0)
    # fermenter3.record(specificG=35, temp=56, volume=9)
    # fermenter3.record(specificG=37, temp=6, volume=9)


    # brew = SQLNewBrew(LOGIN, "Stella", "40","1000","67","2",hop1,hop2,hop3,hop4, "12" )
    # fermenter4=SQLFermentMonitor(LOGIN, brew.getCurrentBrew(), 4)
    # fermenter4.record(specificG=10, temp=64, volume=92)
    # fermenter4.record(specificG=13, temp=63, volume=93)
    # fermenter4.record(specificG=12, temp=62, volume=94)
    # fermenter4.record(specificG=14, temp=62, volume=95)
    # fermenter4.record(specificG=10, temp=61, volume=96)
