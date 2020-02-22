import numpy as np
import logging
import ExceptionLogging
from datetime import datetime
from SqlHandler import SqlTableHandler as dataBase
from Constants import *


import sys
import os

from PyQt5 import QtCore, QtGui, Qt

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, \
                 QPushButton, QHBoxLayout, QVBoxLayout, QTabWidget, \
                    QLabel, QGridLayout, QFrame

from PyQt5.QtCore import QTimer, QDateTime, QTime

# from qwt.qt.QtGui import QApplication, QPen, QBrush, QFrame, QFont, QWidget,
#                           QMainWindow, QToolButton, QIcon, QPixmap, QToolBar,
#                           QHBoxLayout, QLabel, QPrinter, QPrintDialog,
#                           QFontDatabase

# from qwt.qt.QtCore import QSize

# from qwt.qt.QtCore import Qt
from qwt import QwtPlot, QwtPlotMarker, QwtSymbol, QwtLegend, QwtPlotGrid, \
            QwtPlotCurve, QwtPlotItem, QwtLogScaleEngine, QwtText,  \
            QwtPlotRenderer, QwtScaleDraw, QwtText

class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Sunken)


class TimeScaleDraw(QwtScaleDraw):

    intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('mins', 60),
    ('secs', 1),
    )

    def __init__(self, *args):
        QwtScaleDraw.__init__(self, *args)
        self.baseTime = datetime.now()
        self.fmt='H:M:S\nd-M-Y'
        #tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)


    def label(self, value):
        #dt = self.baseTime + datetime(second=value)
        dt = self.display_time(value)
        return QwtText(dt)
        #-self.startTime#.fromMSecsSinceEpoch((value+self.count))#+datetime.timestamp(datetime.now())))
       # return QwtText(dt.toString(self.fmt))

    def display_time(self,seconds, granularity=2):
        result = []
        for name, count in self.intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return '\n '.join(result[:granularity])


class TabGraph(QWidget):

    _logname = 'TabGraph'
    _log = logging.getLogger(f'{_logname}')

    intervals = (
    ('weeks', 604800),  # 60 * 60 * 24 * 7
    ('days', 86400),    # 60 * 60 * 24
    ('hours', 3600),    # 60 * 60
    ('mins', 60),
    ('secs', 1),
    )

    def __init__(self):
        super().__init__()

        self.dataY = np.zeros(0)
        self.dataX = np.linspace(0,len(self.dataY),len(self.dataY))

        self.count = 0
        self.timeLabel = QLabel("Timer:")
        self.timeLabel.setAlignment(QtCore.Qt.AlignRight)

        self.tempLabel = QLabel("Temp:")
        self.tempLabel.setAlignment(QtCore.Qt.AlignRight)

        self.targetTimeLabel = QLabel("Target: ")
        self.targetTimeLabel.setAlignment(QtCore.Qt.AlignRight)
        self.targetTempLabel = QLabel("Target: ")
        self.targetTempLabel.setAlignment(QtCore.Qt.AlignRight)
        self.targetLayout = QHBoxLayout()
        self.targetLayout.addWidget(self.targetTempLabel)
        self.targetLayout.addWidget(self.targetTimeLabel)

        self.startButton = QPushButton()
        self.stopButton = QPushButton()

        self.plot = QwtPlot()
        self.curve = QwtPlotCurve()
        self.curve.attach(self.plot)
        self.plot.resize(1000, 1000)
        self.plot.replot()
        self.plot.show()

        self.recipeGrid = QGridLayout()
        self.recipeGrid.addWidget(QLabel(f"Recipe:"),0,0)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['recipeName']}"),0,1)
        self.recipeGrid.addWidget(QHLine(), 1, 0, 1, 2)

        self.currentStatus = QHBoxLayout()
        self.currentStatus.addWidget(self.tempLabel)
        self.currentStatus.addWidget(self.timeLabel)

        self.plotLayout = QVBoxLayout()
        self.plotLayout.addLayout(self.targetLayout)
        self.plotLayout.addLayout(self.currentStatus)
        self.plotLayout.addWidget(self.plot)


        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.startButton)
        buttonLayout.addWidget(self.stopButton)
        buttonLayout.addLayout(self.recipeGrid)
        buttonLayout.addStretch(100)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(buttonLayout)
        mainLayout.addLayout(self.plotLayout)

        vLayout = QVBoxLayout(self)
        vLayout.addLayout(mainLayout)
        self.firstFlag = True


    def insertSample(self,sample):
        #self.dataY = np.append(self.dataY, [sample])
        # self.dataYHistory = np.roll(self.dataYHistory,1)
        # self.dataYHistory[0] = sample
        # self.dataX = np.append(self.dataX,[self.display_time(self.count)])
        self.updatePlot()
        

    def updatePlot(self):

        


        self.timeLabel.setText("Timer: {}".format(self.display_time(self.count)))
        self.tempLabel.setText("Temp: {}{}".format(self.dataY[-1],DEGREESC))
        
        self.dataX = np.linspace(0, len(self.dataY),len(self.dataY))
        # self.dataX = np.linspace(0, len(self.dataY)/60,len(self.dataY))
        self.curve.setData(self.dataX, self.dataY)
        self.plot.setAxisScaleDraw(QwtPlot.xBottom, TimeScaleDraw())
        self.plot.replot()
        self.plot.show()

    def addCounter(self, seconds):
        self.count += seconds
        self._log.info(f"Count: {self.count}")

    def display_time(self,seconds, granularity=2):
        result = []
        for name, count in self.intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return ', '.join(result[:granularity])

    



class TabMash(TabGraph):
    _logname = 'TabMash'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, recipedata:dict):
        self.recipedata = recipedata
        super().__init__()
        
        self.startButton.setText(self.tr('Start Mash'))
        self.stopButton.setText(self.tr('&Stop Mash'))
        self.plot.setTitle("Mash")
        self.curve.setTitle("Temprature")

        self.targetTimeLabel.setText(f"Set mash time: {self.recipedata['mashTime']} mins")
        self.targetTempLabel.setText(f"Set mash temp: {self.recipedata['mashTemp']}{DEGREESC}")
        

class TabBoil(TabGraph):
    _logname = 'TabBoil'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, recipedata:dict):
        self.recipedata = recipedata
        super().__init__()
        self.plot.setTitle("Boil")
        self.curve.setTitle("Temprature")

        self.startButton.setText(self.tr('Start Boil'))
        self.stopButton.setText(self.tr('&Stop Boil'))

        self.targetTimeLabel.setText(f"Set boil time: {self.recipedata['boilTime']} mins")
        self.targetTempLabel.setText(f"Set boil temp: {self.recipedata['boilTemp']}{DEGREESC}")

        self.recipeGrid.addWidget(QLabel(f"Hop"),3,0)
        self.recipeGrid.addWidget(QLabel(f"Time"),3,1)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['hop1'][0]}"),4,0)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['hop1'][1]}"),4,1)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['hop2'][0]}"),5,0)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['hop2'][1]}"),5,1)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['hop3'][0]}"),6,0)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['hop3'][1]}"),6,1)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['hop4'][0]}"),7,0)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['hop4'][1]}"),7,1)
        


class MonitorWindow(QWidget):

    _logname = 'MonitorWindow'
    _log = logging.getLogger(f'{_logname}')
    
    def __init__(self, LOGIN, batchID):
        super().__init__()
        self.setWindowTitle("Monitor")
        self.LOGIN = LOGIN
        db = dataBase(self.LOGIN, "Brewing")
        self.batchID = batchID

        sql = f"SELECT * FROM Brews WHERE id = '{self.batchID}'"
        query = db.custom(sql)

        self.recipedata = {}
        self.recipedata['recipeName'] = query[0][1]
        self.recipedata['recipeDate'] = query[0][2]
        self.recipedata['mashTemp']   = query[0][3]
        self.recipedata['mashTime']   = query[0][4]
        self.recipedata['boilTemp']   = query[0][5]
        self.recipedata['boilTime']   = query[0][6]
        self.recipedata['hop1']       = (query[0][7],query[0][8])
        self.recipedata['hop2']       = (query[0][9],query[0][10])
        self.recipedata['hop3']       = (query[0][11],query[0][12])
        self.recipedata['hop4']       = (query[0][13],query[0][14])
        self.recipedata['fermenttemp']= query[0][15]
        
        self.tabs = QTabWidget()
        self.tabMash = TabMash(self.recipedata)
        self.tabBoil = TabBoil(self.recipedata)
        self.tabs.resize(100,1000)

        self.tabs.addTab(self.tabMash,"Mash")
        self.tabs.addTab(self.tabBoil,"Boil")

        self.quitButton = QPushButton(self.tr('&Quit'))
        self.quitButton.clicked.connect(lambda: self.close())
        
        self.tabBoil.startButton.clicked.connect(self.boilStartClicked)
        self.tabBoil.stopButton.clicked.connect(self.boilStopClicked)

        self.tabMash.startButton.clicked.connect(self.mashStartClicked)
        self.tabMash.stopButton.clicked.connect(self.mashStopClicked)
        

        hLayout = QHBoxLayout()
        hLayout.addStretch(100)
        hLayout.addWidget(self.quitButton)
        
        vLayout = QVBoxLayout(self)
        vLayout.addWidget(self.tabs) 
        vLayout.addLayout(hLayout)  

        self.mashCount = 0
        self.boilTimer, self.mashTimer = QTimer(self), QTimer(self)
        self.boilTimer.timeout.connect(self.boilCounter)
        self.mashTimer.timeout.connect(self.mashCounter)

        if __name__ == "__main__":
            self.boilMonitor = SQLBoilMonitor(self.LOGIN)
            self.fakeBoilTimer = QTimer(self)
            self.fakeBoilCount = 0
            self.fakeBoilTimer.timeout.connect(self.fakeBoilData)
        

    def boilStartClicked(self):
        self.boilTimer.start(100)
        self.fakeBoilTimer.start(100)

    def boilStopClicked(self):
        self.boilTimer.stop()
        self.fakeBoilTimer.stop()

    def mashStartClicked(self):
        '''
        Set mash Uc up with 
        '''
        self.mashTimer.start(1000)

    def mashStopClicked(self):
        self.mashTimer.stop()

    def mashCounter(self):
        '''
        collect mash data
        '''

        self.mashCount += 1
        self.tabMash.addCounter(1)
        self.tabMash.insertSample(np.sin(self.mashCount/4))
        
    def boilCounter(self):
        db = dataBase(self.LOGIN, "Brewing")
        sql = f"SELECT Temp FROM BoilMonitor WHERE BatchID = '{self.batchID}'"
        query = db.custom(sql)
        # for x in query:
        #     self._log.debug(x)

        self.tabBoil.addCounter(1)
        results = [i[0] for i in query]
        self.tabBoil.dataY = np.fromiter(results, dtype=float)
        self._log.debug(self.tabBoil.dataY)
        self.tabBoil.updatePlot()


    def fakeBoilData(self):
        #temp = float(np.exp(self.fakeBoilCount, dtype=float))
        x = self.fakeBoilCount
        temp = np.divide(10*np.power(x,3)+2*np.square(x)-x, 2*np.power(x,3)+10*np.square(x)+1)
        
        
        self.boilMonitor.record(float(temp),10)
        self.fakeBoilCount +=1



if __name__ == "__main__":
    import logging
    from threading import Thread
    import time
    from SQLBrewingComms import SQLBoilMonitor
    from SqlHandler import SqlTableHandler as db

    logging.basicConfig(format ='%(asctime)s :%(name)-7s :%(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)

    HOST = "localhost"
    USER = "Test"
    PASSWORD = "BirraMosfeti"
    LOGIN = [HOST,USER,PASSWORD]
    database = db(LOGIN,"Brewing")
    batchID = database.maxIdFromTable("Brews")

    # boilMonitor = SQLBoilMonitor(LOGIN)

    app = QApplication(sys.argv)
    #window = MonitorWindow(mashtime=mashtime, boiltime=boiltime,hop1=hop1,hop2=hop2,hop3=hop3,hop4=hop4)
    window = MonitorWindow(LOGIN, batchID)
    window.show()
    sys.exit(app.exec_())