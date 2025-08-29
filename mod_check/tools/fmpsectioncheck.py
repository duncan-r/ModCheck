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

from floodmodeller_api import DAT
from floodmodeller_api.units import RIVER
from floodmodeller_api.units.conveyance import calculate_cross_section_conveyance_cached
from . import toolinterface as ti

# from ship.utils.fileloaders import fileloader as fl
# from ship.utils import utilfunctions as uf
# from ship.fmp.datunits import ROW_DATA_TYPES as rdt
# from ship.utils.tools import openchannel

class ConveyanceData():
    """Wrapper for the FM River section data for section checks.
    
    Precalculates required data on load to make access for graphing etc easier.
    Centralises the logic in one place for ease of update later.
    
    TODO:
        Very basic, needs refactoring.
    """
    
    def __init__(self):
        self.minx = 0
        self.maxx = 0
        self.miny = 0
        self.maxy = 0
        self.xs_x = None
        self.xs_y = None
        self.xs_active_x = None
        self.xs_active_y = None
        self.panels = []
        self.k_x = None
        self.k_y = None
        # self.conveyance = None
        self.active_k = None
        
    @property
    def panel_count(self):
        return len(self.panels)
    
    def addSection(self, section_data, active_k):

        self.active_k = {
            'x': active_k.values,
            'y': active_k.index,
        }
        self.minx = section_data.data['X'].min()
        self.maxx = section_data.data['X'].max()
        self.miny = section_data.data['Y'].min()
        self.maxy = section_data.data['Y'].max()
        
        self.xs_x = section_data.data['X']
        self.xs_y = section_data.data['Y']
        self.xs_active_x = section_data.active_data['X']
        self.xs_active_y = section_data.active_data['Y']

        for i, panel in enumerate(section_data.data['Marker']):
            if panel:
                self.panels.append({
                    'x': [section_data.data['X'][i], section_data.data['X'][i]],
                    'y': [self.miny, self.maxy]
                })
        
        # k = section_data.conveyance
        # self.conveyance = {
        #     'x': k.values,
        #     'y': k.index,
        # }
        

class CheckFmpSections(ti.ToolInterface):
    
    def __init__(self):
        super().__init__()
    
    def _getActiveSectionData(self, section):
        pass
        # xvals = section.row_data['main'].dataObjectAsList(rdt.CHAINAGE)
        # yvals = section.row_data['main'].dataObjectAsList(rdt.ELEVATION)
        # nvals = section.row_data['main'].dataObjectAsList(rdt.ROUGHNESS)
        # pvals = section.row_data['main'].dataObjectAsList(rdt.PANEL_MARKER)
        # deactivation = section.row_data['main'].dataObjectAsList(rdt.DEACTIVATION)
        #
        # # Fetch only the active parts of the section
        # # NOTE: Update SHIP to retrive only active part of section
        # active_start = 0
        # active_end = len(xvals)
        # if 'LEFT' in deactivation:
        #     active_start = deactivation.index('LEFT')
        # if 'RIGHT' in deactivation:
        #     active_end = deactivation.index('RIGHT') + 1
        # active_x = xvals[active_start:active_end]
        # active_y = yvals[active_start:active_end]
        # active_n = nvals[active_start:active_end]
        # active_p = pvals[active_start:active_end]
        # return {
        #     'chainage': active_x, 'elevation': active_y, 'roughness': active_n, 
        #     'panel_marker': active_p
        # }

    @classmethod
    def calculateActiveConveyance(cls, active_data):
        """Calculate conveyance for the active part of the section.
        
        FM API conveyance only seems to calculate from the full section? So the
        active only version is implemented here.
        
        Args:
            active_data(df): active component of the river section.
            
        Return:
            pandas.Series: containing the conveyance results
        """
        return calculate_cross_section_conveyance_cached(
            x=tuple(active_data.X.values),
            y=tuple(active_data.Y.values),
            n=tuple(active_data["Mannings n"].values),
            rpl=tuple(active_data.RPL.values),
            panel_markers=tuple(active_data.Panel.values),
        )

    def calculateConveyance(self, river_sections, k_tol):
        """
        """
        
        
        k_tol = -k_tol
        negative_k = {}
        # conveyance = {}
        for name, river in river_sections.items():
            # k = river.conveyance
            k = self.calculateActiveConveyance(river.active_data)

            # Duplicate k data, shift duplicate rows up by 1, find the difference,
            # and check the difference against the tolerance
            kf = k.to_frame()
            kf.columns = ['K']
            kf['K2'] = kf['K'].shift(-1)
            kf[:-1]
            kf['Kdiff'] = kf['K2'] - kf['K']
            has_diff = kf[kf['Kdiff'].lt(k_tol)]
            
            # If we have any matches the dataframe won't be empty.
            # Generate some conveyance data and add it to the match dict
            if not has_diff.empty:
                min_val = kf['Kdiff'].min()
                min_elev = kf['Kdiff'].idxmin()
                conv = ConveyanceData()
                conv.addSection(river, k)
                negative_k[name] = {
                    'max_kx': min_val, 'max_kx_depth': min_elev,
                    'section': conv,
                }

                
        return negative_k#, conveyance
        # return negative_k, n_zero

    def checkBankLocations(self, river_sections, dy_tol):
        """
        """
        pass

        # bad_banks = {}
        # for r in river_sections:
        #     active = self._getActiveSectionData(r)
        #
        #     # Get the minimum elevation value. This is the channel bed and should
        #     # be in the middle of the section somewhere
        #     miny = min(active['elevation'])
        #     miny_idx = active['elevation'].index(miny)
        #
        #     maxy_left = max(active['elevation'][0:miny_idx])
        #     maxy_left_idx = active['elevation'][0:miny_idx].index(maxy_left)
        #
        #     if miny_idx == len(active['elevation']) - 1:
        #         maxy_right = active['elevation'][-1]
        #         maxy_right_idx = len(active['elevation']) - 1
        #     else:
        #         maxy_right = max(active['elevation'][miny_idx:])
        #         maxy_right_idx = active['elevation'][miny_idx:].index(maxy_right)
        #         maxy_right_idx = miny_idx + maxy_right_idx
        #
        #     # Check to see if there are any drops in elevation greater than the
        #     # given tolerance for the left and right banks
        #     left_drop = 0
        #     for i in range(maxy_left_idx, -1, -1):
        #         drop = maxy_left - active['elevation'][i]
        #         if (drop > dy_tol) and (drop > left_drop):
        #             left_drop = drop
        #
        #     right_drop = 0
        #     for i in range(maxy_right_idx, len(active['elevation']), 1):
        #         drop = maxy_right - active['elevation'][i]
        #         if (drop > dy_tol) and (drop > right_drop):
        #             right_drop = drop
        #
        #     if left_drop > 0 or right_drop > 0:
        #         bad_banks[r.name] = {
        #             'max_left': maxy_left, 'max_right': maxy_right, 'max_left_idx': maxy_left_idx,
        #             'max_right_idx': maxy_right_idx, 'left_drop': left_drop,
        #             'right_drop': right_drop, 'xvals': active['chainage'], 
        #             'yvals': active['elevation']
        #         }
        # return bad_banks

    def loadRiverSections(self, dat_path):
        # try:
        model = DAT(dat_path)
        # except Exception as err:
        #     pass
        # rivers = model.unitsByType('river')
        sections = model.sections
        rivers = {}
        for k, s in sections.items():
            if s.unit == 'RIVER':
                rivers[k] = s

        return rivers