# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './forms/ui_fmptuflow_widthcheck_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_FmpTuflowWidthCheckDialog(object):
    def setupUi(self, FmpTuflowWidthCheckDialog):
        FmpTuflowWidthCheckDialog.setObjectName("FmpTuflowWidthCheckDialog")
        FmpTuflowWidthCheckDialog.resize(937, 619)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(FmpTuflowWidthCheckDialog)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.groupBox_2 = QtWidgets.QGroupBox(FmpTuflowWidthCheckDialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName("gridLayout")
        self.label_5 = QtWidgets.QLabel(self.groupBox_2)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 6, 2, 1, 1)
        self.cnLinesLayerCbox = QgsMapLayerComboBox(self.groupBox_2)
        self.cnLinesLayerCbox.setObjectName("cnLinesLayerCbox")
        self.gridLayout.addWidget(self.cnLinesLayerCbox, 5, 0, 1, 5)
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 3)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 3)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 7, 1, 1, 1)
        self.datFileWidget = QgsFileWidget(self.groupBox_2)
        self.datFileWidget.setObjectName("datFileWidget")
        self.gridLayout.addWidget(self.datFileWidget, 1, 0, 1, 4)
        self.checkWidthsBtn = QtWidgets.QPushButton(self.groupBox_2)
        self.checkWidthsBtn.setObjectName("checkWidthsBtn")
        self.gridLayout.addWidget(self.checkWidthsBtn, 7, 0, 1, 1)
        self.fmpNodesLayerCbox = QgsMapLayerComboBox(self.groupBox_2)
        self.fmpNodesLayerCbox.setObjectName("fmpNodesLayerCbox")
        self.gridLayout.addWidget(self.fmpNodesLayerCbox, 3, 0, 1, 5)
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 3)
        self.dwToleranceSpinbox = QgsSpinBox(self.groupBox_2)
        self.dwToleranceSpinbox.setMaximum(20)
        self.dwToleranceSpinbox.setProperty("value", 5)
        self.dwToleranceSpinbox.setObjectName("dwToleranceSpinbox")
        self.gridLayout.addWidget(self.dwToleranceSpinbox, 7, 2, 1, 2)
        self.verticalLayout_3.addWidget(self.groupBox_2)
        self.groupBox_3 = QtWidgets.QGroupBox(FmpTuflowWidthCheckDialog)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.resultsTabWidget = QtWidgets.QTabWidget(self.groupBox_3)
        self.resultsTabWidget.setObjectName("resultsTabWidget")
        self.failTab = QtWidgets.QWidget()
        self.failTab.setObjectName("failTab")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.failTab)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.failedTableWidget = QtWidgets.QTableWidget(self.failTab)
        self.failedTableWidget.setObjectName("failedTableWidget")
        self.failedTableWidget.setColumnCount(6)
        self.failedTableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.failedTableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.failedTableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.failedTableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.failedTableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.failedTableWidget.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.failedTableWidget.setHorizontalHeaderItem(5, item)
        self.failedTableWidget.horizontalHeader().setDefaultSectionSize(150)
        self.failedTableWidget.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_4.addWidget(self.failedTableWidget)
        self.resultsTabWidget.addTab(self.failTab, "")
        self.allTab = QtWidgets.QWidget()
        self.allTab.setObjectName("allTab")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.allTab)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.allTableWidget = QtWidgets.QTableWidget(self.allTab)
        self.allTableWidget.setObjectName("allTableWidget")
        self.allTableWidget.setColumnCount(5)
        self.allTableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.allTableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.allTableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.allTableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.allTableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.allTableWidget.setHorizontalHeaderItem(4, item)
        self.allTableWidget.horizontalHeader().setDefaultSectionSize(150)
        self.allTableWidget.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_5.addWidget(self.allTableWidget)
        self.resultsTabWidget.addTab(self.allTab, "")
        self.verticalLayout_2.addWidget(self.resultsTabWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.exportResultsBtn = QtWidgets.QPushButton(self.groupBox_3)
        self.exportResultsBtn.setObjectName("exportResultsBtn")
        self.horizontalLayout.addWidget(self.exportResultsBtn)
        self.includeFailedCheckbox = QtWidgets.QCheckBox(self.groupBox_3)
        self.includeFailedCheckbox.setChecked(True)
        self.includeFailedCheckbox.setObjectName("includeFailedCheckbox")
        self.horizontalLayout.addWidget(self.includeFailedCheckbox)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.verticalLayout_3.addWidget(self.groupBox_3)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.statusLabel = QtWidgets.QLabel(FmpTuflowWidthCheckDialog)
        self.statusLabel.setObjectName("statusLabel")
        self.horizontalLayout_2.addWidget(self.statusLabel)
        self.buttonBox = QtWidgets.QDialogButtonBox(FmpTuflowWidthCheckDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close|QtWidgets.QDialogButtonBox.Help)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_2.addWidget(self.buttonBox)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.retranslateUi(FmpTuflowWidthCheckDialog)
        self.resultsTabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(FmpTuflowWidthCheckDialog.accept)
        self.buttonBox.rejected.connect(FmpTuflowWidthCheckDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(FmpTuflowWidthCheckDialog)

    def retranslateUi(self, FmpTuflowWidthCheckDialog):
        _translate = QtCore.QCoreApplication.translate
        FmpTuflowWidthCheckDialog.setWindowTitle(_translate("FmpTuflowWidthCheckDialog", "FMP-TUFLOW Section Width Compare"))
        self.groupBox_2.setTitle(_translate("FmpTuflowWidthCheckDialog", "Inputs"))
        self.label_5.setText(_translate("FmpTuflowWidthCheckDialog", "DW Tolerance (m)"))
        self.label_3.setText(_translate("FmpTuflowWidthCheckDialog", "CN line layer"))
        self.label_4.setText(_translate("FmpTuflowWidthCheckDialog", "FMP nodes layer"))
        self.datFileWidget.setDialogTitle(_translate("FmpTuflowWidthCheckDialog", "Select FMP Model .dat File"))
        self.datFileWidget.setFilter(_translate("FmpTuflowWidthCheckDialog", "*.dat"))
        self.checkWidthsBtn.setText(_translate("FmpTuflowWidthCheckDialog", "Check 1D-2D Widths"))
        self.label_2.setText(_translate("FmpTuflowWidthCheckDialog", "FMP .dat file"))
        self.dwToleranceSpinbox.setSuffix(_translate("FmpTuflowWidthCheckDialog", " m"))
        self.groupBox_3.setTitle(_translate("FmpTuflowWidthCheckDialog", "Outputs"))
        item = self.failedTableWidget.horizontalHeaderItem(0)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "Failure"))
        item = self.failedTableWidget.horizontalHeaderItem(1)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "ID"))
        item = self.failedTableWidget.horizontalHeaderItem(2)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "Unit Type"))
        item = self.failedTableWidget.horizontalHeaderItem(3)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "Difference"))
        item = self.failedTableWidget.horizontalHeaderItem(4)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "1D Width"))
        item = self.failedTableWidget.horizontalHeaderItem(5)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "2D Width"))
        self.resultsTabWidget.setTabText(self.resultsTabWidget.indexOf(self.failTab), _translate("FmpTuflowWidthCheckDialog", "Failed"))
        item = self.allTableWidget.horizontalHeaderItem(0)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "ID"))
        item = self.allTableWidget.horizontalHeaderItem(1)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "Unit Type"))
        item = self.allTableWidget.horizontalHeaderItem(2)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "Difference"))
        item = self.allTableWidget.horizontalHeaderItem(3)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "1D Width"))
        item = self.allTableWidget.horizontalHeaderItem(4)
        item.setText(_translate("FmpTuflowWidthCheckDialog", "2D Width"))
        self.resultsTabWidget.setTabText(self.resultsTabWidget.indexOf(self.allTab), _translate("FmpTuflowWidthCheckDialog", "All"))
        self.exportResultsBtn.setText(_translate("FmpTuflowWidthCheckDialog", "Export Results"))
        self.includeFailedCheckbox.setText(_translate("FmpTuflowWidthCheckDialog", "Create Failed nodes file?"))
        self.statusLabel.setText(_translate("FmpTuflowWidthCheckDialog", "TextLabel"))

from qgsfilewidget import QgsFileWidget
from qgsmaplayercombobox import QgsMapLayerComboBox
from qgsspinbox import QgsSpinBox
