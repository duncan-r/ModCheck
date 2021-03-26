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
        TuflowStabilityCheckDialog.resize(740, 642)
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
        self.mbGraphicsView = QtWidgets.QGraphicsView(TuflowStabilityCheckDialog)
        self.mbGraphicsView.setObjectName("mbGraphicsView")
        self.verticalLayout.addWidget(self.mbGraphicsView)
        self.buttonBox = QtWidgets.QDialogButtonBox(TuflowStabilityCheckDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(TuflowStabilityCheckDialog)
        self.buttonBox.accepted.connect(TuflowStabilityCheckDialog.accept)
        self.buttonBox.rejected.connect(TuflowStabilityCheckDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(TuflowStabilityCheckDialog)

    def retranslateUi(self, TuflowStabilityCheckDialog):
        _translate = QtCore.QCoreApplication.translate
        TuflowStabilityCheckDialog.setWindowTitle(_translate("TuflowStabilityCheckDialog", "TUFLOW Stability Viewer"))
        self.label.setText(_translate("TuflowStabilityCheckDialog", "TUFLOW MB file"))
        self.mbFileWidget.setFilter(_translate("TuflowStabilityCheckDialog", "*.csv"))
        self.mbReloadBtn.setText(_translate("TuflowStabilityCheckDialog", "Reload"))

from qgsfilewidget import QgsFileWidget
