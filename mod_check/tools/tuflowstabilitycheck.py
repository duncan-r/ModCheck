'''
@summary: View tuflow MB / dvol etc outputs

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 10th March 2021
@copyright: Ermeview Environmental Ltd
@license: LGPL v2
'''

# import logging
# logging.basicConfig(level=logging.DEBUG)

import os
import sys
import csv
from pprint import pprint
from PyQt5 import QtCore
import numpy as np

from . import globaltools as gt


class TuflowHpcCheck(QtCore.QObject):
    status_signal = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.series_data = None
        self.series_columns = {
            'tend': (1, 'tEnd'),
            'dtstar': (2, 'dtStar'),
            'dt': (3, 'dt'),
            'nu': (4, 'Nu'),
            'nc': (5, 'Nc'),
            'nd': (6, 'Nd'),
            'eff': (7, 'Efficiency'),
        }
        
    def findHpcFiles(self, root_folder):
        """
        """
        hpc_paths = []
        for root, dirs, files in os.walk(root_folder):
            self.status_signal.emit('Searching folder {0} ...'.format(root))
            for f in files:
                filepath = os.path.join(root,f)

                # Skip the differently formatted files for section MB
                if 'hpc.dt.csv' in filepath:
                    hpc_paths.append(filepath)

        return hpc_paths
    
    def seriesColumn(self, column_name):
        if not column_name in self.series_columns.keys():
            return None
            # raise KeyError('Column name does not exist')
        return (self.series_columns[column_name][0], self.series_columns[column_name][1])
    
    def loadHpcFile(self, hpc_path):
        """Load the contents of TUFLOW hpc.dt.csv file.
        
        Note:
            As well as returning the loaded data, it is saved as a class member.
        
        Args:
            hpc_path(str): file path for the hpc dt log file (hpc.dt.csv)
        
        Return:
            nparray: containing the loaded series data
        """
        
        # use_cols = (1, 2, 3, 4, 5, 6, 7)
        converters = {
            1: lambda x: float(x.strip()) / 3600
        }
        self.series_data = np.loadtxt(hpc_path, delimiter=',', skiprows=1, converters=converters)
        return self.series_data
            

def getMbHeaders(mb_path):
    """Get the column headers to load for a specific MB file type.
    
    Args:
        mb_path(str): the file path of the MB file being loaded.
        
    Return:
        tuple(list, str, str) - (column headers, MB file type, filename)
            where the MB file type is either MB, MB1D, MB2D.
    """
    mb_type = ''
    headers = []
    filename = os.path.split(mb_path)[1]
    if filename.endswith('_MB.csv'):
        headers = [
            'Q Vol In', 'Q Vol Out', 'Tot Vol In', 'Tot Vol Out', 'Vol I-O', 
            'dVol', 'Vol Err', 'Q ME (%)', 'Vol I+O', 'Tot Vol', 'Cum Vol I+O',
            'Cum Vol Err', 'Cum ME (%)', 'Cum Q ME (%)',
        ]
        mb_type = 'MB'
    elif filename.endswith('_MB2D.csv'):
        headers = [
            'V In-Out', 'dVol', 'V Err', 'Q ME (%)', 'Total V', 'Cum V In+Out',
            'Cum V Error', 'Cum ME (%)', 'Cum Q ME (%)',
        ]
        mb_type = 'MB2D'
    elif filename.endswith('_MB1D.csv'):
        headers = [
            'Vol In-Out', 'dVol', 'Vol Err', 'Q ME (%)', 'Total Vol', 'Cum Vol I+O',
            'Cum Vol Err', 'Cum ME (%)', 'Cum Q ME (%)',
        ]
        mb_type = 'MB1D'
    else:
        mb_type = None

    return headers, mb_type, filename


def getIndividualMbSeriesPresets(series_type, mb_type):
    """Get preset graph series configurations.
    
    Args:
        series_type(str): the type of preset graph to show.
        mb_type(str): the type of MB file (MB, MB1D, MB2D)
        
    Return:
        graph_series(list) - containing two elements, both lists, the first
            contains the series headers for the primary axis and the second
            contains the series headers for the secondary axis.
    """
    graph_series = []
    if series_type == 'mb_and_dvol':
        if mb_type == 'MB':
            graph_series = ['Cum ME (%)', 'dVol']
        elif mb_type == 'MB1D':
            graph_series = ['Cum ME (%)', 'dVol']
        elif mb_type == 'MB2D':
            graph_series = ['Cum ME (%)', 'dVol']

    elif series_type == 'volumes':
        if mb_type == 'MB':
            graph_series = ['Q Vol In', 'Q Vol Out']
        elif mb_type == 'MB1D':
            graph_series = ['Vol In-Out', 'Cum Vol I+O']
        elif mb_type == 'MB2D':
            graph_series = ['V In-Out', 'Cum V In+Out']

    # elif series_type == 'volumes_totals':
    #     if mb_type == 'MB':
    #         graph_series = ['Tot Vol In', 'Tot Vol Out']
    #     elif mb_type == 'MB1D':
    #         graph_series = ['Vol In-Out', 'Cum Vol I+O']
    #     elif mb_type == 'MB2D':
    #         graph_series = ['V In-Out', 'Cum V In+Out']

    elif series_type == 'mass_errors':
        if mb_type == 'MB':
            graph_series = ['Q ME (%)', 'Cum ME (%)']
        elif mb_type == 'MB1D':
            graph_series = ['Q ME (%)', 'Cum ME (%)']
        elif mb_type == 'MB2D':
            graph_series = ['Q ME (%)', 'Cum ME (%)']
    # elif series_type == 'mass_errors':
    #     if mb_type == 'MB':
    #         graph_series = [['Q ME (%)', 'Cum ME (%)', 'Cum Q ME (%)'],[]]
    #     elif mb_type == 'MB1D':
    #         graph_series = [['Q ME (%)', 'Cum ME (%)', 'Cum Q ME (%)'],[]]
    #     elif mb_type == 'MB2D':
    #         graph_series = [['Q ME (%)', 'Cum ME (%)', 'Cum Q ME (%)'],[]]

    elif series_type == 'volume_errors':
        if mb_type == 'MB':
            graph_series = ['Vol Err', 'Cum Vol Err']
        elif mb_type == 'MB1D':
            graph_series = ['Vol Err', 'Cum Vol Err']
        elif mb_type == 'MB2D':
            graph_series = ['V Err', 'Cum V Error']
            
    return graph_series


class TuflowStabilityCheck(QtCore.QObject):
    status_signal = QtCore.pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
    
    def findMbFiles(self, root_folder, mb_types=['_MB']):
        """
        """
        mb_paths = []
        for root, dirs, files in os.walk(root_folder):
            self.status_signal.emit('Searching folder {0} ...'.format(root))
            for f in files:
                filepath = os.path.join(root,f)
                # Skip the differently formatted files for section MB
                if '_1d_MB.csv' in filepath: continue
                # Otherwise grab the file path
                for mbt in mb_types:
                    if mbt + '.csv' in filepath:
                        mb_paths.append(filepath)
        return mb_paths
    
    def loadMultipleFiles(self, mb_files, headers=['Cum ME (%)', 'dVol']):
        results = []
        failed_load = {'error': [], 'empty': []}
        total = len(mb_files)
        count = 0
        empty_count = 0
        fail_count = 0
        for mb in mb_files:
            self.status_signal.emit('Loading MB file {0} of {1}'.format(count, total))
            try:
                contents = self.loadMbFile(mb, headers)
                if contents is not None:
                    run_name = os.path.split(mb)[1]
                    run_name = os.path.splitext(run_name)[0]
                    max_mb = max(contents['Cum ME (%)'])
                    min_mb = min(contents['Cum ME (%)'])
                    big_mb = round(max_mb, 2) if max_mb > -min_mb else round(min_mb, 2)
                    fail = big_mb > 1 or big_mb < -1
                    results.append({
                        'path': mb, 'name': run_name, 'data': contents, 'max_mb': big_mb,
                        'fail': fail,
                    })
                    count += 1
                else:
                    empty_count += 1
                    failed_load['empty'].append(mb)
            except Exception as err:
                fail_count += 1
                plen = len(mb)
                txt = '[Chars {0}] {1}'.format(plen, mb)
                failed_load['error'].append(txt)

        if empty_count > 0 or fail_count > 0:
            self.status_signal.emit('Loaded {0} files out of {1} ({2} files were empty and {3} failed to load)'.format(
                count, total, empty_count, fail_count
            ))
        else:
            self.status_signal.emit('Loaded {0} files out of {1}'.format(
                count, total
            ))
        return results, failed_load

    def loadMbFile(self, mb_path, headers=['Cum ME (%)', 'dVol']):
        """Load the contents of TUFLOW MB/MB1D/MB2D.csv file.
        
        Need to be a bit careful about how we load this because the exact string used
        as the header changes between MB file types and I'm not sure that the columns
        always occur in the same place. So we search the headers for what we want and
        then grab the data from the columns that we identify.
        
        Args:
            mb_path(str): file path for the mass balance results file (MB.csv)
            headers(list): containing the header strings. Time will be included
                automatically.
        
        Return:
            Dict containing {time, header1, header2, etc} for the loaded file.
        """
        results = {'Time (h)': []}
        col_lookup = {'Time (h)': -1}
        for h in headers:
            results[h] = []
            col_lookup[h] = -1

        mb_path = gt.longPathCheck(mb_path)
        with open(mb_path, 'r') as mb_file:
            reader = csv.reader(mb_file, delimiter=',')
            count = 0
            for r in reader:
                if count == 0:
                    # This is a dirty approach but there will only ever be about 20
                    # columns and it's only run on one row so it shouldn't take too long
                    for i, col in enumerate(r):
                        strip_col = col.strip()
                        for l in col_lookup.keys():
                            if l == strip_col: col_lookup[l] = i 
                else:
                    for res in results.keys():
                        results[res].append(float(r[col_lookup[res]]))
                count += 1
                
        # Return None if there is no data in the file
        if len(results['Time (h)']) < 2:
            return None
        else:
            return results
        

    