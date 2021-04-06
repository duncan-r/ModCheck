
'''
@summary: Check FMP-TUFLOW changes to default run variables.

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 12th February 2021
@copyright: Ermeview Environmental Ltd
@license: LGPL v2
'''

# import logging
# logging.basicConfig(level=logging.DEBUG)

import csv
import math
import os
import re
from pprint import pprint
import sys

from ship.utils import utilfunctions as uf
from ship.utils.fileloaders import fileloader as fl

from . import toolinterface as ti


class DefaultVariables():
    
    IEF_VARS = {
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
        '2DTimestep': {'var_name': '2D Timestep', 'value_default': ['value', 'Between 1/4 - 1/2 of cell size'], 'description': '2D Timestep - may also be set and/or overriden in the 2D model'},
        'LaunchDoublePrecisionVersion': {'var_name': 'Double Precision FMP', 'checkval': '0', 'value_default': ['Yes', 'No'], 'description': 'Whether double precision FMP is being used'},
        '2DDoublePrecision': {'var_name': 'Double Precision TUFLOW', 'checkval': '0', 'value_default': ['Yes', 'No'], 'description': 'Whether double precision 2D model (like TUFLOW) is being used'},
    }
    
    def __init__(self):
        pass
    
    def checkFmpVariables(self, ief, params):
        variables = DefaultVariables.IEF_VARS
        for variable, variable_dict in variables.items():
            ief_value = ief.getValue(variable)
            has_checkval = True if 'checkval' in variable_dict.keys() else False
            check_value = variable_dict['value_default'][0] if not has_checkval else variable_dict['checkval']
            used_value = variable_dict['value_default'][0] if not variable_dict['value_default'][0] == 'value' else ief_value
            
            if ief_value is not None and not ief_value == check_value:
                params['changed'][variable_dict['var_name']] = {
                    'ief_variable_name': variable, 'value': used_value, 
                    'default': variable_dict['value_default'][1],
                    'description': variable_dict['description'],
                }
            else:
                params['default'][variable_dict['var_name']] = {
                    'ief_variable_name': variable, 'value': used_value, 
                    'default': variable_dict['value_default'][1],
                    'description': variable_dict['description'],
                }
        return params
        

    def checkTuflowVariable(self, variable):
        pass
        

class IefVariablesCheck(ti.ToolInterface):

    
    def __init__(self, project, ief_path):
        super().__init__()
        self.project = project
        self.ief_path = ief_path

        self.variables = {
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
            '2DTimestep': {'var_name': '2D Timestep', 'value_default': ['value', 'Between 1/4 - 1/2 of cell size'], 'description': '2D Timestep - may also be set and/or overriden in the 2D model'},
            'LaunchDoublePrecisionVersion': {'var_name': 'Double Precision FMP', 'checkval': '0', 'value_default': ['Yes', 'No'], 'description': 'Whether double precision FMP is being used'},
            '2DDoublePrecision': {'var_name': 'Double Precision TUFLOW', 'checkval': '0', 'value_default': ['Yes', 'No'], 'description': 'Whether double precision 2D model (like TUFLOW) is being used'},
            '2DOptions': {'var_name': '2D Run Options', 'value_default': ['value', ''], 'description': 'Run options (scenarios/events) for 2D scheme'},
        }

        
    def run_tool(self):
        super()
        return self.loadIefVariables()
    
    def checkFmpVariables(self, ief, params):

        for variable, variable_dict in self.variables.items():
            ief_value = ief.getValue(variable)
            has_checkval = True if 'checkval' in variable_dict.keys() else False
            check_value = variable_dict['value_default'][0] if not has_checkval else variable_dict['checkval']
            used_value = variable_dict['value_default'][0] if not variable_dict['value_default'][0] == 'value' else ief_value
            
            if ief_value is not None and not ief_value == check_value:
                params['changed'][variable_dict['var_name']] = {
                    'ief_variable_name': variable, 'value': used_value, 
                    'default': variable_dict['value_default'][1],
                    'description': variable_dict['description'],
                }
            else:
                params['default'][variable_dict['var_name']] = {
                    'ief_variable_name': variable, 'value': used_value, 
                    'default': variable_dict['value_default'][1],
                    'description': variable_dict['description'],
                }
        return params
        
    def loadIefVariables(self):
        """Loads an FMP ief file and reads the contents.
        
        Extracts all of the filepaths from the ief file. If a particular type of
        filepath does not exists in the ief it will return None as the value.
        
        Checks for the existance and, if found, setting of all the key parameters
        in the ief file. If they are not set to default values they are added to
        the params dictionary.
        
        Args:
            filepath(str): location of ief file on disk.
        
        Return:
            tuple(dict, dict) - containing (filepaths, parameters).
        """
#         root, ext = os.path.splitext(self.ief_path)
#         if not ext == '.ief':
#             raise AttributeError ('Must provide an FMP .ief file')
        
        loader = fl.FileLoader()
        ief = loader.loadFile(self.ief_path)
#         try:
#             ief = loader.loadFile(self.ief_path)
#         except OSError as err:
#             raise ('Unable to read .ief file')
        
        filepaths = {
            'Ief file': ief.path_holder.absolutePath(),
            '1D data file': ief.getValue('Datafile'),
            '2-d control file': ief.getValue('2DFile'),
            'Results files': ief.getValue('Results'),
            'Initial conditions file': ief.getValue('InitialConditions'),
            'Event data': ief.getIedData()
        }
        
        # Check if any key params have been changed from default
        params = {'changed': {}, 'default': {}}
        params['changed']['Timestep'] = ['Not found', '']
        if not ief.getValue('Timestep') is None:
            params['changed']['Timestep'] = {
                'ief_variable_name': 'Timestep', 'value': ief.getValue('Timestep'), 
                'default': 'If 2D model - No less than 1/2 of 2D timestep',
                'description': ''
            }
        params = self.checkFmpVariables(ief, params)
        return filepaths, params
    
    def loadSummaryInfo(self, ief_path):
#         lookup = [
#             ['2DTimestep', ''], ['Slot', 'No'], ['theta', '0.7'], ['alpha', '0.7'], 
#             ['qtol', '0.01'], ['htol', '0.01'], ['dflood', '3'], 
#             ['maxitr', '6'], ['minitr', '2'], ['MatrixDummy', '0'], ['NewMatrixDummy', '0'], 
#             ['LaunchDoublePrecisionVersion', 'No'], ['2DScheme', 'None'], ['2DDoublePrecision', 'No'], 
#             ['2DOptions', ''],
#         ]
        lookup = [
            'Timestep', '2D Timestep', 'Priessmann Slot', 'theta', 'alpha', 
            'qtol', 'htol', 'dflood', 
            'maxitr', 'minitr', 'Matrix Dummy', 'Global Matrix Dummy', 
            'Double Precision FMP', '2D Scheme', 'Double Precision TUFLOW', 
            '2D Run Options', '2D Scheme'
        ]
        no_flag = [
            'Timestep', '2D Timestep', 'Double Precision TUFLOW', 'Double Precision FMP',
            '2D Run Options', '2D Scheme'
        ]
        self.ief_path = ief_path
        _, variables = self.loadIefVariables()
        params = variables['changed']
        outputs = []
        filename = os.path.split(ief_path)[1]
        outputs.append([filename, False])
        changed_keys = variables['changed'].keys()
        default_keys = variables['default'].keys()
        for l in lookup:
            if l in changed_keys:
                changeval = False if l in no_flag else True
                outputs.append([variables['changed'][l]['value'], changeval])
            else:
                outputs.append([variables['default'][l]['default'], False])
        outputs.append([ief_path, False])
        return outputs
        
        
#         loader = fl.FileLoader()
#         ief = loader.loadFile(ief_path)
#         filename = os.path.split(ief_path)[1]
#         outputs = [filename]
#         if not ief.getValue('Timestep') is None:
#             outputs.append(ief.getValue('Timestep'))
#         else:
#             outputs.append('Not set')
#         for l in lookup:
#             val = ief.getValue(l[0])
#             if val is None or val == 'None':
#                 val = l[1]
#             elif val == '1' and (
#                 l[0] == '2DDoublePrecision' or l[0] == 'Slot' or l[0] == 'LaunchDoublePrecisionVersion'
#             ):
#                 val = 'Yes'
#             outputs.append(val)
#         outputs.append(ief_path)
#         return outputs


class ZzdFileCheck(ti.ToolInterface): 
    
    def __init__(self, project, zzd_path):
        super().__init__()
        self.project = project
        self.zzd_path = zzd_path
        
    def run_tool(self):
        super()
        return self.loadZzdContents()
    
    def loadZzdContents(self):
        """
        """
        details = {
            'Run name': {'value': '', 'description': 'Name of the run'},
            'Run date': {'value': '', 'description': 'Date that simulation was run'},
            'Dat file': {'value': '', 'description': 'FMP .dat file used for run'},
            'Version': {'value': '', 'description': 'FMP software version used'},
            'TUFLOW links': {'value': '', 'description': 'Number of links/connections to TUFLOW used'},
            'Unconverged timesteps': {'value': '', 'description': 'Number of unconverged timesteps (high is bad: check for timing around peak)'},
            'Proportion unconverged': {'value': '', 'description': 'Percentage of run unconverged (high is bad)'},
            'Mass balance (Peak volume)': {'value': '', 'description': 'Mass balance error as % of total volume in simulation'},
            'Mass balance (Inflow volume)': {'value': '', 'description': 'Mass balance error as % of total inflow volume from boundaries'},
        }
        warnings = {'warning': {}, 'error': {}}

        with open(self.zzd_path, 'r') as zzd_file:
            lines = zzd_file.readlines()
            line_count = 0
            for line in lines:
                if 'FILE=' in line:
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
                    
                elif '*** warning' in line:
                    warning_type = line[12:18]
                    if not warning_type in warnings['warning'].keys():
                        warnings['warning'][warning_type] = {'count': 1, 'info': ''}
                        info = lines[line_count + 2]
                        if lines[line_count + 3].strip() != '':
                            info += ' ' + lines[line_count + 3].strip()
                        warnings['warning'][warning_type]['info'] = info
                    else:
                        warnings['warning'][warning_type]['count'] += 1
                elif '*** error' in line:
                    error_type = line[12:18]
                    if not error_type in warnings['error'].keys():
                        warnings['error'][error_type] = {'count': 1, 'info': ''}
                        info = lines[line_count + 2]
                        if lines[line_count + 3].strip() != '':
                            info += ' ' + lines[line_count + 3].strip()
                        warnings['error'][error_type]['info'] = info
                    else:
                        warnings['error'][error_type]['count'] += 1
                    
                elif 'Number of links to TUFLOW' in line:
                    split_line = line.split(':')
                    details['TUFLOW links']['value'] = split_line[1].strip()
                elif 'Number of unconverged timesteps' in line:
                    split_line = line.split(':')
                    details['Unconverged timesteps']['value'] = split_line[1].strip()
                elif 'Proportion of simulation unconverged' in line:
                    split_line = line.split(':')
                    details['Proportion unconverged']['value'] = split_line[1].strip()
                elif 'Mass balance error:' in line:
                    split_line = line.split(':')
                    details['Mass balance (Peak volume)']['value'] = split_line[1].strip()
                elif 'Mass balance error [2]:' in line:
                    split_line = line.split(':')
                    details['Mass balance (Inflow volume)']['value'] = split_line[1].strip()

                line_count += 1
        return details, warnings
        
 
class TlfDetailsCheck(ti.ToolInterface):
    
    def __init__(self, project, tlf_path):
        super().__init__()
        self.project = project
        self.tlf_path = tlf_path
        self.variables = {}
        self.files = []
        self.checks = {}
        self.run_summary = {}
        
    def run_tool(self):
        super()
        self.loadTlfDetails()
    
    def loadTlfDetails(self):
        """
        
        TODO:
            - Deal with domain specific variables
            - Deal with domain specific file calls
            - Deal with multiple BC Event Name and Source 
            - Deal with specified events, specified scenarios, and defined variables
        """
#         domain_commands = {
#             'Cell Wet/Dry Depth': {
#                 'Domain': '', 'default': '0.001', 'value': '', 'options': '', 'description': ''
#             }
#         }
        control_file_types = ['.tcf', '.ecf', '.tgc', '.tbc', '.tmf', '.tef', '.trf', '.tlf']
        self.files = {}
        self.checks = {}

        self.variables = {
            'GIS Format': {'default': '', 'value': '', 'options': '', 'description': ''},
            'GRID Format': {'default': 'FLT', 'value': '', 'options': '', 'description': ''},
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
            'Viscosity Formulation': {'default': 'SMAGORINSKY', 'value': '', 'options': 'CONSTANT | SMAGORINSKY', 'description': ''},
            '[Smagorinsky & Constant] Viscosity Coefficients': {'default': '0.5, 0.05', 'value': '', 'options': '', 'description': ''},
            'Viscosity Approach': {'default': 'METHOD B', 'value': '', 'options': '', 'description': ''},
            'Water Level Checks': {'default': 'ON', 'value': '', 'options': 'ON | OFF', 'description': ''},
            'HX Dry 1D Node Test': {'default': 'OFF', 'value': '', 'options': 'ON | OFF', 'description': ''},
            'Distribute HX Flows': {'default': 'OFF', 'value': '', 'options': 'ON | OFF', 'description': 'Only applies to ESTRY'},
            'Unused HX and SX Connections': {'default': 'ERROR', 'value': '', 'options': 'ERROR | WARNING', 'description': ''},
            'Adjust Head at Estry Interface': {'default': 'ON', 'value': '', 'options': 'ON | ON VARIABLE | OFF', 'description': ''},
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
        }
        
        self.run_summary = {
            'Start Time (h)': {'value': '', 'description': ''},
            'End Time (h)': {'value': '', 'description': ''},
            'Build': {'value': '', 'description': ''},
            'Simulation Started': {'value': '', 'description': ''},
            'Clock Time': {'value': '', 'description': ''},
            'WARNINGs prior to simulation': {'value': '', 'description': ''},
            'WARNINGs during simulation': {'value': '', 'description': ''},
            'CHECKs prior to simulation': {'value': '','description': ''},
            'CHECKs during simulation': {'value': '', 'description': ''},
            'Classic 2D Negative Depths': {'value': '', 'description': ''},
            'Volume Error (m3)': {'value': '', 'description': ''},
            'Peak ddV over one timestep': {'value': '', 'description': ''},
            'Peak ddV as a % of peak dV': {'value': '', 'description': ''},
            'Peak Cumulative ME': {'value': '', 'description': ''},
        }
        
        run_summary_keys = self.run_summary.keys()
        command_keys = self.variables.keys()
        with open(self.tlf_path, 'r') as tlf_file:
            line_counter = 1
            for line in tlf_file:
                
                rmatch = re.search('(WARNING|ERROR|CHECK)\s[0-9]{4}', line)
                if not rmatch is None:
                    check_and_code = rmatch.group().split(' ')
                    check_type = check_and_code[0]
                    check_code = check_and_code[1]
                    msg = line
                    temp_count = 0
                    wiki_link = 'Unknown'
                    for line in tlf_file:
                        # This is a bit silly. Use readline rather than iterator
                        if 'Wiki Link:' in line:
                            wiki_link = line
                            break
                        elif temp_count > 1: break
                        temp_count += 1
                        line_counter += 1
                    wiki_link = wiki_link.replace('Wiki Link: ', '')
                    if not check_code in self.checks.keys():
                        self.checks[check_code] = {
                            'type': check_type, 'code': check_code, 'count': 1, 'message': msg,
                            'wiki_link': wiki_link
                        }
                    else:
                        self.checks[check_code]['count'] += 1
                else:
                    
                    found_file = False
                    # THIS IS STUPID: use a regex for it
                    for c in control_file_types:
                        # Dodge instances of the extension being included as a description
                        if c in line and not (' ' + c) in line:
                            found_file = True
                            try:
                                split_line = line.split(c)
                                # Replace backslashes with forward to avoid split issues with escape chars
                                filename = split_line[0].replace('\\', '/')
                                filename = filename.split('/')
                                filename = filename[-1] + c
                                if not filename in self.files.keys():
                                    temp = c[1:].upper()
                                    format_line = '[Line {}] {}'.format(line_counter, line)
                                    self.files[filename] = [temp, format_line]
                            except Exception as err:
                                continue
                            break
                    
                    if not found_file:
                        found_variable = False
                        split_line = line.split('==')
                        command = None
                        value = None
                        if len(split_line) > 1:
                            command = split_line[0].strip()
                            value = split_line[1].split('!')
                            value = value[0].strip()
                        
                            for c in command_keys:
                                if command == c:
                                    found_variable = True
                                    self.variables[c]['value'] = value
                        
                        if not found_variable:
                            split_line = line.split(':')
                            if line.startswith('Clock Time:'):
                                val = split_line[-1].split('[')[-1].replace(']', '')
                                self.run_summary['Clock Time']['value'] = val
                            elif split_line[0] in run_summary_keys:
                                self.run_summary[split_line[0]]['value'] = split_line[1].lstrip().rstrip()

                line_counter += 1
        
                    