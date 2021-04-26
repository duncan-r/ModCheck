# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './forms/ui_text_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_TextDialog(object):
    def setupUi(self, TextDialog):
        TextDialog.setObjectName("TextDialog")
        TextDialog.resize(737, 696)
        TextDialog.setWindowTitle("")
        self.verticalLayout = QtWidgets.QVBoxLayout(TextDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit = QtWidgets.QTextEdit(TextDialog)
        self.textEdit.setObjectName("textEdit")
        self.verticalLayout.addWidget(self.textEdit)

        self.retranslateUi(TextDialog)
        QtCore.QMetaObject.connectSlotsByName(TextDialog)

    def retranslateUi(self, TextDialog):
        pass

