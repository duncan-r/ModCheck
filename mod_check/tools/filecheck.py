'''
@summary: Search model files and check all files exist.

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 23rd March 2021
@copyright: Ermeview Environmental Ltd
@license: LGPL v2

Credit to Matthew Shallcross who wrote the majority of this functionality.
'''



import os
import sys
import csv
import json
import copy
from pprint import pprint
from PyQt5 import QtCore
import re
from pathlib import Path
from lxml import etree
from glob import glob

from . import globaltools as gt
from floodmodeller_api import IEF
from tmf.tuflow_model_files import TCF
from tmf.tuflow_model_files.inp.file import FileInput
from tmf.tuflow_model_files.inp.gis import GisInput
from tmf.tuflow_model_files.inp.setting import SettingInput
import tuflow


class WorkspaceFile():
    
    def __init__(self, path):
        self.rawpath = path
        self.path = Path(path)
        self.missing = 'Yes'
        
    @property
    def fullpath(self):
        return self.path.absolute()

    @property
    def name(self):
        return self.path.name

    @property
    def extension(self):
        return self.path.suffix


class Workspace():
    
    def __init__(self, workspace):
        self.workspace = workspace
        
    def readWorkspaceFile(self):
        wpath = self.workspace.filepath
        
        with open(wpath) as infile:
            xml = infile.read()

        files = [] 

        root = etree.fromstring(xml)
        for primaries in root.getchildren():
            if primaries.tag == "projectlayers":
                for maplayers in primaries.getchildren():
                    for maptags in maplayers.getchildren():
                        if maptags.tag == 'datasource':
                            text = maptags.text
                            files.append(WorkspaceFile(text))
                    
        return files
        

def loadWorkspaceFiles(workspaces):
    workspace_files = {}
    for workspace in workspaces:
        w = Workspace(workspace)
        files = w.readWorkspaceFile()
        workspace_files[workspace.name] = files
    return workspace_files


class IefSubfile():
    
    def __init__(self, path):
        self.rawpath = path
        self.path = Path(path)
        self.missing = 'Yes'
        
    @property
    def fullpath(self):
        return self.path.absolute()

    @property
    def name(self):
        return self.path.name

    @property
    def extension(self):
        return self.path.suffix

class IefFile():
    
    def __init__(self, ief):
        self.ief = ief
        self._files = []
        
    @property
    def filepath(self):
        return self.ief.filepath
    
    @property
    def files(self):
        if not self._files:
            self._files = self.findFiles()
        return self._files
    
    def findFiles(self):
        dat = IefSubfile(self.ief.Datafile)
        results = IefSubfile(self.ief.Results + '.zzn')
        ieds = [IefSubfile(i) for i in self.ief.EventData.values()]
        tcf = getattr(self.ief, '2DFile', None)
        ics = getattr(self.ief, 'InitialConditions', None)

        all_files = [dat, results]
        all_files.extend(ieds)
        if tcf:
            all_files.append(IefSubfile(tcf))
        if ics:
            all_files.append(IefSubfile(ics))
        
        return all_files
    
    

def loadIefFiles(fm_files):
    iefs = {}
    for fm in fm_files:
        if fm.fileExt == 'ief':
            ief_path = Path(fm.filepath)
            ief = IEF(ief_path)
            ief = IefFile(ief)
            iefs[str(ief_path.name)] = ief
    
    return iefs
    

class FileChecker(QtCore.QObject):
    status_signal = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
    def auditModelFiles(self, model_root):
        self.status_signal.emit('Auditing model files ...')

        errors = {}
        error_count = 0
        search_successes = 0
        
        self.status_signal.emit('Searching folders ...')
        iefs, (
            tuflow_model_files, fm_model_files, gis_files, log_files, result_files, csv_files, 
            workspace_files, other_files, ignore_files, file_tree
        ) = self.categorise(model_root)
        # audit = AuditFiles(model_root, model_files, other_files, ignore_files)
        # self.status_signal.emit('Categorising results ...')
        # result_holder = ResultHolder()
        # result_holder.ignored_files = ignore_files
        return iefs, {
            'tuflow_model': tuflow_model_files, 'fm_model': fm_model_files, 'gis': gis_files, 
            'log': log_files, 'csv': csv_files, 'result': result_files, 
            'workspace': workspace_files, 'other': other_files, 'ignore': ignore_files, 
            'tree': file_tree
        }
        
        
        self.status_signal.emit('Checking paths ...')
        
        
        # for f in audit.getModelFiles():
        #     fpath = f.getFilePath()
        #     self.status_signal.emit('Checking paths for file: {0}'.format(fpath))
        #     errorlist = []
        #
        #     if fpath in result_holder.seen_parents: continue
        #
        #     result_holder.parent = fpath
        #     result_holder.seen_parents.append(fpath)
        #
        #     for p, line in f.getPathsToCheck():
        #         if not p.isReal():
        #
        #             path_as_read = p.getPathAsRead()
        #             result_holder.addMissing(p.pathAsRead, line)
        #
        #             error_count += 1
        #             errorlist.append((p, line))
        #             search_result = p.find(audit)
        #             if len(search_result) > 0:
        #
        #                 try:
        #                     result_holder.setFound(p.pathAsRead, search_result)
        #                 except KeyError:
        #                     pass
        #                 search_successes += 1
        #     errors[f] = errorlist
            




        # result_holder.model_root = model_root
        # result_holder.summary = audit.getFileCounts()
        # result_holder.processResults()
        # result_holder.file_tree = file_tree
        # self.status_signal.emit('Check complete')
        # return result_holder

    def categorise(self, model_root):
        '''
            Method for categorising the model passed to the audit tool
            Return: tuple contain list of ModelFile and list of SomeFile instances
        '''
        tuflow_model_files = []
        fm_model_files = []
        gis_files = []
        log_files = []
        result_files = []
        workspace_files = []
        csv_files = []
        other_files = []
        ignore_files = []
        file_tree = []
        try:
            # walk the model folder structure categorising ignore, model and other (eg GIS, csv) files
            root_count = 1
            for root, dirs, files in os.walk(model_root):
                self.status_signal.emit('Searching folder {0} ...'.format(root))
                tree_level = root.replace(model_root, '', 1).count(os.sep)
                tree_indent = '|    ' * (tree_level - 1) + '+---'
                if root_count > 1:
                    file_tree.append({
                        'indent': tree_indent, 'path': os.path.basename(root), 'is_folder': True, 
                        'level': tree_level
                    })
                tree_subindent = '|    ' * (tree_level) + '-   '
                
                for f in files:
                    file_tree.append({
                        'indent': tree_subindent, 'path': f, 'is_folder': False, 'level': tree_level,
                        'fullpath': os.path.join(root, f)
                    })
                    filepath = os.path.join(root,f)
                    filepath = gt.longPathCheck(filepath)
                    
                    # IMPORTANT: The order of these checks is important
                    # Some file types have the same extension and other checks may be required.
                    # We need the order, in some cases, to make sure they're identified correctly
                    query = SomeFile(filepath)
                    if query.isIgnoreFile():
                        ignore_files.append(query)

                    elif query.isTuflowModelFile():
                        tuflow_model_files.append(query)

                    elif query.isFmModelFile():
                        fm_model_files.append(query)

                    elif query.isGisFile():
                        gis_files.append(query)

                    elif query.isLogFile():
                        log_files.append(query)

                    elif query.isResultFile():
                        result_files.append(query)

                    elif query.isWorkspaceFile():
                        workspace_files.append(query)

                    elif query.isCsvFile():
                        csv_files.append(query)
                    #
                    # # model files each have there own class describing their expected format
                    # elif query.isModelFile():
                    #     model_files.append(model_file_exts[query.getFileExt()](filepath))
                    #
                    else:
                        other_files.append(query)
                root_count += 1

        except Exception as err:
            raise
        
        # Load IEFs and remove any FM .dat files for the results files (based on being in an IEF)
        iefs, fm_model_files, result_files = self.findFmFiles(fm_model_files, result_files)
        
        return iefs, (
            tuflow_model_files, fm_model_files, gis_files, log_files, result_files, csv_files, 
            workspace_files, other_files, ignore_files, file_tree
        )
    

    def findFmFiles(self, fm_files, result_files):
        iefs = []
        dat_names = []
        new_result_files = []
        
        for f in fm_files:
            if f.fileExt.lower() == 'ief':
                ief = IEF(f.filepath)
                iefs.append(ief)
                dat_name = Path(ief.datafile).name
                dat_names.append(dat_name)
                
        for r in result_files:
            if not r.name in dat_names: 
                new_result_files.append(r)
            else:
                fm_files.append(r)

        return iefs, fm_files, new_result_files

        

# class ResultHolder():    
#     """
#     """
#
#     def __init__(self):
#         self.model_root = ''
#         self.parent = ''
#         self.seen_parents = []
#         self.missing = {}
#         self.ignored_files = []
#         self.file_tree = []
# #         self.found = {}
#
#         self._summary = {'model_files': 0, 'other_files': 0, 'ignored_files': 0, 'total_files': 0}
#         self.results = {'missing': [], 'found': [], 'found_ief': []}
#         self.results_meta = {'summary': None, 'ignored': None, 'checked': None}
#
#     @property
#     def summary(self):
#         return self._summary
#
#     @summary.setter
#     def summary(self, summary):
#         self._summary = summary
#         self._summary['total_files'] = self.getFileTotal()
#
#     def formatFileTree(self, include_files=True, format_as_text=True, include_full_paths=False):
#         output_list = []
#         fullpath_list = []
#         for f in self.file_tree:
#             if not f['is_folder']:
#                 if include_files:
#                     output_list.append('{}{}\n'.format(f['indent'], f['path']))
#                     fullpath_list.append(f['fullpath'])
#                 else:
#                     fullpath_list.append('')
#             else:
#                 if include_files:
#                     output_list.append('{}\n'.format(f['indent'][:-4]))
#                     fullpath_list.append('')
#                 output_list.append('{}{}/\n'.format(f['indent'], f['path']))
#                 fullpath_list.append('')
#
#         output = None
#         fullpaths = None
#         if format_as_text:
#             output = ''.join(output_list)
#             fullpaths = '\n'.join(fullpath_list)
#
#         if include_full_paths:
#             return output, fullpaths
#         else:
#             del fullpath_list
#             return output
#
#     def saveFileTree(self, save_path, include_files=True):
#         output = self.formatFileTree(include_files=include_files)
#         with open(save_path, 'w', newline='\n') as outfile:
#             outfile.write(output)
#
#     def addMissing(self, path, line, found=''):
#         if path in self.missing:
#             if not self.parent in self.missing[path]['parent']:
#                 self.missing[path]['parent'].append(self.parent)
#                 self.missing[path]['line'].append(line)
#         else:
#             self.missing[path] = {'parent': [self.parent], 'line': [line], 'found': found}
#
#     def setFound(self, path, found):
#         try:
#             self.missing[path]['found'] = found
#         except KeyError:
#             raise 
#
#     def summaryText(self):
#         return 'Model Files: {0:<10}\nOther Files: {1:<10}\nIgnored Files: {2:<10}\nTotal Files: {3:<10}'.format(
#             self._summary['model_files'], self._summary['other_files'], 
#             self._summary['ignored_files'], self._summary['total_files']
#         )
#
#     def getFileTotal(self):
#         return self._summary['model_files'] + self._summary['other_files'] + self._summary['ignored_files']
#
#     def processResults(self):
#         self.results = {'missing': [], 'found': [], 'found_ief': []}
#         self.results_meta['summary'] = self.summary
#         self.results_meta['ignored'] = self.ignored_files
#         self.results_meta['checked'] = self.seen_parents
#
#         for f, details in self.missing.items():
#             info = {'file': [], 'parents': []}
#             psplit = os.path.split(f)
#             filename = psplit[1] if len(psplit) > 1 else f
#             all_ief = True
#             for i, parent in enumerate(details['parent']):
#                 if not parent[-3:] == 'ief':
#                     all_ief = False
#                 info['parents'].append([parent, details['line'][i]])
#
#             if details['found']:
#                 info['file'] = [filename, details['found'], f]
#                 if all_ief:
#                     self.results['found_ief'].append(info)
#                 else:
#                     self.results['found'].append(info)
#             else:
#                 info['file'] = [filename, f]
#                 self.results['missing'].append(info)
#
#     def exportResults(self, save_path):
#         """
#         """
#         with open(save_path, 'w', newline='\n') as outfile:
#             outfile.write('\n###########################')
#             outfile.write('\n# FILE SEARCH SUMMARY')
#             outfile.write('\n###########################\n\n')
#             outfile.write('Root folder: {0}\n'.format(self.model_root))
#             outfile.write(self.summaryText())
#
#             outfile.write('\n\nFILES THAT WERE IGNORED\n')
#             if self.ignored_files:
#                 outfile.write('\n'.join([i.filepath for i in self.ignored_files]))
#             else:
#                 outfile.write('\nNo files were ignored')
#
#             outfile.write('\n\nMISSING FILES\n')
#             if self.results['missing']:
#                 outfile.write('\n'.join(m['file'][0] for m in self.results['missing']))
#             else:
#                 outfile.write('\nNo missing files')
#
#             outfile.write('\n\nFOUND FILES (Incorrect paths)\n')
#             if self.results['found'] or self.results['found_ief']:
#                 outfile.write('\n'.join(f['file'][0] for f in self.results['found']))
#                 outfile.write('\n'.join(f['file'][0] for f in self.results['found_ief']))
#             else:
#                 outfile.write('\nNo misreferenced files')
#
#             outfile.write('\n\nMODEL FILES CHECKED\n')
#             outfile.write('\n'.join([p for p in self.seen_parents]))
#
#             outfile.write('\n\n\n###########################')
#             outfile.write('\n# DETAILED RESULTS')
#             outfile.write('\n###########################\n')
#
#             outfile.write('\n\nMISSING FILES\n')
#             if self.results['missing']:
#                 for m in self.results['missing']:
#                     outfile.write('\n{0:<20}{1}'.format('File:', m['file'][0]))
#                     outfile.write('\n{0:<20}{1}'.format('Path:', m['file'][1]))
#                     outfile.write('\nReferenced by parent files:\n')
#                     outfile.write('\n'.join(['Line ({0})\t {1}'.format(p[1], p[0]) for p in m['parents']]))
#                     outfile.write('\n')
#             else:
#                 outfile.write('\nNo missing files')
#
#             outfile.write('\n\n\nFOUND FILES (Incorrect paths)\n')
#             if self.results['found'] or self.results['found_ief']:
#                 for f in self.results['found']:
#                     outfile.write('\n{0:<20}{1}'.format('File:', f['file'][0]))
#                     outfile.write('\n{0:<20}{1}'.format('Original Path:', f['file'][2]))
#                     outfile.write('\n{0:<20}{1}'.format('Found Path:', f['file'][1]))
#                     outfile.write('\nReferenced by parent files:\n')
#                     outfile.write('\n'.join(['Line ({0})\t {1}'.format(p[1], p[0]) for p in f['parents']]))
#                     outfile.write('\n')
#                 for f in self.results['found_ief']:
#                     outfile.write('\n{0:<20}{1}'.format('File:', f['file'][0]))
#                     outfile.write('\n{0:<20}{1}'.format('Original Path:', f['file'][2]))
#                     outfile.write('\n{0:<20}{1}'.format('Found Path:', f['file'][1]))
#                     outfile.write('\nReferenced by parent files:\n')
#                     outfile.write('\n'.join(['Line ({0})\t {1}'.format(p[1], p[0]) for p in f['parents']]))
#                     outfile.write('\n')
#             else:
#                 outfile.write('\nNo misreferenced files')


ignore_file_exts = ['log', 'doc', 'xlsx', 'pdf', 'xf4', 'txt', 'dbf', 'shx', 'prj']
tuflow_model_file_exts = ['tcf', 'tgc', 'tbc', 'tef', 'ecf', 'trd', 'tsoil', 'tmf']
fm_model_file_exts = ['ief', 'ied', 'iic']
gis_file_exts = ['shp', 'mif', 'mid', 'asc', 'flt', 'tif', 'tiff', 'xml', 'sqlite']
log_file_exts = ['tlf', 'tsf']
result_file_exts = ['xmdf', 'sup', '2dm', 'eof', 'dat', 'zzd', 'zzn', 'zzs']
workspace_file_exts = ['qgs']#, 'wor']
class SomeFile(object):
    '''
        Class for any file found in the model structure
    '''
    def __init__(self, filepath):
        self.filepath = filepath

        # basepath and file name
        self.path, self.name = os.path.split(filepath)
        
        # File extension (converted to lower case)
        self.fileExt = self.name.rsplit('.',1)[-1].lower()
        
        # Regular expressions
        self.empty_re = re.compile('._empty_[LPRlpr]\.(shp|mif|mid|sql|sqlite)$')
        self.messages_re = re.compile('.messages_?[LPRlpr]?\.(shp|mif|mid|sql|sqlite)$')
        self.check_re = re.compile('.(check|DEM_M|DEM_Z)_?[LPRlpr]?\.(shp|mif|mid|flt|asc|tiff{0,1}|sql|sqlite)$')
        self.result_re = re.compile('_(ccA|mmH|mmQ|mmV|PLOT_[LPRlpr]|TS|[dhvDHV]_Max|T(Dur|Exc)|ZUK|input_layers).*\.(shp|mif|mid|sql|sqlite|flt|xml)$')
        
        # File classification
        self.ignoreFile = self.fileExt in ignore_file_exts
        self.tuflow_modelFile = self.fileExt in tuflow_model_file_exts
        self.fm_modelFile = self.fileExt in fm_model_file_exts
        self.gisFile = self.fileExt in gis_file_exts
        self.resultFile = self.fileExt in result_file_exts
        self.logFile = self.fileExt in log_file_exts
        self.csvFile = self.fileExt == 'csv'
        self.workspaceFile = self.fileExt in workspace_file_exts
        
    def __str__(self):
        return f"[{self.fileExt.upper()}] {self.name}"

    def getFilePath(self):
        return self.filepath

    def getPath(self):
        return self.path

    def getName(self):
        return self.name

    def getFileExt(self):
        return self.fileExt

    def isTuflowModelFile(self):
        return self.tuflow_modelFile

    def isFmModelFile(self):
        return self.fm_modelFile

    def isGisFile(self):
        if self.gisFile:
            if re.search(self.empty_re, self.name):
                return False
            if re.search(self.messages_re, self.name):
                return False
            if re.search(self.check_re, self.name):
                return False
            if re.search(self.result_re, self.name):
                return False
            return True
        return False

    def isLogFile(self):
        return self.logFile

    def isResultFile(self):
        return self.resultFile

    def isCsvFile(self):
        return self.csvFile

    def isWorkspaceFile(self):
        return self.workspaceFile

    def isIgnoreFile(self):
        return self.ignoreFile
    
    
    
def read_xs_file(fpath, gpkg_layer=None):
    vec = None
    if gpkg_layer is not None:
        xs_layer = fpath + f"|{gpkg_layer}"
        vec = QgsVectorLayer(xs_layer, "XS Layer", "ogr")
    else:
        vec = QgsVectorLayer(fpath, "XS Layer", "ogr")
        
    xs_attributes = []
    features = vec.getFeatures()
    for feat in features():
        attrs = feat.attributes()
        xs_attributes.append({
            'source': attrs[0],
            'type': attrs[1],
            'flags': attrs[2],
            'column1': attrs[3],
            'column2': attrs[3],
            'column3': attrs[3],
        })
    return xs_attributes


TUFLOW_DEFAULTS = {
    'GIS Format': {'default': '', 'value': '', 'options': '', 'description': ''},
    # 'GRID Format': {'default': 'FLT', 'value': '', 'options': '', 'description': ''},
    'GIS Projection Check': {'default': 'WARNING', 'value': '', 'options': '', 'description': ''},
    'Snap Tolerance': {'default': '0.001', 'value': '', 'options': '', 'description': ''},
    'Units': {'default': 'METRIC', 'value': '', 'options': '', 'description': ''},
    '2D Solution Scheme': {'default': 'CLASSIC', 'value': '', 'options': '', 'description': ''},
    'Number Iterations': {'default': '2', 'value': '', 'options': '', 'description': ''},
    'First Sweep Direction': {'default': 'POSITIVE', 'value': '', 'options': 'AUTOMATIC | POSITIVE', 'description': ''},
    'Mass Balance Output': {'default': 'ON', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'Mass Balance Output Interval (s)': {'default': '900.', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'Mass Balance Corrector': {'default': 'OFF', 'value': '', 'options': 'ON | OFF', 'description': 'Not recommended for 2012 release or later'},
    'HARDWARE': {'default': 'CPU', 'value': '', 'options': '', 'description': ''},
    'BC Event Name': {'default': '', 'value': '', 'options': '', 'description': ''},
    'BC Event Source': {'default': '', 'value': '', 'options': '', 'description': '<source_text> | <source_name>'},
    'BC Zero Flow': {'default': 'OFF', 'value': '', 'options': 'OFF | START | END | START AND END', 'description': ''},
    'Bed Resistance Values': {'default': 'MANNING n', 'value': '', 'options': 'MANNING n | MANNING M | CHEZY', 'description': ''},
    'Bed Resistance Cell Sides': {'default': 'INTERROGATE', 'value': '', 'options': 'AVERAGE M | AVERAGE n | MAXIMUM n | MAXIMUM M | INTERROGATE', 'description': ''},
    'Change Zero Material Values to One': {'default': 'OFF', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'Bed Resistance Depth Interpolation': {'default': 'SPLINE n', 'value': '', 'options': 'SPLINE n | LINEAR n | LINEAR M', 'description': ''},
    'Layered FLC Default Approach': {'default': 'PORTION', 'value': '', 'options': 'PORTION | CUMULATE', 'description': ''},
    'Grid Output Cell Size': {'default': 'Not Specified', 'value': '', 'options': '', 'description': ''},
    'Grid Output Origin': {'default': 'AUTOMATIC', 'value': '', 'options': '', 'description': ''},
    'Maximums Approach': {'default': 'METHOD B', 'value': '', 'options': '', 'description': ''},
    'Map Cutoff Depth (m)': {'default': '-1.', 'value': '', 'options': '', 'description': ''},
    'Maximum Velocity Cutoff Depth (m)': {'default': '0.1', 'value': '', 'options': '', 'description': ''},
    'BSS Cutoff Depth (m)': {'default': '0.1', 'value': '', 'options': '', 'description': ''},
    'Time Output Cutoff [Depths | VxD]': {'default': 'OFF', 'value': '', 'options': '', 'description': ''},
    'ZP Hazard Cutoff Depths': {'default': '0.01 0.01 0.01', 'value': '', 'options': '', 'description': ''},
    'Map Output Corner Interpolation': {'default': 'METHOD C', 'value': '', 'options': '', 'description': ''},
    'Meshparts': {'default': 'OFF', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'UK Hazard Formula': {'default': 'D*(V+0.5)+DF', 'value': '', 'options': 'D*(V+1.5) | D*(V+0.5)+DF', 'description': ''},
    'UK Hazard Land Use': {'default': 'CONSERVATIVE', 'value': '', 'options': 'PASTURE | WOODLAND | URBAN | CONSERVATIVE | NOT SET', 'description': ''},
    'XMDF Output Compression': {'default': '1', 'value': '', 'options': '', 'description': ''},
    'Start Time Series Output (PO and LPO) (h)': {'default': '0.', 'value': '', 'options': '', 'description': 'Time in hours'},
    'CSV Time': {'default': 'HOURS', 'value': '', 'options': 'HOURS | DAYS', 'description': ''},
    'CSV Maximum Number Columns': {'default': 'UNLIMITED', 'value': '', 'options': '', 'description': ''},
    'PO Approach': {'default': 'METHOD B', 'value': '', 'options': '', 'description': ''},
    'Write PO Online': {'default': 'ON', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'Maximums and Minimums Time Series': {'default': 'ON', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'Time Series Null Value': {'default': 'Cell Elevation', 'value': '', 'options': '', 'description': ''},
    'Wetting and Drying': {'default': 'ON METHOD B', 'value': '', 'options': 'ON | ON NO SIDE CHECKS | OFF', 'description': ''},
    'Cell Side Checks': {'default': 'METHOD B', 'value': '', 'options': '', 'description': ''},
    'Supercritical': {'default': 'ON', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'Froude Check': {'default': '1.', 'value': '', 'options': '', 'description': ''},
    'Free Overfall': {'default': 'ON', 'value': '', 'options': 'ON | ON WITHOUT WEIRS | OFF', 'description': ''},
    'Free Overfall Factor': {'default': '0.6', 'value': '', 'options': '', 'description': ''},
    'Global Weir Factor': {'default': '1.', 'value': '', 'options': '', 'description': ''},
    'Shallow Depth Weir Factor Multiplier': {'default': '1.', 'value': '', 'options': '', 'description': ''},
    'Shallow Depth Weir Factor Cut Off Depth (m)': {'default': '0.0001', 'value': '', 'options': '', 'description': ''},
    'Shallow Depth Stability Approach': {'default': 'METHOD B', 'value': '', 'options': '', 'description': ''},
    'Shallow Depth Stability Factor': {'default': '0.', 'value': '', 'options': '', 'description': ''},
    'Shallow Depth Stability Cutoff (m)': {'default': '0.', 'value': '', 'options': '', 'description': ''},
    'Negative Depth In Water Level Output': {'default': 'REMOVE', 'value': '', 'options': '', 'description': ''},
    'Negative Depth Approach': {'default': 'METHOD B', 'value': '', 'options': '', 'description': ''},
    'Negative Depth Values': {'default': '-0.1, 0., 1., 1.', 'value': '', 'options': '', 'description': ''},
    'Viscosity Formulation': {'default': 'WU', 'value': '', 'options': 'CONSTANT | SMAGORINSKY | WU', 'description': ''},
    '[Smagorinsky & Constant] Viscosity Coefficients': {'default': '0.5, 0.05', 'value': '', 'options': '', 'description': ''},
    'Viscosity Approach': {'default': 'METHOD B', 'value': '', 'options': '', 'description': ''},
    'Water Level Checks': {'default': 'ON', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'HX Dry 1D Node Test': {'default': 'OFF', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'Distribute HX Flows': {'default': 'OFF', 'value': '', 'options': 'ON | OFF', 'description': 'Only applies to ESTRY'},
    'Unused HX and SX Connections': {'default': 'ERROR', 'value': '', 'options': 'ERROR | WARNING', 'description': ''},
    'Adjust Head at Estry Interface': {'default': 'OFF', 'value': '', 'options': 'ON | ON VARIABLE | OFF', 'description': ''},
    'Oblique Boundary Method': {'default': 'ON', 'value': '', 'options': '', 'description': ''},
    'Boundary Treatment': {'default': 'METHOD A', 'value': '', 'options': '', 'description': ''},
    'HQ Boundary Approach': {'default': 'METHOD C', 'value': '', 'options': '', 'description': ''},
    'HQ Weighting Factor': {'default': '1.', 'value': '', 'options': '', 'description': ''},
    'Boundary Viscosity Factor': {'default': '1.', 'value': '', 'options': '', 'description': ''},
    'Rainfall Boundaries': {'default': 'STEPPED', 'value': '', 'options': '', 'description': ''},
    'Rainfall Boundary Factor': {'default': '1.', 'value': '', 'options': '', 'description': ''},
    'Rainfall Gauges': {'default': 'UNLIMITED PER CELL', 'value': '', 'options': '', 'description': ''},
    'Line Cell Selection': {'default': 'METHOD D', 'value': '', 'options': '', 'description': ''},
    'Link 2D2D Approach': {'default': 'METHOD D', 'value': '', 'options': '', 'description': ''},
    'Link 2D2D Distribute Flow': {'default': 'ON', 'value': '', 'options': '', 'description': ''},
    'Link 2D2D Adjust Velocity Head Factor': {'default': '0.', 'value': '', 'options': '', 'description': ''},
    'Link 2D2D Weighting Factor': {'default': '1.', 'value': '', 'options': '', 'description': ''},
    'Link 2D2D Global Stability Factor': {'default': '1.', 'value': '', 'options': '', 'description': ''},
    'Reveal 1D Nodes': {'default': 'OFF', 'value': '', 'options': '', 'description': ''},
    'Inside Region': {'default': 'METHOD B', 'value': '', 'options': '', 'description': ''},
    'SA Minimum Depth': {'default': '-99999.', 'value': '', 'options': '', 'description': ''},
    'SA Proportion to Depth': {'default': 'ON', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'SX ZC Check': {'default': 'ON', 'value': '', 'options': 'ON | OFF | <value>', 'description': ''},
    'SX Head Adjustment': {'default': 'OFF', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'SX Flow Distribution Cutoff Depth': {'default': 'AUTO', 'value': '', 'options': '', 'description': ''},
    'SX Head Distribution Cutoff Depth': {'default': 'AUTO', 'value': '', 'options': '', 'description': ''},
    'SX Storage Approach': {'default': '1D NODE AVERAGE', 'value': '', 'options': '', 'description': ''},
    'SX Storage Factor': {'default': '1., 20.', 'value': '', 'options': '', 'description': ''},
    'HX Additional FLC': {'default': '0.', 'value': '', 'options': '', 'description': ''},
    'HX ZC Check': {'default': 'ON', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'Zpt Range Check': {'default': '-9998., 99998.', 'value': '', 'options': '', 'description': ''},
    'ISIS Link Approach': {'default': 'METHOD A', 'value': '', 'options': '', 'description': ''},
    'Assign Flow to Upstream 1D Node': {'default': 'ON', 'value': '', 'options': 'ON | OFF', 'description': 'Used for ISIS/FMP Link only'},
    'Latitude': {'default': '0.', 'value': '', 'options': '', 'description': 'Degress from Equator'},
    'Check Inside Grid': {'default': 'ERROR', 'value': '', 'options': '', 'description': ''},
    'Write X1D Check File': {'default': 'OFF', 'value': '', 'options': 'ON | OFF', 'description': ''},
    'VG Z Adjustment': {'default': 'MAX ZC', 'value': '', 'options': 'ZC | MAX ZC | ZH', 'description': ''},
    'Density of Air': {'default': '1.25', 'value': '', 'options': '', 'description': ''},
    'Density of Water': {'default': '1025.', 'value': '', 'options': '', 'description': ''},
    'Wind/Wave Shallow Depths': {'default': '0.2, 1.', 'value': '', 'options': '', 'description': ''},
    'Blockage Matrix': {'default': 'OFF', 'value': '', 'options': '', 'description': ''},
    'Default': {},
    'Non_Default': {},
}
TUFLOW_DEFAULTS_KEYS = TUFLOW_DEFAULTS.keys()

def read_tlf_file(filepath):
    """
     WARNING:
     - Assumes any control file that has a 'csv' extension is a BCDbase.
       Obviously won't be true when we support csv for TMF files!!
       (see control_type_setter function).
       
    This is not great at the moment. Lots of updates to handle things like the differences
    between quadtree and non-quadtree format .tlf files. A lot of this could be handled
    better / faster with some additional regexes. Probably want to do a fast first path to
    pick things up and then filter/handle additional requirements after. Very slow to run
    a lot these checks for every line. A lot of slower stuff is only hit after an initial
    regex check, which helps, but more can be done.
    
    """
    tuflow_non_defaults = {}
    
    # REGEX SEARCH PATTERNS
    CONTROL_FILE_PATTERN = '==\s(?P<path>.+)\.(?P<extension>tcf|ecf|tgc|tbc|tmf|tef|trf|tlf|trd|tsoilf)'
    
    # Need the closing one, because sometimes the 'Opening GIS' doesn't include the gpkg layer name
    # Match the 'path', then the 'extension' (gis file types), then an optional match for
    # geopackage layers (geolayer) at the end of the line
    # Example GPKG:    Closing GIS Layer 2 [Y:\PROJECTS\AEG4706_Backwell_03\TUFLOW\model\gis\AEG4706_Backwell_TCF.gpkg >> 2d_po_4706_008_L]...
    # Example SHP/MIF: Closing GIS Layer 2 [D:\Models\MoretonOnLugg\Hydraulics\model\tuflow\model\gis\2d_bc_hx_MOL_005_L.shp]...
    GIS_FILE_PATTERN = 'Closing GIS.+\[(?P<path>.+)\.(?P<extension>shp|mif|mid|tab|gpkg)(\]\.{0,3})?(\s>>\s)?(?P<geolayer>.+)?(\]\.{0,3})'

    GIS_FILTER_PATTERN = '_mmH|Q|V|ccA|_TS|_PLOT\.|messages|check.*'
    VARIABLE_PATTERN = '^\s*Set Variable[\s\w~]+==\s\w+'
    
    is_quadtree = False
    control_files = []
    gis_files = {'tcf': [], 'tgc': [], 'tbc': [], 'xs': [], 'outputs': []}
    # gis_files = []
    # tgc_files = []
    # tbc_files = []
    # xs_files = []
    params = {}
    variables = {}
    found_files = {'tcf': [], 'tgc': [], 'tbc': []}
    checks = {'checks': {}, 'warnings': {}, 'errors': {}}

    def reading_xs_match(line):
        if 'Looking for ESTRY table links' in line:
            return True
        return False

    def reading_tgc_match(line):
        if 'tgc>>' in line:
            return True
        return False

    def reading_tbc_match(line):
        if is_quadtree:
            if 'processing .tbc to determine' in line.lower():
                return True
        else:
            if 'opening bc control file' in line.lower():
                return True
        return False

    def ending_tbc_match(line):
        if is_quadtree:
            if 'allocating memory (ram)' in line.lower():
                return True
        else:
            if 'deallocating temporary memory' in line.lower():
                return True
        return False

    def control_file_match(regex, line):
        """Check if line contains a control file.
        """
        rmatch = re.search(regex, line)
        if rmatch:
            cmatch = rmatch.group(0)
            fpath = rmatch.group('path')
            fext = rmatch.group('extension')
            combined = f"{fpath}.{fext}"
            if combined not in control_files:
                control_files.append(combined)

            return True
        return False
    
    def gis_file_match(regex, line, is_tgc, is_tbc, in_xs):
        """Check if line contains a gis file.
        """
        if 'Closing GIS Layer' not in line:
            return False

        rmatch = re.search(regex, line)
        if rmatch:

            cmatch = rmatch.group(0)
            fpath = rmatch.group('path')
            fext = rmatch.group('extension')
            geolayer = rmatch.group('geolayer')
            
            # CHECK: This isn't great, as, I think, not all mid's have mif's?
            if fext in ['mid', 'tab']:
                fext = 'mif'
                
            lookup = fpath+str(geolayer)
                
            if in_xs:
                if not lookup in found_files['tcf']:
                    # xs_files.append([fpath, 'TCF', fext, geolayer])
                    gis_files['xs'].append([fpath, 'TCF', fext, geolayer])
                    gis_files['tcf'].append([fpath, 'TCF', fext, geolayer])
                    found_files['tcf'].append(lookup)
            
            if is_tgc > 0:
                if not lookup in found_files['tgc']:
                    gis_files['tgc'].append([fpath, 'TGC', fext, geolayer])
                    found_files['tgc'].append(lookup)
            elif is_tbc:
                if not lookup in found_files['tbc']:
                    gis_files['tbc'].append([fpath, 'TBC', fext, geolayer])
                    found_files['tbc'].append(lookup)
            else:
                if not lookup in found_files['tcf']:
                    gis_files['tcf'].append([fpath, 'TCF', fext, geolayer])
                    found_files['tcf'].append(lookup)
            return True
        return False

    def variable_match(regex, line):
        """Check if line contains a TUFLOW variable.
        """
        rmatch = re.search(regex, line)
        if rmatch:
            cmatch = rmatch.group(0)
            split = cmatch.split(' == ')
            split[0] = split[0].strip().replace('Set Variable ', '')
            variables[split[0]] = split[1]
            return True
        return False
    
    def gis_file_filter(regex, gis_files):
        """Final pass filter to make sure files are in the correct place.
        
        Checks that there aren't duplicates across the file stores and
        removes check, results and messages files from tcf and tgc.
        Removed results etc are put into an 'outputs' store.
        """
        filtered_files = []
        tcf_files = []
        for s in gis_files['tcf']:
            layer = s[0]
            geolayer = s[3]
            lookup = layer+str(geolayer)
            
            if not lookup in found_files['tgc'] and not lookup in found_files['tbc']:
                if not geolayer is None:
                    if re.search(gis_filter_regex, geolayer):
                        gis_files['outputs'].append([s[0], s[1], s[2], s[3]])
                    else:
                        tcf_files.append([s[0], s[1], s[2], s[3]])
                else:
                    if re.search(gis_filter_regex, layer):
                        gis_files['outputs'].append([s[0], s[1], s[2], s[3]])
                    else:
                        tcf_files.append([s[0], s[1], s[2], s[3]])

        tgc_files = []
        for s in gis_files['tgc']:
            layer = s[0]
            geolayer = s[3]
            if not geolayer is None:
                if re.search(gis_filter_regex, geolayer):
                    gis_files['outputs'].append([s[0], '', s[2], s[3]])
                else:
                    tgc_files.append([s[0], s[1], s[2], s[3]])
            else:
                if re.search(gis_filter_regex, layer):
                    gis_files['outputs'].append([s[0], '', s[2], s[3]])
                else:
                    tgc_files.append([s[0], s[1], s[2], s[3]])
            
                
        filtered_files = gis_files
        filtered_files['tcf'] = tcf_files
        filtered_files['tgc'] = tgc_files
        return filtered_files
            
    def control_type_setter(control_files): 
        """Create tuple with (filename, extension) to designate type.
        """
        output = []
        for c in control_files:
            control = Path(c)
            ext = control.suffix.upper()
            if ext == '.CSV':
                ext = 'BCDBase'

            # We find multiple .trds (list most files), but some of them only include the name
            # and not the path. Get rid if it's only the name
            if ext == '.TRD':
                if len(control.parts) < 2:
                    continue

            output.append([c, ext])
        return output
    
    def order_summary_items(summary):
        lookup = {
            'clock time': 'run_time',
            'simulation': 'simulation_status',
            '1d negative depths': 'negative_depths_1d',
            '2d negative depths': 'negative_depths_2d',
            'warnings prior': 'warnings_prior',
            'warnings during': 'warnings_during',
            'checks prior': 'checks_prior',
            'checks during': 'checks_during',
            'cme whole': 'cme_whole',
            'cme over 5': 'cme_gt_5',
            'final cumulative me': 'cme',
            'hpc hcn repeated timesteps': 'hcn_repeated_timesteps',
            'hpc nan repeated timesteps': 'nan_repeated_timesteps',
            'hpc nan warnings': 'nan_warnings',
            'resolved_name': 'resolved_name',
        }
        output = {}
        for k, v in summary.items():
            c = k.lower()
            try:
                output[lookup[c]] = v
            except KeyError:
                output[k] = v
        return output
    
    def order_params_items(params):
        output = {
            '2D Domains': [],
        }
        for k, v in params.items():
            if k.lower() == 'start 2d domain':
                output['2D Domains'].append(v)
            else:
                output[k] = v

        return output

    def format_checks(checks):
        return json.dumps(checks)
    
    def format_variables(vars):
        variables = []
        scenarios = []
        for k, v in vars.items():
            if k.lower() == '~s~' or k.lower() == '~e~': continue
            if '~' in k:
                scenarios.append({f'{k}': f'{v}'})
            else:
                variables.append({f'<<{k}>>:' f'{v}'})
        return variables, scenarios 


    entry_tcf = ''
    control_file_types = ['.tcf', '.ecf', '.tgc', '.tbc', '.tmf', '.tef', '.trf', '.tlf']
    param_lookup = [
        'bc database', 'bc event name', 'bc event source', 'start time (h)', 'end time (h)',
        'start 2d domain', '2d solution', 'gis format', 'write check files', 'hardware',
        'gpu device ids',
    ]
    control_file_regex = re.compile(CONTROL_FILE_PATTERN)
    gis_file_regex = re.compile(GIS_FILE_PATTERN)
    gis_filter_regex = re.compile(GIS_FILTER_PATTERN)
    variable_regex = re.compile(VARIABLE_PATTERN)

    summary_lines = []
    with open(filepath, 'r') as infile:
        in_summary = False
        in_tgc = 0
        in_tbc = False
        in_xs = False
        # is_quadtree = False

        for line in infile.readlines():
            line = line.replace('\\', '/')
            
            # No need to check any of the other stuff once we're in the summary
            # section. Just grab the lines and process outside the file load
            if in_summary:
                line = line.strip()
                if line == '': continue
                summary_lines.append(line)
                continue
            
            if reading_xs_match(line):
                in_xs = True

            if reading_tgc_match(line):
                pipe_count = 1
                if '|' in line:
                    pipe_count = len(line.split('|'))
                in_tgc = pipe_count
                in_tbc = False

            if reading_tbc_match(line):
                in_tbc = True
                in_tgc = 0
            if ending_tbc_match(line):
                in_tbc = False
            
            # Must catch this first or will be picked up by the control file regex 
            # Can have multiple tcfs, but only one 'main' entry point
            if line.startswith('Reading .tcf File .. '):
                line = line.replace('Reading .tcf File .. ', '')
                entry_tcf = line.strip()
                continue
                    
            # Pick up control files (tcf, tgc, etc)
            if control_file_match(control_file_regex, line):
                continue
            
            # Pick up gis files (shp, mif) - will need geodb support at some point
            if gis_file_match(gis_file_regex, line, in_tgc, in_tbc, in_xs):
                # Found the cross section (table links) command. The following GIS file will
                # be the section data, so we can reset the flag
                in_xs = False
                if in_tgc > 0:
                    in_tgc -= 1
                continue

            # Pick up 'Set Variable' commands
            if variable_match(variable_regex, line):
                continue

            # Collect check and warning messages
            if line.startswith('XY:') or line.startswith('NoXY:'):

                val = line
                if 'http' in line:
                    val = line.split('http')[0].strip()

                check_code = 'NA'
                try:
                    check_code = val.split('-')[0].split(':')[1].strip().split()[1]
                except:
                    pass

                if ': CHECK' in line:
                    if check_code not in checks['checks'].keys():
                        checks['checks'][check_code] = {'count': 1, 'message': val}
                    else:
                        checks['checks'][check_code]['count'] += 1
                elif ': WARNING' in line:
                    if check_code not in checks['warnings'].keys():
                        checks['warnings'][check_code] = {'count': 1, 'message': val}
                    else:
                        checks['warnings'][check_code]['count'] += 1
                elif ': ERROR' in line:
                    if check_code not in checks['errors'].keys():
                        checks['errors'][check_code] = {'count': 1, 'message': val}
                    else:
                        checks['errors'][check_code]['count'] += 1
            
            # Special case because it doesn't get picked up with the '==' check. It's because
            # there are multiple '==' in this one, but a a general check for it was cocking
            # other stuff up. 
            # TODO: come back and deal with this properly!
            if line.startswith('2D Solution Scheme =='):
                command, var = line.split('==', 1)
                if '!' in var:
                    var = var.split('!')[0].strip()
                else:
                    var = var.strip()
                if 'quadtree' in var.lower():
                    is_quadtree = True
                params['2D Solution Scheme'] = var

            # Find parameters set with the '==' command
            elif ' == ' in line:
                try:
                    command, var = line.strip().split(' == ')
                except:
                    command = line.replace(' == ', '')
                    var = ''

                if command == 'BC Database':
                    control_files.append(os.path.split(var)[1])

                elif command.lower() in param_lookup:
                    params[command] = var
                
                elif command in TUFLOW_DEFAULTS_KEYS:
                    for c in TUFLOW_DEFAULTS_KEYS:
                        if command == c:
                            # found_variable = True
                            var = var.split('!')[0].strip()

                            # Create a separate default and non default dict to hold the outputs so that
                            # they can be ordered in the table easily
                            if var != TUFLOW_DEFAULTS[c]['default']:
                                tuflow_non_defaults[c] = TUFLOW_DEFAULTS[c]
                                tuflow_non_defaults[c]['value'] = var
                    
            
            # Handle the other stuff that we want.
            # This can be improved a bit, but it's mostly stuff that is hard to 
            # generalise or needs a bit of special handling for text parsing
            else:
                if line.startswith('Build: '):
                    split = line.strip().split(': ')
                    params[split[0]] = split[1]

                elif line.startswith('Simulation Started: '):
                    split = line.strip().split(': ')
                    params[split[0]] = split[1]
                    
                elif line.startswith('2D Domain Cell Sizes: '):
                    split = line.strip().split(': ')
                    split[1] = split[1].strip()
                    params[split[0]] = split[1]

                elif line.startswith('2D Domain Timesteps: '):
                    split = line.strip().split(': ')
                    split[1] = split[1].strip()
                    params[split[0]] = split[1]

                elif line.startswith('Executable: '):
                    split = line.strip().split(': ')
                    split1 = split[1].split('(')
                    split[1] = split1[0].replace('(', '').strip()
                    params[split[0]] = split[1]
                    
                elif line.startswith('Output Files to be Pre-fixed by:'):
                    split = line.strip().split(': ')[1].strip()
                    params['Output Folder'] = split

                elif line.startswith('Log and message files to be pre-fixed by:'):
                    split = line.strip().split(': ')[1].strip()
                    params['Log Folder'] = split
                    
                # Mark as the summary section at the end of the file when we hit it
                elif line.startswith('SIMULATION SUMMARY'):
                    in_summary = True
                
    # Process the details we need from the summary section
    # This can be handled better and neatened up, but a lot of it requires quite
    # specific parsing, as there isn't much consistency to the file data here
    summary = {}
    for line in summary_lines:
        if line.startswith('Log File:'):
            split = line.replace("\s", "").split()[2] # Format is Log\sFile:\s+ThePathWeWant
            # print('\n\nLog file found')
            log_path = Path(split)
            summary['resolved_name'] = log_path.stem
            # print(summary['resolved_name'])
            # if '/' in split:
            #     summary['resolved_name'] = split.split('/')[-1]
            #     print('Is forward slash')
            #     print(summary['resolved_name'])
            # else:
            #     summary['resolved_name'] = split.split('\\')[-1]
            #     print('Is backward slash')
            #     print(summary['resolved_name'])

        if line.startswith('Clock Time: '):
            split = line.split('[')[0]
            var = split.replace('Clock Time:', '').strip()
            summary['Clock Time'] = var

        elif line.startswith('Simulation '):
            summary['Simulation'] = line.replace('Simulation', '').strip()
            
        elif line.startswith('WARNINGs'):
            var = line.split('[')[0].split(':')[1].strip()
            command = 'Warnings prior' if 'prior' in line else 'Warnings during'
            summary[command] = var

        elif line.startswith('CHECKs'):
            var = line.split('[')[0].split(':')[1].strip()
            command = 'Checks prior' if 'prior' in line else 'Checks during'
            summary[command] = var
            
        elif 'Negative Depths:' in line:
            var = line.split(':')[1].strip()
            command = '1D Negative Depths' if '1D' in line else '2D Negative Depths'
            summary[command] = var
        
        elif line.startswith('Peak Cumulative ME: '):
            line = line.replace('Peak Cumulative ME:', '').replace('at', '')
            split = ' '.join(line.split()).split()
            summary['CME whole'] = split[0]
            summary['CME over 5'] = split[2]

        # HPC
        elif line.startswith('HPC '):
            split = line.split('!')[0].split(':')[1].strip()
            if 'HCN Repeated' in line: 
                summary['HPC HCN Repeated Timesteps'] = split
            if 'Nan Repeated' in line: 
                summary['HPC NaN Repeated Timesteps'] = split
            if 'NaN WARNING' in line: 
                summary['HPC NaN WARNINGS'] = split

        elif line.startswith('Final Cumulative ME'):
            split = line.split(':')[1].strip()
            summary['final_cme'] = split

    # Create the output dictionary
    variables, scenarios = format_variables(variables)
    final_files = {
        'resolved_name': summary['resolved_name'],
        'entry_tcf': entry_tcf,
        'control': control_type_setter(control_files), 
        'gis': gis_file_filter(gis_filter_regex, gis_files),
        # 'gis': gis_files,
        'params': order_params_items(params),
        'variables': variables,
        'scenarios': scenarios,
        # 'summary': order_summary_items(summary),
        'summary': summary,
        'check_messages': format_checks(checks),
        'tuflow_non_defaults': tuflow_non_defaults,
    }

    return final_files


