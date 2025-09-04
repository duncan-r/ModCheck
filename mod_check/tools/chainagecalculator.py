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
import itertools
from math import sqrt
from statistics import fmean

from PyQt5.QtCore import *
from qgis.core import *

from . import toolinterface as ti
from floodmodeller_api import DAT


class CompareFmpTuflowChainage(QObject):
    status_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.fmp_chainage = None
        self.reach_chainage = None
        self.tuflow_chainage = None
        self.comparison = None
        self.nwk_has_len_or_ana = True
        self.nwk_has_id = True
        
    def fmpChainage(self, dat_path):
        model = self.loadFmpModel(dat_path)
        self.fmp_chainage, self.reach_chainage, node_lookup = self.calculateFmpChainage(model)
        return self.fmp_chainage, self.reach_chainage, node_lookup

    def tuflowChainage(self, nwk_layer):
        self.tuflow_chainage = {}
        self.nwk_has_id = True
        self.nwk_has_len_or_ana = True
        self.total_tuflow_chainage = 0.0

        # Check what kind of layer we're dealing with. Make a note of whether there
        # is a Len_or_ANA column and whether there is an ID column.
        # If no Len_or_ANA it's ignored. If no ID we fall back to the first column
        len_or_ana_lookup = 'Len_or_ANA'
        headers = [f.name() for f in nwk_layer.fields()]
        if not 'Len_or_ANA' in headers:
            if not len(nwk_layer.fields()) >= 5:
                self.nwk_has_len_or_ana = False
            else:
                len_or_ana_lookup = 4

        if not len(nwk_layer.fields()) > 0:
            self.nwk_has_id = False

        for feature in nwk_layer.getFeatures():
            if self.nwk_has_id:
                # fmp_id = feature['ID']
                fmp_id = feature[0]
            else:
                fmp_id = feature[0]
            
            if self.nwk_has_len_or_ana:
                tuflow_table_length = feature[len_or_ana_lookup]
            else:
                tuflow_table_length = -1

            tuflow_geom_length = feature.geometry().length()
            self.tuflow_chainage[fmp_id] = [tuflow_table_length, tuflow_geom_length]

            if tuflow_table_length != -1 and tuflow_table_length > 0:
                prev_ttc = self.total_tuflow_chainage
                try:
                    self.total_tuflow_chainage += tuflow_table_length
                except ValueError:
                    self.total_tuflow_chainage = prev_ttc # Just in case
                    self.total_tuflow_chainage += tuflow_geom_length
            else:
                self.total_tuflow_chainage += tuflow_geom_length

        return self.tuflow_chainage, self.total_tuflow_chainage
    
    # def tuflow1dTo2dCellChainage(self, check_1d2d, cell_size):
    def tuflowHXChainage(self, fmp_chainage, node_layer, bc_layer, node_lookup, dx_tol):
        """Calcualte and compare difference between HX line lengths and FM node distance.
        
        TODO: This is horrible.
            So much looping and things going on here, it's really inefficient. There is 
            definitely a better way to do this.
            
        Args:
            nodes_lyr(QgsLayer): TUFLOW 1d_nd type layer with FM ID in first column.
            bc_layer(QgsLayer): TUFLOW 1d_bc layer.
        """
        BC_TYPE_COL = 0
        # self.tuflow_chainage = {}
        self.total_tuflow_chainage = 0.0
        self.comparison = {'missing': [], 'fail': [], 'ok': []}
        problem_nodes = {'no_nwk': [], 'mismatch': []}
        
        TOLERANCE = 0.01
        same = lambda p1, p2, tol: sum((p2[i] - p1[i])**2 for i in range(len(p1))) <= tol**2
        ####
        # hx_length = lambda hx_feat: hx_feat.geometry().length()
        # bc_layer = QgsProject.instance().mapLayersByName('2d_bc_ashton_v13')[0]
        # node_layer = QgsProject.instance().mapLayersByName('1d_isis_nodes_ashton_v13_trimmed')[0]
        # cn_features = {}
        ####
        
        
        cn_data = {}
        cn_lookup = []
        gis_nodes = []
        
        # Find the CN lines connected to each 1D node feature, then get the coordinates of
        # the end of the CN line not connected to the node (i.e. the one connected to the HX).
        for f in node_layer.getFeatures():
            
            node_id = f[0]
            gis_nodes.append(node_id)
            node_geom = f.geometry()
            point = node_geom.asPoint()
            self.status_signal.emit(f"Checking snapped CN lines for node: {node_id}")
             
            for cnf in bc_layer.getFeatures():
                if cnf["Type"] != "CN":
                    continue

                cn_geom = cnf.geometry()
                if node_geom.buffer(0.1, 5).intersects(cn_geom):
                    if not node_id in cn_data.keys():
                        cn_data[node_id] = {
                            'cn_end': [],
                            'lengths': [],
                            'hx_fids': [],
                        }
                        
                    cn_geom = cnf.geometry().constGet()[0]
                    cn_first = cn_geom[0]
                    cn_last = cn_geom[-1]
                    
                    cn_p1 = [cn_first.x(), cn_first.y()]
                    cn_p2 = [cn_last.x(), cn_last.y()]
                    cn_id = cnf.id()
                        
                    match_start = same([point.x(), point.y()], cn_p1, TOLERANCE)
                    match_end = same([point.x(), point.y()], cn_p2, TOLERANCE)
                    
                    if match_start:
                        cn_data[node_id]['cn_end'].append(cn_p2)
                        cn_lookup.append([cn_p2, node_id])
                    elif match_end:
                        cn_data[node_id]['cn_end'].append(cn_p1)
                        cn_lookup.append([cn_p1, node_id])
                    continue
        
        
        # Find where the CN lines connect to the HX lines to calculate the distance between
        # the 1D node connections.
        # Calculates the length along the HX line from the previously found CN line
        HX_SNAP_TOLERANCE = 0.05
        bc_features = bc_layer.getFeatures()
        hx_lines = [[f.id(), f.geometry().asMultiPolyline()] for f in bc_features if f[0] == 'HX']
        hx_count = len(hx_lines)
        for i, hx in enumerate(hx_lines):
            self.status_signal.emit(f"Calculating HX line lengths: {i}/{hx_count}")

            feat = hx[1][0]
            fid = hx[0]
            length = 0
            prev_point = None
            prev_node = None
            for point in feat:
                
                if prev_point:
                    length += sqrt(point.sqrDist(prev_point))
                
                for cn in cn_lookup:
                    is_match = same([point.x(), point.y()], cn[0], HX_SNAP_TOLERANCE)

                    if is_match:
                        node_name = cn[1]
                        
                        # Work out which way we're moving along the HX line. If we're going
                        # backwards we need to assign the length to the next node,
                        # otherwise it should be assigned to the previous node
                        if prev_node:
                            # Check which order index is greater
                            if node_lookup[prev_node] < node_lookup[node_name]:
                                node_name = prev_node
                        
                        # TODO remove matching CN from lookup to reduce iterations
                        cn_data[node_name]['lengths'].append(length)
                        cn_data[node_name]['hx_fids'].append(fid)
                        prev_node = cn[1]
                        length = 0
                        continue
                
                prev_point = point
                
        for i, fmp in enumerate(fmp_chainage):
            # name = fmp_chainage[a]['name']
            # fmchain = fmp_chainage[a]['chainage']
            name = fmp['name']
            fmchain = fmp['chainage']
            hx_avg = 0.0
            self.status_signal.emit(f"Comparing with FM node: {name}")

            if not name in gis_nodes:
                self.comparison['missing'].append({
                    'type': fmp['category'], 'name': name, 'chainage': fmchain,
                    'line_length': -1, 'nwk_len_or_ana': -1, 'diff': -1, 'status': 'NOT FOUND'
                })
                continue

            
            # Easy catch to avoid accidentally assigning a chainage from an end (spill) 
            # HX line. If FM is zero, it's zero.
            if not abs(fmchain) < 0.005:
                try:
                    hxchain = cn_data[name]['lengths']
                    hx_avg = fmean(hxchain)
                    
                    # End HX lines (spills) might be connected as well, we don't care about them.
                    # The length of the two 'side' HX lines should be similar, so take the 
                    # average and check against a tolerance, if it falls outside, get rid of it.
                    # TODO: This is a bit hacky, should probably check if the CN points both
                    # have the same node name and remove length if it does.
                    # TODO: Is mean the right choice, or median??
                    if len(hxchain) > 2:
                        used_hx = []
                        for hx_length in hxchain:
                            # if hx_length * 1.2 < hx_avg or hx_length * 0.8 < hx_avg:
                            #     continue
                            used_hx.append(hx_length)
                            
                        # Might fail the above check with an empty list
                        try:
                            hx_avg = fmean(used_hx)
                        except: # Actually a "StatisticsError" (fix with an import)
                            # TODO: Very, very cheap approach
                            # Generally, the end HX is in index 1.
                            # Do this properly, really!
                            hx_avg = fmean([hxchain[0], hxchain[2]])
                    
                except KeyError:
                    hx_chain = -1
                    self.comparison['missing'].append({
                        'type': fmp['category'], 'name': name, 'chainage': fmchain,
                        'line_length': -1, 'nwk_len_or_ana': -1, 'diff': -1, 'status': 'NOT FOUND'
                    })
                    
            self.total_tuflow_chainage += hx_avg
            chain_diff = abs(fmchain - hx_avg)
            temp = {
                'type': fmp['category'], 'name': name, 'chainage': fmchain,
                'line_length': hx_avg, 'nwk_len_or_ana': -1,
                'diff': chain_diff, 'status': 'NA',
            }
            if chain_diff > dx_tol:
                temp['status'] = 'FAIL'
                self.comparison['fail'].append(temp)
            else:
                temp['status'] = 'PASS'
                self.comparison['ok'].append(temp)
        
        return self.comparison, self.total_tuflow_chainage
    
    def compareChainage1dNwk(self, fmp_chainage, tuflow_chainage, dx_tol):    
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
                        'line_length': -1, 'nwk_len_or_ana': -1, 'diff': -1, 'status': 'NOT FOUND'
                    })
            else:
                # If Len_or_ANA value > 0 (default) use that, otherwise use line length
                if tuflow_chainage[node_id][0] > 0.0000:
                    nwk_chain = tuflow_chainage[node_id][0]
                else:
                    nwk_chain = tuflow_chainage[node_id][1]

                chain_diff = abs(node['chainage'] - nwk_chain)
                output_diff = node['chainage'] - nwk_chain
                temp = {
                    'type': node['category'], 'name': node_id, 'chainage': node['chainage'],
                    'line_length': tuflow_chainage[node_id][1], 
                    'nwk_len_or_ana': tuflow_chainage[node_id][0], 'diff': output_diff,
                    'status': 'NA',
                }
                if chain_diff > dx_tol:
                    temp['status'] = 'FAIL'
                    self.comparison['fail'].append(temp)
                else:
                    temp['status'] = 'PASS'
                    self.comparison['ok'].append(temp)
        return self.comparison

    # def compareChainageHXCheck(self, fmp_chainage, tuflow_chainage, dx_tol):    
    #     problem_nodes = {'no_nwk': [], 'mismatch': []}
    #     self.comparison = {'missing': [], 'fail': [], 'ok': []}
    #     tuflow_keys = tuflow_chainage.keys()
    #
    #     for node in fmp_chainage:
    #         node_id = node['name']
    #         if not node_id in tuflow_keys:
    #             # Check that the FMP node has chainage > 0. Otherwise it won't have
    #             # a nwk line anyway
    #             if node['chainage'] > 0.0001 and node['category'] == 'river':
    #                 problem_nodes['no_nwk'].append('{} ({})'.format(node_id, node['category']))
    #                 self.comparison['missing'].append({
    #                     'type': node['category'], 'name': node_id, 'chainage': node['chainage'],
    #                     'nwk_line_length': -1, 'nwk_len_or_ana': -1, 'diff': -1, 'status': 'NOT FOUND'
    #                 })
    #         else:
    #             # if tuflow_chainage[node_id][0] > 0.0000:
    #             #     nwk_chain = tuflow_chainage[node_id][0]
    #             # else:
    #             #     nwk_chain = tuflow_chainage[node_id][1]
    #             dist_full = tuflow_chainage[node_id]
    #             dist_half = dist_full / 2
    #             diff_full = abs(node['chainage'] - dist_full)
    #             diff_half = abs(node['chainage'] - dist_half)
    #             new_tol = dx_tol
    #
    #             # chain_diff = abs(node['chainage'] - nwk_chain)
    #             # output_diff = node['chainage'] - nwk_chain
    #             temp = {
    #                 'type': node['category'], 'name': node_id, 'chainage': node['chainage'],
    #                 'total_distance': dist_full, 'half_distance': dist_half,
    #                 # 'nwk_line_length': tuflow_chainage[node_id][1], 
    #                 # 'nwk_len_or_ana': tuflow_chainage[node_id][0], 
    #                 'diff': diff_full, 'diff_half': diff_half,
    #                 'comparison': '2 HX', 'status': 'NA',
    #             }
    #             if (dist_half - new_tol) <= diff_full <= (dist_half + new_tol):
    #                 temp['comparison'] = '1 HX'
    #                 temp['status'] = 'PASS'
    #                 self.comparison['ok'].append(temp)
    #
    #             else:
    #                 if diff_full > new_tol:
    #                     temp['status'] = 'FAIL'
    #                     self.comparison['fail'].append(temp)
    #                 else:
    #                     temp['status'] = 'PASS'
    #                     self.comparison['ok'].append(temp)
    #             # if chain_diff > dx_tol:
    #             #     temp['status'] = 'FAIL'
    #             #     self.comparison['fail'].append(temp)
    #             # else:
    #             #     temp['status'] = 'PASS'
    #             #     self.comparison['ok'].append(temp)
    #     return self.comparison

    def loadFmpModel(self, dat_path):
        model = None
        try:
            model = DAT(dat_path)
        except Exception as err:
            pass
        return model
        
    def calculateFmpChainage(self, model):
        
        unit_categories = ['RIVER', 'INTERPOLATE', 'REPLICATE']
        unit_chainage = []
        prev_unit_name = ''
        prev_unit_category = ''
        reach_number = 1
        cum_reach_chainage = 0
        total_chainage = 0
        in_reach = False
        reach_totals = []
        reach_section_count = 0
        node_lookup = {}
        
        # Bit manky - we're hitting a protected variable that stores the units
        # I'm not quite sure how you find either a) the first river unit in the model
        # or b) the first unit in separate reaches. Maybe there's a better way?
        # TODO: Try not to circumvent the intended API if possible.
        #       If the above can be handled, the api does offer public next/prev methods.
        for i, unit in enumerate(model._all_units):

            # Found a unit we want
            # Update the chainge values
            if unit.unit in unit_categories:
                chainage = unit.dist_to_next
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
                    'category': unit.unit, 'name': unit.name, 'chainage': chainage,
                    'prev_unit_name': prev_unit_name, 'prev_unit_cat': prev_unit_category,
                    'reach_number': reach_number, 'cum_reach_chainage': cum_reach_chainage,
                    'cum_total_chainage': total_chainage
                })
                node_lookup[unit.name] = i
                prev_unit_name = unit.name
                prev_unit_category = unit.unit

            # Not a unit we want (doesn't have any distance)
            # Reset the reach totals
            else:
                if in_reach:
                    reach_totals[-1]['end'] = prev_unit_name
                    reach_totals[-1]['total_chainage'] = cum_reach_chainage
                    reach_totals[-1]['section_count'] = reach_section_count
                    reach_number += 1
                cum_reach_chainage = 0
                reach_section_count = 0
                in_reach = False
        
        return unit_chainage, reach_totals, node_lookup
    
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
                'status', 'type', 'name', 'diff', 'chainage', 'line_length', 
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
        