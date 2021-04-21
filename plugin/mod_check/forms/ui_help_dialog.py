# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './forms/ui_help_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_HelpDialog(object):
    def setupUi(self, HelpDialog):
        HelpDialog.setObjectName("HelpDialog")
        HelpDialog.resize(699, 668)
        self.verticalLayout = QtWidgets.QVBoxLayout(HelpDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.helpSelectList = QtWidgets.QListWidget(HelpDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(30)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.helpSelectList.sizePolicy().hasHeightForWidth())
        self.helpSelectList.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        self.helpSelectList.setFont(font)
        self.helpSelectList.setObjectName("helpSelectList")
        item = QtWidgets.QListWidgetItem()
        self.helpSelectList.addItem(item)
        self.horizontalLayout.addWidget(self.helpSelectList)
        self.helpDisplayTextBrowser = QtWidgets.QTextBrowser(HelpDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(70)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.helpDisplayTextBrowser.sizePolicy().hasHeightForWidth())
        self.helpDisplayTextBrowser.setSizePolicy(sizePolicy)
        self.helpDisplayTextBrowser.setObjectName("helpDisplayTextBrowser")
        self.horizontalLayout.addWidget(self.helpDisplayTextBrowser)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.buttonBox = QtWidgets.QDialogButtonBox(HelpDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(HelpDialog)
        self.buttonBox.accepted.connect(HelpDialog.accept)
        self.buttonBox.rejected.connect(HelpDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(HelpDialog)

    def retranslateUi(self, HelpDialog):
        _translate = QtCore.QCoreApplication.translate
        HelpDialog.setWindowTitle(_translate("HelpDialog", "ModCheck Help"))
        __sortingEnabled = self.helpSelectList.isSortingEnabled()
        self.helpSelectList.setSortingEnabled(False)
        item = self.helpSelectList.item(0)
        item.setText(_translate("HelpDialog", "Overview"))
        self.helpSelectList.setSortingEnabled(__sortingEnabled)

