'''
@summary: Load FMP results and check for stability issues.

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 15th May 2021
@copyright: Ermeview Environmental Ltd
@license: LGPL v2
'''

import os
import sys
import csv
from pprint import pprint
from PyQt5 import QtCore
from subprocess import Popen, PIPE
import numpy as np

from ship.utils.fileloaders import fileloader as fl
from ship.utils import utilfunctions as uf
from ship.fmp.datunits import ROW_DATA_TYPES as rdt


class FmpStabilityCheck(QtCore.QObject):
    
    def __init__(self):
        super().__init__()
        
    def loadDatFile(self, dat_path):
        """Load section data from an FMP .dat model file.
        
        Args:
            dat_path(str): path to the FMP .dat file.
        
        Return:
            list - RiverUnit's found in the .dat file.
            nodes - name of all of the RiverUnits in the file.
            
        Raises:
            OSError - if file could not be loaded.
        """
        file_loader = fl.FileLoader()
        try:
            model = file_loader.loadFile(dat_path)
        except Exception as err:
            pass
        rivers = model.unitsByType('river')
        nodes = []
        for r in rivers:
            nodes.append(r.name)
        return rivers, nodes
        
    def createTcsFile(self, section_names, results_path):
        """Creates a .tcs file based on lsd values and writes it to file.
        
        The .tcs file is used by the TabularCSV.exe application to convert the
        results from binary into csv format. It contains a list of the section
        names (nodes) to be included and other formatting details.
        
        This function creates two, one for flow and one for stage.
        
        Args:
            section_names(list): contain the names to be used.
            
        Return:
            tuple(str, str): the paths to the two files created (stage, flow).
            
        Raises:
            OSError: if file cannot be written.
        """
        out_paths = {
            'stage': results_path + '_modcheck_Stage.csv',
            'flow': results_path + '_modcheck_Flow.csv',
        }
        header_stage = ['[Data]',
                        'OutputOption=0',
                        'DataItem=2',
                        'ColumnPerNode=2',
                        'OutputTimeUnits=1',
                        'MaxOverOutputInterval=0',
                        '[Files]',
                        'OutputFileName={}'.format(out_paths['stage']),
                        '[Times]',
                        'FirstOutputTimeID=-1',
                        'LastOutputTimeID=-1',
                        'OutputInterval=1',
                        '[Nodes]'
                       ]
        header_flow = ['[Data]',
                        'OutputOption=0',
                        'DataItem=1',
                        'ColumnPerNode=2',
                        'OutputTimeUnits=1',
                        'MaxOverOutputInterval=0',
                        '[Files]',
                        'OutputFileName={}'.format(out_paths['flow']),
                        '[Times]',
                        'FirstOutputTimeID=-1',
                        'LastOutputTimeID=-1',
                        'OutputInterval=1',
                        '[Nodes]'
                       ]
        
        count = 1
        data = []
        for u in section_names:
            data.append('Node' + str(count) + '=' + u)
            count += 1
        
        header_stage.append('Count=' + str(count))
        header_stage.extend(data)
        header_flow.append('Count=' + str(count))
        header_flow.extend(data)
        
        s = results_path + '_modcheck_stage.tcs'
        f = results_path + '_modcheck_flow.tcs'
        try:
            with open(s, 'w') as outfile:
                for line in header_stage:
                    outfile.write('{}\n'.format(line))

            with open(f, 'w') as outfile:
                for line in header_flow:
                    outfile.write('{}\n'.format(line))

        except OSError as err:
            raise OSError('Unable to write .tcs files')
            
        return s, f, out_paths
        
    def convertResults(self, tabular_path, tcs_path, results_path):
        """Call TabularCSV to convert binary results to CSV.
        
        Runs the FMP TabularCSV.exe tool in headless model to convert the
        proprietary FMP bindary results to a usable csv output.
    
        Args:
            tcs_path(str): path to the .tcs results output template.
            tabular_path(str): path to the TabularCSV.exe application.
            results(str): path to the binary results to convert.
        
        Return:
            stdout(str): console output from the running the application.
            return_code(int): return code from the application.
        """
        cmd = [tabular_path, '-silent', '-tcs', tcs_path, results_path]
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr= p.communicate()
        return_code = p.returncode
        
        return stdout, return_code
    
    def loadResults(self, num_of_nodes, results_path):
        """
        """
        """Loads the resuls.csv file created when converting from isis binary.
    
        The conversion from the ISIS/FMP proprietary binary format creates a 
        csv file with a particular setup. This loads the csv file into a more
        usable data format for returning.
        
        Args:
            num_of_nodes(int): number of nodes in the results file. This should
                be found by reading the dat file.
            result_path(str): location of the results.csv file.
        
        Return:
            tuple(np.ndarry, list) - containing the loaded results. A 2D array with 
                the nodes along the columns and time along the rows. Second value
                is a list containg all of the time values.
        
        Raises:
            IOError: if the file cannot be loaded.
        """
        results = None
        times = []
        try:
            row_count = 0
            count = 0
            with open(results_path, 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                for row in reader:
                    
                    if count == 5:
                        times = [float(i) for i in row[1:]]
                    
                    if count == 6:
                        num_of_cols = len(row) - 1
                        results = np.empty([num_of_cols, num_of_nodes], dtype=np.float32)
                        results[:, row_count] = [float(i) for i in row[1:]]
                        row_count += 1
                    
                    elif count > 6:
                        results[:, row_count] = [float(i) for i in row[1:]]
                        row_count += 1
                    
                    count += 1

        except OSError as err:
            raise OSError('Failed to read csv results at: {}'.format(results_path))
#             logger.error('Unable to read csv results at: ' + result_path)
        
        return results, times
    

def loadGeometry(node_name, sections):
    def loadRiver(section):
        chain = section.row_data['main'].dataObjectAsList(rdt.CHAINAGE)
        elev = section.row_data['main'].dataObjectAsList(rdt.ELEVATION)
        return (chain, elev)
        
    geom = None
    for s in sections:
        if s.name == node_name:
            geom = loadRiver(s)
    return geom
        

def loadExistingResults(results_path):
    nodes = []
    times = []
    raw_results = []
    results = None
    times_horizontal = True
    start_row = 1
    result_type = 'Stage'

    try:
        row_count = 0
        count = 0
        with open(results_path, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if count == 1:
                    if row[0] == 'Flow' or row[0] == 'Stage':
                        start_row = 1
                    else:
                        start_row = 4
                        
                if count == start_row:
                    if row[0] == 'Flow':
                        result_type = 'Flow'
                        
                elif count == start_row + 1:
                    if row[0] == 'Time (hr)':
                        times_horizontal = False
                        nodes = [i for i in row[1:]]
                    else:
                        times = [float(i) for i in row[1:]]
                        
                elif count > start_row + 1:
                    if times_horizontal:
                        nodes.append(row[0])
                    else:
                        times.append(float(row[0]))
                        
                    raw_results.append([float(i) for i in row[1:]])
                    row_count += 1
                count += 1
    except OSError as err:
        raise ('Failed to read csv results at: {}'.format(results_path))
                
    if times_horizontal:
        results = np.array(raw_results).transpose()
    else:
        results = np.array(raw_results)
        
    return results, times, nodes, result_type
        