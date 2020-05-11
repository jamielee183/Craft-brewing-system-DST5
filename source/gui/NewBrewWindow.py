#-*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))

#from PySide2 import QtWidgets
from PyQt5.QtCore import \
    Qt,pyqtSignal #, pyqtSlot
from PyQt5.QtGui import \
    QFont
from PyQt5.QtWidgets import \
    QApplication, QMainWindow, QWidget, \
    QSlider, QPushButton, QLabel, \
    QMessageBox, QDialog, QLineEdit, \
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QGroupBox

from source.tools.constants import DEGREES
from source.tools.sqlHandler import SqlTableHandler as db
from source.tools.sqlBrewingComms import SQLNewBrew
from source.gui.boilMashMonitor import MonitorWindow as MashBoilMonitor


class NewBrewWindow(QDialog):
    formSubmitted = pyqtSignal()

    def __init__(self, LOGIN, parent=None):
        super(NewBrewWindow, self).__init__(parent)
        self.LOGIN = LOGIN
        self.create_layout_newBrew()
        self.setWindowTitle('Start New Brew')

    # Function to create layout of New Brew window
    def create_layout_newBrew(self):
        lab_details = QLabel('Enter brew details in the form below:')


        nameGroupBox = QGroupBox('Recipe')
        nameForm = QFormLayout() 
        self.recipeNameEdit = QLineEdit()
        nameForm.addRow(QLabel('Recipe Name'), self.recipeNameEdit)
        nameGroupBox.setLayout(nameForm)

        # Mash group box
        mashGroupBox = QGroupBox('Mash')
        mashForm = QFormLayout()
        self.mashTempEdit = QLineEdit()
        self.mashTimeEdit = QLineEdit()
        mashForm.addRow(QLabel(f'Temperature ({DEGREES}C):'), self.mashTempEdit)
        mashForm.addRow(QLabel('Time (mins):'), self.mashTimeEdit)
        mashGroupBox.setLayout(mashForm)

        # Boil Group box
        boilGroupBox = QGroupBox('Boil')
        boilForm = QFormLayout()
        self.boilTempEdit = QLineEdit()
        self.boilTimeEdit = QLineEdit()
        boilForm.addRow(QLabel(f'Temperature ({DEGREES}C):'), self.boilTempEdit)
        boilForm.addRow(QLabel('Time (mins):'), self.boilTimeEdit)
       
        # Create 4 hop boxes using createHopBox function
        self.hopBoxes = [self.createHopBox(i,0) for i in range(4)]
        # Create hBoxes for hop boxes
        hopHLayout = QHBoxLayout()
        hopHLayout2 = QHBoxLayout()
        hopHLayout.addWidget(self.hopBoxes[0][0])
        hopHLayout.addWidget(self.hopBoxes[1][0])
        hopHLayout2.addWidget(self.hopBoxes[2][0])
        hopHLayout2.addWidget(self.hopBoxes[3][0])
        # Add hop boxes to boil form layout
        boilForm.addRow(hopHLayout)
        boilForm.addRow(hopHLayout2)
        # Set main layout of boil form
        boilGroupBox.setLayout(boilForm)

        # Fermentation group box
        fermentGroupBox = QGroupBox('Fermentation')
        fermentForm = QFormLayout()
        self.fermentTempEdit = QLineEdit()
        fermentForm.addRow(QLabel('Temperature:'), self.fermentTempEdit)
        fermentGroupBox.setLayout(fermentForm)

        # Buttons at bottom of page
        self.but_next = QPushButton('Start Brew')
        self.but_quit_brew = QPushButton('Quit')
        butHLayout = QHBoxLayout()
        butHLayout.addWidget(self.but_quit_brew)
        butHLayout.addStretch(1)
        butHLayout.addWidget(self.but_next)

        # Add each each layout to main vLayout
        vLayout = QVBoxLayout()
        vLayout.addWidget(lab_details)
        vLayout.addWidget(nameGroupBox)
        vLayout.addWidget(mashGroupBox)
        vLayout.addWidget(boilGroupBox)
        vLayout.addWidget(fermentGroupBox)
        vLayout.addLayout(butHLayout)
        self.setLayout(vLayout)

        # Connect signals and slots for pressing buttons
        self.but_next.clicked.connect(self.but_nextClicked)
        self.but_quit_brew.clicked.connect(self.brewquitClicked)

    #Function to create new hop box for form layout
    def createHopBox(self, hopNum, checkInit):
        hopBox = QGroupBox(f'Hop {hopNum}:')
        hopBox.setCheckable(1)
        hopBox.setChecked(checkInit)
        hopForm = QFormLayout()
        hopNameEdit = QLineEdit()
        hopTimeEdit = QLineEdit()
        hopForm.addRow(QLabel('Name:'), hopNameEdit)
        hopForm.addRow(QLabel('Boil Time (mins):'), hopTimeEdit)
        hopBox.setLayout(hopForm)

        return hopBox, hopNameEdit, hopTimeEdit

    
    # Function to check whether hop box is checked and deal with data accordingly
    # def checkHopBox(self, hopBoxes):

    #     for i in range(4):
    #         if (hopBoxes[i][0].isChecked() == False):
                
    #             hopBoxes[i][1].setText(None)
    #             hopBoxes[i][2].setText(None)

    #             hopBoxes[i][1] = None
    #             hopBoxes[i][2] = None
                
    #         else:
    #             int(hopBoxes[i][2].text(),10)

    def checkHopBox(self, hopBox):

        if (hopBox[0].isChecked() == False):

            # hopBox[1] = None
            # hopBox[2] = None
            return None, None
            
        else:
            return str(hopBox[1].text()), str(int(hopBox[2].text(),10))
    


    # Function run if Start Brew button is pressed
    def but_nextClicked(self):

        try:
            mashTemp = float(self.mashTempEdit.text())
            mashTime = int(self.mashTimeEdit.text(), 10)
            boilTemp = float(self.boilTempEdit.text())
            boilTemp = int(self.boilTimeEdit.text(), 10)
            fermTemp = float(self.fermentTempEdit.text())

            hop1 = self.checkHopBox(self.hopBoxes[0])
            hop2 = self.checkHopBox(self.hopBoxes[1])
            hop3 = self.checkHopBox(self.hopBoxes[2])
            hop4 = self.checkHopBox(self.hopBoxes[3])

            
            # self.checkHopBox(self.hopBoxes)


            # open next page (Jamie's 3 tab window)
            SQLNewBrew( LOGIN       =   self.LOGIN,
                        brewName    =   "{}".format(self.recipeNameEdit.text()), 
                        mashTime    =   "{}".format(mashTime),
                        mashTemp    =   "{}".format(mashTemp),
                        boilTime    =   "{}".format(boilTemp),
                        boilTemp    =   "{}".format(boilTemp),
                        fermentTemp =   "{}".format(fermTemp),
                        hop1        =    self.checkHopBox(self.hopBoxes[0]),
                        hop2        =    self.checkHopBox(self.hopBoxes[1]),
                        hop3        =    self.checkHopBox(self.hopBoxes[2]),
                        hop4        =    self.checkHopBox(self.hopBoxes[3]),
                        )

            # database = db(self.LOGIN,"Brewing")
            # batchID = database.maxIdFromTable("Brews")
            # self.mashBoilMonitor = MashBoilMonitor(LOGIN = self.LOGIN, batchID=batchID, parent=None)
            # self.mashBoilMonitor.show()
            self.formSubmitted.emit()
            self.close()


        # Show error message if wrong type is used in entry form
        except ValueError:
            formFail = QMessageBox()
            formFail.setIcon(QMessageBox.Warning)
            formFail.setText("Error: Unsuitable entry in form.")
            formFail.setStandardButtons(QMessageBox.Ok)
            formFail.setWindowTitle("Form Error")
            formFail.exec_()

    # Function run if Quit button is pressed
    def brewquitClicked(self):
        self.close()


