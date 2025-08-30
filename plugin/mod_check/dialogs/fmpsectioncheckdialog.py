
import numpy as np
import os
import csv
import json
from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget

from .dialogbase import DialogBase
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from ..forms import ui_fmpsectionproperty_check_dialog as fmpsectioncheck_ui
from ..tools import help, globaltools
from ..tools import fmpsectioncheck as fmpsection_check
from ..tools import settings as mrt_settings
from ..mywidgets import graphdialogs as graphs

# DATA_DIR = './data'
# TEMP_DIR = './temp'



class FmpSectionCheckDialog(DialogBase, fmpsectioncheck_ui.Ui_FmpSectionPropertyCheckDialog):


    def __init__(self, dialog_name, iface, project):
        DialogBase.__init__(self, dialog_name, iface, project, 'Check FMP Sections')

        # Loaded section property details
        self.properties = None
        self.graphics_view = graphs.SectionPropertiesGraphicsView()
        self.graph_toolbar = NavigationToolbar(self.graphics_view.canvas, self)


        # Load existing settings
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./temp')
        )
        k_tol = mrt_settings.loadProjectSetting('section_ktol', 10.0)
        dy_tol = mrt_settings.loadProjectSetting('section_dytol', 0.1)

        # Connect file widgets and update slots
        self.datFileReloadBtn.clicked.connect(self.loadSectionData)
        self.datFileWidget.setFilePath(dat_path)
        self.datFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'dat_file'))
        self.fmpNodesLayerCbox.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.kTolSpinbox.setValue(k_tol)
        self.bankDyToleranceSpinbox.setValue(dy_tol)
        self.kTolSpinbox.valueChanged.connect(self._kTolChange)
        self.bankDyToleranceSpinbox.valueChanged.connect(self._dyTolChange)
        self.negativeConveyanceTable.clicked.connect(self.conveyanceTableClicked)
        self.banktopCheckTable.clicked.connect(self.banktopTableClicked)
        self.graphLayout.addWidget(self.graphics_view)
        self.graphLayout.addWidget(self.graph_toolbar)
        self.splitter.setStretchFactor(0, 10)
        self.splitter.setStretchFactor(1, 10)

    def _kTolChange(self, value):
        mrt_settings.saveProjectSetting('section_ktol', value)

    def _dyTolChange(self, value):
        mrt_settings.saveProjectSetting('section_dytol', value)


    def banktopTableClicked(self, item):
        node_id = self.banktopCheckTable.item(item.row(), 0).text()
        self.graphSection(node_id, 'bad_banks')
        self.showSelectedNode(node_id)

    def conveyanceTableClicked(self, item):
        node_id = self.negativeConveyanceTable.item(item.row(), 0).text()
        self.graphSection(node_id, 'conveyance')
        self.showSelectedNode(node_id)

    def graphSection(self, node_id, caller):
        """
        """
        if caller == 'conveyance':
            self.graphics_view.drawConveyancePlot(
                self.properties['problems'][node_id],
                node_id
            )
        elif caller == 'bad_banks':
            self.graphics_view.drawBanktopsPlot(
                self.properties['problems'][node_id],
                node_id
            )

    def showSelectedNode(self, node_id):
        self.statusLabel.setText('')
        node_layer = self.fmpNodesLayerCbox.currentLayer()
        if not node_layer:
            self.statusLabel.setText('Cannot select node: no layer selected')
            return

        try:
            self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
            node_layer.removeSelection()
            found_node = False
            for f in node_layer.getFeatures():
                id = f[0]
                if id == node_id:
                    found_node = True
                    node_layer.select(f.id())
                    self.iface.mapCanvas().zoomToSelected(node_layer)
                    break

            if not found_node:
                self.statusLabel.setText(
                    'Cannot select node: node id ({0}) not in nodes layer'.format(node_id)
                )
        except:
            self.statusLabel.setText("Cannot select node: error reading nodes layer")

    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        if caller == 'dat_file':
            self.loadSectionData()

    def loadSectionData(self):
        self.properties = {}
        k_tol = self.kTolSpinbox.value()
        dy_tol = self.bankDyToleranceSpinbox.value()
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./temp')
        )
        section_check = fmpsection_check.CheckFmpSections()
        try:
            self.statusLabel.setText("Loading FMP model river sections ...")
            QApplication.processEvents()
            river_sections = section_check.loadRiverSections(dat_path)
            # self.properties['sections'] = river_sections

            self.statusLabel.setText("Calculating section properties...")
            QApplication.processEvents()
            problem_sections = section_check.findProblemSections(
                river_sections, k_tol=k_tol, dy_tol=dy_tol
            )
            self.properties['problems'] = problem_sections

        except Exception as err:
            self.statusLabel.setText("FMP model load failed!")
            QMessageBox.warning(
                self, "FMP dat file load error", err.args[0]
            )
        
        # Conveyance issues table
        self.statusLabel.setText("Populating tables ...")
        QApplication.processEvents()
        row_position = 0
        self.negativeConveyanceTable.setRowCount(row_position)
        for name, details in problem_sections.items():
            if details.active_k is None:
                continue

            max_kx = '{:.2f}'.format(details.max_kx)
            max_kx_depth = '{:.2f}'.format(details.max_kx_depth)
            self.negativeConveyanceTable.insertRow(row_position)
            self.negativeConveyanceTable.setItem(row_position, 0, QTableWidgetItem(name))
            self.negativeConveyanceTable.setItem(row_position, 1, QTableWidgetItem(max_kx))
            self.negativeConveyanceTable.setItem(row_position, 2, QTableWidgetItem(max_kx_depth))
            row_position += 1
        
        # Banktop issues table
        row_position = 0
        self.banktopCheckTable.setRowCount(row_position)
        for name, details in problem_sections.items():
            if details.bad_banks is None:
                continue

            left_drop = 'FAIL: {:.2f} m'.format(details.bad_banks['drop_left']) if details.bad_banks['drop_left'] > dy_tol else 'PASS'
            right_drop = 'FAIL: {:.2f} m'.format(details.bad_banks['drop_right']) if details.bad_banks['drop_right'] > dy_tol else 'PASS'
            self.banktopCheckTable.insertRow(row_position)
            self.banktopCheckTable.setItem(row_position, 0, QTableWidgetItem(name))
            self.banktopCheckTable.setItem(row_position, 1, QTableWidgetItem(left_drop))
            self.banktopCheckTable.setItem(row_position, 2, QTableWidgetItem(right_drop))
            row_position += 1

        self.statusLabel.setText("Section check complete")