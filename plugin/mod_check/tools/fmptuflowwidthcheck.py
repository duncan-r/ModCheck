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


class FmpTuflowSectionWidthCheck(ti.ToolInterface):
    
    def __init__(self, project, working_dir, dat_path, node_layer, cn_layer, dw_tol):
        super().__init__()
        self.project = project
        self.working_dir = working_dir
        self.dat_path = dat_path
        self.node_layer = node_layer
        self.cn_layer = cn_layer
        self.dw_tol = dw_tol
        self.results = []
        
        self.cn_fields = [
            "Type", "Flags", "Name", "f", "d", "td", "a", "b", 
        ]
        
    def run_tool(self):
        super()
        self.results = []
        fmp_widths = self.fetch_fmp_widths(self.dat_path)
        cn_widths, total_found = self.fetch_cn_widths()
        return self.check_widths(fmp_widths, cn_widths)
        
    def fetch_fmp_widths(self, fmp_path):
        file_loader = fl.FileLoader()
        try:
            model = file_loader.loadFile(fmp_path)
        except e:
            raise e ("Problem loading FMP .dat file at:\n{}".format(fmp_path))
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
        
    def fetch_cn_widths(self):
        
        # Check that we have the right kind of layer
        headers = [f.name() for f in self.cn_layer.fields()]
        for i, field in enumerate(self.cn_fields):
            if not field in headers:
                raise AttributeError ("Selected CN layer is not a recognised 2b_bc_hx layer")

        total_found = {'nodes': 0, 'snapped_cn': 0}
        details = {}
        for f in self.node_layer.getFeatures():
             
            node_id = f["ID"]
            node_geom = f.geometry()
            total_found['nodes'] += 1
             
            for cnf in self.cn_layer.getFeatures():
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
            distance.setSourceCrs(self.cn_layer.crs(), self.project.transformContext())
            d = []
            d.append(distance.measureLine(line1[0][0], line2[0][0]))
            d.append(distance.measureLine(line1[0][0], line2[0][-1]))
            d.append(distance.measureLine(line1[0][-1], line2[0][0]))
            d.append(distance.measureLine(line1[0][-1], line2[0][-1]))
            maxval = max(d)
            cn_widths[nodename] = maxval

        return cn_widths, total_found
    
    def check_widths(self, fmp_widths, cn_widths):
        """
        """
        missing_2d_nodes = []
        failed = []
        cn_keys = cn_widths.keys()
        for id, details in fmp_widths.items():
            if not id in cn_keys:
                missing_2d_nodes.append(id)
            else:
                width_diff = abs(details[0] - cn_widths[id])
                if width_diff > self.dw_tol:
                    failed.append('Node {}:  difference = {:.2f}m'.format(id, width_diff))
                self.results.append({
                    'id': id, 'type': details[1], '1d_width': details[0], 
                    '2d_width': cn_widths[id], 'width_diff': width_diff
                })
        return missing_2d_nodes, failed
    
    def write_results(self):
        """
        """
        outpath = os.path.join(self.working_dir, 'fmptuflow_widthcompare.csv')
        with open(outpath, 'w', newline='') as outfile:
            fieldnames = [
                'node', 'node type', 'fmp width', 'tuflow width', 'difference'
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for r in self.results:
                writer.writerow({
                    'node': '\'' + r['id'], 'node type': r['type'],
                    'fmp width': r['1d_width'], 'tuflow width': r['2d_width'],
                    'difference': '{:.2f}'.format(r['width_diff'])
                })
        return outpath
