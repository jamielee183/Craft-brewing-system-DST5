# This Python file uses the following encoding: utf-8
import sys
#-*- coding: utf-8 -*-

#from PySide2 import QtWidgets
from PySide2.QtCore import \
    Qt #, pyqtSlot
from PySide2.QtGui import \
    QFont
from PySide2.QtWidgets import \
    QApplication, QMainWindow, QWidget, \
    QSlider, QPushButton, QLabel, \
    QMessageBox, QDialog, QLineEdit, \
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QGroupBox
import NewBrewWindow
import loginWindow
import newUserWindow

DEGREES = chr(176)

class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__()
        self.main_widget = QWidget()
        self.create_layout()
        self.setWindowTitle('Brew Monitoring System')
        self.setCentralWidget(self.main_widget)

    def create_layout(self):

        self.font_title = QFont('Helvetica', 16)
        self.font_title.setBold(True)
        self.label_title = QLabel('Brew Monitoring System')
        self.label_title.setFont(self.font_title)
        self.but_start_brew = QPushButton(self.tr('Go'))
        self.but_history = QPushButton(self.tr('Go'))
        self.but_fermenters = QPushButton(self.tr('Go'))
        self.but_test = QPushButton(self.tr('Go'))
        self.but_newUser = QPushButton(self.tr('Go'))
        self.but_quit = QPushButton(self.tr('Quit'))
        self.lab_start_brew = QLabel(self.tr('Start New Brew'))
        self.lab_history = QLabel(self.tr('View Brew History'))
        self.lab_fermenters = QLabel(self.tr('View Fermenter Data'))
        self.lab_test = QLabel(self.tr('Check System for Faults'))
        self.lab_newUser = QLabel(self.tr('Create New User'))

        #Grid for buttons and labels
        gLay_buttons = QGridLayout()
        gLay_buttons.addWidget(self.but_start_brew, 0, 0)
        gLay_buttons.addWidget(self.lab_start_brew, 0, 1)
        gLay_buttons.addWidget(self.but_history)
        gLay_buttons.addWidget(self.lab_history)
        gLay_buttons.addWidget(self.but_fermenters)
        gLay_buttons.addWidget(self.lab_fermenters)
        gLay_buttons.addWidget(self.but_test)
        gLay_buttons.addWidget(self.lab_test)
        gLay_buttons.addWidget(self.but_newUser)
        gLay_buttons.addWidget(self.lab_newUser)
        hLay_grid = QHBoxLayout()
        hLay_grid.addStretch(1)
        hLay_grid.addLayout(gLay_buttons)
        hLay_grid.addStretch(1)

        #H Layout for title button
        hLay_title = QHBoxLayout()
        hLay_title.addStretch(1)
        hLay_title.addWidget(self.label_title)
        hLay_title.addStretch(1)

        #H Layout for quit button
        hLay_quit = QHBoxLayout()
        hLay_quit.addStretch(1)
        hLay_quit.addWidget(self.but_quit)

        #V layout for main layout
        vLay_main = QVBoxLayout()
        vLay_main.addLayout(hLay_title)
        vLay_main.addStretch(1)
        vLay_main.addLayout(hLay_grid)
        vLay_main.addStretch(1)
        vLay_main.addLayout(hLay_quit)
        vLay_main.addStretch(0)
        self.main_widget.setLayout(vLay_main)

        # connect new brew buttton with open brew window
        self.but_start_brew.clicked.connect(MainWindow.startBrewClicked)
        # connect new user buttton with open new user window
        self.but_newUser.clicked.connect(MainWindow.newUserClicked)
        # connect quit button with closing main window
        self.but_quit.clicked.connect(self.quitClicked)

    def startBrewClicked(self):
        newBrewWindow = NewBrewWindow.NewBrewWindow()
        newBrewWindow.exec_()

    def newUserClicked(self):
        newuserWindow = newUserWindow.NewUserWindow()
        newuserWindow.exec_()

    def quitClicked(self):
        self.close()


if __name__ == "__main__":
    app = QApplication([])
    login = loginWindow.LoginWindow()
    login.show()
    #window = MainWindow()
    #window.show()
    sys.exit(app.exec_())
