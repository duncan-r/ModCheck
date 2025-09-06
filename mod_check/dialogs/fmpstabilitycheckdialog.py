
import numpy as np
import os
import csv
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from .dialogbase import DialogBase
from ..forms import ui_fmpstability_check_dialog as fmpstability_ui
from ..tools import help, globaltools
from ..tools import fmpstabilitycheck as fmps_check
from ..tools import settings as mrt_settings

from ..mywidgets import graphdialogs as graphs

DATA_DIR = './data'
TEMP_DIR = './temp'

class FmpStabilityCheckDialog(DialogBase, fmpstability_ui.Ui_FmpStabilityCheckDialog):
    """Load and display TUFLOW mass balance file contents.
    """

    def __init__(self, dialog_name, iface, project):
        DialogBase.__init__(self, dialog_name, iface, project, 'Check FMP Stability')

        self.default_tabcsv_path = "C:/Program Files/Flood Modeller/bin/TabularCSV.exe"

        self.tab_csv_path = "C:/Program Files/Flood Modeller/bin/TabularCSV.exe"
        self.working_dir = ""
        self.dat_path = ""
        self.results_path = ""
        self.results = None
        self.timestep_press_active = False
        # self.graph_view = graphs.FmpStabilityGraphicsView()
        # self.graph_toolbar = NavigationToolbar(self.graph_view.canvas, self)
        # self.geom_graph_view = graphs.FmpStabilityGeometryGraphicsView()
        # self.geom_graph_toolbar = NavigationToolbar(self.geom_graph_view.canvas, self)
        self.series_graphics_view = graphs.FmpStabilityGraphicsView(self.seriesGraphicsView)
        self.section_graphics_view = graphs.FmpStabilityGeometryGraphicsView(self.sectionGraphicsView)
        self.seriesResetGraphButton.clicked.connect(lambda x: self.resetSeriesGraph(x, 'series'))
        self.sectionResetGraphButton.clicked.connect(lambda x: self.resetSeriesGraph(x, 'section'))
        self.showHoverTextCBox.stateChanged.connect(self.showHoverTextChanged)

        self.setDefaultSettings()
        self.datFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'dat_file'))
        self.datResultsFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'results_file'))
        self.reloadDatAndResultsBtn.clicked.connect(self.loadDatResults)
        self.validationSeriesCbox.currentTextChanged.connect(lambda s: self.validationSeriesChanged(s))
        
        self.fileSelectionTabWidget.setCurrentIndex(0) # Make sure we're on the usable tab
        self.fileSelectionTabWidget.removeTab(1)
        # Not currently used
        # self.existingResultsDatFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'dat_file'))
        # self.loadExistingResultsBtn.clicked.connect(self.loadExistingResults)
        # self.flowResultsFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'flow_results'))
        # self.stageResultsFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'stage_results'))

        self.allSeriesList.currentRowChanged.connect(lambda i: self.updateGraph(i, 'all'))
        self.failedSeriesList.currentRowChanged.connect(lambda i: self.updateGraph(i, 'fail'))
        self.timestepSlider.valueChanged.connect(self.updateTimestepSlider)
        self.timestepSlider.sliderPressed.connect(self.timestepSliderPressed)
        self.timestepSlider.sliderReleased.connect(self.timestepSliderReleased)
        self.timestepIncButton.clicked.connect(lambda i: self.timestepButtonClicked(i, 'inc'))
        self.timestepDecButton.clicked.connect(lambda i: self.timestepButtonClicked(i, 'dec'))

        # self.graphLayout.addWidget(self.graph_view)
        # self.graphLayout.addWidget(self.graph_toolbar)
        # self.geomGraphLayout.addWidget(self.geom_graph_view)
        # self.geomGraphLayout.addWidget(self.geom_graph_toolbar)
        self.splitter.setStretchFactor(5, 10)

    def setDefaultSettings(self):
        self.datFileWidget.setFilePath(mrt_settings.loadProjectSetting(
            'dat_file', './temp')
        )
        self.datResultsFileWidget.setFilePath(mrt_settings.loadProjectSetting(
            'results_file', './temp')
        )
        self.existingResultsDatFileWidget.setFilePath(mrt_settings.loadProjectSetting(
            'dat_file', './temp')
        )
        self.flowResultsFileWidget.setFilePath(mrt_settings.loadProjectSetting(
            'flow_results', './temp')
        )
        self.stageResultsFileWidget.setFilePath(mrt_settings.loadProjectSetting(
            'stage_results', './temp')
        )
        
    def showHoverTextChanged(self, status):
        if status:
            self.series_graphics_view.show_hover = True
            self.section_graphics_view.show_hover = True
        else:
            self.series_graphics_view.show_hover = False
            self.section_graphics_view.show_hover = False
        
    def resetSeriesGraph(self, x, caller):
        if caller == 'series':
            self.series_graphics_view.updatePlot()
        elif caller == 'section':
            pass
            self.section_graphics_view.updatePlot()
            

    def timestepButtonClicked(self, x, value):
        if value == 'inc':
            self.timestepSlider.setValue(self.timestepSlider.value() + 1)
        elif value == 'dec':
            self.timestepSlider.setValue(self.timestepSlider.value() - 1)
        else:
            return
        
    def timestepSliderPressed(self):
        self.timestep_press_active = True

    def timestepSliderReleased(self):
        self.timestep_press_active = False
        self.updateTimestepSlider(self.timestepSlider.value())

    def fileChanged(self, path, caller):
        if caller == 'results_file':
            path = os.path.splitext(path)[0]
        mrt_settings.saveProjectSetting(caller, path)

    def loadDatResults(self):
        dat_path = mrt_settings.loadProjectSetting('dat_file', None)
        results_path = mrt_settings.loadProjectSetting('results_file', None)

        if results_path is None:
            QMessageBox.warning(
                self, "Required file path missing", 
                "Please set .dat and results paths first."
            )
            return
        msg = ''
        if not os.path.exists(results_path + '.zzn'):
            msg = 'FMP results file path does not exists (or does not contain .zzn unsteady results)'
        if msg:
            QMessageBox.warning(self, "File path does not exist", msg)
            return

        self.statusLabel.setText('Loading results...')
        QApplication.processEvents()
        path_with_ext = results_path + '.zzn'
        self.results = fmps_check.convertResults(path_with_ext)
        
        if dat_path and os.path.exists(dat_path):
            self.statusLabel.setText('Loading FMP .dat file...')
            QApplication.processEvents()
            try:
                dat = fmps_check.loadDatFile(dat_path)
                self.results.dat = dat
            except Exception as err:
                self.results._dat = None
                QMessageBox.warning(self, "File Load Error", "Failed to load .dat file - series results can still be viewed")

        series_check_type = self.validationSeriesCbox.currentText()
        self.statusLabel.setText(f'Running stability check for {series_check_type}...')
        QApplication.processEvents()
        status = self.checkStability(series_check_type)

        self.setupNodeLists(self.results.failed_nodes)
        self.updateGraph(0, 'all')
        # self.stageResultsFileWidget.setFilePath(stage_path)
        # self.flowResultsFileWidget.setFilePath(flow_path)
        # self.fileSelectionTabWidget.setCurrentIndex(1) # NOTE: don't use while disabling tab in __init__
        self.statusLabel.setText('Results load complete')
        
    def validationSeriesChanged(self, text):
        if not self.results:
            return
        
        series_check_type = self.validationSeriesCbox.currentText()
        self.statusLabel.setText(f'Running stability check for {series_check_type}...')
        QApplication.processEvents()
        status = self.checkStability(series_check_type)

        self.setupNodeLists(self.results.failed_nodes)
        self.updateGraph(0, 'all')
        # self.fileSelectionTabWidget.setCurrentIndex(1) # NOTE: don't use while disabling tab in __init__
        self.statusLabel.setText('Stability check complete')

#     def loadExistingResults(self):
#         dat_path = mrt_settings.loadProjectSetting('dat_file', None)
#         flow_path = mrt_settings.loadProjectSetting('flow_results', None)
#         stage_path = mrt_settings.loadProjectSetting('stage_results', None)
#
#         # ~DEBUG~
# #         results_path = "C:/Users/ermev/OneDrive/Documents/Main/Company/1_Projects/2_Open/P2009001_CherwellThame_ModelReview/Technical/Hydraulics/Models/River_Cherwell/FMP/Results/001/BAS/108500_IST_BAS_DES_1000_001"
# #         flow_path = results_path + "_Flow_Altered.csv"
# #         stage_path = results_path + "_Stage_Altered.csv"
# #         results_path = "C:/Users/ermev/OneDrive/Documents/Main/Company/1_Projects/2_Open/P2009001_CherwellThame_ModelReview/Technical/Hydraulics/Models/River_Cherwell/FMP/Results/001/BAS/1000/108500_IST_BAS_DES_1000_001_"
# #         flow_path = results_path + "Flow_1000Yrs.csv"
# #         stage_path = results_path + "Stage_1000Yrs.csv"
# #         flow_path = results_path + "Flow_10000Yrs.csv"
# #         stage_path = results_path + "Stage_10000Yrs.csv"
#
#
# #         self.stab_check = fmps_check.FmpStabilityCheck()
#         if os.path.exists(dat_path):
#             self.statusLabel.setText('Loading FMP .dat file...')
#             QApplication.processEvents()
#             self.results.sections, nodes = fmps_check.loadDatFile(dat_path)
#
#         self.statusLabel.setText('Loading results...')
#         QApplication.processEvents()
#         # self.flow_data, self.times, self.nodes, result_type = fmps_check.loadExistingResults(flow_path)
#         self.results = fmps_check.loadExistingResults(stage_path)
#
#         # self.statusLabel.setText('Loading Stage results...')
#         # QApplication.processEvents()
#         # self.stage_data, self.times, self.nodes, result_type = fmps_check.loadExistingResults(stage_path)
#         # self.results = fmps_check.loadExistingResults(stage_path)
#
#         series_check_type = self.validationSeriesCbox.currentText()
#         self.statusLabel.setText('Running stability check...')
#         QApplication.processEvents()
#         status = self.checkStability(series_check_type)
#
#         self.setupNodeLists(self.results.failed_nodes)
#         self.updateGraph(0, 'all')
#         self.statusLabel.setText('Results load complete')

    def setupNodeLists(self, failed_nodes):
        self.allSeriesList.clear()
        self.failedSeriesList.clear()
        self.allSeriesList.addItems(self.results.nodes)
        for f in failed_nodes:
            self.failedSeriesList.addItem(f[0])
        self.timestepSlider.setMaximum(len(self.results.times))

    def updateTimestepSlider(self, val):
        if self.timestep_press_active:
            return
        node_index = self.allSeriesList.currentRow()
        self.updateGraph(node_index, 'all')

    def updateGraph(self, node_index, caller):
        if caller == 'fail' and node_index >= 0:
            node_index = self.results.failed_nodes[node_index][1]
            self.allSeriesList.blockSignals(True)
            self.allSeriesList.setCurrentRow(node_index)
            self.allSeriesList.blockSignals(False)

        series_check_type = self.validationSeriesCbox.currentText()
        node_name = self.results.nodes[node_index]
        node_type = self.results.unit_type(node_name)
        self.nodeNameLabel.setText(node_name)
        self.nodeTypeLabel.setText(node_type)

        timestep_idx = self.timestepSlider.value()
        timestep = self.results.times[timestep_idx]
        time_stage = self.results.stage.at[timestep, node_name]
        self.timestepValueLabel.setText(str("{:.3f}".format(timestep)))

        self.series_graphics_view.drawPlot(
            self.results.times, [self.results.stage[node_name], self.results.flows[node_name]], 
            self.results.derivs[node_index], timestep, series_check_type, node_name
        )
        # self.section_graphics_view(node_name, time_stage)
        self.updateGeomGraph(node_name, time_stage)

    def updateGeomGraph(self, node_name, time_stage):
        pass
        geom = None
        if self.results.dat is not None:
            geom = fmps_check.loadGeometry(node_name, self.results.dat)
        
        if geom is None:
            self.section_graphics_view.clearPlot()
        else:
            self.section_graphics_view.drawPlot(geom, node_name, time_stage)

    def checkStability(self, series_type):
        """Stability analysis of time series.

        Analyse the flow time series to check whether there appear to be any
        unstable sections in the simulation results. This works quite well for
        identifying sections of a series with serious instability. If the
        tolerances are lowered to identify less significant stability isssues, it
        tends to cause a lot of false positives. I think this is just an issue
        with the nature of the series data, but there is probably a better way.

        This is a multi-step process:
            1. Smooth the time series a bit. The results usually have a lot of 
               small variations - increasing/decreasing over individual timesteps -
               that shouldn't be considered an instability. The series is smoothed
               by averaging the values over the "time_window" of 0.5 hours.
            2. Take the first and second order derivatives of the smoothed time
               series with respect to time and loop through them to find the max, 
               min and absolute values over a window of 1 hour.
            3. Check whether the dy2/d2x > dy/dx * 1.5 for each value with a
               tolerance of -1 < dy2 > 1 to avoid some of the remaining signal noise.

        Note: Highly un-optimised at the moment. 
            Should check to see if there's some way to avoid having to do so much 
            looping to get a reasonable result. This is caused by needing to 
            smooth the time series first.
            Still think that an FFT would be better here?
        """
        
        self.loadResultsProgressBar.setMaximum(len(self.results.nodes))
        self.loadResultsProgressBar.setValue(0)
        # progress_inc = len(self.nodes) / 100
        TOL = 1.5
        SMOOTH_TIME_WINDOW = 0.5
        if series_type == 'Flow':
            DY2_MIN_TOL = 1 
        else:
            DY2_MIN_TOL = 0.2

        DX = self.results.save_interval
        node_fail = []
        fail = False
        derivs = []
        failed_nodes = []
        for i, node in enumerate(self.results.nodes):
            if i % 5 == 0:
                self.loadResultsProgressBar.setValue(i)

            window_length = -1
            found_timewindow = False
            found_hourlength = False
            for j, t in enumerate(self.results.times):
                if found_timewindow and found_hourlength:
                    break

                if not found_timewindow and t - self.results.times[0] >= SMOOTH_TIME_WINDOW:
                    window_length = j
                    found_timewindow = True
                if t - self.results.times[0] >= 1:
                    hour_length = j
                    found_hourlength = True

            new_series = []
            count = 0
            if series_type == 'Flow':
                series = self.results.flows[node].to_numpy()
            else:
                series = self.results.stage[node].to_numpy()

            for j, s in enumerate(series):                    
                if j > window_length:
                    mysum = sum(series[j-window_length:j])
                    mylen = len(series[j-window_length:j])
                else:
                    mysum = sum(series[j-count:j])
                    mylen = len(series[j-count:j])

                if j == 0:
                    new_series.append(
                        s
                    )
                else:
                    new_series.append(
                        mysum / mylen
                    )
                count += 1
            dy = np.diff(new_series, n=1) / DX
            dy2 = np.diff(new_series, n=2) / DX

            status = 'Passed'

#             if max(dy2) > 5 and min(dy2) < 5:
#                 status = 'Failed'
            fail_times = []
            newhour_length = hour_length #int(hour_length / 2)

            # Loop the 2nd derivative series and scan the window
            # for variations in 1st/2nd derivative change in relation
            # to the tolerances defined above
            for j, val in enumerate(dy2):
                if j > hour_length:

                    maxdy2 = max(dy2[j-newhour_length:j])
                    mindy2 = min(dy2[j-newhour_length:j])
                    maxdy = max(dy[j-newhour_length:j])
                    mindy = min(dy[j-newhour_length:j])

                    abs_dy2 = abs(maxdy2 - mindy2)
                    abs_dy = abs(maxdy - mindy)
                    abscheck = abs_dy2 > (abs_dy * TOL)

                    if (maxdy2 > DY2_MIN_TOL or mindy2 < (DY2_MIN_TOL * -1)) and abscheck:
                        status = 'Failed'
                        fail_times.append(round(self.results.times[j], 3))

            if status == 'Failed':
                failed_nodes.append([node, i])
            derivs.append({
                'dy2': dy2, 'f': new_series, 'dy': dy, 'status': status, 'fail_times': fail_times, 
            })

        self.results.failed_nodes = failed_nodes
        self.results.derivs = derivs
        self.loadResultsProgressBar.setValue(0)
        return node_fail

