import numpy as np
import logging
from datetime import datetime

import sys
import os

from QLed import QLed
from PyQt5 import QtCore, QtGui, Qt

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, \
                 QPushButton, QHBoxLayout, QVBoxLayout, QTabWidget, \
                    QLabel, QGridLayout, QFrame, QMessageBox

from PyQt5.QtCore import QTimer, QDateTime, QTime

from qwt import QwtPlot, QwtPlotMarker, QwtSymbol, QwtLegend, QwtPlotGrid, \
            QwtPlotCurve, QwtPlotItem, QwtLogScaleEngine, QwtText,  \
            QwtPlotRenderer, QwtScaleDraw, QwtText


# if running from command line, need to append the parent directories to the PATH
# so python knows where to find "source.file"
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
import source.tools.exceptionLogging
from source.tools.sqlHandler import SqlTableHandler as dataBase
from source.tools.sqlBrewingComms import SQLBoil
from source.tools.constants import *
from source.gui.guitools import BoilMashTimeScaleDraw, QHLine, QVLine, BoilFinishedPopup

 

class TabGraph(QWidget):

    _logname = 'TabGraph'
    _log = logging.getLogger(f'{_logname}')



    def __init__(self, LOGIN, parent=None):
        super().__init__(parent)
        self.LOGIN = LOGIN
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

        self.startButton = QPushButton()
        self.stopButton = QPushButton()

        self.plot = QwtPlot()
        self.curve = QwtPlotCurve()
        self.curve.attach(self.plot)
        self.plot.resize(1000, 1000)
        self.plot.replot()
        self.plot.show()

        self.tempStatusLED = QLed(self, onColour=QLed.Green, offColour=QLed.Red, shape=QLed.Circle)
        self.tempStatusLED.value=False

        self.timeStatusLED = QLed(self, onColour=QLed.Green, offColour=QLed.Red, shape=QLed.Circle)
        self.timeStatusLED.value=False


        self.recipeGrid = QGridLayout()
        self.recipeGrid.addWidget(QLabel(f"Recipe:"),0,0)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['recipeName']}"),0,1)
        self.recipeGrid.addWidget(QHLine(), 1, 0, 1, 2)


        self.tempLayout = QHBoxLayout()
        self.tempLayout.addWidget(self.targetTempLabel)
        self.tempLayout.addStretch(10)
        self.tempLayout.addWidget(self.tempLabel)
        self.tempLayout.addStretch(10)
        self.tempLayout.addWidget(self.tempStatusLED)

        self.timeLayout = QHBoxLayout()
        self.timeLayout.addWidget(self.targetTimeLabel)
        self.timeLayout.addStretch(10)
        self.timeLayout.addWidget(self.timeLabel)
        self.timeLayout.addStretch(10)
        self.timeLayout.addWidget(self.timeStatusLED)

        self.plotLayout = QVBoxLayout()
        self.plotLayout.addLayout(self.timeLayout)
        self.plotLayout.addStretch(10)
        self.plotLayout.addLayout(self.tempLayout)
        self.plotLayout.addStretch(10)
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

        self.secondsTimer = QTimer(self)
        self.secondsTimer.timeout.connect(lambda:self.addTimer(1))


    def insertSample(self,sample):
        #self.dataY = np.append(self.dataY, [sample])
        # self.dataYHistory = np.roll(self.dataYHistory,1)
        # self.dataYHistory[0] = sample
        # self.dataX = np.append(self.dataX,[self.display_time(self.count)])
        # self.updatePlot()
        pass
        

    def addTimer(self, seconds):
        self.count += seconds

    def display_time(self,seconds, granularity=2):
        result = []
        for name, count in TIME_INTERVALS:
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

    def __init__(self, LOGIN, batchID, recipedata:dict, parent=None):
        self.recipedata = recipedata
        self.batchID = batchID
        super().__init__(LOGIN, parent)
        
        self.startButton.setText(self.tr('Start Mash'))
        self.stopButton.setText(self.tr('&Stop Mash'))
        self.plot.setTitle("Mash")
        self.curve.setTitle("Temprature")

        self.targetTimeLabel.setText(f"Set mash time: {self.recipedata['mashTime']} mins")
        self.targetTempLabel.setText(f"Set mash temp: {self.recipedata['mashTemp']}{DEGREESC}")
        
    def updatePlot(self):

        db = dataBase(self.LOGIN, "Brewing")
        sql = f"SELECT Temp FROM Mash WHERE BatchID = '{self.batchID}'"
        query = db.custom(sql)

        results = [i[0] for i in query]

        sql = f"SELECT TimeStamp FROM Mash WHERE BatchID = '{self.batchID}'"
        query = db.custom(sql)


        self.timeStamps = [i[0] for i in query]
        # self._log.debug(self.timeStamps)
        self.dataY = np.fromiter(results, dtype=float)
        
        self.dataX = np.linspace(0, len(self.dataY), len(self.dataY))
        self.curve.setData(self.dataX, self.dataY)
        self.plot.setAxisScaleDraw(QwtPlot.xBottom, BoilMashTimeScaleDraw(self.timeStamps))
        self.plot.replot()
        self.plot.show()

        if len(self.dataX) == 0:
            self.timeLabel.setText("Timer:")
            self.tempLabel.setText("Temp:")
        else:
            # timerlabel = TimeScaleDraw(self.timeStamps).label(self.dataX[-1])}")
            self.timeLabel.setText("Timer: {}".format(self.display_time(self.count)))
            self.tempLabel.setText("Temp: {}{}".format(self.dataY[-1],DEGREESC))


class TabBoil(TabGraph):
    _logname = 'TabBoil'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, LOGIN, batchID, recipedata:dict, parent=None):
        self.recipedata = recipedata
        self.batchID = batchID
        super().__init__(LOGIN, parent)
        self.sqlBoilComms = SQLBoil(self.LOGIN)
        self.plot.setTitle("Boil")
        self.curve.setTitle("Temprature")

        self.startButton.setText(self.tr('Start Boil'))
        self.stopButton.setText(self.tr('&Stop Boil'))

        self.targetTimeLabel.setText(f"Set boil time: {self.recipedata['boilTime']} mins")
        self.targetTempLabel.setText(f"Set boil temp: {self.recipedata['boilTemp']}{DEGREESC}")

        self.recipeLED = [QLed(self, onColour=QLed.Green, 
                            offColour=QLed.Red, 
                            shape=QLed.Circle)
                            for _ in range(4)]


        self.hoptimes = {
            '1' :  self.sqlBoilComms.hop1Timer,
            '2' :  self.sqlBoilComms.hop2Timer,
            '3' :  self.sqlBoilComms.hop3Timer,
            '4' :  self.sqlBoilComms.hop4Timer
        }


        # self.recipeLED[0].setOffColour(QLed.Yellow)
        # # self.recipeLED[1].setOffColour(QLed.Yellow)
        # self.recipeLED[2].setOffColour(QLed.Yellow)

        self.hopTimeLabels = [QLabel("") for _ in range(4)]

        self.recipeGrid.addWidget(QLabel(f"Hop"),3,0)
        self.recipeGrid.addWidget(QLabel(f"Time"),3,1)
        self.recipeGrid.addWidget(QLabel(f"Hop\nStatus"),3,2)
        self.recipeGrid.addWidget(QLabel(f"Time\nadded"),3,3)
        for i in range(4):
            self.recipeGrid.addWidget(QLabel("{}".format(self.recipedata[f'hop{i+1}'][0])),4+i,0)
            self.recipeGrid.addWidget(QLabel("{}".format(self.recipedata[f'hop{i+1}'][1])),4+i,1)
            self.recipeGrid.addWidget(self.recipeLED[i],4+i,2)
            self.recipeLED[i].setMaximumSize(35,35)
            self.recipeGrid.addWidget(self.hopTimeLabels[i],4+i,3)

        # for i in range(4):
        #Doesn't work in for loop for some reason
        self.recipeLED[0].clicked.connect(lambda: self.ledClicked(self.recipeLED[0],1))
        self.recipeLED[1].clicked.connect(lambda: self.ledClicked(self.recipeLED[1],2))
        self.recipeLED[2].clicked.connect(lambda: self.ledClicked(self.recipeLED[2],3))
        self.recipeLED[3].clicked.connect(lambda: self.ledClicked(self.recipeLED[3],4))

            

    def ledClicked(self,led,hopNo):
        if self.secondsTimer.isActive():
            if led.offColour == QLed.Yellow and led.value==False:
                self.hoptimes[f'{hopNo}']()
                # led.value=True
                self._log.info("Hop added")

            elif led.offColour == QLed.Red and led.value==False:            
                self.hoptimes[f'{hopNo}']()
                # led.value=True
                self._log.info(f"Hop added early")

            elif led.value == True:
                self._log.info(f"Hop {hopNo} already added")
                return
            else:
                raise Exception("Somethings gone terribly wrong")

            led.value=True
            self.hopTimeLabels[hopNo-1].setText("{}".format(self.display_time(self.count)))


    def updatePlot(self):

        db = dataBase(self.LOGIN, "Brewing")
        sql = f"SELECT Temp FROM BoilMonitor WHERE BatchID = '{self.batchID}'"
        query = db.custom(sql)

        results = [i[0] for i in query]

        sql = f"SELECT TimeStamp FROM BoilMonitor WHERE BatchID = '{self.batchID}'"
        query = db.custom(sql)


        self.timeStamps = [i[0] for i in query]
        # self._log.debug(self.timeStamps)
        self.dataY = np.fromiter(results, dtype=float)
        
        self.dataX = np.linspace(0, len(self.dataY), len(self.dataY))
        self.curve.setData(self.dataX, self.dataY)
        self.plot.setAxisScaleDraw(QwtPlot.xBottom, BoilMashTimeScaleDraw(self.timeStamps))
        self.plot.replot()
        self.plot.show()

        if len(self.dataX) == 0:
            self.timeLabel.setText("Timer:")
            self.tempLabel.setText("Temp:")
        else:
            # timerlabel = TimeScaleDraw(self.timeStamps).label(self.dataX[-1])}")
            self.timeLabel.setText("Timer: {}".format(self.display_time(self.count)))
            self.tempLabel.setText("Temp: {}{}".format(self.dataY[-1],DEGREESC))     

        if (self.dataY[-1] < (self.recipedata['boilTemp']-0.5)) or (self.dataY[-1] > (self.recipedata['boilTemp']+0.5)):
            self.tempStatusLED.value=False
        else:
            self.tempStatusLED.value=True

        for i in range(4):
            if self.count/60 > self.recipedata[f'hop{i+1}'][1]:
                self.recipeLED[i].setOffColour(QLed.Yellow)

class MonitorWindow(QWidget):

    _logname = 'MonitorWindow'
    _log = logging.getLogger(f'{_logname}')
    
    def __init__(self, LOGIN, batchID, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monitor")
        self.LOGIN = LOGIN
        db = dataBase(self.LOGIN, "Brewing")
        self.batchID = batchID

        sql = f"SELECT * FROM Brews WHERE id = '{self.batchID}'"
        query = db.custom(sql)

        self.recipedata = {}
        self.recipedata['batchID']    = self.batchID
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
        self.tabMash = TabMash(LOGIN, self.batchID, self.recipedata, parent=self)
        self.tabBoil = TabBoil(LOGIN, self.batchID, self.recipedata, parent=self)
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
        self.boilPlotUpdateTimer, self.mashPlotUpdateTimer = QTimer(self), QTimer(self)
        self.boilPlotUpdateTimer.timeout.connect(self.updateBoilPlot)
        self.boilPlotUpdateTimer.start(1000)
        self.mashPlotUpdateTimer.timeout.connect(self.updateMashPlot)
        self.mashPlotUpdateTimer.start(1000)


        if __name__ == "__main__":
            self.boilMonitor = SQLBoilMonitor(self.LOGIN)
            self.fakeBoilTimer = QTimer(self)
            self.fakeBoilCount = 0
            self.fakeBoilTimer.timeout.connect(self.fakeBoilData)
        

    def boilStartClicked(self):
        if not self.tabBoil.secondsTimer.isActive():
            msg = 'Start boiling? \n set {}{} for {} minutes'.format(self.recipedata['boilTemp'],DEGREESC,self.recipedata['boilTime'])
            reply = QMessageBox.question(self, 'Continue?', 
                    msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                '''
                TODO: Set Boil Uc
                '''
                self.fakeBoilTimer.start(100)   #TODO: remove once we can get real data
                self.tabBoil.secondsTimer.start(1000)
                self.tabBoil.sqlBoilComms.startTimer()
                self.tabBoil.timeStatusLED.value=True
        elif self.tabBoil.secondsTimer.isActive():
            x = divmod(self.tabBoil.count,60)
            msg = 'Boil already running: {} mins {} secs'.format(x[0],x[1])
            reply = QMessageBox.question(self, 'oops', 
                    msg, QMessageBox.Ok)
        else:
            raise Exception("Boil Error")

    def boilStopClicked(self):
        if self.tabBoil.secondsTimer.isActive():
            x = divmod(self.tabBoil.count,60)
            msg = 'Stop boiling?\nCurrent time: {} mins {} secs\nRecipe time: {} mins'.format(x[0],x[1], self.recipedata['boilTime'] )
            reply = QMessageBox.question(self, 'Continue?', 
                    msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                '''
                TODO: TURN OFF BOIL uC 
                '''
                self.fakeBoilTimer.stop()
                # self.boilPlotUpdateTimer.stop()
                self.tabBoil.secondsTimer.stop()
                self.tabBoil.sqlBoilComms.endTimer()
                self.tabBoil.timeStatusLED.value=False
                
                boilPopup = BoilFinishedPopup(LOGIN=self.LOGIN, recipeData=self.recipedata, parent=self)

                if boilPopup.exec_():
                    tankNumber = boilPopup.selectedTank
                    self._log.debug('Batch {} being sent to tank {}'.format(self.recipedata['batchID'],tankNumber))
                    '''EMIT SIGNAL with fermentation tank number'''
                    self.close()
                    
                

        elif not self.tabBoil.secondsTimer.isActive():
            msg = 'No Boil currently running'
            reply = QMessageBox.question(self, 'oops', 
                    msg, QMessageBox.Ok)


    def mashStartClicked(self):
        '''
        Set mash Uc up with 
        '''
        self.tabMash.secondsTimer.start(1000)

    def mashStopClicked(self):
        self.mashPlotUpdateTimer.stop()
        self.tabMash.secondsTimer.stop()

    def updateMashPlot(self):
        '''
        collect mash data
        '''

        # self.mashCount += 1
        # self.tabMash.addTimer(1)
        # self.tabMash.insertSample(np.sin(self.mashCount/4))
        self.tabMash.updatePlot()
        
    def updateBoilPlot(self):
        '''
        collect boil data
        '''
        self.tabBoil.updatePlot()


    def fakeBoilData(self):
        #temp = float(np.exp(self.fakeBoilCount, dtype=float))
        x = self.fakeBoilCount
        temp = np.divide(10*np.power(x,3)+2*np.square(x)-x, 2*np.power(x,3)+10*np.square(x)+1)
        
        
        self.boilMonitor.record(float(temp),10)
        self.fakeBoilCount +=1



if __name__ == "__main__":
    import logging
    _logname = 'BoilMashMonitorMain'
    _log = logging.getLogger(f'{_logname}')
    

    from threading import Thread
    import time
    from source.tools.sqlBrewingComms import SQLBoilMonitor
    from source.tools.sqlHandler import SqlTableHandler as db

    
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