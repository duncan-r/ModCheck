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
# from subprocess import Popen, PIPE
import numpy as np

# from ship.utils.fileloaders import fileloader as fl
# from ship.fmp.datunits import ROW_DATA_TYPES as rdt
from floodmodeller_api import DAT, ZZN
from floodmodeller_api.to_from_json import to_json, from_json
from ..tools import settings as mrt_settings


def loadDatFile(dat_path):
    """Load section data from an FMP .dat model file.
    
    Args:
        dat_path(str): path to the FMP .dat file.
    
    Return:
        list - RiverUnit's found in the .dat file.
        nodes - name of all of the RiverUnits in the file.
        
    Raises:
        OSError - if file could not be loaded.
    """
    dat = None
    try:
        dat = DAT(dat_path)
    except Exception as err:
        raise Exception('Failed to load FMP .dat file')
    
    return dat

    
class StabilityResults():
    
    def __init__(self, flows, stage, nodes, times, save_interval, timestep):
        self.flows = flows
        self.stage = stage
        self.times = times
        self.timestep = timestep
        self.save_interval = save_interval
        self.nodes = nodes
        self.derivs = None
        self.failed_nodes = None
        self._dat = None
        self.section_lookup = {}
        
    def unit_type(self, node_name):
        utype = 'Unknown'
        try:
            utype = self.section_lookup[node_name]
        except KeyError:
            pass

        return utype
        
    @property
    def dat(self):
        return self._dat
    
    # TODO: Setter adding None value for some reason
    # Don't know why. Check this again at some point
    # def addDat(self, d):
    @dat.setter
    def dat(self, d):
        if not isinstance(d, DAT):
            return
        self._dat = d

        ignored_types = ['COMMENT', 'JUNCTION', 'GENERAL']
        for idx, unit in enumerate(self._dat._all_units):
            unit_type = 'Unknown'
            try:
                unit_type = unit.unit
            except TypeError:
                continue

            if unit_type in ignored_types or unit_type == 'UNSUPPORTED':
                continue

            unit_name = None
            try:
                unit_name = unit.name
            except TypeError:
                continue

            self.section_lookup[unit_name] = unit_type
            
        
def convertResults(results_path):
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
    zzn = ZZN(results_path)
    save_interval = zzn.meta['save_int']
    timestep = zzn.meta['dt']
    nodes = zzn.meta['labels']
    
    flows = zzn.to_dataframe(variable='Flow', include_time=True)
    levels = zzn.to_dataframe(variable='Stage', include_time=True)
    times = list(flows.index)
    results = StabilityResults(flows, levels, nodes, times, save_interval, timestep)
    
    return results 


def loadGeometry(node_name, dat):
    data = None
    try:
        unit = dat.sections[node_name]
        if unit.unit == 'RIVER':
            data = unit.active_data
    except KeyError:
        return None

    try:
        x = data['X'].to_numpy()
        y = data['Y'].to_numpy()
    except TypeError:
        return None
    
    return (x, y)
    
