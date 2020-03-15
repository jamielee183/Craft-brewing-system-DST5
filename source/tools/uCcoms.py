import numpy as np
from abc import ABCMeta, abstractmethod
from threading import Thread, Event
import logging


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
    _log = logging.getlogger(f'{_logname}')

    def __init__(self):
        super().__init__()

    def _configure(self) -> None:




    


