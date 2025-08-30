
# import numpy as np
import os
import csv
# import json
# from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from .dialogbase import DialogBase
from ..forms import ui_tuflowstability_check_dialog as tuflowstability_ui
from ..tools import help, globaltools
from ..tools import tuflowstabilitycheck as tmb_check
from ..tools import settings as mrt_settings

from ..mywidgets import graphdialogs as graphs

# DATA_DIR = './data'
# TEMP_DIR = './temp'


class TuflowStabilityCheckDialog(DialogBase, tuflowstability_ui.Ui_TuflowStabilityCheckDialog):
    """Load and display TUFLOW mass balance file contents.
    """

    def __init__(self, dialog_name, iface, project):
        DialogBase.__init__(self, dialog_name, iface, project, 'Check TUFLOW MB')

        self.summary_results = []
        self.file_results = None
        self.summary_mboptions = ['_MB']
        self.current_mb_filetype = ''
        self.individual_graphics_view = graphs.MbCheckIndividualGraphicsView()
        self.individual_graph_toolbar = NavigationToolbar(self.individual_graphics_view.canvas, self)
        self.summary_graphics_view = graphs.MbCheckMultipleGraphicsView()
        self.summary_graph_toolbar = NavigationToolbar(self.summary_graphics_view.canvas, self)
        
        self.hpc_file_results = None
        self.current_hpc_filetype = ''
        self.hpc_individual_graphics_view = graphs.HpcCheckIndividualGraphicsView()
        self.hpc_individual_graph_toolbar = NavigationToolbar(self.hpc_individual_graphics_view.canvas, self)

        mb_folder = mrt_settings.loadProjectSetting(
            'mb_folder', self.project.readPath('./temp')
        )
        mb_file = mrt_settings.loadProjectSetting(
            'mb_file', mb_folder
        )
        hpc_folder = mrt_settings.loadProjectSetting(
            'hpc_folder', self.project.readPath('./temp')
        )
        hpc_file = mrt_settings.loadProjectSetting(
            'hpc_file', hpc_folder
        )
        self.mbFolderWidget.setStorageMode(QgsFileWidget.GetDirectory)
        self.mbFolderWidget.setFilePath(os.path.dirname(mb_folder))
        self.mbFolderWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'mb_folder'))
        self.mbFileWidget.setFilePath(mb_file)
        self.mbFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'mb_file'))
        self.mbReloadSummaryBtn.clicked.connect(self.findMbFiles)
        self.mbSummaryResetGraphBtn.clicked.connect(self.resetSummaryGraph)
        self.mbReloadIndividualBtn.clicked.connect(self.loadMbFile)
        self.mbIndividualUpdateGraphBtn.clicked.connect(self.updateIndividualGraph)
        self.mbSummaryTable.cellChanged.connect(self.summaryCellChanged)
        self.mbSummaryTable.cellClicked.connect(self.summaryTableClicked)
        self.MBCheckbox.stateChanged.connect(self.summaryMbCheckChanged)
        self.MB2DCheckbox.stateChanged.connect(self.summaryMbCheckChanged)
        self.MB1DCheckbox.stateChanged.connect(self.summaryMbCheckChanged)
        self.mbAndDvolRadioBtn.clicked.connect(self.updateIndividualGraph)
        self.volumesRadioBtn.clicked.connect(self.updateIndividualGraph)
        self.massErrorsRadioBtn.clicked.connect(self.updateIndividualGraph)
        self.volumeErrorsRadioBtn.clicked.connect(self.updateIndividualGraph)
        self.mbShowDvolCheckbox.stateChanged.connect(self.graphMultipleResults)
        self.mbSummarySelectAllCheckbox.stateChanged.connect(self.summarySelectAll)
        
        self.hpcFileWidget.setFilePath(hpc_file)
        self.hpcFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'hpc_file'))
        self.hpcReloadButton.clicked.connect(self.loadHpcFile)
        self.hpcUpdateGraphBtn.clicked.connect(self.updateHpcGraph)
        self.hpcDtStarRadioBtn.clicked.connect(self.updateHpcGraph)
        self.hpcDtRadioBtn.clicked.connect(self.updateHpcGraph)
        self.hpcNcRadioBtn.clicked.connect(self.updateHpcGraph)
        self.hpcNuRadioBtn.clicked.connect(self.updateHpcGraph)
        self.hpcNdRadioBtn.clicked.connect(self.updateHpcGraph)
        self.hpcEffRadioBtn.clicked.connect(self.updateHpcGraph)

        self.mbSummaryTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mbSummaryTable.customContextMenuRequested.connect(self._showIndividualMbPlot)
        self.mbSummaryTable.setColumnWidth(0, 30)
        self.mbSummaryTable.setColumnWidth(1, 150)
        self.mbSummaryTable.setColumnWidth(2, 50)
        self.mbSummaryTable.setColumnWidth(3, 50)

        self.mbIndividualGraphLayout.addWidget(self.individual_graphics_view)
        self.mbIndividualGraphLayout.addWidget(self.individual_graph_toolbar)
        self.mbSummaryGraphLayout.addWidget(self.summary_graphics_view)
        self.mbSummaryGraphLayout.addWidget(self.summary_graph_toolbar)
        self.hpcGraphLayout.addWidget(self.hpc_individual_graphics_view)
        self.hpcGraphLayout.addWidget(self.hpc_individual_graph_toolbar)

    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        if caller == 'mb_folder':
            self.findMbFiles()
        elif caller == 'mb_file':
            self.loadMbFile()
        elif caller == 'hpc_file':
            self.loadHpcFile()

    @pyqtSlot(str)
    def _updateStatus(self, status):
        if len(status) > 120:
            status = status[:120] + ' ...'
        self.statusLabel.setText(status)
        QApplication.processEvents()

    def _showIndividualMbPlot(self, pos):
        """Handle summary table context menu.

        Adds context menu and deals with the associated actions.
        """
        index = self.mbSummaryTable.itemAt(pos)
        if index is None: return
        menu = QMenu()
        locate_section_action = menu.addAction("Show detailed graph")

        # Get the action and do whatever it says
        action = menu.exec_(self.mbSummaryTable.viewport().mapToGlobal(pos))
        if action == locate_section_action:
            row = self.mbSummaryTable.currentRow()
            col_count = self.mbSummaryTable.columnCount()
            full_path = self.mbSummaryTable.item(row, col_count-1).text()
            mrt_settings.saveProjectSetting('mb_file', full_path)
            self.mbTabWidget.setCurrentIndex(1)
            self.mbIndividualSeriesTabWidget.setCurrentIndex(0)
            QApplication.processEvents()
            self.mbFileWidget.setFilePath(full_path)
            self.loadMbFile()

    def summaryMbCheckChanged(self):
        """Update summary_mboptions based on checkbox settings."""

        self.summary_mboptions = []
        if self.MBCheckbox.isChecked():
            self.summary_mboptions.append('_MB')
        if self.MB2DCheckbox.isChecked():
            self.summary_mboptions.append('_MB2D')
        if self.MB1DCheckbox.isChecked():
            self.summary_mboptions.append('_MB1D')

    def findMbFiles(self):
        """Locate and load MB files for the summary graph and table.

        Search through all subfolders from the mb_folder down looking for 
        mass balance (MB/1D/2D) csv files. Load the CME and dVol time series
        and display them in the summary table and graph.
        """
        mb_path = mrt_settings.loadProjectSetting(
            'mb_folder', self.project.readPath('./temp')
        )
        self.summary_results = []
        self.mbSummaryTable.setRowCount(0)
        mb_check = tmb_check.TuflowStabilityCheck()
        mb_check.status_signal.connect(self._updateStatus)
        failed_load = []
        try:
            # self.statusLabel.setText('Searching for MB files under: {0}'.format(mb_path))
            self._updateStatus('Searching for MB files under: {0}'.format(mb_path))
            mb_files = mb_check.findMbFiles(mb_path, self.summary_mboptions)
            self.summary_results, failed_load = mb_check.loadMultipleFiles(mb_files)
        except:
            self.summary_results = []
            QMessageBox.warning(
                self, "MB files load error", 
                "Failed to load mass balance files"
            )
            return
        if self.summary_results:
            self.mbSummaryTable.blockSignals(True)
            self.updateSummaryTable()
            self.mbSummaryTable.blockSignals(False)
            self.graphMultipleResults()
            if failed_load['error'] or failed_load['empty']:
                dlg = graphs.LocalHelpDialog(title='MB file load errors')
                txt = ['Some MB files failed to load or contained no data:\n']
                txt += ['\n\nFailed to load:\n'] + failed_load['error']
                txt += ['\n\nNo data:\n'] + failed_load['empty']
                dlg.showText('\n'.join(txt), wrap_text=False)
                dlg.exec_()
        else:
            QMessageBox.warning(
                self, "MB files not found", 
                "No TUFLOW MB, MB1D, or MB2D file were found within subfolders."
            )

    def summaryCellChanged(self, row, col):
        """Update summary series draw status based on checkbox change."""

        if col != 0: return
        item = self.mbSummaryTable.item(row, col)
        check_state = item.checkState()
        if check_state == Qt.Checked:
            self.summary_results[row]['draw'] = True
        else:
            self.summary_results[row]['draw'] = False
        self.graphMultipleResults()

    def summaryTableClicked(self, row, col):
        """Update summary series highlight status based on table row click."""

        if col == 0: return
        for i, r in enumerate(self.summary_results):
            self.summary_results[i]['highlight'] = False
        self.summary_results[row]['highlight'] = True
        self.graphMultipleResults()

    def updateSummaryTable(self):
        """Update the contents of the summary table with mass balance series.

        Adds some key information about the series (fail status, max mb, name and path)
        along with a checkbox to change draw status.
        """
        row_position = 0
        self.mbSummaryTable.setRowCount(0)
        for i, r in enumerate(self.summary_results):
            self.summary_results[i]['draw'] = True
            self.summary_results[i]['highlight'] = False
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check_item.setCheckState(Qt.Checked)       

            self.mbSummaryTable.insertRow(row_position)
            self.mbSummaryTable.setItem(row_position, 0, check_item)
            self.mbSummaryTable.setItem(row_position, 1, QTableWidgetItem(r['name']))
            self.mbSummaryTable.setItem(row_position, 2, QTableWidgetItem(str(r['max_mb'])))
            self.mbSummaryTable.setItem(row_position, 3, QTableWidgetItem(str(r['fail'])))
            self.mbSummaryTable.setItem(row_position, 4, QTableWidgetItem(r['path']))
            row_position += 1

    def resetSummaryGraph(self):
        """Reset the loaded data to default setup in the table and the graph."""
        self.mbSummaryTable.blockSignals(True)
        self.mbSummarySelectAllCheckbox.blockSignals(True)
        self.mbShowDvolCheckbox.blockSignals(True)

        if self.summary_results:
            self.updateSummaryTable()
            self.graphMultipleResults()
        self.mbSummarySelectAllCheckbox.setChecked(False)

        self.mbSummaryTable.blockSignals(False)
        self.mbSummarySelectAllCheckbox.blockSignals(False)
        self.mbShowDvolCheckbox.blockSignals(False)

    def summarySelectAll(self, new_state):
        draw_status = True if new_state == Qt.Checked else False
        self.mbSummaryTable.blockSignals(True)
        for i, r in enumerate(self.summary_results):
            self.summary_results[i]['draw'] = draw_status
            self.mbSummaryTable.item(i, 0).setCheckState(new_state)
        self.mbSummaryTable.blockSignals(False)
        self.graphMultipleResults()

    def graphMultipleResults(self):
        """Plot summary mb series on the summary graph view.
        """
        if not self.summary_results:
            return

        try:
            self.summary_graphics_view.drawPlot(
                self.summary_results, self.mbShowDvolCheckbox.isChecked()
            )
        except:
            QMessageBox.warning(
                self, "Summary graph draw error", 
                '\n'.join([
                    "Failed to draw the summary graph.", 
                    "Something is probably wrong with the data formatting (it may be a bug)"
                ])
            )

    def loadMbFile(self):
        mb_path = mrt_settings.loadProjectSetting(
            'mb_file', self.project.readPath('./temp')
        )

        headers, self.current_mb_filetype, self.current_mb_filename = tmb_check.getMbHeaders(mb_path)
        mb_check = tmb_check.TuflowStabilityCheck()
        self._updateStatus('Loading file: {0}'.format(mb_path))
        try:
            self.file_results = mb_check.loadMbFile(mb_path, headers)
            self.updateIndividualGraph()
        except Exception as err:
            self._updateStatus('File load error: {0}'.format(mb_path))
            QMessageBox.warning(self, "MB file load error", err.args[0])
        self._updateStatus('Loaded file: {0}'.format(mb_path))

    def updateIndividualGraph(self):
        if self.file_results is None:
            QMessageBox.warning(
                self, "No MB File Loaded", 
                "Please load an MB File or select one from the summary table."
            )
            return

        series_type = ''
        if self.mbAndDvolRadioBtn.isChecked():
            series_type = 'mb_and_dvol'
        elif self.volumesRadioBtn.isChecked():
            series_type = 'volumes'
        elif self.massErrorsRadioBtn.isChecked():
            series_type = 'mass_errors'
        elif self.volumeErrorsRadioBtn.isChecked():
            series_type = 'volume_errors'

        graph_series = tmb_check.getIndividualMbSeriesPresets(
            series_type, self.current_mb_filetype
        )

        if graph_series:
            self.individual_graphics_view.drawPlot(
                graph_series, self.file_results, self.current_mb_filename
            )
            
    def loadHpcFile(self):
        hpc_path = mrt_settings.loadProjectSetting(
            'hpc_file', self.project.readPath('./temp')
        )

        self.current_hpc_filename = os.path.split(hpc_path)[1]
        self.hpc_check = tmb_check.TuflowHpcCheck()
        self._updateStatus('Loading file: {0}'.format(hpc_path))
        # try:
        self.hpc_check.loadHpcFile(hpc_path)
        self.updateHpcGraph()
        # except Exception as err:
        #     self._updateStatus('File load error: {0}'.format(mb_path))
        #     QMessageBox.warning(self, "MB file load error", err.args[0])
        self._updateStatus('Loaded file: {0}'.format(hpc_path))
    
    def updateHpcGraph(self):
        if self.hpc_check.series_data is None:
            QMessageBox.warning(
                self, "No HPC File Loaded", 
                "Please load an HPC File",
            )
            return

        series_type = 'dtstar'
        if self.hpcDtRadioBtn.isChecked():
            series_type = 'dt'
        elif self.hpcDtStarRadioBtn.isChecked():
            series_type = 'dtstar'
        elif self.hpcNcRadioBtn.isChecked():
            series_type = 'nc'
        elif self.hpcNuRadioBtn.isChecked():
            series_type = 'nu'
        elif self.hpcNdRadioBtn.isChecked():
            series_type = 'nd'
        elif self.hpcEffRadioBtn.isChecked():
            series_type = 'eff'
        
        series_meta = self.hpc_check.seriesColumn(series_type)

        if series_meta:
            self.hpc_individual_graphics_view.drawPlot(
                series_meta, self.hpc_check.series_data, self.current_hpc_filename
            )