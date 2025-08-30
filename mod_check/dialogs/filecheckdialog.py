
import os
import csv
from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget

from .dialogbase import DialogBase
from ..forms import ui_file_check_dialog as filecheck_ui
from ..tools import help, globaltools
from ..tools import filecheck
from ..tools import settings as mrt_settings

from ..mywidgets import graphdialogs as graphs
from PyQt5.pyrcc_main import showHelp

DATA_DIR = './data'
TEMP_DIR = './temp'


class FileCheckDialog(DialogBase, filecheck_ui.Ui_CheckFilesDialog):
    """Search model files and folders to check that files exist.
    """

    def __init__(self, dialog_name, iface, project):

        DialogBase.__init__(self, dialog_name, iface, project, 'Model File Audit')

        model_root = mrt_settings.loadProjectSetting(
            'model_root', self.project.readPath('./')
        )

        # Connect the slots
        self.modelFolderFileWidget.setStorageMode(QgsFileWidget.GetDirectory)
        self.modelFolderFileWidget.setFilePath(model_root)
        self.modelFolderFileWidget.fileChanged.connect(self.updateModelRoot)
        self.reloadBtn.clicked.connect(self.checkFiles)
        self.exportResultsBtn.clicked.connect(self.exportResults)
        self.saveFileTreeBtn.clicked.connect(self.saveFileTree)
        # self.elsewhereFilesTable.clicked.connect(lambda i: self.showParents(i, 'elsewhere'))
        # self.iefElsewhereFilesTable.clicked.connect(lambda i: self.showParents(i, 'ief'))
        # self.missingFilesTable.clicked.connect(lambda i: self.showParents(i, 'missing'))
        # self.elsewhereParentList.currentRowChanged.connect(lambda i: self.showParentFile(i, 'elsewhere'))
        # self.iefElsewhereParentList.currentRowChanged.connect(lambda i: self.showParentFile(i, 'ief'))
        # self.missingParentList.currentRowChanged.connect(lambda i: self.showParentFile(i, 'missing'))
        self.fileTreeFoldersOnlyCheckbox.stateChanged.connect(self.updateFileTree)
        self.searchFileTreeTextbox.returnPressed.connect(lambda: self.searchFileTree(False))
        self.fileTreeSearchBtn.clicked.connect(lambda: self.searchFileTree(False))
        self.fileTreeSearchFromTopBtn.clicked.connect(lambda: self.searchFileTree(True))
        self.showFullPathsBtn.clicked.connect(self.showFullPaths)
#         self.fileTreeTextEdit.verticalScrollbar().sliderMoved.connect(lambda i: self.treeSliderMoved(i, 'main'))
        self.fileTreeTextEdit.verticalScrollBar().valueChanged.connect(
            self.fileTreePathTextEdit.verticalScrollBar().setValue
        )
#             lambda i: self.treeSliderMoved(i, 'main'))
        self.fileTreePathTextEdit.verticalScrollBar().valueChanged.connect(
            self.fileTreeTextEdit.verticalScrollBar().setValue
        )
        
        # NEW 2025
        self.summaryLookup = []
        self.summaryComboBox.currentIndexChanged.connect(lambda i: self.showSummaryFiles(i))
        self.workspaceLookup = []
        self.logComboBox.currentIndexChanged.connect(lambda i: self.showWorkspaceFiles(i))
        self.fmpLookup = []
        self.fmpComboBox.currentIndexChanged.connect(lambda i: self.showFmpFiles(i))

#         self.splitter.setCollapsable(0, False)
#         self.splitter.setCollapsable(1, True)
        self.splitter.setStretchFactor(0, 9)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([self.splitter.sizes()[0], 0])
        self.search_results = None
        self.file_check = filecheck.FileChecker()
        self.file_check.status_signal.connect(self.updateStatus)

    def updateModelRoot(self):
        mrt_settings.saveProjectSetting('model_root', self.modelFolderFileWidget.filePath())
        self.checkFiles()

    @pyqtSlot(str)
    def updateStatus(self, status):
        if len(status) > 120:
            status = status[:120] + ' ...'
        self.statusLabel.setText(status)
        QApplication.processEvents()

    def treeSliderMoved(self, val, caller):
        self.fileTreePathTextEdit.verticalScrollbar().setSliderPosition(
            self.fileTreeTextEdit.verticalScrollbar().sliderPosition()
        )

    def showFullPaths(self):
        width = QApplication.primaryScreen().size().width()
        if self.splitter.sizes()[1] > 0:
            self.splitter.setSizes([width, 0])
        else:
            self.splitter.setSizes([width, width])

    def searchFileTree(self, from_start):
        """Search for text in the file tree text edit.

        Args:
            from_start(bool): if True the search will start from the file start.
        """
        def moveCursorToStart():
            cursor = self.fileTreeTextEdit.textCursor()
            cursor.movePosition(QTextCursor.Start) 
            self.fileTreeTextEdit.setTextCursor(cursor)

        if from_start:
            moveCursorToStart()
        search_text = self.searchFileTreeTextbox.text()
        found = self.fileTreeTextEdit.find(search_text)

        # If it isn't found try from the start
        if not found and not from_start:
            moveCursorToStart()
            found = self.fileTreeTextEdit.find(search_text)

    def checkFiles(self):
        """Search folders, load data and update dialog data."""
        self.search_results = []
        self.iefs = []
        self.workspace_files = {}
        self.workspaceLookup = []
        self.iefLookup = []
        self.summaryLookup = None
        self.logComboBox.clear()
        self.summaryComboBox.clear()
        self.summaryTable.setRowCount(0)
        self.logTable.setRowCount(0)
        # self.missingParentList.clear()
        # self.elsewhereParentList.clear()
        # self.iefElsewhereParentList.clear()
        model_root = mrt_settings.loadProjectSetting('model_root', './temp')
        self.iefs, self.search_results = self.file_check.auditModelFiles(model_root)

        self.summaryLookup = [
            'tuflow_model', 'fm_model', 'gis', 'result', 'workspace', 'log', 'csv', 'other'
        ]
        self.summaryComboBox.addItems(['Tuflow Model', 'FM Model', 'GIS', 'Results', 'Workspaces', 'Logs', 'CSVs', 'Other'])        
        self.loadWorkspaceFiles()
        self.workspaceLookup = list(self.workspace_files.keys())
        self.logComboBox.addItems(self.workspaceLookup)
        self.loadIefFiles()
        self.iefLookup = list(self.ief_files.keys())
        self.fmpComboBox.addItems(self.iefLookup)

        # self.resultsTabWidget.setCurrentIndex(0)
        # self.updateSummaryTab()
        # self.updateElsewhereTable(self.elsewhereFilesTable, self.search_results.results['found'])
        # self.updateElsewhereTable(self.iefElsewhereFilesTable, self.search_results.results['found_ief'])
        # self.updateMissingTable(self.search_results.results['missing'])
        # self.updateFileTree()
        
    def showSummaryFiles(self, i):
        try:
            contents = self.search_results[self.summaryLookup[i]]
        except KeyError:
            return
        except IndexError:
            return
        except TypeError:
            return

        self.summaryTable.setSortingEnabled(False)
        row_position = 0
        self.summaryTable.setRowCount(row_position)
        for content in contents:
            self.summaryTable.insertRow(row_position)
            self.summaryTable.setItem(row_position, 0, QTableWidgetItem(content.fileExt))
            self.summaryTable.setItem(row_position, 1, QTableWidgetItem(content.name))
            self.summaryTable.setItem(row_position, 2, QTableWidgetItem(content.filepath))
            row_position += 1
        self.summaryTable.setSortingEnabled(True)
        
    def findAllFiles(self, include_files=[], exclude_files=[]):
        all_files = {}
        for fname, ftype in self.search_results.items():
            if include_files and fname not in include_files: continue
            if exclude_files and fname in exclude_files: continue
            for f in ftype:
                all_files[f.name.lower()] = f.filepath
        return all_files

    def loadWorkspaceFiles(self):
        self.workspace_files = filecheck.loadWorkspaceFiles(self.search_results['workspace'])
        all_files = {}
        for fname, ftype in self.search_results.items():
            if fname in ['tree', 'log', 'workspace']: continue
            for f in ftype:
                all_files[f.name.lower()] = f.filepath

        for workspace, wfiles in self.workspace_files.items():
            for i, w in enumerate(wfiles):
                missing = 'No'
                newpath = 'Missing'
                try:
                    newpath = all_files[w.name.lower()]
                except KeyError:
                    missing = 'Yes'
                self.workspace_files[workspace][i].missing = missing
                self.workspace_files[workspace][i].newpath = newpath

    def showWorkspaceFiles(self, i):
        if len(self.workspaceLookup) < 1: return
        workspace = self.workspace_files[self.workspaceLookup[i]]

        self.logTable.setSortingEnabled(False)
        row_position = 0
        self.logTable.setRowCount(row_position)
        for w in workspace:
            self.logTable.insertRow(row_position)
            self.logTable.setItem(row_position, 0, QTableWidgetItem(w.missing))
            self.logTable.setItem(row_position, 1, QTableWidgetItem(w.extension))
            self.logTable.setItem(row_position, 2, QTableWidgetItem(w.name))
            self.logTable.setItem(row_position, 3, QTableWidgetItem(w.rawpath))
            self.logTable.setItem(row_position, 4, QTableWidgetItem(w.newpath))
            row_position += 1
        self.logTable.setSortingEnabled(True)
        
    def loadIefFiles(self):
        self.ief_files = filecheck.loadIefFiles(self.search_results['fm_model'])
        all_files = self.findAllFiles(include_files=['fm_model', 'tuflow_model', 'result'])
        all_files_keys = [k for k in all_files.keys()]
        all_files_keys_lower = [k.lower() for k in all_files_keys]
        for name, ief in self.ief_files.items():
            for i, f in enumerate(ief.files):
                missing = 'No'
                newpath = 'Missing'
                if f.name.lower() in all_files_keys_lower:
                    idx = all_files_keys_lower.index(f.name.lower())
                    newpath = all_files[all_files_keys[idx]]
                else:
                    missing = 'Yes'
                self.ief_files[name].files[i].missing = missing
                self.ief_files[name].files[i].newpath = newpath
    
    def showFmpFiles(self, i): 
        if len(self.iefLookup) < 1: return
        ief = self.ief_files[self.iefLookup[i]]

        self.fmpTable.setSortingEnabled(False)
        row_position = 0
        self.fmpTable.setRowCount(row_position)
        for i in ief.files:
            self.fmpTable.insertRow(row_position)
            self.fmpTable.setItem(row_position, 0, QTableWidgetItem(i.missing))
            self.fmpTable.setItem(row_position, 1, QTableWidgetItem(i.extension))
            self.fmpTable.setItem(row_position, 2, QTableWidgetItem(i.name))
            self.fmpTable.setItem(row_position, 3, QTableWidgetItem(i.rawpath))
            self.fmpTable.setItem(row_position, 4, QTableWidgetItem(i.newpath))
            row_position += 1
        self.fmpTable.setSortingEnabled(True)

    def updateFileTree(self):
        include_files = not self.fileTreeFoldersOnlyCheckbox.isChecked()
        if self.search_results:
            output, fullpaths = self.search_results.formatFileTree(
                include_files=include_files, include_full_paths=True
            )
            self.fileTreeTextEdit.setPlainText(output)
            self.fileTreePathTextEdit.setPlainText(fullpaths)
        if include_files:
            self.showFullPathsBtn.setEnabled(True)
        else:
            self.splitter.setSizes([50, 0])
            self.showFullPathsBtn.setEnabled(False)
            

    # def updateSummaryTab(self):
    #     output = ['File search summary\n'.upper()]
    #     output.append(self.search_results.summaryText())
    #     output.append('\n\nFiles that were ignored\n'.upper())
    #     output += [f.filepath for f in self.search_results.results_meta['ignored']]
    #     output.append('\n\nModel files reviewed\n'.upper())
    #     output += self.search_results.results_meta['checked']
    #     output = '\n'.join(output)
    #     self.summaryTextEdit.clear()
    #     self.summaryTextEdit.setText(output)

    # def updateMissingTable(self, missing_files):
    #     row_position = 0
    #     self.missingFilesTable.setRowCount(row_position)
    #     for missing in missing_files:
    #         self.missingFilesTable.insertRow(row_position)
    #         self.missingFilesTable.setItem(row_position, 0, QTableWidgetItem(missing['file'][0]))
    #         self.missingFilesTable.setItem(row_position, 1, QTableWidgetItem(missing['file'][1]))
    #         row_position += 1
    #
    # def updateElsewhereTable(self, table, file_list):
    #     row_position = 0
    #     table.setRowCount(row_position)
    #     for found in file_list:
    #         table.insertRow(row_position)
    #         table.setItem(row_position, 0, QTableWidgetItem(found['file'][0]))
    #         table.setItem(row_position, 1, QTableWidgetItem(found['file'][1]))
    #         table.setItem(row_position, 2, QTableWidgetItem(found['file'][2]))
    #         row_position += 1

    # def showParents(self, row, tab_name):
    #     if tab_name == 'elsewhere':
    #         the_table = self.elsewhereFilesTable
    #         the_list = self.elsewhereParentList
    #         parents = self.search_results.results['found'][the_table.currentRow()]['parents']
    #     elif tab_name == 'ief':
    #         the_table = self.iefElsewhereFilesTable
    #         the_list = self.iefElsewhereParentList
    #         parents = self.search_results.results['found_ief'][the_table.currentRow()]['parents']
    #     elif tab_name == 'missing':
    #         the_table = self.missingFilesTable
    #         the_list = self.missingParentList
    #         parents = self.search_results.results['missing'][the_table.currentRow()]['parents']
    #     else:
    #         return
    #
    #     the_list.clear()
    #     for p in parents:
    #         filename = os.path.split(p[0])[1]
    #         line = '{0} (line {1}) :\t {2}'.format(filename, p[1], p[0])
    #         the_list.addItem(line)

    # def showParentFile(self, row, tab_name):
    #     if row == -1: return
    #
    #     if tab_name == 'elsewhere':
    #         the_table = self.elsewhereFilesTable
    #         table_row = the_table.currentRow()
    #         parents = self.search_results.results['found'][table_row]['parents']
    #     elif tab_name == 'ief':
    #         the_table = self.iefElsewhereFilesTable
    #         table_row = the_table.currentRow()
    #         parents = self.search_results.results['found_ief'][table_row]['parents']
    #     elif tab_name == 'missing':
    #         the_table = self.missingFilesTable
    #         table_row = the_table.currentRow()
    #         parents = self.search_results.results['missing'][table_row]['parents']
    #     else:
    #         return
    #
    #     filename = the_table.item(table_row, 0).text()
    #     parent_file = parents[row][0]
    #     contents = []
    #     try:
    #         with open(parent_file, 'r') as pf:
    #             for line in pf.readlines():
    #                 contents.append(line)
    #     except OSError as err:
    #         QMessageBox.warning(
    #             self, "Failed to open file {0} ".format(filename), err.args[0]
    #         )
    #     dlg = graphs.ModelFileDialog(filename)
    #     dlg.showText(''.join(contents), filename)
    #     dlg.exec_()

    def saveFileTree(self):
        if self.search_results is None:
            QMessageBox.warning(
                self, "No results loaded", "There are no results loaded. Please run the check first."
            )
            return
        save_folder = mrt_settings.loadProjectSetting(
            'file_check_tree', mrt_settings.loadProjectSetting('model_root', './temp')
        )
        default_path = os.path.join(save_folder, 'file_tree.txt')
        filepath = QFileDialog(self).getSaveFileName(
            self, 'Export File Tree', default_path, "TXT File (*.txt)"
        )[0]
        if filepath:
            mrt_settings.saveProjectSetting('file_check_tree', os.path.split(filepath)[0])
            include_files = not self.fileTreeFoldersOnlyCheckbox.isChecked()
            try:
                self.search_results.saveFileTree(filepath, include_files=include_files)
            except OSError as err:
                QMessageBox.warning(
                    self, "File tree save failed", err.args[0] 
                )
                return

    def exportResults(self):
        if self.search_results is None:
            QMessageBox.warning(
                self, "No results loaded", "There are no results loaded. Please run the check first."
            )
            return
        save_folder = mrt_settings.loadProjectSetting(
            'file_check_results', mrt_settings.loadProjectSetting('model_root', './temp')
        )
        default_path = os.path.join(save_folder, 'filecheck_results.txt')
        filepath = QFileDialog(self).getSaveFileName(
            self, 'Export Results', default_path, "TXT File (*.txt)"
        )[0]
        if filepath:
            mrt_settings.saveProjectSetting('file_check_results', os.path.split(filepath)[0])
            try:
                self.search_results.exportResults(filepath)
            except OSError as err:
                QMessageBox.warning(
                    self, "Results export failed", err.args[0] 
                )
                return