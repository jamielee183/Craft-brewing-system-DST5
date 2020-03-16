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
        self.minDate = QDate(2020,1,1)
        self.dateEdit.setDate(self.minDate)
        self.dateEdit.setDateRange(self.minDate, self.maxDate)
        self.dateEdit.setCalendarPopup(1)
        
        # Recipe drop down box
        lab_recipe = QLabel("Recipe:")
        self.recipeEdit = QComboBox()
        self.recipeEdit.addItem("Recipe 1")
        self.recipeEdit.addItem("Recipe 2")
        self.recipeEdit.addItem("Recipe 3")

        ### Text edit filters ###
        # Batch ID search
        self.edit_batchID = QLineEdit()
        self.edit_batchID.setPlaceholderText("Enter Batch ID")
        self.but_IDsearch = QPushButton("Go")
        self.but_IDsearch.clicked.connect(self.filter_batchID)
        # Recipe search
        self.lineEdit_recipe = QLineEdit()
        self.lineEdit_recipe.setPlaceholderText("Enter Recipe")
        self.lineEdit_recipe.textChanged.connect(self.filter_recipe)
        
        # Filter groupbox layout
        recipeHLayout = QHBoxLayout()
        recipeHLayout.addWidget(lab_recipe)
        recipeHLayout.addWidget(self.recipeEdit)
        recipeVLayout = QVBoxLayout()
        recipeVLayout.addLayout(recipeHLayout)
        recipeVLayout.addWidget(self.lineEdit_recipe)
        filterHLayout = QHBoxLayout()
        filterHLayout.addStretch(1)
        filterHLayout.addWidget(lab_date)
        filterHLayout.addWidget(self.dateEdit)
        filterHLayout.addStretch(1)
        filterHLayout.addLayout(recipeVLayout)
        filterHLayout.addStretch(1)
        filterHLayout.addWidget(self.edit_batchID)
        filterHLayout.addWidget(self.but_IDsearch)
        filterHLayout.addStretch(1)
        filterGroupBox.setLayout(filterHLayout)

        # scrollHLayout = QHBoxLayout()
        # scrollHLayout.addWidget(filterGroupBox)
        # scrollHLayout.addStretch(1)

        
        # Create QTableView of brew data
        header = ['Brew ID', 'Recipe', 'Date']
        model = MyTableModel(my_array, header, self)     
        self.proxyModel =  QSortFilterProxyModel(self)
        self.proxyModel.setSourceModel(model)
        self.dataTable = QTableView()          
        self.dataTable.setModel(self.proxyModel)
        self.dataTable.setSortingEnabled(True)

        #for x in self.db.readFromTable("Brews", "id, Recipe, Date"):

        #    self.addTableData(x)

        # Create quit button
        self.but_quit = QPushButton("Quit")
        quitHLayout = QHBoxLayout()
        quitHLayout.addStretch(1)
        quitHLayout.addWidget(self.but_quit)

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
        self.proxyModel.setFilterRegExp(self.lineEdit_recipe.text())
        self.proxyModel.setFilterKeyColumn(1)


    # To do - functions to add database into dataTable, don't know how to access
    # database data and what format it is in
  #  def loadData(self):
        
    # This function takes columns from the database and adds the items to the table row by row
    # Just need to know how to correctly pass it columns from the database
    def addTableData(self, dataIn):

        rowPosition = self.dataTable.rowCount()
        self.dataTable.insertRow(rowPosition)

        for i in range(3):
            self.dataTable.setItem(rowPosition,i, QTableWidgetItem(str(dataIn[i])))

    #    for i, column in enumerate(columns):
    #        self.dataTable.setItem(rowPosition, i, QWidgets.QtTableWidgetItem(str(column)))


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