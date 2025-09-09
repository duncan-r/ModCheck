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

        

class ResultHolder():    
    """
    """
    
    def __init__(self):
        self.model_root = ''
        self.parent = ''
        self.seen_parents = []
        self.missing = {}
        self.ignored_files = []
        self.file_tree = []
#         self.found = {}

        self._summary = {'model_files': 0, 'other_files': 0, 'ignored_files': 0, 'total_files': 0}
        self.results = {'missing': [], 'found': [], 'found_ief': []}
        self.results_meta = {'summary': None, 'ignored': None, 'checked': None}

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, summary):
        self._summary = summary
        self._summary['total_files'] = self.getFileTotal()
        
    def formatFileTree(self, include_files=True, format_as_text=True, include_full_paths=False):
        output_list = []
        fullpath_list = []
        for f in self.file_tree:
            if not f['is_folder']:
                if include_files:
                    output_list.append('{}{}\n'.format(f['indent'], f['path']))
                    fullpath_list.append(f['fullpath'])
                else:
                    fullpath_list.append('')
            else:
                if include_files:
                    output_list.append('{}\n'.format(f['indent'][:-4]))
                    fullpath_list.append('')
                output_list.append('{}{}/\n'.format(f['indent'], f['path']))
                fullpath_list.append('')
                
        output = None
        fullpaths = None
        if format_as_text:
            output = ''.join(output_list)
            fullpaths = '\n'.join(fullpath_list)

        if include_full_paths:
            return output, fullpaths
        else:
            del fullpath_list
            return output

    def saveFileTree(self, save_path, include_files=True):
        output = self.formatFileTree(include_files=include_files)
        with open(save_path, 'w', newline='\n') as outfile:
            outfile.write(output)
    
    def addMissing(self, path, line, found=''):
        if path in self.missing:
            if not self.parent in self.missing[path]['parent']:
                self.missing[path]['parent'].append(self.parent)
                self.missing[path]['line'].append(line)
        else:
            self.missing[path] = {'parent': [self.parent], 'line': [line], 'found': found}
    
    def setFound(self, path, found):
        try:
            self.missing[path]['found'] = found
        except KeyError:
            raise 
        
    def summaryText(self):
        return 'Model Files: {0:<10}\nOther Files: {1:<10}\nIgnored Files: {2:<10}\nTotal Files: {3:<10}'.format(
            self._summary['model_files'], self._summary['other_files'], 
            self._summary['ignored_files'], self._summary['total_files']
        )
        
    def getFileTotal(self):
        return self._summary['model_files'] + self._summary['other_files'] + self._summary['ignored_files']

    def processResults(self):
        self.results = {'missing': [], 'found': [], 'found_ief': []}
        self.results_meta['summary'] = self.summary
        self.results_meta['ignored'] = self.ignored_files
        self.results_meta['checked'] = self.seen_parents

        for f, details in self.missing.items():
            info = {'file': [], 'parents': []}
            psplit = os.path.split(f)
            filename = psplit[1] if len(psplit) > 1 else f
            all_ief = True
            for i, parent in enumerate(details['parent']):
                if not parent[-3:] == 'ief':
                    all_ief = False
                info['parents'].append([parent, details['line'][i]])

            if details['found']:
                info['file'] = [filename, details['found'], f]
                if all_ief:
                    self.results['found_ief'].append(info)
                else:
                    self.results['found'].append(info)
            else:
                info['file'] = [filename, f]
                self.results['missing'].append(info)
                
    def exportResults(self, save_path):
        """
        """
        with open(save_path, 'w', newline='\n') as outfile:
            outfile.write('\n###########################')
            outfile.write('\n# FILE SEARCH SUMMARY')
            outfile.write('\n###########################\n\n')
            outfile.write('Root folder: {0}\n'.format(self.model_root))
            outfile.write(self.summaryText())

            outfile.write('\n\nFILES THAT WERE IGNORED\n')
            if self.ignored_files:
                outfile.write('\n'.join([i.filepath for i in self.ignored_files]))
            else:
                outfile.write('\nNo files were ignored')

            outfile.write('\n\nMISSING FILES\n')
            if self.results['missing']:
                outfile.write('\n'.join(m['file'][0] for m in self.results['missing']))
            else:
                outfile.write('\nNo missing files')

            outfile.write('\n\nFOUND FILES (Incorrect paths)\n')
            if self.results['found'] or self.results['found_ief']:
                outfile.write('\n'.join(f['file'][0] for f in self.results['found']))
                outfile.write('\n'.join(f['file'][0] for f in self.results['found_ief']))
            else:
                outfile.write('\nNo misreferenced files')
                
            outfile.write('\n\nMODEL FILES CHECKED\n')
            outfile.write('\n'.join([p for p in self.seen_parents]))
            
            outfile.write('\n\n\n###########################')
            outfile.write('\n# DETAILED RESULTS')
            outfile.write('\n###########################\n')

            outfile.write('\n\nMISSING FILES\n')
            if self.results['missing']:
                for m in self.results['missing']:
                    outfile.write('\n{0:<20}{1}'.format('File:', m['file'][0]))
                    outfile.write('\n{0:<20}{1}'.format('Path:', m['file'][1]))
                    outfile.write('\nReferenced by parent files:\n')
                    outfile.write('\n'.join(['Line ({0})\t {1}'.format(p[1], p[0]) for p in m['parents']]))
                    outfile.write('\n')
            else:
                outfile.write('\nNo missing files')

            outfile.write('\n\n\nFOUND FILES (Incorrect paths)\n')
            if self.results['found'] or self.results['found_ief']:
                for f in self.results['found']:
                    outfile.write('\n{0:<20}{1}'.format('File:', f['file'][0]))
                    outfile.write('\n{0:<20}{1}'.format('Original Path:', f['file'][2]))
                    outfile.write('\n{0:<20}{1}'.format('Found Path:', f['file'][1]))
                    outfile.write('\nReferenced by parent files:\n')
                    outfile.write('\n'.join(['Line ({0})\t {1}'.format(p[1], p[0]) for p in f['parents']]))
                    outfile.write('\n')
                for f in self.results['found_ief']:
                    outfile.write('\n{0:<20}{1}'.format('File:', f['file'][0]))
                    outfile.write('\n{0:<20}{1}'.format('Original Path:', f['file'][2]))
                    outfile.write('\n{0:<20}{1}'.format('Found Path:', f['file'][1]))
                    outfile.write('\nReferenced by parent files:\n')
                    outfile.write('\n'.join(['Line ({0})\t {1}'.format(p[1], p[0]) for p in f['parents']]))
                    outfile.write('\n')
            else:
                outfile.write('\nNo misreferenced files')


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





def read_tlf_file(filepath):
    """
     WARNING:
     - Assumes any control file that has a 'csv' extension is a BCDbase.
       Obviously won't be true when we support csv for TMF files!!
       (see control_type_setter function).
    
    """
    
    
    # REGEX SEARCH PATTERNS
    CONTROL_FILE_PATTERN = '[\\|/][\w~]+\.(tcf|ecf|tgc|tbc|tmf|tef|trf|tlf)'
    
    # This one needs some explaining :)
    # Match the 'path', then the 'extension' (gis file types), then an optional match for
    # geopackage layers, 'geolayer' at the end of the line
    # Shapefile example: Opening GIS Layer: D:\Models\MoretonOnLugg\Hydraulics\model\tuflow\model\gis\2d_bc_hx_MOL_005_L.shp
    # Geopackage example: Opening GIS Layer: Y:\PROJECTS\AEG4706_Backwell_03\TUFLOW\model\gis\AEG4706_Backwell_TBC.gpkg >> 2d_bc_4706_DSBDY_001_L
    # GIS_FILE_PATTERN = 'Opening GIS.+:\s(?P<path>.+)\.(?P<extension>shp|mif|gpkg)(\s>>\s)?(?P<geolayer>.+)?'
    
    # Need the closing one, because sometimes the 'Opening GIS' doesn't include the gpkg layer name
    GIS_FILE_PATTERN = 'Closing GIS.+\[(?P<path>.+)\.(?P<extension>shp|mif|gpkg)(\]\.{0,3})?(\s>>\s)?(?P<geolayer>.+)?(\]\.{0,3})'
   
    # GIS_FILE_PATTERN = '[\\|/][\w~]+\.shp|mif|mid|gpkg\s>>\s.+$'
    # GPKG_FILE_PATTERN = 'Opening GIS.+:\s(?P<db>.+gpkg)\s>>\s(?P<layer>.+$)'
    GIS_FILTER_PATTERN = '_mmH|Q|V|ccA|_TS|_PLOT\.|messages|check.*'
    VARIABLE_PATTERN = '^\s*Set Variable[\s\w~]+==\s\w+'
    
    control_files = []
    gis_files = []
    gpkg_files = []
    params = {}
    variables = {}
    checks = {'checks': {}, 'warnings': {}, 'errors': {}}

    def reading_tgc_match(line):
        if 'Reading Geometry File' in line:
            return True
        return False

    def ending_tgc_match(line):
        if 'Finished Reading Geometry File' in line:
            return True
        return False

    def reading_tbc_match(line):
        if 'opening bc control file' in line.lower():
            return True
        return False

    def ending_tbc_match(line):
        if 'deallocating temporary memory' in line.lower():
            return True
        return False

    def control_file_match(regex, line):
        """Check if line contains a control file.
        """
        rmatch = re.search(regex, line)
        if rmatch:
            # Remove the leading slash
            cmatch = rmatch.group(0)[1:]
            if cmatch not in control_files:
                control_files.append(cmatch)
            return True
        return False
    
    def old_gis_file_match(regex, line, is_tgc, is_tbc):
        """Check if line contains a shp/mif file.
        """
        if 'Opening GIS Layer:' not in line:
            return False

        rmatch = re.search(regex, line)
        if rmatch:

            # Remove the leading slash
            cmatch = rmatch.group(0)[1:]
            if cmatch not in gis_files:
                if is_tgc:
                    gis_files.append([cmatch, 'TGC'])
                elif is_tbc:
                    gis_files.append([cmatch, 'TBC'])
                else:
                    gis_files.append([cmatch, 'TCF'])
            return True
        return False

    # GIS_FILE_PATTERN = 'Opening GIS.+:\s(?P<path>.+)\.(?P<extension>shp|mif|gpkg)(\s>>\s)?(?P<geolayer>.+)?'
    def gis_file_match(regex, line, is_tgc, is_tbc):
        """Check if line contains a gpkg file.
        """
        if 'Closing GIS Layer' not in line:
            return False

        rmatch = re.search(regex, line)
        if rmatch:

            # Remove the leading slash
            cmatch = rmatch.group(0)#[1:]
            fpath = rmatch.group('path')
            fext = rmatch.group('extension')
            geolayer = rmatch.group('geolayer')
            
            # CHECK: This isn't great, as, I think, not all mid's have mif's?
            if fext in ['mid', 'tab']:
                fext = 'mif'
            
            # if layer not in gis_files:
            # if layer not in gis:
            if is_tgc:
                gis_files.append([fpath, 'TGC', fext, geolayer])
                # gis_files.append([layer, 'TGC', db])
            elif is_tbc:
                gis_files.append([fpath, 'TBC', fext, geolayer])
                # gis_files.append([layer, 'TGC', db])
            else:
                gis_files.append([fpath, 'TCF', fext, geolayer])
                # gis_files.append([layer, 'TCF', db])
            return True
        return False

    def variable_match(regex, line):
        """Check if line contains a shp/mif file.
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
        """Removes check, results and messages files from list.
        """
        filtered_files = []
        found_files = []
        for s in gis_files:
            layer = s[0]
            geolayer = s[3]
            
            if geolayer is not None:
                if re.search(gis_filter_regex, geolayer):
                    continue
                if layer+geolayer not in found_files:
                    found_files.append(layer+geolayer)
                    filtered_files.append([s[0], s[1], s[3], s[2]])
            else:
                if re.search(gis_filter_regex, layer):
                    continue
                if layer not in found_files:
                    found_files.append(layer)
                    filtered_files.append([s[0], s[1], s[3], s[2]])
            
            
            # if re.search(gis_filter_regex, layer):
            #     continue
            # # Probably don't need the gf seach (above) for gpkg but I don't think it will hurt?
            # if geolayer is not None and re.search(gis_filter_regex, geolayer):
            #     continue
            # # ext = os.path.splitext(gf)[1][1:].upper()
            # # if ext == 'TAB' or ext == 'MID':
            # #     ext = 'MIF'
            #
            # # Check the gpkg layer name rather than the db path
            # if geolayer is not None and geolayer not in found_files:
            #     found_files.append(geolayer)
            #     # continue
            #
            # # Other wise check the shp/mif path
            # elif layer in found_files:
            #     found_files.append(layer)
            #     # continue
            #
            # # filtered_files.append([gf, ext, s[1]])
            # # filtered_files.append([s[0], s[1], s[2], ext])
            # filtered_files.append([s[0], s[1], s[3], s[2]])
        return filtered_files
            
    def control_type_setter(control_files): 
        """Create tuple with (filename, extension) to designate type.
        """
        output = []
        for c in control_files:
            ext = os.path.splitext(c)[1][1:].upper()
            if ext == 'CSV':
                ext = 'BCDBase'
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
                pass
        return output
    
    def order_params_items(params):
        # lookup = {
        #     'build': 'build',
        #     'executable': 'executable',
        #     'simulation started': 'run_start',
        #     'output folder': 'result_folder',
        #     'write check files': 'check_folder',
        #     'log folder': 'log_folder',
        #     'gis format': 'gis_format',
        #     'grid format': 'grid_format',
        #     'bc event source': 'event_source',
        #     'start time (h)': 'start_time',
        #     'end time (h)': 'end_time',
        #     '2d domain cell sizes': 'cell_sizes',
        #     '2d domain timesteps': 'timesteps_2d',
        #     'hardware': 'hardware',
        #     'gpu device ids': 'gpu_ids',
        #     '2d solution scheme': 'solution_scheme_2d',
        # }
        output = {
            '2D Domains': [],
            # '2D Solution Scheme': 'Unknown',
        }
        for k, v in params.items():
            if k.lower() == 'start 2d domain':
                output['2D Domains'].append(v)
            else:
                output[k] = v

        # if '2D Solution Scheme' in params.keys():
        #     output['2D Solution Scheme'] = params['2D Solution Scheme'].split('!')[0].strip()            
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
        # scenarios = ', '.join(scenarios)
        # variables = ', '.join(variables)
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
    # gpkg_file_regex = re.compile(GPKG_FILE_PATTERN)
    gis_filter_regex = re.compile(GIS_FILTER_PATTERN)
    variable_regex = re.compile(VARIABLE_PATTERN)

    summary_lines = []
    with open(filepath, 'r') as infile:
        in_summary = False
        in_tgc = False
        in_tbc = False

        for line in infile.readlines():
            line = line.replace('\\', '/')
            
            # No need to check any of the other stuff once we're in the summary
            # section. Just grab the lines and process outside the file load
            if in_summary:
                line = line.strip()
                if line == '': continue
                summary_lines.append(line)
                continue

            if reading_tgc_match(line):
                in_tgc = True
                in_tbc = False
            if ending_tgc_match(line):
                in_tgc = False

            if reading_tbc_match(line):
                in_tbc = True
                in_tgc = False
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
            
            # Pick up GPKG gis files
            # More specific, so needs to be above the gis_file_match
            # if gpkg_file_match(gpkg_file_regex, line, in_tgc, in_tbc):
            #     continue
            
            # Pick up gis files (shp, mif) - will need geodb support at some point
            if gis_file_match(gis_file_regex, line, in_tgc, in_tbc):
                continue

            # Pick up 'Set Variable' commands
            if variable_match(variable_regex, line):
                continue

            # Collect check and warning messages
            if line.startswith('XY:') or line.startswith('NoXY:'):
                # def find_number(message):
                #     split_msg = message.split('-')[0].split(':')[1].strip().split()
                #     import pdb;pdb.set_trace()
                #     return split_msg[1]

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
                    # checks['checks'].append({'code': check_code, 'message': val})
                elif ': WARNING' in line:
                    if check_code not in checks['warnings'].keys():
                        checks['warnings'][check_code] = {'count': 1, 'message': val}
                    else:
                        checks['warnings'][check_code]['count'] += 1
                    # checks['warnings'].append({'code': check_code, 'message': val})
                elif ': ERROR' in line:
                    if check_code not in checks['errors'].keys():
                        checks['errors'][check_code] = {'count': 1, 'message': val}
                    else:
                        checks['errors'][check_code]['count'] += 1
                    # checks['errors'].append({'code': check_code, 'message': val})
            
            # Special case because it doesn't get picked up with the '==' check. It's because
            # there are multiple '==' in this one, but a a general check for it was cocking
            # other stuff up. 
            # TODO: come back and deal with this properly!
            if line.startswith('2D Solution Scheme =='):
                command, var = line.split('==', 1)
                if '!' in var:
                    var = var.split('!')[0].strip()
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
            print('\n\nLog file found')
            log_path = Path(split)
            summary['resolved_name'] = log_path.stem
            print(summary['resolved_name'])
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
            summary['cme'] = split

    # Create the output dictionary
    variables, scenarios = format_variables(variables)
    final_files = {
        'resolved_name': summary['resolved_name'],
        'entry_tcf': entry_tcf,
        'control': control_type_setter(control_files), 
        'gis': gis_file_filter(gis_filter_regex, gis_files),
        # 'gpkg': gpkg_files,
        'params': order_params_items(params),
        'variables': variables,
        'scenarios': scenarios,
        'summary': order_summary_items(summary),
        'check_messages': format_checks(checks),
    }

    # print()
    print('Control files:')
    for c in final_files['control']:
        print(c)
    #
    print()
    print('Params')
    for c, v in final_files['params'].items():
        print('{} : {}'.format(c, v))
    #
    print()
    print('Variables')
    print(final_files['variables'])
    print(final_files['scenarios'])
    # for c, v in final_files['variables'].items():
    #     print('{} : {}'.format(c, v))
    #
    print()
    print('Summary')
    for c, v in final_files['summary'].items():
        print('{} : {}'.format(c, v))

    print('Check messages')
    pprint(final_files['check_messages'])
    
    return final_files

# final_files = {
#         'entry_tcf': entry_tcf,
#         'control': control_type_setter(control_files), 
#         'gis': gis_file_filter(gis_filter_regex, gis_files),
#         'params': params,
#         'variables': variables,
#         'summary': summary,
#     }


# def load_data_into_db(data, entry_id):
#     print('\nLoading into database')
#     log_entry = models.TuflowLogEntry.objects.get(id=entry_id)
#     log_entry.tcf = data['entry_tcf']
#     log_entry.se_vals = data['scenarios']
#     log_entry.save()
#
#     tuflow_settings = []
#     for k, v in data['params'].items():
#         tuflow_settings.append(
#             models.TuflowSetting(log_entry=log_entry, command=k, value=v)
#         )
#     models.TuflowSetting.objects.bulk_create(tuflow_settings)
#
#     warnings = int(data['summary'].get('warnings_prior', -1))
#     warnings_during = int(data['summary'].get('warnings_during', -1))
#     if warnings_during != -1:
#         if warnings == -1:
#             warnings += 1
#         warnings += warnings_during
#
#     checks = int(data['summary'].get('checks_prior', -1))
#     checks_during = int(data['summary'].get('checks_during', -1))
#     if checks_during != -1:
#         if checks == -1:
#             checks += 1
#         checks += checks_during
#
#     diagnostics = models.TuflowDiagnostics(
#         log_entry=log_entry,
#         resolved_name=data['summary'].get('resolved_name', 'NA'),
#         run_time=data['summary'].get('run_time', 'NA'),
#         simulation_status=data['summary'].get('simulation_status', 'NA'),
#         negative_depths_1d=float(data['summary'].get('negative_depths_1d', -1)),
#         negative_depths_2d=float(data['summary'].get('negative_depths_2d', -1)),
#         cme_gt_5=data['summary'].get('cme_gt_5', 'NA'),
#         cme_whole=data['summary'].get('cme_whole', 'NA'),
#         warnings=warnings,
#         checks=checks,
#         final_cme=data['summary'].get('cme', 'NA'),
#         hcn_repeated_timesteps=int(data['summary'].get('hcn_repeated_timesteps', -1)),
#         nan_repeated_timesteps=int(data['summary'].get('nan_repeated_timesteps', -1)),
#         nan_warnings=int(data['summary'].get('nan_warnings', -1)),
#     )
#     if data['check_messages']:
#         diagnostics.check_messages = data['check_messages']
#     diagnostics.save()
#
#     control_files = []
#     for c in data['control']:
#         control = models.TuflowControlFile.objects.get_or_create(
#             control_type=c[1],
#             name=c[0],
#             description='',
#         )
#         control_files.append(control)
#
#     sub_files = []
#     for s in data['gis']:
#         sub = models.TuflowSubFile.objects.get_or_create(
#             control_type=s[2],
#             gis_type=s[1],
#             name=s[0],
#             command='NA',
#             description='',
#         )
#         sub_files.append(sub)
#
#     for c in control_files:
#         runcontrol = models.TuflowEntryControlFile(
#             log_entry=log_entry,
#             control_file=c[0],
#             new_file=c[1],
#         )
#         runcontrol.save()
#
#     for s in sub_files:
#         runsub = models.TuflowEntrySubFile(
#             log_entry=log_entry,
#             sub_file=s[0],
#             new_file=s[1],
#         )
#         runsub.save()

# if __name__ == '__main__':
#     filepath = os.path.join(BASE_DIR, 'temp', 'ShornBrook_BAS_0030_010.tlf')
#     data = read_file(filepath)
