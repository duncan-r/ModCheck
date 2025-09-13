
import os
import csv
from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget

from .dialogbase import DialogBase
# from ..forms import ui_file_check_dialog as filecheck_ui
from ..forms import ui_modelvarsfiles_check_dialog as modelcheck_ui
from ..tools import help, globaltools
from ..tools import filecheck
from ..tools import settings as mrt_settings

from ..mywidgets import graphdialogs as graphs
from PyQt5.pyrcc_main import showHelp

DATA_DIR = './data'
TEMP_DIR = './temp'


class ModelVarsFilesCheckDialog(DialogBase, modelcheck_ui.Ui_ModelVarsFilesCheckDialog):
    """Search model files and folders to check that files exist.
    """

    def __init__(self, dialog_name, iface, project):

        DialogBase.__init__(self, dialog_name, iface, project, 'Model Files Variables')

        model_root = mrt_settings.loadProjectSetting(
            'model_root', self.project.readPath('./')
        )

        self.modelFolderFileWidget.setStorageMode(QgsFileWidget.GetDirectory)
        self.modelFolderFileWidget.setFilePath(model_root)
        self.modelFolderFileWidget.fileChanged.connect(self.updateModelRoot)
        self.reloadBtn.clicked.connect(self.findFiles)
        
        self.modelsCBox.currentIndexChanged.connect(lambda i: self.showModel(i))
        # self.tuflowModelsCBox.currentIndexChanged.connect(lambda i: self.show_tuflow(i))

        self.summaryLookup = []
        self.fm_models = {}
        self.tuflow_models = {}
        self.allFilesSummaryCBox.currentIndexChanged.connect(lambda i: self.showSummaryFiles(i))

    def updateModelRoot(self):
        mrt_settings.saveProjectSetting('model_root', self.modelFolderFileWidget.filePath())
        self.findFiles()
        
    def findFiles(self):
        model_root = mrt_settings.loadProjectSetting('model_root', './temp')
        if not os.path.isdir(model_root):
            # file_finder = filecheck.FileFinder()
            # self.iefs, self.tlfs, self.search_results = file_finder.auditModelFiles(model_root)
        # else:
            QMessageBox.warning(self, "Folder does not exist", "Model folder doesn't exist at: {}".format(model_root))
            return
        
        # try:
        self.model_checker = filecheck.ModelChecker(model_root)
        self.model_checker.status_update_signal.connect(self._updateStatus)
        self.model_checker.progress_max_signal.connect(self._setProgressMax)
        self.model_checker.progress_val_signal.connect(self._setProgressVal)
        self.model_checker.searchFiles()
        self.model_checker.checkMissingFiles()
        self._updateStatus("Model check complete")
        self._setProgressVal(0)
        # except Exception as err:
        #     QMessageBox.warning(self, "Search Files Error", "Failed to read model files at: {}".format(model_root))
        #     return

        self.setUpdatesEnabled(False)
        self.modelsCBox.clear()
        # self.tuflowModelsCBox.clear()
        self.modelsCBox.addItems(self.model_checker.ief_names)
        self.modelsCBox.addItems(self.model_checker.tlf_names)
        # self.tuflowModelsCBox.addItems(self.model_checker.tlf_names)
        self.summaryLookup = [
            'tuflow_model', 'fm_model', 'gis', 'result', 'workspace', 'log', 'csv', 'other'
        ]
        self.allFilesSummaryCBox.addItems(['Tuflow Model', 'FM Model', 'GIS', 'Results', 'Workspaces', 'Logs', 'CSVs', 'Other'])        
        self.resultsTabWidget.setCurrentIndex(0)
        self.setUpdatesEnabled(True)
        self.showModel(0)
        
    def _updateStatus(self, status):
        self.statusLabel.setText(status)
        QApplication.processEvents()
    
    def _setProgressMax(self, value):
        self.progressBar.setMaximum(value)

    def _setProgressVal(self, value):
        self.progressBar.setValue(value)
            
    def showModel(self, i):
        name = str(self.modelsCBox.currentText())
        name = name.replace('\s', ' ')
        name = name.split()
        if len(name) < 2:
            return
        if name[0].strip() == 'FM':
            self.showFm(name[1].strip())
        elif name[0].strip() == 'TUFLOW':
            self.showTuflow(name[1].strip())
    
    def showFm(self, name):
        # fm = self.search_results['fm_model']
        # iefs = filecheck.loadIefFiles(fm)
        # fm_name = str(self.fmModelsCBox.currentText())
        try:
            fm = self.model_checker.fm_models[name]
        except KeyError as err:
            return

        self.variablesTable.setSortingEnabled(False)
        row_position = 0
        self.variablesTable.setRowCount(row_position)
        for k, params in fm.params['changed'].items():
            self.variablesTable.insertRow(row_position)
            self.variablesTable.setItem(row_position, 0, QTableWidgetItem(params['name']))
            self.variablesTable.setItem(row_position, 1, QTableWidgetItem('No'))
            self.variablesTable.setItem(row_position, 2, QTableWidgetItem(str(params['value'])))
            self.variablesTable.setItem(row_position, 3, QTableWidgetItem(params['default']))
            self.variablesTable.setItem(row_position, 4, QTableWidgetItem(params['description']))
            row_position += 1
        self.variablesTable.setSortingEnabled(True)

        self.modelFilesTable.setSortingEnabled(False)
        row_position = 0
        self.modelFilesTable.setRowCount(row_position)
        for f in fm.files:
            self.modelFilesTable.insertRow(row_position)
            self.modelFilesTable.setItem(row_position, 0, QTableWidgetItem(f.ftype))
            self.modelFilesTable.setItem(row_position, 1, QTableWidgetItem(f.name))
            self.modelFilesTable.setItem(row_position, 2, QTableWidgetItem(f.missing))
            self.modelFilesTable.setItem(row_position, 3, QTableWidgetItem(str(f.resolved_path)))
            self.modelFilesTable.setItem(row_position, 4, QTableWidgetItem(str(f.fullpath)))
            row_position += 1
        self.modelFilesTable.setSortingEnabled(True)

        self.modelFilesMissingTable.setSortingEnabled(False)
        row_position = 0
        self.modelFilesMissingTable.setRowCount(row_position)
        for f in fm.missing:
            self.modelFilesMissingTable.insertRow(row_position)
            self.modelFilesMissingTable.setItem(row_position, 0, QTableWidgetItem(f.filepath.suffix.upper()))
            self.modelFilesMissingTable.setItem(row_position, 1, QTableWidgetItem(f.name))
            self.modelFilesMissingTable.setItem(row_position, 2, QTableWidgetItem(str(f.fullpath)))
            row_position += 1
        self.modelFilesMissingTable.setSortingEnabled(True)

        self.diagnosticDetailsTable.setSortingEnabled(False)
        row_position = 0
        self.diagnosticDetailsTable.setRowCount(row_position)
        for k, detail in fm.diagnostics['details'].items():
            self.diagnosticDetailsTable.insertRow(row_position)
            self.diagnosticDetailsTable.setItem(row_position, 0, QTableWidgetItem(k))
            self.diagnosticDetailsTable.setItem(row_position, 1, QTableWidgetItem(detail['value']))
            self.diagnosticDetailsTable.setItem(row_position, 2, QTableWidgetItem(detail['description']))
            row_position += 1
        self.diagnosticDetailsTable.setSortingEnabled(True)

        self.diagnosticWarningTable.setSortingEnabled(False)
        row_position = 0
        self.diagnosticWarningTable.setRowCount(row_position)
        for k, warning in fm.diagnostics['warnings'].items():
            self.diagnosticWarningTable.insertRow(row_position)
            self.diagnosticWarningTable.setItem(row_position, 0, QTableWidgetItem(k))
            self.diagnosticWarningTable.setItem(row_position, 1, QTableWidgetItem(str(warning['count'])))
            self.diagnosticWarningTable.setItem(row_position, 2, QTableWidgetItem(warning['info']))
            row_position += 1
        self.diagnosticWarningTable.setSortingEnabled(True)
    
    def showTuflow(self, name):
        
        # tuflow_name = str(self.tuflowModelsCBox.currentText())
        try:
            tuflow = self.model_checker.tuflow_models[name]
        except KeyError as err:
            return

        self.variablesTable.setSortingEnabled(False)
        row_position = 0
        self.variablesTable.setRowCount(row_position)
        for var in tuflow.all_variables:
            for k, v in var.items():
                self.variablesTable.insertRow(row_position)
                self.variablesTable.setItem(row_position, 0, QTableWidgetItem(k))
                self.variablesTable.setItem(row_position, 1, QTableWidgetItem(''))
                self.variablesTable.setItem(row_position, 2, QTableWidgetItem(str(v)))
                self.variablesTable.setItem(row_position, 3, QTableWidgetItem(''))
                self.variablesTable.setItem(row_position, 4, QTableWidgetItem(''))
                row_position += 1

        for k, v in tuflow.non_defaults.items():
            self.variablesTable.insertRow(row_position)
            self.variablesTable.setItem(row_position, 0, QTableWidgetItem(k))
            self.variablesTable.setItem(row_position, 1, QTableWidgetItem('No'))
            self.variablesTable.setItem(row_position, 2, QTableWidgetItem(str(v['value'])))
            self.variablesTable.setItem(row_position, 3, QTableWidgetItem(v['default']))
            self.variablesTable.setItem(row_position, 4, QTableWidgetItem(v['description']))
            row_position += 1
        self.variablesTable.setSortingEnabled(True)
        
        self.modelFilesTable.setSortingEnabled(False)
        row_position = 0
        self.modelFilesTable.setRowCount(row_position)
        for f in tuflow.all_files:
            self.modelFilesTable.insertRow(row_position)
            self.modelFilesTable.setItem(row_position, 0, QTableWidgetItem(f.ftype))
            self.modelFilesTable.setItem(row_position, 1, QTableWidgetItem(f.name))
            self.modelFilesTable.setItem(row_position, 2, QTableWidgetItem(f.missing))
            self.modelFilesTable.setItem(row_position, 3, QTableWidgetItem(str(f.resolved_path)))
            self.modelFilesTable.setItem(row_position, 4, QTableWidgetItem(str(f.fullpath)))
            row_position += 1
        self.modelFilesTable.setSortingEnabled(True)

        self.modelFilesMissingTable.setSortingEnabled(False)
        row_position = 0
        self.modelFilesMissingTable.setRowCount(row_position)
        for f in tuflow.missing:
            self.modelFilesMissingTable.insertRow(row_position)
            self.modelFilesMissingTable.setItem(row_position, 0, QTableWidgetItem(f.filepath.suffix.upper()))
            self.modelFilesMissingTable.setItem(row_position, 1, QTableWidgetItem(f.name))
            self.modelFilesMissingTable.setItem(row_position, 2, QTableWidgetItem(str(f.fullpath)))
            row_position += 1
        self.modelFilesMissingTable.setSortingEnabled(True)
        
        self.diagnosticDetailsTable.setSortingEnabled(False)
        row_position = 0
        self.diagnosticDetailsTable.setRowCount(row_position)
        for k, detail in tuflow.run_summary.items():
            self.diagnosticDetailsTable.insertRow(row_position)
            self.diagnosticDetailsTable.setItem(row_position, 0, QTableWidgetItem(k))
            self.diagnosticDetailsTable.setItem(row_position, 1, QTableWidgetItem(str(detail)))
            self.diagnosticDetailsTable.setItem(row_position, 2, QTableWidgetItem(''))
            row_position += 1
        self.diagnosticDetailsTable.setSortingEnabled(True)
        
        self.diagnosticWarningTable.setSortingEnabled(False)
        row_position = 0
        self.diagnosticWarningTable.setRowCount(row_position)
        for d in tuflow.diagnostics:
            # for k, d in dtype.items():
            self.diagnosticWarningTable.insertRow(row_position)
            self.diagnosticWarningTable.setItem(row_position, 0, QTableWidgetItem(d['type']))
            self.diagnosticWarningTable.setItem(row_position, 1, QTableWidgetItem(str(d['count'])))
            self.diagnosticWarningTable.setItem(row_position, 2, QTableWidgetItem(d['message']))
            row_position += 1
        self.diagnosticWarningTable.setSortingEnabled(True)
    
    def showSummaryFiles(self, i):
        try:
            # contents = self.search_results[self.summaryLookup[i]]
            contents = self.model_checker.found_files.files[self.summaryLookup[i]]
        except (KeyError, IndexError, TypeError) as err:
            return

        self.allFilesSummaryTable.setSortingEnabled(False)
        row_position = 0
        self.allFilesSummaryTable.setRowCount(row_position)
        for content in contents:
            self.allFilesSummaryTable.insertRow(row_position)
            self.allFilesSummaryTable.setItem(row_position, 0, QTableWidgetItem(content.fileExt))
            self.allFilesSummaryTable.setItem(row_position, 1, QTableWidgetItem(content.filepath.stem))
            self.allFilesSummaryTable.setItem(row_position, 2, QTableWidgetItem(str(content.filepath.resolve())))
            row_position += 1
        self.allFilesSummaryTable.setSortingEnabled(True)
        
        
        