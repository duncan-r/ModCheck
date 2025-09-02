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

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import QgsDistanceArea, QgsWkbTypes
from . import toolinterface as ti

from floodmodeller_api import DAT
# from ship.utils.fileloaders import fileloader as fl
# from ship.utils import utilfunctions as uf
# from ship.fmp.datunits import ROW_DATA_TYPES as rdt


# class SectionWidthCheck(ti.ToolInterface):
class SectionWidthCheck(QObject):
    """Compare FMP and TUFLOW section widths for parity, based on a tolerance.
    
    Calculates the active section widths for all river sections in an FMP model,
    as well as calculating the widths of interpolated sections, and compares
    them against the width within the 2D TUFLOW model representation. If the
    difference in width is greater than a given tolerance they will be 
    marked as failed.
    """
    status_signal = pyqtSignal(str)
    
    def __init__(self, project):
        super().__init__()
        self.project = project
        self.dat_path = None
        self.node_layer = None
        self.cn_layer = None
        self.results = []
        self.failed = {}
        
        self.cn_fields = [
            "type", "flags", "name", "f", "d", "td", "a", "b", 
        ]
        
    # def run_tool(self):
    #     super()
    #     self.results = []
    #     model = self.loadModel(self.dat_path)
    #     fmp_widths = self.fetchFmpWidths(model)
    #     cn_widths, missing_cn, total_found = self.fetchCnWidths()
    #     results, failed = self.check_widths(fmp_widths, cn_widths, missing_cn)
    #     return results, failed#, total_found
    
    def loadModel(self, dat_path):
        model = None
        try:
            model = DAT(dat_path)
        except Exception as err:
            raise Exception ("Problem loading FMP .dat file at:\n{}\n{}".format(dat_path, str(err)))
        return model
        
    def fetchFmpWidths(self, dat_path):
        """Calculate the active widths of all FMP river and interpolate sections.

        Find the width of all of the river type sections in the FMP model. The 
        widths of the interpolated sections are calculated by interpolating the
        difference between the two nearest river sections and the distance 
        between them.
        
        Args:
            dat_path(str): path to an FMP .dat file.
        
        Return:
            dict - {width, section type} where the width is a float and the
                section type is a str - either 'river' or 'interpolate' - and
                the key is the FMP section name.
                
        Note: Does not currently find FMP Replicate sections.
            This will be added soon.
        """

        def interpolate_widths(start_river, end_river, interpolates, end_width, dist_diff):
            """Interpolate widths between two cross sections (RIVER units).
            
            Calculates a linear relationship between surrounding river sections and the cross
            section widths. Applies that relationship to the interpolate sections, based on
            their distance between the sections, to derive interpolated section widths.
            No clever assumptions about difference in flow area, or suchlike, are considered
            here, which could make a difference in reality. It's a fairly good estimate of
            suitability though and should identify interpolate sections where the 2D channel
            is significantly different from the 1D width at that location.
            
            Args:
                start_river(Unit): the RIVER unit before the interpolates.
                end_river(Unit): the RIVER unit after the interpolates.
                interpolates(list): the intervening INTERPOLATE units.
                end_width(float): the width of the end_river unit.
                dist_diff(float): distance between start and end river units.
                
            Return:
                list - width of the INTERPOLATE units in the same order as 'interpolates'.
            """
            start_width = start_river[1]
            start_river = start_river[0]
            
            x1 = 0
            x2 = dist_diff
            y1 = start_width
            y2 = end_width
            c = y1
            m = ((y2 - y1) / x2)
            new_widths = {}
            dist_sum = start_river.dist_to_next
            for i in interpolates:
                width = m * dist_sum + c
                new_widths[i.name] = [width, i.unit]
                dist_sum += i.dist_to_next
            
            return new_widths
        
        model = self.loadModel(dat_path)
        
        # TODO: Add 'REPLICATE' to the checks
        unit_categories = ['RIVER', 'INTERPOLATE']
        widths = {}
        prev_unit = None
        prev_river = []
        interps = []
        interp_chainage = 0.0
        
        # Bit manky - we're hitting a protected variable that stores the units
        # I'm not quite sure how you find either a) the first river unit in the model
        # or b) the first unit in separate reaches. Maybe there's a better way?
        # TODO: Try not to circumvent the intended API if possible.
        #       If the above can be handled, the api does offer public next/prev methods.
        for unit in model._all_units:
            if not unit.unit in unit_categories:
                continue
            
            if unit.unit == 'RIVER':
                active_start = float(unit.active_data.head(1)['X'])
                active_end = float(unit.active_data.tail(1)['X'])
                active_width = active_end - active_start
                
                if prev_unit and prev_unit.unit == 'INTERPOLATE':
                    dist_diff = interp_chainage + unit.dist_to_next
                    interp_widths = interpolate_widths(prev_river, unit, interps, active_width, dist_diff)
                    widths = widths | interp_widths
                    interps = []
                        
                widths[unit.name] = [active_width, unit.unit]
                prev_river = [unit, active_width]
                prev_unit = unit
                interp_chainage = unit.dist_to_next
                
            elif unit.unit == 'INTERPOLATE':
                interps.append(unit)
                prev_unit = unit
                interp_chainage += unit.dist_to_next

        return widths
        
    def fetchCnWidths(self, node_layer, cn_layer):
        """Calculate the 2D TUFLOW widths for each node.
        
        Loops through all of the features in the node_layer and finds the CN
        lines that are snapped to the layer. Calculates the distance between
        the two furthest points on the two snapped CN lines to find the width.
        
        This algorithm is horribly inefficient at the moment and does way too
        much looping through layers multiple times. It's probably better to 
        try and loop the CN layer looking for snapped nodes, record the id
        alongside the cn feature and then create a final list. This would, 
        I think, mean only having to look the CN layer once. It will need to
        support multiple CN and nodes layers at some point, so the current
        setup is not really viable.
        
        Args:
            node_layer(VectorLayer): the TUFLOW 1d_nodes layer.
            cn_layer(VectorLayer): the TUFLOW 2d_bc_hx type layer containing the
                cn lines.
                
        Return:
            tuple - (dict, total found) where the dict contains the widths and
                the key is the 1D node name and total found is the total number
                of sections found in the CN layer.
        """
        self.node_layer = node_layer
        self.cn_layer = cn_layer
        
        # Check that we have the right kind of layer
        headers = [f.name().lower() for f in cn_layer.fields()]
        for i, field in enumerate(self.cn_fields):
            if not field in headers:
                raise AttributeError ("Selected CN layer is not a recognised 2b_bc_hx layer")

        total_found = {'nodes': 0, 'snapped_cn': 0}
        details = {}
        for f in node_layer.getFeatures():
            self.status_signal.emit(f"Finding snapped CN lines for feature: {f[0]}")
             
            node_id = f[0]
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
             
        # Calculate the max distance between CN line pair end points.
        cn_widths = {}
        single_cn = []
        self.status_signal.emit(f"Calculating widths...")
        for nodename, feats in details.items():
            if len(feats) < 2:
                single_cn.append(nodename)
                continue

            distance = QgsDistanceArea()
            distance.setSourceCrs(cn_layer.crs(), self.project.transformContext())
            d = []
            if not QgsWkbTypes.isSingleType(feats[0].geometry().wkbType()):
                line1 = feats[0].geometry().asMultiPolyline()
                line1_a = line1[0][0]
                line1_b = line1[0][-1]
            else:
                line1 = feats[0].geometry().asPolyline()
                line1_a = line1[0]
                line1_b = line1[-1]
            if not QgsWkbTypes.isSingleType(feats[1].geometry().wkbType()):
                line2 = feats[1].geometry().asMultiPolyline()
                line2_a = line2[0][0]
                line2_b = line2[0][-1]
            else:
                line2 = feats[1].geometry().asPolyline()
                line2_a = line2[0]
                line2_b = line2[-1]
 
            d.append(distance.measureLine(line1_a, line2_a))
            d.append(distance.measureLine(line1_a, line2_b))
            d.append(distance.measureLine(line1_b, line2_a))
            d.append(distance.measureLine(line1_b, line2_b))
            maxval = max(d)
            cn_widths[nodename] = maxval

        return cn_widths, single_cn, total_found
    
    def checkWidths(self, fmp_widths, cn_widths, single_cn, dw_tol=5):
        """Compare the FMP and TUFLOW (1D-2D) width values for each node.
        
        Compare the 1D (FMP) width to the 2D (TUFLOW) width. If the difference
        in widths is greater than the given width tolerance (dw_tol) the
        section will be added to the failed dict. The failed dict contains
        lists of 'fail' and 'missing' sections. Missing sections are those
        that were found in the FMP model, but are not in the TUFLOW model.
        
        Args:
            fmp_widths(dict): containing the section type and width for each
                FMP section with the section name as the key.
            cn_widths(dict): containing the TUFLOW (2D) widths with the node
                as the key.
            single_cn(list): containing the FMP nodes that only had a single
                CN line snapped to them (no width calculation possible).
            dw_tol(int): the tolerance, in metres, to determine whether the
                difference in width is classed as failing or not.
                
        Return:
            tuple - (all results, failed results) where 'all results' contains
                the 1D and 2D widths and difference for every FMP node. The
                'failed results' contains only those nodes that either had
                widths greater than the tolerance or could not be found in
                the TUFLOW layer.
        """
#         missing_2d_nodes = []
        self.results = []
        self.failed = {'fail': [], 'missing': [], 'single_cn': []}
        cn_keys = cn_widths.keys()
        for id, details in fmp_widths.items():
            temp = {
                'id': id, 'type': details[1], '1d_width': details[0], 
                '2d_width': -99999, 'diff': -99999
            }
            if not id in cn_keys:
                if id in single_cn:
                    self.failed['single_cn'].append(temp)
                else:
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
        """Export the results of the width compare to csv.
        
        Exports all FMP sections and widths, as well as the comparison to the
        TUFLOW representations where found.

        Args:
            save_path(str): the file path to save the csv file to.
            
        Except:
            OSError - if the file write fails.
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
        """Export the failed sections.
        
        Only export the sections that were either greater than tolerance or
        could not be found in the TUFLOW model files.
        
        Args:
            save_path(str): the file path to save the csv file to.

        Except:
            OSError - if the file write fails.
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
