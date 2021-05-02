# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './forms/ui_file_check_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CheckFilesDialog(object):
    def setupUi(self, CheckFilesDialog):
        CheckFilesDialog.setObjectName("CheckFilesDialog")
        CheckFilesDialog.resize(861, 750)
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(CheckFilesDialog)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.modelFolderGroupbox = QtWidgets.QGroupBox(CheckFilesDialog)
        self.modelFolderGroupbox.setObjectName("modelFolderGroupbox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.modelFolderGroupbox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.modelFolderGroupbox)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.modelFolderFileWidget = QgsFileWidget(self.modelFolderGroupbox)
        self.modelFolderFileWidget.setObjectName("modelFolderFileWidget")
        self.verticalLayout.addWidget(self.modelFolderFileWidget)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.reloadBtn = QtWidgets.QPushButton(self.modelFolderGroupbox)
        self.reloadBtn.setObjectName("reloadBtn")
        self.horizontalLayout.addWidget(self.reloadBtn)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_6.addWidget(self.modelFolderGroupbox)
        self.outputsGroupbox = QtWidgets.QGroupBox(CheckFilesDialog)
        self.outputsGroupbox.setObjectName("outputsGroupbox")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.outputsGroupbox)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.resultsTabWidget = QtWidgets.QTabWidget(self.outputsGroupbox)
        self.resultsTabWidget.setObjectName("resultsTabWidget")
        self.searchSummaryTab = QtWidgets.QWidget()
        self.searchSummaryTab.setObjectName("searchSummaryTab")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.searchSummaryTab)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.summaryTextEdit = QtWidgets.QTextBrowser(self.searchSummaryTab)
        font = QtGui.QFont()
        font.setFamily("Courier")
        font.setPointSize(10)
        self.summaryTextEdit.setFont(font)
        self.summaryTextEdit.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.summaryTextEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.summaryTextEdit.setObjectName("summaryTextEdit")
        self.verticalLayout_4.addWidget(self.summaryTextEdit)
        self.resultsTabWidget.addTab(self.searchSummaryTab, "")
        self.missingFilesTab = QtWidgets.QWidget()
        self.missingFilesTab.setObjectName("missingFilesTab")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.missingFilesTab)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout()
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.label_6 = QtWidgets.QLabel(self.missingFilesTab)
        self.label_6.setObjectName("label_6")
        self.verticalLayout_10.addWidget(self.label_6)
        self.missingFilesTable = QtWidgets.QTableWidget(self.missingFilesTab)
        self.missingFilesTable.setObjectName("missingFilesTable")
        self.missingFilesTable.setColumnCount(2)
        self.missingFilesTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.missingFilesTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.missingFilesTable.setHorizontalHeaderItem(1, item)
        self.missingFilesTable.horizontalHeader().setMinimumSectionSize(250)
        self.missingFilesTable.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_10.addWidget(self.missingFilesTable)
        self.verticalLayout_2.addLayout(self.verticalLayout_10)
        self.verticalLayout_11 = QtWidgets.QVBoxLayout()
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.label_7 = QtWidgets.QLabel(self.missingFilesTab)
        self.label_7.setObjectName("label_7")
        self.verticalLayout_11.addWidget(self.label_7)
        self.missingParentList = QtWidgets.QListWidget(self.missingFilesTab)
        self.missingParentList.setObjectName("missingParentList")
        self.verticalLayout_11.addWidget(self.missingParentList)
        self.verticalLayout_2.addLayout(self.verticalLayout_11)
        self.verticalLayout_2.setStretch(0, 3)
        self.resultsTabWidget.addTab(self.missingFilesTab, "")
        self.foundElsewhereTab = QtWidgets.QWidget()
        self.foundElsewhereTab.setObjectName("foundElsewhereTab")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.foundElsewhereTab)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.label_4 = QtWidgets.QLabel(self.foundElsewhereTab)
        self.label_4.setObjectName("label_4")
        self.verticalLayout_8.addWidget(self.label_4)
        self.elsewhereFilesTable = QtWidgets.QTableWidget(self.foundElsewhereTab)
        self.elsewhereFilesTable.setObjectName("elsewhereFilesTable")
        self.elsewhereFilesTable.setColumnCount(3)
        self.elsewhereFilesTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.elsewhereFilesTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.elsewhereFilesTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.elsewhereFilesTable.setHorizontalHeaderItem(2, item)
        self.elsewhereFilesTable.horizontalHeader().setMinimumSectionSize(250)
        self.elsewhereFilesTable.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_8.addWidget(self.elsewhereFilesTable)
        self.verticalLayout_3.addLayout(self.verticalLayout_8)
        self.verticalLayout_9 = QtWidgets.QVBoxLayout()
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.label_5 = QtWidgets.QLabel(self.foundElsewhereTab)
        self.label_5.setObjectName("label_5")
        self.verticalLayout_9.addWidget(self.label_5)
        self.elsewhereParentList = QtWidgets.QListWidget(self.foundElsewhereTab)
        self.elsewhereParentList.setObjectName("elsewhereParentList")
        self.verticalLayout_9.addWidget(self.elsewhereParentList)
        self.verticalLayout_3.addLayout(self.verticalLayout_9)
        self.verticalLayout_3.setStretch(0, 3)
        self.resultsTabWidget.addTab(self.foundElsewhereTab, "")
        self.foundIefRefTab = QtWidgets.QWidget()
        self.foundIefRefTab.setObjectName("foundIefRefTab")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.foundIefRefTab)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout()
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.label_8 = QtWidgets.QLabel(self.foundIefRefTab)
        self.label_8.setObjectName("label_8")
        self.verticalLayout_12.addWidget(self.label_8)
        self.iefElsewhereFilesTable = QtWidgets.QTableWidget(self.foundIefRefTab)
        self.iefElsewhereFilesTable.setObjectName("iefElsewhereFilesTable")
        self.iefElsewhereFilesTable.setColumnCount(3)
        self.iefElsewhereFilesTable.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.iefElsewhereFilesTable.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.iefElsewhereFilesTable.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.iefElsewhereFilesTable.setHorizontalHeaderItem(2, item)
        self.iefElsewhereFilesTable.horizontalHeader().setMinimumSectionSize(250)
        self.iefElsewhereFilesTable.horizontalHeader().setStretchLastSection(True)
        self.verticalLayout_12.addWidget(self.iefElsewhereFilesTable)
        self.verticalLayout_7.addLayout(self.verticalLayout_12)
        self.verticalLayout_13 = QtWidgets.QVBoxLayout()
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.label_9 = QtWidgets.QLabel(self.foundIefRefTab)
        self.label_9.setObjectName("label_9")
        self.verticalLayout_13.addWidget(self.label_9)
        self.iefElsewhereParentList = QtWidgets.QListWidget(self.foundIefRefTab)
        self.iefElsewhereParentList.setObjectName("iefElsewhereParentList")
        self.verticalLayout_13.addWidget(self.iefElsewhereParentList)
        self.verticalLayout_7.addLayout(self.verticalLayout_13)
        self.verticalLayout_7.setStretch(0, 3)
        self.resultsTabWidget.addTab(self.foundIefRefTab, "")
        self.verticalLayout_5.addWidget(self.resultsTabWidget)
        self.verticalLayout_6.addWidget(self.outputsGroupbox)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.statusLabel = QtWidgets.QLabel(CheckFilesDialog)
        self.statusLabel.setText("")
        self.statusLabel.setObjectName("statusLabel")
        self.horizontalLayout_2.addWidget(self.statusLabel)
        self.buttonBox = QtWidgets.QDialogButtonBox(CheckFilesDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Close|QtWidgets.QDialogButtonBox.Help)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout_2.addWidget(self.buttonBox)
        self.verticalLayout_6.addLayout(self.horizontalLayout_2)

        self.retranslateUi(CheckFilesDialog)
        self.resultsTabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(CheckFilesDialog.accept)
        self.buttonBox.rejected.connect(CheckFilesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(CheckFilesDialog)

    def retranslateUi(self, CheckFilesDialog):
        _translate = QtCore.QCoreApplication.translate
        CheckFilesDialog.setWindowTitle(_translate("CheckFilesDialog", "File Check"))
        self.modelFolderGroupbox.setTitle(_translate("CheckFilesDialog", "Model location"))
        self.label.setText(_translate("CheckFilesDialog", "Model root folder"))
        self.reloadBtn.setText(_translate("CheckFilesDialog", "Reload"))
        self.outputsGroupbox.setTitle(_translate("CheckFilesDialog", "Outputs"))
        self.resultsTabWidget.setTabText(self.resultsTabWidget.indexOf(self.searchSummaryTab), _translate("CheckFilesDialog", "Search Summary"))
        self.label_6.setText(_translate("CheckFilesDialog", "Missing Files"))
        item = self.missingFilesTable.horizontalHeaderItem(0)
        item.setText(_translate("CheckFilesDialog", "File Name"))
        item = self.missingFilesTable.horizontalHeaderItem(1)
        item.setText(_translate("CheckFilesDialog", "Original Path"))
        self.label_7.setText(_translate("CheckFilesDialog", "Parent references"))
        self.resultsTabWidget.setTabText(self.resultsTabWidget.indexOf(self.missingFilesTab), _translate("CheckFilesDialog", "Missing"))
        self.label_4.setText(_translate("CheckFilesDialog", "Found Files (with incorrect paths)"))
        item = self.elsewhereFilesTable.horizontalHeaderItem(0)
        item.setText(_translate("CheckFilesDialog", "File Name"))
        item = self.elsewhereFilesTable.horizontalHeaderItem(1)
        item.setText(_translate("CheckFilesDialog", "Found At"))
        item = self.elsewhereFilesTable.horizontalHeaderItem(2)
        item.setText(_translate("CheckFilesDialog", "Original Path"))
        self.label_5.setText(_translate("CheckFilesDialog", "Parent references"))
        self.resultsTabWidget.setTabText(self.resultsTabWidget.indexOf(self.foundElsewhereTab), _translate("CheckFilesDialog", "Found Elsewhere"))
        self.label_8.setText(_translate("CheckFilesDialog", "Found Files referenced by .ief files (with incorrect paths)"))
        item = self.iefElsewhereFilesTable.horizontalHeaderItem(0)
        item.setText(_translate("CheckFilesDialog", "File Name"))
        item = self.iefElsewhereFilesTable.horizontalHeaderItem(1)
        item.setText(_translate("CheckFilesDialog", "Found At"))
        item = self.iefElsewhereFilesTable.horizontalHeaderItem(2)
        item.setText(_translate("CheckFilesDialog", "Original Path"))
        self.label_9.setText(_translate("CheckFilesDialog", "Parent references"))
        self.resultsTabWidget.setTabText(self.resultsTabWidget.indexOf(self.foundIefRefTab), _translate("CheckFilesDialog", "Ief References Found Elsewhere"))

from qgsfilewidget import QgsFileWidget
