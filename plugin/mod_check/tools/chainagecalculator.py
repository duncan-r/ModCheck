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



class CompareFmpTuflowChainage():
    
    def __init__(self):
        super().__init__()
        self.fmp_chainage = None
        self.reach_chainage = None
        self.tuflow_chainage = None
        self.comparison = None
        
    def fmpChainage(self, dat_path):
        model = self.loadFmpModel(dat_path)
        self.fmp_chainage, self.reach_chainage = self.calculateFmpChainage(model)
        return self.fmp_chainage, self.reach_chainage

    def tuflowChainage(self, nwk_layer):
        self.tuflow_chainage = {}
        for feature in nwk_layer.getFeatures():
            fmp_id = feature['ID']
            tuflow_table_length = feature['Len_or_ANA']
            tuflow_geom_length = feature.geometry().length()
            self.tuflow_chainage[fmp_id] = [tuflow_table_length, tuflow_geom_length]
        return self.tuflow_chainage 
    
    def compareChainage(self, fmp_chainage, tuflow_chainage, dx_tol):    
        problem_nodes = {'no_nwk': [], 'mismatch': []}
        self.comparison = {'missing': [], 'fail': [], 'ok': []}
        tuflow_keys = tuflow_chainage.keys()
        
        for node in fmp_chainage:
            node_id = node['name']
            if not node_id in tuflow_keys:
                # Check that the FMP node has chainage > 0. Otherwise it won't have
                # a nwk line anyway
                if node['chainage'] > 0.0001 and node['category'] == 'river':
                    problem_nodes['no_nwk'].append('{} ({})'.format(node_id, node['category']))
                    self.comparison['missing'].append({
                        'type': node['category'], 'name': node_id, 'chainage': node['chainage'],
                        'nwk_line_length': -1, 'nwk_len_or_ana': -1, 'diff': -1, 'status': 'NOT FOUND'
                    })
            else:
                if tuflow_chainage[node_id][0] > 0.0000:
                    nwk_chain = tuflow_chainage[node_id][0]
                else:
                    nwk_chain = tuflow_chainage[node_id][1]
                chain_diff = abs(node['chainage'] - nwk_chain)
                output_diff = node['chainage'] - nwk_chain
                temp = {
                    'type': node['category'], 'name': node_id, 'chainage': node['chainage'],
                    'nwk_line_length': tuflow_chainage[node_id][1], 
                    'nwk_len_or_ana': tuflow_chainage[node_id][1], 'diff': output_diff,
                    'status': 'NA',
                }
                if chain_diff > dx_tol:
                    temp['status'] = 'FAIL'
                    self.comparison['fail'].append(temp)
                else:
                    temp['status'] = 'PASS'
                    self.comparison['ok'].append(temp)
        return self.comparison

    def loadFmpModel(self, dat_path):
        file_loader = fl.FileLoader()
        model = file_loader.loadFile(dat_path)
        return model
        
    def calculateFmpChainage(self, model):
        
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
                        'start': unit.name, 'end': '', 'total_chainage': chainage,
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
                    reach_totals[-1]['end'] = prev_unit_name
                    reach_totals[-1]['total_chainage'] = cum_reach_chainage
                    reach_totals[-1]['section_count'] = reach_section_count
                    reach_number += 1
                cum_reach_chainage = 0
                reach_section_count = 0
                in_reach = False
                
        return unit_chainage, reach_totals
    
    def exportResults(self, folder, result_type):
        
        def writeOutput(filename, header, data):
            with open(filename, 'w', newline='\n') as  outfile:
                writer = csv.writer(outfile, delimiter=',')
                writer.writerow(header)
                for row in data:
                    out_row = [row[k] for k in header]
                    writer.writerow(out_row)

        def saveFmpChainage(folder):
            header = [
                'category', 'name', 'chainage', 'reach_number', 'cum_reach_chainage',
                'cum_total_chainage'
            ]
            save_path = os.path.join(folder, 'fmp_chainage.csv')
            writeOutput(save_path, header, self.fmp_chainage)

        def saveReachChainage(folder):
            header = [
                'reach_number', 'start', 'end', 'total_chainage',
            ]
            save_path = os.path.join(folder, 'fmp_reach_chainage.csv')
            writeOutput(save_path, header, self.reach_chainage)

        def saveComparison(folder):
            header = [
                'status', 'type', 'name', 'diff', 'chainage', 'nwk_line_length', 
                'nwk_len_or_ana',
            ]
            data = self.comparison['fail'] + self.comparison['missing'] + self.comparison['ok']
            save_path = os.path.join(folder, 'fmptuflow_chainage_compare.csv')
            writeOutput(save_path, header, data)
        
        if result_type == 'fmp' and self.fmp_chainage is not None: 
            saveFmpChainage(folder)
        if result_type == 'reach' and self.reach_chainage is not None: 
            saveReachChainage(folder)
        if result_type == 'comparison' and self.comparison is not None: 
            saveComparison(folder)
        