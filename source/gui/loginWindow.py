#-*- coding: utf-8 -*-

import sys
import os
#from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import \
    Qt #, pyqtSlot
from PyQt5.QtGui import \
    QFont
from PyQt5.QtWidgets import \
    QApplication, QMainWindow, QWidget, \
    QSlider, QPushButton, QLabel, \
    QMessageBox, QDialog, QLineEdit, \
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QGroupBox \

sys.path.append(os.path.join(os.path.join(os.getcwd(), os.pardir),os.pardir))
from source.gui.mainwindow import MainWindow
from source.tools.sqlHandler import SqlTableHandler, LoginError
from source.tools.constants import *
import mysql.connector as sql

class LoginWindow(QDialog):

    def __init__(self, parent=None):
        super(LoginWindow, self).__init__(parent)
        self.create_layout_login()
        self.setWindowTitle('Brew Monitoring System')
        self.setFixedSize(300, 200)

    def create_layout_login(self):

        # Form layout for entering login details
        loginGroupBox = QGroupBox('Enter Log In Details:')
        loginForm = QFormLayout()
        self.usernameEdit = QLineEdit()
        self.passwordEdit = QLineEdit()
        self.passwordEdit.setEchoMode(QLineEdit.Password)
        self.hostEdit = QLineEdit()
        loginForm.addRow(QLabel(f'Host:'), self.hostEdit)
        loginForm.addRow(QLabel(f'Username:'), self.usernameEdit)
        loginForm.addRow(QLabel('Password:'), self.passwordEdit)
        loginGroupBox.setLayout(loginForm)

        # H layout for buttons
        hLayoutButtons = QHBoxLayout()
        self.quitLoginButton = QPushButton('Quit')
        self.loginButton = QPushButton('Log In')
        hLayoutButtons.addWidget(self.quitLoginButton)
        hLayoutButtons.addStretch(1)
        hLayoutButtons.addWidget(self.loginButton)

        # Main V layout
        vLayoutLogin = QVBoxLayout()
        vLayoutLogin.addWidget(loginGroupBox)
        vLayoutLogin.addLayout(hLayoutButtons)
        self.setLayout(vLayoutLogin)

        self.quitLoginButton.clicked.connect(self.quitLoginButtonClicked)
        self.loginButton.clicked.connect(self.loginButtonClicked)


    def quitLoginButtonClicked(self):

        self.close()


    def loginButtonClicked(self):

        HOST = self.hostEdit.text()
        USER = self.usernameEdit.text()
        PASSWORD = self.passwordEdit.text()
        if HOST == "Pi":
            HOST = PI_IP
        LOGIN = [HOST, USER, PASSWORD]

        try:
            # SqlTableHandler(LOGIN=LOGIN, databaseName="Brewing")

            # self.close()
            self.window = MainWindow(LOGIN=LOGIN)
            self.close()
            self.window.show()
        
        except LoginError:
            loginFail = QMessageBox()
            loginFail.setIcon(QMessageBox.Critical)
            loginFail.setText("Login Failed")
            loginFail.setStandardButtons(QMessageBox.Ok)
            loginFail.setWindowTitle("Warning")
            loginFail.exec_()


        # # Successful log in, open main window
        # if (self.usernameEdit.text() == '') and (self.passwordEdit.text() == ''):
        #     db = sql.connect(
        #         host=LOGIN[0],
        #         user=LOGIN[1],
        #         passwd=LOGIN[2]
        #     )

        #     self.close()
        #     self.window = MainWindow(LOGIN=)
        #     self.window.show()

        # # Log in failed, show warning box
        # else:
        #     loginFail = QMessageBox()
        #     loginFail.setIcon(QMessageBox.Critical)
        #     loginFail.setText("Login Failed")
        #     loginFail.setStandardButtons(QMessageBox.Ok)
        #     loginFail.setWindowTitle("Warning")
        #     loginFail.exec_()

