#-*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))

#from PySide2 import QtWidgets
from PyQt5.QtCore import \
    Qt,pyqtSignal, QDate, QObject, QAbstractTableModel, QVariant, \
    QSortFilterProxyModel #, pyqtSlot
from PyQt5.QtGui import \
    QFont
from PyQt5.QtWidgets import \
    QApplication, QMainWindow, QWidget, QTableWidget, QTabWidget, \
    QSlider, QPushButton, QLabel, \
    QMessageBox, QDialog, QLineEdit, \
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QGroupBox, \
    QDateEdit, QComboBox, QCalendarWidget, QTableWidgetItem, QTableView \
    
from source.tools.constants import DEGREES
from source.tools.sqlHandler import SqlTableHandler as db
from source.tools.sqlBrewingComms import SQLNewBrew
from source.gui.boilMashMonitor import MonitorWindow as MashBoilMonitor

my_array = [('1','Carling','01/01/19'),
            ('2','Tennents','13/10/19'),
            ('3','Drygate','21/01/20'),
            ('4','Asahi','01/03/20')]

class ViewDataWindow(QDialog):
    formSubmitted = pyqtSignal()

    def __init__(self, LOGIN, parent=None):
        super(ViewDataWindow, self).__init__(parent)
        self.LOGIN = LOGIN
        self.db = db(self.LOGIN,"Brewing")

        #print(self.db.readFromTable("Brews", "id, Recipe, Date"))
        self.create_layout_viewData()
        self.setWindowTitle('Data Viewer')

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
        

        # Database data
        #self.db.readFromTable("Brews", "id, Recipe, Date")

        # Create bottom buttons
        self.but_quit = QPushButton("Quit")
        self.but_quit.setAutoDefault(0)
        self.but_view = QPushButton("View Data")
        self.but_view.setAutoDefault(0)
        quitHLayout = QHBoxLayout()
        quitHLayout.addStretch(0)
        quitHLayout.addWidget(self.but_quit)
        quitHLayout.addStretch(3)
        quitHLayout.addWidget(self.but_view)
        quitHLayout.addStretch(0)

        # Main vertical layout for left area
        vLayoutL = QVBoxLayout()
        vLayoutL.addWidget(filterGroupBox)
        vLayoutL.addWidget(self.dataTable)
        vLayoutL.addLayout(quitHLayout)

        # Main h layout for displayed brews widget
        displayTitle = QLabel("Displayed Brews") 
        hLayoutDisplayed = QHBoxLayout()
        hLayoutDisplayed.addWidget(displayTitle)

        # Main vertical layout for right area
        vLayoutR = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabMash = MashTab()
        self.tabBoil = BoilTab()
        self.tabFerment = FermentTab()
        self.tabs.resize(100,1000)
        self.tabs.addTab(self.tabMash,"Mash")
        self.tabs.addTab(self.tabBoil, "Boil")
        self.tabs.addTab(self.tabFerment, "Ferment")
        vLayoutR.addLayout(hLayoutDisplayed)
        vLayoutR.addWidget(self.tabs)
        
        # Main layout for whole window
        mainLayout = QHBoxLayout()
        mainLayout.addLayout(vLayoutL, 1)
        mainLayout.addLayout(vLayoutR, 2)

        self.setLayout(mainLayout)
        self.setGeometry(0, 0, 2000, 1000)

        self.but_view.clicked.connect(self.viewButtonClicked)
        self.but_quit.clicked.connect(self.quitButtonClicked)

    def quitButtonClicked(self):     
        
        self.close()


    # Slot for adding selected brew to widget
    def viewButtonClicked(self): # brewID, recipe, date, displayNo):

        rows = sorted(set(index.row() for index in
                      self.dataTable.selectedIndexes()))
        for row in rows:
            print('Row %d is selected' % row)
            test = self.model.data(self.dataTable.selectedIndexes()[0], 0).value()
            print(test)
            #print(self.model.data(self.dataTable.selectedIndexes()[0], 0))
        
        #brewID = self.model.data(rows)

        #brewGroupBox = QGroupBox(f'displayNo')
        #brewForm = QFormLayout()
        #brewForm.addRow(QLabel('Brew ID:'), brewID)
        #brewForm.addRow(QLabel('Recipe:'), recipe)
        #brewForm.addRow(QLabel('Date:'), date)
        #brewGroupBox.addLayout(brewForm)
    
    # Slot for filtering by Batch ID
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
        self.arraydata = datain
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
        
        # Groupbox for Inputs section
        inputGroupBox = QGroupBox("Inputs")
        inputForm = QFormLayout() 
        self.mashTempLab = QLabel()
        inputForm.addRow(QLabel(f'Temperature ({DEGREES}C):'), self.mashTempLab)
        self.mashTimeLab = QLabel()
        inputForm.addRow(QLabel(f'Time (mins):'), self.mashTimeLab)
        inputGroupBox.setLayout(inputForm)

        # Groupbox for Temp graph
        tempGroupBox = QGroupBox("Temperature Graph")
        # command to add graph to groupbox

        # V layout for input box
        vLayout = QVBoxLayout()
        vLayout.addWidget(inputGroupBox)
        vLayout.addStretch(1)
        # Main H layout for mash tab
        hLayout = QHBoxLayout()
        hLayout.addLayout(vLayout)
        hLayout.addWidget(tempGroupBox, 1)
        self.setLayout(hLayout)

class BoilTab(QTabWidget):

    def __init__(self, parent=None):
        super(BoilTab, self).__init__(parent)
        self.create_layout_boilTab()

    def create_layout_boilTab(self):
        
        # Groupbox for Inputs section
        inputGroupBox = QGroupBox("Inputs")
        inputForm = QFormLayout() 
        self.boilTempLab = QLabel()
        inputForm.addRow(QLabel(f'Temperature ({DEGREES}C):'), self.boilTempLab)
        self.boilTimeLab = QLabel()
        inputForm.addRow(QLabel(f'Time (mins):'), self.boilTimeLab)
        inputGroupBox.setLayout(inputForm)

        # Groupbox for Temp graph
        tempGroupBox = QGroupBox("Temperature Graph")
        # command to add graph to groupbox

        # V layout for input box
        vLayout = QVBoxLayout()
        vLayout.addWidget(inputGroupBox)
        vLayout.addStretch(1)
        # Main H layout for mash tab
        hLayout = QHBoxLayout()
        hLayout.addLayout(vLayout)
        hLayout.addWidget(tempGroupBox, 1)
        self.setLayout(hLayout)

class FermentTab(QTabWidget):

    def __init__(self, parent=None):
        super(FermentTab, self).__init__(parent)
        self.create_layout_fermentTab()

    def create_layout_fermentTab(self):
        
        # Groupbox for Inputs section
        inputGroupBox = QGroupBox("Inputs")
        inputForm = QFormLayout() 
        self.fermentTempLab = QLabel()
        inputForm.addRow(QLabel(f'Temperature ({DEGREES}C):'), self.fermentTempLab)
        inputGroupBox.setLayout(inputForm)

        # Groupbox for Temp graph
        tempGroupBox = QGroupBox("Temperature Graph")
        # command to add graph to groupbox

        # Groupbox for Specific Gravity Graph
        gravGroupBox = QGroupBox("Specific Gravity Graph")
        # command to add graph to groupbox

        # V layout for input box
        vLayout = QVBoxLayout()
        vLayout.addWidget(inputGroupBox)
        vLayout.addStretch(1)

        # V layout for graphs
        vLayout2 = QVBoxLayout()
        vLayout2.addWidget(tempGroupBox)
        vLayout2.addWidget(gravGroupBox)

        # Main H layout for mash tab
        hLayout = QHBoxLayout()
        hLayout.addLayout(vLayout)
        hLayout.addLayout(vLayout2, 2)
        self.setLayout(hLayout)

# Class for widget that shows which brews are being displayed
class DisplayedBrews(QWidget):

    def __init__(self, parent=None):
        super(DisplayedBrews, self).__init__(parent)
        self.create_layout_displayedBrews()

    def create_layout_displayedBrews(self):

        title = QLabel("Displayed Brews")

        # Main h layout for widget
        hLayout = QHBoxLayout()
        hLayout.addWidget(title)

        

    # Function for adding selected brew to widget
    def add_brew(self, brewID, recipe, date, displayNo):

        brewGroupBox = QGroupBox(f'displayNo')
        brewForm = QFormLayout()
        brewForm.addRow(QLabel('Brew ID:'), brewID)
        brewForm.addRow(QLabel('Recipe:'), recipe)
        brewForm.addRow(QLabel('Date:'), date)
        brewGroupBox.addLayout(brewForm)

