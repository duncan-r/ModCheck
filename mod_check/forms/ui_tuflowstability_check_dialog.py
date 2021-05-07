# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './forms/ui_tuflowstability_check_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_TuflowStabilityCheckDialog(object):
    def setupUi(self, TuflowStabilityCheckDialog):
        TuflowStabilityCheckDialog.setObjectName("TuflowStabilityCheckDialog")
        TuflowStabilityCheckDialog.resize(1111, 661)
        self.verticalLayout = QtWidgets.QVBoxLayout(TuflowStabilityCheckDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(TuflowStabilityCheckDialog)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.mbFileWidget = QgsFileWidget(TuflowStabilityCheckDialog)
        self.mbFileWidget.setObjectName("mbFileWidget")
        self.horizontalLayout.addWidget(self.mbFileWidget)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.mbReloadBtn = QtWidgets.QPushButton(TuflowStabilityCheckDialog)
        self.mbReloadBtn.setObjectName("mbReloadBtn")
        self.horizontalLayout_2.addWidget(self.mbReloadBtn)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.mainTabWidget = QtWidgets.QTabWidget(TuflowStabilityCheckDialog)
        self.mainTabWidget.setObjectName("mainTabWidget")
        self.summaryTab = QtWidgets.QWidget()
        self.summaryTab.setObjectName("summaryTab")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.summaryTab)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.MBCheckbox = QtWidgets.QCheckBox(self.summaryTab)
        self.MBCheckbox.setChecked(True)
        self.MBCheckbox.setObjectName("MBCheckbox")
        self.horizontalLayout_4.addWidget(self.MBCheckbox)
        self.MB2DCheckbox = QtWidgets.QCheckBox(self.summaryTab)
        self.MB2DCheckbox.setObjectName("MB2DCheckbox")
        self.horizontalLayout_4.addWidget(self.MB2DCheckbox)
        self.MB1DCheckbox = QtWidgets.QCheckBox(self.summaryTab)
        self.MB1DCheckbox.setObjectName("MB1DCheckbox")
        self.horizontalLayout_4.addWidget(self.MB1DCheckbox)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.summaryTable = QtWidgets.QTableWidget(self.summaryTab)
        self.summaryTable.setObjectName("summaryTable")
        self.summaryTable.setColumnCount(5)
        self.summaryTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.summaryTable.setHorizontalHeaderItem(4, item)
        self.summaryTable.horizontalHeader().setCascadingSectionResizes(False)
        self.summaryTable.horizontalHeader().setDefaultSectionSize(200)
        self.summaryTable.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_2.addWidget(self.summaryTable)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.summaryGraphicsView = QtWidgets.QGraphicsView(self.summaryTab)
        self.summaryGraphicsView.setObjectName("summaryGraphicsView")
        self.horizontalLayout_3.addWidget(self.summaryGraphicsView)
        self.horizontalLayout_3.setStretch(0, 4)
        self.horizontalLayout_3.setStretch(1, 6)
        self.mainTabWidget.addTab(self.summaryTab, "")
        self.individualTab = QtWidgets.QWidget()
        self.individualTab.setObjectName("individualTab")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.individualTab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.mbGraphicsView = QtWidgets.QGraphicsView(self.individualTab)
        self.mbGraphicsView.setObjectName("mbGraphicsView")
        self.verticalLayout_3.addWidget(self.mbGraphicsView)
        self.mainTabWidget.addTab(self.individualTab, "")
        self.verticalLayout.addWidget(self.mainTabWidget)
        self.buttonBox = QtWidgets.QDialogButtonBox(TuflowStabilityCheckDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close|QtWidgets.QDialogButtonBox.Help)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(TuflowStabilityCheckDialog)
        self.mainTabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(TuflowStabilityCheckDialog.accept)
        self.buttonBox.rejected.connect(TuflowStabilityCheckDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(TuflowStabilityCheckDialog)

    def retranslateUi(self, TuflowStabilityCheckDialog):
        _translate = QtCore.QCoreApplication.translate
        TuflowStabilityCheckDialog.setWindowTitle(_translate("TuflowStabilityCheckDialog", "TUFLOW Stability Viewer"))
        self.label.setText(_translate("TuflowStabilityCheckDialog", "TUFLOW MB file"))
        self.mbFileWidget.setFilter(_translate("TuflowStabilityCheckDialog", "*.csv"))
        self.mbReloadBtn.setText(_translate("TuflowStabilityCheckDialog", "Reload"))
        self.MBCheckbox.setText(_translate("TuflowStabilityCheckDialog", "_MB"))
        self.MB2DCheckbox.setText(_translate("TuflowStabilityCheckDialog", "_MB2D"))
        self.MB1DCheckbox.setText(_translate("TuflowStabilityCheckDialog", "_MB1D"))
        item = self.summaryTable.horizontalHeaderItem(0)
        item.setText(_translate("TuflowStabilityCheckDialog", "Graph"))
        item = self.summaryTable.horizontalHeaderItem(1)
        item.setText(_translate("TuflowStabilityCheckDialog", "Failed"))
        item = self.summaryTable.horizontalHeaderItem(2)
        item.setText(_translate("TuflowStabilityCheckDialog", "Max"))
        item = self.summaryTable.horizontalHeaderItem(3)
        item.setText(_translate("TuflowStabilityCheckDialog", "Run Name"))
        item = self.summaryTable.horizontalHeaderItem(4)
        item.setText(_translate("TuflowStabilityCheckDialog", "Full Path"))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.summaryTab), _translate("TuflowStabilityCheckDialog", "Summary"))
        self.mainTabWidget.setTabText(self.mainTabWidget.indexOf(self.individualTab), _translate("TuflowStabilityCheckDialog", "Individual"))

from qgsfilewidget import QgsFileWidget
