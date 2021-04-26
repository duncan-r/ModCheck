'''
@summary: Check FMP section properties

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 21st February 2021
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
from ship.utils.tools import openchannel


class CheckFmpSections(ti.ToolInterface):
    
#     def __init__(self, working_dir, dat_file, k_tol, dy_tol):
    def __init__(self):
        super().__init__()
#         self.working_dir = working_dir
#         self.dat_file = dat_file
#         self.k_tol = k_tol
#         self.dy_tol = dy_tol
    
#     def run_tool(self):
#         model = self.load_fmp_model(self.dat_file)
#         river_sections = model.unitsByType('river')
#         negative_k, n_zero = self.calculate_conveyance(river_sections)
#         bad_banks = self.checkBankLocations(river_sections)
#         return {
#             'negative_k': negative_k, 'n_zero': n_zero, 
#             'bad_banks': bad_banks
#         }
    
    def _getActiveSectionData(self, section):
        xvals = section.row_data['main'].dataObjectAsList(rdt.CHAINAGE)
        yvals = section.row_data['main'].dataObjectAsList(rdt.ELEVATION)
        nvals = section.row_data['main'].dataObjectAsList(rdt.ROUGHNESS)
        pvals = section.row_data['main'].dataObjectAsList(rdt.PANEL_MARKER)
        deactivation = section.row_data['main'].dataObjectAsList(rdt.DEACTIVATION)
        
        # Fetch only the active parts of the section
        # NOTE: Update SHIP to retrive only active part of section
        active_start = 0
        active_end = len(xvals)
        if 'LEFT' in deactivation:
            active_start = deactivation.index('LEFT')
        if 'RIGHT' in deactivation:
            active_end = deactivation.index('RIGHT') + 1
        active_x = xvals[active_start:active_end]
        active_y = yvals[active_start:active_end]
        active_n = nvals[active_start:active_end]
        active_p = pvals[active_start:active_end]
        return {
            'chainage': active_x, 'elevation': active_y, 'roughness': active_n, 
            'panel_marker': active_p
        }

    def calculateConveyance(self, river_sections, k_tol):
        """
        """
        negative_k = {}
        n_zero = []
        for r in river_sections:
            active = self._getActiveSectionData(r)
            active_x = active['chainage']
            active_y = active['elevation']
            active_n = active['roughness']
            active_p = active['panel_marker']
            
            try:
                conveyance, has_negative = openchannel.calcConveyance(
                    active_x, active_y, active_p, active_n, active_y,
                    interpolate_space=0, tolerance=k_tol
                )
            except ZeroDivisionError as err:
                n_zero.append(r.name)
                continue

            if has_negative:
                max_kx = 0
                max_kx_depth = 0
                for i, c in enumerate(conveyance):
                    if i > 0 and c[2]:
                        temp = conveyance[i][0] - conveyance[i-1][0]
                        if temp < max_kx:
                            max_kx = temp
                            max_kx_depth = c[1]
                negative_k[r.name] = {
                    'conveyance': conveyance, 'xvals': active_x, 'yvals': active_y,
                    'max_kx': max_kx, 'max_kx_depth': max_kx_depth, 'panels': active_p
                }
                
        return negative_k, n_zero

    def checkBankLocations(self, river_sections, dy_tol):
        """
        """
#         bank_tol = 0.1

        bad_banks = {}
        for r in river_sections:
            active = self._getActiveSectionData(r)
            
            # Get the minimum elevation value. This is the channel bed and should
            # be in the middle of the section somewhere
            miny = min(active['elevation'])
            miny_idx = active['elevation'].index(miny)
            
            maxy_left = max(active['elevation'][0:miny_idx])
            maxy_left_idx = active['elevation'][0:miny_idx].index(maxy_left)

            if miny_idx == len(active['elevation']) - 1:
                maxy_right = active['elevation'][-1]
                maxy_right_idx = len(active['elevation']) - 1
            else:
                maxy_right = max(active['elevation'][miny_idx:])
                maxy_right_idx = active['elevation'][miny_idx:].index(maxy_right)
                maxy_right_idx = miny_idx + maxy_right_idx

            # Check to see if there are any drops in elevation greater than the
            # given tolerance for the left and right banks
            left_drop = 0
            for i in range(maxy_left_idx, -1, -1):
                drop = maxy_left - active['elevation'][i]
#                 if (active['elevation'][i] - bank_tol) > maxy_left:
                if (drop > dy_tol) and (drop > left_drop):
                    left_drop = drop
                
            right_drop = 0
            for i in range(maxy_right_idx, len(active['elevation']), 1):
                drop = maxy_right - active['elevation'][i]
#                 if (active['elevation'][i] - bank_tol) > maxy_right:
                if (drop > dy_tol) and (drop > right_drop):
                    right_drop = drop
                
            if left_drop > 0 or right_drop > 0:
                bad_banks[r.name] = {
                    'max_left': maxy_left, 'max_right': maxy_right, 'max_left_idx': maxy_left_idx,
                    'max_right_idx': maxy_right_idx, 'left_drop': left_drop,
                    'right_drop': right_drop, 'xvals': active['chainage'], 
                    'yvals': active['elevation']
                }
        return bad_banks

    def loadRiverSections(self, fmp_path):
        file_loader = fl.FileLoader()
        try:
            model = file_loader.loadFile(fmp_path)
        except Exception as err:
            pass
        rivers = model.unitsByType('river')
        return rivers