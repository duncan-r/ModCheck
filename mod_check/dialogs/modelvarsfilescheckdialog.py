
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
        self.fmModelsCBox.addItems(ief_names)
        self.tuflowModelsCBox.addItems(tlf_names)
        self.summaryLookup = [
            'tuflow_model', 'fm_model', 'gis', 'result', 'workspace', 'log', 'csv', 'other'
        ]
        self.allFilesSummaryCBox.addItems(['Tuflow Model', 'FM Model', 'GIS', 'Results', 'Workspaces', 'Logs', 'CSVs', 'Other'])        
        self.resultsTabWidget.setCurrentIndex(0)
        
    
    def show_fm(self, i):
        pass
    
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
        
        
        