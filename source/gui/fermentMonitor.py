import sys
import os

import numpy as np
import logging
from datetime import datetime


from PyQt5 import QtCore, QtGui, Qt

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, \
                 QPushButton, QHBoxLayout, QVBoxLayout, QTabWidget, \
                    QLabel, QGridLayout, QComboBox

from PyQt5.QtCore import QTimer, QDateTime, QTime

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


# class TimeScaleDraw(QwtScaleDraw):

#     _logname = 'TimeScaleDraw'
#     _log = logging.getLogger(f'{_logname}')

#     def __init__(self, timeStamps, *args):
#         QwtScaleDraw.__init__(self, *args)
#         self.timeStamps = timeStamps
#         #self.baseTime = datetime
#         self.fmt='%H:%M:%S\n%Y-%m-%d'
#         #tdelta = datetime.strptime(s2, FMT) - datetime.strptime(s1, FMT)

#     def label(self, value):
#         self._log.debug(f"VALUE: {value}")
#         self._log.debug(f"timestamp length: {len(self.timeStamps)}")
        
#         try:
#             dt = self.timeStamps[int(value)][0]
#             return QwtText(dt.strftime(self.fmt))
#         except IndexError:
#             return QwtText(self.timeStamps[-1][0].strftime(self.fmt))


class FermentPlot(QWidget):

    _logname = 'FermentPlot'
    _log = logging.getLogger(f'{_logname}')
    
    def __init__(self, LOGIN):
        super().__init__()
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

        sql = f"SELECT BatchID FROM Ferment WHERE Fermenter = '{tankID}'"
        query = self.db.custom(sql)
        # self._log.debug(f"Query: {query}")
        self.batchID = query[-1][0]
        self._log.debug(f"BatchID: {self.batchID}, DataType: {displayDataType}")

        
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
       

        self.displayData = self.getData(f"{displayDataType}","BatchID","Ferment")

        # for i in range(len(self.displayData)):
        #     self.displayData[i] = [self.timeStamp[i], self.displayData[i]] 


        self.updatePlot()
        self.updateLabels()

    def updatePlot(self):
        # # self.dataY = self.sGData
        # self.displayData = self.getData(f"{self.displayDataType}","BatchID","Ferment")
        # self.dataY = self.displayData
        # # self.dataX = np.zeros(len(self.dataY))
        # # self._log.debug(f"timestamp type: {type(self.timeStamp[0][0])}")
        # # for i in range(len(self.dataX)):
        # #     self.dataX = self.timeStamp[i][0]

        # self.dataX = np.linspace(0,len(self.dataY),len(self.dataY))

        self.plot.setTitle(f"{self.recipeData['recipeName']}: {self.recipeData['recipeDate']}")

        # self.curve.setData(self.dataX, self.dataY)
        # self.plot.setAxisScaleDraw(QwtPlot.xBottom, TimeScaleDraw(self.timeStamp))
        # # self.curve.setData(self.dataY)
        # self.plot.replot()
        self.updatePlotData()

    def updatePlotData(self):
        db = dataBase(self.LOGIN, "Brewing")
        sql = (f"SELECT TimeStamp FROM Ferment "
              f"WHERE BatchID = '{self.batchID}' "
              f"AND Fermenter = '{self.tankID}'")
        data = db.custom(sql)
        self.timeStamp = data
        self.displayData = self.getData(f"{self.displayDataType}","BatchID","Ferment")
        self.dataY = self.displayData
        self.dataX = np.linspace(0,len(self.dataY),len(self.dataY))
        self.curve.setData(self.dataX, self.dataY)
        self.plot.setAxisScaleDraw(QwtPlot.xBottom, FermentTimeScaleDraw(self.timeStamp))
        # self.curve.setData(self.dataY)
        self.plot.replot()

    def updateLabels(self):
        self.labelFermentTemp.setText(f"{self.recipeData['fermenttemp']}{DEGREESC}")
        self.recipeName.setText(f"{self.recipeData['recipeName']}")

        db = dataBase(self.LOGIN, "Brewing")
        sql = (f"SELECT BoilStart, BoilFinish FROM Boil "
              f"WHERE BatchID = '{self.batchID}' ")
        data = db.custom(sql)
        self.boilStartTime.setText(data[-1][0].strftime('%H:%M:%S'))
        self.boilEndTime.setText(data[-1][1].strftime('%H:%M:%S'))


    def getData(self,dataType, id,table):
        db = dataBase(self.LOGIN, "Brewing")
        sql = f"SELECT {dataType} FROM {table} WHERE {id} = '{self.batchID}'"
        data = db.custom(sql)
        data = [i[0] for i in data]
        #self._log.debug(f"batchID: {self.batchID}, sql return: {data}")
        
        return np.fromiter(data, dtype=float)
        # except:
        #     return data




class FermentMonitor(QWidget):

    _logname = 'FermentMonitor'
    _log = logging.getLogger(f'{_logname}')

    textGraphDrop = {
        "Temperature": "Temp",
        "Specific Gravity" : "Sg",
        "Volume" : "Volume"
    }

    def __init__(self, LOGIN):
        self.LOGIN = LOGIN

        self.numberTotalTanks = dataBase(self.LOGIN, "Brewing").maxValueFromTable("Fermenter","Ferment")
        super().__init__()
        self.setWindowTitle('Fermentation monitor')
        
        self.dropDownBox = QComboBox()
        self.dropDownGraphBox = QComboBox()
        self.dropDownGraphBox.addItem("Specific Gravity")
        self.dropDownGraphBox.addItem("Temperature")
        self.dropDownGraphBox.addItem("Volume")

        if self.numberTotalTanks == None:
            raise Exception("No fermentations active")

        for i in range(self.numberTotalTanks):
            self.dropDownBox.addItem(f"Fermentation tank {i+1}")
        


        self.plot = FermentPlot(self.LOGIN)
        self.plot.updateData(1, "Sg")
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
        self.quitButton.clicked.connect(lambda: self.close())
        quitLayout = QHBoxLayout()
        quitLayout.addStretch(100)
        quitLayout.addWidget(self.quitButton)

        self.mainLayout = QVBoxLayout(self)
        self.mainLayout.addLayout(self.gridLayout)
        self.mainLayout.addLayout(quitLayout)

        updateTimer = QTimer(self)
        updateTimer.timeout.connect(self.indexChanged)
        updateTimer.start(1000)

        if __name__ == "__main__":
            self.fakeFermentCount = 0
            self.fakeFermenter = SQLFermentMonitor(self.LOGIN,1,1)
            # self.fakeFermenter2 = SQLFermentMonitor(self.LOGIN,5,4)
            updateDataTimer = QTimer(self)
            updateDataTimer.timeout.connect(self.fakeFermentData)
            updateDataTimer.start(1000)

    def indexChanged(self):
        self._log.debug(f"INDEX {self.dropDownBox.currentIndex()}")
        self.plot.updateData(self.dropDownBox.currentIndex()+1, self.textGraphDrop[f"{self.dropDownGraphBox.currentText()}"])

    def fakeFermentData(self):
        x = self.fakeFermentCount
        temp = np.divide(10*np.power(x,3)+2*np.square(x)-x, 2*np.power(x,3)+10*np.square(x)+1)
        self.fakeFermenter.record(float(temp),float(temp*2),float(temp*4))
        # self.fakeFermenter2.record(float(temp),float(temp*2),float(temp*4))
        self.fakeFermentCount +=1

if __name__ == "__main__":
    import logging
    _logname = 'FermentMonitorMain'
    _log = logging.getLogger(f'{_logname}')
    
    HOST = "localhost"
    USER = "Test"
    PASSWORD = "BirraMosfeti"
    LOGIN = [HOST,USER,PASSWORD]



    app = QApplication(sys.argv)
    #window = MonitorWindow(mashtime=mashtime, boiltime=boiltime,hop1=hop1,hop2=hop2,hop3=hop3,hop4=hop4)
    window = FermentMonitor(LOGIN)
    window.show()
    sys.exit(app.exec_())