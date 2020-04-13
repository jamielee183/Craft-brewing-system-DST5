# This Python file uses the following encoding: utf-8
import sys
import os
import traceback, types
import logging

#-*- coding: utf-8 -*-

#from PySide2 import QtWidgets
from PyQt5.QtCore import \
    Qt, QThread, pyqtSignal, pyqtSlot, QTimer, QThreadPool, QCoreApplication, QSize#, QMdiArea #, pyqtSlot
from PyQt5.QtGui import \
    QFont, QIcon, QPixmap
from PyQt5.QtWidgets import \
    QApplication, QMainWindow, QWidget, \
    QSlider, QPushButton, QLabel, \
    QMessageBox, QDialog, QLineEdit, \
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, \
    QGroupBox,QMdiArea, QMdiSubWindow, QScrollArea, QToolButton


# if running from command line, need to append the parent directories to the PATH
# so python knows where to find "source.file"
sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
import source.tools.exceptionLogging
from source.gui.boilMashMonitor import MonitorWindow as MashBoilMonitor
from source.gui.fermentMonitor import FermentMonitor
from source.tools.constants import *
from source.tools.sqlHandler import SqlTableHandler as db
from source.gui.NewBrewWindow import NewBrewWindow

from source.gui.newUserWindow import NewUserWindow
from source.gui.viewDataWindow import ViewDataWindow


class MainWindow(QMainWindow):

    _logname = 'MainWindow'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self,LOGIN, isRunningOnPi=False, parent = None):
        super(MainWindow, self).__init__()

        self.main_widget = QWidget()
        self.mdi = QMdiArea()
        self.setWindowTitle('Brew Monitoring System')
        
        bar = self.menuBar()
        filebar = bar.addMenu("File")
        filebar.addAction("New User")
        filebar.addAction("New Brew")
        filebar.triggered.connect(self.fileaction)

        viewbar = bar.addMenu("View")
        viewbar.addAction("Mash and Boil Vessels")
        viewbar.addAction("Fermentation Vessels")
        viewbar.addAction("Past Brew Data")
        viewbar.triggered.connect(self.viewaction)

        windowbar = bar.addMenu("Window")
        windowbar.addAction("Cascade")
        windowbar.addAction("Tiled")
        windowbar.triggered.connect(self.windowaction)

        systembar = bar.addMenu("System")
        systembar.addAction("Check For Faults")

        self.mainwindow = MdiMainWindow(LOGIN, isRunningOnPi=isRunningOnPi, parent = self)

        quitButton = QPushButton("Quit")
        quitButton.clicked.connect(lambda : self.close())

        quitLayout= QHBoxLayout()
        quitLayout.addStretch(10)
        quitLayout.addWidget(quitButton)

        layout = QVBoxLayout()
        layout.addWidget(self.mainwindow)
        layout.addWidget(self.mdi)
        layout.addLayout(quitLayout)
        self.main_widget.setLayout(layout)
        # self.main_widget.showFullScreen()

        self.setMinimumSize(700,700)
        self.resize(0,0)

        self.setCentralWidget(self.main_widget)
        # self.showFullScreen()

    
    def fileaction(self,selected):
        selected = selected.text()
        if selected == "New User":
            self.mainwindow.newUserClicked()
        elif selected == "New Brew":
            self.mainwindow.startBrewClicked()

    def windowaction(self,selected):
        selected = selected.text()
        if selected == "Cascade":
            self.mdi.cascadeSubWindows()
        elif selected == "Tiled":
            self.mdi.tileSubWindows()

    def viewaction(self,selected):
        selected = selected.text()
        if selected == "Fermentation Vessels":
            self.mainwindow.fermentButtonClicked()
        elif selected == "Mash and Boil Vessels":
            self.mainwindow.mashBoilButtonClicked()
        elif selected == "Past Brew Data":
            self.mainwindow.viewDataClicked()

class MdiMainWindow(QWidget):

    _logname = 'MainWindow'
    _log = logging.getLogger(f'{_logname}')

    def __init__(self,LOGIN, isRunningOnPi=False, parent = None):
        super(MdiMainWindow, self).__init__()
        self.LOGIN = LOGIN
        # self.main_widget = QWidget()
        self.create_layout()
        self.setWindowTitle("Brew Monitoring System")
        # self.setCentralWidget(self.main_widget)
        self.isRunningOnPi = isRunningOnPi
        self.parent = parent

        if self.isRunningOnPi:
            from source.tools.uCcoms import PiRadio
            from source.gui.irCameraWidget import IrCameraWidget
            self.radio = PiRadio(self.LOGIN)
            self.radio.configure()

    def create_layout(self):

        #self.font_title = QFont('Helvetica', 16)
        #self.font_title.setBold(True)
        #self.label_title = QLabel('Brew Monitoring System')
        #self.label_title.setFont(self.font_title)
        #self.but_start_brew = QPushButton(self.tr('Start New Brew'))
        #self.but_view_data = QPushButton(self.tr('View Past Brew Data'))
        #self.but_fermenters = QPushButton(self.tr('Fermentation tanks'))
        #self.but_mashBoil = QPushButton(self.tr('Monitor Mash and Boil'))
        icon_size = 25
        self.but_start_brew = QToolButton()
        self.but_start_brew.setToolTip("Start New Brew")
        self.but_start_brew.setIcon(QIcon(QPixmap("icons/new_brew.png")))
        self.but_start_brew.setIconSize(QSize(icon_size,icon_size))
        self.but_view_data = QToolButton()
        self.but_view_data.setToolTip("View Past Brew Data")
        self.but_view_data.setIcon(QIcon(QPixmap("icons/view_past_brew.png")))
        self.but_view_data.setIconSize(QSize(icon_size,icon_size))
        self.but_fermenters = QToolButton()
        self.but_fermenters.setToolTip("View Fermentation Vessels")
        self.but_fermenters.setIcon(QIcon(QPixmap("icons/view_fermenters.png")))
        self.but_fermenters.setIconSize(QSize(icon_size,icon_size))
        self.but_mashBoil = QToolButton()
        self.but_mashBoil.setToolTip("View Mash and Boil Vessels")
        self.but_mashBoil.setIcon(QIcon(QPixmap("icons/view_mashboil.png")))
        self.but_mashBoil.setIconSize(QSize(icon_size, icon_size))
        self.but_test = QPushButton(self.tr('Check System for Faults'))
        self.but_newUser = QPushButton()
        self.but_newUser.setToolTip("Create New User")
        self.but_newUser.setIcon(QIcon(QPixmap("icons/new_user_icon.png")))
        self.but_newUser.setIconSize(QSize(icon_size, icon_size))
        self.but_quit = QPushButton(self.tr('&Quit'))

        self.lab_start_brew = QLabel(self.tr('Start New Brew'))
        self.lab_view_data = QLabel(self.tr('View Past Brew Data'))
        self.lab_fermenters = QLabel(self.tr('Monitor Fermentation Vessels'))
        self.lab_test = QLabel(self.tr('Check System for Faults'))
        self.lab_newUser = QLabel(self.tr('Create New User'))
        self.lab_mashBoil = QLabel(self.tr('Monitor Mash and Boil Vessels'))

        #Grid for buttons and labels
        gLay_buttons = QHBoxLayout()
        
        gLay_buttons.addWidget(self.but_start_brew)
        # gLay_buttons.addWidget(self.lab_start_brew, 0, 1)
        gLay_buttons.addWidget(self.but_view_data)
        # gLay_buttons.addWidget(self.lab_view_data)
        gLay_buttons.addWidget(self.but_fermenters)
        # gLay_buttons.addWidget(self.lab_fermenters)
        gLay_buttons.addWidget(self.but_mashBoil)
        gLay_buttons.addWidget(self.but_newUser)
        # gLay_buttons.addWidget(self.lab_mashBoil)
        # gLay_buttons.addWidget(self.but_test)
        # gLay_buttons.addWidget(self.lab_test)
        # gLay_buttons.addWidget(self.but_newUser)
        # gLay_buttons.addWidget(self.lab_newUser)
        hLay_grid = QHBoxLayout()
        # hLay_grid.addStretch(1)
        hLay_grid.addLayout(gLay_buttons)
        hLay_grid.addStretch(1)

        #H Layout for title button
        #hLay_title = QHBoxLayout()
        # hLay_title.addStretch(1)
        #hLay_title.addWidget(self.label_title)
        #hLay_title.addStretch(1)

        #H Layout for quit button
        hLay_quit = QHBoxLayout()
        hLay_quit.addStretch(1)
        hLay_quit.addWidget(self.but_quit)

        #V layout for main layout
        vLay_main = QVBoxLayout()
        #vLay_main.addLayout(hLay_title)
        # vLay_main.addStretch(1)
        vLay_main.addLayout(hLay_grid)
        # vLay_main.addStretch(1)
        # vLay_main.addLayout(hLay_quit)
        # vLay_main.addStretch(0)
        self.setLayout(vLay_main)

        # connect new brew buttton with open brew window
        self.but_start_brew.clicked.connect(self.startBrewClicked)
        # connect new user buttton with open new user window
        self.but_newUser.clicked.connect(self.newUserClicked)
        # connect quit button with closing main window
        self.but_quit.clicked.connect(self.quitClicked)

        self.but_fermenters.clicked.connect(self.fermentButtonClicked)

        self.but_view_data.clicked.connect(self.viewDataClicked)

        # self.fermentMonitor = FermentMonitor(self.LOGIN)

        # database = db(LOGIN,"Brewing")
        # batchID = database.maxIdFromTable("Brews")
        # self.mashBoilMonitor = MashBoilMonitor(self.LOGIN, batchID)
        self.but_mashBoil.clicked.connect(self.mashBoilButtonClicked)


    def irCameraclick(self):

        if self.isRunningOnPi:
            irCamera = IrCameraWidget(radio=self.radio, parent=parent)
            irCamera.show()
        else:
            self._log.warning("Cannot open camera as application running in remote mode")

    def fermentButtonClicked(self):
        self.fermentMonitor = FermentMonitor(self.LOGIN)
#        self.fermentMonitor.startTimers()
        self.fermentMonitor.updateTankDropdown()
        # self.fermentMonitor.show()

        sub = QMdiSubWindow()
        sub.setWidget(self.fermentMonitor)
        self.parent.mdi.addSubWindow(sub)
        sub.show()
        self.fermentMonitor.closeSignal.connect(lambda: sub.close())



    def mashBoilButtonClicked(self):
        database = db(self.LOGIN,"Brewing")
        database.flushTables()
        batchID = database.maxIdFromTable("Brews")

        sub = QMdiSubWindow()
        if self.isRunningOnPi:
            ##Create instance of MashBoilMonitor
            mashBoilMonitor = MashBoilMonitor(self.LOGIN, batchID, radio=self.radio, parent=self)
        else:
            mashBoilMonitor = MashBoilMonitor(self.LOGIN, batchID, radio=None, parent=self)            
        # self.mashBoilMonitor.show()
        mashBoilMonitor.finishedSignal.connect(lambda: self.fermentMonitor.restartTankDropdown())

        
        sub.setWidget(mashBoilMonitor)
        self.parent.mdi.addSubWindow(sub)
        mashBoilMonitor.closeSignal.connect(lambda : sub.close())
        sub.show()
        

    def startBrewClicked(self):
        newBrewWindow = NewBrewWindow(LOGIN=self.LOGIN, parent=self)
        newBrewWindow.formSubmitted.connect(self.mashBoilButtonClicked)
        newBrewWindow.exec_()
        # newBrewWindow.show()


        # sub = QMdiSubWindow()
        # sub.setWidget(newBrewWindow)
        # self.parent.mdi.addSubWindow(sub)
        # newBrewWindow.closeSignal.connect(lambda : sub.close())
        # sub.show()
        # pass

    def viewDataClicked(self):
        viewDataWindow = ViewDataWindow(LOGIN=self.LOGIN, parent=self)
        #viewDataWindow.exec_()
        # viewDataWindow.show()
        # pass
        sub = QMdiSubWindow()
        sub.setWidget(viewDataWindow)
        self.parent.mdi.addSubWindow(sub)
        viewDataWindow.closeSignal.connect(lambda : sub.close())
        sub.show()

    def newUserClicked(self):
        newuserWindow = NewUserWindow(LOGIN=self.LOGIN, parent=self)
        newuserWindow.exec_()
        # newuserWindow.show()
        # pass
        # sub = QMdiSubWindow()
        # sub.setWidget(newuserWindow)
        # self.parent.mdi.addSubWindow(sub)
        # newuserWindow.closeSignal.connect(lambda : sub.close())
        # sub.show()

    def quitClicked(self):
        self.close()
        self.parent.close()


if __name__ == "__main__":

    from source.tools.sqlHandler import SqlTableHandler as db
    from source.gui.loginWindow import LoginWindow
    from getpass import getpass

    HOST = "192.168.10.223"
    USER = "jamie"
    PASSWORD = "beer"

    # HOST = "localhost"
    # USER = "Test"
    # PASSWORD = "BirraMosfeti"

    # HOST = input("Host ID: ")
    # USER = input("User: ")
    # PASSWORD = getpass()
    if HOST == "Pi":
        HOST = PI_IP

    LOGIN = [HOST,USER,PASSWORD]
    
    LOGIN = [HOST,USER,PASSWORD]

    


    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    # window = MainWindow(LOGIN, isRunningOnPi=False)
    # window.show()
    sys.exit(app.exec_())
