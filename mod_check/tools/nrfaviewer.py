'''
@summary: View details for an NRFA station record

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 26th March 2021
@copyright: Ermeview Environmental Ltd
@license: LGPL v2
'''

import os
import csv
import json
import requests

from . import toolinterface as ti


class NrfaViewer():
    
    def __init__(self):
        super().__init__()
        self.NRFA_BASE_URL = 'https://nrfaapps.ceh.ac.uk/nrfa/ws/'
    
    def fetchStationData(self, station_id, fields='all'):
        url = self.NRFA_BASE_URL + 'station-info?'
        params = {
            'format': 'json-object',
#             'format': 'csv',
            'station': str(station_id),
            'fields': fields,
        }
        
        response = requests.get(url, params=params)
#         if response.status_code == 200:
        
        data = response.json()
        
        output = []
        for k, v in data['data'][0].items():
            output.append('{0:<50} {1}'.format(k + ':', v))
        return '\n'.join(output)
    
    def fetchAmaxData(self, station_id):
        url = self.NRFA_BASE_URL + 'time-series?'
        params = {
            'format': 'json-object',
            'station': str(station_id),
            'data-type': 'amax-flow',
        }
#         response = requests.get(url, params=params)
#         stage_data = None
        flow_data = None
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            flow_data = response.json()
        else:
            raise RuntimeError(
                'Failed to connect to server. Response failed with status code {0}'.format(
                    response.status_code
            ))

        params['data-type'] = 'amax-stage'
#         if response.status_code == 200:
#             stage_data = response.json()
#         else:
#             raise RuntimeError(
#                 'Failed to connect to server. Response failed with status code {0}'.format(
#                     response.status_code
#             ))
        
        series = []
        count = 0
        dateval = None
        for i, value in enumerate(flow_data['data-stream']):
            if i == 0 or i % 2 == 0:
                dateval = value
            else:
                series.append(
                    [value, dateval]
#                     [value, stage_data['data-stream'][i], dateval]
                )
            count += 1
#         return stage_data['data-type'], flow_data['data-type'], series
        return flow_data['data-type'], series
    
    def fetchPotData(self, station_id):
        url = self.NRFA_BASE_URL + 'time-series?'
        params = {
            'format': 'json-object',
            'station': str(station_id),
            'data-type': 'pot-flow',
        }
        response = requests.get(url, params=params)
#         stage_data = None
        flow_data = None
        if response.status_code == 200:
            flow_data = response.json()
        else:
            raise RuntimeError(
                'Failed to connect to server. Response failed with status code {0}'.format(
                    response.status_code
            ))
        
#         params['data-type'] = 'pot-stage'
#         response = requests.get(url, params=params)
#         if response.status_code == 200:
#             stage_data = response.json()
#         else:
#             raise RuntimeError(
#                 'Failed to connect to server. Response failed with status code {0}'.format(
#                     response.status_code
#             ))
        
        series = []
        count = 0
        dateval = None
        for i, value in enumerate(flow_data['data-stream']):
            if i == 0 or i % 2 == 0:
                dateval = value
            else:
                series.append({
                    'flow': value, 'datetime': dateval
                })
            count += 1
        return flow_data['data-type'], series
#         return flow_data['data-type'], stage_data['data-type'], series
    
    
    def fetchDailyFlowData(self, station_id):
        url = self.NRFA_BASE_URL + 'time-series?'
        params = {
            'format': 'json-object',
            'station': str(station_id),
            'data-type': 'gdf',
            'flags': 'true',
        }
        response = requests.get(url, params=params)
        flow_data = None
        if response.status_code == 200:
            flow_data = response.json()
        else:
            raise RuntimeError(
                'Failed to connect to server. Response failed with status code {0}'.format(
                    response.status_code
            ))
        
        series = {}
        count = 0
        dateval = None
        year = -1
        for i, value in enumerate(flow_data['data-stream']):
            if i == 0 or i % 2 == 0:
                dateval = value
                new_year = int(dateval[:4])
                if new_year > year:
                    year = new_year
                    series[year] = []
            else:
                if isinstance(value, list):
                    series[year].append({
                        'flow': value[0], 'date': dateval, 'flag': value[1]
                    })
                else:
                    series[year].append({
                        'flow': value, 'date': dateval, 'flag': ''
                    })
                    
            count += 1
        meta = flow_data['data-type']
        meta['interval'] = flow_data['interval']
        meta['timestamp'] = flow_data['timestamp']
        return meta, series, year


# class EAHydrologyViewer():
#     
#     def __init__(self):
#         self.EA_BASE_URL = "http://environment.data.gov.uk/hydrology/"
#     
#     def fetchEventData(self, station_id, min_date, max_date):
#         url = self.EA_BASE_URL + 'data/readings.json?'
#         params = {
#             'station.nrfaStationID': station_id,
#             'mineq-date': min_date,
#             'maxeq-date': max_date,
#         }
#         
#         response = requests.get(url, params=params)
# #         if response.status_code == 200:
#         data = response.json()
        
        