# This Python file uses the following encoding: utf-8
import sys
import os
import logging

#-*- coding: utf-8 -*-

#from PySide2 import QtWidgets
from PyQt5.QtCore import \
    Qt, QThread, pyqtSignal, pyqtSlot #, pyqtSlot
from PyQt5.QtGui import \
    QFont
from PyQt5.QtWidgets import \
    QApplication, QMainWindow, QWidget, \
    QSlider, QPushButton, QLabel, \
    QMessageBox, QDialog, QLineEdit, \
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QGroupBox


# if running from command line, need to append the parent directories to the PATH
# so python knows where to find "source.file"
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
import source.tools.exceptionLogging
from source.gui.boilMashMonitor import MonitorWindow as MashBoilMonitor
from source.gui.fermentMonitor import FermentMonitor, FermentMonitorThread
from source.tools.constants import *
from source.tools.sqlHandler import SqlTableHandler as db

# import NewBrewWindow
# import loginWindow
# import newUserWindow

DEGREES = chr(176)

class MainWindow(QMainWindow):

    _logname = 'MainWindow'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self,LOGIN, parent = None):
        super(MainWindow, self).__init__()
        self.LOGIN = LOGIN
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
        self.but_quit = QPushButton(self.tr('&Quit'))
        self.but_mashBoil = QPushButton(self.tr('Go'))

        self.lab_start_brew = QLabel(self.tr('Start New Brew'))
        self.lab_history = QLabel(self.tr('View Brew History'))
        self.lab_fermenters = QLabel(self.tr('View Fermenter Data'))
        self.lab_test = QLabel(self.tr('Check System for Faults'))
        self.lab_newUser = QLabel(self.tr('Create New User'))
        self.lab_mashBoil = QLabel(self.tr('Mash/Boil monitor'))

        #Grid for buttons and labels
        gLay_buttons = QGridLayout()
        gLay_buttons.addWidget(self.but_start_brew, 0, 0)
        gLay_buttons.addWidget(self.lab_start_brew, 0, 1)
        gLay_buttons.addWidget(self.but_history)
        gLay_buttons.addWidget(self.lab_history)
        gLay_buttons.addWidget(self.but_fermenters)
        gLay_buttons.addWidget(self.lab_fermenters)
        gLay_buttons.addWidget(self.but_mashBoil)
        gLay_buttons.addWidget(self.lab_mashBoil)
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

        self.but_fermenters.clicked.connect(self.fermentButtonClicked)

        self.fermentThread = QThread()
        self.fermentMonitor = FermentMonitorThread(self.LOGIN)
        self.fermentMonitor.moveToThread(self.fermentThread)

        # self.fermentMonitor.moveToThread(self.fermentThread)
        # self.fermentMonitor.fermentMonitor.fermentClose.connect(self.fermentCloseSignal)
        # self.fermentThread.start()

        # database = db(LOGIN,"Brewing")
        # batchID = database.maxIdFromTable("Brews")
        # self.mashBoilMonitor = MashBoilMonitor(self.LOGIN, batchID)
        self.but_mashBoil.clicked.connect(self.mashBoilButtonClicked)


    # @pyqtSlot()
    def fermentCloseSignal(self):
        if self.fermentThread.isRunning():
            self.fermentThread.terminate()
            self.fermentThread.wait()
            self.fermentMonitor.fermentMonitor.close()
            self._log.info("Ferment Thread closed")
            # del self.fermentMonitor


    def forceFermentQuit(self):
        if self.fermentThread.isRunning():
            self.fermentThread.terminate()
            self.fermentThread.wait()


    def fermentButtonClicked(self):
        # self.fermentMonitor = FermentMonitor(self.LOGIN)
        # self.fermentMonitor = FermentMonitor(self.LOGIN)
        # self.fermentMonitor.show()
        # # self.fermentMonitor = FermentMonitorThread(self.LOGIN)
        # self.fermentMonitor.moveToThread(self.fermentThread)
        # v
        self.fermentThread.start()
        self.fermentMonitor.fermentMonitor.fermentClose.connect(self.fermentCloseSignal)
        self.fermentMonitor.fermentMonitor.show()


    def mashBoilButtonClicked(self):
        # self.fermentMonitor = FermentMonitor(self.LOGIN)
        database = db(self.LOGIN,"Brewing")
        batchID = database.maxIdFromTable("Brews")
        self.mashBoilMonitor = MashBoilMonitor(self.LOGIN, batchID)
        self.mashBoilMonitor.show()
        

    def startBrewClicked(self):
        # newBrewWindow = NewBrewWindow.NewBrewWindow()
        # newBrewWindow.exec_()

        pass

    def newUserClicked(self):
        # # newuserWindow = newUserWindow.NewUserWindow()
        # newuserWindow.exec_()
        pass

    def quitClicked(self):
        self.close()


if __name__ == "__main__":

    from source.tools.sqlHandler import SqlTableHandler as db

    HOST = "192.168.0.17"
    USER = "jamie"
    PASSWORD = "beer"
    LOGIN = [HOST,USER,PASSWORD]

    


    app = QApplication([])
    # login = loginWindow.LoginWindow()
    # login.show()
    window = MainWindow(LOGIN)
    window.show()
    sys.exit(app.exec_())
