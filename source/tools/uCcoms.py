import numpy as np
from abc import ABCMeta, abstractmethod
from threading import Thread, Event
import logging
import sys, os
# if running from command line, need to append the parent directories to the PATH
# so python knows where to find "source.file"
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
from source.tools.constants import *


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

    def __init__(self):
        super().__init__()
        self.pipes = [[0xE0,0xE0,0xF1,0xF1,0xE0], [0xCC, 0xCE,0xCC,0xCE,0xCC]]
        

    def _configure(self) -> None:

        self.radio = RF24(25,8)
        self.radio.begin()
        self.radio.openReadingPipe(1,bytes(self.pipes[1]))
        self.radio.openWritingPipe(bytes(self.pipes[0]))
        self.radio.setChannel(PI_RADIO_CHANNEL)
        self.radio.eneableDynamicPayloads()
        self.radio.setRetries(5,15)
        self.radio.startListening()


    def readData(self, channel=PI_RADIO_CHANNEL):
        self.radio.setChannel(channel)
        if self.radio.available():
            recieved = self.radio.read(self.radio.getDynamicPayloadSize())
            self._log.debug("Recieved data: {}".format(recieved.decode('utf-8')))
            return recieved.decode('utf-8')

    def sendData(self, channel=PI_RADIO_CHANNEL):
        self.radio.stopListening()

    

    


