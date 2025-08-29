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

class ProblemData():
    """Wrapper for the FM River section data for section checks.
    
    Precalculates required data on load to make access for graphing etc easier.
    Centralises the logic in one place for ease of update later.
    
    TODO:
        Very basic, needs refactoring.
    """
    
    def __init__(self):
        # Section
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
        
        # Conveyance
        # self.conveyance = None
        self.active_k = None
        self.max_kx = 0
        self.max_kx_depth = 0

        # Banks
        self.bad_banks = None
        
    @property
    def panel_count(self):
        return len(self.panels)
    
    def addSection(self, section_data):

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
                
    def addConveyance(self, conveyance_data, max_kx, max_kx_depth):
        self.active_k = {
            'x': conveyance_data.values,
            'y': conveyance_data.index,
        }
        self.max_kx = max_kx
        self.max_kx_depth = max_kx_depth
        
    def addBanks(self, bank_data):
        self.bad_banks = bank_data
        

class CheckFmpSections(ti.ToolInterface):
    
    def __init__(self):
        super().__init__()
    
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
        
    def findProblemSections(self, river_sections, **kwargs):
        problems = self.calculateConveyance(river_sections, **kwargs)
        problems = self.checkBankLocations(river_sections, problems, **kwargs)
        return problems

    def calculateConveyance(self, river_sections, k_tol=10.0, **kwargs):
        """
        """
        k_tol = -k_tol
        issues = {}
        for name, river in river_sections.items():
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
                problem = ProblemData()
                problem.addSection(river)
                problem.addConveyance(k, min_val, min_elev)
                issues[name] = problem
                
        return issues

    def checkBankLocations(self, river_sections, issue_sections, dy_tol=0.1, **kwargs):
        """
        """
        # bad_banks = {}
        for name, river in river_sections.items():
            # Index references are not updated for the new 'active' part of the df
            # Find the indexes so we can use a relative lookup
            # This feels hacky, assume there's a better way?
            xs_start = river.active_data['Y'][:1].index[0]
            xs_end = river.active_data['Y'][-1:].index[0]
            
            # Get max l/r banks and min bed from active section
            min_index = river.active_data.loc[xs_start:xs_end]['Y'].idxmin()
            max_index_l = river.active_data.loc[xs_start:min_index]['Y'].idxmax()
            max_index_r = river.active_data.loc[min_index:xs_end]['Y'].idxmax()
            
            fail_l = fail_r = False
            drop_l = -9999
            drop_r = -9999
            min_l = 9999
            min_r = 9999
            max_l = 9999
            max_r = 9999
            # Left section lower than banktop check
            if max_index_l != xs_start:
                max_l = river.active_data.loc[xs_start:max_index_l]['Y'].max()
                min_l = river.active_data.loc[xs_start:max_index_l]['Y'].min()
                drop_l = max_l - min_l
                if drop_l > dy_tol:
                    fail_l = True
            
            # Right section lower than banktop check
            if max_index_r != xs_end:
                max_r = river.active_data.loc[max_index_r:xs_end]['Y'].max()
                min_r = river.active_data.loc[max_index_r:xs_end]['Y'].min()
                drop_r = max_r - min_r
                if drop_r > dy_tol:
                    fail_r = True
            
            if fail_l or fail_r:
                bad_banks = {
                    'fail_left': fail_l, 'fail_right': fail_r,
                    'max_left': max_l, 'max_right': max_r, 'max_left_idx': max_index_l, 
                    'max_right_idx': max_index_r, 'min_left': min_l, 'min_right': min_r,
                    'drop_left': drop_l, 'drop_right': drop_r,
                    'xs_start': xs_start, 'xs_end': xs_end,
                }
                if not name in issue_sections.keys():
                    problem = ProblemData()
                    problem.addSection(river)
                    issue_sections[name] = problem
                issue_sections[name].addBanks(bad_banks)

        return issue_sections

    def loadRiverSections(self, dat_path):
        model = None
        try:
            model = DAT(dat_path)
        except Exception as err:
            pass
        rivers = model.unitsByType('river')
        sections = model.sections
        rivers = {}
        for k, s in sections.items():
            if s.unit == 'RIVER':
                rivers[k] = s
        return rivers