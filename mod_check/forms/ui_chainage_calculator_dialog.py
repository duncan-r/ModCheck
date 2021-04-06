# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './forms/ui_chainage_calculator_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ChainageCalculator(object):
    def setupUi(self, ChainageCalculator):
        ChainageCalculator.setObjectName("ChainageCalculator")
        ChainageCalculator.resize(665, 699)
        self.gridLayout = QtWidgets.QGridLayout(ChainageCalculator)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBox = QtWidgets.QGroupBox(ChainageCalculator)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.datFileWidget = QgsFileWidget(self.groupBox)
        self.datFileWidget.setObjectName("datFileWidget")
        self.verticalLayout.addWidget(self.datFileWidget)
        self.gridLayout.addWidget(self.groupBox, 2, 0, 1, 2)
        self.tuflowInputsGroupbox = QtWidgets.QGroupBox(ChainageCalculator)
        self.tuflowInputsGroupbox.setObjectName("tuflowInputsGroupbox")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tuflowInputsGroupbox)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.label_5 = QtWidgets.QLabel(self.tuflowInputsGroupbox)
        self.label_5.setObjectName("label_5")
        self.gridLayout_3.addWidget(self.label_5, 5, 5, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_3.addItem(spacerItem, 5, 4, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.tuflowInputsGroupbox)
        self.label_3.setObjectName("label_3")
        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 3)
        self.estryNwkLayerCBox = QgsMapLayerComboBox(self.tuflowInputsGroupbox)
        self.estryNwkLayerCBox.setObjectName("estryNwkLayerCBox")
        self.gridLayout_3.addWidget(self.estryNwkLayerCBox, 1, 0, 1, 7)
        self.dxToleranceSpinbox = QgsSpinBox(self.tuflowInputsGroupbox)
        self.dxToleranceSpinbox.setMaximum(50)
        self.dxToleranceSpinbox.setProperty("value", 10)
        self.dxToleranceSpinbox.setObjectName("dxToleranceSpinbox")
        self.gridLayout_3.addWidget(self.dxToleranceSpinbox, 5, 6, 1, 1)
        self.compareChainageBtn = QtWidgets.QPushButton(self.tuflowInputsGroupbox)
        self.compareChainageBtn.setObjectName("compareChainageBtn")
        self.gridLayout_3.addWidget(self.compareChainageBtn, 5, 0, 1, 1)
        self.gridLayout.addWidget(self.tuflowInputsGroupbox, 6, 0, 1, 2)
        self.groupBox_2 = QtWidgets.QGroupBox(ChainageCalculator)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.fmpOnlyCheckbox = QtWidgets.QCheckBox(self.groupBox_2)
        self.fmpOnlyCheckbox.setMaximumSize(QtCore.QSize(276, 16777215))
        self.fmpOnlyCheckbox.setObjectName("fmpOnlyCheckbox")
        self.verticalLayout_2.addWidget(self.fmpOnlyCheckbox)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.calcFmpChainageOnlyBtn = QtWidgets.QPushButton(self.groupBox_2)
        self.calcFmpChainageOnlyBtn.setEnabled(False)
        self.calcFmpChainageOnlyBtn.setObjectName("calcFmpChainageOnlyBtn")
        self.horizontalLayout.addWidget(self.calcFmpChainageOnlyBtn)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.gridLayout.addWidget(self.groupBox_2, 3, 0, 1, 2)
        self.buttonBox = QtWidgets.QDialogButtonBox(ChainageCalculator)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 9, 1, 1, 1)
        self.statusLabel = QtWidgets.QLabel(ChainageCalculator)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(5)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.statusLabel.sizePolicy().hasHeightForWidth())
        self.statusLabel.setSizePolicy(sizePolicy)
        self.statusLabel.setText("")
        self.statusLabel.setObjectName("statusLabel")
        self.gridLayout.addWidget(self.statusLabel, 9, 0, 1, 1)
        self.groupBox_4 = QtWidgets.QGroupBox(ChainageCalculator)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.outputsTabWidget = QtWidgets.QTabWidget(self.groupBox_4)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(2)
        sizePolicy.setHeightForWidth(self.outputsTabWidget.sizePolicy().hasHeightForWidth())
        self.outputsTabWidget.setSizePolicy(sizePolicy)
        self.outputsTabWidget.setObjectName("outputsTabWidget")
        self.fmpChainageTab = QtWidgets.QWidget()
        self.fmpChainageTab.setObjectName("fmpChainageTab")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.fmpChainageTab)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.fmpChainageTable = QtWidgets.QTableWidget(self.fmpChainageTab)
        self.fmpChainageTable.setObjectName("fmpChainageTable")
        self.fmpChainageTable.setColumnCount(6)
        self.fmpChainageTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.fmpChainageTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.fmpChainageTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.fmpChainageTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.fmpChainageTable.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.fmpChainageTable.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.fmpChainageTable.setHorizontalHeaderItem(5, item)
        self.fmpChainageTable.horizontalHeader().setStretchLastSection(True)
        self.horizontalLayout_2.addWidget(self.fmpChainageTable)
        self.fmpReachChainageTable = QtWidgets.QTableWidget(self.fmpChainageTab)
        self.fmpReachChainageTable.setObjectName("fmpReachChainageTable")
        self.fmpReachChainageTable.setColumnCount(5)
        self.fmpReachChainageTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.fmpReachChainageTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.fmpReachChainageTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.fmpReachChainageTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.fmpReachChainageTable.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.fmpReachChainageTable.setHorizontalHeaderItem(4, item)
        self.fmpReachChainageTable.horizontalHeader().setStretchLastSection(True)
        self.horizontalLayout_2.addWidget(self.fmpReachChainageTable)
        self.outputsTabWidget.addTab(self.fmpChainageTab, "")
        self.compareChainageTab = QtWidgets.QWidget()
        self.compareChainageTab.setObjectName("compareChainageTab")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.compareChainageTab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.tuflowFmpComparisonTable = QtWidgets.QTableWidget(self.compareChainageTab)
        self.tuflowFmpComparisonTable.setObjectName("tuflowFmpComparisonTable")
        self.tuflowFmpComparisonTable.setColumnCount(7)
        self.tuflowFmpComparisonTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tuflowFmpComparisonTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tuflowFmpComparisonTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tuflowFmpComparisonTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tuflowFmpComparisonTable.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tuflowFmpComparisonTable.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.tuflowFmpComparisonTable.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.tuflowFmpComparisonTable.setHorizontalHeaderItem(6, item)
        self.tuflowFmpComparisonTable.horizontalHeader().setCascadingSectionResizes(False)
        self.tuflowFmpComparisonTable.horizontalHeader().setDefaultSectionSize(150)
        self.tuflowFmpComparisonTable.horizontalHeader().setStretchLastSection(True)
        self.tuflowFmpComparisonTable.verticalHeader().setCascadingSectionResizes(False)
        self.verticalLayout_3.addWidget(self.tuflowFmpComparisonTable)
        self.outputsTabWidget.addTab(self.compareChainageTab, "")
        self.verticalLayout_4.addWidget(self.outputsTabWidget)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.exportResultsBtn = QtWidgets.QPushButton(self.groupBox_4)
        self.exportResultsBtn.setObjectName("exportResultsBtn")
        self.horizontalLayout_3.addWidget(self.exportResultsBtn)
        self.exportAllCheckbox = QtWidgets.QCheckBox(self.groupBox_4)
        self.exportAllCheckbox.setChecked(True)
        self.exportAllCheckbox.setTristate(False)
        self.exportAllCheckbox.setObjectName("exportAllCheckbox")
        self.horizontalLayout_3.addWidget(self.exportAllCheckbox)
        self.exportFmpCheckbox = QtWidgets.QCheckBox(self.groupBox_4)
        self.exportFmpCheckbox.setObjectName("exportFmpCheckbox")
        self.horizontalLayout_3.addWidget(self.exportFmpCheckbox)
        self.exportReachCheckbox = QtWidgets.QCheckBox(self.groupBox_4)
        self.exportReachCheckbox.setObjectName("exportReachCheckbox")
        self.horizontalLayout_3.addWidget(self.exportReachCheckbox)
        self.exportComparisonCheckbox = QtWidgets.QCheckBox(self.groupBox_4)
        self.exportComparisonCheckbox.setObjectName("exportComparisonCheckbox")
        self.horizontalLayout_3.addWidget(self.exportComparisonCheckbox)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.gridLayout.addWidget(self.groupBox_4, 8, 0, 1, 2)

        self.retranslateUi(ChainageCalculator)
        self.outputsTabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(ChainageCalculator.accept)
        self.buttonBox.rejected.connect(ChainageCalculator.reject)
        QtCore.QMetaObject.connectSlotsByName(ChainageCalculator)

    def retranslateUi(self, ChainageCalculator):
        _translate = QtCore.QCoreApplication.translate
        ChainageCalculator.setWindowTitle(_translate("ChainageCalculator", "FMP-TUFLOW Chainage Compare"))
        self.groupBox.setTitle(_translate("ChainageCalculator", "FMP Model"))
        self.label_2.setText(_translate("ChainageCalculator", "FMP .dat file"))
        self.datFileWidget.setDialogTitle(_translate("ChainageCalculator", "Load chainage results file ..."))
        self.datFileWidget.setFilter(_translate("ChainageCalculator", "*.dat"))
        self.tuflowInputsGroupbox.setTitle(_translate("ChainageCalculator", "TUFLOW inputs"))
        self.label_5.setText(_translate("ChainageCalculator", "DX Tolerance (m)"))
        self.label_3.setText(_translate("ChainageCalculator", "Nwk line layer"))
        self.dxToleranceSpinbox.setSuffix(_translate("ChainageCalculator", " m"))
        self.compareChainageBtn.setText(_translate("ChainageCalculator", "Compare TUFLOW / FMP Chainage"))
        self.groupBox_2.setTitle(_translate("ChainageCalculator", "FMP Only?"))
        self.fmpOnlyCheckbox.setText(_translate("ChainageCalculator", "Calculate FMP chainage only"))
        self.calcFmpChainageOnlyBtn.setText(_translate("ChainageCalculator", "Calculate FMP Chainage"))
        self.label_4.setText(_translate("ChainageCalculator", "Use this if there is no nwk line layer available for comparison and you just want to output node distances from the FMP model"))
        self.groupBox_4.setTitle(_translate("ChainageCalculator", "Outputs"))
        item = self.fmpChainageTable.horizontalHeaderItem(0)
        item.setText(_translate("ChainageCalculator", "Type"))
        item = self.fmpChainageTable.horizontalHeaderItem(1)
        item.setText(_translate("ChainageCalculator", "Name"))
        item = self.fmpChainageTable.horizontalHeaderItem(2)
        item.setText(_translate("ChainageCalculator", "Chainage"))
        item = self.fmpChainageTable.horizontalHeaderItem(3)
        item.setText(_translate("ChainageCalculator", "Cumulative Reach"))
        item = self.fmpChainageTable.horizontalHeaderItem(4)
        item.setText(_translate("ChainageCalculator", "Cumulative Total"))
        item = self.fmpChainageTable.horizontalHeaderItem(5)
        item.setText(_translate("ChainageCalculator", "Reach Number"))
        item = self.fmpReachChainageTable.horizontalHeaderItem(0)
        item.setText(_translate("ChainageCalculator", "Reach No."))
        item = self.fmpReachChainageTable.horizontalHeaderItem(1)
        item.setText(_translate("ChainageCalculator", "Start Name"))
        item = self.fmpReachChainageTable.horizontalHeaderItem(2)
        item.setText(_translate("ChainageCalculator", "End Name"))
        item = self.fmpReachChainageTable.horizontalHeaderItem(3)
        item.setText(_translate("ChainageCalculator", "No. of Sections"))
        item = self.fmpReachChainageTable.horizontalHeaderItem(4)
        item.setText(_translate("ChainageCalculator", "Reach Chainage"))
        self.outputsTabWidget.setTabText(self.outputsTabWidget.indexOf(self.fmpChainageTab), _translate("ChainageCalculator", "FMP Chainage"))
        item = self.tuflowFmpComparisonTable.horizontalHeaderItem(0)
        item.setText(_translate("ChainageCalculator", "Status"))
        item = self.tuflowFmpComparisonTable.horizontalHeaderItem(1)
        item.setText(_translate("ChainageCalculator", "Type"))
        item = self.tuflowFmpComparisonTable.horizontalHeaderItem(2)
        item.setText(_translate("ChainageCalculator", "Name"))
        item = self.tuflowFmpComparisonTable.horizontalHeaderItem(3)
        item.setText(_translate("ChainageCalculator", "Difference"))
        item = self.tuflowFmpComparisonTable.horizontalHeaderItem(4)
        item.setText(_translate("ChainageCalculator", "FMP Chainage"))
        item = self.tuflowFmpComparisonTable.horizontalHeaderItem(5)
        item.setText(_translate("ChainageCalculator", "Nwk Line Length"))
        item = self.tuflowFmpComparisonTable.horizontalHeaderItem(6)
        item.setText(_translate("ChainageCalculator", "Nwk Len_or_ANA"))
        self.outputsTabWidget.setTabText(self.outputsTabWidget.indexOf(self.compareChainageTab), _translate("ChainageCalculator", "TUFLOW-FMP Comparison"))
        self.exportResultsBtn.setText(_translate("ChainageCalculator", "Export Results"))
        self.exportAllCheckbox.setText(_translate("ChainageCalculator", "All"))
        self.exportFmpCheckbox.setText(_translate("ChainageCalculator", "FMP Chainage"))
        self.exportReachCheckbox.setText(_translate("ChainageCalculator", "Reach Chainage"))
        self.exportComparisonCheckbox.setText(_translate("ChainageCalculator", "Chainage Comparison"))

from qgsfilewidget import QgsFileWidget
from qgsmaplayercombobox import QgsMapLayerComboBox
from qgsspinbox import QgsSpinBox
