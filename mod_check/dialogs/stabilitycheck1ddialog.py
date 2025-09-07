
import numpy as np
import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from .dialogbase import DialogBase
from ..forms import ui_1d_stability_check_dialog as stability_ui
from ..tools import help, globaltools
from ..tools import stabilitycheck1d as stab_check
from ..tools import settings as mrt_settings

from ..mywidgets import graphdialogs as graphs

DATA_DIR = './data'
TEMP_DIR = './temp'

class StabilityCheck1DDialog(DialogBase, stability_ui.Ui_StabilityCheck1DDialog):
    """Load and display TUFLOW mass balance file contents.
    """

    def __init__(self, dialog_name, iface, project):
        DialogBase.__init__(self, dialog_name, iface, project, 'Check 1D Stability')

        self.working_dir = ""
        self.dat_path = ""
        self.results_path = ""
        self.results = None
        self.timestep_press_active = False

        self.series_graphics_view = graphs.FmpStabilityGraphicsView(self.seriesGraphicsView)
        self.section_graphics_view = graphs.FmpStabilityGeometryGraphicsView(self.sectionGraphicsView)
        self.seriesResetGraphButton.clicked.connect(lambda x: self.resetSeriesGraph(x, 'series'))
        self.sectionResetGraphButton.clicked.connect(lambda x: self.resetSeriesGraph(x, 'section'))
        self.showHoverTextCBox.stateChanged.connect(self.showHoverTextChanged)

        self.setDefaultSettings()
        self.datFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'dat_file'))
        self.datResultsFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'results_file'))
        self.estryResultsFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'tpc_file'))
        self.reloadDatAndResultsBtn.clicked.connect(self.loadResults)
        self.validationSeriesCbox.currentTextChanged.connect(lambda s: self.validationSeriesChanged(s))
        
        # self.fileSelectionTabWidget.setCurrentIndex(0)
        self.allSeriesList.currentRowChanged.connect(lambda i: self.updateGraph(i, 'all'))
        self.failedSeriesList.currentRowChanged.connect(lambda i: self.updateGraph(i, 'fail'))
        self.timestepSlider.valueChanged.connect(self.updateTimestepSlider)
        self.timestepSlider.sliderPressed.connect(self.timestepSliderPressed)
        self.timestepSlider.sliderReleased.connect(self.timestepSliderReleased)
        self.timestepIncButton.clicked.connect(lambda i: self.timestepButtonClicked(i, 'inc'))
        self.timestepDecButton.clicked.connect(lambda i: self.timestepButtonClicked(i, 'dec'))
        self.splitter.setStretchFactor(5, 10)
        
        self.model_type = ''

    def setDefaultSettings(self):
        self.datFileWidget.setFilePath(mrt_settings.loadProjectSetting(
            'dat_file', './temp')
        )
        self.datResultsFileWidget.setFilePath(mrt_settings.loadProjectSetting(
            'results_file', './temp')
        )
        self.estryResultsFileWidget.setFilePath(mrt_settings.loadProjectSetting(
            'tpc_file', './temp')
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
        
    def loadResults(self):
        self.failedSeriesList.clear()
        self.allSeriesList.clear()
        self.timestepSlider.setValue(0)
        self.series_graphics_view.clearPlot()
        self.section_graphics_view.clearPlot()
        if self.fileSelectionTabWidget.currentIndex() == 0:
            self.loadDatResults()
        elif self.fileSelectionTabWidget.currentIndex() == 1:
            self.loadEstryResults()

    def loadDatResults(self):
        dat_path = mrt_settings.loadProjectSetting('dat_file', None)
        results_path = mrt_settings.loadProjectSetting('results_file', None)

        if results_path is None:
            QMessageBox.warning(
                self, "Required file path missing", 
                "Please set .dat and results paths first, or use the ESTRY tab for TUFLOW."
            )
            return
        msg = ''
        if not os.path.exists(results_path + '.zzn'):
            msg = 'FMP results file path does not exists (or does not contain .zzn unsteady results)'
        if msg:
            QMessageBox.warning(self, "File path does not exist", msg)
            return

        self.model_type = 'fm'
        self.statusLabel.setText('Loading results...')
        QApplication.processEvents()
        path_with_ext = results_path + '.zzn'
        self.results = stab_check.convertResults(path_with_ext)
        
        if dat_path and os.path.exists(dat_path):
            self.statusLabel.setText('Loading FMP .dat file...')
            QApplication.processEvents()
            try:
                dat = stab_check.loadDatFile(dat_path)
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
        self.statusLabel.setText('Results load complete')
        
    def loadEstryResults(self):
        tpc_path = mrt_settings.loadProjectSetting('tpc_file', None)
        if tpc_path is None:
            QMessageBox.warning(
                self, "Required file path missing",
                "Select a .tpc file path first or select the FM tab to use Flood Modeller."
            )
        
        self.model_type = 'estry'
        self.statusLabel.setText('Loading results...')
        QApplication.processEvents()
        tpc_paths, valid = stab_check.loadTpc(tpc_path)
        if not valid:
            QMessageBox.warning(
                self, "TPC linked file missing",
                "One or more of the results files linked from the .tpc could not be found."
            )
            self.statusLabel.setText("Result load fail: missing results files")
            return
        
        self.results = stab_check.convertEstryResults(tpc_paths)

        series_check_type = self.validationSeriesCbox.currentText()
        self.statusLabel.setText(f'Running stability check for {series_check_type}...')
        QApplication.processEvents()
        status = self.checkStability(series_check_type)

        self.setupNodeLists(self.results.failed_nodes)
        self.updateGraph(0, 'all')
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
        self.statusLabel.setText('Stability check complete')

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

        if self.model_type == 'fm':
            self.series_graphics_view.drawPlot(
                self.results.times,
                {'stage': [self.results.stage[node_name]], 'flow': [self.results.flows[node_name]]}, 
                self.results.derivs[node_index], timestep, series_check_type, node_name
            )
            self.updateGeomGraph(node_name, time_stage)
        elif self.model_type == 'estry':
            try:
                second_stage = self.results.stage[node_name + '_ds']
            except KeyError:
                second_stage = None
            self.series_graphics_view.drawPlot(
                self.results.times, 
                {'stage': [self.results.stage[node_name], second_stage], 'flow': [self.results.flows[node_name]]}, 
                self.results.derivs[node_index], timestep, series_check_type, node_name,
            )

    def updateGeomGraph(self, node_name, time_stage):
        pass
        geom = None
        if self.results.dat is not None:
            geom = stab_check.loadGeometry(node_name, self.results.dat)
        
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
            
        Args:
            series_type(str): 'Flow' or 'Stage'.
        """
        
        self.loadResultsProgressBar.setMaximum(len(self.results.nodes))
        self.loadResultsProgressBar.setValue(0)
        # progress_inc = len(self.nodes) / 100
        TOL = 1.5
        SMOOTH_TIME_WINDOW = 0.5
        
        # We want to be a bit more pedantic for stage than flow because acceptable
        # instability in stage tends to be less
        if series_type == 'Flow':
            DY2_MIN_TOL = 1 
        else:
            DY2_MIN_TOL = 0.2

        DX = self.results.save_interval
        node_fail = []
        fail = False
        derivs = []
        failed_nodes = []
        
        # ESTRY has flows for channels and stage for nodes
        # FM uses nodes for both
        # if self.model_type == 'estry':
        #     if series_type == 'Flow':
        #         enumeration_values = self.results.channels
        #     else:
        #         enumeration_values = self.results.nodes
        # else:
        #     enumeration_values = self.results.nodes
        
        for i, node in enumerate(self.results.nodes):
        # for i, node in enumerate(enumeration_values):
            if i % 5 == 0:
                self.loadResultsProgressBar.setValue(i)

            # Calculate the window step range
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

            # Smooth time series over a moving window to remove minor variations that are
            # not problematic, but would get flagged as instabilities
            # Average the values over the moving window
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
                
            # Calculate the derivatives
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

