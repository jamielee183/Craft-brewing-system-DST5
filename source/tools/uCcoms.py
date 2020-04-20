##@package UCcoms
#Communications package to recieve data from brewing modules
# 
#Link up brewing module to database through Raspberry Pi and nRF24L01+

import numpy as np
from abc import ABCMeta, abstractmethod
from threading import Thread, Event, Lock
import time
import logging
import sys, os
# if running from command line, need to append the parent directories to the PATH
# so python knows where to find "source.file"
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
from source.tools.constants import *
from source.tools.exceptionLogging import *
from source.tools.sqlBrewingComms import *
from source.tools.sqlHandler import SqlTableHandler as dataBase


import RPi.GPIO as GPIO
import time
import spidev 
from RF24 import *


CONFIGURE_ARUDINO = [0x05]

BOIL_COMMAND = 0x02
MASH_COMMAND = 0x01
FERMENT_COMMAND = 0x03

##UCComms abstract calss
#
#Generic communications class, with confiure and readData functions
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


    #Configuration method to overide
    #   
    #This method needs to be implemented when subclassing Comms:
    #This is where the configuration routine for each uC goes
    @abstractmethod
    def _configure(self) -> None:
        pass
    
    ##read Data method to overide
    #
    #This method is to read the data coming from the uC
    @abstractmethod
    def readData(self):
        pass


##Pi Radio communications class
#
#Event driven class using nRF24L01+ to communicate with brewing modules   
class PiRadio(UCComms):

    CONFIGURE_ARUDINO = [0x05]
    BOIL_COMMAND = 0x02
    MASH_COMMAND = 0x01
    FERMENT_COMMAND = 0x03

    _logname = 'PiRadio'
    _log = logging.getLogger(f'{_logname}')
    ##PiRadio constructor
    #
    #set up the pipes for communications
    #@param LOGIN The login details of the MySQL database.
    def __init__(self, LOGIN):
        self.LOGIN=LOGIN
        self.db = dataBase(self.LOGIN, "Brewing")
        super().__init__()
        self.pipes = [[0xE0,0xE0,0xF1,0xF1,0xE0], [0xCC, 0xCE,0xCC,0xCE,0xCC]]
        self.PI_INTERUPT_PIN = 5
        self.cases ={
            self.MASH_COMMAND : self.mash,
            self.BOIL_COMMAND : self.boil,
            self.FERMENT_COMMAND : self.ferment
        }
        self.sendRetryCount = 0

        self.irTemp = np.ones((8,8))
        self.mutex = Lock()
        
    ##PiRadio configure
    #
    #configure the radio with the pipes, send command to brewing modules that Pi is active and redy to listen for data
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
        self.sendData(CONFIGURE_ARUDINO)


    ##Read Data from the radio module
    #
    #If there is data ready, ready it and return whats been recived
    def readData(self):
        if self.radio.available():
            recieved = self.radio.read(self.radio.getDynamicPayloadSize())
            self._log.debug("Recieved data: {}".format(recieved))
            return recieved

    ##Send data to a brewing module
    #
    #try send data to a module. If failed try resending. 
    #@param data The data to send to the brewing module (32 bytes maximum).
    #@param channel The channel to send the data on.
    #@param retries the number of times to try resending the data before giving up and warning user.
    #@return True if sending sucessful, False if failed.
    def sendData(self, data, channel=PI_RADIO_CHANNEL, retries=5):
        self.radio.stopListening()
        self._log.debug("sending data: {}".format(data))
        sent = False
        while not sent:
            sent = self.radio.write(bytes(data))
            if not sent:
                self.sendRetryCount +=1
                if self.sendRetryCount == retries:
                    self._log.warning("Sending Data failed") 
                    break

        self.sendRetryCount = 0
        self._log.debug("data sent")
        self.radio.startListening()
        return sent

    ##Callback method called on Interupt
    #
    #Decide what to do with the data when its recived on GPIO interupt
    def callback(self, channel=0):
        tx, fail, rx  = self.radio.whatHappened()
        if rx or self.radio.available():
            dataIn = self.readData()
            if dataIn is not None:

                thread = Thread(target=self.caseSwitcher, args=dataIn)
                thread.daemon = True   # Daemonize thread
                thread.start()    
                # self.caseSwitcher(dataIn)
                self._log.debug("Data available")

        if tx:
            self._log.debug("Ack Payload sucessfull")

        if fail:
            self._log.debug("Ack Payload fail")

    ##Case Switcher
    #
    #send the data to the appropiated function for processing
    def caseSwitcher(self, data):
        assert data[0] in self.cases
        func = self.cases.get(data[0])
        return func(data[1:])


    ##Mash data recived method
    #
    #If mash data recieved, check if its IR camera data or temprature data and enter into database.
    def mash(self, data):
        if data[0] == 0x01: #if temp sensor data, 12 bit data? (2 bytes)
            #insert temp and volume data
            temp = int.from_bytes(data[1:3], 'big', signed=False)
            #convert 16bit number to temp value
            x = SQLMashMonitor(LOGIN=self.LOGIN)
            x.record(temp=temp, volume=20, pH=0, SG=1.0)
            x.db.cursor.close()
            x.db.db.close()
        elif data[0] == 0x02: #if temp camera data, 8x8 array of 1 byte values
            row = data[1]
            self.mutex.acquire()
            self.irTemp[row][0] = int.from_bytes(data[2:4], 'big', signed=False)/100
            self.irTemp[row][1] = int.from_bytes(data[4:6], 'big', signed=False)/100
            self.irTemp[row][2] = int.from_bytes(data[6:8], 'big', signed=False)/100
            self.irTemp[row][3] = int.from_bytes(data[8:10], 'big', signed=False)/100
            self.irTemp[row][4] = int.from_bytes(data[10:12], 'big', signed=False)/100
            self.irTemp[row][5] = int.from_bytes(data[12:14], 'big', signed=False)/100
            self.irTemp[row][6] = int.from_bytes(data[14:16], 'big', signed=False)/100
            self.irTemp[row][7] = int.from_bytes(data[16:18], 'big', signed=False)/100
            self.mutex.release()
        else:
            self._log.warning("Wrong data type for Mash")

    ##Start Mash
    #
    #method to send command to brewing module to start a mash
    #@param temp The temprature to set the mash to.
    def startMash(self, temp):
        temp *= 10
        temp = int(temp)
        while True:
            if self.sendData([self.MASH_COMMAND, 0x01,(temp>>8)&0xFF, temp&0xFF]):
                break

    ##Stop Mash
    #
    #Send command to brewing module to stop the mash.
    def stopMash(self):
        self.sendData([self.MASH_COMMAND, 0x02])

    ##Boil data recived method
    #
    #If boil data recieved, check if its IR camera data or temprature data and enter into database.
    def boil(self, data):
        if data[0] == 0x01: #if temp sensor data
            #insert temp and volume data
            temp = int.from_bytes(data[1:3], 'big', signed=False)
            #convert 16bit number to temp value
            x = SQLBoilMonitor(LOGIN=self.LOGIN)
            x.record(temp=temp, volume=20)
            x.db.cursor.close()
            x.db.db.close()
            
        elif data[0] == 0x02: #if temp cam data
            pass
        else:
            self._log.warning("Wrong data type for Boil")

    ##Start Boil
    #
    #method to send command to brewing module to start a boil
    #@param temp The temprature to set the boil to.
    def startBoil(self, temp):
        temp *= 10
        temp = int(temp)
        while True:
            if self.sendData([self.BOIL_COMMAND, 0x01,(temp>>8)&0xFF, temp&0xFF]):
                break

    ##Stop Boil
    #
    #Send command to brewing module to stop the boil.
    def stopBoil(self):
        self.sendData([self.BOIL_COMMAND, 0x02])

    ##Feremntaion data recived
    #
    #decifer what btach is in what tank and place data into database.
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
        addtodatabase.db.cursor.close()
        addtodatabase.db.db.close()


    

    


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
        HOST = "192.168.0.17"

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
