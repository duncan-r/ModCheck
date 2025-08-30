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
    # ief_paths = glob(folder + + '\*.ief', recursive=True)
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

# class FileChecker(QtCore.QObject):
#     status_signal = QtCore.pyqtSignal(str)
#
#     def __init__(self):
#         super().__init__()
#
#     def auditModelFiles(self, model_root):
#         self.status_signal.emit('Auditing model files ...')
#
#         errors = {}
#         error_count = 0
#         search_successes = 0
#
#         self.status_signal.emit('Searching folders ...')
#         model_files, other_files, ignore_files, file_tree = self.categorise(model_root)
#         audit = AuditFiles(model_root, model_files, other_files, ignore_files)
#         self.status_signal.emit('Categorising results ...')
#         result_holder = ResultHolder()
#         result_holder.ignored_files = ignore_files
#
#         self.status_signal.emit('Checking paths ...')
#         for f in audit.getModelFiles():
#             fpath = f.getFilePath()
#             self.status_signal.emit('Checking paths for file: {0}'.format(fpath))
#             errorlist = []
#
#             if fpath in result_holder.seen_parents: continue
#
#             result_holder.parent = fpath
#             result_holder.seen_parents.append(fpath)
#
#             for p, line in f.getPathsToCheck():
#                 if not p.isReal():
#
#                     path_as_read = p.getPathAsRead()
#                     result_holder.addMissing(p.pathAsRead, line)
#
#                     error_count += 1
#                     errorlist.append((p, line))
#                     search_result = p.find(audit)
#                     if len(search_result) > 0:
#
#                         try:
#                             result_holder.setFound(p.pathAsRead, search_result)
#                         except KeyError:
#                             pass
#                         search_successes += 1
#             errors[f] = errorlist
#
#         result_holder.model_root = model_root
#         result_holder.summary = audit.getFileCounts()
#         result_holder.processResults()
#         result_holder.file_tree = file_tree
#         self.status_signal.emit('Check complete')
#         return result_holder
#
#     def categorise(self, model_root):
#         '''
#             Method for categorising the model passed to the audit tool
#             Return: tuple contain list of ModelFile and list of SomeFile instances
#         '''
#         model_files = []
#         other_files = []
#         ignore_files = []
#         file_tree = []
#         try:
#             # walk the model folder structure categorising ignore, model and other (eg GIS, csv) files
#             root_count = 1
#             for root, dirs, files in os.walk(model_root):
#                 self.status_signal.emit('Searching folder {0} ...'.format(root))
#                 tree_level = root.replace(model_root, '', 1).count(os.sep)
#                 tree_indent = '|    ' * (tree_level - 1) + '+---'
#                 if root_count > 1:
#                     file_tree.append({
#                         'indent': tree_indent, 'path': os.path.basename(root), 'is_folder': True, 
#                         'level': tree_level
#                     })
#                 tree_subindent = '|    ' * (tree_level) + '-   '
#
#                 for f in files:
#                     file_tree.append({
#                         'indent': tree_subindent, 'path': f, 'is_folder': False, 'level': tree_level,
#                         'fullpath': os.path.join(root, f)
#                     })
#                     filepath = os.path.join(root,f)
#                     filepath, _ = gt.longPathCheck(filepath)
#                     query = SomeFile(filepath)
#                     if query.isIgnoreFile():
#                         ignore_files.append(query)
#
#                     # model files each have there own class describing their expected format
#                     elif query.isModelFile():
#                         model_files.append(model_file_exts[query.getFileExt()](filepath))
#
#                     else:
#                         other_files.append(query)
#                 root_count += 1
#
#         except Exception as err:
#             raise
#
#         return model_files, other_files, ignore_files, file_tree
#
#
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
#
#
# class AuditFiles():
#     '''
#         Path checking audit tool
#     '''
#     def __init__(self, model_root, model_files, other_files, ignore_files):
#         '''
#             Takes a string describing the path to the root of the model folder structure being audited
#         '''
#         self.model_root = model_root
#         if not os.path.isdir(model_root):
#             raise ValueError('Unable to find that directory')
#
#         self.modelFiles = model_files
#         self.otherFiles = other_files
#         self.ignoreFiles = ignore_files
#
#     def getModelFiles(self):
#         return self.modelFiles
#
#     def getOtherFiles(self):
#         return self.otherFiles
#
#     def getFileCounts(self):
#         return {
#             'model_files': len(self.modelFiles),
#             'other_files': len(self.otherFiles),
#             'ignored_files': len(self.ignoreFiles),
#         }
#
#

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


# class ModelFile(SomeFile):
#     '''
#         Class for model files found in the model structure
#     '''
#     def __init__(self, filepath):
#         SomeFile.__init__(self, filepath)
#         self.filepath = filepath
#         self.path, self.name = os.path.split(filepath)
#         self.pathsToCheck = None #self.PathSearch()
#
#     def isModelFile(self):
#         return True
#
#     def PathSearch(self, terms, comment = '\n', splitOn = None, inactiveLines = False):
#         '''
#             Find lines containing each search variable in list 'terms' (a list of strings)
#             Optional 'comment' string ignores text that appears after that string in a line
#             !!!    NOT CURRENTLY USED: Optional inactiveLines switch allows you to search lines that have been commented-out at the beginning of the line
#             Returns a list of the active lines containing the search terms (after removing comments)
#         '''
#         def ExtractPath(line, splitOn):
#             '''
#                 Helper function to extract the paths found in the active lines containing the search term
#                 It simply right splits on the 'splitOn' string
#             '''
#             return line.rsplit(splitOn,1)[-1].strip()
#
#
#         def TermSearch(term, text):
#             '''
#                 Helper function to check 'term' is a string and that it is in 'text'
#             '''
#             if type(term) != type(''):
#                 raise TypeError ('Search term must be a string')
#             return term in text
#
#
#         def checkForPipes(line):
#             """Checks the line to see if it contains multiple files.
#
#             Some commands in tuflow can contain multiple files seperate by a pipe
#             "|" charactar. This checks to see if that's the case and returns the
#             file names if so.
#             Sometimes pipe commands can be values to adjust parameters with, such
#             as the materials file manning's adjustment. This checks whether the
#             value is an int or a float, if not it's added.
#             """
#             # Break line
#             #
#             line = line.strip()
#             command, instruction = line.split('==', 1)
#             command = command.strip()
#             instruction = instruction.strip()
#
#             # check for pipes
#             #
#             found, split, comment_char = separateComment(instruction)
#             instruction = split[0].strip()
#
#             instructions = instruction.split('|')
#             out = []
#             if len(instructions) > 1:
#                 for i in instructions:
#                     # Make sure it's not an adjustment value
#                     i = i.strip()
#                     try:
#                         temp = int(i)
#                     except ValueError:
#                         try:
#                             temp = float(i)
#                         except ValueError:
#                             out.append([command + ' == ' + i.strip(), i.strip()])
#             else:
#                 out.append([line, instructions[0]])
#
#             return out
#
#
#         def separateComment(line):
#             """Separates any comment from the line.
#             """
#             comment_char = None
#             if '!' in line:
#                 comment_char = '!'
#
#             if '#' in line:
#                 comment_char = '#'
#
#             if not comment_char is None:
#                 split = line.split(comment_char, 1)
#             else:
#                 split = [line]
#                 comment_char = ''
#
#             if len(split) > 1:
#                 return True, split, comment_char
#             else:
#                 return False, split, comment_char
#
#
#         results = []
#
#         with open(self.filepath, 'r') as mf:
#             for lineNum, lineText in enumerate(mf,1):
#                 lineText = lineText.rstrip()
#                 # ignore blank lines
#                 if lineText == '':
#                     continue
#                 # remove text that follows the 'comment' string    
#                 activeText = lineText.split(comment,1)[0]
#                 # print lineNum, activeText
#                 # store the paths in lines that contain our search terms as ModelPath instances
#                 for i, term in enumerate(terms):
#                     try:
#                         if TermSearch(term, activeText): 
#                             # Separate any piped file command if found
#                             if '==' in activeText and splitOn == '==':
#                                 paths = checkForPipes(activeText)
#                                 for p in paths:
# #                                     results.append(((ModelPath(ExtractPath(activeText, splitOn), self.path)), lineNum))
#                                     results.append(((ModelPath(p[0], p[1], self.path)), lineNum))
#                             else:
#                                 splitText = ExtractPath(activeText, splitOn)
#                                 results.append(((ModelPath(splitText, splitText, self.path)), lineNum))
#                             break
#                     except TypeError:
#                         pass
#
#         return results
#
#     def getPathsToCheck(self):
#         if self.pathsToCheck is None:
#             self.pathsToCheck = self.PathSearch()
#         return self.pathsToCheck            
#
#
# class ModelPath():
#     '''
#         Class for path data and methods extracted from model files
#     '''
#     def __init__(self, extractedPath, pathAsRead, pathOfContainingFile):
#         self.pathAsRead = pathAsRead
#         self.pathOfContainingFile = pathOfContainingFile        
#         self.pathFileName = os.path.basename(extractedPath)
#         self.pathFileExt = self.pathFileName.rsplit('.',1)[-1].lower()
#
#         # check if absolute and set absPath string accordingly
#         if not os.path.isabs(extractedPath):
#             self.absPath = os.path.normpath(os.path.join(self.pathOfContainingFile, self.pathAsRead))
#         else:
#             self.absPath = extractedPath
#
#         self.real = self.check()
#
#     def getPathFileName(self):
#         return self.pathFileName
#
#     def getPathFileExt(self):
#         return self.pathFileExt
#
#     def getPathAsRead(self):
#         return self.pathAsRead
#
#     def getPathOfContainingFile(self):
#         return self.pathOfContainingFile
#
#     def getAbsPath(self):
#         return self.absPath
#
#     def check(self):
#         '''
#             Returns true if path exists, false otherwise
#         '''
#         # if we are looking for a mid file we need a mif file (and vice versa).
#         if self.getPathFileExt() == 'mif':
#             return os.path.exists(self.absPath) and (
#                 os.path.exists(self.absPath.rsplit('.',1)[0] + '.mid') or os.path.exists(
#                     self.absPath.rsplit('.',1)[0] + '.MID'
#                 )
#             )
#
#         elif self.getPathFileExt() == 'mid':
#             return os.path.exists(self.absPath) and (
#                 os.path.exists(self.absPath.rsplit('.',1)[0] + '.mif') or os.path.exists(
#                     self.absPath.rsplit('.',1)[0] + '.MIF'
#                 )
#             )
#         # With shape files we need .shp, dbf and shx files too
#         elif self.getPathFileExt() == 'shp':
#             return os.path.exists(self.absPath) and (
#                 os.path.exists(self.absPath.rsplit('.',1)[0].lower() + '.dbf') and os.path.exists(
#                     self.absPath.rsplit('.',1)[0].lower() + '.shx'
#                 )
#             )
#
#         else:
#             return os.path.exists(self.absPath)
#
#     def isReal(self):
#         return self.real
#
#     def find(self, audit):
#
#         allFiles = audit.getModelFiles() + audit.getOtherFiles()
#         result = ''
#
#         for f in allFiles:
#             if f.getName() == self.pathFileName:
#                 result = f.getFilePath()
#                 break
#             else:
#                 pass
#
#         return result
#
# class TCF_file(ModelFile):
#     '''
#         Class for TCF model files
#     '''
#     def __init__(self, filepath):
#         ModelFile.__init__(self, filepath)
#
#     def PathSearch(self):
#         # Use 'File ' not 'File' as this picks up all 'File Read' commands and misses 'Write Files' commmands
#         return ModelFile.PathSearch(self, ['File ', 'BC Database', 'Read'], '!', '==')
#
#     #def GIS_Search(self):
#     #    return ModelFile.PathSearch(self, ['MI Projection'], '!', '==')
#
#
# class ECF_file(ModelFile):
#     '''
#         Class for TCF model files
#     '''
#     def __init__(self, filepath):
#         ModelFile.__init__(self, filepath)
#
#     def PathSearch(self):
#         return ModelFile.PathSearch(self, ['Read', 'Data'], '!', '==')
#
#
# class TBC_file(ModelFile):
#     '''
#         Class for TBC model files
#     '''
#     def __init__(self, filepath):
#         ModelFile.__init__(self, filepath)
#
#     def PathSearch(self):
#         return ModelFile.PathSearch(self, ['BC Database', 'Read'], '!', '==')
#
# class TGC_file(ModelFile):
#     '''
#         Class for TGC model files
#     '''
#     def __init__(self, filepath):
#         ModelFile.__init__(self, filepath)
#
#     def PathSearch(self):
#         return ModelFile.PathSearch(self, ['Read'], '!', '==')
#
# class TEF_file(ModelFile):
#     '''
#         Class for TEF model files
#     '''
#     def __init__(self, filepath):
#         ModelFile.__init__(self, filepath)
#
#     def PathSearch(self):
#         return []
#
# class IEF_file(ModelFile):
#     '''
#         Class for IEF model files
#     '''
#     def __init__(self, filepath):
#         ModelFile.__init__(self, filepath)
#
#     def PathSearch(self):
#         return ModelFile.PathSearch(self, ['Datafile', 'InitialConditions', 'EventData', '2DFile'], splitOn = '=')

# file extension pointing the the associated paths. trd files follow the same format as tcf files hence share the same class
# model_file_exts = {'tcf': TCF_file, 'trd': TCF_file, 'ecf': ECF_file, 'tbc': TBC_file, 'tgc': TGC_file, 'tef': TEF_file, 'ief': IEF_file}
# ignore_file_exts = ['log', 'doc', 'xlsx', 'pdf']
#model_file_ignore = []