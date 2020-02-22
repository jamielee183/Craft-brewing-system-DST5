from SqlHandler import SqlTableHandler as Sql
from datetime import datetime
from abc import ABCMeta, abstractmethod
import logging

class SQLBrewingComms(metaclass=ABCMeta):

    _logname = 'SQLBrewingComms'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN:list):
        self.LOGIN = LOGIN
        self.dbName = "Brewing"
        self.db = Sql(self.LOGIN, self.dbName)
        self.batchID = self.getCurrentBrew()
        
    def _custom(self, sql: str, val=None ):
        db = Sql(self.LOGIN, self.dbName)
        if val is None:
            db.custom(sql)
        elif val is not None:
            db.custom(sql,val)

    def getCurrentBrew(self):
        db = Sql(self.LOGIN, self.dbName)
        return db.maxIdFromTable("Brews")

    @abstractmethod
    def record(self):
        pass

class SQLBoilMonitor(SQLBrewingComms):

    _logname = 'SQLBoilMonitor'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN:list):
       super().__init__(LOGIN)

    
    def record(self, temp, volume):
        insert = []
        insert.append(("BatchID", "TimeStamp", "Temp", "Volume"))
        insert.append((self.batchID, datetime.now(), temp, volume))
        self._log.info(f"Batch ID:{self.batchID}, Time Stamp: {datetime.now()}, Temp: {temp}, Volume:{volume}")
        db = Sql(self.LOGIN, self.dbName)
        db.insertToTable("BoilMonitor", insert)

class SQLBoil(SQLBrewingComms):

    _logname = 'SQLBoil'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN:list):
       super().__init__(LOGIN)
       self.hop1timer = None
       self.hop2timer = None
       self.hop3timer = None
       self.hop4timer = None


    def startTimer(self):
        self.starttime = datetime.now()

    def endTimer(self):
        self.endtime = datetime.now()

    def hop1Timer(self):
        self.hop1timer = datetime.time(datetime.now())
    def hop2Timer(self):
        self.hop2timer = datetime.time(datetime.now())
    def hop3Timer(self):
        self.hop3timer = datetime.time(datetime.now())
    def hop4Timer(self):
        self.hop4timer = datetime.time(datetime.now())

    def record(self):
        insert = []
        insert.append(("BatchID", "BoilStart", "Hop1", "Hop2", "Hop3", "Hop4", "BoilFinish"))
        insert.append((self.batchID, self.starttime, self.hop1timer,self.hop2timer,self.hop3timer,self.hop4timer, self.endtime))
        db = Sql(self.LOGIN, self.dbName)
        db.insertToTable("Boil", insert)

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
        self.batchID = self.getCurrentBrew()

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
        db = Sql(self.LOGIN, self.dbName)
        db.insertToTable("Brews", insert)
        


class SQLFermentMonitor(SQLBrewingComms):

    _logname = 'SQLFermentMonitor'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN:list, fermenterID):
        super().__init__(LOGIN)
        self.fermenterID = fermenterID
        # self.batchID = self.getCurrentBrew()

    def newBatch(self):
        self.batchID = self.getCurrentBrew()

    def record(self, specificG, temp, volume):
        insert = []
        insert.append(("BatchID", "TimeStamp", "Fermenter", "Sg", "Temp", "Volume"))
        insert.append((self.batchID, datetime.now(), self.fermenterID, specificG, temp, volume))
        self._log.info(f"Fermenter:{self.fermenterID}, Batch:{self.batchID}, SG:{specificG},Temp:{temp}, Volume:{volume}")
        db = Sql(self.LOGIN, self.dbName)
        db.insertToTable("Ferment", insert)


if __name__ == '__main__':

    import time

    HOST = "localhost"
    USER = "Test"
    PASSWORD = "BirraMosfeti"
    LOGIN = [HOST,USER,PASSWORD]

    # brewName:str, mashTime:str, \
    #             mashTemp:str, boilTime:str, boilTemp:str. \
    #             hop1:tuple, hop2:tuple, hop3:tuple, hop4:tuple, fermentTemp):


    hop1 = ("Citra","0")
    hop2 = ("Simcoe","15")
    hop3 = ("Saaz","45")
    hop4 = ("HoppidyHop","59")

    brew = SQLNewBrew(LOGIN, "Tennents", "60","-20","69","-2",hop1,hop2,hop3,hop4, "112" )
    fermenter1=SQLFermentMonitor(LOGIN, 1)
    boilMonitor = SQLBoilMonitor(LOGIN)
    boil = SQLBoil(LOGIN)
    
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

    # fermenter2=SQLFermentMonitor(LOGIN, 4)

    
    fermenter1.record(10,10,10)
    # fermenter2.record(20,20,20)
    fermenter1.record(30,30,30)
    # fermenter2.record(40,40,40)