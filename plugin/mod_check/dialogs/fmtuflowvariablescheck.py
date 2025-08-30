
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
from ..forms import ui_runvariables_check_dialog as fmptuflowvariablescheck_ui
from ..tools import help, globaltools
from ..tools import runvariablescheck as runvariables_check
from ..tools import settings as mrt_settings
from PyQt5.pyrcc_main import showHelp

# DATA_DIR = './data'
# TEMP_DIR = './temp'



class FmpTuflowVariablesCheckDialog(DialogBase, fmptuflowvariablescheck_ui.Ui_FmpTuflowVariablesCheckDialog):

    def __init__(self, dialog_name, iface, project):

        DialogBase.__init__(self, dialog_name, iface, project, 'Run Variables Summary')

        tlf_path = mrt_settings.loadProjectSetting(
            'tlf_file', self.project.readPath('./temp')
        )
        ief_path = mrt_settings.loadProjectSetting(
            'ief_file', self.project.readPath('./temp')
        )
        zzd_path = mrt_settings.loadProjectSetting(
            'zzd_file', self.project.readPath('./temp')
        )
        ief_folder = mrt_settings.loadProjectSetting(
            'ief_folder', self.project.readPath('./temp')
        )

        self.fmpIefFolderFileWidget.setStorageMode(QgsFileWidget.GetDirectory)
        self.tuflowFolderFileWidget.setStorageMode(QgsFileWidget.GetDirectory)

        # Connect the slots
        self.iefTableRefreshBtn.clicked.connect(self.loadIefVariables)
        self.zzdTableRefreshBtn.clicked.connect(self.loadZzdResults)
        self.tlfTableRefreshBtn.clicked.connect(self.loadTlfDetails)
        self.exportFmpSummaryBtn.clicked.connect(self.exportFmpSummary)
        self.exportTuflowSummaryBtn.clicked.connect(self.exportTuflowSummary)
        self.iefFileWidget.setFilePath(ief_path)
        self.zzdFileWidget.setFilePath(zzd_path)
        self.tlfFileWidget.setFilePath(tlf_path)
        self.iefFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'ief_file'))
        self.zzdFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'zzd_file'))
        self.tlfFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'tlf_file'))
        self.fmpIefFolderFileWidget.fileChanged.connect(self.loadMultipleIefSummary)
        self.tuflowFolderFileWidget.fileChanged.connect(self.loadMultipleTsfSummary)
        self.fmpMultipleSummaryTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.fmpMultipleSummaryTable.customContextMenuRequested.connect(self._multipleIefTableContext)
        self.tuflowMultipleSummaryTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tuflowMultipleSummaryTable.customContextMenuRequested.connect(self._multipleTsfTableContext)

    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)

        if caller == 'ief_file':
            self.loadIefVariables()
        elif caller == 'zzd_file':
            self.loadZzdResults()
        elif caller == 'tlf_file':
            self.loadTlfDetails()

    def _multipleIefTableContext(self, pos):
        """Add context menu to failed sections table.

        Allow user to select and zoom to the chosen section in the map window.
        """
        index = self.fmpMultipleSummaryTable.itemAt(pos)
        if index is None: return
        menu = QMenu()
        locate_section_action = menu.addAction("Show detailed view")

        # Get the action and do whatever it says
        action = menu.exec_(self.fmpMultipleSummaryTable.viewport().mapToGlobal(pos))
        if action == locate_section_action:
            row = self.fmpMultipleSummaryTable.currentRow()
            col_count = self.fmpMultipleSummaryTable.columnCount()
            full_path = self.fmpMultipleSummaryTable.item(row, col_count-1).text()
            mrt_settings.saveProjectSetting('ief_path', full_path)
            self.fmpTabWidget.setCurrentIndex(1)
            self.iefFileWidget.setFilePath(full_path)

    def _multipleTsfTableContext(self, pos):
        """Add context menu to failed sections table.

        Allow user to select and zoom to the chosen section in the map window.
        """
        index = self.tuflowMultipleSummaryTable.itemAt(pos)
        if index is None: return
        menu = QMenu()
        locate_section_action = menu.addAction("Show detailed view")

        # Get the action and do whatever it says
        action = menu.exec_(self.tuflowMultipleSummaryTable.viewport().mapToGlobal(pos))
        if action == locate_section_action:
            row = self.tuflowMultipleSummaryTable.currentRow()
            col_count = self.tuflowMultipleSummaryTable.columnCount()
            full_path = self.tuflowMultipleSummaryTable.item(row, col_count-1).text()
            mrt_settings.saveProjectSetting('tlf_path', full_path)
            self.tuflowMainTabWidget.setCurrentIndex(1)
            self.tuflowTabWidget.setCurrentIndex(0)
            QApplication.processEvents()
            self.tlfFileWidget.setFilePath(full_path)

    def exportFmpSummary(self):
        self.exportSummary(self.fmpMultipleSummaryTable, 'ief_summary')

    def exportTuflowSummary(self):
        self.exportSummary(self.tuflowMultipleSummaryTable, 'tsf_summary')

    def exportSummary(self, table, save_name):
        """Export contents of the ief/tsf summary tables.

        Args:
            table(QTableWidget): the table to export the data from.
            save_name(str): the default save file name.
        """
        csv_file = mrt_settings.loadProjectSetting('csv_file', './temp')
        default_path = os.path.split(csv_file)[0]
        default_path = os.path.join(default_path, save_name + '.csv')
        filepath = QFileDialog(self).getSaveFileName(
            self, 'Export Results', default_path, "CSV File (*.csv)"
        )
        if not filepath[0]:
            return
        mrt_settings.saveProjectSetting('csv_file', filepath[0])

        cur_row = 0
        cur_col = 0
        row_count = table.rowCount()
        col_count = table.columnCount()

        output = []
        headers = []
        while cur_col < col_count:
            headers.append(table.horizontalHeaderItem(cur_col).text())
            cur_col += 1

        while cur_row < row_count:
            cur_col = 0
            line = []
            while cur_col < col_count:
                line.append(table.item(cur_row, cur_col).text())
                cur_col += 1
            output.append(line)
            cur_row += 1

        try:
            runvariables_check.exportTableSummary(filepath[0], headers, output)
        except OSError as err:
            QMessageBox.warning(
                self, "Results export failed", err.args[0] 
            )

    def loadMultipleIefSummary(self, path):
        mrt_settings.saveProjectSetting('ief_folder', path)

        failed_load = []
        has_error = False
        try:
            ief_files = []
            for root, dirs, files in os.walk(path):
                for file in files:
                    fext = os.path.splitext(file)
                    if len(fext) > 1 and fext[1] == '.ief':
                        ief_files.append(os.path.join(root, file))

            check = runvariables_check.IefVariablesCheck(self.project, 'fakepath')
            outputs = []
            for ief in ief_files:
                try:
                    # result = check.loadSummaryInfo(ief)
                    outputs.append(check.loadSummaryInfo(ief))
                except Exception as err:
                    has_error = True
                    failed_load.append(ief)

            row_position = 0
            self.fmpMultipleSummaryTable.setRowCount(row_position)
            for output in outputs:
                self.fmpMultipleSummaryTable.insertRow(row_position)
                for i, value in enumerate(output):
                    if value[1] == True:
                        item = QTableWidgetItem()
                        item.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                        item.setBackground(QColor(239, 175, 175)) # Light Red
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                        item.setText(str(value[0]))
                        self.fmpMultipleSummaryTable.setItem(row_position, i, item)
                    else:
                        self.fmpMultipleSummaryTable.setItem(row_position, i, QTableWidgetItem(str(value[0])))
                row_position += 1
        except Exception as err:
            has_error = True

        if has_error:
            if failed_load:
                msg = 'Failed to load some .ief files\n'
                msg += '\n'.join(failed_load)
            else:
                msg = 'Unable to read .ief file folders'
            QMessageBox.warning(
                self, "IEF file read fail", msg
            )

    def loadMultipleTsfSummary(self, path):
        mrt_settings.saveProjectSetting('runs_folder', path)

        tsf_check = runvariables_check.TsfSummaryCheck(self.project)
        tsf_files = tsf_check.findTsfFiles(path)
        output, key_order = tsf_check.loadTsfData(tsf_files)

        row_position = 0
        self.tuflowMultipleSummaryTable.setRowCount(row_position)
        for row in output:
            self.tuflowMultipleSummaryTable.insertRow(row_position)
            for i, item in enumerate(key_order):
                try:
                    self.tuflowMultipleSummaryTable.setItem(
                        row_position, i, QTableWidgetItem(str(output[row_position][item]))
                    )
                except KeyError:
                    self.tuflowMultipleSummaryTable.setItem(
                        row_position, i, QTableWidgetItem("Not Found")
                    )
            row_position += 1
        pass

    def loadIefVariables(self):

        def outputTableRow(details, is_default):
            item = None
            if is_default:
                item = QTableWidgetItem('Yes')
            else:
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                item.setBackground(QColor(239, 175, 175)) # Light Red
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item.setText('No')

            self.fmpVariablesTable.insertRow(row_position)
            self.fmpVariablesTable.setItem(row_position, 0, QTableWidgetItem(str(variable)))
            self.fmpVariablesTable.setItem(row_position, 1, item)
            self.fmpVariablesTable.setItem(row_position, 2, QTableWidgetItem(str(details['value'])))
            self.fmpVariablesTable.setItem(row_position, 3, QTableWidgetItem(str(details['default'])))
            self.fmpVariablesTable.setItem(row_position, 4, QTableWidgetItem(str(details['description'])))


        ief_path = mrt_settings.loadProjectSetting(
            'ief_file', self.project.readPath('./temp')
        )
        variables_check = runvariables_check.IefVariablesCheck(self.project, ief_path)
        try:
            file_paths, variables = variables_check.run_tool()
        except Exception as err:
            QMessageBox.warning(
                self, "FMP ief file load failed", err.args[0]
            )
            return
        
        row_position = 0
        self.fmpVariablesTable.setRowCount(row_position)
        for variable, details in variables['changed'].items():
            outputTableRow(details, False)
            row_position += 1
        for variable, details in variables['default'].items():
            outputTableRow(details, True)
            row_position += 1

        row_position = 0
        self.fmpFilesTable.setRowCount(row_position)
        for file_type, file_data in file_paths.items():
            self.fmpFilesTable.insertRow(row_position)
            if file_type == 'Event data':
                for event in file_data:
                    event_name = 'Event ({})'.format(event['name'])
                    self.fmpFilesTable.setItem(row_position, 0, QTableWidgetItem(event_name))
                    self.fmpFilesTable.setItem(row_position, 1, QTableWidgetItem(event['file']))
            else:
                self.fmpFilesTable.setItem(row_position, 0, QTableWidgetItem(file_type))
                self.fmpFilesTable.setItem(row_position, 1, QTableWidgetItem(file_data))
            row_position += 1

        # Get the zzd file path
        # ief_name = os.path.split(ief_path)[1]
        results_path = file_paths['Results files'] + '.zzd'
        # results_path = os.path.join(results_path, ief_name + '.zzd')
        self.fmpRunSummaryTable.setRowCount(0)
        self.fmpDiagnosticsTable.setRowCount(0)
        if os.path.exists(results_path):
            mrt_settings.saveProjectSetting('zzd_file', results_path)
            self.loadZzdResults()


    def loadZzdResults(self):
        zzd_path = mrt_settings.loadProjectSetting(
            'zzd_file', self.project.readPath('./temp')
        )
        zzd_check = runvariables_check.ZzdFileCheck(self.project, zzd_path)
        try:
            diagnostics, warnings = zzd_check.run_tool()
        except Exception as err:
            QMessageBox.warning(
                self, "FMP zzd file load failed", err.args[0]
            )

        row_position = 0
        self.fmpRunSummaryTable.setRowCount(row_position)
        for name, details in diagnostics.items():
            self.fmpRunSummaryTable.insertRow(row_position)
            self.fmpRunSummaryTable.setItem(row_position, 0, QTableWidgetItem(name))
            self.fmpRunSummaryTable.setItem(row_position, 1, QTableWidgetItem(details['value']))
            self.fmpRunSummaryTable.setItem(row_position, 2, QTableWidgetItem(details['description']))
            row_position += 1

        row_position = 0
        self.fmpDiagnosticsTable.setRowCount(row_position)
        for error_type, details in warnings['error'].items():
            error_name = 'ERROR: ' + error_type
            self.fmpDiagnosticsTable.insertRow(row_position)
            self.fmpDiagnosticsTable.setItem(row_position, 0, QTableWidgetItem(error_name))
            self.fmpDiagnosticsTable.setItem(row_position, 1, QTableWidgetItem(str(details['count'])))
            self.fmpDiagnosticsTable.setItem(row_position, 2, QTableWidgetItem(details['info']))
            row_position += 1

        for warning_type, details in warnings['warning'].items():
            warning_name = 'WARNING: ' + warning_type
            self.fmpDiagnosticsTable.insertRow(row_position)
            self.fmpDiagnosticsTable.setItem(row_position, 0, QTableWidgetItem(warning_name))
            self.fmpDiagnosticsTable.setItem(row_position, 1, QTableWidgetItem(str(details['count'])))
            self.fmpDiagnosticsTable.setItem(row_position, 2, QTableWidgetItem(details['info']))
            row_position += 1

    def loadTlfDetails(self):
        def outputTableRow(details, is_default):
            item = None
            if is_default:
                item = QTableWidgetItem('Yes')
            else:
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
                item.setBackground(QColor(239, 175, 175)) # Light Red
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item.setText('No')

            self.tuflowVariablesTable.insertRow(row_position)
            self.tuflowVariablesTable.setItem(row_position, 0, QTableWidgetItem(variable))
            self.tuflowVariablesTable.setItem(row_position, 1, item)
            self.tuflowVariablesTable.setItem(row_position, 2, QTableWidgetItem(details['value']))
            self.tuflowVariablesTable.setItem(row_position, 3, QTableWidgetItem(details['default']))
            self.tuflowVariablesTable.setItem(row_position, 4, QTableWidgetItem(details['options']))
            self.tuflowVariablesTable.setItem(row_position, 5, QTableWidgetItem(details['description']))

        self.tuflowVariablesTable.setRowCount(0)
        self.tuflowFilesTable.setRowCount(0)
        self.tuflowRunSummaryTable.setRowCount(0)
        self.tuflowDiagnosticsTable.setRowCount(0)

        tlf_path = mrt_settings.loadProjectSetting(
            'tlf_file', self.project.readPath('./temp')
        )
        self.statusLabel.setText('Loading detailed TUFLOW .tlf data ...')
        QApplication.processEvents()
        variables_check = runvariables_check.TlfDetailsCheck(self.project, tlf_path)
        try:
            variables_check.run_tool()
        except Exception as err:
            QMessageBox.warning(
                self, "TUFLOW zzd file load failed", err.args[0]
            )
        variables = variables_check.variables
        files = variables_check.files
        checks = variables_check.checks
        run_summary = variables_check.run_summary

        self.statusLabel.setText('Updating TUFLOW Tables ...')
        QApplication.processEvents()
        row_position = 0
        self.tuflowVariablesTable.setRowCount(row_position)
        for variable, details in variables['Non_Default'].items():
            outputTableRow(details, False)
            row_position += 1
        for variable, details in variables['Default'].items():
            outputTableRow(details, True)
            row_position += 1

        row_position = 0
        self.tuflowFilesTable.setRowCount(row_position)
        for filename, details in files.items():
            self.tuflowFilesTable.insertRow(row_position)
            self.tuflowFilesTable.setItem(row_position, 0, QTableWidgetItem(details[0]))
            self.tuflowFilesTable.setItem(row_position, 1, QTableWidgetItem(''))
            self.tuflowFilesTable.setItem(row_position, 2, QTableWidgetItem(filename))
            self.tuflowFilesTable.setItem(row_position, 3, QTableWidgetItem(details[1]))
            row_position += 1

        row_position = 0
        self.tuflowDiagnosticsTable.setRowCount(row_position)
        for check_code, details in checks.items():
            self.tuflowDiagnosticsTable.insertRow(row_position)
            self.tuflowDiagnosticsTable.setItem(row_position, 0, QTableWidgetItem(details['type']))
            self.tuflowDiagnosticsTable.setItem(row_position, 1, QTableWidgetItem(check_code))
            self.tuflowDiagnosticsTable.setItem(row_position, 2, QTableWidgetItem(str(details['count'])))
            self.tuflowDiagnosticsTable.setItem(row_position, 3, QTableWidgetItem(details['message']))
            self.tuflowDiagnosticsTable.setItem(row_position, 4, QTableWidgetItem(details['wiki_link']))

        row_position = 0
        self.tuflowRunSummaryTable.setRowCount(row_position)
        for variable, details in run_summary.items():
            self.tuflowRunSummaryTable.insertRow(row_position)
            self.tuflowRunSummaryTable.setItem(row_position, 0, QTableWidgetItem(variable))
            self.tuflowRunSummaryTable.setItem(row_position, 1, QTableWidgetItem(details['value']))
            self.tuflowRunSummaryTable.setItem(row_position, 2, QTableWidgetItem(details['description']))
            row_position += 1

        self.statusLabel.setText('Update complete')
        QApplication.processEvents()