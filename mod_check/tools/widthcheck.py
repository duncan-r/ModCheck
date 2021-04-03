'''
@summary: Check FMP-TUFLOW cross section width parity.

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 8th February 2021
@copyright: Ermeview Environmental Ltd
@license: LGPL v2

TODO:
    Need to consider replicates as well as interpolates at some point.
'''

# import logging
# logging.basicConfig(level=logging.DEBUG)

import os
import sys
import csv
import math
from pprint import pprint

from qgis.core import QgsDistanceArea
from . import toolinterface as ti

from ship.utils.fileloaders import fileloader as fl
from ship.utils import utilfunctions as uf
from ship.fmp.datunits import ROW_DATA_TYPES as rdt


class SectionWidthCheck(ti.ToolInterface):
    
    def __init__(self, project): #, dat_path, node_layer, cn_layer, dw_tol):
        super().__init__()
        self.project = project
        self.dat_path = None
        self.node_layer = None
        self.cn_layer = None
        self.results = []
        self.failed = {}
        
        self.cn_fields = [
            "Type", "Flags", "Name", "f", "d", "td", "a", "b", 
        ]
        
    def run_tool(self):
        super()
        self.results = []
        fmp_widths = self.fetchFmpWidths(self.dat_path)
        cn_widths, total_found = self.fetchCnWidths()
        results, failed = self.check_widths(fmp_widths, cn_widths)
        return results, failed#, total_found
        
    def fetchFmpWidths(self, dat_path):
        self.dat_path = dat_path
        file_loader = fl.FileLoader()
        try:
            model = file_loader.loadFile(dat_path)
        except Exception as e:
            raise e ("Problem loading FMP .dat file at:\n{}".format(dat_path))
        unit_categories = ['river', 'interpolate']
        units = model.unitsByCategory(unit_categories)
        
        widths = {}
        prev_river = None
        interpolates = []
        interpolated_chainage = 0
        for unit in units:
            if unit.unit_type == 'river':
        
                # Get the width and deactivation values form the river section
                xvals = unit.row_data['main'].dataObjectAsList(rdt.CHAINAGE)
                dvals = unit.row_data['main'].dataObjectAsList(rdt.DEACTIVATION)
                
                x_start = xvals[0]
                x_end = xvals[-1]
                
                # loop through the section width values, check where any deactivation
                # markers are and set the active width start and end variables accordingly
                for i, x in enumerate(xvals, 0):
                    if dvals[i] == 'LEFT':
                        x_start = x
                    if dvals[i] == 'RIGHT':
                        x_end = x
                
                active_width = math.fabs(x_end - x_start)
                widths[unit.name] = [active_width, unit.unit_type]
                
                if len(interpolates) > 0:
                    r1_width = prev_river[1]
                    chainage = prev_river[2]
                    r2_width = active_width
                    x = interpolated_chainage + chainage
                    # Treat width as y and get the slope of the line
                    m = (r2_width - r1_width) / x
                    current_x = chainage
                    for i in interpolates:
                        # c = r1_width because x = 0 is at the first section
                        widths[i[0]] = [m * current_x + r1_width, 'interpolate']
                        current_x += i[1]   # add the interpolates chainage to x 
                    
                    # Reset the interpolate stuff
                    interpolates = []
                    interpolated_chainage = 0
                
                prev_river = [unit.name, active_width, unit.head_data['distance'].value]
                
            else:
                interpolates.append([unit.name, unit.head_data['distance'].value])
                interpolated_chainage += unit.head_data['distance'].value
            
        return widths
        
    def fetchCnWidths(self, node_layer, cn_layer):
        self.node_layer = node_layer
        self.cn_layer = cn_layer
        
        # Check that we have the right kind of layer
        headers = [f.name() for f in cn_layer.fields()]
        for i, field in enumerate(self.cn_fields):
            if not field in headers:
                raise AttributeError ("Selected CN layer is not a recognised 2b_bc_hx layer")

        total_found = {'nodes': 0, 'snapped_cn': 0}
        details = {}
        for f in node_layer.getFeatures():
             
            node_id = f["ID"]
            node_geom = f.geometry()
            total_found['nodes'] += 1
             
            for cnf in cn_layer.getFeatures():
                # Ignore any other types
                if cnf["Type"] != "CN":
                    continue

                cn_geom = cnf.geometry()
                if node_geom.buffer(0.1, 5).intersects(cn_geom):
                    total_found['snapped_cn'] += 1
                    if not node_id in details.keys():
                        details[node_id] = []
                    details[node_id].append(cnf)
                    continue
             
        cn_widths = {}
        for nodename, feats in details.items():
            line1 = feats[0].geometry().asMultiPolyline()
            line2 = feats[1].geometry().asMultiPolyline()
 
            distance = QgsDistanceArea()
            distance.setSourceCrs(cn_layer.crs(), self.project.transformContext())
            d = []
            d.append(distance.measureLine(line1[0][0], line2[0][0]))
            d.append(distance.measureLine(line1[0][0], line2[0][-1]))
            d.append(distance.measureLine(line1[0][-1], line2[0][0]))
            d.append(distance.measureLine(line1[0][-1], line2[0][-1]))
            maxval = max(d)
            cn_widths[nodename] = maxval

        return cn_widths, total_found
    
    def checkWidths(self, fmp_widths, cn_widths, dw_tol=5):
        """
        """
#         missing_2d_nodes = []
        self.results = []
        self.failed = {'fail': [], 'missing': []}
        cn_keys = cn_widths.keys()
        for id, details in fmp_widths.items():
            temp = {
                'id': id, 'type': details[1], '1d_width': details[0], 
                '2d_width': -99999, 'diff': -99999
            }
            if not id in cn_keys:
                self.failed['missing'].append(temp)
                self.results.append(temp)
            else:
                width_diff = abs(details[0] - cn_widths[id])
                output_diff = details[0] - cn_widths[id]
                temp['2d_width'] = cn_widths[id]
                temp['diff'] = output_diff
                if width_diff > dw_tol:
                    self.failed['fail'].append(temp)
                self.results.append(temp)
        return self.results, self.failed
    
    def writeResults(self, save_path):
        """
        """
        def formatWidth(value):
            return '{:.3f}'.format(value)

        if not self.results:
            raise OSError('Cannot find results. Please re-run the check first.')
        with open(save_path, 'w', newline='') as outfile:
            fieldnames = [
                'node', 'node type', 'fmp width', 'tuflow width', 'difference'
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in self.results:
                writer.writerow({
                    'node': '"' + r['id'] + '"', 'node type': r['type'],
                    'fmp width': formatWidth(r['1d_width']), 
                    'tuflow width': formatWidth(r['2d_width']), 'difference': formatWidth(r['diff'])
                })

    def writeFailed(self, save_path):
        """
        """
        def formatWidth(value):
            return '{:.3f}'.format(value)

        if not self.failed:
            raise OSError('Cannot find failed results. Please re-run the check first.')
        # No point writing out empty results
        if not self.failed['fail'] and not self.failed['missing']:
            return
        with open(save_path, 'w', newline='') as outfile:
            fieldnames = [
                'status', 'node', 'node type', 'fmp width', 'tuflow width', 'difference'
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for k, v in self.failed.items():
                for r in v:
                    writer.writerow({
                        'status': k, 'node': '"' + r['id'] + '"', 'node type': r['type'],
                        'fmp width': formatWidth(r['1d_width']), 
                        'tuflow width': formatWidth(r['2d_width']), 'difference': formatWidth(r['diff'])
                    })
