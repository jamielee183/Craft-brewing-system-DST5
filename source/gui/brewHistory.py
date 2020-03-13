import numpy as np
import logging
import sys
import os

from PyQt5 import QtCore, QtGui, Qt

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, \
                 QPushButton, QHBoxLayout, QVBoxLayout, QTabWidget, \
                    QLabel, QGridLayout

from PyQt5.QtCore import QTimer, QDateTime, QTime

from qwt import QwtPlot, QwtPlotMarker, QwtSymbol, QwtLegend, QwtPlotGrid, \
            QwtPlotCurve, QwtPlotItem, QwtLogScaleEngine, QwtText,  \
            QwtPlotRenderer, QwtScaleDraw, QwtText

import source.tools.exceptionLogging
from source.tools.constants import *


class BrewHistory(QWidget):

    _logname = 'BrewHistory'
    _log = logging.getLogger(f'{_logname}')

    def __intit__(self, LOGIN):
        self.LOGIN = LOGIN