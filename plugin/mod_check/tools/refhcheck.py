
'''
@summary: Compare the setup of Refh units in model

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
from collections import OrderedDict

from . import toolinterface as ti

from ship.utils.fileloaders import fileloader as fl
from ship.utils import utilfunctions as uf
from ship.fmp.datunits import ROW_DATA_TYPES as rdt



class CompareFmpRefhUnits(ti.ToolInterface):
    
    def __init__(self, model_paths):
        super().__init__()
        self.model_paths = model_paths
    
    def run_tool(self):
        super()
        refh_data = self.fetchRefhData(self.model_paths)
        return refh_data
    
    def fetchRefhData(self, model_paths):
        """
        """
        consistency_vals = self._getConsistencyVals()
        self._resetListStatus()
        self._setupInputLists()
        
        failed_paths = []
        missing_refh = []
        self.csv_results = []
        output = []
        total_output = []
        for p in model_paths:
            
            # Convert from QtString to str
            p = str(p)

            if not os.path.exists(p):
                failed_paths.append(p)
            else: 
                try:
                    unit_data = self.loadHydrologicalData(p, self.item_status)
                    if unit_data == False:
                        missing_refh.append(p)
                    else:
                        dat_results, output = self.formatData(
                            unit_data, self.items, self.item_status, self.item_order, 
                            p, consistency_vals
                        )
                        dat_results.insert(0, p)
                        self.csv_results.append(dat_results)
                        total_output.append(output)
                        total_output.append('\n\n')
                    
                except IOError:
                    failed_paths.append(p)
                    
        return self.csv_results, total_output, failed_paths, missing_refh
    
    def loadHydrologicalData(self, file_path, list_status):
        """Loads a model file and extracts the requested hydrological data.
        """
        data = []
        
        try:
            loader = fl.FileLoader()
            units = loader.loadFile(file_path)
            if units == False: 
                raise IOError # Because of stupid tmac_tools error handling
        except IOError:
            raise IOError ("Cannot read file from:\n " + file_path)
            
        refh = units.unitsByType('refh')
        if not refh: return False
        
        for r in refh:
            temp = {}
            temp['type'] = r.UNIT_TYPE
            temp['name'] = r.head_data['section_label']
            for key, val in list_status.items():
                
                # False if not selected by user
#                 if val is False: continue
                if key == '#STORMDEPTH#':
                    storm = r.row_data['main'].dataObjectAsList(rdt.RAIN)
                    storm_sum = 0.0
                    for s in storm:
                        storm_sum += float(s)
                    temp[key] = storm_sum
                else:
                    temp[key] = r.head_data[key].value
            
            data.append(temp)
        return data
        
    def formatData(self, data, items, item_status, item_order, dat_path, consistency_vals):
        """Format the data for text display and csv outputs.
        
        Args:
            data(dict): the data loaded from the hydrological units.
            list_items(dict): the available data options and required status.
            dat_path(str): the filepath of the dat file.
        
        Return:
            tuple(list, list) - formatted for (csv, text display).
        """
        
        def checkSameVals(key, value):
            """
            """
            if key in consistency_vals:
                if consistency_vals[key] is None:
                    consistency_vals[key] = value
                else:
                    if not value == consistency_vals[key]:
                        value = '!!! ' + value + ' !!!'
            
            return value
                
        
        def alteredOutput(key, value):
            """
            """
            if key == 'Catchment->Urban':
                if value == '':
                    return 'No'
                else:
                    return 'Yes'
            if key == 'Urban ReFH->Draining Away->Sewer Type':
                if value == '':
                    return 'None'
                else:
                    return value
            if key == 'Urban ReFH->Draining Away->Sewer Loss':
                if value == '':
                    return 'None'
                else:
                    return value
                
        def truncateComment(value):
            short_text = value
            if len(short_text) > 38:
                short_text = short_text[:35] + '...'
            return short_text
            
        
        summary = [] #collections.OrderedDict()
        output = []
        found_keys = []
        altered_keys = ['Catchment->Urban', 'Urban ReFH->Draining Away->Sewer Type', 
                        'Urban ReFH->Draining Away->Sewer Loss']
        filename = os.path.split(dat_path)[1]
        
        # Keep names and type separate so they can be put at the top of the list
        unit_names = []
        unit_types = []
        
        output_header = 'Summary results from audit - %s\n' % (filename)
        output_header += '==========================\n'
        output_format = '%-40s'
        
        for d in data:
            # Add the type and name to the dict
            unit_names.append(d['name'])
            unit_types.append(d['type'])
            # Delete these entries or we'll get a key error in the chosen values
            del d['type']
            del d['name']
        
            # For the loaded data in the unit
            for key in item_order:

#                 if item_status[items[key]] == True:
                if not key in found_keys:
                    found_keys.append(key)
                    summary.append(key)
                    if key in altered_keys:
                        val = alteredOutput(key, str(d[items[key]]))
                        val = checkSameVals(key, val)
                        summary.append([val])
                    elif key == 'Catchment->Comment':
                        val = truncateComment(str(d[items[key]]))
                        summary.append([val])
                    else:
                        val = checkSameVals(key, str(d[items[key]]))
                        summary.append([val])
                else:
                    index = summary.index(key) + 1
                    if key in altered_keys:
                        val = alteredOutput(key, str(d[items[key]]))
                        val = checkSameVals(key, val)
                        summary[index].append(val)
                    elif key == 'Catchment->Comment':
                        val = truncateComment(str(d[items[key]]))
                        summary[index].append(val)
                    else:
                        val = checkSameVals(key, str(d[items[key]]))
                        summary[index].append(val)
                
                
        # Loop through the outputs to format them
        output_text = []
        output_csv = []
        for i in range(len(summary)):
            if i != 0 and i % 2 != 0:
                continue
            txt_line = '%-45s' % (summary[i]) 
            txt_add = [output_format % (val) for val in summary[i+1]]
            txt_line += ''.join(txt_add)
            csv_line = summary[i] + ',' + ','.join(summary[i+1])
            output_text.append(txt_line)
            csv_line = csv_line.replace('!!!', '')
            output_csv.append(csv_line)
            
        # Then format and and put name and type at the top of the list
        txt_line_name = '%-45s' % ('Unit Name') 
        txt_add_name = [output_format % (val) for val in unit_names]
        txt_line_name += ''.join(txt_add_name)
        txt_line_type = '%-45s' % ('Unit Type') 
        txt_add_type = [output_format % (val) for val in unit_types]
        txt_line_type += ''.join(txt_add_type)
        output_text.insert(0, txt_line_name) 
        output_text.insert(0, txt_line_type) 
        unit_types.insert(0, 'Unit Type')
        unit_names.insert(0, 'Unit Name')
        output_csv.insert(0, ','.join(unit_types))
        output_csv.insert(0, ','.join(unit_names))
        
        # Add some header text and join list into string
        output_text.insert(0, output_header)
        output_text = '\n'.join(output_text)
        
        return output_csv, output_text
    
    def exportResults(self):
        pass
    
    def _getConsistencyVals(self):
        """
        """
        vals = {}
        vals['Rainfall->Duration'] = None
        vals['Rainfall->Design Params->Return Period'] = None
        vals['Options->Scaling->Scaling Factor'] = None
        vals['Rainfall->Design Params->Storm Area'] = None
        vals['Rainfall->Design Params->Season'] = None
        vals['Rainfall->Time Step'] = None
        vals['Models->Routing Model->Tp0 Value'] = None
        vals['Models->Baseflow Model->BF0 Value'] = None
        vals['Models->Loss Model->CMAX DCF'] = None
        return vals
    
    def _resetListStatus(self):
        """Resets the list status dictionary to defaults."""
        
        self.item_status = {
            'comment' : False,
            'easting' : False,
            'northing' : False,
            'catchment_area' : False,
            'urbext' : False,
            'saar' : False,
            'propwet' : False,
            'dplbar' : False,
            'bfihost' : False,
            'dpsbar' : False,
            'c' : False,
            'd1' : False,
            'd2' : False,
            'd3' : False,
            'e' : False,
            'f' : False,
            'urban' : False,
            'rainfall_comment' : False,
            'storm_duration' : False,
            'time_step' : False,
            'hydrograph_mode' : False,
            'return_period' : False,
            'season' : False,
            'storm_area' : False,
            'scf_flag' : False,
            'scf' : False,
            'arf_flag' : False,
            'arf' : False,
            '#STORMDEPTH#' : False,
            'models_comment' : False,
            'cmax_flag' : False,
            'cm_dcf' : False,
            'cmax' : False,
            'cini_flag' : False,
            'cini' : False,
            'alpha_flag' : False,
            'alpha' : False,
            'tp_flag' : False,
            'tp_dcf' : False,
            'tp0' : False,
            'up_flag' : False,
            'up' : False,
            'uk_flag' : False,
            'uk' : False,
            'bl_flag' : False,
            'bl_dcf' : False,
            'bl' : False,
            'br_flag' : False,
            'br_dcf' : False,
            'br' : False,
            'bf0_flag' : False,
            'bf0' : False,
            'subarea_1' : False,
            'dplbar_1' : False,
            'suburbext_1' : False,
            'calibration_1' : False,
            'subarea_2' : False,
            'dplbar_2' : False,
            'suburbext_2' : False,
            'calibration_2' : False,
            'sewer_rp_2' : False,
            'sewer_depth_2' : False,
            'sewer_lossvolume_2' : False,
            'subarea_3' : False,
            'dplbar_3' : False,
            'suburbext_3' : False,
            'calibration_3' : False,
            'hydrograph_scaling' : False,
            'min_flow' : False,
            'time_delay' : False,
            #'hydrograph_scaled' : False,
            'sc_flag' : False,
            'scale_factor' : False,
            'hydrograph_mode' : False,
            'published_report' : False
        }
    
    def _setupInputLists(self):
        self.item_order = []
        self.item_order.append('Catchment->Comment')
        self.item_order.append('Catchment->Descriptors->Easting')
        self.item_order.append('Catchment->Descriptors->Northing')
        self.item_order.append('Catchment->Descriptors->Area')
        self.item_order.append('Catchment->Descriptors->URBEXT')
        self.item_order.append('Catchment->Descriptors->SAAR')
        self.item_order.append('Catchment->Descriptors->PROPWET')
        self.item_order.append('Catchment->Descriptors->DPLBAR')
        self.item_order.append('Catchment->Descriptors->BFIHOST')
        self.item_order.append('Catchment->Descriptors->DPSBAR')
        self.item_order.append('Catchment->Rainfall DDF->c')
        self.item_order.append('Catchment->Rainfall DDF->d1')
        self.item_order.append('Catchment->Rainfall DDF->d2')
        self.item_order.append('Catchment->Rainfall DDF->d3')
        self.item_order.append('Catchment->Rainfall DDF->e')
        self.item_order.append('Catchment->Rainfall DDF->f')
        self.item_order.append('Catchment->Urban')
        self.item_order.append('Rainfall->Comment')
        self.item_order.append('Rainfall->Duration')
        self.item_order.append('Rainfall->Time Step')
        self.item_order.append('Rainfall->Des/Obs')
        self.item_order.append('Rainfall->Design Params->Return Period')
        self.item_order.append('Rainfall->Design Params->Season')
        self.item_order.append('Rainfall->Design Params->Storm Area')
        self.item_order.append('Rainfall->Design Params->SCF Method')
        self.item_order.append('Rainfall->Design Params->SCF')
        self.item_order.append('Rainfall->Design Params->ARF Method')
        self.item_order.append('Rainfall->Design Params->ARF')
        self.item_order.append('Rainfall->Obs Evt Depth')
        self.item_order.append('Models->Comment')
        self.item_order.append('Models->Loss Model->CMAX Method')
        self.item_order.append('Models->Loss Model->CMAX DCF')
        self.item_order.append('Models->Loss Model->CMAX Value')
        self.item_order.append('Models->Loss Model->Cini Method')
        self.item_order.append('Models->Loss Model->Cini Value')
        self.item_order.append('Models->Loss Model->Alpha Method')
        self.item_order.append('Models->Loss Model->Alpha Value')
        self.item_order.append('Models->Routing Model->Tp Method')
        self.item_order.append('Models->Routing Model->Tp DCF')
        self.item_order.append('Models->Routing Model->Tp0 Value')
        self.item_order.append('Models->Routing Model->Up Method')
        self.item_order.append('Models->Routing Model->Up Value')
        self.item_order.append('Models->Routing Model->Uk Method')
        self.item_order.append('Models->Routing Model->Uk Value')
        self.item_order.append('Models->Baseflow Model->BL Method')
        self.item_order.append('Models->Baseflow Model->BL DCF')
        self.item_order.append('Models->Baseflow Model->BL Value')
        self.item_order.append('Models->Baseflow Model->BR Method')
        self.item_order.append('Models->Baseflow Model->BR DCF')
        self.item_order.append('Models->Baseflow Model->BR Value')
        self.item_order.append('Models->Baseflow Model->BF0 Method')
        self.item_order.append('Models->Baseflow Model->BF0 Value')
        self.item_order.append('Urban ReFH->Undeveloped->Area')
        self.item_order.append('Urban ReFH->Undeveloped->DPLBAR')
        self.item_order.append('Urban ReFH->Undeveloped->URBEXT')
        self.item_order.append('Urban ReFH->Undeveloped->Calibration')
        self.item_order.append('Urban ReFH->Draining Away->Area')
        self.item_order.append('Urban ReFH->Draining Away->DPLBAR')
        self.item_order.append('Urban ReFH->Draining Away->URBEXT')
        self.item_order.append('Urban ReFH->Draining Away->Calibration')
        self.item_order.append('Urban ReFH->Draining Away->Sewer Type')
        self.item_order.append('Urban ReFH->Draining Away->Sewer Capacity')
        self.item_order.append('Urban ReFH->Draining Away->Sewer Loss')
        self.item_order.append('Urban ReFH->Draining Towards->Area')
        self.item_order.append('Urban ReFH->Draining Towards->DPLBAR')
        self.item_order.append('Urban ReFH->Draining Towards->URBEXT')
        self.item_order.append('Urban ReFH->Draining Towards->Calibration')
        self.item_order.append('Options->Sim Type')
        self.item_order.append('Options->Min Flow')
        self.item_order.append('Options->Time Delay')
        #self.item_order.append('Options->Scaling->Hydrograph Scaled')
        self.item_order.append('Options->Scaling->Scaling Method')
        self.item_order.append('Options->Scaling->Scaling Value')
        self.item_order.append('Options->Boundary Type')
        self.item_order.append('Options->Calculation Source')

        self.items = OrderedDict()
        self.items['Catchment->Comment'] = 'comment'
        self.items['Catchment->Descriptors->Easting'] = 'easting'
        self.items['Catchment->Descriptors->Northing'] = 'northing'
        self.items['Catchment->Descriptors->Area'] = 'catchment_area'
        self.items['Catchment->Descriptors->URBEXT'] = 'urbext'
        self.items['Catchment->Descriptors->SAAR'] = 'saar'
        self.items['Catchment->Descriptors->PROPWET'] = 'propwet'
        self.items['Catchment->Descriptors->DPLBAR'] = 'dplbar'
        self.items['Catchment->Descriptors->BFIHOST'] = 'bfihost'
        self.items['Catchment->Descriptors->DPSBAR'] = 'dpsbar'
        self.items['Catchment->Rainfall DDF->c'] = 'c'
        self.items['Catchment->Rainfall DDF->d1'] = 'd1'
        self.items['Catchment->Rainfall DDF->d2'] = 'd2'
        self.items['Catchment->Rainfall DDF->d3'] = 'd3'
        self.items['Catchment->Rainfall DDF->e'] = 'e'
        self.items['Catchment->Rainfall DDF->f'] = 'f'
        self.items['Catchment->Urban'] = 'urban'
        self.items['Rainfall->Comment'] = 'rainfall_comment'
        self.items['Rainfall->Duration'] = 'storm_duration'
        self.items['Rainfall->Time Step'] = 'time_step'
        self.items['Rainfall->Des/Obs'] = 'hydrograph_mode'
        self.items['Rainfall->Design Params->Return Period'] = 'return_period'
        self.items['Rainfall->Design Params->Season'] = 'season'
        self.items['Rainfall->Design Params->Storm Area'] = 'storm_area'
        self.items['Rainfall->Design Params->SCF Method'] = 'scf_flag'
        self.items['Rainfall->Design Params->SCF'] = 'scf'
        self.items['Rainfall->Design Params->ARF Method'] = 'arf_flag'
        self.items['Rainfall->Design Params->ARF'] = 'arf'
        self.items['Rainfall->Obs Evt Depth'] = '#STORMDEPTH#'
        self.items['Models->Comment'] = 'models_comment'
        self.items['Models->Loss Model->CMAX Method'] = 'cmax_flag'
        self.items['Models->Loss Model->CMAX DCF'] = 'cm_dcf'
        self.items['Models->Loss Model->CMAX Value'] = 'cmax'
        self.items['Models->Loss Model->Cini Method'] = 'cini_flag'
        self.items['Models->Loss Model->Cini Value'] = 'cini'
        self.items['Models->Loss Model->Alpha Method'] = 'alpha_flag'
        self.items['Models->Loss Model->Alpha Value'] = 'alpha'
        self.items['Models->Routing Model->Tp Method'] = 'tp_flag'
        self.items['Models->Routing Model->Tp DCF'] = 'tp_dcf'
        self.items['Models->Routing Model->Tp0 Value'] = 'tp0'
        self.items['Models->Routing Model->Up Method'] = 'up_flag'
        self.items['Models->Routing Model->Up Value'] = 'up'
        self.items['Models->Routing Model->Uk Method'] = 'uk_flag'
        self.items['Models->Routing Model->Uk Value'] = 'uk'
        self.items['Models->Baseflow Model->BL Method'] = 'bl_flag'
        self.items['Models->Baseflow Model->BL DCF'] = 'bl_dcf'
        self.items['Models->Baseflow Model->BL Value'] = 'bl'
        self.items['Models->Baseflow Model->BR Method'] = 'br_flag'
        self.items['Models->Baseflow Model->BR DCF'] = 'br_dcf'
        self.items['Models->Baseflow Model->BR Value'] = 'br'
        self.items['Models->Baseflow Model->BF0 Method'] = 'bf0_flag'
        self.items['Models->Baseflow Model->BF0 Value'] = 'bf0'
        self.items['Urban ReFH->Undeveloped->Area'] = 'subarea_1'
        self.items['Urban ReFH->Undeveloped->DPLBAR'] = 'dplbar_1'
        self.items['Urban ReFH->Undeveloped->URBEXT'] = 'suburbext_1'
        self.items['Urban ReFH->Undeveloped->Calibration'] = 'calibration_1'
        self.items['Urban ReFH->Draining Away->Area'] = 'subarea_2'
        self.items['Urban ReFH->Draining Away->DPLBAR'] = 'dplbar_2'
        self.items['Urban ReFH->Draining Away->URBEXT'] = 'suburbext_2'
        self.items['Urban ReFH->Draining Away->Calibration'] = 'calibration_2'
        self.items['Urban ReFH->Draining Away->Sewer Type'] = 'sewer_rp_2'
        self.items['Urban ReFH->Draining Away->Sewer Capacity'] = 'sewer_depth_2'
        self.items['Urban ReFH->Draining Away->Sewer Loss'] = 'sewer_lossvolume_2'
        self.items['Urban ReFH->Draining Towards->Area'] = 'subarea_3'
        self.items['Urban ReFH->Draining Towards->DPLBAR'] = 'dplbar_3'
        self.items['Urban ReFH->Draining Towards->URBEXT'] = 'suburbext_3'
        self.items['Urban ReFH->Draining Towards->Calibration'] = 'calibration_3'
        self.items['Options->Sim Type'] = 'hydrograph_scaling'
        self.items['Options->Min Flow'] = 'min_flow'
        self.items['Options->Time Delay'] = 'time_delay'
        #self.items['Options->Scaling->Hydrograph Scaled'] = 'hydrograph_scaled'
        self.items['Options->Scaling->Scaling Method'] = 'sc_flag'
        self.items['Options->Scaling->Scaling Value'] = 'scale_factor'
        self.items['Options->Boundary Type'] = 'hydrograph_mode'
        self.items['Options->Calculation Source'] = 'published_report'