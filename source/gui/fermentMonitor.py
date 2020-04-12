import sys
import os

import numpy as np
import logging
from datetime import datetime


from PyQt5 import QtCore, QtGui, Qt

from PyQt5.QtGui import QFont

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
from source.gui.guitools import FermentTimeScaleDraw, DateTimeTimeScaleDraw, QHLine, NewGraph


class FermentGraph(QWidget):
    _logname = 'FermentGraphGeneric'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.db = database
        self.updateTimer = QTimer(self)
        self.updateTimer.start(5000)

        self.plot = QwtPlot()
        self.curve = QwtPlotCurve()
        self.curve.attach(self.plot)
        self.plot.resize(1000, 1000)
        self.plot.show()
        self.plot.setAxisScaleDraw(QwtPlot.xBottom, DateTimeTimeScaleDraw())

        axisFont = QFont("Helvetica", 11, QFont.Bold)
        titleFont = QFont("Helvetica", 12, QFont.Bold)

        xTitle = QwtText()
        xTitle.setText("Time")
        xTitle.setFont(axisFont)
        self.plot.setAxisTitle(self.plot.xBottom, xTitle)

        self.yTitle = QwtText()
        self.yTitle.setFont(axisFont)
        self.plot.setAxisTitle(self.plot.yLeft, self.yTitle)

        self.titleText = QwtText()
        self.titleText.setFont(titleFont)
        self.plot.setTitle(self.titleText)

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.plot)
        self.setLayout(mainLayout)

        self.plot.show()
        self.results = []
        self.batchID = None

        
    def updatePlot(self, variable):
        if self.batchID is not None:
            self.db.flushTables()
            sql = f"SELECT TimeStamp, {variable} FROM Ferment WHERE BatchID = '{self.batchID}'"
            
            timestamps = []
            self.results = []
            for data in self.db.custom(sql)[1:]:
                timestamps.append(data[0])
                self.results.append(data[1])

            startTime = timestamps[0]
            for i in range(len(timestamps)):
                timestamps[i] = (timestamps[i]-startTime).seconds

            # self.plot.setAxisScaleDraw(QwtPlot.xBottom, TimeScaleDraw())


            self.curve.setData(timestamps, self.results)
            self.plot.replot()
            self.plot.show()

    def changeTank(self, tankID):
        self.titleText.setText(f"Fermentation Tank: {tankID}")

    
class FermentTempTab(FermentGraph):
    _logname = 'FermentTempTab'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, database, parent=None):
        super().__init__(database=database, parent=parent)
        self.yTitle.setText("Temperature"+DEGREESC)
        self.updateTimer.timeout.connect(lambda : self.updatePlot(variable = 'Temp'))

    def changeBatchID(self,batchID):
        self.batchID = batchID
        self.updatePlot("Temp")


class FermentSgTab(FermentGraph):
    _logname = 'FermentSgTab'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self, database, parent=None):
        super().__init__(database=database, parent=parent)
        self.yTitle.setText("Specific Gravity units")
        self.updateTimer.timeout.connect(lambda : self.updatePlot(variable = 'Sg'))

    def changeBatchID(self,batchID):
        self.batchID = batchID
        self.updatePlot("Sg")


class FermentMonitor(QDialog):
    _logname = 'FermentMonitor'
    _log = logging.getLogger(f'{_logname}')

    closeSignal = pyqtSignal()

    def __init__(self, LOGIN, parent=None):
        self.LOGIN = LOGIN
        self.db = dataBase(self.LOGIN, "Brewing")
        super().__init__(parent)
        self.setWindowTitle('Fermentation tanks')
        self.batchInTank = {}

        self.tabs = QTabWidget()
        self.tabSg = FermentSgTab(database=self.db, parent=parent)
        self.tabTemp = FermentTempTab(database=self.db, parent=parent)
        self.tabs.resize(100,1000)

        self.tabs.addTab(self.tabSg,"Gravity")
        self.tabs.addTab(self.tabTemp,"Temperature")

        self.dropDownBox = QComboBox()
        self.updateTankDropdown()

        self.dropDownBox.currentIndexChanged.connect(self.indexChanged)

        quitButton = QPushButton(self.tr('&Quit'))
        quitButton.clicked.connect(self.closeWindow)
        quitLayout = QHBoxLayout()
        quitLayout.addStretch(10)
        quitLayout.addWidget(quitButton)

        currentValuetimer = QTimer(self)
        currentValuetimer.timeout.connect(self.updateCurrentValues)
        currentValuetimer.start(1000)

        self.recipelayout = QGridLayout()
        
        nameLabel = QLabel("Recipe:")
        self.nameValue = QLabel()

        dateLabel = QLabel("Date:")
        self.dateValue = QLabel()

        brewIDLabel =QLabel("Brew ID:")
        self.brewIDValue =QLabel()

        setTempLabel =QLabel("Set temperature:")
        self.setTempValue = QLabel()

        currentTempLabel =QLabel("Current temperature:")
        self.currentTempValue = QLabel()

        currentSgLabel =QLabel("Current specific gravity:")
        self.currentSgValue = QLabel()

        self.recipelayout.addWidget(nameLabel, 0,0)
        self.recipelayout.addWidget(self.nameValue, 0,1)
        self.recipelayout.addWidget(dateLabel, 1,0)
        self.recipelayout.addWidget(self.dateValue, 1,1)
        self.recipelayout.addWidget(brewIDLabel, 2,0)
        self.recipelayout.addWidget(self.brewIDValue, 2,1)
        self.recipelayout.addWidget(setTempLabel, 3,0)
        self.recipelayout.addWidget(self.setTempValue, 3,1)
        self.recipelayout.addWidget(currentTempLabel, 4,0)
        self.recipelayout.addWidget(self.currentTempValue, 4,1)
        self.recipelayout.addWidget(currentSgLabel, 5,0)
        self.recipelayout.addWidget(self.currentSgValue, 5,1)

        buttonlayout = QVBoxLayout()
        buttonlayout.addWidget(self.dropDownBox)
        buttonlayout.addLayout(self.recipelayout)
        buttonlayout.addStretch(10)

        tablayout = QHBoxLayout()
        tablayout.addLayout(buttonlayout)
        tablayout.addWidget(self.tabs)

        mainlayout = QVBoxLayout()
        mainlayout.addLayout(tablayout)
        mainlayout.addLayout(quitLayout)

        self.setLayout(mainlayout)

        self.recipeUpdate(self.batchInTank["1"])
        self.tabSg.changeTank(1)
        self.tabTemp.changeTank(1)


    def updateTankDropdown(self):
        self.db.flushTables()
        self.numberTotalTanks = self.db.maxValueFromTable("Fermenter","Ferment")
        self.dropDownBox.clear()
        if self.numberTotalTanks is not None:
            tanks = []
            for i in range(self.numberTotalTanks):
                tanks.append(f"Fermentation Tank {i+1}")
                sql = f"SELECT max(BatchID) FROM Ferment WHERE Fermenter = '{i+1}'"
                self.batchInTank[f"{i+1}"] = self.db.custom(sql)[0][0]

            self.dropDownBox.addItems(tanks)



    def recipeUpdate(self, batchID):

        sql = f"SELECT * FROM Brews WHERE id = '{batchID}'"
        query = self.db.custom(sql)

        recipeData = {}
        recipeData['recipeName'] = query[0][1]
        recipeData['recipeDate'] = query[0][2]
        recipeData['fermenttemp']= query[0][15]

        self.nameValue.setText(f"{recipeData['recipeName']}")
        self.dateValue.setText(f"{recipeData['recipeDate']}")
        self.brewIDValue.setText(f"{batchID}")
        self.setTempValue.setText(f"{recipeData['fermenttemp']}")




        self.tabSg.changeBatchID(batchID)
        self.tabTemp.changeBatchID(batchID)


    def updateCurrentValues(self):
        try:
            self.currentSgValue.setText(f"{self.tabSg.results[-1]}")
            self.currentTempValue.setText(f"{self.tabTemp.results[-1]}")
        except IndexError:
            pass


    def indexChanged(self):
        # print(self.batchInTank)
        tankNo = self.dropDownBox.currentIndex()+1

        if self.isVisible():
            self.recipeUpdate(self.batchInTank[f"{tankNo}"])
            self.tabSg.changeTank(tankNo)
            self.tabTemp.changeTank(tankNo)

            # self._log.debug(f"INDEX {self.dropDownBox.currentIndex()}")
            # self.plot.updateData(self.dropDownBox.currentIndex()+1, self.textGraphDrop[f"{self.dropDownGraphBox.currentText()}"])


    def closeWindow(self):
        self.close()
        self.closeSignal.emit()


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
