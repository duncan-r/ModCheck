# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './forms/ui_fmprefh_check_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_FmpRefhCheckDialog(object):
    def setupUi(self, FmpRefhCheckDialog):
        FmpRefhCheckDialog.setObjectName("FmpRefhCheckDialog")
        FmpRefhCheckDialog.resize(840, 552)
        self.verticalLayout = QtWidgets.QVBoxLayout(FmpRefhCheckDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(FmpRefhCheckDialog)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.fmpFileWidget = QgsFileWidget(FmpRefhCheckDialog)
        self.fmpFileWidget.setObjectName("fmpFileWidget")
        self.verticalLayout.addWidget(self.fmpFileWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.fmpFileReloadBtn = QtWidgets.QPushButton(FmpRefhCheckDialog)
        self.fmpFileReloadBtn.setObjectName("fmpFileReloadBtn")
        self.horizontalLayout.addWidget(self.fmpFileReloadBtn)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.refhOutputTextbox = QtWidgets.QPlainTextEdit(FmpRefhCheckDialog)
        self.refhOutputTextbox.setStyleSheet("font: 10pt \"Courier\";")
        self.refhOutputTextbox.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        self.refhOutputTextbox.setObjectName("refhOutputTextbox")
        self.verticalLayout.addWidget(self.refhOutputTextbox)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.csvExportBtn = QtWidgets.QPushButton(FmpRefhCheckDialog)
        self.csvExportBtn.setObjectName("csvExportBtn")
        self.horizontalLayout_2.addWidget(self.csvExportBtn)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.buttonBox = QtWidgets.QDialogButtonBox(FmpRefhCheckDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_2.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(FmpRefhCheckDialog)
        self.buttonBox.accepted.connect(FmpRefhCheckDialog.accept)
        self.buttonBox.rejected.connect(FmpRefhCheckDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(FmpRefhCheckDialog)

    def retranslateUi(self, FmpRefhCheckDialog):
        _translate = QtCore.QCoreApplication.translate
        FmpRefhCheckDialog.setWindowTitle(_translate("FmpRefhCheckDialog", "Audit ReFH Units"))
        self.label.setText(_translate("FmpRefhCheckDialog", "FMP .dat / .ied file"))
        self.fmpFileWidget.setFilter(_translate("FmpRefhCheckDialog", "*dat *.ied"))
        self.fmpFileReloadBtn.setText(_translate("FmpRefhCheckDialog", "Reload"))
        self.refhOutputTextbox.setPlaceholderText(_translate("FmpRefhCheckDialog", "Results output"))
        self.csvExportBtn.setText(_translate("FmpRefhCheckDialog", "Export to CSV"))

from qgsfilewidget import QgsFileWidget
