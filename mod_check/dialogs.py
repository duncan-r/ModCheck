

import os
import csv
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from .forms import ui_help_dialog as help_ui
from .forms import ui_text_dialog as text_dialog
from .forms import ui_chainage_calculator_dialog as chaincalc_ui
from .forms import ui_fmptuflow_widthcheck_dialog as fmptuflowwidthcheck_ui
from .forms import ui_runvariables_check_dialog as fmptuflowvariablescheck_ui
from .forms import ui_fmpsectionproperty_check_dialog as fmpsectioncheck_ui
from .forms import ui_fmprefh_check_dialog as refh_ui
from .forms import ui_tuflowstability_check_dialog as tuflowstability_ui
from .forms import ui_nrfa_viewer_dialog as nrfa_ui
from .forms import ui_file_check_dialog as filecheck_ui

from .tools import help
from .tools import chainagecalculator as chain_calc
from .tools import widthcheck
from .tools import runvariablescheck as runvariables_check
from .tools import fmpsectioncheck as fmpsection_check
from .tools import refhcheck
from .tools import tuflowstabilitycheck as tmb_check
from .tools import nrfaviewer as nrfa_viewer
from .tools import filecheck
from .tools import settings as mrt_settings

from .widgets import graphdialogs as graphs
from PyQt5.pyrcc_main import showHelp

DATA_DIR = './data'
TEMP_DIR = './temp'

class DialogBase(QDialog):
    """Base class interface for standard functionality in Dialog classes.
    
    """
    closing = pyqtSignal(str)
    
    def __init__(self, dialog_name, iface, project, help_key):
        QDialog.__init__(self)
        self.dialog_name = dialog_name
        self.iface = iface
        self.project = project
        self.help_key = help_key
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        
        self.buttonBox.clicked.connect(self.buttonBoxClicked)
        
    def buttonBoxClicked(self, btn):
        name = btn.text()
        if name == 'Close':
            self.close()
        elif name == 'Help':
            self.showHelp()
            
    def signalClose(self):
        """Notify listeners that the dialog is being closed."""
        self.closing.emit(self.dialog_name)
        
    def closeEvent(self, *args, **kwargs):
        """Override the close event to emit a signal.
        
        Overrides: QDialog.closeEvent.
        """
        self.signalClose()
        return QDialog.closeEvent(self, *args, **kwargs)

    def showHelp(self):
        dialog = graphs.LocalHelpDialog('{0} - {1}'.format('Help', self.help_key))
        dialog.showText(help.helpText(self.help_key))
        dialog.exec_()


class ChainageCalculatorDialog(DialogBase, chaincalc_ui.Ui_ChainageCalculator):
    """Retrieve and compare chainage values from FMP and TUFLOW models.
    
    Extracts the chainage (distance to next node) values for all sections in an
    FMP model .dat file. Also summarises chainage totals by reach.
    
    If a nwk_line shape file is available for the TUFLOW model it will compare
    the length values of the nwk_line to check that there is consistency 
    between the FMP and TUFLOW model chainages.
    """
    
    def __init__(self, dialog_name, iface, project):
        DialogBase.__init__(self, dialog_name, iface, project, 'Check Chainage')
        
        self.chainage_calculator = chain_calc.CompareFmpTuflowChainage()
        
        self.buttonBox.clicked.connect(self.signalClose)
        self.calcFmpChainageOnlyBtn.clicked.connect(self.calculateFmpOnlyChainage)
        self.compareChainageBtn.clicked.connect(self.compareTuflowFmpChainage)
        self.fmpOnlyCheckbox.stateChanged.connect(self.compareFmpOnlyChange)
        self.exportResultsBtn.clicked.connect(self.exportChainageResults)
        self.exportAllCheckbox.stateChanged.connect(self.setExportAll)
        self.exportFmpCheckbox.stateChanged.connect(self.setExportIndividual)
        self.exportReachCheckbox.stateChanged.connect(self.setExportIndividual)
        self.exportComparisonCheckbox.stateChanged.connect(self.setExportIndividual)
        self.tuflowFmpComparisonTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tuflowFmpComparisonTable.customContextMenuRequested.connect(self._comparisonTableContext)
        
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./temp')
        )
        dx_tol = mrt_settings.loadProjectSetting('chainage_dx_tol', 10)
        self.datFileWidget.setFilePath(dat_path)
        self.datFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'dat_file'))
        self.dxToleranceSpinbox.valueChanged.connect(self.dxTolValueChanged)
        self.dxToleranceSpinbox.setValue(dx_tol)
        
        # Populate estry nwk layer combo (line layers only)
        self.estryNwkLayerCBox.setFilters(QgsMapLayerProxyModel.LineLayer)
        
    def _comparisonTableContext(self, pos):
        """Add context menu to comparison table.
        
        Allow user to select and zoom to the chosen nwk line section in the map window.
        """
        index = self.tuflowFmpComparisonTable.itemAt(pos)
        if index is None: return
        menu = QMenu()
        locate_section_action = menu.addAction("Locate Section")

        # Get the action and do whatever it says
        action = menu.exec_(self.tuflowFmpComparisonTable.viewport().mapToGlobal(pos))

        if action == locate_section_action:
            row = self.tuflowFmpComparisonTable.currentRow()
            id = self.tuflowFmpComparisonTable.item(row, 2).text()

            # Find the nwk line feature with the given id, select and zoom to it
            nwk_layer = self.estryNwkLayerCBox.currentLayer()
            self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
            nwk_layer.removeSelection()
            for f in nwk_layer.getFeatures():
                if f['ID'] == id:
                    nwk_layer.select(f.id())
                    self.iface.mapCanvas().zoomToSelected(nwk_layer)
                    break

    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        
    def dxTolValueChanged(self, value):
        mrt_settings.saveProjectSetting('chainage_dx_tol', value)
        
    def setExportAll(self, checkState):
        if checkState == 2:
            self.exportFmpCheckbox.setChecked(False)
            self.exportReachCheckbox.setChecked(False)
            self.exportComparisonCheckbox.setChecked(False)
            self.exportAllCheckbox.setChecked(True)
        
    def setExportIndividual(self):
        if self.exportAllCheckbox.isChecked():
            self.exportAllCheckbox.setChecked(False)
        
    def compareFmpOnlyChange(self, *args):
        """Setup the dialog for FMP only or FMP-TUFLOW calculation.
        
        Disables different parts of the dialog depending on whether the user
        wants to just extract FMP chainage values or compare them to TUFLOW.
        """
        if self.fmpOnlyCheckbox.isChecked():
            self.calcFmpChainageOnlyBtn.setEnabled(True)
            self.tuflowInputsGroupbox.setEnabled(False)
        else:
            self.calcFmpChainageOnlyBtn.setEnabled(False)
            self.tuflowInputsGroupbox.setEnabled(True)
            
    def calculateFmpOnlyChainage(self):
        """Calculate only the FMP model chainage values.
        
        If no TUFLOW nwk line shape file is available for comparison (common in
        models that do not include WLL's) the user can calculate only the FMP
        chainage values.
        
        Loads values by both section and 'reach' and puts them into tables on the
        dialog. The reach chainage summary is the total chainage across 
        consecutive river, interpolate or replicate sections.
        """
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./temp')
        )
        if dat_path is None:
            QMessageBox.warning(
                self, "Select an FMP dat file", "Please select an FMP dat file first"
            )
        elif not os.path.exists(dat_path):
            QMessageBox.warning(
                self, "FMP dat file not found", "FMP dat file could not be found"
            )
        else:
            self.statusLabel.setText('Calculating FMP Chainage...')
            QApplication.processEvents()
            fmp_chainage, reach_chainage = self.chainage_calculator.fmpChainage(dat_path)
            self._showFmpChainageResults(fmp_chainage, reach_chainage)
            self.statusLabel.setText('FMP Chainage calculation complete')
        self.tuflowFmpComparisonTable.setRowCount(0)
        self.outputsTabWidget.setCurrentIndex(0)
            
    def compareTuflowFmpChainage(self):
        """Compare FMP section chainage to TUFLOW node distances.
        
        Load the FMP section chainage values and compare them against the values
        calculated from the user selected TUFLOW nwk line layer. Identifies
        all sections where the difference is chainage is greater than the user
        supplied tolerance.
        """
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./temp')
        )
        
        nwk_layer = self.estryNwkLayerCBox.currentLayer()
        dx_tol = self.dxToleranceSpinbox.value()
        self.statusLabel.setText('Calculating FMP chainage (1/3) ...')
        QApplication.processEvents()
        fmp_chainage, reach_chainage = self.chainage_calculator.fmpChainage(dat_path)
        self.statusLabel.setText('Calculating TUFLOW nwk line chainage (2/3) ...')
        QApplication.processEvents()
        tuflow_chainage = self.chainage_calculator.tuflowChainage(nwk_layer)
        self.statusLabel.setText('Comparing FMP-TUFLOW chainage (3/3) ...')
        QApplication.processEvents()
        chainage_compare = self.chainage_calculator.compareChainage(
            fmp_chainage, tuflow_chainage, dx_tol
        )
        self.statusLabel.setText('Chainage compare complete')

        self._showFmpChainageResults(fmp_chainage, reach_chainage)
        self._showCompareChainageResults(chainage_compare)
        self.outputsTabWidget.setCurrentIndex(1)
            
    def _showFmpChainageResults(self, unit_chainage, reach_chainage):
        """Populate the FMP chainage tables with the results."""
        row_position = 0
        self.fmpChainageTable.setRowCount(row_position)
        for unit in unit_chainage:
            chainage = '{:.2f}'.format(unit['chainage'])
            cum_reach_chainage = '{:.2f}'.format(unit['cum_reach_chainage'])
            cum_total_chainage = '{:.2f}'.format(unit['cum_total_chainage'])
            self.fmpChainageTable.insertRow(row_position)
            self.fmpChainageTable.setItem(row_position, 0, QTableWidgetItem(unit['category']))
            self.fmpChainageTable.setItem(row_position, 1, QTableWidgetItem(unit['name']))
            self.fmpChainageTable.setItem(row_position, 2, QTableWidgetItem(chainage))
            self.fmpChainageTable.setItem(row_position, 3, QTableWidgetItem(cum_reach_chainage))
            self.fmpChainageTable.setItem(row_position, 4, QTableWidgetItem(cum_total_chainage))
            self.fmpChainageTable.setItem(row_position, 5, QTableWidgetItem(str(unit['reach_number'])))
            row_position += 1

        row_position = 0
        self.fmpReachChainageTable.setRowCount(row_position)
        for unit in reach_chainage:
            total_chainage = '{:.2f}'.format(unit['total_chainage'])
            self.fmpReachChainageTable.insertRow(row_position)
            self.fmpReachChainageTable.setItem(row_position, 0, QTableWidgetItem(str(unit['reach_number'])))
            self.fmpReachChainageTable.setItem(row_position, 1, QTableWidgetItem(unit['start']))
            self.fmpReachChainageTable.setItem(row_position, 2, QTableWidgetItem(unit['end']))
            self.fmpReachChainageTable.setItem(row_position, 3, QTableWidgetItem(str(unit['section_count'])))
            self.fmpReachChainageTable.setItem(row_position, 4, QTableWidgetItem(total_chainage))
            row_position += 1

    def _showCompareChainageResults(self, chainage_compare):
        """Populate the FMP-TUFLOW comparison table with the results."""

        def addRow(details, status, row_position):
            """Add a row to comparison table.
            
            Args:
                details(dict): containing the row data.
                status(str): the pass/fail status of the section.
                row_position(int): the row number to insert into the table.
            """
            status_item = QTableWidgetItem()
            status_item.setTextAlignment(Qt.AlignCenter|Qt.AlignVCenter)
            status_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            status_item.setText(status)
            if status == 'FAILED' or status == 'NOT FOUND':
                status_item.setBackground(QColor(239, 175, 175)) # Light Red

            diff = '{:.2f}'.format(details['diff'])
            fmp_chainage = '{:.2f}'.format(details['chainage'])
            nwk_length = '{:.2f}'.format(details['nwk_line_length'])
            nwk_len_or_ana = '{:.2f}'.format(details['nwk_len_or_ana'])
            self.tuflowFmpComparisonTable.insertRow(row_position)
            self.tuflowFmpComparisonTable.setItem(row_position, 0, status_item)
            self.tuflowFmpComparisonTable.setItem(row_position, 1, QTableWidgetItem(details['type']))
            self.tuflowFmpComparisonTable.setItem(row_position, 2, QTableWidgetItem(details['name']))
            self.tuflowFmpComparisonTable.setItem(row_position, 3, QTableWidgetItem(diff))
            self.tuflowFmpComparisonTable.setItem(row_position, 4, QTableWidgetItem(fmp_chainage))
            self.tuflowFmpComparisonTable.setItem(row_position, 5, QTableWidgetItem(nwk_length))
            self.tuflowFmpComparisonTable.setItem(row_position, 6, QTableWidgetItem(nwk_len_or_ana))
        
        row_position = 0
        self.tuflowFmpComparisonTable.setRowCount(row_position)
        for item in chainage_compare['fail']:
            addRow(item, 'FAILED', row_position)
            row_position += 1

        self.tuflowFmpComparisonTable.setRowCount(row_position)
        for item in chainage_compare['missing']:
            addRow(item, 'NOT FOUND', row_position)
            row_position += 1

        self.tuflowFmpComparisonTable.setRowCount(row_position)
        for item in chainage_compare['ok']:
            addRow(item, 'PASS', row_position)
            row_position += 1
        
    def exportChainageResults(self):
        """Export the chainage results to csv.
        
        Export the results types selected by the user to csv files.
        """
        default_folder = mrt_settings.loadProjectSetting('results_dir', './temp')
        if default_folder == './temp':
            default_folder = mrt_settings.loadProjectSetting('working_dir', './temp')
        folder = QFileDialog(self).getExistingDirectory(
            self, 'Results Ouput Folder', default_folder
        )
        mrt_settings.saveProjectSetting('results_dir', folder)
        export_widgets = {
            'all': self.exportAllCheckbox,
            'fmp': self.exportFmpCheckbox,
            'reach': self.exportReachCheckbox,
            'comparison': self.exportComparisonCheckbox,
        }
        export_types = []
        if export_widgets['all'].isChecked():
            export_types = export_widgets.keys()
        else:
            for name, widget in export_widgets.items():
                if name != 'all' and widget.isChecked():
                    export_types.append(name) 
        
        export_fail = []
        for t in export_types:
            self.statusLabel.setText('Exporting results for {0} ...'.format(t))
            try:
                self.chainage_calculator.exportResults(folder, t)
            except Exception as err:
                export_fail.append(t)
        label_path = folder if len(folder) < 100 else folder[-100:]
        self.statusLabel.setText('Results saved to {0}'.format(label_path))
        if export_fail:
            QMessageBox.warning(
                self, "Unable to export some results", 
                '\n'.join(
                    "Unable to export some results for {0}".format(', '.join(export_fail)), 
                    err.args[0]
                )
            )


class FmpTuflowWidthCheckDialog(DialogBase, fmptuflowwidthcheck_ui.Ui_FmpTuflowWidthCheckDialog):
    """Compare FMP and TUFLOW model sections widths.
    
    Find the active section widths from the FMP model and compare them to the TUFLOW
    model.
    """
    
    def __init__(self, dialog_name, iface, project):
        DialogBase.__init__(self, dialog_name, iface, project, 'Check Width')
        
        self.width_check = widthcheck.SectionWidthCheck(self.project)

        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./')
        )
        
        # Connect the slots
        self.buttonBox.clicked.connect(self.signalClose)
        self.checkWidthsBtn.clicked.connect(self.checkWidths)
        self.datFileWidget.setFilePath(dat_path)
        self.datFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'dat_file'))
        self.exportResultsBtn.clicked.connect(self.exportResults)
        self.failedTableWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.failedTableWidget.customContextMenuRequested.connect(self._failedTableContext)
        
        # Populate estry nwk layer combo (point and line layers only)
        self.fmpNodesLayerCbox.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.cnLinesLayerCbox.setFilters(QgsMapLayerProxyModel.LineLayer)

    def _failedTableContext(self, pos):
        """Add context menu to failed sections table.
        
        Allow user to select and zoom to the chosen section in the map window.
        """
        index = self.failedTableWidget.itemAt(pos)
        if index is None: return
        menu = QMenu()
        locate_section_action = menu.addAction("Locate Section")

        # Get the action and do whatever it says
        action = menu.exec_(self.failedTableWidget.viewport().mapToGlobal(pos))

        if action == locate_section_action:
            row = self.failedTableWidget.currentRow()
            id = self.failedTableWidget.item(row, 1).text()

            # Find the nodes point feature with the given id, select and zoom to it
            nodes_layer = self.fmpNodesLayerCbox.currentLayer()
            self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
            nodes_layer.removeSelection()
            for f in nodes_layer.getFeatures():
                if f[0] == id:
                    nodes_layer.select(f.id())
                    self.iface.mapCanvas().zoomToSelected(nodes_layer)
                    break

    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        
    def checkWidths(self):
        """Compare FMP and TUFLOW section widths for parity.
        
        Calculate the active 1D section widths from the FMP .dat file and compare 
        them to the widths in the TUFLOW model, based on the distance between 
        the end points of the CN lines attached to the point in the 1d_nodes 
        layer with the same name as the FMP section.
        
        Success of failure of the check is based on the user supplier dw_tol
        tolerance value.
        """
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./')
        )
        if dat_path is None:
            QMessageBox.warning(
                self, "No FMP dat file selected", "Please select an FMP dat file first"
            )
        elif not os.path.exists(dat_path):
            QMessageBox.warning(
                self, "FMP dat file not found", "Please check that FMP dat file exists"
            )
        else:
            nodes_layer = self.fmpNodesLayerCbox.currentLayer()
            cn_layer = self.cnLinesLayerCbox.currentLayer()
            dw_tol = self.dwToleranceSpinbox.value()

            self.statusLabel.setText('Comparing 1D-2D widths ...')
            QApplication.processEvents()
            
            try:
                self.statusLabel.setText('Loading FMP 1D widths ...')
                QApplication.processEvents()
                fmp_widths = self.width_check.fetchFmpWidths(dat_path)
                self.statusLabel.setText('Loading TUFLOW 2D widths ...')
                QApplication.processEvents()
                cn_widths, single_cn, total_found = self.width_check.fetchCnWidths(
                    nodes_layer, cn_layer
                )
                self.statusLabel.setText('Comparing 1D-2D widths ...')
                QApplication.processEvents()
                results, failed = self.width_check.checkWidths(
                    fmp_widths, cn_widths, single_cn, dw_tol
                )
            except (AttributeError, Exception) as e:
                QMessageBox.warning(
                    self, "Width check failed", e.args[0]
                )
            else:
                if len(failed['missing']) > 0 or len(failed['fail']) > 0 or len(failed['single_cn']) > 0:
                    self.statusLabel.setText('Check complete - Failed or missing nodes found')
                    self.updateFailedTable(failed)
                else:
                    self.statusLabel.setText('Check complete - All nodes passed')
                self.updateAllTable(results)

    def _buildRow(self, data, table_widget, row_position, status=None):
        """Create a table row and add it to the table.
        
        Args:
            data(dict): containing the value to place in the table row.
            table_widget(QTableWidget): the table to add the row to.
            row_position(int): the row count or position to add the row.
            status=None(str): if given an additional item will be added to
                the start of the row with the value given.
        """
        width_1d = '{:.2f}'.format(data['1d_width'])
        width_2d = '{:.2f}'.format(data['2d_width'])
        diff = '{:.2f}'.format(data['diff'])
        table_widget.insertRow(row_position)
        col = 0 
        if status is not None:
            table_widget.setItem(row_position, col, QTableWidgetItem(status))
            col += 1

        table_widget.setItem(row_position, col, QTableWidgetItem(data['id']))
        table_widget.setItem(row_position, col+1, QTableWidgetItem(data['type']))
        table_widget.setItem(row_position, col+2, QTableWidgetItem(diff))
        table_widget.setItem(row_position, col+3, QTableWidgetItem(width_1d))
        table_widget.setItem(row_position, col+4, QTableWidgetItem(width_2d))

    def updateFailedTable(self, results):
        """Update failed table with fail and missing values."""
        row_position = 0
        self.failedTableWidget.setRowCount(row_position)
        for f in results['fail']:
            self._buildRow(f, self.failedTableWidget, row_position, 'FAIL')
            row_position += 1
        for f in results['single_cn']:
            self._buildRow(f, self.failedTableWidget, row_position, 'SINGLE CN')
            row_position += 1
        for m in results['missing']:
            self._buildRow(m, self.failedTableWidget, row_position, 'NOT FOUND')
            row_position += 1
            
    def updateAllTable(self, results):
        """Update the 'all' table with all of the results."""
        row_position = 0
        self.allTableWidget.setRowCount(row_position)
        for r in results:
            self._buildRow(r, self.allTableWidget, row_position)
            row_position += 1
                
    def exportResults(self):
        """Export the results to csv.
        
        If the includeFailedCheckbox is checked an additional file will be
        created containing only the details of the failing sections.
        """
        include_failed = self.includeFailedCheckbox.isChecked()

        csv_file = mrt_settings.loadProjectSetting(
            'width_results', mrt_settings.loadProjectSetting(
                    'results_dir', mrt_settings.loadProjectSetting('working_dir', './temp')
            )
        )
        if os.path.isdir(csv_file):
            csv_file = os.path.join(csv_file, 'width_results.csv')
        filepath = QFileDialog(self).getSaveFileName(
            self, 'Export Results', csv_file, "CSV File (*.csv)"
        )[0]
        if filepath:
            mrt_settings.saveProjectSetting('width_results', csv_file)
            try:
                self.width_check.writeResults(filepath)
            except OSError as err:
                QMessageBox.warning(
                    self, "Results export failed", err.args[0] 
                )
                return

            if include_failed:
                root, filename = os.path.split(filepath)
                filename, ext = os.path.splitext(filename)
                filepath = os.path.join(root, filename + '_failed.csv')
                try:
                    self.width_check.writeFailed(filepath)
                except OSError as err:
                    QMessageBox.warning(
                        self, "Results export failed", err.args[0] 
                    )
            
        
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
                    result = check.loadSummaryInfo(ief)
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
                        item.setText(value[0])
                        self.fmpMultipleSummaryTable.setItem(row_position, i, item)
                    else:
                        self.fmpMultipleSummaryTable.setItem(row_position, i, QTableWidgetItem(value[0]))
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
            self.fmpVariablesTable.setItem(row_position, 0, QTableWidgetItem(variable))
            self.fmpVariablesTable.setItem(row_position, 1, item)
            self.fmpVariablesTable.setItem(row_position, 2, QTableWidgetItem(details['value']))
            self.fmpVariablesTable.setItem(row_position, 3, QTableWidgetItem(details['default']))
            self.fmpVariablesTable.setItem(row_position, 4, QTableWidgetItem(details['description']))
        

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
        for variable, details in variables.items():
            is_default = details['default'] == details['value']
            outputTableRow(details, is_default)
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

        
class FmpSectionCheckDialog(DialogBase, fmpsectioncheck_ui.Ui_FmpSectionPropertyCheckDialog):
   

    def __init__(self, dialog_name, iface, project):
        DialogBase.__init__(self, dialog_name, iface, project, 'Check FMP Sections')
        
        # Loaded section property details
        self.properties = None
        self.graph_toolbar = None
        
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
        self.graphics_view = graphs.SectionPropertiesGraphicsView()
#         self.resultsLayout.addWidget(self.graphics_view)
        self.graphLayout.addWidget(self.graphics_view)

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
        def showToolbar():
            if self.graph_toolbar is not None:
                self.graphLayout.removeWidget(self.graph_toolbar)
            self.graph_toolbar = NavigationToolbar(self.graphics_view.canvas, self)
            self.graphLayout.addWidget(self.graph_toolbar)

        if caller == 'conveyance':
            self.graphics_view.drawConveyancePlot(
                self.properties['negative_k'][node_id], node_id
            )
            showToolbar()
        elif caller == 'bad_banks':
            self.graphics_view.drawBanktopsPlot(
                self.properties['bad_banks'][node_id], node_id
            )
            showToolbar()
        
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
#         section_check = fmpsection_check.CheckFmpSections(working_dir, dat_path, k_tol, dy_tol)
        section_check = fmpsection_check.CheckFmpSections()
        try:
            self.statusLabel.setText("Loading FMP model river sections ...")
            QApplication.processEvents()
            river_sections = section_check.loadRiverSections(dat_path)
            self.statusLabel.setText("Calculating section conveyance ...")
            QApplication.processEvents()
            self.properties['negative_k'], self.properties['n_zero'] = section_check.calculateConveyance(
                river_sections, k_tol
            )
            self.statusLabel.setText("Checking bank elevations ...")
            QApplication.processEvents()
            self.properties['bad_banks'] = section_check.checkBankLocations(river_sections, dy_tol)
        except Exception as err:
            self.statusLabel.setText("FMP model load failed!")
            QMessageBox.warning(
                self, "FMP dat file load error", err.args[0]
            )
            
        if len(self.properties['n_zero']) > 0:
            msg = ["This error is probably caused by sections with '0' Manning's values."]
            msg.append("The following sections were affected\n")
            msg += self.properties['n_zero'] 
            QMessageBox.warning(
                self, "Zero Division Error",
                '\n'.join(msg)
            )
        
        self.statusLabel.setText("Populating tables ...")
        QApplication.processEvents()
        conveyance = self.properties['negative_k']
        row_position = 0
        self.negativeConveyanceTable.setRowCount(row_position)
        for name, details in conveyance.items():
            max_kx = '{:.2f}'.format(details['max_kx'])
            max_kx_depth = '{:.2f}'.format(details['max_kx_depth'])
            self.negativeConveyanceTable.insertRow(row_position)
            self.negativeConveyanceTable.setItem(row_position, 0, QTableWidgetItem(name))
            self.negativeConveyanceTable.setItem(row_position, 1, QTableWidgetItem(max_kx))
            self.negativeConveyanceTable.setItem(row_position, 2, QTableWidgetItem(max_kx_depth))
            row_position += 1

        bad_banks = self.properties['bad_banks']
        row_position = 0
        self.banktopCheckTable.setRowCount(row_position)
        for name, details in bad_banks.items():
            left_drop = 'FAIL: {:.2f} m'.format(details['left_drop']) if details['left_drop'] > 0 else 'PASS'
            right_drop = 'FAIL: {:.2f} m'.format(details['right_drop']) if details['right_drop'] > 0 else 'PASS'
            self.banktopCheckTable.insertRow(row_position)
            self.banktopCheckTable.setItem(row_position, 0, QTableWidgetItem(name))
            self.banktopCheckTable.setItem(row_position, 1, QTableWidgetItem(left_drop))
            self.banktopCheckTable.setItem(row_position, 2, QTableWidgetItem(right_drop))
            row_position += 1
        self.statusLabel.setText("Section check complete")


class FmpRefhCheckDialog(DialogBase, refh_ui.Ui_FmpRefhCheckDialog):
    
    def __init__(self, dialog_name, iface, project):

        DialogBase.__init__(self, dialog_name, iface, project, 'ReFH Check')
        
        self.csv_results = None
        
        model_path = mrt_settings.loadProjectSetting(
            'refh_file', self.project.readPath('./temp')
        )
        self.fmpFileWidget.setFilePath(model_path)

        self.fmpFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'refh_file'))
        self.fmpFileReloadBtn.clicked.connect(self.loadModelFile)
        self.csvExportBtn.clicked.connect(self.exportCsv)
        
    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        self.loadModelFile()
        
    def loadModelFile(self):
        model_path = mrt_settings.loadProjectSetting(
            'refh_file', self.project.readPath('./temp')
        )
        refh_compare = refhcheck.CompareFmpRefhUnits([model_path])
        try:
            self.csv_results, text_output, failed_paths, missing_refh = refh_compare.run_tool()
        except Exception as err:
            QMessageBox.warning(
                self, "FMP dat/ied file load failed", err.args[0]
            )
        self.formatTexbox(text_output, failed_paths, missing_refh)
        
    def formatTexbox(self, output, failed_paths, missing_refh):   

        self.refhOutputTextbox.clear()
        self.refhOutputTextbox.appendPlainText('\n'.join(output))

        # Highlight the values that are different in red
        cursor = self.refhOutputTextbox.textCursor()

        # Setup the desired format for matches
        text_format = QTextCharFormat()
        text_format.setBackground(QBrush(QColor("red")))

        # Setup the regex engine
        pattern = "!!!"
        regex = QRegExp(pattern)

        # Process the displayed document
        pos = 0
        index = regex.indexIn(self.refhOutputTextbox.toPlainText(), pos)
        while (index != -1):
            # Select the matched text and apply the desired text_format
            cursor.setPosition(index)
            cursor.movePosition(QTextCursor.EndOfWord, 1)
            cursor.mergeCharFormat(text_format)
            # Move to the next match
            pos = index + regex.matchedLength()
            index = regex.indexIn(self.refhOutputTextbox.toPlainText(), pos)
        
        msg = None
        if failed_paths:
            msg = ['The following files could not be audited:']
            for f in failed_paths:
                msg.append(f)
            msg = '\n'.join(msg)
        
        if missing_refh:
            if failed_paths: msg += '\n\n'
            msg = ['The following files contain no ReFH units:']
            for m in missing_refh:
                msg.append(m)
            msg = '\n'.join(msg)
        if msg is not None:
            msg += '\n\n'
            cursor.setPosition(0)
            self.refhOutputTextbox.insertPlainText(msg)
        self.refhOutputTextbox.moveCursor(cursor.Start)
        self.refhOutputTextbox.ensureCursorVisible()
            
    def exportCsv(self):
        if not self.csv_results:
            QMessageBox.warning(self, "Export Failed", "No results found: Please load model first")
            return
            
        csv_file = mrt_settings.loadProjectSetting(
            'csv_file', self.project.readPath('./temp')
        )

        filepath = QFileDialog(self).getSaveFileName(
            self, 'Export Results', csv_file, "CSV File (*.csv)"
        )
        if filepath[0]:
            mrt_settings.saveProjectSetting('csv_file', filepath[0])
            r = self.csv_results[0]
            with open(filepath[0], 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                for row in r:
                    out = row.strip('\n').split('\s')
                    writer.writerow(out)


class TuflowStabilityCheckDialog(DialogBase, tuflowstability_ui.Ui_TuflowStabilityCheckDialog):
    
    def __init__(self, dialog_name, iface, project):

        DialogBase.__init__(self, dialog_name, iface, project, 'Check TUFLOW MB')
        
        self.summary_results = []
        self.summary_mboptions = ['_MB']
        
        mb_file = mrt_settings.loadProjectSetting(
            'mb_file', self.project.readPath('./temp')
        )
        self.mbFileWidget.setStorageMode(QgsFileWidget.GetDirectory)
        self.mbFileWidget.setFilePath(os.path.dirname(mb_file))
        self.mbFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'mb_file'))
        self.mbReloadBtn.clicked.connect(self.findMbFiles)
        self.summaryTable.cellChanged.connect(self.summaryCellChanged)
        self.summaryTable.cellClicked.connect(self.summaryTableClicked)
        self.MBCheckbox.stateChanged.connect(self.summaryMbCheckChanged)
        self.MB2DCheckbox.stateChanged.connect(self.summaryMbCheckChanged)
        self.MB1DCheckbox.stateChanged.connect(self.summaryMbCheckChanged)

        self.summaryTable.setColumnWidth(0, 40)
        self.summaryTable.setColumnWidth(1, 70)
        self.summaryTable.setColumnWidth(2, 70)
        
    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        self.findMbFiles()
    
    def summaryMbCheckChanged(self):
        self.summary_mboptions = []
        if self.MBCheckbox.isChecked():
            self.summary_mboptions.append('_MB')
        if self.MB2DCheckbox.isChecked():
            self.summary_mboptions.append('_MB2D')
        if self.MB1DCheckbox.isChecked():
            self.summary_mboptions.append('_MB1D')
    
    def findMbFiles(self):
        mb_path = mrt_settings.loadProjectSetting(
            'mb_file', self.project.readPath('./temp')
        )
        self.summaryTable.setRowCount(0)
        mb_check = tmb_check.TuflowStabilityCheck()
        mb_files = mb_check.findMbFiles(mb_path, self.summary_mboptions)
        self.summary_results = mb_check.loadMultipleFiles(mb_files)
        if self.summary_results:
            self.summaryTable.blockSignals(True)
            self.updateSummaryTable()
            self.summaryTable.blockSignals(False)
            self.graphMultipleResults()
        else:
            QMessageBox.warning(
                self, "MB files not found", 
                "No TUFLOW MB, MB1D, or MB2D file were found within subfolders."
            )
        
#         self.graphResults(results)
    
    def loadMbFile(self):
        mb_path = mrt_settings.loadProjectSetting(
            'mb_file', self.project.readPath('./temp')
        )
        mb_check = tmb_check.TuflowStabilityCheck()
        results = mb_check.run_tool()
        self.graphResults(results)
        
    def summaryCellChanged(self, row, col):
        if col != 0: return
        item = self.summaryTable.item(row, col)
        check_state = item.checkState()
        if check_state == Qt.Checked:
            self.summary_results[row]['draw'] = True
        else:
            self.summary_results[row]['draw'] = False
        self.graphMultipleResults()
            
    def summaryTableClicked(self, row, col):
        if col == 0: return
        for i, r in enumerate(self.summary_results):
            self.summary_results[i]['color'] = '-r'
        self.summary_results[row]['color'] = '-b'
        self.graphMultipleResults()
        
    def updateSummaryTable(self):
        row_position = 0
        self.summaryTable.setRowCount(0)
        for i, r in enumerate(self.summary_results):
            self.summary_results[i]['color'] = '-r'
            self.summary_results[i]['draw'] = True
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check_item.setCheckState(Qt.Checked)       
            
            self.summaryTable.insertRow(row_position)
            self.summaryTable.setItem(row_position, 0, check_item)
            self.summaryTable.setItem(row_position, 1, QTableWidgetItem(str(r['fail'])))
            self.summaryTable.setItem(row_position, 2, QTableWidgetItem(str(r['max_mb'])))
            self.summaryTable.setItem(row_position, 3, QTableWidgetItem(r['name']))
            self.summaryTable.setItem(row_position, 4, QTableWidgetItem(r['path']))
            row_position += 1

    def graphMultipleResults(self):
    
        scene = QGraphicsScene()
        view = self.summaryGraphicsView.setScene(scene)
        fig = Figure()
        axes = fig.gca()
        
        x = self.summary_results[0]['data']['Time (h)']
        
#         axes.set_title(self.title)
        axes.set_ylabel('CME (%)', color='r')
        axes.set_xlabel('Time (h)')
        
        cme_min = [1 for i in x]
        cme_max = [-1 for i in x]

        mb_max_plot = axes.plot(x, cme_min, "-g", alpha=0.5, label="CME max recommended", dashes=[6,2])
        mb_min_plot = axes.plot(x, cme_max, "-g", alpha=0.5, label="CME min recommended", dashes=[6,2])

        for r in self.summary_results:
            if r['draw']:
                cme = r['data']['Cum ME (%)']
                plot_color = r['color']
                mb_plot = axes.plot(x, cme, plot_color, label="CME")

        plot_lines = mb_max_plot
        labels = [l.get_label() for l in plot_lines]
        axes.legend(plot_lines, labels, loc='lower right')

        axes.grid(True)
        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)
        
    def graphResults(self, results):
    
        scene = QGraphicsScene()
        view = self.mbGraphicsView.setScene(scene)
        fig = Figure()
        axes = fig.gca()
        
        x = results['time']
        cme = results['cme']
        dvol = results['dvol']
        
#         axes.set_title(self.title)
        axes.set_ylabel('CME (%)', color='r')
        axes.set_xlabel('Time (h)')
        
        cme_min = [1 for i in x]
        cme_max = [-1 for i in x]

        mb_plot = axes.plot(x, cme, "-r", label="CME")
        mb_max_plot = axes.plot(x, cme_min, "-g", alpha=0.5, label="CME max recommended", dashes=[6,2])
        mb_min_plot = axes.plot(x, cme_max, "-g", alpha=0.5, label="CME min recommended", dashes=[6,2])

        axes2 = axes.twinx()
        dvol_plot = axes2.plot(x, dvol, "-b", label="dVol")
        axes2.set_ylabel('dVol (m3/s/s)', color='b')
        
        plot_lines = mb_max_plot
        labels = [l.get_label() for l in plot_lines]
        axes.legend(plot_lines, labels, loc='lower right')

        axes.grid(True)
        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)


class NrfaStationViewerDialog(DialogBase, nrfa_ui.Ui_NrfaViewerDialog):
    """Dialog for selecting and viewing NRFA station information.
    
    Identify nearby NRFA stations and view the station information,
    AMAX, POT and daily flows data for the selected station.
    """
    
    TOOL_NAME = 'nrfa_viewer'
    TOOL_DATA = os.path.join(DATA_DIR, TOOL_NAME)
    NRFA_STATIONS = os.path.join(TOOL_DATA, 'NRFA_Station_Info.shp')

    def __init__(self, dialog_name, iface, project):
        DialogBase.__init__(self, dialog_name, iface, project, 'NRFA Station Viewer')
        
        self.do_dailyflow_update = False
        
        self.workingDirFileWidget.setStorageMode(QgsFileWidget.GetDirectory)
        self.nrfa_stations = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            NrfaStationViewerDialog.NRFA_STATIONS
        )

        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        distance = mrt_settings.loadProjectSetting('nrfa_max_distance', 15)

        self.workingDirFileWidget.setFilePath(working_dir)
        self.maxDistanceSpinbox.setValue(distance)
        self.workingDirFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'working_directory'))
        self.maxDistanceSpinbox.valueChanged.connect(self.maxDistanceChanged)
        self.fetchStationsBtn.clicked.connect(self.fetchStations)
        self.stationNamesCbox.currentIndexChanged.connect(self.showStationInfo)
        self.buttonBox.clicked.connect(self.signalClose)
        self.stationTabWidget.currentChanged.connect(self.stationTabChanged)
        self.showAmaxGraphBtn.clicked.connect(self.graphAmax)
        self.exportAmaxCsvBtn.clicked.connect(self.exportAmaxCsv)
        self.showPotGraphBtn.clicked.connect(self.graphPot)
        self.exportPotCsvBtn.clicked.connect(self.exportPotCsv)
        self.showDailyFlowsGraphBtn.clicked.connect(self.graphDailyFlows)
        self.exportDailyFlowsCsvBtn.clicked.connect(self.exportDailyFlowsCsv)
        self.dailyFlowsYearCbox.currentTextChanged.connect(self.updateDailyFlowsTable)
        
        self.nrfa_viewer = nrfa_viewer.NrfaViewer(self.project, self.iface)
        
    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        
    def maxDistanceChanged(self, value):
        mrt_settings.saveProjectSetting('nrfa_max_distance', value)
        
    def stationTabChanged(self, index):
        if index == 0:
            pass
        elif index == 1:
            self.loadAdditionalInfo()
        elif index == 2:
            self.loadAmaxData()
        elif index == 3:
            self.loadPotData()
        elif index == 4:
            self.loadDailyFlowsData()
        
    def fetchStations(self):
        """Locate all NRFA stations within a radius of the map canvas center.
        
        Calls the self.nrfa_viewer.fetchStations() function to create a memory
        layer containing the point location and IDs of NRFA stations that are
        within the user supplied radius of the map canvas center.
        Supplies the function with a pre-compiled point layer (in the data
        folder) containing summary information about NRFA stations in the UK.
        
        Displays the ID and station name for all selected stations in the 
        station selection combobox and updates the station info tab with the
        details of the default selected station.
        """
        nrfa_layer = QgsVectorLayer(self.nrfa_stations, "nrfa_stations", "ogr")
        if not nrfa_layer.isValid():
            QMessageBox.warning(
                self, "Unable to load NRFA layer", 
                "NRFA Station info layer could not be loaded, please reimport the data."
            )
            return
        
        self.statusLabel.setText("Loading NRFA stations ...")
        search_radius = self.maxDistanceSpinbox.value() * 1000
        stations = self.nrfa_viewer.fetchStations(nrfa_layer, search_radius)
        
        self.stationNamesCbox.clear()
        if not stations:
            QMessageBox.information(
                self, "No NRFA station found in given radius", 
                "There are no NRFA stations in the given radius. Try increasing the distance."
            )
        else:
            self.stationNamesCbox.blockSignals(True)
            for s in stations:
                self.stationNamesCbox.addItem(s)
            self.stationNamesCbox.blockSignals(False)
            self.showStationInfo()
            self.stationInfoGroupbox.setEnabled(True)

    def showStationInfo(self, *args): 
        """Show the summary infomation about the selected NRFA station.

        Calls the self.nrfa_viewer function to retrieve the summary information
        for the currently selected NRFA station and displays it on the "Station Info"
        tab. These are just some key details about the station.
        """
        self.statusLabel.setText("Updating NRFA station info ...")
        self.stationTabWidget.setCurrentIndex(0)
        self.stationInfoTextbox.clear()
        text = self.stationNamesCbox.currentText()
        if text == '': 
            return
        station_id, station_name = text.split(')')
        station_id = int(station_id[1:])
        station_name = station_name.strip()
        
        output = self.nrfa_viewer.fetchStationSummary(station_id)
        self.stationInfoTextbox.append('\n'.join(output)) 
        self.statusLabel.setText("Station info updated")
        
    def loadAdditionalInfo(self):
        """Displays all the NRFA information availble for this station.
        
        Calls the API request function in self.nrfa_viewer to fetch all of the 
        metadata available for this NRFA station. The details are then displayed
        in a textedit on the "Full Details" tab.
        """
        try:
            output = self.nrfa_viewer.fetchStationData()
        except ConnectionError as err:
            QMessageBox.warning(
                self, "NRFA API connection failed", err.args[0]
            )
        self.fullDetailsTextbox.clear()
        self.fullDetailsTextbox.append(output)
        self.fullDetailsTextbox.moveCursor(self.fullDetailsTextbox.textCursor().Start)
        self.fullDetailsTextbox.ensureCursorVisible()

    def loadAmaxData(self):
        """Load the AMAX (Annual Maximum) data.

        Call the API request function in self.nrfa_viewer to fetch the data. Updates
        the summary metadata and table with the loaded data for the currently selected
        NRFA station.
        """
        try:
            metadata, series = self.nrfa_viewer.fetchAmaxData()
        except ConnectionError as err:
            QMessageBox.warning(
                self, "NRFA API connection failed", err.args[0]
            )
        self.amaxSummaryTextbox.clear()
        self.amaxSummaryTextbox.append('\n'.join(metadata))
        self.amaxSummaryTextbox.moveCursor(self.amaxSummaryTextbox.textCursor().Start)
        self.amaxSummaryTextbox.ensureCursorVisible()
        
        row_position = 0
        self.amaxResultsTable.setRowCount(row_position)
        for s in series:
            flow = '{:.2f}'.format(s['flow'])
            self.amaxResultsTable.insertRow(row_position)
            self.amaxResultsTable.setItem(row_position, 0, QTableWidgetItem(flow))
            self.amaxResultsTable.setItem(row_position, 1, QTableWidgetItem(s['datetime']))
            row_position += 1

    def loadPotData(self):
        """Load the POT (Peaks over threshold) data.

        Call the API request function in self.nrfa_viewer to fetch the data. Updates
        the summary metadata and table with the loaded data for the currently selected
        NRFA station.
        """
        try:
            metadata, series = self.nrfa_viewer.fetchPotData()
        except ConnectionError as err:
            QMessageBox.warning(
                self, "NRFA API connection failed", err.args[0]
            )
        self.potSummaryTextbox.clear()
        self.potSummaryTextbox.append('\n'.join(metadata))
        self.potSummaryTextbox.moveCursor(self.potSummaryTextbox.textCursor().Start)
        self.potSummaryTextbox.ensureCursorVisible()
        
        row_position = 0
        self.potResultsTable.setRowCount(row_position)
        for s in series:
            flow = '{:.2f}'.format(s['flow'])
            self.potResultsTable.insertRow(row_position)
            self.potResultsTable.setItem(row_position, 0, QTableWidgetItem(flow))
            self.potResultsTable.setItem(row_position, 1, QTableWidgetItem(s['datetime']))
            row_position += 1
            
    def loadDailyFlowsData(self):
        """Load Daily Flow Data.
        
        Call the API request function in self.nrfa_viewer to fetch the data. The
        data is separated into years with the most recent year being the default.
        Populates the years combobox, sets the current item to the most recent 
        year and calls the updateDailyFlowsTable() function to add year data to 
        the table.
        """
        try:
            metadata, series, latest_year = self.nrfa_viewer.fetchDailyFlowsData()
        except ConnectionError as err:
            QMessageBox.warning(
                self, "NRFA API connection failed", err.args[0]
            )
        if latest_year == -1:
            return

        self.dailyFlowsYearCbox.blockSignals(True)
        self.cur_dailyflow_year = latest_year
        self.dailyFlowsYearCbox.clear()
        for year in series.keys():
            self.dailyFlowsYearCbox.addItem(str(year))
        self.dailyFlowsYearCbox.blockSignals(False)
        self.dailyFlowsYearCbox.setCurrentText(str(latest_year))
        self.updateDailyFlowsTable(str(latest_year))
            
    def updateDailyFlowsTable(self, year):
        """Update the contents of the daily flows table to the given year.
        
        Args:
            year(str/int): the year to update the table to.
        
        Except:
            AttributeError: if year does not exist in the daily flows dataset.
        """
        year = int(year)
        if not year in self.nrfa_viewer.daily_flows_series.keys():
            return
        self.cur_dailyflow_year = year
        row_position = 0
        self.dailyFlowsTable.setRowCount(row_position)
        for s in self.nrfa_viewer.daily_flows_series[year]:
            flow = '{:.2f}'.format(s['flow'])
            self.dailyFlowsTable.insertRow(row_position)
            self.dailyFlowsTable.setItem(row_position, 0, QTableWidgetItem(str(year)))
            self.dailyFlowsTable.setItem(row_position, 1, QTableWidgetItem(s['date']))
            self.dailyFlowsTable.setItem(row_position, 2, QTableWidgetItem(flow))
            self.dailyFlowsTable.setItem(row_position, 3, QTableWidgetItem(s['flag']))
            row_position += 1
            
    def graphAmax(self):
        """Graph AMAX data."""
        dlg = graphs.AmaxGraphDialog()
        dlg.setupGraph(self.nrfa_viewer.amax_series, self.nrfa_viewer.cur_station)
        dlg.exec_()
    
    def graphPot(self):
        """Graph POT data."""
        dlg = graphs.PotGraphDialog()
        dlg.setupGraph(self.nrfa_viewer.pot_series, self.nrfa_viewer.cur_station)
        dlg.exec_()
    
    def graphDailyFlows(self):
        """Graph Daily Flows data."""
        series_year = self.cur_dailyflow_year
        series = self.nrfa_viewer.daily_flows_series[series_year]
        dlg = graphs.DailyFlowsGraphDialog()
        dlg.setupGraph(series, self.nrfa_viewer.cur_station, series_year)
        dlg.exec_()
        
    def exportData(self, data_name, export_func, **kwargs):
        """Export NRFA data to csv format.
        
        Args:
            data_name(str): the name to use for dialogs and default filename.
            export_func(func): csv writing function to call.
        
        **kwargs:
            default_filename(str): str to use as a default filename if the 
                standard '{station id}_{data_name} format isn't wanted.
                (This will be removed prior to passing kwargs to export_func).
        """
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        default_filename = kwargs.pop(
            'default_filename',
            '{0}_{1}.csv'.format(self.nrfa_viewer.cur_station['id'], data_name)
        )
        default_name = os.path.join(working_dir, default_filename)
        filename = QFileDialog(self).getSaveFileName(
            self, 'Export {0}'.format(data_name), default_name, "CSV File (*.csv)"
        )[0]
        if filename:
            try:
                export_func(filename, **kwargs)
            except ValueError as err:
                QMessageBox.warning(
                    self, "No {0} loaded".format(data_name), err.args[0]
                )
            except Exception as err:
                QMessageBox.warning(
                    self, "Failed to write {0} ".format(data_name), err.args[0]
                )
    
    def exportAmaxCsv(self):
        self.exportData('AMAX_Data', self.nrfa_viewer.exportAmaxData)

    def exportPotCsv(self):
        self.exportData('POT_Data', self.nrfa_viewer.exportPotData)

    def exportDailyFlowsCsv(self):
        export_type = self.dailyFlowExportTypeCbox.currentIndex()
        export_year = self.cur_dailyflow_year if export_type == 0 else None
        func_kwargs = {'export_year': export_year}
        if export_year is not None:
            func_kwargs['default_filename'] = '{0}_DailyFlows_Data_{1}'.format(
                self.nrfa_viewer.cur_station['id'], export_year
            )
        self.exportData(
            'Daily_Flows_Data', self.nrfa_viewer.exportDailyFlowsData, **func_kwargs
        )
        

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
        self.elsewhereFilesTable.clicked.connect(lambda i: self.showParents(i, 'elsewhere'))
        self.iefElsewhereFilesTable.clicked.connect(lambda i: self.showParents(i, 'ief'))
        self.missingFilesTable.clicked.connect(lambda i: self.showParents(i, 'missing'))
        self.elsewhereParentList.currentRowChanged.connect(lambda i: self.showParentFile(i, 'elsewhere'))
        self.iefElsewhereParentList.currentRowChanged.connect(lambda i: self.showParentFile(i, 'ief'))
        self.missingParentList.currentRowChanged.connect(lambda i: self.showParentFile(i, 'missing'))

        self.search_results = None
        self.file_check = filecheck.FileChecker()
        self.file_check.status_signal.connect(self.updateStatus)
        
    def updateModelRoot(self):
        mrt_settings.saveProjectSetting('model_root', self.modelFolderFileWidget.filePath())
        self.checkFiles()
        
    @pyqtSlot(str)
    def updateStatus(self, status):
        self.statusLabel.setText(status)
        QApplication.processEvents()
        
    def checkFiles(self):
        self.search_results = None
        self.missingParentList.clear()
        self.elsewhereParentList.clear()
        self.iefElsewhereParentList.clear()
        model_root = mrt_settings.loadProjectSetting('model_root', './temp')
        self.search_results = self.file_check.auditModelFiles(model_root)
        self.resultsTabWidget.setCurrentIndex(0)
        self.updateSummaryTab()
        self.updateElsewhereTable(self.elsewhereFilesTable, self.search_results.results['found'])
        self.updateElsewhereTable(self.iefElsewhereFilesTable, self.search_results.results['found_ief'])
        self.updateMissingTable(self.search_results.results['missing'])
        
    def updateSummaryTab(self):
        output = ['File search summary\n'.upper()]
        output.append(self.search_results.summaryText())
        output.append('\n\nFiles that were ignored\n'.upper())
        output += [f.filepath for f in self.search_results.results_meta['ignored']]
        output.append('\n\nModel files reviewed\n'.upper())
        output += self.search_results.results_meta['checked']
        output = '\n'.join(output)
        self.summaryTextEdit.clear()
        self.summaryTextEdit.setText(output)
                
    def updateMissingTable(self, missing_files):
        row_position = 0
        self.missingFilesTable.setRowCount(row_position)
        for missing in missing_files:
            self.missingFilesTable.insertRow(row_position)
            self.missingFilesTable.setItem(row_position, 0, QTableWidgetItem(missing['file'][0]))
            self.missingFilesTable.setItem(row_position, 1, QTableWidgetItem(missing['file'][1]))
            row_position += 1

    def updateElsewhereTable(self, table, file_list):
        row_position = 0
        table.setRowCount(row_position)
        for found in file_list:
            table.insertRow(row_position)
            table.setItem(row_position, 0, QTableWidgetItem(found['file'][0]))
            table.setItem(row_position, 1, QTableWidgetItem(found['file'][1]))
            table.setItem(row_position, 2, QTableWidgetItem(found['file'][2]))
            row_position += 1

    def showParents(self, row, tab_name):
        if tab_name == 'elsewhere':
            the_table = self.elsewhereFilesTable
            the_list = self.elsewhereParentList
            parents = self.search_results.results['found'][the_table.currentRow()]['parents']
        elif tab_name == 'ief':
            the_table = self.iefElsewhereFilesTable
            the_list = self.iefElsewhereParentList
            parents = self.search_results.results['found_ief'][the_table.currentRow()]['parents']
        elif tab_name == 'missing':
            the_table = self.missingFilesTable
            the_list = self.missingParentList
            parents = self.search_results.results['missing'][the_table.currentRow()]['parents']
        else:
            return

        the_list.clear()
        for p in parents:
            filename = os.path.split(p[0])[1]
            line = '{0} (line {1}) :\t {2}'.format(filename, p[1], p[0])
            the_list.addItem(line)

    def showParentFile(self, row, tab_name):
        if row == -1: return
        
        if tab_name == 'elsewhere':
            the_table = self.elsewhereFilesTable
            table_row = the_table.currentRow()
            parents = self.search_results.results['found'][table_row]['parents']
        elif tab_name == 'ief':
            the_table = self.iefElsewhereFilesTable
            table_row = the_table.currentRow()
            parents = self.search_results.results['found_ief'][table_row]['parents']
        elif tab_name == 'missing':
            the_table = self.missingFilesTable
            table_row = the_table.currentRow()
            parents = self.search_results.results['missing'][table_row]['parents']
        else:
            return
        
        filename = the_table.item(table_row, 0).text()
        parent_file = parents[row][0]
        contents = []
        try:
            with open(parent_file, 'r') as pf:
                for line in pf.readlines():
                    contents.append(line)
        except OSError as err:
            QMessageBox.warning(
                self, "Failed to open file {0} ".format(filename), err.args[0]
            )
        dlg = graphs.ModelFileDialog(filename)
        dlg.showText(''.join(contents), filename)
        dlg.exec_()
    
    def exportResults(self):
        if self.search_results is None:
            QMessageBox.warning(
                self, "No results loaded", "There are no results loaded. Please run the check first."
            )
            return
        save_folder = mrt_settings.loadProjectSetting('model_root', './temp')
        default_path = os.path.join(save_folder, 'filecheck_results.txt')
        filepath = QFileDialog(self).getSaveFileName(
            self, 'Export Results', default_path, "TXT File (*.txt)"
        )[0]
        if filepath:
            mrt_settings.saveProjectSetting('file_check_results', filepath)
            try:
                self.search_results.exportResults(filepath)
            except OSError as err:
                QMessageBox.warning(
                    self, "Results export failed", err.args[0] 
                )
                return


class HelpPageDialog(QDialog, help_ui.Ui_HelpDialog):
    """Display the plugin help page dialog."""

    def __init__(self, iface, project):
        QDialog.__init__(self)
        self.iface = iface
        self.project = project
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        
        self.help = help.ModCheckHelp()
        self.setupHelpList()
        self.helpSelectList.currentTextChanged.connect(self.changeHelpPage)
        
    def setupHelpList(self):
        self.helpSelectList.clear()
        help_items = self.help.helpList()
        for item in help_items:
            self.helpSelectList.addItem(item)
        
    def changeHelpPage(self, tool_name):
        contents = self.help.helpContents(tool_name)
        self.helpDisplayTextBrowser.setText(contents)
        
        
        