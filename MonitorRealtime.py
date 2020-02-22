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

class HistoryPlot(QWidget):

    _logname = 'HistoryPlot'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self,length):
        super().__init__()
        self.length = length
        self.dataYHistory = np.zeros(self.length)
        self.dataXHistory = np.linspace(len(self.dataYHistory),0,len(self.dataYHistory))

       

    def setup(self, namePlot, nameCurve):
        self.plotHistory = QwtPlot(namePlot)
        # self.mashPlot.setAxisScaleDraw(QwtPlot.xBottom, TimeScaleDraw())
        self.curveHistory = QwtPlotCurve(nameCurve)
        self.curveHistory.attach(self.plotHistory)
        self.plotHistory.resize(10, 10)
        self.plotHistory.replot()
        self.plotHistory.show()

        self.plotLayout = QHBoxLayout()
        self.plotLayout.addWidget(self.plotHistory)

    def updatePlot(self):
        self.dataXHistory = np.linspace(len(self.dataYHistory)/60, 0,len(self.dataYHistory))
        self.curveHistory.setData(self.dataXHistory, self.dataYHistory)
        self.plotHistory.replot()
        self.plotHistory.show()

    def insertSample(self, sample):
        self.dataYHistory = np.roll(self.dataYHistory,1)
        self.dataYHistory[0] = sample
        self.updatePlot()
    
