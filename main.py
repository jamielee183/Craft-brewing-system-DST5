import numpy as np
import logging
from datetime import datetime
from SqlHandler import SqlTableHandler as dataBase


import sys
import os

from PyQt5 import QtCore, QtGui, Qt

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, \
                 QPushButton, QHBoxLayout, QVBoxLayout, QTabWidget, \
                    QLabel, QGridLayout

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


class TimeScaleDraw(QwtScaleDraw):
    def __init__(self, *args):
        QwtScaleDraw.__init__(self, *args)
        self.fmt='mm:s'#\nd-MMM-yyyy'
        self.startTime = QTime
        #tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)


    def label(self, value):
        dt = self.startTime+value
        #-self.startTime#.fromMSecsSinceEpoch((value+self.count))#+datetime.timestamp(datetime.now())))
        return QwtText(dt.toString(self.fmt))


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

        self.target1Label = QLabel("Target: ")
        self.target1Label.setAlignment(QtCore.Qt.AlignRight)
        self.target2Label = QLabel("Target: ")
        self.target2Label.setAlignment(QtCore.Qt.AlignRight)
        self.targetLayout = QHBoxLayout()
        self.targetLayout.addWidget(self.target2Label)
        self.targetLayout.addWidget(self.target1Label)


    def setup(self,namePlot,nameCurve,target1,target2):
        self.plot = QwtPlot(namePlot)
        # self.mashPlot.setAxisScaleDraw(QwtPlot.xBottom, TimeScaleDraw())
        self.curve = QwtPlotCurve(nameCurve)
        self.curve.attach(self.plot)
        self.plot.resize(1000, 1000)
        self.plot.replot()
        self.plot.show()

        self.target1Label.setText(f"{target1}")
        self.target2Label.setText(f"{target2}")


        self.plotLayout = QVBoxLayout()
        self.plotLayout.addLayout(self.targetLayout)
        self.plotLayout.addWidget(self.timeLabel)
        self.plotLayout.addWidget(self.plot)

    def insertSample(self,sample):
        #self.dataY = np.append(self.dataY, [sample])
        # self.dataYHistory = np.roll(self.dataYHistory,1)
        # self.dataYHistory[0] = sample
        # self.dataX = np.append(self.dataX,[self.display_time(self.count)])
        self.updatePlot()
        

    def updatePlot(self):
        self.timeLabel.setText("Timer: {}".format(self.display_time(self.count)))

        self.dataX = np.linspace(0, len(self.dataY)/60,len(self.dataY))
        self.curve.setData(self.dataX, self.dataY)
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

    def __init__(self, time, temp):
        super().__init__()
        #self.setup("Mash", "Temperature")
        self.setup("Boil", "Temprature",f"Mash time: {time}",f"Temp target: {temp}")
        self.startMashButton = QPushButton(self.tr('Start Mash'))
        self.stopMashButton = QPushButton(self.tr('Stop Mash'))
        

        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.startMashButton)
        buttonLayout.addWidget(self.stopMashButton)
        buttonLayout.addStretch(100)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(buttonLayout)
        mainLayout.addLayout(self.plotLayout)

        vLayout = QVBoxLayout(self)
        vLayout.addLayout(mainLayout)
        


class TabBoil(TabGraph):
    _logname = 'TabBoil'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, time, temp, hop1, hop2, hop3, hop4):
        super().__init__()
        self.setup("Boil", "Temprature",f"Boil time: {time}",f"Temp target: {temp}")
        self.startBoilButton = QPushButton(self.tr('Start Boil'))
        self.stopBoilButton = QPushButton(self.tr('Stop Boil'))


        self.hopGrid = QGridLayout()
        self.hopGrid.addWidget(QLabel(f"Hop"),0,0)
        self.hopGrid.addWidget(QLabel(f"Time"),0,1)
        self.hopGrid.addWidget(QLabel(f"{hop1[0]}"),1,0)
        self.hopGrid.addWidget(QLabel(f"{hop1[1]}"),1,1)
        self.hopGrid.addWidget(QLabel(f"{hop2[0]}"),2,0)
        self.hopGrid.addWidget(QLabel(f"{hop2[1]}"),2,1)
        self.hopGrid.addWidget(QLabel(f"{hop3[0]}"),3,0)
        self.hopGrid.addWidget(QLabel(f"{hop3[1]}"),3,1)
        self.hopGrid.addWidget(QLabel(f"{hop4[0]}"),4,0)
        self.hopGrid.addWidget(QLabel(f"{hop4[1]}"),4,1)
        

        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(self.startBoilButton)
        buttonLayout.addWidget(self.stopBoilButton)
        buttonLayout.addLayout(self.hopGrid)
        buttonLayout.addStretch(100)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(buttonLayout)
        mainLayout.addLayout(self.plotLayout)

        vLayout = QVBoxLayout(self)
        vLayout.addLayout(mainLayout)


class MonitorWindow(QWidget):

    _logname = 'MonitorWindow'
    _log = logging.getLogger(f'{_logname}')
    
    def __init__(self, LOGIN, batchID):
    #def __init__(self, mashtime:int, boiltime:int, hop1:tuple, hop2:tuple, hop3:tuple, hop4:tuple):
        super().__init__()
        self.setWindowTitle("Monitor")
        self.LOGIN = LOGIN
        db = dataBase(self.LOGIN, "Brewing")
        self.batchID = batchID
        sql = f"SELECT * FROM Brews WHERE id = '{self.batchID}'"
        query = db.custom(sql)
        self._log.debug(f"batchID: {self.batchID}, sql return: {query}")

        self.recipeName = query[0][1]
        self.recipeDate = query[0][2]
        self.mashTemp   = query[0][3]
        self.mashTime   = query[0][4]
        self.boilTemp   = query[0][5]
        self.boilTime   = query[0][6]
        self.hop1       = (query[0][7],query[0][8])
        self.hop2       = (query[0][9],query[0][10])
        self.hop3       = (query[0][11],query[0][12])
        self.hop4       = (query[0][13],query[0][14])
        self.fermenttemp= query[0][15]
        #self._log.info(self.recipeName)

        #self.layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tabMash = TabMash(self.mashTime, self.mashTemp)
        self.tabBoil = TabBoil(self.boilTime, self.boilTemp ,self.hop1,self.hop2,self.hop3,self.hop4)
        self.tabs.resize(100,1000)

        self.tabs.addTab(self.tabMash,"Mash")
        self.tabs.addTab(self.tabBoil,"Boil")

        self.quitButton = QPushButton(self.tr('&Quit'))
        self.quitButton.clicked.connect(lambda: self.close())
        
        self.tabBoil.startBoilButton.clicked.connect(self.boilStartClicked)
        self.tabBoil.stopBoilButton.clicked.connect(self.boilStopClicked)

        self.tabMash.startMashButton.clicked.connect(self.mashStartClicked)
        self.tabMash.stopMashButton.clicked.connect(self.mashStopClicked)
        

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


        self.fakeBoilTimer = QTimer(self)
        self.fakeBoilCount = 0
        self.fakeBoilTimer.timeout.connect(self.fakeBoilData)
        

    def boilStartClicked(self):
        self.boilTimer.start(1000)
        self.fakeBoilTimer.start(1000)

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
        #self.tabBoil.insertSample(np.sin(self.boilCount/6))
        # self.tabBoil.insertSample(query[3])
        # self._log.info(f"inserted count {self.boilCount}")

    def fakeBoilData(self):
        #temp = float(np.exp(self.fakeBoilCount, dtype=float))
        temp = np.divide(self.fakeBoilCount,
            (np.square(self.fakeBoilCount)+self.fakeBoilCount+1))
        
        
        boilMonitor.record(float(temp),10)
        self.fakeBoilCount +=1



if __name__ == "__main__":
    import logging
    from threading import Thread
    import time
    from SQLBrewingComms import SQLBoilMonitor

    logging.basicConfig(format ='%(asctime)s :%(name)-7s :%(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)

    HOST = "localhost"
    USER = "Test"
    PASSWORD = "BirraMosfeti"
    LOGIN = [HOST,USER,PASSWORD]
    batchID = 2

    boilMonitor = SQLBoilMonitor(LOGIN)


    mashtime = 150 #mashtime in minutes
    boiltime = 150 #mashtime in minutes


    app = QApplication(sys.argv)
    #window = MonitorWindow(mashtime=mashtime, boiltime=boiltime,hop1=hop1,hop2=hop2,hop3=hop3,hop4=hop4)
    window = MonitorWindow(LOGIN, batchID)
    window.show()
    sys.exit(app.exec_())