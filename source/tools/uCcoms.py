import numpy as np
from abc import ABCMeta, abstractmethod
from threading import Thread, Event
import logging
import sys, os
# if running from command line, need to append the parent directories to the PATH
# so python knows where to find "source.file"
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
from source.tools.constants import *
from source.tools.sqlBrewingComms import SQLBoilMonitor, SQLFermentMonitor
from source.tools.sqlHandler import SqlTableHandler as dataBase


import RPi.GPIO as GPIO
import time
import spidev 
from RF24 import *

class UCComms(Thread, metaclass=ABCMeta):


    _logname = 'UCComms'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self):
        super().__init__()


    def configure(self) -> bool:

        try:
            self._configure()
            return True

        except Exception as e:
            self._log.warning("Could not configure device")
            self._log.warning(e)
            return False


    @abstractmethod
    def _configure(self) -> None:
        '''
        This method needs to be implemented when subclassing Comms:
        This is where the configuration routine for each I2C uC goes
        '''
        pass

        
class PiRadio(UCComms):

    _logname = 'PiRadio'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN):
        self.LOGIN=LOGIN
        self.db = dataBase(self.LOGIN, "Brewing")
        super().__init__()
        self.pipes = [[0xE0,0xE0,0xF1,0xF1,0xE0], [0xCC, 0xCE,0xCC,0xCE,0xCC]]
        self.PI_INTERUPT_PIN = 5
        self.cases ={
            0x01 : self.mash,
            0x02 : self.boil,
            0x03 : self.ferment
        }

        

    def _configure(self) -> None:

        self.radio = RF24(25,8)
        self.radio.begin()
        self.radio.openReadingPipe(1,bytes(self.pipes[1]))
        self.radio.openWritingPipe(bytes(self.pipes[0]))
        self.radio.setChannel(PI_RADIO_CHANNEL)
        self.radio.eneableDynamicPayloads()
        self.radio.setRetries(5,15)
        #Setup GPIO pin for interupt when datas ready
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PI_INTERUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.PI_INTERUPT_PIN, GPIO.FALLING, callback=self.callback)
        self.radio.startListening()


    def readData(self):
        
        if self.radio.available():
            recieved = self.radio.read(self.radio.getDynamicPayloadSize()).decode('utf-8')
            self._log.debug("Recieved data: {}".format(recieved))
            return recieved

    def sendData(self, channel=PI_RADIO_CHANNEL):
        self.radio.stopListening()

    def callback(self):
        dataIn = self.readData()
        self.caseSwitcher(dataIn)

    def caseSwitcher(self, data):
        try:
            func = self.cases.get(data[0])
            return func(data[1:])
        except:
            self._log("something went wrong")

    def mash(self, data):
        if data[0] == 0x01: #if temp sensor data, 12 bit data? (2 bytes)
            pass
        elif data[0] == 0x02: #if temp camera data, 8x8 array of 1 byte values
            pass
        else:
            self._log.warning("Wrong data type for Mash")

    def boil(self, data):
        if data[0] == 0x01: #if temp sensor data
            #insert temp and volume data
            SQLBoilMonitor(LOGIN=self.LOGIN).record(temp=data[1:2], volume=10)
            
        elif data[0] == 0x02: #if temp cam data
            pass
        else:
            self._log.warning("Wrong data type for Boil")

    def ferment(self, data):
        #bytes 0 are the fermented ID
        #bytes 1-2 are temp sensor (12 bit data)
        #bytes 3-4 are specific gravity (assume 16 bit?)
        #bytes 5-6 are volume
        fermenterID = int.from_bytes(data[0], "big") 
        tempData = int.from_bytes(data[1:2], "big")
        specificG = int.from_bytes(data[3:4], "big")
        volume = int.from_bytes(data[5:6], "big")


        sql = f"SELECT BatchID FROM Ferment WHERE Fermenter = '{fermenterID}'"
        query = self.db.custom(sql)
        batchID = query[-1][0]

        addtodatabase = SQLFermentMonitor(LOGIN=self.LOGIN, batchID=batchID,fermenterID=fermenterID)
        addtodatabase.record(specificG=specificG,temp=tempData,volume=None)


    

    


if __name__=="__main__":
    from getpass import getpass
    HOST = "192.168.10.223"
    USER = "jamie"
    PASSWORD = "beer"

    # HOST = "localhost"
    # USER = "Test"
    # PASSWORD = "BirraMosfeti"

    # HOST = input("Host ID: ")
    # USER = input("User: ")
    # PASSWORD = getpass()
    if HOST == "Pi":
        HOST = "192.168.10.223"

    LOGIN = [HOST,USER,PASSWORD]

    x = PiRadio(LOGIN)
    x.configure()