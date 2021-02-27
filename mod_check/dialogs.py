

import os
import csv
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar
# from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# import matplotlib
# matplotlib.use('Qt5Agg')
# import matplotlib.pyplot as plt

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

from .forms import ui_chainage_calculator_dialog as chaincalc_ui
from .forms import ui_fmptuflow_widthcheck_dialog as fmptuflowwidthcheck_ui
from .forms import ui_runvariables_check_dialog as fmptuflowvariablescheck_ui
from .forms import ui_fmpsectionproperty_check_dialog as fmpsectioncheck_ui
from .forms import ui_graph_dialog as graph_ui

from .tools import chainagecalculator as chain_calc
from .tools import fmptuflowwidthcheck as fmptuflow_widthcheck
from .tools import runvariablescheck as runvariables_check
from .tools import fmpsectioncheck as fmpsection_check
from .tools import settings as mrt_settings

class ChainageCalculatorDialog(QDialog, chaincalc_ui.Ui_ChainageCalculator):
    
    def __init__(self, iface, project):
        QDialog.__init__(self)
        self.iface = iface
        self.project = project
        self.setupUi(self)
        
        # Connect the slots
        self.calcFmpChainageOnlyBtn.clicked.connect(self.calculateFmpOnlyChainage)
        self.compareChainageBtn.clicked.connect(self.compareEstryFmpChainage)
        self.fmpOnlyCheckbox.stateChanged.connect(self.compareFmpOnlyChange)
        
        # Load existing settings
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', str, self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', str, self.project.readPath('./temp')
        )
        chainage_results = mrt_settings.loadProjectSetting(
            'chainage_results', str, self.project.readPath('./temp')
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
            'working_directory', str, self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', str, self.project.readPath('./temp')
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
            'working_directory', str, self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', str, self.project.readPath('./temp')
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
        
        # Load existing settings
        working_dir = mrt_settings.loadProjectSetting(
            'working_directory', str, self.project.readPath('./')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', str, self.project.readPath('./')
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
            'working_directory', str, self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', str, self.project.readPath('./')
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
            'tlf_file', str, self.project.readPath('./temp')
        )
        ief_path = mrt_settings.loadProjectSetting(
            'ief_file', str, self.project.readPath('./temp')
        )
        zzd_path = mrt_settings.loadProjectSetting(
            'zzd_file', str, self.project.readPath('./temp')
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
            'ief_file', str, self.project.readPath('./temp')
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
            'zzd_file', str, self.project.readPath('./temp')
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
            'tlf_file', str, self.project.readPath('./temp')
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
            'temp_dir', str, self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', str, self.project.readPath('./temp')
        )
        chainage_results = mrt_settings.loadProjectSetting(
            'fmp_conveyance_data', str, self.project.readPath('./temp')
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
        node_layer.removeSelection()
        found_node = False
        for f in node_layer.getFeatures():
            id = f['ID']
            if id == node_id:
                found_node = True
                node_layer.select(f.id())
                self.iface.actionZoomToSelected().trigger()
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
            'working_directory', str, self.project.readPath('./temp')
        )
        dat_path = mrt_settings.loadProjectSetting(
            'dat_file', str, self.project.readPath('./temp')
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

