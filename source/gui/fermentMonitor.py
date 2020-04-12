import sys
import os

import numpy as np
import logging
from datetime import datetime


from PyQt5 import QtCore, QtGui, Qt

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, \
                 QPushButton, QHBoxLayout, QVBoxLayout, QTabWidget, \
                    QLabel, QGridLayout, QComboBox, QDialog

from PyQt5.QtCore import QTimer, QDateTime, QTime, QObject, pyqtSignal, QThread, QRunnable, QCoreApplication

from qwt import QwtPlot, QwtPlotMarker, QwtSymbol, QwtLegend, QwtPlotGrid, \
            QwtPlotCurve, QwtPlotItem, QwtLogScaleEngine, QwtText,  \
            QwtPlotRenderer, QwtScaleDraw, QwtText

# if running from command line, need to append the parent directories to the PATH
# so python knows where to find "source.file"
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
import source.tools.exceptionLogging
from source.tools.constants import *
from source.tools.sqlHandler import SqlTableHandler as dataBase
from source.tools.sqlBrewingComms import SQLFermentMonitor
from source.gui.guitools import FermentTimeScaleDraw, QHLine


class FermentPlot(QWidget):

    _logname = 'FermentPlot'
    _log = logging.getLogger(f'{_logname}')

    textGraphDrop = {
        "Temperature": "Temp",
        "Specific Gravity" : "Sg",
        "Volume" : "Volume"
    }
    
    def __init__(self, LOGIN,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monitor")
        self.LOGIN = LOGIN
        self.db = dataBase(self.LOGIN, "Brewing")

        self.displayDataType = {}


        self.plot = QwtPlot()
        
        self.curve = QwtPlotCurve()
        self.curve.attach(self.plot)
        #self.curve.setData(self.dataX, self.dataY)
        self.plot.resize(1000, 1000)
        self.plot.replot()
        self.plot.show()

        self.labelFerment = QLabel("Set Temp:")
        self.labelFermentTemp = QLabel("Temp")
        self.recipeLabel = QLabel(f"Recipe:")
        self.recipeName = QLabel("Name")
        self.boilStartLabel = QLabel("Boil Start:")
        self.boilStartTime = QLabel("Time")
        self.boilEndLabel = QLabel("Boil End:")
        self.boilEndTime = QLabel("Time")
        

        self.recipeGrid = QGridLayout()
        self.recipeGrid.addWidget(self.recipeLabel,0,0)
        self.recipeGrid.addWidget(self.recipeName,0,1)
        self.recipeGrid.addWidget(QHLine(), 1, 0, 1, 2)
        self.recipeGrid.addWidget(self.labelFerment,2,0)
        self.recipeGrid.addWidget(self.labelFermentTemp,2,1)
        self.recipeGrid.addWidget(self.boilStartLabel,3,0)
        self.recipeGrid.addWidget(self.boilStartTime,3,1)
        self.recipeGrid.addWidget(self.boilEndLabel,4,0)
        self.recipeGrid.addWidget(self.boilEndTime,4,1)

        mainLayout = QHBoxLayout()
        # mainLayout.addLayout(buttonLayout)
        mainLayout.addWidget(self.plot)

        vLayout = QVBoxLayout(self)
        vLayout.addLayout(mainLayout)


    def updateData(self, tankID, displayDataType):
        self.displayDataType = displayDataType
        self.tankID = tankID
        self.db.flushTables()

        sql = f"SELECT max(BatchID) FROM Ferment WHERE Fermenter = '{tankID}'"
        query = self.db.custom(sql)
        # self._log.debug(f"Query: {query}")
        self.batchID = query[-1][0]
        self._log.debug(f"BatchID: {self.batchID}, DataType: {self.displayDataType}")

        
        sql = f"SELECT * FROM Brews WHERE id = '{self.batchID}'"
        query = self.db.custom(sql)

        self.recipeData = {}
        self.recipeData['recipeName'] = query[0][1]
        self.recipeData['recipeDate'] = query[0][2]
        self.recipeData['mashTemp']   = query[0][3]
        self.recipeData['mashTime']   = query[0][4]
        self.recipeData['boilTemp']   = query[0][5]
        self.recipeData['boilTime']   = query[0][6]
        self.recipeData['hop1']       = (query[0][7],query[0][8])
        self.recipeData['hop2']       = (query[0][9],query[0][10])
        self.recipeData['hop3']       = (query[0][11],query[0][12])
        self.recipeData['hop4']       = (query[0][13],query[0][14])
        self.recipeData['fermenttemp']= query[0][15]

        # self.tempData = self.getData("Temp","BatchID","Ferment")
        # self.sGData = self.getData("Sg","BatchID","Ferment")
        # self.volumeData = self.getData("Volume","BatchID","Ferment")
        # self.tankNumber = self.getData("Fermenter","BatchID","Ferment")
        sql = (f"SELECT TimeStamp FROM Ferment "
              f"WHERE BatchID = '{self.batchID}' "
              f"AND Fermenter = '{tankID}'")
        data = self.db.custom(sql)
        self.timeStamp = data
        self._log.debug(self.timeStamp[0][0])
       

        self.displayData = self.getData(f"{self.displayDataType}","BatchID","Ferment")


        self.updatePlot()
        self.updateLabels()

    def updatePlot(self):
        self.plot.setTitle(f"{self.recipeData['recipeName']}: {self.recipeData['recipeDate']}")
        self.updatePlotData()

    def updatePlotData(self):
        sql = (f"SELECT TimeStamp FROM Ferment "
            f"WHERE BatchID = '{self.batchID}' "
            f"AND Fermenter = '{self.tankID}'")
        self.db.flushTables()
        data = self.db.custom(sql)
        self.timeStamp = data
        self.displayData = self.getData(f"{self.displayDataType}","BatchID","Ferment")
        self.dataY = self.displayData
        self.dataX = np.linspace(0,len(self.dataY),len(self.dataY))
        self.curve.setData(self.dataX, self.dataY)
        self.plot.setAxisScaleDraw(QwtPlot.xBottom, FermentTimeScaleDraw(self.timeStamp))
        # self.curve.setData(self.dataY)
        self.plot.replot()

    def updateLabels(self):
        # if self.isVisible():
        self.labelFermentTemp.setText(f"{self.recipeData['fermenttemp']}{DEGREESC}")
        self.recipeName.setText(f"{self.recipeData['recipeName']}")

        # db = dataBase(self.LOGIN, "Brewing")
        sql = (f"SELECT BoilStart, BoilFinish FROM Boil "
            f"WHERE BatchID = '{self.batchID}' ")
        data = self.db.custom(sql)
        self.boilStartTime.setText(data[-1][0].strftime('%H:%M:%S'))
        self.boilEndTime.setText(data[-1][1].strftime('%H:%M:%S'))


        # self.label1.setText(self.displayDataType)


    def getData(self,dataType, id,table):
        # db = dataBase(self.LOGIN, "Brewing")
        self.db.flushTables()
        sql = f"SELECT {dataType} FROM {table} WHERE {id} = '{self.batchID}'"
        data = self.db.custom(sql)
        # data = [i[0] for i in data]
        data = np.asarray(data, dtype=float)
        #self._log.debug(f"batchID: {self.batchID}, sql return: {data}")
        
        return np.fromiter(data, dtype=float)
        # return np.asarray(data, dtype=float)
        # except:
        #     return data




class FermentMonitor(QDialog):

    _logname = 'FermentMonitor'
    _log = logging.getLogger(f'{_logname}')

    textGraphDrop = {
        "Temperature": "Temp",
        "Specific Gravity" : "Sg",
        "Volume" : "Volume"
    }
    fermentClose = pyqtSignal()
    

    def __init__(self, LOGIN, parent=None):
        self.LOGIN = LOGIN
        super().__init__(parent)
        # super().__init__()
        # self.app = QCoreApplication.instance()
        # self.restart()

        self.numberTotalTanks = dataBase(self.LOGIN, "Brewing").maxValueFromTable("Fermenter","Ferment")
        # super().__init__(parent)
        self.setWindowTitle('Fermentation Monitor')
        
        self.dropDownBox = QComboBox()
        self.dropDownGraphBox = QComboBox()
        self.dropDownGraphBox.addItem("Specific Gravity")
        self.dropDownGraphBox.addItem("Temperature")
        self.dropDownGraphBox.addItem("Volume")

        # if self.numberTotalTanks == None:
        #    raise Exception("No fermentations active")
        # #    pass

        # for i in range(self.numberTotalTanks):
        #     self.dropDownBox.addItem(f"Fermentation tank {i+1}")
        self.restartTankDropdown()


        self.plot = FermentPlot(self.LOGIN)
        # self.plot.updateData(1, "Sg")
        self.dropDownBox.currentIndexChanged.connect(self.indexChanged)
        self.dropDownGraphBox.currentIndexChanged.connect(self.indexChanged)

        self.plotLayout = QHBoxLayout()
        self.plotLayout.addWidget(self.plot)

        self.dropDownBoxLayout = QVBoxLayout()
        self.dropDownBoxLayout.addStretch(10)
        self.dropDownBoxLayout.addWidget(self.dropDownBox)
        self.dropDownBoxLayout.addWidget(self.dropDownGraphBox)
        self.dropDownBoxLayout.addStretch(10)
        self.dropDownBoxLayout.addLayout(self.plot.recipeGrid)
        self.dropDownBoxLayout.addStretch(100)

        self.gridLayout = QGridLayout()
        self.gridLayout.addLayout(self.dropDownBoxLayout,0,0)
        self.gridLayout.addLayout(self.plotLayout,0,1)

        self.quitButton = QPushButton(self.tr('&Quit'))
        self.quitButton.clicked.connect(self.closeWindow)
        quitLayout = QHBoxLayout()
        quitLayout.addStretch(100)
        quitLayout.addWidget(self.quitButton)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addLayout(self.gridLayout)
        self.mainLayout.addLayout(quitLayout)

        self.updateTimer = QTimer(self)
        self.updateTimer.timeout.connect(self.indexChanged)
        # self.updateTimer.start(1000)

        # if __name__ == "__main__":
        self.fakeFermentCount = 0
        self.fakeFermenter = SQLFermentMonitor(self.LOGIN,1,1)
        # self.fakeFermenter2 = SQLFermentMonitor(self.LOGIN,5,4)
        self.updateDataTimer = QTimer(self)
        # self.updateDataTimer.timeout.connect(self.fakeFermentData)
        # self.updateDataTimer.start(1000)
        self.startTimers()

    def restartTankDropdown(self):
        self.numberTotalTanks = dataBase(self.LOGIN, "Brewing").maxValueFromTable("Fermenter","Ferment")
        self.dropDownBox.clear()
        if self.numberTotalTanks == None:
        #    raise Exception("No fermentations active")
           pass
        else:
            tanks = []
            for i in range(self.numberTotalTanks):
                tanks.append(f"Fermentation tank {i+1}")

            self.dropDownBox.addItems(tanks)

    def startMonitor(self):
        pass

    def indexChanged(self):
        if self.isVisible():
            self._log.debug(f"INDEX {self.dropDownBox.currentIndex()}")
            self.plot.updateData(self.dropDownBox.currentIndex()+1, self.textGraphDrop[f"{self.dropDownGraphBox.currentText()}"])

    def fakeFermentData(self):
        self.fakeFermenter = SQLFermentMonitor(self.LOGIN,
                                                batchID=self.plot.batchID,
                                                fermenterID=self.dropDownBox.currentIndex()+1)
        x = self.fakeFermentCount
        temp = np.divide(10*np.power(x,3)+2*np.square(x)-x, 2*np.power(x,3)+10*np.square(x)+1)
        self.fakeFermenter.record(float(temp),float(temp*2*x),float(temp*4))
        # self.fakeFermenter2.record(float(temp),float(temp*2),float(temp*4))
        self.fakeFermentCount +=1

    def startTimers(self):
        self.updateDataTimer.start(5000)
        self.updateTimer.start(10000)

    def stopTimers(self):
        self.updateTimer.stop()
        self.updateDataTimer.stop()

    def closeWindow(self):
        self.stopTimers()
        self.close()


if __name__ == "__main__":
    import logging
    from getpass import getpass
    _logname = 'FermentMonitorMain'
    _log = logging.getLogger(f'{_logname}')
    
    HOST = "localhost"
    USER = "Test"
    PASSWORD = "BirraMosfeti"

    HOST = "192.168.0.17"
    USER = "jamie"
    PASSWORD = "beer"

    HOST = input("Host ID: ")
    USER = input("User: ")
    PASSWORD = getpass()
    if HOST == "Pi":
        HOST = "192.168.0.17"

    LOGIN = [HOST,USER,PASSWORD]



    app = QApplication(sys.argv)
    #window = MonitorWindow(mashtime=mashtime, boiltime=boiltime,hop1=hop1,hop2=hop2,hop3=hop3,hop4=hop4)
    window = FermentMonitor(LOGIN)
    window.startTimers()
    window.show()
    sys.exit(app.exec_())
