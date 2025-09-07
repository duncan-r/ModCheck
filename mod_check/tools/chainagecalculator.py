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
from statistics import fmean, median

from PyQt5.QtCore import *
from qgis.core import *

from . import toolinterface as ti
from floodmodeller_api import DAT


class CompareFmpTuflowChainage(QObject):
    status_signal = pyqtSignal(str)
    progress_max_signal = pyqtSignal(int)
    progress_val_signal = pyqtSignal(int)
    
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

        fcount = nwk_layer.featureCount()
        self.progress_max_signal.emit(fcount)
        for i, feature in enumerate(nwk_layer.getFeatures()):
            self.progress_val_signal.emit(i)
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
        
        cn_data = {}
        cn_lookup = []
        gis_nodes = []
        
        # Find the CN lines connected to each 1D node feature, then get the coordinates of
        # the end of the CN line not connected to the node (i.e. the one connected to the HX).
        node_count = node_layer.featureCount()
        self.progress_max_signal.emit(node_count)
        for i, f in enumerate(node_layer.getFeatures()):
            
            node_id = f[0]
            gis_nodes.append(node_id)
            node_geom = f.geometry()
            point = node_geom.asPoint()
            # self.status_signal.emit(f"Checking snapped CN lines for node: {node_id}")
            self.status_signal.emit(f"Checking snapped CN lines...")
            self.progress_val_signal.emit(i)
             
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
        self.progress_max_signal.emit(hx_count)
        for i, hx in enumerate(hx_lines):
            self.status_signal.emit(f"Calculating HX line lengths...")
            self.progress_val_signal.emit(i)

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
                
        self.progress_max_signal.emit(len(fmp_chainage))
        for i, fmp in enumerate(fmp_chainage):
            # name = fmp_chainage[a]['name']
            # fmchain = fmp_chainage[a]['chainage']
            name = fmp['name']
            fmchain = fmp['chainage']
            hx_avg = 0.0
            self.status_signal.emit(f"Comparing with FM nodes...")
            self.progress_val_signal.emit(i)

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
                    cns = cn_data[name] 
                    hxchain = cns['lengths']
                    hx_avg = fmean(hxchain)
                    
                    # End HX lines (spills) might be connected as well, we don't care about them.
                    # Sometimes we get zero length line included. I'm not entirely sure why, but
                    # it's probably an issue with just assigning zero at zero distance FM node.
                    # Better logic in the HX measure section might handle it.
                    if len(hxchain) > 2:
                        
                        # Clear out zero length entries
                        found_zero_length = False
                        if len(cns['cn_end']) <= 2:
                            keepers = []
                            for l in hxchain:
                                # Tolerance can be quite large. Shouldn't really get such short
                                # chainage in FM anyway.
                                if abs(l) < 0.1:
                                    found_zero_length = True
                                    continue
                                keepers.append(l)
                            hx_avg = fmean(keepers)
                            
                        # Could be an 'end' HX. Compare the lengths against the median of all
                        # lengths to see if it's more than 20% out. Generally, the side HX lengths
                        # are similar and the end HX would fall far short of the median 
                        if not found_zero_length: 
                            keepers = []
                            hx_med = median(hxchain)
                            for hx_length in hxchain:
                                if hx_length * 1.2 < hx_med or hx_length * 0.8 > hx_med:
                                    continue
                                keepers.append(hx_length)

                            # Might fail the above check with an empty list
                            # At this point just give up and take the total average
                            try:
                                hx_avg = fmean(keepers)
                            except Exception: # Actually a "StatisticsError" (fix with an import)
                                hx_avg = fmean(hxchain)
                                
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
        
        self.progress_val_signal.emit(0)
        return self.comparison, self.total_tuflow_chainage
    
    def compareChainage1dNwk(self, fmp_chainage, tuflow_chainage, dx_tol):    
        problem_nodes = {'no_nwk': [], 'mismatch': []}
        self.comparison = {'missing': [], 'fail': [], 'ok': []}
        tuflow_keys = tuflow_chainage.keys()
        
        self.progress_max_signal.emit(len(fmp_chainage))
        for i, node in enumerate(fmp_chainage):
            self.progress_val_signal.emit(i)

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

        self.progress_val_signal.emit(0)
        return self.comparison

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
        