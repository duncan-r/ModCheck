

import os
import csv
from datetime import datetime
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import dates as mdates
from matplotlib.dates import DateFormatter
import numpy as np

# import pyqtgraph as pg

from .forms import ui_chainage_calculator_dialog as chaincalc_ui
from .forms import ui_fmptuflow_widthcheck_dialog as fmptuflowwidthcheck_ui
from .forms import ui_runvariables_check_dialog as fmptuflowvariablescheck_ui
from .forms import ui_fmpsectionproperty_check_dialog as fmpsectioncheck_ui
from .forms import ui_graph_dialog as graph_ui
from .forms import ui_fmprefh_check_dialog as refh_ui
from .forms import ui_tuflowstability_check_dialog as tuflowstability_ui
from .forms import ui_nrfa_viewer_dialog as nrfa_ui
from .forms import ui_pyqtgraph_dialog as pyqtgraph_ui

from .tools import chainagecalculator as chain_calc
from .tools import fmptuflowwidthcheck as fmptuflow_widthcheck
from .tools import runvariablescheck as runvariables_check
from .tools import fmpsectioncheck as fmpsection_check
from .tools import refhcheck
from .tools import tuflowstabilitycheck as tmb_check
from .tools import nrfaviewer as nrfa_viewer
from .tools import settings as mrt_settings

class ChainageCalculatorDialog(QDialog, chaincalc_ui.Ui_ChainageCalculator):
    
    def __init__(self, iface, project):
        QDialog.__init__(self)
        self.iface = iface
        self.project = project
        self.setupUi(self)
        
        self.workingDirFileWidget.setStorageMode(QgsFileWidget.GetDirectory)
        
        # Connect the slots
        self.calcFmpChainageOnlyBtn.clicked.connect(self.calculateFmpOnlyChainage)
        self.compareChainageBtn.clicked.connect(self.compareEstryFmpChainage)
        self.fmpOnlyCheckbox.stateChanged.connect(self.compareFmpOnlyChange)
        
        # Load existing settings
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./temp')
        )
        chainage_results = mrt_settings.loadProjectSetting(
            'chainage_results', self.project.readPath('./temp')
        )
        # Connect file widgets and update slots
        self.workingDirFileWidget.setFilePath(working_dir)
        self.datFileWidget.setFilePath(dat_path)
        self.workingDirFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'working_directory'))
        self.datFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'dat_file'))
        
        # Populate estry nwk layer combo (line layers only)
        self.estryNwkLayerCBox.setFilters(QgsMapLayerProxyModel.LineLayer)
        
    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        
    def compareFmpOnlyChange(self, *args):
        if self.fmpOnlyCheckbox.isChecked():
            self.calcFmpChainageOnlyBtn.setEnabled(True)
            self.tuflowInputsGroupbox.setEnabled(False)
        else:
            self.calcFmpChainageOnlyBtn.setEnabled(False)
            self.tuflowInputsGroupbox.setEnabled(True)
            
    def calculateFmpOnlyChainage(self):
        """
        """
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./temp')
        )
        if working_dir is None or dat_path is None:
            self.loggingTextedit.appendPlainText("Please set working directory and FMP dat path first")
        elif not os.path.isdir(working_dir) or not os.path.exists(dat_path):
            self.loggingTextedit.appendPlainText("Please make sure working directory and FMP dat paths exist")
        else:
            self.loggingTextedit.clear()
            self.loggingTextedit.appendPlainText("Calculating FMP Chainage...")
            fmp_chainage = chain_calc.FmpChainageCalculator(working_dir, dat_path)
            fmp_chainage.run_tool()
            self.loggingTextedit.appendPlainText("FMP Chainage calculation complete\n")
            self.loggingTextedit.appendPlainText("Results saved to:")
            self.loggingTextedit.appendPlainText(working_dir)
            
    def compareEstryFmpChainage(self):
        """
        """
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./temp')
        )
        
        nwk_layer = self.estryNwkLayerCBox.currentLayer()
        dx_tol = self.dxToleranceSpinbox.value()
        
        chain_compare = chain_calc.CompareFmpTuflowChainage(
            working_dir, dat_path, nwk_layer, dx_tol
        )
        problem_nodes, save_path = chain_compare.run_tool()
                
        self.loggingTextedit.clear()
        self.loggingTextedit.appendPlainText("\nUsing .dat file:\n" + dat_path)
        self.loggingTextedit.appendPlainText("\nUsing nwk layer:\n" + nwk_layer.name())
        self.loggingTextedit.appendPlainText("")

        self.loggingTextedit.appendPlainText("\nNwk compare complete...")
        self.loggingTextedit.appendPlainText("\nFMP/nwk chainage greater than tolerance ({}m):".format(dx_tol))
        self.loggingTextedit.appendPlainText('\n'.join(problem_nodes['mismatch']))
        self.loggingTextedit.appendPlainText("\nFMP nodes not found in nwk layer:")
        self.loggingTextedit.appendPlainText('\n'.join(problem_nodes['no_nwk']))
        
        self.loggingTextedit.appendPlainText("\nResults output to:")
        self.loggingTextedit.appendPlainText(save_path)


class FmpTuflowWidthCheckDialog(QDialog, fmptuflowwidthcheck_ui.Ui_FmpTuflowWidthCheckDialog):
    
    def __init__(self, iface, project):
        QDialog.__init__(self)
        self.iface = iface
        self.project = project
        self.setupUi(self)

        self.workingDirFileWidget.setStorageMode(QgsFileWidget.GetDirectory)
        
        # Load existing settings
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./')
        )
        
        # Connect the slots
        self.checkWidthsBtn.clicked.connect(self.checkWidths)
        self.workingDirFileWidget.setFilePath(working_dir)
        self.datFileWidget.setFilePath(dat_path)
        self.workingDirFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'working_directory'))
        self.datFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'dat_file'))
        
        # Populate estry nwk layer combo (line layers only)
        self.fmpNodesLayerCbox.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.cnLinesLayerCbox.setFilters(QgsMapLayerProxyModel.LineLayer)

    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
            
    def checkWidths(self):
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./')
        )
        if working_dir is None or dat_path is None:
            self.loggingTextedit.appendPlainText("Please set working directory and FMP dat path first")
        elif not os.path.isdir(working_dir) or not os.path.exists(dat_path):
            self.loggingTextedit.appendPlainText("Please make sure working directory and FMP dat paths exist")
        else:
            nodes_layer = self.fmpNodesLayerCbox.currentLayer()
            cn_layer = self.cnLinesLayerCbox.currentLayer()
            dw_tol = self.dwToleranceSpinbox.value()

            self.loggingTextedit.clear()
            self.loggingTextedit.appendPlainText("Using .dat file:\n" + dat_path)
            self.loggingTextedit.appendPlainText("\nUsing nodes layer:\n" + nodes_layer.name())
            self.loggingTextedit.appendPlainText("\nUsing CN layer:\n" + cn_layer.name())
            self.loggingTextedit.appendPlainText("\nWidth diffference (DW) Tolerance = {}m".format(dw_tol))
            self.loggingTextedit.appendPlainText("\nComparing 1D-2D widths...")
            self.loggingTextedit.repaint()
            
            width_check = fmptuflow_widthcheck.FmpTuflowSectionWidthCheck(
                self.project, working_dir, dat_path, nodes_layer, 
                cn_layer, dw_tol
            )
            try:
                missing_nodes, failed = width_check.run_tool()
            except AttributeError as e:
                self.iface.messageBar().pushWarning("Width Check", e.args[0])
            except Exception as e:
                self.iface.messageBar().pushWarning("Width Check", e.args[0])
            else:
                self.loggingTextedit.appendPlainText("")
                self.loggingTextedit.appendPlainText("FMP nodes missing from 2D:")
                if len(missing_nodes) > 0:
                    self.loggingTextedit.appendPlainText('\n'.join(missing_nodes))
                else:
                    self.loggingTextedit.appendPlainText('No missing nodes found\n')

                self.loggingTextedit.appendPlainText(
                    "Nodes with width difference greater than tolerance (+-{}m):".format(dw_tol)
                )
                if len(failed) > 0:
                    self.loggingTextedit.appendPlainText("\n".join(failed))
                else:
                    self.loggingTextedit.appendPlainText("No failed nodes found\n")
                
                self.loggingTextedit.appendPlainText("\nWriting results to working dir...")
                save_location = width_check.write_results()
                self.loggingTextedit.appendPlainText("Results output to:")
                self.loggingTextedit.appendPlainText(save_location)
        
        
class FmpTuflowVariablesCheckDialog(QDialog, fmptuflowvariablescheck_ui.Ui_FmpTuflowVariablesCheckDialog):
    
    def __init__(self, iface, project):
        QDialog.__init__(self)
        self.iface = iface
        self.project = project
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        
        tlf_path = mrt_settings.loadProjectSetting(
            'tlf_file', self.project.readPath('./temp')
        )
        ief_path = mrt_settings.loadProjectSetting(
            'ief_file', self.project.readPath('./temp')
        )
        zzd_path = mrt_settings.loadProjectSetting(
            'zzd_file', self.project.readPath('./temp')
        )
        
        # Connect the slots
        self.iefTableRefreshBtn.clicked.connect(self.loadIefVariables)
        self.zzdTableRefreshBtn.clicked.connect(self.loadZzdResults)
        self.tlfTableRefreshBtn.clicked.connect(self.loadTlfDetails)
        self.iefFileWidget.setFilePath(ief_path)
        self.zzdFileWidget.setFilePath(zzd_path)
        self.tlfFileWidget.setFilePath(tlf_path)
        self.iefFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'ief_file'))
        self.zzdFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'zzd_file'))
        self.tlfFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'tlf_file'))

    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        
        if caller == 'ief_file':
            self.loadIefVariables()
        if caller == 'zzd_file':
            self.loadZzdResults()
        elif caller == 'tlf_file':
            self.loadTlfDetails()

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
        file_paths, variables = variables_check.run_tool()
        
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
        diagnostics, warnings = zzd_check.run_tool()
        
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

        tlf_path = mrt_settings.loadProjectSetting(
            'tlf_file', self.project.readPath('./temp')
        )
        variables_check = runvariables_check.TlfDetailsCheck(self.project, tlf_path)
        variables_check.run_tool()
        variables = variables_check.variables
        files = variables_check.files
        checks = variables_check.checks
        run_summary = variables_check.run_summary

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
        

class ConveyanceGraphDialog(QDialog, graph_ui.Ui_GraphDialog):
    
    def __init__(self, title="Section Conveyance"):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)

    def setupGraph(self, section_data, section_id):
        try:
            self.setWindowTitle('{} - {}'.format(self.title, section_id))
        except: pass
        
        scene = QGraphicsScene()
        view = self.graphGraphicsView.setScene(scene)
        fig = Figure()
        axes = fig.gca()
        
        minx = section_data['xvals'][0]
        maxx = section_data['xvals'][-1]
        miny = min(section_data['yvals'])
        maxy = max(section_data['yvals'])
        
        x = section_data['xvals']
        y = section_data['yvals']
        
#         axes.set_title(self.title)
        axes.set_ylabel('Elevation (mAOD)')
        axes.set_xlabel('Chainage (m)')

        xs_plot = axes.plot(x, y, "-k", label="Cross Section")
        p_plot = None

        panel_count = 0
        for i, panel in enumerate(section_data['panels']):
            if panel:
                panel_count += 1
                panel_label = 'Panel {}'.format(panel_count)
                panelx = [section_data['xvals'][i], section_data['xvals'][i]]
                panely = [miny, maxy]
                p_plot = axes.plot(panelx, panely, "-b", label=panel_label)
        
        cx = []
        cy = []
        for c in section_data['conveyance']:
            cx.append(c[0])
            cy.append(c[1])
        axes2 = axes.twiny()
        k_plot = axes2.plot(cx, cy, "-r", label="Conveyance")
        axes2.set_xlabel('Conveyance (m3/s)', color='r')

        plot_lines = xs_plot + k_plot
        labels = [l.get_label() for l in plot_lines]
        if p_plot is not None: 
            plot_lines += p_plot
            labels.append('Panels')
        axes.legend(plot_lines, labels, loc='lower right')
#         axes.legend()
#         axes2.legend()

        axes.grid(True)
        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)
        
        
class BadBanksGraphDialog(QDialog, graph_ui.Ui_GraphDialog):
    
    def __init__(self, title="Banktop Check"):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)

    def setupGraph(self, section_data, section_id):
        try:
            self.setWindowTitle('{} - {}'.format(self.title, section_id))
        except: pass
        
        scene = QGraphicsScene()
        view = self.graphGraphicsView.setScene(scene)
        fig = Figure()
        axes = fig.gca()
        
        x = section_data['xvals']
        y = section_data['yvals']
        
#         axes.set_title(self.title)
        axes.set_ylabel('Elevation (mAOD)')
        axes.set_xlabel('Chainage (m)')

        xs_plot = axes.plot(x, y, "-k", label="Cross Section")
        fill_plot = axes.fill(np.NaN, np.NaN, 'r', alpha=0.5)
        
        if section_data['left_drop'] > 0:
            line_x = x[:(section_data['max_left_idx']+1)]
            line_y = y[:(section_data['max_left_idx']+1)]
            line_elev = [section_data['max_left'] for i in line_x]
            axes.plot(
                line_x, line_elev, '-r'
            )
            axes.fill_between(line_x, line_y, line_elev, interpolate=True, alpha=0.5, color='r')
        if section_data['right_drop'] > 0:
            line_x = x[section_data['max_right_idx']:]
            line_y = y[section_data['max_right_idx']:]
            line_elev = [section_data['max_right'] for i in line_x]
            axes.plot(
                line_x, line_elev, '-r'
            )
            axes.fill_between(line_x, line_y, line_elev, interpolate=True, alpha=0.5, color='r')

        axes.legend(xs_plot + fill_plot, ['Cross Section', 'Poor Banks'], loc='lower right')
        axes.grid(True)
        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)

        
class FmpSectionCheckDialog(QDialog, fmpsectioncheck_ui.Ui_FmpSectionPropertyCheckDialog):
    
    def __init__(self, iface, project):
        QDialog.__init__(self)
        self.iface = iface
        self.project = project
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        
        # Loaded section property details
        self.properties = None
        
        # Setup context menus on tables
        self.negativeConveyanceTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.negativeConveyanceTable.customContextMenuRequested.connect(self._conveyanceTableContext)
        self.banktopCheckTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.banktopCheckTable.customContextMenuRequested.connect(self._banktopCheckTableContext)
        
        # Connect the slots
        self.datFileReloadBtn.clicked.connect(self.loadSectionData)
        
        # Load existing settings
        temp_dir = mrt_settings.loadProjectSetting(
            'temp_dir', self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./temp')
        )
        chainage_results = mrt_settings.loadProjectSetting(
            'fmp_conveyance_data', self.project.readPath('./temp')
        )
        # Connect file widgets and update slots
        self.datFileWidget.setFilePath(dat_path)
        self.datFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'dat_file'))
        self.fmpNodesLayerCbox.setFilters(QgsMapLayerProxyModel.PointLayer)
        
    def _conveyanceTableContext(self, pos):
        index = self.negativeConveyanceTable.itemAt(pos)
        if index is None: return
        menu = QMenu()
        locate_section_action = menu.addAction("Locate Section")
        graph_section_action = menu.addAction("Graph Section")

        # Get the action and do whatever it says
        action = menu.exec_(self.negativeConveyanceTable.viewport().mapToGlobal(pos))

        if action is None: return
        if action == locate_section_action or action == graph_section_action:
            row = self.negativeConveyanceTable.currentRow()
            id = self.negativeConveyanceTable.item(row, 0).text()
            if action == locate_section_action:
                self.showSelectedNode(id)
            elif action == graph_section_action:
                self.graphSection(id, 'conveyance')

    def _setupTableContext(self, pos, table, caller):
        index = table.itemAt(pos)
        if index is None: return
        menu = QMenu()
        locate_section_action = menu.addAction("Locate Section")
        graph_section_action = menu.addAction("Graph Section")

        # Get the action and do whatever it says
        action = menu.exec_(table.viewport().mapToGlobal(pos))

        if action is None: return
        if action == locate_section_action or action == graph_section_action:
            row = table.currentRow()
            id = table.item(row, 0).text()
            if action == locate_section_action:
                self.showSelectedNode(id)
            elif action == graph_section_action:
                self.graphSection(id, caller)
                
    def _banktopCheckTableContext(self, pos):
        self._setupTableContext(pos, self.banktopCheckTable, 'bad_banks')

    def graphSection(self, node_id, caller):
        """
        """
        if caller == 'conveyance':
            dlg = ConveyanceGraphDialog()
            dlg.setupGraph(self.properties['negative_k'][node_id], node_id)
            dlg.exec_()
        elif caller == 'bad_banks':
            dlg = BadBanksGraphDialog()
            dlg.setupGraph(self.properties['bad_banks'][node_id], node_id)
            dlg.exec_()
        
    def showSelectedNode(self, node_id):
        node_layer = self.fmpNodesLayerCbox.currentLayer()
        self.iface.mainWindow().findChild(QAction, 'mActionDeselectAll').trigger()
        node_layer.removeSelection()
        found_node = False
        for f in node_layer.getFeatures():
            id = f['ID']
            if id == node_id:
                found_node = True
                node_layer.select(f.id())
                self.iface.mapCanvas().zoomToSelected(node_layer)
#                 box = node_layer.boundingBoxOfSelected()
#                 self.iface.mapCanvas().setExtent(box)
#                 self.iface.mapCanvas().refresh()
                break

        if not found_node:
            QMessageBox.warning(
                self, "FMP Node Not Found", 
                "FMP node {} could not be found in nodes layer".format(node_id)
            )
        
    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        if caller == 'dat_file':
            self.loadSectionData()
        
    def loadSectionData(self):
#         k_tol = 10
        k_tol = self.kTolSpinbox.value()
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', self.project.readPath('./temp')
        )
        section_check = fmpsection_check.CheckFmpSections(working_dir, dat_path, k_tol)
        self.properties = section_check.run_tool()
        
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


class FmpRefhCheckDialog(QDialog, refh_ui.Ui_FmpRefhCheckDialog):
    
    def __init__(self, iface, project):
        QDialog.__init__(self)
        self.iface = iface
        self.project = project
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        
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
        self.csv_results, text_output, failed_paths, missing_refh = refh_compare.run_tool()
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
        if filepath:
            mrt_settings.saveProjectSetting('csv_file', filepath[0])
            r = self.csv_results[0]
            with open(filepath[0], 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                for row in r:
                    out = row.strip('\n').split('\s')
                    writer.writerow(out)


class TuflowStabilityCheckDialog(QDialog, tuflowstability_ui.Ui_TuflowStabilityCheckDialog):
    
    def __init__(self, iface, project):
        QDialog.__init__(self)
        self.iface = iface
        self.project = project
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        
        mb_file = mrt_settings.loadProjectSetting(
            'mb_file', self.project.readPath('./temp')
        )
        self.mbFileWidget.setFilePath(mb_file)
        self.mbFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'mb_file'))
        self.mbReloadBtn.clicked.connect(self.loadMbFile)
        
    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)
        self.loadMbFile()
    
    def loadMbFile(self):
        mb_path = mrt_settings.loadProjectSetting(
            'mb_file', self.project.readPath('./temp')
        )
        mb_check = tmb_check.TuflowStabilityCheck(mb_path)
        results = mb_check.run_tool()
        self.graphResults(results)
        
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


class AmaxGraphDialog(QDialog, graph_ui.Ui_GraphDialog):
    
    def __init__(self, title="AMAX"):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)

    def setupGraph(self, series, station):
        try:
            self.setWindowTitle('{} - {} {}'.format(self.title, station['id']))
        except: pass
        
        flow = []
        years = []
        for s in series:
            flow.append(s[0])
            years.append(int(s[1][:4]))
            
        scene = QGraphicsScene()
        view = self.graphGraphicsView.setScene(scene)
        fig = Figure()
        axes = fig.gca()
        
        axes.bar(years, flow)
#         axes.xaxis.set_major_formatter(DateFormatter("%Y"))
#         axes.xaxis.set_major_locator(mdates.YearLocator(5, month=1, day=1))
        axes.set(
            xlabel="Year",
            ylabel="Flow (m3/s)",
            title="AMAX Flow Data at ({0}) {1}".format(station['id'], station['name'])
        )
        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)


class PotGraphDialog(QDialog, graph_ui.Ui_GraphDialog):
    
    def __init__(self, title="POT"):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)

    def setupGraph(self, series, station):
        try:
            self.setWindowTitle('{} - {} {}'.format(self.title, station['id']))
        except: pass
        
        flow = []
        years = []
        for s in series:
            flow.append(s['flow'])
            years.append(int(s['datetime'][:4]))
            
        scene = QGraphicsScene()
        view = self.graphGraphicsView.setScene(scene)
        fig = Figure()
        axes = fig.gca()
        
        axes.scatter(years, flow, marker='x', s=3, alpha=0.7)
#         axes.xaxis.set_major_formatter(DateFormatter("%Y"))
#         axes.xaxis.set_major_locator(mdates.YearLocator(5, month=1, day=1))
        axes.set(
            xlabel="Year",
            ylabel="Flow (m3/s)",
            title="POT Flow Data at ({0}) {1}".format(station['id'], station['name'])
        )
        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)
        
        
class DailyFlowsGraphDialog(QDialog, graph_ui.Ui_GraphDialog):
    
    def __init__(self, title="Daily Flows"):
        QDialog.__init__(self)
        self.setupUi(self)
        self.title = title
        self.setWindowTitle(title)

    def setupGraph(self, series, station, year):
        try:
            self.setWindowTitle('{0} {1} - {2}'.format(self.title, year, station['id']))
        except: pass
        
        flow = []
        dates = []
        for s in series:
            flow.append(s['flow'])
            date = datetime.strptime(s['date'], '%Y-%m-%d').date()
            dates.append(date)
            
        scene = QGraphicsScene()
        view = self.graphGraphicsView.setScene(scene)
        fig = Figure()
        axes = fig.gca()
        
        plot = axes.plot(dates, flow, "-b", label="Flow")
        axes.xaxis.set_major_formatter(DateFormatter("%m-%d"))
#         axes.xaxis.set_major_locator(mdates.YearLocator(5, month=1, day=1))
        axes.set(
            xlabel="Date",
            ylabel="Flow (m3/s)",
            title="{0} Daily Flow Data: ({1}) {2}".format(year, station['id'], station['name'])
        )
        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)


class NrfaStationViewerDialog(QDialog, nrfa_ui.Ui_NrfaViewerDialog):
    
    NRFA_STATIONS = './data/nrfa_viewer/NRFA_Station_Info.shp'
    closing = pyqtSignal(name='closing')

    def __init__(self, iface, project):
        QDialog.__init__(self)
        self.iface = iface
        self.project = project
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)
        
        self.station_points = None
        self.cur_station = {}
        self.cache_tracker = {
            'full_info': -1,
            'amax': -1,
            'pot': -1,
            'daily_flows': -1,
        }
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
        
    def signalClose(self):
        self.closing.emit()
        
    def closeEvent(self, *args, **kwargs):
        self.signalClose()
        return QDialog.closeEvent(self, *args, **kwargs)

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
            self.loadDailyFlowData()
        
    def fetchStations(self):
        nrfa_layer = QgsVectorLayer(self.nrfa_stations, "nrfa_stations", "ogr")
#         nrfa_layer = QgsVectorLayer(NRFA_STATIONS, "nrfa_stations", "ogr")
        if not nrfa_layer.isValid():
            QMessageBox.warning(
                self, "Unable to load NRFA layer", 
                "NRFA Station info layer could not be loaded, please reimport the data."
            )
            return

        self.stationNamesCbox.clear()
#         working_dir = mrt_settings.loadProjectSetting(
#             'working_directory', str, self.project.readPath('./temp')
#         )
        search_radius = self.maxDistanceSpinbox.value() * 1000
        canvas_centre = self.iface.mapCanvas().center()
        distance = QgsDistanceArea()
        distance.setSourceCrs(nrfa_layer.crs(), self.project.transformContext())
        
        self.stations = {}
        for point in nrfa_layer.getFeatures():
            p = point.geometry()
            name = point['name']
            id = point['id']
            p.convertToSingleType()
            if distance.measureLine(p.asPoint(), canvas_centre) <= search_radius:
                self.stations[point['id']] = {'layer': point, 'name': point['name']}
                
        self.stationNamesCbox.blockSignals(True)
        for k, v in self.stations.items():
            s = '({0}) {1}'.format(k, v['name'])
            self.stationNamesCbox.addItem(s)
        self.stationNamesCbox.blockSignals(False)
                
        if len(self.stations.keys()) == 0:
            QMessageBox.information(
                self, "No NRFA station found in given radius", 
                "There are no NRFA stations in the given radius. Try increasing the distance."
            )
        else:
            self.stationInfoGroupbox.setEnabled(True)
            existing_layers = self.project.instance().mapLayersByName("NRFA Stations Selection")
            if existing_layers:
                self.project.instance().removeMapLayers([existing_layers[0].id()])
            self.station_points = QgsVectorLayer("Point", "NRFA Stations Selection", "memory")
            self.station_points.setCrs(nrfa_layer.crs())
            provider = self.station_points.dataProvider()
            provider.addAttributes([
                QgsField("ID", QVariant.Int),
                QgsField("Name", QVariant.String),
            ])
            self.station_points.updateFields()
            for k, v in self.stations.items():
                feat = QgsFeature()
                feat.setGeometry(v['layer'].geometry())
                feat.setAttributes([k, v['name']])
                provider.addFeature(feat)
            self.station_points.updateExtents()
            
            # Set labels to the station ID
            text_format = QgsTextFormat()
            label = QgsPalLayerSettings()
            label.fieldName = 'ID'
            label.enabled = True
            label.setFormat(text_format)
            labeler = QgsVectorLayerSimpleLabeling(label)
            self.station_points.setLabelsEnabled(True)
            self.station_points.setLabeling(labeler)
            
            self.project.instance().addMapLayer(self.station_points)
            self.showStationInfo()

    def showStationInfo(self, *args): 
        self.stationTabWidget.setCurrentIndex(0)
        stn_type_link = 'https://nrfa.ceh.ac.uk/hydrometric-information'
        text = self.stationNamesCbox.currentText()
        if text == '': 
            return
        station_id, station_name = text.split(')')
        self.cur_station['id'] = int(station_id[1:])
        self.cur_station['name'] = station_name.strip()
        self.selected_station = self.stations[self.cur_station['id']]['layer']
        self.stationInfoTextbox.clear()

        self.station_points.removeSelection()
        for f in self.station_points.getFeatures():
            id = f['ID']
            if id == self.cur_station['id']:
                self.station_points.select(f.id())
                box = self.station_points.boundingBoxOfSelected()
                self.iface.mapCanvas().setExtent(box)
                self.iface.mapCanvas().refresh()
                break

        output = [
            '{0:<20} {1}'.format('ID:', self.cur_station['id']),
            '{0:<20} {1}'.format('Name:', self.selected_station['name']),
            '{0:<20} {1}'.format('River:', self.selected_station['river']),
            '{0:<20} {1}'.format('Location:', self.selected_station['location']),
            '{0:<20} {1} (details - {2})'.format('Station Type:', self.selected_station['stn-type'], stn_type_link),
            '{0:<20} {1}'.format('BNG:', self.selected_station['BNG']),
            '{0:<20} {1}'.format('Easting:', self.selected_station['easting']),
            '{0:<20} {1}'.format('Northing:', self.selected_station['northing']),
            '{0:<20} {1} km2'.format('Catchment Area:', self.selected_station['catch-area']),
            '{0:<20} {1} mAOD'.format('Station Level:', self.selected_station['stn-level']),
        ]
        self.stationInfoTextbox.append('\n'.join(output)) 
        
    def loadAdditionalInfo(self):
        if not self.cache_tracker['full_info'] == self.cur_station['id']:
            nrfa = nrfa_viewer.NrfaViewer()
            output = nrfa.fetchStationData(self.cur_station['id'], fields='all')
            self.fullDetailsTextbox.clear()
            self.fullDetailsTextbox.append(output)
            self.cache_tracker['full_info'] = self.cur_station['id']

    def loadAmaxData(self):
        if not self.cache_tracker['amax'] == self.cur_station['id']:
            self.cur_amax_series = None
            nrfa = nrfa_viewer.NrfaViewer()
            try:
                flow_meta, series = nrfa.fetchAmaxData(self.cur_station['id'])
            except RuntimeError as err:
                QMessageBox.warning(
                    self, "Failed to load AMAX data", 
                    err.args[0]
                )

            summary = [
                '{0:<40} {1:<40}'.format('ID', 'amax-stage', 'amax-flow'),
                '{0:<40} {1:<40}'.format('Name', flow_meta['name']),
                '{0:<40} {1:<40}'.format('Parameter', flow_meta['parameter']),
                '{0:<40} {1:<40}'.format('Units', flow_meta['units']),
                '{0:<40} {1:<40}'.format('Measurement type', flow_meta['measurement-type']),
                '{0:<40} {1:<40}'.format('Period', flow_meta['period']),
            ]
            self.amaxSummaryTextbox.clear()
            self.amaxSummaryTextbox.append('\n'.join(summary))
            
            row_position = 0
            self.amaxResultsTable.setRowCount(row_position)
            self.cur_amax_series = series
            for s in series:
                flow = '{:.2f}'.format(s[0])
                self.amaxResultsTable.insertRow(row_position)
                self.amaxResultsTable.setItem(row_position, 0, QTableWidgetItem(flow))
                self.amaxResultsTable.setItem(row_position, 1, QTableWidgetItem(s[1]))
                row_position += 1
            
            self.cache_tracker['amax'] = self.cur_station['id']


    def graphAmax(self, results):
        dlg = AmaxGraphDialog()
        dlg.setupGraph(self.cur_amax_series, self.cur_station)
        dlg.exec_()
    
    def exportAmaxCsv(self):
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        file_name = '{0}_AMAX_Data.csv'.format(str(self.cur_station['id']))
        file_name = os.path.join(working_dir, file_name)
        if self.cur_amax_series is not None:
            with open(file_name, 'w', newline='\n') as save_file:
                writer = csv.writer(save_file, delimiter=',')
                writer.writerow(['Date', 'Flow (m3/s)'])
                for row in self.cur_amax_series:
                    writer.writerow([row[1], row[0]])
            
    def loadPotData(self):
        if not self.cache_tracker['pot'] == self.cur_station['id']:
            self.cur_pot_series = None
            nrfa = nrfa_viewer.NrfaViewer()
            try:
#                 stage_meta, flow_meta, series = nrfa.fetchPotData(self.cur_station['id'])
                flow_meta, series = nrfa.fetchPotData(self.cur_station['id'])
            except RuntimeError as err:
                QMessageBox.warning(
                    self, "Failed to load POT data", 
                    err.args[0]
                )

            summary = [
                '{0:<40} {1:<40}'.format('ID', 'pot-flow'),
                '{0:<40} {1:<40}'.format('Name', flow_meta['name']),
                '{0:<40} {1:<40}'.format('Parameter', flow_meta['parameter']),
                '{0:<40} {1:<40}'.format('Units', flow_meta['units']),
                '{0:<40} {1:<40}'.format('Measurement type', flow_meta['measurement-type']),
                '{0:<40} {1:<40}'.format('Period', flow_meta['period']),
            ]
            self.potSummaryTextbox.clear()
            self.potSummaryTextbox.append('\n'.join(summary))
            
            row_position = 0
            self.potResultsTable.setRowCount(row_position)
            self.cur_pot_series = series
            for s in series:
                flow = '{:.2f}'.format(s['flow'])
                self.potResultsTable.insertRow(row_position)
                self.potResultsTable.setItem(row_position, 0, QTableWidgetItem(flow))
                self.potResultsTable.setItem(row_position, 1, QTableWidgetItem(s['datetime']))
                row_position += 1
            
            self.cache_tracker['pot'] = self.cur_station['id']
            
    def graphPot(self, results):
        dlg = PotGraphDialog()
        dlg.setupGraph(self.cur_pot_series, self.cur_station)
        dlg.exec_()
    
    def exportPotCsv(self):
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        file_name = '{0}_POT_Data.csv'.format(str(self.cur_station['id']))
        file_name = os.path.join(working_dir, file_name)
        if self.cur_pot_series is not None:
            with open(file_name, 'w', newline='\n') as save_file:
                writer = csv.writer(save_file, delimiter=',')
                writer.writerow(['Date', 'Flow (m3/s)'])
                for row in self.cur_pot_series:
                    writer.writerow([row['datetime'], row['flow']])
        
    def loadDailyFlowData(self):
        if not self.cache_tracker['daily_flows'] == self.cur_station['id']:
            self.cur_dailyflow_series = None
            nrfa = nrfa_viewer.NrfaViewer()
            try:
                meta, series, latest_year = nrfa.fetchDailyFlowData(self.cur_station['id'])
            except RuntimeError as err:
                QMessageBox.warning(
                    self, "Failed to load daily flow data", 
                    err.args[0]
                )
            
            self.do_dailyflow_update = False
            self.cur_dailyflow_series = series
            self.cur_dailyflow_year = latest_year
            self.dailyFlowsYearCbox.clear()
            for year in series.keys():
                self.dailyFlowsYearCbox.addItem(str(year))

            self.dailyFlowsYearCbox.setCurrentText(str(latest_year))
            self.do_dailyflow_update = True
            self.updateDailyFlowsTable(str(latest_year))
            self.cache_tracker['daily_flows'] = self.cur_station['id']
            
    def updateDailyFlowsTable(self, year):
        if not self.do_dailyflow_update: return
        year = int(year)
        self.cur_dailyflow_year = year
        row_position = 0
        self.dailyFlowsTable.setRowCount(row_position)
        for s in self.cur_dailyflow_series[year]:
            flow = '{:.2f}'.format(s['flow'])
            self.dailyFlowsTable.insertRow(row_position)
            self.dailyFlowsTable.setItem(row_position, 0, QTableWidgetItem(str(year)))
            self.dailyFlowsTable.setItem(row_position, 1, QTableWidgetItem(s['date']))
            self.dailyFlowsTable.setItem(row_position, 2, QTableWidgetItem(flow))
            self.dailyFlowsTable.setItem(row_position, 3, QTableWidgetItem(s['flag']))
            row_position += 1
            
    def graphDailyFlows(self):
        series_year = self.cur_dailyflow_year
        series = self.cur_dailyflow_series[series_year]
        dlg = DailyFlowsGraphDialog()
        dlg.setupGraph(series, self.cur_station, series_year)
        dlg.exec_()
    
    def exportDailyFlowsCsv(self):
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', self.project.readPath('./temp')
        )
        export_type = self.dailyFlowExportTypeCbox.currentIndex()
        if export_type == 0:
            export_all = False
            file_name = '{0}_DailyFlow_Data_{1}.csv'.format(
                self.cur_station['id'], self.cur_dailyflow_year
            )
        else:
            export_all = True
            file_name = '{0}_DailyFlow_Data.csv'.format(
                self.cur_station['id']
            )
        file_name = os.path.join(working_dir, file_name)
        if self.cur_dailyflow_series is not None:
            with open(file_name, 'w', newline='\n') as save_file:
                writer = csv.writer(save_file, delimiter=',')
                writer.writerow(['Year', 'Date', 'Flow (m3/s)', 'Q Flag'])
                if not export_all:
                    for row in self.cur_dailyflow_series[self.cur_dailyflow_year]:
                        writer.writerow([
                            self.cur_dailyflow_year, row['date'], row['flow'], row['flag']
                        ])
                else:
                    for year, data in self.cur_dailyflow_series.items():
                        for row in data:
                            writer.writerow([
                                str(year), row['date'], row['flow'], row['flag']
                            ])
            