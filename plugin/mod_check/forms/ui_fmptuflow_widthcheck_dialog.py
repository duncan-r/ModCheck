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
        FmpTuflowWidthCheckDialog.resize(573, 473)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(FmpTuflowWidthCheckDialog)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.groupBox = QtWidgets.QGroupBox(FmpTuflowWidthCheckDialog)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.workingDirFileWidget = QgsFileWidget(self.groupBox)
        self.workingDirFileWidget.setStorageMode(QgsFileWidget.GetDirectory)
        self.workingDirFileWidget.setObjectName("workingDirFileWidget")
        self.verticalLayout.addWidget(self.workingDirFileWidget)
        self.verticalLayout_3.addWidget(self.groupBox)
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
        self.fmpNodesLayerCbox = QgsMapLayerComboBox(self.groupBox_2)
        self.fmpNodesLayerCbox.setObjectName("fmpNodesLayerCbox")
        self.gridLayout.addWidget(self.fmpNodesLayerCbox, 3, 0, 1, 5)
        self.checkWidthsBtn = QtWidgets.QPushButton(self.groupBox_2)
        self.checkWidthsBtn.setObjectName("checkWidthsBtn")
        self.gridLayout.addWidget(self.checkWidthsBtn, 7, 0, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 3)
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 3)
        self.datFileWidget = QgsFileWidget(self.groupBox_2)
        self.datFileWidget.setObjectName("datFileWidget")
        self.gridLayout.addWidget(self.datFileWidget, 1, 0, 1, 4)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 7, 1, 1, 1)
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
        self.loggingTextedit = QtWidgets.QPlainTextEdit(self.groupBox_3)
        self.loggingTextedit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.loggingTextedit.setObjectName("loggingTextedit")
        self.verticalLayout_2.addWidget(self.loggingTextedit)
        self.verticalLayout_3.addWidget(self.groupBox_3)
        self.buttonBox = QtWidgets.QDialogButtonBox(FmpTuflowWidthCheckDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_3.addWidget(self.buttonBox)

        self.retranslateUi(FmpTuflowWidthCheckDialog)
        self.buttonBox.accepted.connect(FmpTuflowWidthCheckDialog.accept)
        self.buttonBox.rejected.connect(FmpTuflowWidthCheckDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(FmpTuflowWidthCheckDialog)

    def retranslateUi(self, FmpTuflowWidthCheckDialog):
        _translate = QtCore.QCoreApplication.translate
        FmpTuflowWidthCheckDialog.setWindowTitle(_translate("FmpTuflowWidthCheckDialog", "FMP-TUFLOW Section Width Compare"))
        self.groupBox.setTitle(_translate("FmpTuflowWidthCheckDialog", "Results folder"))
        self.label.setText(_translate("FmpTuflowWidthCheckDialog", "Set working directory"))
        self.workingDirFileWidget.setDialogTitle(_translate("FmpTuflowWidthCheckDialog", "Select Output Folder"))
        self.groupBox_2.setTitle(_translate("FmpTuflowWidthCheckDialog", "Inputs"))
        self.label_5.setText(_translate("FmpTuflowWidthCheckDialog", "DW Tolerance (m)"))
        self.label_3.setText(_translate("FmpTuflowWidthCheckDialog", "CN line layer"))
        self.checkWidthsBtn.setText(_translate("FmpTuflowWidthCheckDialog", "Check 1D-2D Widths"))
        self.label_4.setText(_translate("FmpTuflowWidthCheckDialog", "FMP nodes layer"))
        self.label_2.setText(_translate("FmpTuflowWidthCheckDialog", "FMP .dat file"))
        self.datFileWidget.setDialogTitle(_translate("FmpTuflowWidthCheckDialog", "Select FMP Model .dat File"))
        self.datFileWidget.setFilter(_translate("FmpTuflowWidthCheckDialog", "*.dat"))
        self.dwToleranceSpinbox.setSuffix(_translate("FmpTuflowWidthCheckDialog", " m"))
        self.groupBox_3.setTitle(_translate("FmpTuflowWidthCheckDialog", "Outputs"))

from qgsfilewidget import QgsFileWidget
from qgsmaplayercombobox import QgsMapLayerComboBox
from qgsspinbox import QgsSpinBox
