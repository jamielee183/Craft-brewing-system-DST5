#-*- coding: utf-8 -*-

import sys
import os

#from PySide2 import QtWidgets, QtCore, QtGui
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

from source.tools.sqlHandler import SqlDatabaseHandler

class NewUserWindow(QDialog):

    def __init__(self,LOGIN, parent=None):
        super(NewUserWindow, self).__init__(parent)
        self.create_layout_newUser()
        self.setWindowTitle('Create New User')
        self.setFixedSize(300, 200)
        self.db = SqlDatabaseHandler(LOGIN)

    def create_layout_newUser(self):

        newUserGroupBox = QGroupBox('Enter New User Log In Details:')
        newUserForm = QFormLayout()
        self.__new_usernameEdit = QLineEdit()
        self.__new_passwordEdit = QLineEdit()
        self.__new_passwordEdit.setEchoMode(QLineEdit.Password)
        self.__confirm_passwordEdit = QLineEdit()
        self.__confirm_passwordEdit.setEchoMode(QLineEdit.Password)
        self.__new_hostEdit = QLineEdit()
        newUserForm.addRow(QLabel(f'Host:'), self.__new_hostEdit)
        newUserForm.addRow(QLabel(f'Username:'), self.__new_usernameEdit)
        newUserForm.addRow(QLabel('Password:'), self.__new_passwordEdit)
        newUserForm.addRow(QLabel('Confirm Password:'), self.__confirm_passwordEdit)
        newUserGroupBox.setLayout(newUserForm)

        # H layout for buttons
        hLayoutButtons = QHBoxLayout()
        self.quitNewUserButton = QPushButton('Quit')
        self.createUserButton = QPushButton('Create User')
        hLayoutButtons.addWidget(self.quitNewUserButton)
        hLayoutButtons.addStretch(1)
        hLayoutButtons.addWidget(self.createUserButton)

        # Main V layout
        vLayoutnewUser = QVBoxLayout()
        vLayoutnewUser.addWidget(newUserGroupBox)
        vLayoutnewUser.addLayout(hLayoutButtons)
        self.setLayout(vLayoutnewUser)

        self.quitNewUserButton.clicked.connect(self.quitNewUserButtonClicked)
        self.createUserButton.clicked.connect(self.createUserButtonClicked)


    def quitNewUserButtonClicked(self):

        self.close()


    def createUserButtonClicked(self):

        # Error if any boxes are left blank
        if (self.__new_usernameEdit.text() == '') or (self.__new_passwordEdit.text() == '') or (self.__confirm_passwordEdit.text() == '') or (self.__new_hostEdit.text() == ''):

            newUserFail = QMessageBox()
            newUserFail.setIcon(QMessageBox.Critical)
            newUserFail.setText("Login Details Incomplete")
            newUserFail.setStandardButtons(QMessageBox.Ok)
            newUserFail.setWindowTitle("Warning")
            newUserFail.exec_()

        # Error if password and confirm password don't match
        elif (self.__new_passwordEdit.text() != self.__confirm_passwordEdit.text()):

            passwordFail = QMessageBox()
            passwordFail.setIcon(QMessageBox.Critical)
            passwordFail.setText("Password and Confirm Password do not match.")
            passwordFail.setStandardButtons(QMessageBox.Ok)
            passwordFail.setWindowTitle("Warning")
            passwordFail.exec_()

        # New user created successfully successful
        else:
            self.__loginDetails = [str(self.__new_hostEdit.text()), str(self.__new_usernameEdit.text()), str(self.__new_passwordEdit.text())]
            self.db.createUser(host=self.__loginDetails[0], user=self.__loginDetails[1], passwd=self.__loginDetails[2])

            userSuccess = QMessageBox()
            userSuccess.setIcon(QMessageBox.Information)
            userSuccess.setText("User successfully created.")
            userSuccess.setStandardButtons(QMessageBox.Ok)
            userSuccess.setWindowTitle("Success!")
            userSuccess.exec_()

            self.close()






