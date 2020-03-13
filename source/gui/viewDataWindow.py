#-*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))

#from PySide2 import QtWidgets
from PyQt5.QtCore import \
    Qt,pyqtSignal, QDate #, pyqtSlot
from PyQt5.QtGui import \
    QFont
from PyQt5.QtWidgets import \
    QApplication, QMainWindow, QWidget, QTableWidget,\
    QSlider, QPushButton, QLabel, \
    QMessageBox, QDialog, QLineEdit, \
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QGroupBox, \
    QDateEdit, QComboBox, QCalendarWidget, QTableWidgetItem

from source.tools.constants import DEGREES
from source.tools.sqlHandler import SqlTableHandler as db
from source.tools.sqlBrewingComms import SQLNewBrew
from source.gui.boilMashMonitor import MonitorWindow as MashBoilMonitor

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
        self.maxDate = QDate()
        self.maxDate.currentDate()
        self.minDate = QDate(1,1,2018)
        self.dateEdit.setMinimumDate(self.minDate)
        self.dateEdit.setMaximumDate(self.maxDate)
        self.dateEdit.setCalendarPopup(1)
        
        # Recipe drop down box
        lab_recipe = QLabel("Recipe:")
        self.recipeEdit = QComboBox()
        self.recipeEdit.addItem("Recipe 1")
        self.recipeEdit.addItem("Recipe 2")
        self.recipeEdit.addItem("Recipe 3")

        filterHLayout = QHBoxLayout()
        filterHLayout.addStretch(1)
        filterHLayout.addWidget(lab_date)
        filterHLayout.addWidget(self.dateEdit)
        filterHLayout.addWidget(lab_recipe)
        filterHLayout.addWidget(self.recipeEdit)
        filterGroupBox.setLayout(filterHLayout)

        # Batch ID search
        self.lab_batchID = QLineEdit()
        self.lab_batchID.setPlaceholderText("Enter Batch ID")
        self.but_IDsearch = QPushButton("Go")

        scrollHLayout = QHBoxLayout()
        scrollHLayout.addWidget(filterGroupBox)
        scrollHLayout.addStretch(1)
        scrollHLayout.addWidget(self.lab_batchID)
        scrollHLayout.addWidget(self.but_IDsearch)
        scrollHLayout.addStretch(3)
        
        # Create QTableWidget of brew data
        self.dataTable = QTableWidget(10,3)
        columnNames = ["Batch ID", "Recipe", "Date"]
        self.dataTable.setHorizontalHeaderLabels(columnNames)
        for x in self.db.readFromTable("Brews", "id, Recipe, Date"):

            self.addTableData(x)

        # Create quit button
        self.but_quit = QPushButton("Quit")
        quitHLayout = QHBoxLayout()
        quitHLayout.addStretch(1)
        quitHLayout.addWidget(self.but_quit)

        # Main vertical layout
        vLayout = QVBoxLayout()
        vLayout.addLayout(scrollHLayout)
        vLayout.addWidget(self.dataTable)
        vLayout.addLayout(quitHLayout)

        self.setLayout(vLayout)

        self.but_quit.clicked.connect(self.quitButtonClicked)


    def quitButtonClicked(self):     
        
        self.close()


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

        
        