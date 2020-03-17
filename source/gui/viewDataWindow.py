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
    QApplication, QMainWindow, QWidget, QTableWidget,\
    QSlider, QPushButton, QLabel, \
    QMessageBox, QDialog, QLineEdit, \
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QGroupBox, \
    QDateEdit, QComboBox, QCalendarWidget, QTableWidgetItem, QTableView \
    
from source.tools.constants import DEGREES
from source.tools.sqlHandler import SqlTableHandler as db
from source.tools.sqlBrewingComms import SQLNewBrew
from source.gui.boilMashMonitor import MonitorWindow as MashBoilMonitor

my_array = [['1','Carling','01/01/19'],
            ['2','Tennents','13/10/19'],
            ['3','Drygate','21/01/20'],
            ['4','Asahi','01/03/20']]

class ViewDataWindow(QDialog):
    formSubmitted = pyqtSignal()

    def __init__(self, LOGIN, parent=None):
        super(ViewDataWindow, self).__init__(parent)
        self.LOGIN = LOGIN
        self.db = db(self.LOGIN,"Brewing")

        print(self.db.readFromTable("Brews", "id, Recipe, Date"))
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
        self.but_clearFilter = QPushButton("Clear Filter")
        self.but_clearFilter.setAutoDefault(0)
        clearHLayout = QHBoxLayout()
        clearHLayout.addStretch(1)
        clearHLayout.addWidget(self.but_clearFilter)
        clearHLayout.addStretch(1)
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
        model = MyTableModel(my_array, header, self)     
        self.proxyModel = QSortFilterProxyModel(self)
        self.proxyModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxyModel.setSourceModel(model)
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

        # Main vertical layout
        vLayout = QVBoxLayout()
        vLayout.addWidget(filterGroupBox)
        vLayout.addWidget(self.dataTable)
        vLayout.addLayout(quitHLayout)

        self.setLayout(vLayout)

        self.but_quit.clicked.connect(self.quitButtonClicked)

    def quitButtonClicked(self):     
        
        self.close()

    def filter_batchID(self):
        self.lineEdit_recipe.clear()
        self.proxyModel.setFilterRegExp(self.edit_batchID.text())
        self.proxyModel.setFilterKeyColumn(0)

    def filter_recipe(self):
        self.edit_batchID.clear()
        self.proxyModel.setFilterRegExp(self.lineEdit_recipe.text())
        self.proxyModel.setFilterKeyColumn(1)

    def filter_date(self):     
        self.lineEdit_recipe.clear()
        self.edit_batchID.clear()
        self.proxyModel.setFilterRegExp(self.dateEdit.date().toString("dd/MM/yy"))
        self.proxyModel.setFilterKeyColumn(2)

    def clearFilters(self):
        self.dateEdit.setDate(self.maxDate)
        self.proxyModel.setFilterRegExp('')
        self.proxyModel.setFilterKeyColumn(0)
        self.proxyModel.setFilterKeyColumn(1)
        self.proxyModel.setFilterKeyColumn(2)
        self.lineEdit_recipe.clear()
        self.edit_batchID.clear()
        

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