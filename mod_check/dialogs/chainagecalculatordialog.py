
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

from .dialogbase import DialogBase
from ..forms import ui_chainage_calculator_dialog as chaincalc_ui
from ..tools import help, globaltools
from ..tools import chainagecalculator as chain_calc
from ..tools import settings as mrt_settings

# DATA_DIR = './data'
# TEMP_DIR = './temp'



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
            # use_fname = {'tested': False, 'failed': True}
            tested_fname = False
            f_lookup = 'ID'
            for f in nwk_layer.getFeatures():
                if not tested_fname:
                    try:
                        f['ID'] == id
                    except KeyError:
                        f_lookup = 0
                    tested_fname = True

                if f[f_lookup] == id:
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

        self.tuflowTotalChainageLabel.setText('Total Tuflow Chainage:')
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
        if nwk_layer is None:
            QMessageBox.warning(
                self, "No 1d_nwk Layer Provider", "Please select a 1d_nwk layer or choose FMP only"
            )
            return

        dx_tol = self.dxToleranceSpinbox.value()
        self.statusLabel.setText('Calculating FMP chainage (1/3) ...')
        QApplication.processEvents()
        fmp_chainage, reach_chainage = self.chainage_calculator.fmpChainage(dat_path)
        self.statusLabel.setText('Calculating TUFLOW nwk line chainage (2/3) ...')
        QApplication.processEvents()
        tuflow_chainage, total_tuflow_chainage = self.chainage_calculator.tuflowChainage(nwk_layer)
        self.statusLabel.setText('Comparing FMP-TUFLOW chainage (3/3) ...')
        QApplication.processEvents()
        chainage_compare = self.chainage_calculator.compareChainage(
            fmp_chainage, tuflow_chainage, dx_tol
        )
        self.statusLabel.setText('Chainage compare complete')

        self._showFmpChainageResults(fmp_chainage, reach_chainage)
        self._showCompareChainageResults(chainage_compare, total_tuflow_chainage)
        self.outputsTabWidget.setCurrentIndex(1)

    def _showFmpChainageResults(self, unit_chainage, reach_chainage):
        """Populate the FMP chainage tables with the results."""
        
        total_chainage = '{:.2f}'.format((unit_chainage[-1]['cum_total_chainage'] / 1000))
        self.fmpTotalChainageLabel.setText(f'Total FMP Chainage: {total_chainage} km')
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

    def _showCompareChainageResults(self, chainage_compare, total_tuflow_chainage):
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

        total_chainage = '{:.2f}'.format(total_tuflow_chainage / 1000)
        self.tuflowTotalChainageLabel.setText(f'Total Tuflow Chainage: {total_chainage} km')

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