'''
@summary: Search model files and check all files exist.

@author: Duncan R.
@created 23rd March 2021
@copyright: Duncan Runnacles 2025
@license: LGPL v2

TODO:
Bit of a mess of different functions that have been pulled together from multiple places.
Some of it is redundent, a lot of it needs refactoring to setup some nice clean data
structures and a consistent interface.
For now, just get it done and working, then come back and fix up.
'''

import os
# import sys
import csv
import json
import copy
import re
from pathlib import Path
# from lxml import etree
# from glob import glob

from PyQt5.QtCore import *
from PyQt5.Qt import pyqtSignal
from qgis.core import *

from . import globaltools as gt
from floodmodeller_api import IEF
# from tmf.tuflow_model_files import TCF
# from tmf.tuflow_model_files.inp.file import FileInput
# from tmf.tuflow_model_files.inp.gis import GisInput
# from tmf.tuflow_model_files.inp.setting import SettingInput


# class WorkspaceFile():
#
#     def __init__(self, path):
#         self.rawpath = path
#         self.path = Path(path)
#         self.missing = 'Yes'
#
#     @property
#     def fullpath(self):
#         return self.path.absolute()
#
#     @property
#     def name(self):
#         return self.path.name
#
#     @property
#     def extension(self):
#         return self.path.suffix
#
#
# class Workspace():
#
#     def __init__(self, workspace):
#         self.workspace = workspace
#
#     def readWorkspaceFile(self):
#         wpath = self.workspace.filepath
#
#         with open(wpath) as infile:
#             xml = infile.read()
#
#         files = [] 
#
#         root = etree.fromstring(xml)
#         for primaries in root.getchildren():
#             if primaries.tag == "projectlayers":
#                 for maplayers in primaries.getchildren():
#                     for maptags in maplayers.getchildren():
#                         if maptags.tag == 'datasource':
#                             text = maptags.text
#                             files.append(WorkspaceFile(text))
#
#         return files
#
#
# def loadWorkspaceFiles(workspaces):
#     workspace_files = {}
#     for workspace in workspaces:
#         w = Workspace(workspace)
#         files = w.readWorkspaceFile()
#         workspace_files[workspace.name] = files
#     return workspace_files

    
def loadZzd(zzd_path):
    """
    """
    details = {
        'Run name': {'value': '', 'description': 'Name of the run'},
        'Run date': {'value': '', 'description': 'Date that simulation was run'},
        'Dat file': {'value': '', 'description': 'FMP .dat file used for run'},
        'Version': {'value': '', 'description': 'FMP software version used'},
        'Run completed': {'value': '', 'description': 'Success status of the simulation'},
        'TUFLOW links': {'value': '', 'description': 'Number of links/connections to TUFLOW used'},
        'Unconverged timesteps': {'value': '', 'description': 'Number of unconverged timesteps (high is bad: check for timing around peak)'},
        'Proportion unconverged': {'value': '', 'description': 'Percentage of run unconverged (high is bad)'},
        'Mass balance (Peak volume)': {'value': '', 'description': 'Mass balance error as % of total volume in simulation'},
        'Mass balance (Inflow volume)': {'value': '', 'description': 'Mass balance error as % of total inflow volume from boundaries'},
    }
    warnings = {'warning': {}, 'error': {}}
    run_completed = False
    with open(zzd_path, 'r') as zzd_file:
        lines = zzd_file.readlines()
        line_count = 0
        for line in lines:
            low_line = line.lower()
            if 'run completed' in line:
                run_completed = True

            elif 'FILE=' in line:
                split_line = line.replace('  ', '')
                split_line = line.split()
                details['Run name']['value'] = split_line[0].strip()
                split_line = line.split('FILE=')
                split_line = split_line[1].split(' ')
                details['Dat file']['value'] = split_line[0].strip()
                split_line = line.split('VER=')
                details['Version']['value'] = split_line[1].strip()
            elif line.startswith('Simulation started'):
                split_line = line.split(' at ')
                details['Run date']['value'] = split_line[1].strip()
                
            elif '*** warning' in low_line:
                warning_type = line[12:18]
                if not warning_type in warnings['warning'].keys():
                    warnings['warning'][warning_type] = {'count': 1, 'info': ''}
                    info = lines[line_count + 2]
                    if lines[line_count + 3].strip() != '':
                        info += ' ' + lines[line_count + 3].strip()
                    warnings['warning'][warning_type]['info'] = info
                else:
                    warnings['warning'][warning_type]['count'] += 1
            elif '*** error' in low_line:
                error_type = line[12:18]
                if not error_type in warnings['error'].keys():
                    warnings['error'][error_type] = {'count': 1, 'info': ''}
                    info = lines[line_count + 2]
                    if lines[line_count + 3].strip() != '':
                        info += ' ' + lines[line_count + 3].strip()
                    warnings['error'][error_type]['info'] = info
                else:
                    warnings['error'][error_type]['count'] += 1
                
            elif 'number of links to tuflow' in low_line:
                split_line = line.split(':')
                details['TUFLOW links']['value'] = split_line[1].strip()
            elif 'number of unconverged timesteps' in low_line:
                split_line = line.split(':')
                details['Unconverged timesteps']['value'] = split_line[1].strip()
            elif 'proportion of simulation unconverged' in low_line:
                split_line = line.split(':')
                details['Proportion unconverged']['value'] = split_line[1].strip()
            elif 'mass balance error:' in low_line:
                split_line = line.split(':')
                details['Mass balance (Peak volume)']['value'] = split_line[1].strip()
            elif 'mass balance error [2]:' in low_line:
                split_line = line.split(':')
                details['Mass balance (Inflow volume)']['value'] = split_line[1].strip()

            line_count += 1
    
    details['Run completed']['value'] = 'Yes' if run_completed else 'No'
    has_errors = {
        'errors': len(warnings['error']) > 0,
        'warnings': len(warnings['warning']) > 0
    }
    combo_warnings = warnings['error'] | warnings['warning']
    return details, combo_warnings, has_errors


class IefFile():
    
    def __init__(self, path):
        self.rawpath = path
        self.filepath = Path(path)
        self.missing = 'Yes'
        self.resolved_path = None
        
    @property
    def fullpath(self):
        return self.filepath.absolute()

    @property
    def name(self):
        return self.filepath.name

    @property
    def extension(self):
        return self.filepath.suffix

    @property
    def ftype(self):
        return self.filepath.suffix[1:].upper()
    
    def __str__(self):
        return self.filepath.name


class FoundFiles():
    """
    """
    FILE_NOT_FOUND = -1
    FILE_EXISTS = 0
    FILE_FOUND_UNSURE = 1
    FILE_FOUND_PROBABLY = 2
    FILE_FOUND_LIKELY = 3
    GPKG_LAYER_NOT_FOUND = 4
    
    GPKG_RESULTS_LOOKUP = {
        "_1d_ccA": ["_L"],
        "_1d_mmH": ["_P"],
        "_1d_mmQ": ["_P"],
        "_1d_mmV": ["_P"],
        "_TS": ["_P", "_L", "_R"],
        "_TSF": ["_P"],
        "_TSL": ["_P"],
        "_TSMB": ["_P"],
        "_TSMB1d2d": ["_P", "_R"],
    }
    GPKG_RESULTS_LOOKUP_KEYS = GPKG_RESULTS_LOOKUP.keys()

    def __init__(self, model_root, iefs, tlfs, found_files):
        self.model_root = ''
        self.iefs = iefs
        self.tlfs = tlfs
        self.files = found_files
        
    def checkFmFiles(self, fm_files, ftypes, ignore_case=False):
        missing = []
        for i, f in enumerate(fm_files):
            status = self.FILE_NOT_FOUND
            match_file = None
            for ftype in ftypes:
                check_files = self.files[ftype]
                status, match_file = self.checkFile(f, check_files, ignore_case=ignore_case)
            
                # TODO: Bit of a hack to catch some of the IEF files that haven't been setup
                # properly
                if match_file is not None and not isinstance(match_file, Path):
                    match_file = match_file.filepath
            
                if status == self.FILE_NOT_FOUND:
                    fm_files[i].missing = 'Yes'
                    fm_files[i].resolved_path = ''
                    missing.append(f)
                elif status == self.FILE_EXISTS:
                    fm_files[i].missing = 'No'
                    fm_files[i].resolved_path = match_file
                elif status == self.FILE_FOUND_UNSURE:
                    fm_files[i].missing = 'No (3)'
                    fm_files[i].resolved_path = match_file
                elif status == self.FILE_FOUND_LIKELY:
                    fm_files[i].missing = 'No (2)'
                    fm_files[i].resolved_path = match_file
                elif status == self.FILE_FOUND_PROBABLY:
                    fm_files[i].missing = 'No (1)'
                    fm_files[i].resolved_path = match_file

                if not status == self.FILE_NOT_FOUND:
                    break
        
        return fm_files, missing
        
    def checkTuflowFiles(self, tuflow_files, ftypes):
        """
        
        Args:
            tuflow_files(list): file paths to check.
            ftypes(list): lookup keys to check self.files against
        """
        missing = []
        for i, f in enumerate(tuflow_files):
            status = self.FILE_NOT_FOUND
            match_file = None
            for ftype in ftypes:
                check_files = self.files[ftype]
                status, match_file = self.checkFile(f, check_files)
                
                if status == self.FILE_NOT_FOUND:
                    tuflow_files[i].missing = 'Yes'
                    tuflow_files[i].resolved_path = ''
                    # missing.append(f)
                elif status == self.FILE_EXISTS:
                    tuflow_files[i].missing = 'No'
                    tuflow_files[i].resolved_path = match_file.filepath
                elif status == self.FILE_FOUND_UNSURE:
                    tuflow_files[i].missing = 'No (3)'
                    tuflow_files[i].resolved_path = match_file.filepath
                elif status == self.FILE_FOUND_PROBABLY:
                    tuflow_files[i].missing = 'No (2)'
                    tuflow_files[i].resolved_path = match_file.filepath
                elif status == self.FILE_FOUND_LIKELY:
                    tuflow_files[i].missing = 'No (1)'
                    tuflow_files[i].resolved_path = match_file.filepath

                if status != self.FILE_NOT_FOUND:
                    status, new_f = self.checkGpkg(tuflow_files[i], status)
                    if status == self.GPKG_LAYER_NOT_FOUND:
                        tuflow_files[i].missing = 'Yes (GPKG)'
                        missing.append(f)
                    else:
                        # Update the layer name if we found that it has _P/L/R appended
                        tuflow_files[i].gpkg_layer = new_f.gpkg_layer
                    break
                
            if status == self.FILE_NOT_FOUND:
                missing.append(f)
        
        return tuflow_files, missing
                
    def checkFile(self, f, check_files, ignore_case=False):
        if f.filepath.is_file():
            return self.FILE_EXISTS, f

        for check in check_files:
            if ignore_case:
                if f.filepath.stem.upper() + f.filepath.suffix.upper() != check.filepath.stem.upper() + check.filepath.suffix.upper():
                    continue
            else:
                if f.filepath.stem + f.filepath.suffix.upper() != check.filepath.stem + check.filepath.suffix.upper():
                    continue
                
            fparts = f.filepath.parts
            cparts = check.filepath.parts
            if ignore_case:
                fparts = [f.upper() for f in fparts]
                cparts = [c.upper() for c in cparts]
            if fparts[-2] == cparts[-2]: # 1 parent up match
                if fparts[-3] == cparts[-3]: # 2 parents up match
                    return self.FILE_FOUND_LIKELY, check
                else:
                    return self.FILE_FOUND_PROBABLY, check
            else:
                return self.FILE_FOUND_UNSURE, check
        return self.FILE_NOT_FOUND, None
    
    def checkGpkg(self, f, file_found_status):
        is_valid = True
        if f.gpkg_layer is not None:
            is_valid = False

            try:
                gpkg_path = f"{f.resolved_path}|layername={f.gpkg_layer}"
                vec = QgsVectorLayer(gpkg_path, "GPKG layer", "ogr")
                if vec.isValid():
                    is_valid = True
                
                else:
                    # For the results and check files, TUFLOW seems to put _P/L/R on the end of the layer
                    # names within the .gpkg DB, but doesn't include them in the .tlf.
                    # Check if it's a results file and if it has an expected layer name end match
                    lyr = QgsVectorLayer(f"{f.resolved_path}", "GPKG Layer", "ogr")
                    sublayers = lyr.dataProvider().subLayers()
                    
                    for sublayer in sublayers:
                        name = sublayer.split('!!::!!')[1]
                        if f.gpkg_layer == name:
                            is_valid = True
                            break
                        elif f.gpkg_layer + "_P" == name:
                            is_valid = True
                            f.gpkg_layer += "_P"
                            break
                        elif f.gpkg_layer + "_L" == name:
                            is_valid = True
                            f.gpkg_layer += "_L"
                            break
                        elif f.gpkg_layer + "_R" == name:
                            is_valid = True
                            f.gpkg_layer += "_R"
                            break

            except Exception as err:
                is_valid = False

        if is_valid:
            return file_found_status, f
        else:
            return self.GPKG_LAYER_NOT_FOUND, f


    # @property
    # def summary(self):
    #     return self._summary
    #
    # @summary.setter
    # def summary(self, summary):
    #     self._summary = summary
    #     self._summary['total_files'] = self.getFileTotal()

    # def formatFileTree(self, include_files=True, format_as_text=True, include_full_paths=False):
    #     output_list = []
    #     fullpath_list = []
    #     for f in self.file_tree:
    #         if not f['is_folder']:
    #             if include_files:
    #                 output_list.append('{}{}\n'.format(f['indent'], f['path']))
    #                 fullpath_list.append(f['fullpath'])
    #             else:
    #                 fullpath_list.append('')
    #         else:
    #             if include_files:
    #                 output_list.append('{}\n'.format(f['indent'][:-4]))
    #                 fullpath_list.append('')
    #             output_list.append('{}{}/\n'.format(f['indent'], f['path']))
    #             fullpath_list.append('')
    #
    #     output = None
    #     fullpaths = None
    #     if format_as_text:
    #         output = ''.join(output_list)
    #         fullpaths = '\n'.join(fullpath_list)
    #
    #     if include_full_paths:
    #         return output, fullpaths
    #     else:
    #         del fullpath_list
    #         return output

    # def saveFileTree(self, save_path, include_files=True):
    #     output = self.formatFileTree(include_files=include_files)
    #     with open(save_path, 'w', newline='\n') as outfile:
    #         outfile.write(output)

    # def addMissing(self, path, line, found=''):
    #     if path in self.missing:
    #         if not self.parent in self.missing[path]['parent']:
    #             self.missing[path]['parent'].append(self.parent)
    #             self.missing[path]['line'].append(line)
    #     else:
    #         self.missing[path] = {'parent': [self.parent], 'line': [line], 'found': found}
    #
    # def setFound(self, path, found):
    #     try:
    #         self.missing[path]['found'] = found
    #     except KeyError:
    #         raise 

    # def summaryText(self):
    #     return 'Model Files: {0:<10}\nOther Files: {1:<10}\nIgnored Files: {2:<10}\nTotal Files: {3:<10}'.format(
    #         self._summary['model_files'], self._summary['other_files'], 
    #         self._summary['ignored_files'], self._summary['total_files']
    #     )

    # def getFileTotal(self):
    #     return self._summary['model_files'] + self._summary['other_files'] + self._summary['ignored_files']

    # def processResults(self):
    #     self.results = {'missing': [], 'found': [], 'found_ief': []}
    #     self.results_meta['summary'] = self.summary
    #     self.results_meta['ignored'] = self.ignored_files
    #     self.results_meta['checked'] = self.seen_parents
    #
    #     for f, details in self.missing.items():
    #         info = {'file': [], 'parents': []}
    #         psplit = os.path.split(f)
    #         filename = psplit[1] if len(psplit) > 1 else f
    #         all_ief = True
    #         for i, parent in enumerate(details['parent']):
    #             if not parent[-3:] == 'ief':
    #                 all_ief = False
    #             info['parents'].append([parent, details['line'][i]])
    #
    #         if details['found']:
    #             info['file'] = [filename, details['found'], f]
    #             if all_ief:
    #                 self.results['found_ief'].append(info)
    #             else:
    #                 self.results['found'].append(info)
    #         else:
    #             info['file'] = [filename, f]
    #             self.results['missing'].append(info)

    # def exportResults(self, save_path):
    #     """
    #     """
    #     with open(save_path, 'w', newline='\n') as outfile:
    #         outfile.write('\n###########################')
    #         outfile.write('\n# FILE SEARCH SUMMARY')
    #         outfile.write('\n###########################\n\n')
    #         outfile.write('Root folder: {0}\n'.format(self.model_root))
    #         outfile.write(self.summaryText())
    #
    #         outfile.write('\n\nFILES THAT WERE IGNORED\n')
    #         if self.ignored_files:
    #             outfile.write('\n'.join([i.filepath for i in self.ignored_files]))
    #         else:
    #             outfile.write('\nNo files were ignored')
    #
    #         outfile.write('\n\nMISSING FILES\n')
    #         if self.results['missing']:
    #             outfile.write('\n'.join(m['file'][0] for m in self.results['missing']))
    #         else:
    #             outfile.write('\nNo missing files')
    #
    #         outfile.write('\n\nFOUND FILES (Incorrect paths)\n')
    #         if self.results['found'] or self.results['found_ief']:
    #             outfile.write('\n'.join(f['file'][0] for f in self.results['found']))
    #             outfile.write('\n'.join(f['file'][0] for f in self.results['found_ief']))
    #         else:
    #             outfile.write('\nNo misreferenced files')
    #
    #         outfile.write('\n\nMODEL FILES CHECKED\n')
    #         outfile.write('\n'.join([p for p in self.seen_parents]))
    #
    #         outfile.write('\n\n\n###########################')
    #         outfile.write('\n# DETAILED RESULTS')
    #         outfile.write('\n###########################\n')
    #
    #         outfile.write('\n\nMISSING FILES\n')
    #         if self.results['missing']:
    #             for m in self.results['missing']:
    #                 outfile.write('\n{0:<20}{1}'.format('File:', m['file'][0]))
    #                 outfile.write('\n{0:<20}{1}'.format('Path:', m['file'][1]))
    #                 outfile.write('\nReferenced by parent files:\n')
    #                 outfile.write('\n'.join(['Line ({0})\t {1}'.format(p[1], p[0]) for p in m['parents']]))
    #                 outfile.write('\n')
    #         else:
    #             outfile.write('\nNo missing files')
    #
    #         outfile.write('\n\n\nFOUND FILES (Incorrect paths)\n')
    #         if self.results['found'] or self.results['found_ief']:
    #             for f in self.results['found']:
    #                 outfile.write('\n{0:<20}{1}'.format('File:', f['file'][0]))
    #                 outfile.write('\n{0:<20}{1}'.format('Original Path:', f['file'][2]))
    #                 outfile.write('\n{0:<20}{1}'.format('Found Path:', f['file'][1]))
    #                 outfile.write('\nReferenced by parent files:\n')
    #                 outfile.write('\n'.join(['Line ({0})\t {1}'.format(p[1], p[0]) for p in f['parents']]))
    #                 outfile.write('\n')
    #             for f in self.results['found_ief']:
    #                 outfile.write('\n{0:<20}{1}'.format('File:', f['file'][0]))
    #                 outfile.write('\n{0:<20}{1}'.format('Original Path:', f['file'][2]))
    #                 outfile.write('\n{0:<20}{1}'.format('Found Path:', f['file'][1]))
    #                 outfile.write('\nReferenced by parent files:\n')
    #                 outfile.write('\n'.join(['Line ({0})\t {1}'.format(p[1], p[0]) for p in f['parents']]))
    #                 outfile.write('\n')
    #         else:
    #             outfile.write('\nNo misreferenced files')


class FileFinder(QObject):
    status_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
    def auditModelFiles(self, model_root):
        self.status_signal.emit('Searching folders ...')

        iefs, (
            tuflow_model_files, fm_model_files, gis_files, log_files, result_files, csv_files, 
            workspace_files, other_files, ignore_files, file_tree
        ) = self.categorise(model_root)
        tlfs = self.extractTlfs(log_files)
        located_files = {
            'tuflow_model': tuflow_model_files, 'fm_model': fm_model_files, 'gis': gis_files, 
            'log': log_files, 'csv': csv_files, 'result': result_files, 
            'workspace': workspace_files, 'other': other_files, 'ignore': ignore_files, 
            'tree': file_tree
        }
        found_files = FoundFiles(model_root, iefs, tlfs, located_files)
        return found_files, iefs, tlfs
        
    def extractTlfs(self, log_files):
        output = []
        for l in log_files:
            suffixes = l.filepath.suffixes
            if '.tlf' in suffixes and not '.hpc' in suffixes:
                output.append(l)
        return output

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
                        
                    elif query.isBcdbaseFile():
                        tuflow_model_files.append(query)

                    elif query.isCsvFile():
                        csv_files.append(query)

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
                dat_name = Path(ief.datafile).stem
                dat_names.append(dat_name)
                
        for r in result_files:
            if not r.name in dat_names: 
                new_result_files.append(r)
            else:
                fm_files.append(r)

        return iefs, fm_files, new_result_files

        

ignore_file_exts = ['log', 'doc', 'pdf', 'xf4', 'xf8', 'txt', 'dbf', 'shx', 'prj', 'iml', 'feb', 'ext', 'pxy', 'hdr', 'id', 'ext']
tuflow_model_file_exts = ['tcf', 'tgc', 'tbc', 'tef', 'ecf', 'trd', 'tsoil', 'tmf']
fm_model_file_exts = ['ief', 'ied', 'iic']
gis_file_exts = ['shp', 'mif', 'mid', 'asc', 'flt', 'tif', 'tiff', 'xml', 'gpkg', 'tin']
log_file_exts = ['tlf', 'tsf']
result_file_exts = ['xmdf', 'sup', '2dm', 'eof', 'dat', 'zzd', 'zzn', 'zzs', 'bmp']
workspace_file_exts = ['qgs']#, 'wor']
class SomeFile(object):
    '''
        Class for any file found in the model structure
    '''
    def __init__(self, filepath):
        self.raw_path = filepath
        self.filepath = Path(filepath)

        # Regular expressions
        self.empty_re = re.compile('._empty_[LPRlpr]\.(shp|mif|mid|sql|sqlite)$')
        self.messages_re = re.compile('.messages_?[LPRlpr]?\.(shp|mif|mid|sql|sqlite)$')
        self.check_re = re.compile('.(check|DEM_M|DEM_Z)_?[LPRlpr]?\.(shp|mif|mid|flt|asc|tiff{0,1}|sql|sqlite)$')
        self.result_re = re.compile('_(ccA|mmH|mmQ|mmV|PLOT_[LPRlpr]|TS|[dhvDHV]_Max|T(Dur|Exc)|ZUK|input_layers).*\.(shp|mif|mid|sql|sqlite|flt|xml)$')
        self.dbase_re = re.compile('(?i)(dbase|database|bc_{0,1}db)')
        
        # File classification
        self.ignoreFile = self.fileExt in ignore_file_exts
        self.tuflow_modelFile = self.fileExt in tuflow_model_file_exts
        self.fm_modelFile = self.fileExt in fm_model_file_exts
        self.gisFile = self.fileExt in gis_file_exts
        self.resultFile = self.fileExt in result_file_exts
        self.logFile = self.fileExt in log_file_exts
        self.csvFile = self.fileExt == 'csv'
        self.workspaceFile = self.fileExt in workspace_file_exts
        
    @property
    def path(self):
        return self.filepath.resolve()

    @property
    def name(self):
        return self.filepath.stem

    @property
    def fileExt(self):
        return self.filepath.suffix[1:].lower()

    @property
    def parent1(self):
        return self.filepath.parent

    @property
    def parent2(self):
        return self.filepath.parent.parent
        
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
    
    def isBcdbaseFile(self):
        if re.search(self.dbase_re, self.name):
            return True
        return False

    def isCsvFile(self):
        return self.csvFile

    def isWorkspaceFile(self):
        return self.workspaceFile

    def isIgnoreFile(self):
        return self.ignoreFile


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


class TuflowFile():
    
    def __init__(self, path, parent_type=None, gpkg_layer=None):
        self.rawpath = path
        self.filepath = Path(path)
        self.missing = 'Yes'
        self.resolved_path = None
        self.gpkg_layer = gpkg_layer
        if parent_type is None:
            self.parent_type = ''
        else:
            self.parent_type = parent_type
        
    @property
    def fullpath(self):
        return self.filepath.absolute()

    @property
    def name(self):
        return self.filepath.name

    @property
    def extension(self):
        return self.filepath.suffix

    @property
    def ftype(self):
        temp = self.filepath.suffix[1:].upper()
        if self.parent_type:
            temp = f"{temp} ({self.parent_type})"
        return temp
    
    def __str__(self):
        return self.filepath.name


def readTlfFile(filepath):
    """TUFLOW TLF file parser.
       
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
    # Example GPKG:    Closing GIS Layer 2 [C:\some\folders\TUFLOW\model\gis\Modelpackagename.gpkg >> 2d_po_4706_008_L]...
    # Example SHP/MIF: Closing GIS Layer 2 [D:\some\folders\tuflow\model\gis\2d_bc_hx_model_001_L.shp]...
    GIS_FILE_PATTERN = 'Closing GIS.+\[(?P<path>.+)\.(?P<extension>shp|mif|mid|tab|gpkg)(\]\.{0,3})?(\s>>\s)?(?P<geolayer>.+)?(\]\.{0,3})'

    GIS_FILTER_PATTERN = '_mmH|Q|V|ccA|_TS|_PLOT\.|messages|check.*'
    VARIABLE_PATTERN = '^\s*Set Variable[\s\w~]+==\s\w+'
    
    is_quadtree = False
    in_runtime = False
    control_files = []
    params = {}
    variables = {}
    gis_files = {'tcf': [], 'tgc': [], 'tbc': [], 'xs': [], 'outputs': []}
    found_files = {'tcf': [], 'tgc': [], 'tbc': [], 'control': []}
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
            if combined not in found_files['control']:
                found_files['control'].append(combined)
                control_files.append(TuflowFile(combined, parent_type='TCF'))

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
            combined = f"{fpath}.{fext}"
            
            # CHECK: This isn't great, as, I think, not all mid's have mif's?
            if fext in ['mid', 'tab']:
                fext = 'mif'
                
            lookup = fpath+str(geolayer)
                
            if in_xs:
                if not lookup in found_files['tcf']:
                    gis_files['xs'].append(TuflowFile(combined, parent_type='TCF', gpkg_layer=geolayer))
                    gis_files['tcf'].append(TuflowFile(combined, parent_type='TCF', gpkg_layer=geolayer))
                    found_files['tcf'].append(lookup)
            
            if is_tgc > 0:
                if not lookup in found_files['tgc']:
                    gis_files['tgc'].append(TuflowFile(combined, parent_type='TGC', gpkg_layer=geolayer))
                    found_files['tgc'].append(lookup)
            elif is_tbc:
                if not lookup in found_files['tbc']:
                    gis_files['tbc'].append(TuflowFile(combined, parent_type='TBC', gpkg_layer=geolayer))
                    found_files['tbc'].append(lookup)
            else:
                if not lookup in found_files['tcf']:
                    gis_files['tcf'].append(TuflowFile(combined, parent_type='TCF', gpkg_layer=geolayer))
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
    
    def in_runtime_match(line):
        if 'initialising run time summary' in line:
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
            layer = s.rawpath
            geolayer = s.gpkg_layer
            lookup = s.rawpath+str(geolayer)
            
            if not lookup in found_files['tgc'] and not lookup in found_files['tbc']:
                if not geolayer is None:
                    if re.search(gis_filter_regex, geolayer):
                        gis_files['outputs'].append(TuflowFile(layer, parent_type=s.parent_type, gpkg_layer=geolayer))
                    else:
                        tcf_files.append(TuflowFile(layer, parent_type=s.parent_type, gpkg_layer=geolayer))
                else:
                    if re.search(gis_filter_regex, layer):
                        gis_files['outputs'].append(TuflowFile(layer, parent_type=s.parent_type, gpkg_layer=geolayer))
                    else:
                        tcf_files.append(TuflowFile(layer, parent_type=s.parent_type, gpkg_layer=geolayer))

        tgc_files = []
        for s in gis_files['tgc']:
            layer = s.rawpath
            geolayer = s.gpkg_layer
            if not geolayer is None:
                if re.search(gis_filter_regex, geolayer):
                    gis_files['outputs'].append(TuflowFile(layer, parent_type=s.parent_type, gpkg_layer=geolayer))
                else:
                    tgc_files.append(TuflowFile(layer, parent_type=s.parent_type, gpkg_layer=geolayer))
            else:
                if re.search(gis_filter_regex, layer):
                    gis_files['outputs'].append(TuflowFile(layer, parent_type=s.parent_type, gpkg_layer=geolayer))
                else:
                    tgc_files.append(TuflowFile(layer, parent_type=s.parent_type, gpkg_layer=geolayer))
            
                
        filtered_files = gis_files
        filtered_files['tcf'] = tcf_files
        filtered_files['tgc'] = tgc_files
        return filtered_files
            
    def control_type_setter(control_files): 
        """Create tuple with (filename, extension) to designate type.
        """
        output = []
        for c in control_files:
            control = c.filepath
            ext = control.suffix.upper()
            if ext == '.CSV':
                ext = 'BCDBase'

            # We find multiple .trds (like most files), but some of them only include the name
            # and not the path. Get rid if it's only the name
            if ext == '.TRD':
                if len(control.parts) < 2:
                    continue

            output.append(c)
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
            # elif k.lower() == 'bc event source':
            #     variables.append(('BC Event Source', v))
            # elif k.lower() == 'bc event text':
            #     variables.append(('BC Event Text', v))
            else:
                output[k] = v

        return output

    def format_checks(checks):
        return json.dumps(checks)
    
    def format_variables(vars):
        variables = []
        scenarios = []
        for k, v in vars.items():
            # Don't get the 'default' values without a number. They're the same as the '~s1~' or
            # '~e1~' values anyway. Ignore so we don't get duplicates.
            if k.lower() == '~s~' or k.lower() == '~e~': continue
            if '~' in k:
                scenarios.append((f'{k}', f'{v}'))
            elif k == 'BC Event Source':
                variables.append((k, v))
            else:
                variables.append((f'<<{k}>>', f'{v}'))
        return variables, scenarios 


    entry_tcf = ''
    home_folder = ''
    home_found = False
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

            # Mark as the summary section at the end of the file when we hit it
            if line.startswith('SIMULATION SUMMARY'):
                in_summary = True
                continue
            
            # Don't need to do lots of expensive checks if we've reached the model run outputs.
            # Skip lines until we hit the summary (above) which will handle parsing the info
            # at the end of the file
            if in_runtime:
                continue
            if in_runtime_match(line):
                in_runtime = True
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
            
            if not home_found:
                # Must catch this first or will be picked up by the control file regex 
                # Can have multiple tcfs, but only one 'main' entry point
                if line.startswith('Reading .tcf File .. '):
                    line = line.replace('Reading .tcf File .. ', '')
                    entry_tcf = TuflowFile(line.strip(), parent_type='Root')
                    continue
                
                # Root path (tcf directory) for the model
                if line.startswith('Home Folder:'):
                    home_folder = Path(line.strip()[13:])
                    
                    # Sometimes (rarely) tcfs can be a name only (don't know why, possibly only
                    # happens in older versions of TUFLOW?). If it is, we join it to the home 
                    # folder to create a full path. As far as I know, this always comes after the 
                    # "Reading .tcf File" line
                    if entry_tcf and not entry_tcf.filepath.is_absolute():
                        entry_tcf = home_folder / entry_tcf
                    home_found = True
                    
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
            # there are multiple '==' in this one, but a a general check for it was messing
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

                if command.startswith('BC'):
                    if command == 'BC Database':
                        # control_files.append(os.path.split(var)[1])
                        if var not in found_files['control']:
                            found_files['control'].append(var)
                            control_files.append(TuflowFile(var, parent_type='TCF'))
                            
                    elif command == 'BC Event Source':
                        splitvar = var.split('|')
                        if not 'BC Event Source' in variables.keys():
                            variables['BC Event Source'] = {}
                        variables['BC Event Source'][splitvar[0].strip()] = splitvar[1].strip()

                    elif command == 'BC Event Text':
                        variables.append(('BC Event Text', var))

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
                    
                # # Mark as the summary section at the end of the file when we hit it
                # elif line.startswith('SIMULATION SUMMARY'):
                #     in_summary = True
                
    # Process the details we need from the summary section
    # This can be handled better and neatened up, but a lot of it requires quite
    # specific parsing, as there isn't much consistency to the file data here
    summary = {}
    for line in summary_lines:
        if line.startswith('Log File:'):
            split = line.replace("\s", "").split()[2] # Format is Log\sFile:\s+ThePathWeWant
            log_path = Path(split)
            summary['resolved_name'] = log_path.stem

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
        'home_folder': home_folder,
        'resolved_name': summary['resolved_name'],
        'entry_tcf': entry_tcf,
        'control': control_type_setter(control_files), 
        'gis': gis_file_filter(gis_filter_regex, gis_files),
        'params': order_params_items(params),
        'variables': variables,
        'scenarios': scenarios,
        # 'summary': order_summary_items(summary),
        'summary': summary,
        # 'check_messages': format_checks(checks),
        'check_messages': checks,
        'tuflow_non_defaults': tuflow_non_defaults,
    }

    return final_files
    
    
def readXsFile(fpath, gpkg_layer=None):
    vec = None
    if gpkg_layer is not None:
        xs_layer = f"{fpath}|layername={gpkg_layer}"
        vec = QgsVectorLayer(xs_layer, "XS Layer", "ogr")
    else:
        vec = QgsVectorLayer(str(fpath), "XS Layer", "ogr")
        
    field_names = [f.name() for f in vec.fields()]
    has_fid = field_names[0].lower() == 'fid'
    fid_shift = 1 if has_fid else 0
    xs_attributes = []
    for feat in vec.getFeatures():
        attrs = feat.attributes()
        xs_attributes.append({
            'source': attrs[0 + fid_shift],
            'type': attrs[1 + fid_shift],
            'flags': attrs[2 + fid_shift],
            'column1': attrs[3 + fid_shift],
            'column2': attrs[4 + fid_shift],
            'column3': attrs[5 + fid_shift],
        })
    return xs_attributes


class FmModel():
    
    def __init__(self, ief):
        self.ief = ief
        self.dat = None
        self.ics = None
        self.results = []
        self.ieds = []
        self.tcf = None
        self.has_zzd = False
        self.diagnostics = {'details': {}, 'warnings': {}}
        self.has_errors = False
        self.has_warnings = False
        self.params = {'changed': {}, 'default': {}} 
        self.missing = []
        self.loaded = False
        self._variables = {
            'Slot': {'var_name': 'Priessmann Slot', 'checkval': '0', 'value_default': ['Yes', 'No'], 'description': 'Inserts an infinitesimally small slot in sections: not usually required for high flow models'},
            'FroudeLower': {'var_name': 'Froude Lower Limit', 'value_default': ['value', '0.75'], 'description': 'Affects the way that supercritical flow is approximated by phasing out dA/dx between values'},
            'FroudeUpper': {'var_name': 'Froude Upper Limit', 'value_default': ['value', '0.9'], 'description': 'Affects the way that supercritical flow is approximated by phasing out dA/dx between values'},
            'PivotalChoice': {'var_name': 'Pivotal Choice', 'value_default': ['value', '0.1'], 'description': 'Specifies the degree of matrix pivoting: expert use only is recommended'},
            'MatrixDummy': {'var_name': 'Matrix Dummy', 'value_default': ['value', '0'], 'description': 'Helps to maintain the matrix solution structure: expert use only (sometimes helps with many moving structures - small changes only)'},
            'NewMatrixDummy': {'var_name': 'Global Matrix Dummy', 'value_default': ['value', '0'], 'description': 'Same as Matrix Dummy but applied to the main calculation engine.'},
            'Temperature': {'var_name': 'Temperature', 'value_default': ['value', '10'], 'description': 'Temperate of the water'},
            'Dflood': {'var_name': 'dflood', 'value_default': ['value', '3'], 'description': 'Height of glass walling applied to river sections'},
            'Htol': {'var_name': 'htol', 'value_default': ['value', '0.01'], 'description': 'Stage tolerance: how much stage can vary between time steps (both absolute and relative)'},
            'Qtol': {'var_name': 'qtol', 'value_default': ['value', '0.01'], 'description': 'Flow tolerance: how much flow can vary between time steps (both absolute and relative)'},
            'Minitr': {'var_name': 'minitr', 'value_default': ['value', '2'], 'description': 'Minimum number of iterations at each timestep'},
            'Maxitr': {'var_name': 'maxitr', 'value_default': ['value', '6'], 'description': 'Maximum number of iterations allowed at each timestep (prime numbers are recommended)'},
            'Theta': {'var_name': 'theta', 'value_default': ['value', '0.7'], 'description': 'Preissmann box weighting factor: fully implicit at 1.0 (justified changes include tidal models and many pumps, etc)'},
            'Alpha': {'var_name': 'alpha', 'value_default': ['value', '0.7'], 'description': 'Under relaxation parameter: sets weighting towards the previous iterations result (value of 1.0 is no relaxation)'},
            'Sconmx': {'var_name': 'sconmx', 'value_default': ['value', '100'], 'description': 'Maximum piezometric head above symmetrical conduit soffit'},
            'Dltmax': {'var_name': 'dltmax', 'value_default': ['value', '1'], 'description': 'Maximum transition gradient for lateral spills (dQ/dh)'},
            'Dilmax': {'var_name': 'dilmax', 'value_default': ['value', '1000'], 'description': 'Maximum transition gradient for inline spills (dQ/dh)'},
            'Swop': {'var_name': 'swop', 'value_default': ['value', '0.001'], 'description': 'Determines when to apply "special case" equations to spill units'},
            'Weight': {'var_name': 'Weight', 'value_default': ['value', '0.1'], 'description': 'Under relaxation parameter applied to spills'},
            'SpillThreshold': {'var_name': 'Spill Threshold', 'value_default': ['value', '1E-6'], 'description': 'Difference in adjacent water levels at spill at which 0 flow applied'},
            'Dfloodb': {'var_name': 'dfloodb', 'value_default': ['value', '10'], 'description': 'Height of glass walling applied to bridge sections'},
            'Pcmxvd': {'var_name': 'pcmxvd', 'value_default': ['value', '2'], 'description': 'Dummy point interpolation percentage for calculating cross section properties'},
            'Pswide': {'var_name': 'pswide', 'value_default': ['value', '0'], 'description': 'Width of triangular priessmann slot'},
            'Psdeep': {'var_name': 'psdeep', 'value_default': ['value', '0'], 'description': 'Depth of triangular preissmann slot'},
            'DHLinearise': {'var_name': 'Orifice Linearisation Head', 'value_default': ['value', '0'], 'description': 'Can help prevent oscillations at low head differences in orifice units'},
            'BottomSlotDepth': {'var_name': 'Bottom Slot Depth', 'value_default': ['value', '0'], 'description': 'Depth of bottom slot in conduit units'},
            'BottomSlotdh': {'var_name': 'Bottom Slot dh', 'value_default': ['value', '0'], 'description': 'Height of bottom slot above invert in conduit units'},
            'TopSlotHeight': {'var_name': 'Top Slot Height', 'value_default': ['value', '0'], 'description': 'Height of top slot in conduit units'},
            'TopSlotdh': {'var_name': 'Top Slot dh', 'value_default': ['value', '0'], 'description': 'Depth of top slot below soffit in conduit units'},
            '2DScheme': {'var_name': '2D Scheme', 'check_value': '0', 'value_default': ['value', 'No'], 'description': 'Whether a 2D scheme (like TUFLOW) is being used'},
            '2DTimestep': {'var_name': '2D Timestep', 'value_default': ['value', ''], 'description': '2D Timestep - may also be set and/or overriden in the 2D model'},
            'LaunchDoublePrecisionVersion': {'var_name': 'Double Precision FMP', 'checkval': '0', 'value_default': ['Yes', 'No'], 'description': 'Whether double precision FMP is being used'},
            '2DDoublePrecision': {'var_name': 'Double Precision TUFLOW', 'checkval': '0', 'value_default': ['Yes', 'No'], 'description': 'Whether double precision 2D model (like TUFLOW) is being used'},
            '2DOptions': {'var_name': '2D Run Options', 'value_default': ['value', ''], 'description': 'Run options (scenarios/events) for 2D scheme'},
        }
        
    @property
    def filepath(self):
        return self.ief.filepath
    
    @property
    def files(self):
        fm_files = [self.dat]
        if self.ics:
            fm_files.append(self.ics)
        if self.tcf:
            fm_files.append(self.tcf)
        fm_files.extend(self.results)
        fm_files.extend(self.ieds)
        return fm_files
        
    @property
    def zzd(self):
        for r in self.results:
            if r.filepath.suffix.upper() == '.ZZD':
                return r
        return None

    @property
    def zzn(self):
        for r in self.results:
            if r.filepath.suffix.upper() == '.ZZN':
                return r
        return None
    
    @property
    def has_non_defaults(self):
        ignore = [
            '2D Scheme', '2D Timestep', 'Double Precision FMP', 'Double Precision TUFLOW',
            '2D Run Options',
        ]
        non_default_keys = self.params['changed'].keys()
        failed = False
        for k in non_default_keys:
            if k not in ignore:
                return True
        return False
    
    def findFiles(self):
        self.dat = IefFile(self.ief.Datafile)
        self.results = [
            IefFile(self.ief.Results + '.zzn'),
            IefFile(self.ief.Results + '.zzd')
        ]
        self.ieds = [IefFile(i) for i in self.ief.EventData.values()]
        tcf = getattr(self.ief, '2DFile', None)
        ics = getattr(self.ief, 'InitialConditions', None)
        if tcf:
            self.tcf = IefFile(tcf)
        if ics:
            self.ics = IefFile(ics)
    
    def checkParams(self):

        for variable, variable_dict in self._variables.items():
            ief_value = getattr(self.ief, variable, None)
            has_checkval = True if 'checkval' in variable_dict.keys() else False
            check_value = variable_dict['value_default'][0] if not has_checkval else variable_dict['checkval']
            used_value = variable_dict['value_default'][0] if not variable_dict['value_default'][0] == 'value' else ief_value
            
            if ief_value is not None and not ief_value == check_value:
                self.params['changed'][variable_dict['var_name']] = {
                    'name': variable, 'value': used_value, 
                    'default': variable_dict['value_default'][1],
                    'description': variable_dict['description'],
                }
            else:
                self.params['default'][variable_dict['var_name']] = {
                    'name': variable, 'value': used_value, 
                    'default': variable_dict['value_default'][1],
                    'description': variable_dict['description'],
                }
                
    def loadDiagnostics(self):
        self.has_zzd = False
        for f in self.files:
            if f.extension.upper() == '.ZZD':
                self.has_zzd = True
                if f.resolved_path and f.resolved_path.is_file():
                    details, warnings, has_errors = loadZzd(f.resolved_path)
                    self.diagnostics['details'] = details
                    self.diagnostics['warnings'] = warnings
                    self.has_errors = has_errors['errors']
                    self.has_warnings = has_errors['warnings']


class TuflowModel():
    
    def __init__(self, tlf_path):
        self.tlf_path = tlf_path
        self.resolved_name = ''
        self.tcf = None
        self.control_files = []
        self.gis_files = []
        self.xs_files = []
        self.parameters = []
        self.variables = []
        self.scenarios = []
        self.summary = {}
        self.warnings = []
        self.non_defaults = {}
        self.missing = []
        self.loaded = False
    
    def readTlf(self):
        tlf = readTlfFile(self.tlf_path)
        self.home_folder = tlf['home_folder']
        self.resolved_name = tlf['resolved_name']
        self.tcf = tlf['entry_tcf']
        self.control_files = tlf['control']
        self.gis_files = tlf['gis']
        self.xs_files = []
        self.parameters = tlf['params']
        self.variables = tlf['variables']
        self.scenarios = tlf['scenarios']
        self.summary = tlf['summary']
        self.warnings = tlf['check_messages']
        self.non_defaults = tlf['tuflow_non_defaults']
        
    @property
    def all_variables(self):
        return self.variables + self.scenarios# + [self.parameters]

    @property
    def all_files(self):
        gis_files = []
        for k, g in self.gis_files.items():
            gis_files.extend(g)
        return [self.tcf] + self.control_files + gis_files + self.xs_files
    
    @property
    def diagnostics(self):
        checks = self.warnings.get('checks', {})
        warns = self.warnings.get('warnings', {})
        errors = self.warnings.get('errors', {})
        checks = [{'type': k, 'count': v['count'], 'message': v['message']} for k, v in checks.items()]
        warns = [{'type': k, 'count': v['count'], 'message': v['message']} for k, v in warns.items()]
        errors = [{'type': k, 'count': v['count'], 'message': v['message']} for k, v in errors.items()]
        return errors + warns + checks

    @property
    def has_errors(self):
        errors = self.warnings.get('errors', {})
        return len(errors) > 0

    @property
    def has_warnings(self):
        errors = self.warnings.get('warnings', {})
        return len(errors) > 0
    
    @property
    def run_summary(self):
        temp = self.summary | self.parameters
        return temp


class ModelChecker(QObject):
    status_update_signal = pyqtSignal(str)
    progress_max_signal = pyqtSignal(int)
    progress_val_signal = pyqtSignal(int)
    
    def __init__(self, model_root):
        super().__init__()
        self.model_root = model_root
        self.found_files = None
        self.tuflow_models = {}
        self.fm_models = {}
        self.ief_names = []
        self.tlf_names = []
        
    def searchFiles(self, model_root=None):
        if model_root is not None:
            self.model_root = model_root

        file_finder = FileFinder()
        self.found_files, iefs, tlfs = file_finder.auditModelFiles(self.model_root)
        self.loadIefFiles(iefs)
        self.loadTlfFiles(tlfs)
        self.tlf_names = [f"TUFLOW  {k}" for k, v in self.tuflow_models.items() if v.loaded]
        self.ief_names = [f"FM  {k}" for k, v in self.fm_models.items() if v.loaded]
        
    def modelSummaryInfo(self):
        summary_info = []
        for name, fm in self.fm_models.items():
            if not fm.loaded:
                summary_info.append({
                    'type': 'FM',
                    'loaded': False
                })
            else:
                summary_info.append({
                    'type': 'FM',
                    'loaded': fm.loaded,
                    'name': name,
                    'missing_files': 'Yes' if len(fm.missing) > 0 else 'No',
                    'non_defaults': 'Yes' if fm.has_non_defaults else 'No',
                    'warnings': 'Yes' if fm.has_warnings else 'No',
                    'errors': 'Yes' if fm.has_errors else 'No',
                    'run_status': 'FINISHED' if fm.diagnostics['details']['Run completed']['value'] == 'Yes' else 'FAILED',
                })
        for name, tuflow in self.tuflow_models.items():
            if not tuflow.loaded:
                summary_info.append({
                    'type': 'TUFLOW',
                    'loaded': False
                })
            else:
                summary_info.append({
                    'type': 'TUFLOW',
                    'loaded': tuflow.loaded,
                    'name': name,
                    'missing_files': 'Yes' if len(tuflow.missing) > 0 else 'No',
                    'non_defaults': 'Yes' if len(tuflow.non_defaults) > 0 else 'No',
                    'warnings': 'Yes' if tuflow.has_warnings else 'No',
                    'errors': 'Yes' if tuflow.has_errors else 'No',
                    'run_status': tuflow.summary['Simulation'],
                })
        return summary_info 
        
    def checkMissingFiles(self):
        if not self.found_files:
            raise AttributeError("No found files to check.")
        
        self.progress_val_signal.emit(0)
        self.status_update_signal.emit('Checking missing FM files...')
        self.progress_max_signal.emit(len(self.fm_models))
        count = 0
        for k, fm in self.fm_models.items():
            count += 1
            self.progress_val_signal.emit(count)
            if not fm.loaded:
                continue

            missing_ics = []
            missing_fmtcf = []
            dats, missing_dats = self.found_files.checkFmFiles(
                [fm.dat], ['fm_model']
            )
            self.fm_models[k].dat = dats[0]
            if fm.tcf:
                tcfs, missing_fmtcfs = self.found_files.checkFmFiles(
                    [fm.tcf], ['tuflow_model']
                )
                self.fm_models[k].tcf = tcfs[0]
            if fm.ics:
                ics, missing_ics = self.found_files.checkFmFiles(
                    [fm.ics], ['fm_model']
                )
                self.fm_models[k].ics = ics[0]
            self.fm_models[k].results, missing_results = self.found_files.checkFmFiles(
                fm.results, ['result'], ignore_case=True
            )
            self.fm_models[k].ieds, missing_ieds = self.found_files.checkFmFiles(
                fm.ieds, ['fm_model']
            )
            fm.missing = missing_dats + missing_fmtcfs + missing_ics + missing_results + missing_ieds
            fm.loadDiagnostics()
            
        self.progress_val_signal.emit(0)
        self.status_update_signal.emit('Checking missing TUFLOW files...')
        self.progress_max_signal.emit(len(self.tuflow_models))
        count = 0
        for k, tuflow in self.tuflow_models.items():
            count += 1
            self.progress_val_signal.emit(count)
            if not tuflow.loaded:
                continue

            root_tcf, missing_roottcf = self.found_files.checkTuflowFiles(
                [tuflow.tcf], ['tuflow_model']
            )
            self.tuflow_models[k].tcf = root_tcf[0]
            self.tuflow_models[k].control_files, missing_control = self.found_files.checkTuflowFiles(
                tuflow.control_files, ['tuflow_model']
            )
            self.tuflow_models[k].gis_files['tcf'], missing_tcf = self.found_files.checkTuflowFiles(
                tuflow.gis_files['tcf'], ['gis']
            )
            self.tuflow_models[k].gis_files['tgc'], missing_tgc = self.found_files.checkTuflowFiles(
                tuflow.gis_files['tgc'], ['gis']
            )
            self.tuflow_models[k].gis_files['tbc'], missing_tbc = self.found_files.checkTuflowFiles(
                tuflow.gis_files['tbc'], ['gis']
            )
            self.tuflow_models[k].gis_files['outputs'], missing_out = self.found_files.checkTuflowFiles(
                tuflow.gis_files['outputs'], ['result', 'gis']
            )
            self.tuflow_models[k].gis_files['xs'], missing_xs = self.found_files.checkTuflowFiles(
                tuflow.gis_files['xs'], ['gis']
            )
            tuflow.missing = missing_roottcf + missing_control + missing_tcf + missing_tgc + missing_tbc + missing_xs + missing_out
            # tuflow.missing = (
            #     missing_roottcf + missing_control + missing_tcf + missing_tgc + 
            #     missing_tbc + missing_xs
            # )
        
    def loadTlfFiles(self, tlf_files):
        self.progress_val_signal.emit(0)
        self.status_update_signal.emit('Loading TLF files...')
        self.progress_max_signal.emit(len(tlf_files))
        tuflow_models = {}
        for i, tlf in enumerate(tlf_files):
            self.progress_val_signal.emit(i)

            # TODO: Change this to use the new path setup
            if tlf.fileExt == 'tlf':
                tlf_path = Path(tlf.filepath)
                tuflow = TuflowModel(tlf_path)
                try:
                    tuflow.readTlf()
                    tuflow.loaded = True
                except:
                    tuflow.loaded = False
                self.tuflow_models[str(tlf_path.stem)] = tuflow

    def loadIefFiles(self, fm_files):
        self.progress_val_signal.emit(0)
        self.status_update_signal.emit('Loading IEF files...')
        self.progress_max_signal.emit(len(fm_files))
        iefs = {}
        for i, ief in enumerate(fm_files):
            self.progress_val_signal.emit(i)

            model = FmModel(ief)
            model.checkParams()
            model.findFiles()
            model.loaded = True
            self.fm_models[str(ief.filepath.stem)] = model
            
    def loadTuflowSubfiles(self):
        """Load additional TUFLOW files like XS and BCDbase.
        """
        self.progress_val_signal.emit(0)
        self.status_update_signal.emit('Loading Tuflow subfiles...')
        self.progress_max_signal.emit(len(self.tuflow_models))
        count = 0
        for name, tuflow in self.tuflow_models.items():
            count += 1
            self.progress_val_signal.emit(count)
            if not tuflow.loaded:
                continue
            
            xs_files = tuflow.gis_files['xs']
            for xs in xs_files:
                attributes = readXsFile(xs.resolved_path, xs.gpkg_layer)
                for a in attributes:
                    resolved_path = f"{xs.resolved_path.parent}/{a['source']}"
                    original_path = f"{xs.filepath.parent}/{a['source']}"
                    section_file = TuflowFile(original_path, parent_type='XS', gpkg_layer=None)
                    section_file.resolved_path = Path(resolved_path)
                    if section_file.resolved_path.is_file():
                        section_file.missing = 'No'
                    else:
                        section_file.missing = 'Yes'
                        self.tuflow_models[name].missing.append(section_file)
                    self.tuflow_models[name].xs_files.append(section_file)


