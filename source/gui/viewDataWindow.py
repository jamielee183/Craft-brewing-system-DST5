#-*- coding: utf-8 -*-

import sys
import os
import numpy as np
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))


#from PySide2 import QtWidgets
from PyQt5.QtCore import \
    Qt,pyqtSignal, QDate, QObject, QAbstractTableModel, QVariant,\
    QSortFilterProxyModel #, pyqtSlot
from PyQt5.QtGui import \
    QFont, QPalette, QColor
from PyQt5.QtWidgets import \
    QApplication, QMainWindow, QWidget, QTableWidget, QTabWidget, \
    QSlider, QPushButton, QLabel, QScrollArea,\
    QMessageBox, QDialog, QLineEdit, QSplitter, \
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QGroupBox, \
    QDateEdit, QComboBox, QCalendarWidget, QTableWidgetItem, QTableView\

from qwt import QwtPlot, QwtPlotMarker, QwtSymbol, QwtLegend, QwtPlotGrid, \
            QwtPlotCurve, QwtPlotItem, QwtLogScaleEngine, QwtText,  \
            QwtPlotRenderer, QwtScaleDraw, QwtText
    
from source.tools.constants import DEGREES
from source.tools.sqlHandler import SqlTableHandler as db
from source.tools.sqlBrewingComms import SQLNewBrew
from source.gui.boilMashMonitor import MonitorWindow as MashBoilMonitor
from source.gui.guitools import TimeScaleDraw, DateTimeTimeScaleDraw, NewGraph


class ViewDataWindow(QDialog):
    formSubmitted = pyqtSignal()
    closeSignal = pyqtSignal()

    def __init__(self, LOGIN, parent=None):
        #super(ViewDataWindow, self).__init__(parent)
        super().__init__(parent)
        self.LOGIN = LOGIN
        self.db = db(self.LOGIN,"Brewing")
        self.displayNo = 0
        self.displayedBrewsH = []
        self.displayedBrewsVMash = []
        self.displayedBrewsVBoil = []
        self.displayedBrewsVFerment = []
        self.create_layout_viewData()
        self.setWindowTitle('Past Brew Viewer')
        self.activeColours = []
        self.colours = ["red", "green", "blue", "black",\
                        "cyan", "magenta", "yellow", "gray"]
        
        
    # Function to create layout of New Brew window
    def create_layout_viewData(self):

        # Create scroll boxes for filtering data
        filterGroupBox = QGroupBox("Filter by:")

        # Date edit box
        lab_date = QLabel("Date:")
        self.dateEdit = QDateEdit()   
        # Set range of possible dates, current date is max date
        self.maxDate = QDate().currentDate()
        self.minDate = QDate(2019,1,1)
        self.dateEdit.setDate(self.maxDate)
        self.dateEdit.setDateRange(self.minDate, self.maxDate)
        self.dateEdit.setCalendarPopup(1)
        self.dateEdit.setDisplayFormat("dd/MM/yy")
        #self.dateEdit2 = QLineEdit()
        self.dateEdit.dateChanged.connect(self.filter_date)

        dateHLayout = QHBoxLayout()
        dateHLayout.addWidget(lab_date)
        dateHLayout.addWidget(self.dateEdit)
        

        ### Text edit filters ###
        # Batch ID search
        lab_batch = QLabel("Batch ID:")
        self.edit_batchID = QLineEdit()
        self.edit_batchID.setPlaceholderText("Enter Batch ID")
        self.but_IDsearch = QPushButton("Go")
        self.but_IDsearch.setAutoDefault(0)
        self.but_IDsearch.clicked.connect(self.filter_batchID)
        self.edit_batchID.returnPressed.connect(self.filter_batchID)
        batchHLayout = QHBoxLayout()
        batchHLayout.addWidget(lab_batch)
        batchHLayout.addWidget(self.edit_batchID)
        batchHLayout.addWidget(self.but_IDsearch)
        
        # Recipe search
        lab_recipe = QLabel("Recipe:")
        self.lineEdit_recipe = QLineEdit()
        self.lineEdit_recipe.setPlaceholderText("Enter Recipe")      
        self.lineEdit_recipe.textChanged.connect(self.filter_recipe)
        self.lineEdit_recipe.returnPressed.connect(self.filter_recipe)
        recipeHLayout = QHBoxLayout()
        recipeHLayout.addWidget(lab_recipe)
        recipeHLayout.addWidget(self.lineEdit_recipe)

        # Clear filters button
        self.but_clearFilter = QPushButton("Clear Filters")
        self.but_clearFilter.setAutoDefault(0)
        clearHLayout = QHBoxLayout()
        clearHLayout.addStretch(1)
        clearHLayout.addWidget(self.but_clearFilter)
        clearHLayout.addStretch(0)
        self.but_clearFilter.clicked.connect(self.clearFilters)

        # Filter groupbox layout
        
        #recipeHLayout.addWidget(self.recipeEdit)
        #recipeVLayout = QVBoxLayout()
        #recipeVLayout.addLayout(recipeHLayout)
        #recipeVLayout.addWidget(self.lineEdit_recipe)
        filterHLayout = QHBoxLayout()
        filterHLayout.addStretch(1)
        filterHLayout.addWidget(lab_date)
        filterHLayout.addWidget(self.dateEdit)
        filterHLayout.addStretch(1)
        #filterHLayout.addLayout(recipeVLayout)
        filterHLayout.addStretch(1)
        filterHLayout.addWidget(self.edit_batchID)
        filterHLayout.addWidget(self.but_IDsearch)
        filterHLayout.addStretch(1)
        #filterGroupBox.setLayout(filterHLayout)

        # Alternate - Filter vertical layout
        filterVLayout = QVBoxLayout()
        filterVLayout.addLayout(batchHLayout)
        filterVLayout.addLayout(recipeHLayout)
        filterVLayout.addLayout(dateHLayout)
        filterVLayout.addLayout(clearHLayout)
        filterGroupBox.setLayout(filterVLayout)

        # scrollHLayout = QHBoxLayout()
        # scrollHLayout.addWidget(filterGroupBox)
        # scrollHLayout.addStretch(1)

        
        # Create QTableView of brew data
        header = ['Brew ID', 'Recipe', 'Date'] 
        self.model = MyTableModel(self.db.readFromTable("Brews", "id, Recipe, Date"), header, self)
        self.proxyModel = QSortFilterProxyModel(self)
        self.proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxyModel.setSourceModel(self.model)
        self.dataTable = QTableView() 
        self.dataTable.setModel(self.proxyModel)
        self.dataTable.setSortingEnabled(True)
        self.dataTable.setSelectionBehavior(1)
        

        # Create bottom buttons
        self.but_quit = QPushButton("Quit")
        self.but_quit.setAutoDefault(0)
        self.but_view = QPushButton("Display Brew")
        self.but_view.setAutoDefault(0)
        quitHLayout = QHBoxLayout()
        quitHLayout.addStretch(0)
        quitHLayout.addWidget(self.but_quit)
        quitHLayout.addStretch(3)
        quitHLayout.addWidget(self.but_view)
        quitHLayout.addStretch(0)

        # Main vertical layout for left area
        lWidget = QWidget()
        vLayoutL = QVBoxLayout(lWidget)
        vLayoutL.addWidget(filterGroupBox)
        vLayoutL.addWidget(self.dataTable)
        vLayoutL.addLayout(quitHLayout)


        # Widget for displayed brews - Widget allows fixed height to be set
        displayedWidget = QWidget()
        #displayedWidget.setFixedHeight(180)
        # h Layout to add groupboxes of displayed brews - added to in viewButtonClicked slot
        self.hLayoutDisplayed = QHBoxLayout()
        self.hLayoutDisplayed.addStretch(1)
        self.hLayoutDisplayed.setSizeConstraint(5)
        displayedWidget.setLayout(self.hLayoutDisplayed)
        # Scroll area for horizontal displayed brews
        hScrollArea = QScrollArea()
        hScrollArea.setWidget(displayedWidget)
        hScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        hScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        hScrollArea.setFixedHeight(170)
        # Main v layout for displayed brews widget
        displayTitle = QLabel("Displayed Brews:")
        displayTitle.setMaximumHeight(20)
        self.vLayoutDisplayed = QVBoxLayout()
        self.vLayoutDisplayed.addWidget(displayTitle)
        self.vLayoutDisplayed.addWidget(hScrollArea)

        # Main vertical layout for right area
        rWidget = QWidget()
        vLayoutR = QVBoxLayout(rWidget)
        self.tabs = QTabWidget()
        self.tabMash = MashTab()
        self.tabBoil = BoilTab()
        self.tabFerment = FermentTab()
        self.tabs.resize(100,1000)
        self.tabs.setMinimumSize(400,400)
        self.tabs.addTab(self.tabMash,"Mash")
        self.tabs.addTab(self.tabBoil, "Boil")
        self.tabs.addTab(self.tabFerment, "Ferment")
        vLayoutR.addLayout(self.vLayoutDisplayed)
        vLayoutR.addWidget(self.tabs)

        # Main layout for whole window - splitter so widget sizes are adjustable
        mainLayout = QHBoxLayout()
        mainSplitter = QSplitter()
        mainSplitter.addWidget(lWidget)
        mainSplitter.addWidget(rWidget)
        mainLayout.addWidget(mainSplitter)
        mainSplitter.setSizes([260,740])


        self.setLayout(mainLayout)
        #self.showFullScreen()
        self.setGeometry(0, 0, 1500, 1000)

        self.but_view.clicked.connect(self.viewButtonClicked)
        self.but_view.clicked.connect(self.viewButtonClickedTabs)
        self.but_quit.clicked.connect(self.quitButtonClicked)


    def quitButtonClicked(self):     
        
        self.close()
        self.closeSignal.emit()


    # Slot for adding selected brew to widget
    def viewButtonClicked(self):
        
        self.brewInfo = [] # array to place brew info: ID, Recipe, Date
        self.displayNo = self.displayNo + 1
        # Add brew info to array based on selected row
        index = (self.dataTable.selectionModel().currentIndex())
        for i in range(3):
            self.brewInfo.append(QLabel(str(index.sibling(index.row(), i).data())))

        # Choose colour to use for this displayed brew
        self.colourToUse = self.chooseColour()

        # Create group box with all brew info displayed and Remove button
        brewGroupBox = QGroupBox(str(self.displayNo))
        brewGroupBox.setObjectName("ColouredGroupBox")
        brewGroupBox.setStyleSheet("QGroupBox#ColouredGroupBox { border: 2px solid %s;}" % self.colourToUse)
        brewForm = QFormLayout()
        brewForm.addRow(QLabel('Brew ID:'), self.brewInfo[0])
        brewForm.addRow(QLabel('Recipe:'), self.brewInfo[1])
        brewForm.addRow(QLabel('Date:'), self.brewInfo[2])
        removeButHLayout = QHBoxLayout()
        removeButHLayout.addStretch(1)
        self.but_Remove = QPushButton("Remove")
        removeButHLayout.addWidget(self.but_Remove)
        brewForm.addRow(removeButHLayout)
        brewGroupBox.setLayout(brewForm)
        # Add group box to layout - use insert so that stretch stays on right side
        self.hLayoutDisplayed.insertWidget(self.displayNo-1, brewGroupBox)
        self.displayedBrewsH.append(brewGroupBox) # Add groupbox to array of displayed brews
        # Signal to connect remove brew button. Lambda function used to pass argument of specific
        # brew to be removed
        self.but_Remove.clicked.connect(lambda: self.removeBrewClickedMash(brewGroupBox))
        self.but_Remove.clicked.connect(lambda: self.removeBrewClickedBoil(brewGroupBox))
        self.but_Remove.clicked.connect(lambda: self.removeBrewClickedFerment(brewGroupBox))
        self.but_Remove.clicked.connect(lambda: self.removeBrewClicked(brewGroupBox))

    
    # Slot for adding brew info to each of the process tabs
    def viewButtonClickedTabs(self):

        batchID = self.brewInfo[0].text()
        # Query database to get recipe data for the brew selected to view
        # brewInfo[0].text() gives brew ID for selected brew from table
        sql = f"SELECT * FROM Brews WHERE id = '{self.brewInfo[0].text()}'"
        query = self.db.custom(sql)

        self.recipedata = {}
        self.recipedata['batchID']    = query[0][0]
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

        # Create groupboxes for each of the process tabs to fill with brew info
        mashGroupBox = QGroupBox(str(self.displayNo))
        mashGroupBox.setObjectName("MashColouredGroupBox")
        mashGroupBox.setStyleSheet("QGroupBox#MashColouredGroupBox { border: 2px solid %s;}" % self.colourToUse)
        mashFormLayout = QFormLayout()
        mashFormLayout.addRow(QLabel(f"Temp ({DEGREES}C): {self.recipedata['mashTemp']}"))
        mashFormLayout.addRow(QLabel(f"Time (mins): {self.recipedata['mashTime']}"))
        mashGroupBox.setLayout(mashFormLayout)
        self.tabMash.mashVLayout.insertWidget(self.displayNo - 1, mashGroupBox)
        self.displayedBrewsVMash.append(mashGroupBox)

        boilGroupBox = QGroupBox(str(self.displayNo))
        boilGroupBox.setObjectName("BoilColouredGroupBox")
        boilGroupBox.setStyleSheet("QGroupBox#BoilColouredGroupBox { border: 2px solid %s;}" % self.colourToUse)
        boilFormLayout = QFormLayout()
        boilFormLayout.addRow(QLabel(f"Temp ({DEGREES}C):{self.recipedata['boilTemp']}"))
        boilFormLayout.addRow(QLabel(f"Time (mins): {self.recipedata['boilTime']}"))
        boilFormLayout.addRow(QLabel(f"Hop 1: {self.recipedata['hop1'][0]}"))
        boilFormLayout.addRow(QLabel(f"Time (mins): {self.recipedata['hop1'][1]}"))
        boilFormLayout.addRow(QLabel(f"Hop 2: {self.recipedata['hop2'][0]}"))
        boilFormLayout.addRow(QLabel(f"Time (mins): {self.recipedata['hop2'][1]}"))
        boilFormLayout.addRow(QLabel(f"Hop 3: {self.recipedata['hop3'][0]}"))
        boilFormLayout.addRow(QLabel(f"Time (mins): {self.recipedata['hop3'][1]}"))
        boilFormLayout.addRow(QLabel(f"Hop 4: {self.recipedata['hop4'][0]}"))
        boilFormLayout.addRow(QLabel(f"Time (mins): {self.recipedata['hop4'][1]}"))
        boilGroupBox.setLayout(boilFormLayout)
        self.tabBoil.boilVLayout.insertWidget(self.displayNo - 1, boilGroupBox)
        self.displayedBrewsVBoil.append(boilGroupBox)

        fermentGroupBox = QGroupBox(str(self.displayNo))
        fermentGroupBox.setObjectName("FermentColouredGroupBox")
        fermentGroupBox.setStyleSheet("QGroupBox#FermentColouredGroupBox { border: 2px solid %s;}" % self.colourToUse)
        fermentFormLayout = QFormLayout()
        fermentFormLayout.addRow(QLabel(f"Temp ({DEGREES}C): {self.recipedata['fermenttemp']}"))
        #fermentFormLayout.addRow(QLabel('Time (mins):'))
        fermentGroupBox.setLayout(fermentFormLayout)
        self.tabFerment.fermentVLayout.insertWidget(self.displayNo - 1, fermentGroupBox)
        self.displayedBrewsVFerment.append(fermentGroupBox)

        ### PUTTING DATA ONTO GRAPHS ###
        # Query database to get data to plot on graphs
        sqlMash = f"SELECT TimeStamp, Temp FROM Mash WHERE BatchID = '{batchID}'"        
        sqlBoil = f"SELECT TimeStamp, Temp FROM BoilMonitor WHERE BatchID = '{batchID}'"
        sqlFermentTemp = f"SELECT TimeStamp, Temp FROM Ferment WHERE BatchID = '{batchID}'"
        sqlFermentSG = f"SELECT TimeStamp, Sg FROM Ferment WHERE BatchID = '{batchID}'"
        mashDataX, mashDataY = self.createData(sqlMash)
        boilDataX, boilDataY = self.createData(sqlBoil)
        fermentTempDataX, fermentTempDataY = self.createData(sqlFermentTemp)
        fermentSGDataX, fermentSGDataY = self.createData(sqlFermentSG)

        # Create and add curves to each of the plots
        self.tabMash.graph.createCurve(mashDataX, mashDataY, self.colourToUse)
        self.tabBoil.graph.createCurve(boilDataX, boilDataY, self.colourToUse)
        self.tabFerment.tempGraph.createCurve(fermentTempDataX[1:], fermentTempDataY[1:], self.colourToUse)
        self.tabFerment.gravGraph.createCurve(fermentSGDataX[1:], fermentSGDataY[1:], self.colourToUse)

    # Function to choose first available colour
    def chooseColour(self):
        
        # Loop through dictionary, checking if self.colours[j] appear
        for colours in self.colours:
            # If it does appear, continue to next colour
            if colours not in self.activeColours:
                # If it doesn't appear, add colour to dictionary and return colour
                self.activeColours.append(colours)
                return colours

                
    # Get data from database using sql query
    def createData(self, sql):
        timestamps = []
        tempdat = []
        for data in self.db.custom(sql):
            timestamps.append(data[0])
            tempdat.append(data[1])
        
        startTime = timestamps[0]
        for i in range(len(timestamps)):
            timestamps[i] = (timestamps[i] - startTime).seconds

        return timestamps, tempdat

    # Slot for removing group boxes from horizontal tab
    def removeBrewClicked(self, brewToRemove):
        
        brewArrayPos = self.displayedBrewsH.index(brewToRemove)

        self.hLayoutDisplayed.removeWidget(brewToRemove) # remove widget from layout
        brewToRemove.setParent(None) # remove parent so widget dissappears
        self.displayNo = self.displayNo - 1
        self.displayedBrewsH.remove(brewToRemove) # remove brew from array of displayed brews
        i = 0
        # Loop to renumber the remaining displayed groupboxes using the array
        for i in range(len(self.displayedBrewsH)):
            self.displayedBrewsH[i].setTitle(str(i+1))
        
        del self.activeColours[brewArrayPos]


    # Slot for removing group boxes of brew info in mash tab
    def removeBrewClickedMash(self, brewToRemove):
        
        # Obtain position in array of displayed brews of brew to remove
        brewArrayPos = self.displayedBrewsH.index(brewToRemove)
        # Use position to remove widget from layout
        self.tabMash.mashVLayout.takeAt(brewArrayPos)
        # Use position to remove parent
        self.displayedBrewsVMash[brewArrayPos].setParent(None)
        # Use position to delete from vertical array
        del self.displayedBrewsVMash[brewArrayPos]
        # Renumber groupboxes in vertical display
        for i in range(len(self.displayedBrewsVMash)): 
            self.displayedBrewsVMash[i].setTitle(str(i+1))
        
        # Remove curve from graph
        self.tabMash.graph.removeCurve(brewArrayPos)


    # Slot for removing group boxes of brew info in boil tab
    def removeBrewClickedBoil(self, brewToRemove):
        
        # Obtain position in array of displayed brews of brew to remove
        brewArrayPos = self.displayedBrewsH.index(brewToRemove)
        # Use position to remove widget from layout
        self.tabBoil.boilVLayout.takeAt(brewArrayPos)
        # Use position to remove parent
        self.displayedBrewsVBoil[brewArrayPos].setParent(None)
        # Use position to delete from vertical array
        del self.displayedBrewsVBoil[brewArrayPos]
        # Renumber groupboxes in vertical display
        for i in range(len(self.displayedBrewsVBoil)):
            self.displayedBrewsVBoil[i].setTitle(str(i+1))

        self.tabBoil.graph.removeCurve(brewArrayPos)

    # Slot for removing group boxes of brew info in ferment tab
    def removeBrewClickedFerment(self, brewToRemove):
        
        # Obtain position in array of displayed brews of brew to remove
        brewArrayPos = self.displayedBrewsH.index(brewToRemove)
        # Use position to remove widget from layout
        self.tabFerment.fermentVLayout.takeAt(brewArrayPos)
        # Use position to remove parent
        self.displayedBrewsVFerment[brewArrayPos].setParent(None)
        # Use position to delete from vertical array
        del self.displayedBrewsVFerment[brewArrayPos]
        # Renumber groupboxes in vertical display
        for i in range(len(self.displayedBrewsVFerment)):
            self.displayedBrewsVFerment[i].setTitle(str(i+1))

        self.tabFerment.tempGraph.removeCurve(brewArrayPos)
        self.tabFerment.gravGraph.removeCurve(brewArrayPos)

    # Slot for filtering by Batch IDdisplayed
    def filter_batchID(self):
        self.lineEdit_recipe.clear()
        self.proxyModel.setFilterRegExp(self.edit_batchID.text())
        self.proxyModel.setFilterKeyColumn(0)

    # Slot for filtering by Recipe
    def filter_recipe(self):
        self.edit_batchID.clear()
        self.proxyModel.setFilterRegExp(self.lineEdit_recipe.text())
        self.proxyModel.setFilterKeyColumn(1)

    # Slot for filtering by date
    def filter_date(self):     
        self.lineEdit_recipe.clear()
        self.edit_batchID.clear()
        self.proxyModel.setFilterRegExp(self.dateEdit.date().toString("dd/MM/yy"))
        self.proxyModel.setFilterKeyColumn(2)

    # Slot for clearing all filters
    def clearFilters(self):
        self.dateEdit.setDate(self.maxDate)
        self.proxyModel.setFilterRegExp('')
        self.proxyModel.setFilterKeyColumn(0)
        self.proxyModel.setFilterKeyColumn(1)
        self.proxyModel.setFilterKeyColumn(2)
        self.lineEdit_recipe.clear()
        self.edit_batchID.clear()
        

# Class to create model to hold database data to present in table
class MyTableModel(QAbstractTableModel):
    def __init__(self, datain, headerdata, parent=None, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        
        self.arraydata = []
        # Loop to convert all dates to strings to be displayed in table
        for i in range(len(datain)):
            self.arraydata.append(list(datain[i]))
            self.arraydata[i][2] = self.arraydata[i][2].strftime("%d/%m/%Y")

        self.headerdata = headerdata

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.arraydata[index.row()][index.column()])        
        
    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.headerdata[col])
        return QVariant()


### Classes for each of the tabs in the window (Mash, Boil, Ferment) ###
class MashTab(QTabWidget):

    def __init__(self, parent=None):
        super(MashTab, self).__init__(parent)
        self.create_layout_mashTab()

    def create_layout_mashTab(self):

        self.graph = NewGraph()
        self.graph.createGraph()
        self.graph.setTitle("Mash Temperature")
        self.graph.setAxisTitles(f"Temperature ({DEGREES}C)", "Time (mins)")
        
        # V layout for input box inside widget to allow fixed width
        displayedWidget = QWidget()
        displayedWidget.setFixedWidth(150)
        self.mashVLayout = QVBoxLayout()
        self.mashVLayout.addStretch(1)
        self.mashVLayout.setSizeConstraint(5)
        displayedWidget.setLayout(self.mashVLayout)
        mashScrollArea = QScrollArea()
        mashScrollArea.setWidget(displayedWidget)
        mashScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Main H layout for mash tab
        hLayout = QHBoxLayout()
        hLayout.addWidget(mashScrollArea)
        hLayout.addWidget(self.graph.plot, 1)
        self.setLayout(hLayout)

class BoilTab(QTabWidget):

    def __init__(self, parent=None):
        super(BoilTab, self).__init__(parent)
        self.create_layout_boilTab()

    def create_layout_boilTab(self):

        self.graph = NewGraph()
        self.graph.createGraph()
        self.graph.setTitle("Boil Temperature")
        self.graph.setAxisTitles(f"Temperature ({DEGREES}C)", "Time (mins)")

        # V layout for input box inside widget to allow fixed width
        displayedWidget = QWidget()
        displayedWidget.setFixedWidth(150)
        self.boilVLayout = QVBoxLayout()
        self.boilVLayout.addStretch(1)
        self.boilVLayout.setSizeConstraint(5)
        displayedWidget.setLayout(self.boilVLayout)
        boilScrollArea = QScrollArea()
        boilScrollArea.setWidget(displayedWidget)
        boilScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Main H layout for mash tab
        hLayout = QHBoxLayout()
        hLayout.addWidget(boilScrollArea)
        hLayout.addWidget(self.graph.plot, 1)
        self.setLayout(hLayout)

class FermentTab(QTabWidget):

    def __init__(self, parent=None):
        super(FermentTab, self).__init__(parent)
        self.create_layout_fermentTab()

    def create_layout_fermentTab(self):

        tabs = QTabWidget()
        tabTemp = QTabWidget()
        tabGrav = QTabWidget()

        self.tempGraph = NewGraph()
        self.tempGraph.createGraph()
        self.tempGraph.setTitle("Fermentation Temperature")
        self.tempGraph.setAxisTitles(f"Temperature ({DEGREES}C)", "Time")
        tempLayout = QVBoxLayout()
        tempLayout.addWidget(self.tempGraph.plot)
        tabTemp.setLayout(tempLayout)

        self.gravGraph = NewGraph()
        self.gravGraph.createGraph()
        self.gravGraph.setTitle("Specific Gravity")
        self.gravGraph.setAxisTitles("Specific Gravity", "Time")
        gravLayout = QVBoxLayout()
        gravLayout.addWidget(self.gravGraph.plot)
        tabGrav.setLayout(gravLayout)

        # V layout for input box inside widget to allow fixed width
        displayedWidget = QWidget()
        displayedWidget.setFixedWidth(150)
        self.fermentVLayout = QVBoxLayout()       
        self.fermentVLayout.addStretch(1)
        self.fermentVLayout.setSizeConstraint(5)
        displayedWidget.setLayout(self.fermentVLayout)
        fermentScrollArea = QScrollArea()
        fermentScrollArea.setWidget(displayedWidget)
        fermentScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # V layout for graphs - adding tabs
        tabs.addTab(tabTemp,"Temp")
        tabs.addTab(tabGrav, "Gravity")        
        vLayout2 = QVBoxLayout()
        vLayout2.addWidget(tabs)

        # Main H layout for mash tab
        hLayout = QHBoxLayout()
        hLayout.addWidget(fermentScrollArea)
        hLayout.addLayout(vLayout2, 2)
        self.setLayout(hLayout)

