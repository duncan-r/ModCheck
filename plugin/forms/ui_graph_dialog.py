# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './forms/ui_graph_dialog.ui'
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
        self.graphGraphicsView = QtWidgets.QGraphicsView(GraphDialog)
        self.graphGraphicsView.setObjectName("graphGraphicsView")
        self.verticalLayout.addWidget(self.graphGraphicsView)

        self.retranslateUi(GraphDialog)
        QtCore.QMetaObject.connectSlotsByName(GraphDialog)

    def retranslateUi(self, GraphDialog):
        _translate = QtCore.QCoreApplication.translate
        GraphDialog.setWindowTitle(_translate("GraphDialog", "Dialog"))

