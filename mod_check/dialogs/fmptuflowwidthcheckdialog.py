
import os
import csv
# from pathlib import Path
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget

from .dialogbase import DialogBase
from ..forms import ui_fmptuflow_widthcheck_dialog as fmptuflowwidthcheck_ui
from ..tools import help, globaltools
from ..tools import widthcheck
from ..tools import settings as mrt_settings

# DATA_DIR = './data'
# TEMP_DIR = './temp'

class FmpTuflowWidthCheckDialog(DialogBase, fmptuflowwidthcheck_ui.Ui_FmpTuflowWidthCheckDialog):
    """Compare FMP and TUFLOW model sections widths.

    Find the active section widths from the FMP model and compare them to the TUFLOW
    model.
    """

    def __init__(self, dialog_name, iface, project):
        DialogBase.__init__(self, dialog_name, iface, project, 'Check Width')

        self.width_check = widthcheck.SectionWidthCheck(self.project)
        self.width_check.status_signal.connect(self._updateStatus)

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
        
    def _updateStatus(self, status):
        self.statusLabel.setText(status)
        QApplication.processEvents()

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