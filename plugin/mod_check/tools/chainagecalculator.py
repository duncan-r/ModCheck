'''
@summary: Calculate 1D FMP chainage

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 29th September 2020
@copyright: Ermeview Environmental Ltd
@license: LGPL v2
'''

# import logging
# logging.basicConfig(level=logging.DEBUG)

import os
import sys
import csv
from pprint import pprint

from . import toolinterface as ti

from ship.utils.fileloaders import fileloader as fl
from ship.utils import utilfunctions as uf
from ship.fmp.datunits import ROW_DATA_TYPES as rdt



class CompareFmpTuflowChainage(ti.ToolInterface):
    
    def __init__(self, working_dir, dat_file, nwk_layer, dx_tol):
        super().__init__()
        self.working_dir = working_dir
        self.dat_file = dat_file
        self.nwk_layer = nwk_layer
        self.dx_tol = dx_tol
    
    def run_tool(self):
        super()
        fmp_chainage = self.fetchFmpChainage()
        tuflow_chainage = self.fetchTuflowChainage()
        return self.compareChainage(fmp_chainage, tuflow_chainage)
        
    def fetchFmpChainage(self):
        fmp_calc = FmpChainageCalculator(self.working_dir, self.dat_file)
        return fmp_calc.run_tool()
    
    def fetchTuflowChainage(self):
        estry_chainage = {}
        for feature in self.nwk_layer.getFeatures():
            fmp_id = feature['ID']
            estry_table_length = feature['Len_or_ANA']
            estry_geom_length = feature.geometry().length()
            estry_chainage[fmp_id] = [estry_table_length, estry_geom_length]
        return estry_chainage 
    
    def compareChainage(self, fmp_chainage, tuflow_chainage):    
        problem_nodes = {'no_nwk': [], 'mismatch': []}
        tuflow_keys = tuflow_chainage.keys()
        outpath = os.path.join(self.working_dir, 'chainage_compare.csv')
        with open(outpath, 'w', newline='') as outfile:
            fieldnames = [
                'node', 'node type', 'fmp chainage', 'nwk line length', 
                'nwk Len_or_ANA', 'chainage dx'
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for node in fmp_chainage:
                node_id = node['name']
                if not node_id in tuflow_keys:
                    # Check that the FMP node has chainage > 0. Otherwise it won't have
                    # a nwk line anyway
                    if node['chainage'] > 0.0001:
                        problem_nodes['no_nwk'].append('{} ({})'.format(node_id, node['category']))
                else:
                    if tuflow_chainage[node_id][0] > 0.0000:
                        nwk_chain = tuflow_chainage[node_id][0]
                    else:
                        nwk_chain = tuflow_chainage[node_id][1]
                    chain_diff = abs(node['chainage'] - nwk_chain)
                    if chain_diff > self.dx_tol:
                        problem_nodes['mismatch'].append(
                            'Node: {} ({})\t DX = {:.2f}'.format(
                                node_id, node['category'], chain_diff
                            )
                        )
                    writer.writerow({
                        'node': '\'' + node_id, 'node type': node['category'],
                        'fmp chainage': node['chainage'],
                        'nwk line length': tuflow_chainage[node_id][1], 
                        'nwk Len_or_ANA': tuflow_chainage[node_id][0],
                        'chainage dx': '{:.2f}'.format(chain_diff)
                    })
        return problem_nodes, outpath
        

class FmpChainageCalculator(ti.ToolInterface):
    
    def __init__(self, working_dir, model_path):
        super().__init__()
        self.working_dir = working_dir
        self.model_path = model_path
        
    def run_tool(self):
        super()
        model = self.load_fmp_model(self.model_path)
        return self.calculate_chainage(model)
        
    def load_fmp_model(self, fmp_path):
        file_loader = fl.FileLoader()
        try:
            model = file_loader.loadFile(fmp_path)
        except Exception as err:
            pass
        return model
        
    def calculate_chainage(self, model):
        
        unit_categories = ['river', 'interpolate', 'conduit']
        unit_chainage = []
        prev_unit_name = ''
        prev_unit_category = ''
        reach_number = 1
        cum_reach_chainage = 0
        total_chainage = 0
        in_reach = False
        reach_totals = []
        reach_section_count = 0
        
        for unit in model:
            if unit.unit_category in unit_categories:
                chainage = unit.head_data['distance'].value
                cum_reach_chainage += chainage
                total_chainage += chainage
                reach_section_count += 1

                if not in_reach:
                    reach_totals.append({
                        'start': ''.join(['"', unit.name, '"']), 'end': '', 'total_chainage': chainage,
                        'reach_number': reach_number
                    })
                
                in_reach = True
                
                unit_chainage.append({
                    'category': unit.unit_category, 'name': unit.name, 'chainage': chainage,
                    'prev_unit_name': prev_unit_name, 'prev_unit_cat': prev_unit_category,
                    'reach_number': reach_number, 'cum_reach_chainage': cum_reach_chainage,
                    'cum_total_chainage': total_chainage
                })
                prev_unit_name = unit.name
                prev_unit_category = unit.unit_category
            else:
                if in_reach:
                    reach_totals[-1]['end'] = ''.join(['"', prev_unit_name, '"'])
                    reach_totals[-1]['total_chainage'] = cum_reach_chainage
                    reach_totals[-1]['section_count'] = reach_section_count
                    reach_number += 1
                cum_reach_chainage = 0
                reach_section_count = 0
                in_reach = False
                
        outpath = os.path.join(self.working_dir, 'chainage_results.csv')
        with open(outpath, 'w', newline='') as outfile:
            fieldnames = [
                'category', 'name', 'chainage', 'reach_number', 'cumulative_reach_chainage',
                'cumulative_total_chainage'
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for unit in unit_chainage:
                writer.writerow({
                    'category': unit['category'], 'name': "\'" + unit['name'], 'chainage': unit['chainage'], 
                    'reach_number': unit['reach_number'], 'cumulative_reach_chainage': unit['cum_reach_chainage'], 
                    'cumulative_total_chainage': unit['cum_total_chainage']
                })

        outpath = os.path.join(self.working_dir, 'reach_chainage_results.csv')
        with open(outpath, 'w', newline='') as outfile:
            fieldnames = [
                'reach_number', 'start_section', 'end_section', 'section_count', 'reach_chainage',
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for reach in reach_totals:
                writer.writerow({
                    'reach_number': reach['reach_number'], 'start_section': reach['start'], 
                    'end_section': reach['end'], 'section_count': reach['section_count'], 
                    'reach_chainage': reach['total_chainage'],
                })
        
        return unit_chainage
            