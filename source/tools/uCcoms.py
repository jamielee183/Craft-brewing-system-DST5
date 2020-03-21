import numpy as np
from abc import ABCMeta, abstractmethod
from threading import Thread, Event
import time
import logging
import sys, os
# if running from command line, need to append the parent directories to the PATH
# so python knows where to find "source.file"
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
from source.tools.constants import *
from source.tools.exceptionLogging import *
from source.tools.sqlBrewingComms import SQLBoilMonitor, SQLFermentMonitor
from source.tools.sqlHandler import SqlTableHandler as dataBase


import RPi.GPIO as GPIO
import time
import spidev 
from RF24 import *


CONFIGURE_ARUDINO = [0x05]

BOIL_COMMAND = 0x02
MASH_COMMAND = 0x01
FERMENT_COMMAND = 0x03


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

#    def readData(self) -> bool:
#        try:
#            sel

    @abstractmethod
    def _configure(self) -> None:
        '''
        This method needs to be implemented when subclassing Comms:
        This is where the configuration routine for each I2C uC goes
        '''
        pass

    @abstractmethod
    def readData(self):
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
            BOIL_COMMAND : self.mash,
            BOIL_COMMAND : self.boil,
            FERMENT_COMMAND : self.ferment
        }
        self.sendRetryCount = 0
        

    def _configure(self) -> None:

        self.radio = RF24(25,8)
        self.radio.begin()
        self.radio.openReadingPipe(1,bytes(self.pipes[1]))
        self.radio.openWritingPipe(bytes(self.pipes[0]))
        self.radio.setChannel(PI_RADIO_CHANNEL)
        self.radio.enableDynamicPayloads()
        self.radio.setRetries(5,15)
        #Setup GPIO pin for interupt when datas ready
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PI_INTERUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.PI_INTERUPT_PIN, GPIO.FALLING, callback=self.callback)
        self.radio.startListening()
        self.sendData(bytes(CONFIGURE_ARUDINO))
       # self.sendData(bytes([0x02, 0x01, 0x00, 0x05]))


    def readData(self):
        
        if self.radio.available():
            recieved = self.radio.read(self.radio.getDynamicPayloadSize())
            self._log.debug("Recieved data: {}".format(recieved))
            return recieved

    def sendData(self, data, channel=PI_RADIO_CHANNEL):
        self.radio.stopListening()
        self._log.debug("sending data: {}".format(data))
        sent = False
        while not sent:
            sent = self.radio.write(data)
            if not sent:
                self.sendRetryCount +=1
                if self.sendRetryCount == 5:
                    self._log.warning("Sending Data failed") 
                    break

        self.sendRetryCount = 0
        self._log.debug("data sent")
        self.radio.startListening()
        return sent

    def callback(self, channel=0):
        tx, fail, rx  = self.radio.whatHappened()
        if rx or self.radio.available():
            dataIn = self.readData()
            if dataIn is not None:
                self.caseSwitcher(dataIn)
                self._log.debug("Data available")

        if tx:
            self._log.debug("Ack Payload sucessfull")

        if fail:
            self._log.debug("Ack Payload fail")

    def caseSwitcher(self, data):
        assert data[0] in self.cases
        func = self.cases.get(data[0])
        return func(data[1:])


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
            temp = int.from_bytes(data[1:3], 'big', signed=False)
            #convert 16bit number to temp value
            x = SQLBoilMonitor(LOGIN=self.LOGIN)
            x.record(temp=temp, volume=20)
            
        elif data[0] == 0x02: #if temp cam data
            pass
        else:
            self._log.warning("Wrong data type for Boil")

    def startBoil(self, temp):
        temp *= 10
        temp = int(temp)
        while True:
            if self.sendData(bytes([BOIL_COMMAND, 0x01,(temp>>8)&0xFF, temp&0xFF])):
                break

    def stopBoil(self):
        self.sendData(bytes([BOIL_COMMAND, 0x02]))

    def ferment(self, data):
        #bytes 0 are the fermented ID
        #bytes 1-2 are temp sensor (12 bit data)
        #bytes 3-4 are specific gravity (assume 16 bit?)
        #bytes 5-6 are volume

        #fermenterID = int.from_bytes(data[0], "big", signed=False) 
        fermenterID = data[0]
        tempData = int.from_bytes(data[1:3], "big", signed=False)
        specificG = int.from_bytes(data[3:5], "big", signed=False)
        volume = int.from_bytes(data[5:7], "big", signed=False)
        self.db.flushTables()
        sql = f"SELECT max(BatchID) FROM Ferment WHERE Fermenter = '{fermenterID}'"
        query = self.db.custom(sql)
        batchID = query[-1][0]
        
        addtodatabase = SQLFermentMonitor(LOGIN=self.LOGIN, batchID=batchID,fermenterID=fermenterID)
        addtodatabase.record(specificG=specificG,temp=tempData,volume=volume)


    

    


if __name__=="__main__":
    from getpass import getpass
    import time
    LOGGING_LEVEL = logging.DEBUG
    _log = logging.getLogger(__name__)
    logging.basicConfig(format ='%(asctime)s :%(name)-7s :%(levelname)s :%(message)s', datefmt='%d-%b-%y %H:%M:%S', level=LOGGING_LEVEL)
    handler = logging.StreamHandler(stream=sys.stdout)
    _log.addHandler(handler)
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
    senddata = [0x01,0x02,0x03,0x04,0x05]

    x = PiRadio(LOGIN)
    x.configure()
    time.sleep(10)
    x.startBoil(100)
    time.sleep(300)
    x.stopBoil()
        #time.sleep(20)
        #x.stopBoil()
        #time.sleep(5)
