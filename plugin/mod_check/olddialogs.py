
import os
import csv
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *
from qgis.gui import QgsMessageBar, QgsFileWidget

from floodmodeller_api import DAT
from tmf.tuflow_model_files import TCF
from tmf.tuflow_model_files.inp.file import FileInput
from tmf.tuflow_model_files.inp.setting import SettingInput

from .mydialogs.dialogbase import DialogBase
from .forms import ui_assessment_dialog as assessment_ui
from .tools import help, globaltools
from .tools import filecheck
from .tools import settings as mrt_settings
from .mywidgets import graphdialogs as graphs

DATA_DIR = './data'
TEMP_DIR = './temp'


class AssessmentDialog(DialogBase, assessment_ui.Ui_AssessmentDialog):
    
    def __init__(self, dialog_name, iface, project):

        DialogBase.__init__(self, dialog_name, iface, project, 'Model Assessment')
        
        self.reloadBtn.clicked.connect(self.testStuff)
        
        model_path = mrt_settings.loadProjectSetting(
            'model_folder', self.project.readPath('./temp')
        )
        self.modelFolderFileWidget.setFilePath(model_path)

        self.modelFolderFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'model_folder'))
        # self.fmpFileReloadBtn.clicked.connect(self.loadModelFile)
        # self.csvExportBtn.clicked.connect(self.exportCsv)
        
    def testStuff(self):
        # self.checkParameters()
        self.fileCheck()
        
    def fileCheck(self):
        ief_path = "C:/Users/ermev/Documents/Programming/Test_Data/Modcheck/pm_AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13/Runs21.10_AshGt_trimmed/Defended/AshGt2110_Def_2122_T0001HC_F0100cc26_PostDev_trimmed_v13.ief"
        from .tools import runvariablescheck
        iefCheck = runvariablescheck.IefVariablesCheck(self.project, ief_path)
        filepaths, _ = iefCheck.run_tool()
        fpaths = []
        for k, v in filepaths.items():
            if k == 'Event data':
                for ed in v:
                    fpaths.append(globaltools.longPathCheck(os.path.normpath(ed)))
            elif k == 'Results files':
                fpaths.append(os.path.normpath(v + '.zzn'))
            else:
                fpaths.append(str(os.path.normpath(v)))
        
        self.outputTextEdit.appendPlainText('FM missing files:\n')
        missing_fm = []
        for f in fpaths:
            if not os.path.exists(f):
                missing_fm.append(f)
                self.outputTextEdit.appendPlainText('\n{}'.format(f))
                
                
        self.outputTextEdit.appendPlainText('\n\nTUFLOW missing files:')
        # tcf_path = "C:/Users/ermev/Documents/Programming/Test_Data/Modcheck/pm_AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13/Runs21.10_AshGt_trimmed/Defended/AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13.tcf"
        # run_options = "-s1 PostDev"
        tcf_path = "C:/Users/ermev/Documents/Programming/Test_Data/Modcheck/MortonOnLugg_TuflowClassic/tuflow/runs/MoretonOnLugg_~s1~_~e1~_009_test.tcf"
        # run_options = "-s1 BAS -e1 Q0100"

        tcf_root, tcf_name = os.path.split(tcf_path)
        tuflow = TCF(tcf_path)
        # context = tuflow.context(run_options) 
        context = tuflow.context() 
        
        tcf_inputs = tuflow.inputs
        tgc_inputs = tuflow.tgc().get_inputs()
        tbc_inputs = tuflow.tbc().get_inputs()
        
        # tcf_files = {'1d': [], '2d': []}
        # tcf_settings = {}
        tcf_files = []
        tcf_settings = []
        tgc_files = []
        tgc_settings = []
        tbc_files = []
        
        # print('\nTCF')
        for inp in tcf_inputs:
            if isinstance(inp, FileInput):
                scope = []
                for s in inp.scope():
                    stype = s._type
                    if stype == 'SCENARIO' or stype == 'EVENT':
                        scope.append('{} {}'.format(s._type, str(s.name)))
                    else:
                        scope.append(s._type)
                    
                missing = inp.missing_files
                value = str(inp.resolved_value)
                if 'tmf' in inp.value.lower() and '|' in inp.value:
                    missing = False
                tcf_files.append('({}) {} - {}'.format(missing, ' '.join(scope), value))
            
            elif isinstance(inp, SettingInput):
                # scope = inp.scope()
                scope = [y for y in [x.name for x in inp.scope()]]
                value = inp.resolved_value
                tcf_settings.append('{} - {}'.format(scope, value))

        # print('\nTGC')
        for inp in tgc_inputs:
            if isinstance(inp, FileInput):
                scope = inp.scope()
                missing = inp.missing_files
                value = str(inp.resolved_value)
                tgc_files.append('({}) {} - {}'.format(missing, scope, value))
            elif isinstance(inp, SettingInput):
                scope = inp.scope()
                # value = inp.value
                value = inp.resolved_value
                tgc_settings.append('{} - {}'.format(scope, value))

        # print('\nTBC')
        for inp in tbc_inputs:
            if isinstance(inp, FileInput):
                scope = inp.scope()
                missing = inp.missing_files
                value = str(inp.resolved_value)
                tbc_files.append('({}) {} - {}'.format(missing, scope, value))
        
        
        self.outputTextEdit.appendPlainText('\n\nTCF files:')
        self.outputTextEdit.appendPlainText('\n'.join(tcf_files))
        self.outputTextEdit.appendPlainText('\n\nTGC files:')
        self.outputTextEdit.appendPlainText('\n'.join(tgc_files))
        self.outputTextEdit.appendPlainText('\n\nTBC files:')
        self.outputTextEdit.appendPlainText('\n'.join(tbc_files))
        self.outputTextEdit.appendPlainText('\n\nTCF settings:')
        self.outputTextEdit.appendPlainText('\n'.join(tcf_settings))
        self.outputTextEdit.appendPlainText('\n\nTGC settings:')
        self.outputTextEdit.appendPlainText('\n'.join(tgc_settings))
        
        # for i in tcf_inputs:
        #     if isinstance(i, FileInput):
        #
        #         domain = '2d'
        #         for s in i.scope():
        #             if isinstance(s, OneDimScope):
        #                 domain = '1d'
        #
        #         trd = None if i.trd is None else i.trd.dbpath
        #
        #         is_multi = False
        #         if isinstance(i, GisInput):
        #             if i.multi_layer:
        #                 is_multi = True
        #
        #         tcf_files[domain].append({
        #             'command': i.command,
        #             'full_path': i.files,
        #             'value': i.value,
        #             'parent': i.parent.path,
        #             'trd': trd,
        #             'is_multi': is_multi,
        #             'missing': missing,
        #         })
        #
        #     if isinstance(i, SettingInput):
        #         is_estry = False
        #         for s in i.scope():
        #             if isinstance(s, OneDimScope):
        #                 is_estry = True
        #         if i.command.lower() == 'timestep':
        #             if is_estry:
        #                 tcf_settings['timestep_1d'] = str(i.value)
        #             else:
        #                 tcf_settings['timestep_2d'] = str(i.value)
        #         if i.command.lower() == 'bc event text':
        #             tcf_settings['bc_event_text'] = str(i.value)
        #         if i.command.lower() == 'bc event name':
        #             tcf_settings['bc_event_name'] = str(i.value)
        #
        # tgc_files = []
        # tgc_settings = {}
        # for i in tgc_inputs:
        #
        #     if isinstance(i, FileInput):
        #
        #         trd = None if i.trd is None else i.trd.dbpath
        #
        #         is_multi = False
        #         if isinstance(i, GisInput):
        #             if i.multi_layer:
        #                 is_multi = True
        #
        #         tgc_files.append({
        #             'command': i.command,
        #             'full_path': i.files,
        #             'value': i.value,
        #             'parent': i.parent.path,
        #             'trd': trd,
        #             'is_multi': is_multi,
        #         })
        #
        #     if isinstance(i, SettingInput):
        #         if i.command.lower() == 'cell size':
        #             tgc_settings['cell_size'] = str(i.value)
        #
        # tbc_files = []
        # for i in tbc_inputs:
        #
        #     if isinstance(i, FileInput):
        #
        #         trd = None if i.trd is None else i.trd.dbpath
        #
        #         is_multi = False
        #         if isinstance(i, GisInput):
        #             if i.multi_layer:
        #                 is_multi = True
        #
        #         tbc_files.append({
        #             'command': i.command,
        #             'full_path': i.files,
        #             'value': i.value,
        #             'parent': i.parent.path,
        #             'trd': trd,
        #             'is_multi': is_multi,
        #         })
        #
        # log_folder = None
        #
        # log_1d = {
        #     'files': [], 'settings': [],
        # }
        #
        # log_2d = {
        #     'tcf': {'files': [], 'settings': []},
        #     'tgc': {'files': [], 'settings': []},
        #     'tbc': {'files': [], 'settings': []},
        #     'bcdbase': {'files': [], 'settings': []},
        # } 
        #
        # log_1d['files'] = tcf_files['1d']
        # log_2d['tcf']['files'] = tcf_files['2d']
        # log_2d['tcf']['settings'] = tcf_settings
        # log_2d['tgc']['files'] = tgc_files
        # log_2d['tgc']['settings'] = tgc_settings
        # log_2d['tbc']['files'] = tbc_files
        # log_folder = os.path.join(tcf_root, tuflow.log_folder)
        #
        # self.outputTextEdit.appendPlainText('\n\nTUFLOW tcf files:')
        # self.outputTextEdit.appendPlainText(str(log_1d['files']))
        # self.outputTextEdit.appendPlainText(str(log_2d['tcf']['files']))
        #
        # self.outputTextEdit.appendPlainText('\nTUFLOW tcf settings:')
        # self.outputTextEdit.appendPlainText(str(log_2d['tcf']['settings']))
        #
        # self.outputTextEdit.appendPlainText('\nTUFLOW tgc files:')
        # self.outputTextEdit.appendPlainText(str(log_2d['tgc']['files']))
        # self.outputTextEdit.appendPlainText('\nTUFLOW tgc settings:')
        # self.outputTextEdit.appendPlainText(str(log_2d['tgc']['settings']))
        #
        # self.outputTextEdit.appendPlainText('\nTUFLOW tbc files:')
        # self.outputTextEdit.appendPlainText(str(log_2d['tbc']['files']))
        #
        # # TODO: Handle events data base stuff here
        # eventdb = tuflow.event_database()
        # self.outputTextEdit.appendPlainText('\nTUFLOW Events DBase:')
        # self.outputTextEdit.appendPlainText(str(eventdb))
        #
        # bcdb = tuflow.bc_database
        # # log_2d['bcdbase']['files'] = bcdb
        # self.outputTextEdit.appendPlainText('\nTUFLOW BC DBase:')
        # # self.outputTextEdit.appendPlainText(str(bcdb))
        # bcfiles = []
        # # for b in log_2d['bcdbase']['files']:
        # for b in bcdb:
        #     f = b.get_files()
        #     temp = str(f)
        #     if 'bc_event_text' in log_2d['tcf']['settings'].keys():
        #         temp = temp.replace(
        #             log_2d['tcf']['settings']['bc_event_text'],
        #             log_2d['tcf']['settings']['bc_event_name'],
        #         )
        #         bcfiles.append(temp)
        #
        # self.outputTextEdit.appendPlainText(str(bcfiles))

        # xsdb = tuflow.xs_dbase()
                
        
    def checkParameters(self):
        ief_path = "C:/Users/ermev/Documents/Programming/Test_Data/Modcheck/pm_AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13/Runs21.10_AshGt_trimmed/Defended/AshGt2110_Def_2122_T0001HC_F0100cc26_PostDev_trimmed_v13.ief"
        # from .tools import runvariablescheck
        iefCheck = runvariablescheck.IefVariablesCheck(self.project, ief_path)
        filepaths, parameters = iefCheck.run_tool()
        fpaths = []
        params = []
        for k, v in filepaths.items():
            fpaths.append('{}: {}'.format(k, str(v)))
        for k, v in parameters['changed'].items():
            params.append('{}: {} (default = {}) - {}'.format(
                v['ief_variable_name'], v['value'], v['default'], v['description']
            ))
        output = ['\nFM parameters:\n']
        output.extend('\n'.join(fpaths))
        output += '\n\n' + '\n'.join(params)
        output = [
            'Filepaths\n',
            '\n'.join(fpaths),
            '\n\nParameters',
            '\n'.join(params),
        ]
        self.outputTextEdit.setPlainText(''.join(output))
        
        output += ['\nZZD Checks:\n']
        self.outputTextEdit.appendPlainText('\n\nZZD Check\n')
        zzd_path = "C:/Users/ermev/Documents/Programming/Test_Data/Modcheck/pm_AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13/Results21.10_AshGt_trimmed/Defended/1d_isis/ASHGT2110_DEF_2122_T0001HC_F0100CC26_POSTDEV_TRIMMED_CULV_V13.zzd"
        zzd_check = runvariablescheck.ZzdFileCheck(self.project, zzd_path)
        diagnostics, warnings = zzd_check.run_tool()
        
        for name, details in diagnostics.items():
            self.outputTextEdit.appendPlainText(
                '{}: {} - {}'.format(
                    name, details['value'], details['description']
                )
            )
#
        for error_type, details in warnings['error'].items():
            error_name = 'ERROR: ' + error_type
            self.outputTextEdit.appendPlainText(
                '{} (count: {}) - {}'.format(
                    error_name, str(details['count']), details['info']
                )
            )

        for warning_type, details in warnings['warning'].items():
            warning_name = 'WARNING: ' + warning_type
            self.outputTextEdit.appendPlainText(
                '{} (count: {}) - {}'.format(
                    warning_name, str(details['count']), details['info']
                )
            )
        
        self.outputTextEdit.appendPlainText('\n\n\nTUFLOW\n\n')
        tlf_path = "C:/Users/ermev/Documents/Programming/Test_Data/Modcheck/pm_AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13/Results21.10_AshGt_trimmed/Defended/log/AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13_PostDev+Culv.tlf"
        tlf_check = runvariablescheck.TlfDetailsCheck(self.project, tlf_path)
        tlf_check.run_tool()

        variables = tlf_check.variables
        files = tlf_check.files
        checks = tlf_check.checks
        run_summary = tlf_check.run_summary

        self.outputTextEdit.appendPlainText('Parameters:\n')
        for variable, details in variables.items():
            self.outputTextEdit.appendPlainText(
                '{}: {} (default: {}) - {}'.format(
                    variable, details['value'], details['default'], details['description']
                )
            )

        self.outputTextEdit.appendPlainText('\n\nFiles:\n')
        for filename, details in files.items():
            self.outputTextEdit.appendPlainText(
                '{}: {} - {}'.format(
                    details[0], filename, details[1]
                )
            )

        self.outputTextEdit.appendPlainText('\n\nChecks:\n')
        for check_code, details in checks.items():
            self.outputTextEdit.appendPlainText(
                '{}: {} (count: {}) - {} ({})'.format(
                    details['type'], check_code, str(details['count']), details['message'], details['wiki_link']
                )
            )

        self.outputTextEdit.appendPlainText('\n\nRun summary:\n')
        for variable, details in run_summary.items():
            self.outputTextEdit.appendPlainText(
                '{}: {} - {}'.format(
                    variable, details['value'], details['description']
                )
            )

        
        
    # def teststuffinitial(self):
    #     model_path = mrt_settings.loadProjectSetting(
    #         'model_folder', self.project.readPath('./temp')
    #     )
    #     self.outputTextEdit.setPlainText("Model folder: {}".format(model_path))
    #     dat = DAT("C:/Users/ermev/Documents/Main/Company/3_Technical/Dev/FM_API/test_data/epicpark/dat/AshGt2110_1D_Defended_v13-PD_trimmed.dat")
    #     names = []
    #     for k, v in dat.sections.items():
    #         names.append(v.name)
    #     self.outputTextEdit.appendPlainText("Made it")
    #     self.outputTextEdit.appendPlainText('\n'.join(names))
    #
    #
    #     # tcf = TCF("C:/Users/ermev/Documents/Main/Company/3_Technical/Dev/TUFLOW/test_models/fm_tuflow_epicpark/pm_AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13/Runs21.10_AshGt_trimmed/Defended/AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13.tcf")
    #     # tcf_path = "C:/Users/ermev/Documents/Main/Company/3_Technical/Dev/TUFLOW/test_models/fm_tuflow_epicpark/pm_AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13/Runs21.10_AshGt_trimmed/Defended/AshGt2110_Def_2122_T0001HC_F0100cc26_trimmed_v13.tcf"
    #     tcf = TCF("C:/Users/ermev/Documents/Main/Company/1_Projects/2_Open/P2207001_DiltonMarsh_FMS/Technical/Hydraulics/model/tuflow/runs/DiltonMarsh_~s1~_~e1~_006.tcf")
    #     self.outputTextEdit.appendPlainText("\n\nTCF Loaded")
        
    def fileChanged(self, path, caller):
        mrt_settings.saveProjectSetting(caller, path)


# class FmpRefhCheckDialog(DialogBase, refh_ui.Ui_FmpRefhCheckDialog):
#
#     def __init__(self, dialog_name, iface, project):
#
#         DialogBase.__init__(self, dialog_name, iface, project, 'ReFH Check')
#
#         self.csv_results = None
#
#         model_path = mrt_settings.loadProjectSetting(
#             'refh_file', self.project.readPath('./temp')
#         )
#         self.fmpFileWidget.setFilePath(model_path)
#
#         self.fmpFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'refh_file'))
#         self.fmpFileReloadBtn.clicked.connect(self.loadModelFile)
#         self.csvExportBtn.clicked.connect(self.exportCsv)
#
#     def fileChanged(self, path, caller):
#         mrt_settings.saveProjectSetting(caller, path)
#         self.loadModelFile()
#
#     def loadModelFile(self):
#         model_path = mrt_settings.loadProjectSetting(
#             'refh_file', self.project.readPath('./temp')
#         )
#         refh_compare = refhcheck.CompareFmpRefhUnits([model_path])
#         try:
#             self.csv_results, text_output, failed_paths, missing_refh = refh_compare.run_tool()
#         except Exception as err:
#             QMessageBox.warning(
#                 self, "FMP dat/ied file load failed", err.args[0]
#             )
#         self.formatTexbox(text_output, failed_paths, missing_refh)
#
#     def formatTexbox(self, output, failed_paths, missing_refh):   
#
#         self.refhOutputTextbox.clear()
#         self.refhOutputTextbox.appendPlainText('\n'.join(output))
#
#         # Highlight the values that are different in red
#         cursor = self.refhOutputTextbox.textCursor()
#
#         # Setup the desired format for matches
#         text_format = QTextCharFormat()
#         text_format.setBackground(QBrush(QColor("red")))
#
#         # Setup the regex engine
#         pattern = "!!!"
#         regex = QRegExp(pattern)
#
#         # Process the displayed document
#         pos = 0
#         index = regex.indexIn(self.refhOutputTextbox.toPlainText(), pos)
#         while (index != -1):
#             # Select the matched text and apply the desired text_format
#             cursor.setPosition(index)
#             cursor.movePosition(QTextCursor.EndOfWord, 1)
#             cursor.mergeCharFormat(text_format)
#             # Move to the next match
#             pos = index + regex.matchedLength()
#             index = regex.indexIn(self.refhOutputTextbox.toPlainText(), pos)
#
#         msg = None
#         if failed_paths:
#             msg = ['The following files could not be audited:']
#             for f in failed_paths:
#                 msg.append(f)
#             msg = '\n'.join(msg)
#
#         if missing_refh:
#             if failed_paths: msg += '\n\n'
#             msg = ['The following files contain no ReFH units:']
#             for m in missing_refh:
#                 msg.append(m)
#             msg = '\n'.join(msg)
#         if msg is not None:
#             msg += '\n\n'
#             cursor.setPosition(0)
#             self.refhOutputTextbox.insertPlainText(msg)
#         self.refhOutputTextbox.moveCursor(cursor.Start)
#         self.refhOutputTextbox.ensureCursorVisible()
#
#     def exportCsv(self):
#         if not self.csv_results:
#             QMessageBox.warning(self, "Export Failed", "No results found: Please load model first")
#             return
#
#         csv_file = mrt_settings.loadProjectSetting(
#             'csv_file', self.project.readPath('./temp')
#         )
#
#         filepath = QFileDialog(self).getSaveFileName(
#             self, 'Export Results', csv_file, "CSV File (*.csv)"
#         )
#         if filepath[0]:
#             mrt_settings.saveProjectSetting('csv_file', filepath[0])
#             r = self.csv_results[0]
#             with open(filepath[0], 'w', newline='') as csvfile:
#                 writer = csv.writer(csvfile, delimiter=',')
#                 for row in r:
#                     out = row.strip('\n').split('\s')
#                     writer.writerow(out)
#

# class NrfaStationViewerDialog(DialogBase, nrfa_ui.Ui_NrfaViewerDialog):
#     """Dialog for selecting and viewing NRFA station information.
#
#     Identify nearby NRFA stations and view the station information,
#     AMAX, POT and daily flows data for the selected station.
#     """
#
#     TOOL_NAME = 'nrfa_viewer'
#     TOOL_DATA = os.path.join(DATA_DIR, TOOL_NAME)
#     NRFA_STATIONS = os.path.join(TOOL_DATA, 'NRFA_Station_Info.shp')
#
#     def __init__(self, dialog_name, iface, project):
#         DialogBase.__init__(self, dialog_name, iface, project, 'NRFA Station Viewer')
#
#         self.do_dailyflow_update = False
#
#         self.workingDirFileWidget.setStorageMode(QgsFileWidget.GetDirectory)
#         self.nrfa_stations = os.path.join(
#             os.path.dirname(os.path.realpath(__file__)),
#             NrfaStationViewerDialog.NRFA_STATIONS
#         )
#
#         working_dir = mrt_settings.loadProjectSetting(
#             'working_directory', self.project.readPath('./temp')
#         )
#         distance = mrt_settings.loadProjectSetting('nrfa_max_distance', 15)
#
#         self.workingDirFileWidget.setFilePath(working_dir)
#         self.maxDistanceSpinbox.setValue(distance)
#         self.workingDirFileWidget.fileChanged.connect(lambda i: self.fileChanged(i, 'working_directory'))
#         self.maxDistanceSpinbox.valueChanged.connect(self.maxDistanceChanged)
#         self.fetchStationsBtn.clicked.connect(self.fetchStations)
#         self.stationNamesCbox.currentIndexChanged.connect(self.showStationInfo)
#         self.buttonBox.clicked.connect(self.signalClose)
#         self.stationTabWidget.currentChanged.connect(self.stationTabChanged)
#         self.showAmaxGraphBtn.clicked.connect(self.graphAmax)
#         self.exportAmaxCsvBtn.clicked.connect(self.exportAmaxCsv)
#         self.showPotGraphBtn.clicked.connect(self.graphPot)
#         self.exportPotCsvBtn.clicked.connect(self.exportPotCsv)
#         self.showDailyFlowsGraphBtn.clicked.connect(self.graphDailyFlows)
#         self.exportDailyFlowsCsvBtn.clicked.connect(self.exportDailyFlowsCsv)
#         self.dailyFlowsYearCbox.currentTextChanged.connect(self.updateDailyFlowsTable)
#
#         self.nrfa_viewer = nrfa_viewer.NrfaViewer(self.project, self.iface)
#
#     def fileChanged(self, path, caller):
#         mrt_settings.saveProjectSetting(caller, path)
#
#     def maxDistanceChanged(self, value):
#         mrt_settings.saveProjectSetting('nrfa_max_distance', value)
#
#     def stationTabChanged(self, index):
#         if index == 0:
#             pass
#         elif index == 1:
#             self.loadAdditionalInfo()
#         elif index == 2:
#             self.loadAmaxData()
#         elif index == 3:
#             self.loadPotData()
#         elif index == 4:
#             self.loadDailyFlowsData()
#
#     def fetchStations(self):
#         """Locate all NRFA stations within a radius of the map canvas center.
#
#         Calls the self.nrfa_viewer.fetchStations() function to create a memory
#         layer containing the point location and IDs of NRFA stations that are
#         within the user supplied radius of the map canvas center.
#         Supplies the function with a pre-compiled point layer (in the data
#         folder) containing summary information about NRFA stations in the UK.
#
#         Displays the ID and station name for all selected stations in the 
#         station selection combobox and updates the station info tab with the
#         details of the default selected station.
#         """
#         nrfa_layer = QgsVectorLayer(self.nrfa_stations, "nrfa_stations", "ogr")
#         if not nrfa_layer.isValid():
#             QMessageBox.warning(
#                 self, "Unable to load NRFA layer", 
#                 "NRFA Station info layer could not be loaded, please reimport the data."
#             )
#             return
#
#         self.statusLabel.setText("Loading NRFA stations ...")
#         search_radius = self.maxDistanceSpinbox.value() * 1000
#         stations = self.nrfa_viewer.fetchStations(nrfa_layer, search_radius)
#
#         self.stationNamesCbox.clear()
#         if not stations:
#             QMessageBox.information(
#                 self, "No NRFA station found in given radius", 
#                 "There are no NRFA stations in the given radius. Try increasing the distance."
#             )
#         else:
#             self.stationNamesCbox.blockSignals(True)
#             for s in stations:
#                 self.stationNamesCbox.addItem(s)
#             self.stationNamesCbox.blockSignals(False)
#             self.showStationInfo()
#             self.stationInfoGroupbox.setEnabled(True)
#
#     def showStationInfo(self, *args): 
#         """Show the summary infomation about the selected NRFA station.
#
#         Calls the self.nrfa_viewer function to retrieve the summary information
#         for the currently selected NRFA station and displays it on the "Station Info"
#         tab. These are just some key details about the station.
#         """
#         self.statusLabel.setText("Updating NRFA station info ...")
#         self.stationTabWidget.setCurrentIndex(0)
#         self.stationInfoTextbox.clear()
#         text = self.stationNamesCbox.currentText()
#         if text == '': 
#             return
#         station_id, station_name = text.split(')')
#         station_id = int(station_id[1:])
#         station_name = station_name.strip()
#
#         output = self.nrfa_viewer.fetchStationSummary(station_id)
#         self.stationInfoTextbox.append('\n'.join(output)) 
#         self.statusLabel.setText("Station info updated")
#
#     def loadAdditionalInfo(self):
#         """Displays all the NRFA information availble for this station.
#
#         Calls the API request function in self.nrfa_viewer to fetch all of the 
#         metadata available for this NRFA station. The details are then displayed
#         in a textedit on the "Full Details" tab.
#         """
#         try:
#             output = self.nrfa_viewer.fetchStationData()
#         except ConnectionError as err:
#             QMessageBox.warning(
#                 self, "NRFA API connection failed", err.args[0]
#             )
#         self.fullDetailsTextbox.clear()
#         self.fullDetailsTextbox.append(output)
#         self.fullDetailsTextbox.moveCursor(self.fullDetailsTextbox.textCursor().Start)
#         self.fullDetailsTextbox.ensureCursorVisible()
#
#     def loadAmaxData(self):
#         """Load the AMAX (Annual Maximum) data.
#
#         Call the API request function in self.nrfa_viewer to fetch the data. Updates
#         the summary metadata and table with the loaded data for the currently selected
#         NRFA station.
#         """
#         try:
#             metadata, series = self.nrfa_viewer.fetchAmaxData()
#         except ConnectionError as err:
#             QMessageBox.warning(
#                 self, "NRFA API connection failed", err.args[0]
#             )
#         self.amaxSummaryTextbox.clear()
#         self.amaxSummaryTextbox.append('\n'.join(metadata))
#         self.amaxSummaryTextbox.moveCursor(self.amaxSummaryTextbox.textCursor().Start)
#         self.amaxSummaryTextbox.ensureCursorVisible()
#
#         row_position = 0
#         self.amaxResultsTable.setRowCount(row_position)
#         for s in series:
#             flow = '{:.2f}'.format(s['flow'])
#             self.amaxResultsTable.insertRow(row_position)
#             self.amaxResultsTable.setItem(row_position, 0, QTableWidgetItem(flow))
#             self.amaxResultsTable.setItem(row_position, 1, QTableWidgetItem(s['datetime']))
#             row_position += 1
#
#     def loadPotData(self):
#         """Load the POT (Peaks over threshold) data.
#
#         Call the API request function in self.nrfa_viewer to fetch the data. Updates
#         the summary metadata and table with the loaded data for the currently selected
#         NRFA station.
#         """
#         try:
#             metadata, series = self.nrfa_viewer.fetchPotData()
#         except ConnectionError as err:
#             QMessageBox.warning(
#                 self, "NRFA API connection failed", err.args[0]
#             )
#         self.potSummaryTextbox.clear()
#         self.potSummaryTextbox.append('\n'.join(metadata))
#         self.potSummaryTextbox.moveCursor(self.potSummaryTextbox.textCursor().Start)
#         self.potSummaryTextbox.ensureCursorVisible()
#
#         row_position = 0
#         self.potResultsTable.setRowCount(row_position)
#         for s in series:
#             flow = '{:.2f}'.format(s['flow'])
#             self.potResultsTable.insertRow(row_position)
#             self.potResultsTable.setItem(row_position, 0, QTableWidgetItem(flow))
#             self.potResultsTable.setItem(row_position, 1, QTableWidgetItem(s['datetime']))
#             row_position += 1
#
#     def loadDailyFlowsData(self):
#         """Load Daily Flow Data.
#
#         Call the API request function in self.nrfa_viewer to fetch the data. The
#         data is separated into years with the most recent year being the default.
#         Populates the years combobox, sets the current item to the most recent 
#         year and calls the updateDailyFlowsTable() function to add year data to 
#         the table.
#         """
#         try:
#             metadata, series, latest_year = self.nrfa_viewer.fetchDailyFlowsData()
#         except ConnectionError as err:
#             QMessageBox.warning(
#                 self, "NRFA API connection failed", err.args[0]
#             )
#         if latest_year == -1:
#             return
#
#         self.dailyFlowsYearCbox.blockSignals(True)
#         self.cur_dailyflow_year = latest_year
#         self.dailyFlowsYearCbox.clear()
#         for year in series.keys():
#             self.dailyFlowsYearCbox.addItem(str(year))
#         self.dailyFlowsYearCbox.blockSignals(False)
#         self.dailyFlowsYearCbox.setCurrentText(str(latest_year))
#         self.updateDailyFlowsTable(str(latest_year))
#
#     def updateDailyFlowsTable(self, year):
#         """Update the contents of the daily flows table to the given year.
#
#         Args:
#             year(str/int): the year to update the table to.
#
#         Except:
#             AttributeError: if year does not exist in the daily flows dataset.
#         """
#         year = int(year)
#         if not year in self.nrfa_viewer.daily_flows_series.keys():
#             return
#         self.cur_dailyflow_year = year
#         row_position = 0
#         self.dailyFlowsTable.setRowCount(row_position)
#         for s in self.nrfa_viewer.daily_flows_series[year]:
#             flow = '{:.2f}'.format(s['flow'])
#             self.dailyFlowsTable.insertRow(row_position)
#             self.dailyFlowsTable.setItem(row_position, 0, QTableWidgetItem(str(year)))
#             self.dailyFlowsTable.setItem(row_position, 1, QTableWidgetItem(s['date']))
#             self.dailyFlowsTable.setItem(row_position, 2, QTableWidgetItem(flow))
#             self.dailyFlowsTable.setItem(row_position, 3, QTableWidgetItem(s['flag']))
#             row_position += 1
#
#     def graphAmax(self):
#         """Graph AMAX data."""
#         dlg = graphs.AmaxGraphDialog()
#         dlg.setupGraph(self.nrfa_viewer.amax_series, self.nrfa_viewer.cur_station)
#         dlg.exec_()
#
#     def graphPot(self):
#         """Graph POT data."""
#         dlg = graphs.PotGraphDialog()
#         dlg.setupGraph(self.nrfa_viewer.pot_series, self.nrfa_viewer.cur_station)
#         dlg.exec_()
#
#     def graphDailyFlows(self):
#         """Graph Daily Flows data."""
#         series_year = self.cur_dailyflow_year
#         series = self.nrfa_viewer.daily_flows_series[series_year]
#         dlg = graphs.DailyFlowsGraphDialog()
#         dlg.setupGraph(series, self.nrfa_viewer.cur_station, series_year)
#         dlg.exec_()
#
#     def exportData(self, data_name, export_func, **kwargs):
#         """Export NRFA data to csv format.
#
#         Args:
#             data_name(str): the name to use for mydialogs and default filename.
#             export_func(func): csv writing function to call.
#
#         **kwargs:
#             default_filename(str): str to use as a default filename if the 
#                 standard '{station id}_{data_name} format isn't wanted.
#                 (This will be removed prior to passing kwargs to export_func).
#         """
#         working_dir = mrt_settings.loadProjectSetting(
#             'working_directory', self.project.readPath('./temp')
#         )
#         default_filename = kwargs.pop(
#             'default_filename',
#             '{0}_{1}.csv'.format(self.nrfa_viewer.cur_station['id'], data_name)
#         )
#         default_name = os.path.join(working_dir, default_filename)
#         filename = QFileDialog(self).getSaveFileName(
#             self, 'Export {0}'.format(data_name), default_name, "CSV File (*.csv)"
#         )[0]
#         if filename:
#             try:
#                 export_func(filename, **kwargs)
#             except ValueError as err:
#                 QMessageBox.warning(
#                     self, "No {0} loaded".format(data_name), err.args[0]
#                 )
#             except Exception as err:
#                 QMessageBox.warning(
#                     self, "Failed to write {0} ".format(data_name), err.args[0]
#                 )
#
#     def exportAmaxCsv(self):
#         self.exportData('AMAX_Data', self.nrfa_viewer.exportAmaxData)
#
#     def exportPotCsv(self):
#         self.exportData('POT_Data', self.nrfa_viewer.exportPotData)
#
#     def exportDailyFlowsCsv(self):
#         export_type = self.dailyFlowExportTypeCbox.currentIndex()
#         export_year = self.cur_dailyflow_year if export_type == 0 else None
#         func_kwargs = {'export_year': export_year}
#         if export_year is not None:
#             func_kwargs['default_filename'] = '{0}_DailyFlows_Data_{1}'.format(
#                 self.nrfa_viewer.cur_station['id'], export_year
#             )
#         self.exportData(
#             'Daily_Flows_Data', self.nrfa_viewer.exportDailyFlowsData, **func_kwargs
#         )
#
#
        
        