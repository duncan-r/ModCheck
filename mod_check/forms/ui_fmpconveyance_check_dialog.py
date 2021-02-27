# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './forms/ui_fmpconveyance_check_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_FmpConveyanceCheckDialog(object):
    def setupUi(self, FmpConveyanceCheckDialog):
        FmpConveyanceCheckDialog.setObjectName("FmpConveyanceCheckDialog")
        FmpConveyanceCheckDialog.resize(525, 537)
        self.verticalLayout = QtWidgets.QVBoxLayout(FmpConveyanceCheckDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label = QtWidgets.QLabel(FmpConveyanceCheckDialog)
        self.label.setObjectName("label")
        self.horizontalLayout_4.addWidget(self.label)
        self.datFileWidget = QgsFileWidget(FmpConveyanceCheckDialog)
        self.datFileWidget.setObjectName("datFileWidget")
        self.horizontalLayout_4.addWidget(self.datFileWidget)
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.datFileReloadBtn = QtWidgets.QPushButton(FmpConveyanceCheckDialog)
        self.datFileReloadBtn.setObjectName("datFileReloadBtn")
        self.horizontalLayout.addWidget(self.datFileReloadBtn)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.poorConveyanceTable = QtWidgets.QTableWidget(FmpConveyanceCheckDialog)
        self.poorConveyanceTable.setObjectName("poorConveyanceTable")
        self.poorConveyanceTable.setColumnCount(3)
        self.poorConveyanceTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.poorConveyanceTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.poorConveyanceTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.poorConveyanceTable.setHorizontalHeaderItem(2, item)
        self.poorConveyanceTable.horizontalHeader().setDefaultSectionSize(150)
        self.poorConveyanceTable.horizontalHeader().setMinimumSectionSize(150)
        self.poorConveyanceTable.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout.addWidget(self.poorConveyanceTable)
        self.buttonBox = QtWidgets.QDialogButtonBox(FmpConveyanceCheckDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(FmpConveyanceCheckDialog)
        self.buttonBox.accepted.connect(FmpConveyanceCheckDialog.accept)
        self.buttonBox.rejected.connect(FmpConveyanceCheckDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(FmpConveyanceCheckDialog)

    def retranslateUi(self, FmpConveyanceCheckDialog):
        _translate = QtCore.QCoreApplication.translate
        FmpConveyanceCheckDialog.setWindowTitle(_translate("FmpConveyanceCheckDialog", "Check FMP Model Conveyance"))
        self.label.setText(_translate("FmpConveyanceCheckDialog", "FMP .dat File"))
        self.datFileWidget.setFilter(_translate("FmpConveyanceCheckDialog", "*.dat"))
        self.datFileReloadBtn.setText(_translate("FmpConveyanceCheckDialog", "Reload"))
        item = self.poorConveyanceTable.horizontalHeaderItem(0)
        item.setText(_translate("FmpConveyanceCheckDialog", "Node Name"))
        item = self.poorConveyanceTable.horizontalHeaderItem(1)
        item.setText(_translate("FmpConveyanceCheckDialog", "Negative K value"))
        item = self.poorConveyanceTable.horizontalHeaderItem(2)
        item.setText(_translate("FmpConveyanceCheckDialog", "Depth"))

from qgsfilewidget import QgsFileWidget
