import numpy as np
import logging
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")
import sys
import os

from QLed import QLed
from PyQt5 import QtCore, QtGui, Qt

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, \
                 QPushButton, QHBoxLayout, QVBoxLayout, QTabWidget, \
                    QLabel, QGridLayout, QFrame, QMessageBox, QDialog

from PyQt5.QtGui import QFont

from PyQt5.QtCore import QTimer, QDateTime, QTime, pyqtSignal

from qwt import QwtPlot, QwtPlotMarker, QwtSymbol, QwtLegend, QwtPlotGrid, \
            QwtPlotCurve, QwtPlotItem, QwtLogScaleEngine, QwtText,  \
            QwtPlotRenderer, QwtScaleDraw, QwtText


# if running from command line, need to append the parent directories to the PATH
# so python knows where to find "source.file"
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
import source.tools.exceptionLogging
from source.tools.sqlHandler import SqlTableHandler as dataBase
from source.tools.sqlBrewingComms import SQLBoil, SQLBoilMonitor, SQLFermentMonitor
from source.tools.constants import *
from source.gui.guitools import BoilMashTimeScaleDraw, QHLine, QVLine, BoilFinishedPopup, QBoxColour, TimeScaleDraw
from source.gui.irCameraWidget import IrCameraWidget

 
##Parent class to hold graph instance
#
#Subclassed by TabBoil and TabMash
#@sa TabBoil and TabMash
class TabGraph(QWidget):
    
    _logname = 'TabGraph'
    _log = logging.getLogger(f'{_logname}')


    ##TabGraph constructor
    #
    #Create the graph and accompanying buttons
    def __init__(self, db, parent=None):
        super().__init__(parent)
        # self.LOGIN = LOGIN
        # self.db = dataBase(self.LOGIN, "Brewing")
        self.db=db
        self.dataY = np.zeros(0)
        self.dataX = np.linspace(0,len(self.dataY),len(self.dataY))

        self.count = 0
        self.timeLabel = QLabel("Timer:")
        self.timeLabel.setAlignment(QtCore.Qt.AlignRight)

        self.tempLabel = QLabel("Temp:")
        self.tempLabel.setAlignment(QtCore.Qt.AlignRight)

        self.targetTemp=QLabel("Set temp:")
        self.targetTime=QLabel(f"Set temp:")

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

        axisFont = QFont("Helvetica", 11, QFont.Bold)
        titleFont = QFont("Helvetica", 12, QFont.Bold)

        xTitle = QwtText()
        xTitle.setText("Time")
        xTitle.setFont(axisFont)
        self.plot.setAxisTitle(self.plot.xBottom, xTitle)
        yTitle = QwtText()
        yTitle.setText(f"Temperature {DEGREESC}")
        yTitle.setFont(axisFont)
        self.plot.setAxisTitle(self.plot.yLeft, yTitle)


        self.tempStatusLED = QLed(self, onColour=QLed.Green, offColour=QLed.Red, shape=QLed.Circle)
        self.tempStatusLED.value=False
        self.tempStatusLED.setMaximumSize(25,25)

        self.timeStatusLED = QLed(self, onColour=QLed.Green, offColour=QLed.Red, shape=QLed.Circle)
        self.timeStatusLED.value=False
        self.timeStatusLED.setMaximumSize(25,25)


        self.recipeGrid = QGridLayout()
        self.recipeGrid.addWidget(QLabel(f"Recipe:"),0,0)
        self.recipeGrid.addWidget(QLabel(f"{self.recipedata['recipeName']}"),0,1)
        self.recipeGrid.addWidget(QHLine(), 1, 0, 1, 2)
        self.recipeGrid.addWidget(self.targetTemp)
        self.recipeGrid.addWidget(self.targetTempLabel)
        self.recipeGrid.addWidget(self.targetTime)
        self.recipeGrid.addWidget(self.targetTimeLabel)
        self.recipeGrid.addWidget(QHLine(), 4, 0, 1, 2)


        self.tempLayout = QHBoxLayout()
        # self.tempLayout.addWidget(self.targetTempLabel)
        # self.tempLayout.addStretch(10)
        self.tempLayout.addWidget(self.tempLabel)
        # self.tempLayout.addStretch(10)
        self.tempLayout.addWidget(self.tempStatusLED)
        self.tempLayout.addStretch(10)

        self.timeLayout = QHBoxLayout()
        # self.timeLayout.addWidget(self.targetTimeLabel)
        # self.timeLayout.addStretch(10)
        self.timeLayout.addWidget(self.timeLabel)
        # self.timeLayout.addStretch(10)
        self.timeLayout.addWidget(self.timeStatusLED)
        self.timeLayout.addStretch(10)

        self.plotLayout = QVBoxLayout()
        self.plotLayout.addLayout(self.timeLayout)
        # self.plotLayout.addStretch(10)
        self.plotLayout.addLayout(self.tempLayout)
        # self.plotLayout.addStretch(10)
        self.plotLayout.addWidget(self.plot)
    
        self.buttonLayout = QVBoxLayout()
        self.buttonLayout.addWidget(self.startButton)
        self.buttonLayout.addWidget(self.stopButton)
        self.buttonLayout.addLayout(self.recipeGrid)
        self.buttonLayout.addStretch(100)

        mainLayout = QHBoxLayout()
        mainLayout.addLayout(self.buttonLayout)
        mainLayout.addLayout(self.plotLayout)

        vLayout = QVBoxLayout(self)
        vLayout.addLayout(mainLayout)

        self.minuteTimer = QTimer(self)
        self.minuteTimer.timeout.connect(lambda:self.addTimer(60))
        
    ##Keep track of the timer
    def addTimer(self, seconds):
        self.count += seconds

    ##convery the time from seconds to hours/minutes
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

    
##Tab specific to mashing
class TabMash(TabGraph):
    _logname = 'TabMash'
    _log = logging.getLogger(f'{_logname}')

    ##Create tab layout and setup plot for camera
    def __init__(self, db, LOGIN, batchID, recipedata:dict, parent=None, radio = None):
        self.recipedata = recipedata
        self.batchID = batchID
        self.radio = radio
        super().__init__(db, parent)
        
        self.startButton.setText(self.tr('Start Mash'))
        self.stopButton.setText(self.tr('&Stop Mash'))
        self.plot.setTitle("Mash")
        self.curve.setTitle("Temprature")

        self.targetTimeLabel.setText(f"{self.recipedata['mashTime']} mins")
        self.targetTempLabel.setText(f"{self.recipedata['mashTemp']}{DEGREESC}")


        # if self.radio is not None:
        #     irCamera = IrCameraWidget(radio=self.radio, parent=parent)
        #     self.buttonLayout.addWidget(irCamera)

        # if self.radio is not None:
        #     self.slider = QSlider(QtCore.Qt.Vertical)
        #     self.slider.setMinimum(0)
        #     self.slider.setMaximum(50)
        #     self.slider.setValue(10)
        #     self.irCameraPlot = PlotCanvas(self, width=4, height=4)
        #     self.slider.valueChanged.connect(lambda: self.sliderchanged())
        #     ircameralayout = QHBoxLayout()
        #     ircameralayout.addWidget(self.irCameraPlot)
        #     ircameralayout.addWidget(self.slider)
        #     self.buttonLayout.addLayout(ircameralayout)

        #     self.irCameraTimer = QTimer(self)
        #     self.irCameraTimer.timeout.connect(lambda: self.updateIr())
        #     self.irCameraTimer.start(5000)

    # def sliderchanged(self):
    #     self.irCameraPlot.scale = self.slider.value()

    # ##Update the IR camera plot every 5 seconds
    # def updateIr(self):
    #     if self.minuteTimer.isActive():
    #         self.irCameraPlot.plot(self.radio.irTemp)
        
    ##Update the mash plot with new data from the database
    def updatePlot(self):
        self.db.flushTables()
        # db = dataBase(self.LOGIN, "Brewing")
        sql = f"SELECT TimeStamp, Temp FROM Mash WHERE BatchID = '{self.batchID}'"
        # query = self.db.custom(sql)

        # results = [i[0] for i in query]
        # self.dataY = np.fromiter(results, dtype=float)

        # sql = f"SELECT TimeStamp FROM Mash WHERE BatchID = '{self.batchID}'"
        # query = self.db.custom(sql)

        timestamps = []
        results = []
        for data in self.db.custom(sql):
            timestamps.append(data[0])
            results.append(data[1])

        startTime = timestamps[0]
        for i in range(len(timestamps)):
            timestamps[i] = (timestamps[i]-startTime).seconds
            # timestamps[i] = timestamps[i].seconds

        self.plot.setAxisScaleDraw(QwtPlot.xBottom, TimeScaleDraw())

        # self.timeStamps = [i[0] for i in query]
        
        # self.dataX = np.linspace(0, len(self.dataY), len(self.dataY))
        self.curve.setData(timestamps, results)
        # self.plot.setAxisScaleDraw(QwtPlot.xBottom, BoilMashTimeScaleDraw(self.timeStamps))
        self.plot.replot()
        self.plot.show()

        if len(timestamps) == 0:
            self.timeLabel.setText("Timer:")
            self.tempLabel.setText("Temp:")
        else:
            self.timeLabel.setText("Timer: {}".format(self.display_time(timestamps[-1])))
            self.tempLabel.setText("Temp: {}{}".format(results[-1],DEGREESC))     

            if (results[-1] < (self.recipedata['mashTemp']-0.5)) or (results[-1] > (self.recipedata['mashTemp']+0.5)):
                self.tempStatusLED.value=False
            else:
                self.tempStatusLED.value=True
        if len(timestamps) == 0:
            self.timeLabel.setText("Timer:")
            self.tempLabel.setText("Temp:")
        else:
            self.timeLabel.setText("Timer: {}".format(self.display_time(timestamps[-1])))
            self.tempLabel.setText("Temp: {}{}".format(results[-1],DEGREESC))

##Tab specific to Boiling
class TabBoil(TabGraph):
    _logname = 'TablesTabBoil'
    _log = logging.getLogger(f'{_logname}')

    ##Create tab layout and setup plot and recipe data timings
    def __init__(self, db, LOGIN, batchID, recipedata:dict, parent=None, radio = None):
        self.recipedata = recipedata
        self.batchID = batchID
        self.radio = radio
        super().__init__(db, parent)
        self.sqlBoilComms = SQLBoil(LOGIN)
        self.plot.setTitle("Boil")
        self.curve.setTitle("Temprature")

        self.startButton.setText(self.tr('Start Boil'))
        self.stopButton.setText(self.tr('&Stop Boil'))

        # self.targetTimeLabel.setText(f"Set boil time: {self.recipedata['boilTime']} mins")
        # self.targetTempLabel.setText(f"Set boil temp: {self.recipedata['boilTemp']}{DEGREESC}")

        self.targetTimeLabel.setText(f"{self.recipedata['boilTime']} mins")
        self.targetTempLabel.setText(f"{self.recipedata['boilTemp']}{DEGREESC}")


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



        self.hopTimeLabels = [QLabel("") for _ in range(4)]

        self.recipeGrid.addWidget(QLabel(f"Hop"),5,0)
        self.recipeGrid.addWidget(QLabel(f"Time"),5,1)
        self.recipeGrid.addWidget(QLabel(f"Hop\nStatus"),5,2)
        self.recipeGrid.addWidget(QLabel(f"Time\nadded"),5,3)
        for i in range(4):
            if self.recipedata[f'hop{i+1}'][0] is None:
                self.recipeGrid.addWidget(QLabel(""),6+i,0)
                self.recipeGrid.addWidget(QLabel(""),6+i,1)

            else:
                self.recipeGrid.addWidget(QLabel("{}".format(self.recipedata[f'hop{i+1}'][0])),6+i,0)
                self.recipeGrid.addWidget(QLabel("{}".format(self.recipedata[f'hop{i+1}'][1])),6+i,1)
                self.recipeGrid.addWidget(self.recipeLED[i],6+i,2)
            self.recipeLED[i].setMaximumSize(25,25)
            self.recipeGrid.addWidget(self.hopTimeLabels[i],6+i,3)


        #Doesn't work in for loop for some reason
        self.recipeLED[0].clicked.connect(lambda: self.ledClicked(self.recipeLED[0],1))
        self.recipeLED[1].clicked.connect(lambda: self.ledClicked(self.recipeLED[1],2))
        self.recipeLED[2].clicked.connect(lambda: self.ledClicked(self.recipeLED[2],3))
        self.recipeLED[3].clicked.connect(lambda: self.ledClicked(self.recipeLED[3],4))

        for i in range(4):
            if self.recipedata[f'hop{i+1}'][0] is None:
                self.recipeLED[i].deleteLater()
                
    ##When LED is clicked, set timer in Database
    def ledClicked(self,led,hopNo):
        if self.minuteTimer.isActive():
            if led.offColour == QLed.Yellow and led.value==False:
                self.hoptimes[f'{hopNo}']()
                self._log.info("Hop added")

            elif led.offColour == QLed.Red and led.value==False:            
                self.hoptimes[f'{hopNo}']()
                self._log.info(f"Hop added early")

            elif led.value == True:
                self._log.info(f"Hop {hopNo} already added")
                return
            else:
                raise Exception("Somethings gone terribly wrong")

            led.value=True
            time = (self.recipedata['boilTime']*60)-self.count
            self.hopTimeLabels[hopNo-1].setText("{}".format(self.display_time(time)))

    ##Update the plot with new data from the database
    def updatePlot(self):
        self.db.flushTables()
        # db = dataBase(self.LOGIN, "Brewing")
        sql = f"SELECT TimeStamp, Temp FROM BoilMonitor WHERE BatchID = '{self.batchID}'"
        query = self.db.custom(sql)

        # results = [i[0] for i in query]
        # results = np.asarray(query)
        # self.dataY = np.fromiter(results, dtype=float)

        # sql = f"SELECT TimeStamp FROM BoilMonitor WHERE BatchID = '{self.batchID}'"
        # query = self.db.custom(sql)

        timestamps = []
        results = []
        for data in self.db.custom(sql):
            timestamps.append(data[0])
            results.append(data[1])

        
        if len(timestamps) == 0:
            return

        startTime = timestamps[0]
        for i in range(len(timestamps)):
            timestamps[i] = (timestamps[i]-startTime).seconds
            # timestamps[i] = timestamps[i].seconds

        self.plot.setAxisScaleDraw(QwtPlot.xBottom, TimeScaleDraw())

        # self.timeStamps = [i[0] for i in query]
        # self.dataY = np.fromiter(results, dtype=float)
        
        # self.dataX = np.linspace(0, len(self.dataY), len(self.dataY))
        self.curve.setData(timestamps, results)
        # self.plot.setAxisScaleDraw(QwtPlot.xBottom, BoilMashTimeScaleDraw(self.timeStamps))
        self.plot.replot()
        self.plot.show()

        if len(timestamps) == 0:
            self.timeLabel.setText("Timer:")
            self.tempLabel.setText("Temp:")
        else:

            self.timeLabel.setText("Timer: {}".format(self.display_time(timestamps[-1])))
            self.tempLabel.setText("Temp: {}{}".format(results[-1],DEGREESC))     

            if (results[-1] < (self.recipedata['boilTemp']-0.5)) or (results[-1] > (self.recipedata['boilTemp']+0.5)):
                self.tempStatusLED.value=False
            else:
                self.tempStatusLED.value=True

        for i in range(4):
            if self.recipedata[f'hop{i+1}'][1] is not None:
                if timestamps[-1]/60 >= self.recipedata['boilTime']-self.recipedata[f'hop{i+1}'][1]:
                    self.recipeLED[i].setOffColour(QLed.Yellow)

##Monitoring window for boiling and mashing processes
class MonitorWindow(QDialog):

    _logname = 'MonitorWindow'
    _log = logging.getLogger(f'{_logname}')

    closeSignal= pyqtSignal()
    finishedSignal = pyqtSignal()
    ##Setup to window 
    def __init__(self, LOGIN, batchID, radio=None ,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monitor")
        self.LOGIN = LOGIN
        self.db = dataBase(self.LOGIN, "Brewing")
        self.batchID = batchID
        
        self.radio = radio

        sql = f"SELECT * FROM Brews WHERE id = '{self.batchID}'"
        query = self.db.custom(sql)

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
        self.tabMash = TabMash(self.db, LOGIN, self.batchID, self.recipedata, parent=self, radio=radio)
        self.tabBoil = TabBoil(self.db, LOGIN, self.batchID, self.recipedata, parent=self, radio=radio)
        self.tabs.resize(100,1000)

        self.tabs.addTab(self.tabMash,"Mash")
        self.tabs.addTab(self.tabBoil,"Boil")

        self.quitButton = QPushButton(self.tr('&Quit'))
        self.quitButton.clicked.connect(self.closeWindow)
        
        self.tabBoil.startButton.clicked.connect(self.boilStartClicked)
        self.tabBoil.stopButton.clicked.connect(self.boilStopClicked)

        self.tabMash.startButton.clicked.connect(self.mashStartClicked)
        self.tabMash.stopButton.clicked.connect(self.mashStopClicked)

        if radio is None:
            self.tabBoil.startButton.setEnabled(False)
            self.tabBoil.stopButton.setEnabled(False)
            self.tabMash.startButton.setEnabled(False)
            self.tabMash.stopButton.setEnabled(False)
        

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


    ##Start the boil when the button is clicked
    def boilStartClicked(self):
        if not self.tabBoil.minuteTimer.isActive():
            msg = 'Start boiling? \n set {}{} for {} minutes'.format(self.recipedata['boilTemp'],DEGREESC,self.recipedata['boilTime'])
            reply = QMessageBox.question(self, 'Continue?', 
                    msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                '''
                TODO: Set Boil Uc
                '''
                self.radio.startBoil(self.recipedata['boilTemp'])

                self.tabBoil.minuteTimer.start(60000)
                self.tabBoil.sqlBoilComms.startTimer()
                self.tabBoil.timeStatusLED.value=True
        elif self.tabBoil.minuteTimer.isActive():
            x = divmod(self.tabBoil.count,60)
            msg = 'Boil already running: {} mins.'.format(x[0])
            reply = QMessageBox.question(self, 'oops', 
                    msg, QMessageBox.Ok)
        else:
            raise Exception("Boiling Error")

    ##Stop the boil when clicked
    def boilStopClicked(self):
        if self.tabBoil.minuteTimer.isActive():
            x = divmod(self.tabBoil.count,60)
            msg = 'Stop boiling?\nCurrent time: {} mins\nRecipe time: {} mins.'.format(x[0], self.recipedata['boilTime'] )
            reply = QMessageBox.question(self, 'Continue?', 
                    msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                '''
                TODO: TURN OFF BOIL uC 
                '''
                self.radio.stopBoil()
                self.tabBoil.minuteTimer.stop()

                self.tabBoil.sqlBoilComms.endTimer()
                self.tabBoil.timeStatusLED.value=False

                boilPopup = BoilFinishedPopup(LOGIN=self.LOGIN, recipeData=self.recipedata, parent=self)

                if boilPopup.exec_():
                    tankNumber = boilPopup.selectedTank
                    self._log.debug('Batch {} being sent to tank {}'.format(self.recipedata['batchID'],tankNumber))
                    '''EMIT SIGNAL with fermentation tank number'''
                    fermtank = SQLFermentMonitor(self.LOGIN, self.recipedata['batchID'], tankNumber)
                    fermtank.record(None,None,None) #enter null into database to attach tank to batch id
                    self.finishedSignal.emit()
                    self.close()

        elif not self.tabBoil.minuteTimer.isActive():
            msg = 'No Boil currently running'
            reply = QMessageBox.question(self, 'oops', 
                    msg, QMessageBox.Ok)

    ##Start the mash when button is clicked
    def mashStartClicked(self):
        if not self.tabMash.minuteTimer.isActive():
            msg = 'Start mashing? \n set {}{} for {} minutes'.format(self.recipedata['mashTemp'],DEGREESC,self.recipedata['mashTime'])
            reply = QMessageBox.question(self, 'Continue?', 
                    msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:
                '''
                TODO: Set mash Uc
                '''
                self.radio.startMash(self.recipedata['mashTemp'])

                self.tabMash.minuteTimer.start(60000)
                self.tabMash.timeStatusLED.value=True
        elif self.tabMash.minuteTimer.isActive():
            x = divmod(self.tabMash.count,60)
            msg = 'Mash already running: {} mins.'.format(x[0])
            reply = QMessageBox.question(self, 'oops', 
                    msg, QMessageBox.Ok)
        else:
            raise Exception("Mashing Error")
        # self.tabMash.minuteTimer.start(60000)

    ##Stop the mash when the button is clicked
    def mashStopClicked(self):
        if self.tabMash.minuteTimer.isActive():
            x = divmod(self.tabMash.count,60)
            msg = 'Stop mashing?\nCurrent time: {} mins\nRecipe time: {} mins.'.format(x[0], self.recipedata['mashTime'] )
            reply = QMessageBox.question(self, 'Continue?', 
                    msg, QMessageBox.Yes, QMessageBox.No)
            if reply == QMessageBox.Yes:

                self.radio.stopMash()

                self.tabMash.minuteTimer.stop() 
                self.tabMash.timeStatusLED.value=False

        elif not self.tabMash.minuteTimer.isActive():
            msg = 'No mash currently running'
            reply = QMessageBox.question(self, 'oops', 
                    msg, QMessageBox.Ok)

    ##call the plot to be updated when the timer runs out
    def updateMashPlot(self):
        self.tabMash.updatePlot()

    ##call the plot to be updated when the timer runs out  
    def updateBoilPlot(self):
        self.tabBoil.updatePlot()

    ##close the window safely, stop all the timers  
    def closeWindow(self):
        if self.radio is not None:
            self.radio.stopMash()
            self.radio.stopBoil()

        self.boilPlotUpdateTimer.stop()
        self.tabBoil.minuteTimer.stop()
        self.mashPlotUpdateTimer.stop()
        self.tabMash.minuteTimer.stop()
        self.close()
        self.closeSignal.emit()
        




if __name__ == "__main__":
    import logging
    _logname = 'BoilMashMonitorMain'
    _log = logging.getLogger(f'{_logname}')
    

    from source.tools.sqlHandler import SqlTableHandler as db

    
    HOST = "localhost"
    USER = "Test"
    PASSWORD = "BirraMosfeti"

    HOST = "192.168.0.17"
    USER = "jamie"
    PASSWORD = "beer"

    LOGIN = [HOST,USER,PASSWORD]
    database = db(LOGIN,"Brewing")
    batchID = database.maxIdFromTable("Brews")

    # boilMonitor = SQLBoilMonitor(LOGIN)

    app = QApplication(sys.argv)
    #window = MonitorWindow(mashtime=mashtime, boiltime=boiltime,hop1=hop1,hop2=hop2,hop3=hop3,hop4=hop4)
    window = MonitorWindow(LOGIN, batchID)
    window.show()
    sys.exit(app.exec_())
