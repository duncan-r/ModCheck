
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

        DialogBase.__init__(self, dialog_name, iface, project, 'Model Vars and Files Check')

        model_root = mrt_settings.loadProjectSetting(
            'model_root', self.project.readPath('./')
        )

        self.modelFolderFileWidget.setStorageMode(QgsFileWidget.GetDirectory)
        self.modelFolderFileWidget.setFilePath(model_root)
        self.modelFolderFileWidget.fileChanged.connect(self.updateModelRoot)
        self.reloadBtn.clicked.connect(self.find_files)
        
        self.fmModelsCBox.currentIndexChanged.connect(lambda i: self.show_fm(i))
        self.tuflowModelsCBox.currentIndexChanged.connect(lambda i: self.show_tuflow(i))

        self.summaryLookup = []
        self.fm_models = {}
        self.tuflow_models = {}
        self.allFilesSummaryCBox.currentIndexChanged.connect(lambda i: self.showSummaryFiles(i))

    def updateModelRoot(self):
        mrt_settings.saveProjectSetting('model_root', self.modelFolderFileWidget.filePath())
        self.find_files()
        
    def find_files(self):
        model_root = mrt_settings.loadProjectSetting('model_root', './temp')
        if os.path.isdir(model_root):
            file_finder = filecheck.FileFinder()
            self.iefs, self.tlfs, self.search_results = file_finder.auditModelFiles(model_root)
        else:
            QMessageBox.warning(self, "Model folder doesn't exist ".format(model_root))
            return
        
        ief_names = [ief.filepath.stem for ief in self.iefs]
        tlf_names = [tlf.filepath.stem for tlf in self.tlfs]
        try:
            self.setUpdatesEnabled(False)
            self.fmModelsCBox.addItems(ief_names)
            self.tuflowModelsCBox.addItems(tlf_names)
            self.summaryLookup = [
                'tuflow_model', 'fm_model', 'gis', 'result', 'workspace', 'log', 'csv', 'other'
            ]
            self.allFilesSummaryCBox.addItems(['Tuflow Model', 'FM Model', 'GIS', 'Results', 'Workspaces', 'Logs', 'CSVs', 'Other'])        
            self.resultsTabWidget.setCurrentIndex(0)
            self.fm_models = filecheck.loadIefFiles(self.search_results['fm_model'])
        except Exception as err:
            raise err
        finally:
            self.setUpdatesEnabled(True)

        if len(self.fm_models) > 0:
            self.show_fm(0)
        
    
    def show_fm(self, i):
        # fm = self.search_results['fm_model']
        # iefs = filecheck.loadIefFiles(fm)
        fm_name = str(self.fmModelsCBox.currentText())
        try:
            fm = self.fm_models[fm_name]
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

        self.variablesTable.setSortingEnabled(False)
        row_position = 0
        self.modelFilesTable.setRowCount(row_position)
        for f in fm.files:
            self.modelFilesTable.insertRow(row_position)
            self.modelFilesTable.setItem(row_position, 0, QTableWidgetItem(f.ftype))
            self.modelFilesTable.setItem(row_position, 1, QTableWidgetItem(f.name))
            self.modelFilesTable.setItem(row_position, 2, QTableWidgetItem(''))
            self.modelFilesTable.setItem(row_position, 3, QTableWidgetItem(str(f.fullpath)))
            row_position += 1
        self.modelFilesTable.setSortingEnabled(True)

        self.diagnosticDetailsTable.setSortingEnabled(False)
        row_position = 0
        self.diagnosticDetailsTable.setRowCount(row_position)
        for k, detail in fm.diagnostics['details'].items():
            self.diagnosticDetailsTable.insertRow(row_position)
            self.diagnosticDetailsTable.setItem(row_position, 0, QDetailsTableWidgetItem(k))
            self.diagnosticDetailsTable.setItem(row_position, 1, QDetailsTableWidgetItem(detail['value']))
            self.diagnosticDetailsTable.setItem(row_position, 2, QDetailsTableWidgetItem(detail['description']))
            row_position += 1
        self.diagnosticDetailsTable.setSortingEnabled(True)

        self.diagnosticWarningTable.setSortingEnabled(False)
        row_position = 0
        self.diagnosticWarningTable.setRowCount(row_position)
        for k, warning in fm.diagnostics['warnings'].items():
            self.diagnosticWarningTable.insertRow(row_position)
            self.diagnosticWarningTable.setItem(row_position, 0, QWarningTableWidgetItem(warning['type']))
            self.diagnosticWarningTable.setItem(row_position, 1, QWarningTableWidgetItem(str(warning['count'])))
            self.diagnosticWarningTable.setItem(row_position, 2, QWarningTableWidgetItem(warning['description']))
            row_position += 1
        self.diagnosticWarningTable.setSortingEnabled(True)
    
    def show_tuflow(self, i):
        pass
    
    def showSummaryFiles(self, i):
        try:
            contents = self.search_results[self.summaryLookup[i]]
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
        
        
        