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
from pathlib import Path
# from subprocess import Popen, PIPE
import pandas as pd
import numpy as np

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
    
    def __init__(
            self, model_type, flows, stage, nodes, times, save_interval, timestep,
            channels=None
        ):
        self.model_type = model_type
        self.flows = flows
        self.stage = stage
        self.times = times
        self.timestep = timestep
        self.save_interval = save_interval
        self._nodes = nodes
        self.derivs = None
        self.failed_nodes = None
        
        # ESTRY
        self.channels = channels
        
        # FM
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
    def nodes(self):
        if self.model_type == 'fm':
            return self._nodes
        else:
            return self.channels
        
    @property
    def dat(self):
        return self._dat
    
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
    """Use FM API to convert binary zzn results for flow/stage.
    
    Args:
        results_path(str): path to the zzn binary results to convert.
    
    Return:
        results(StabilityResults): object containing the results data
    """
    zzn = ZZN(results_path)
    save_interval = zzn.meta['save_int']
    timestep = zzn.meta['dt']
    nodes = zzn.meta['labels']
    
    flows = zzn.to_dataframe(variable='Flow', include_time=True)
    levels = zzn.to_dataframe(variable='Stage', include_time=True)
    times = list(flows.index)
    results = StabilityResults('fm', flows, levels, nodes, times, save_interval, timestep)
    
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
    
    
def loadTpc(tpc):
    tpc_path = Path(tpc)
    tpc_dir = tpc_path.parent
    output = {
        '1d_node_info': None,
        '1d_channel_info': None,
        '1d_water_levels': None,
        '1d_flows': None,
    }

    def splitLine(line, output_key):
        split_line = line.split('==')[1]
        split_line = split_line.strip()
        output[output_key] = tpc_dir / split_line

        
    lines = []
    with open(tpc, 'r') as infile:
        lines = infile.readlines()

    for l in lines:
        lowline = l.strip().lower()
        if lowline.startswith('1d node info'):
            node_info = splitLine(l, "1d_node_info")
        if lowline.startswith('1d channel info'):
            node_info = splitLine(l, "1d_channel_info")
        if lowline.startswith('1d water levels'):
            node_info = splitLine(l, "1d_water_levels")
        if lowline.startswith('1d flows'):
            node_info = splitLine(l, "1d_flows")

    success = True
    for rtype, value, in output.items():
        if value is None: success = False
        elif not value.exists(): success = False
                    
    return output, success


def loadEstryTimeSeries(result_path):
    df = pd.read_csv(result_path, sep=',', index_col=0, skipinitialspace=True)
    
    names = df.columns
    name_map = {}
    for i, n in enumerate(names):
        # if i == 0:
        #     name_map[n] = "ID"
        if i == 0:
            name_map[n] = "Time"
        else:
            temp = n.split('[')[0]
            temp = temp[2:].strip()
            name_map[n] = temp
    df.rename(columns=name_map, inplace=True)
    df.set_index('Time', drop=True, inplace=True)
    return df

def loadEstryNodeInfo(nodes_path):
    data = {}
    with open(nodes_path, 'r') as infile:
        reader = csv.reader(infile)
        for i, r in enumerate(reader):
            if i == 0: continue

            node = r[1].strip()
            number = r[0].strip()
            for channel in r[5:]:
                chan = channel.strip()
                data[chan] = {
                    'node': node,
                    'number': number,
                }
    
    return data
    
def loadEstryChannelInfo(channels_path):
    data = {}
    with open(channels_path, 'r') as infile:
        reader = csv.reader(infile)
        for i, r in enumerate(reader):
            if i == 0: continue

            channel = r[1].strip()
            node_us = r[2].strip()
            node_ds = r[3].strip()
            flags = r[6].strip()
            data[channel] = {
                'node_us': node_us,
                'node_ds': node_ds,
                'flags': flags,
            }
    
    return data

def convertEstryResults(tpc_paths):
    """Load ESTRY results from dict of TPC files.
    
    Use the loadTpc() function to retrieve the dict.
    
    Args:
        tpc_data(dict): dict of results files as returned from loadTpc().
        
    Return:
        
    """
    nodes = loadEstryNodeInfo(tpc_paths["1d_node_info"])
    channels = loadEstryChannelInfo(tpc_paths["1d_channel_info"])
    levels = loadEstryTimeSeries(tpc_paths["1d_water_levels"])
    flows = loadEstryTimeSeries(tpc_paths["1d_flows"])
    
    # TODO: Creates duplicate columns (data not name) by creating an us and ds series for
    # every channel. This could add up for large results sets.
    # It's a convenience to make lookups consistent across FM and ESTRY results, but could
    # probably be handled better. 
    new_levels = {}
    for k, v in channels.items():
        us_series = levels[v['node_us']]
        ds_series = levels[v['node_ds']]
        new_levels[k] = us_series
        new_levels[k + '_ds'] = ds_series
    new_levels = pd.DataFrame(new_levels)
    channels = list(channels.keys())

    times = levels.index.tolist()
    save_interval = times[1] - times[0]
    timestep = save_interval # Meaningless, but keeps interface consistent

    levels = new_levels
    del(new_levels)
    results = StabilityResults(
        'estry', flows, levels, nodes, times, save_interval, timestep,
        channels=channels
    )
    return results
