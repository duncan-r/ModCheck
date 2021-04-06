# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './forms/ui_pyqtgraph_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_GraphDialog(object):
    def setupUi(self, GraphDialog):
        GraphDialog.setObjectName("GraphDialog")
        GraphDialog.resize(771, 692)
        self.verticalLayout = QtWidgets.QVBoxLayout(GraphDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.graphicsView = PlotWidget(GraphDialog)
        self.graphicsView.setObjectName("graphicsView")
        self.verticalLayout.addWidget(self.graphicsView)

        self.retranslateUi(GraphDialog)
        QtCore.QMetaObject.connectSlotsByName(GraphDialog)

    def retranslateUi(self, GraphDialog):
        _translate = QtCore.QCoreApplication.translate
        GraphDialog.setWindowTitle(_translate("GraphDialog", "Dialog"))

from pyqtgraph import PlotWidget
