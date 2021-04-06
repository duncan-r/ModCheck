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
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from qgis.core import *

from . import toolinterface as ti


class NrfaViewer():
    """Retrieve NFRA station locations and data.
    
    Contains functions for identifying nearby NRFA stations and calling
    the NRFA API to obtain station information and AMAX, POT and daily
    flows data.
    """
    
    def __init__(self, project, iface):
        super().__init__()
        self.NRFA_BASE_URL = 'https://nrfaapps.ceh.ac.uk/nrfa/ws/'
        self.project = project
        self.iface = iface
        self.stations = {}
        self.station_points = None
        self.cur_station = None
        self.cache = {
            'full_info': [-1, ''],
            'amax': [-1, None, None],
            'pot': [-1, None, None],
            'daily_flows': [-1, None, None],
        }
        
    @property
    def amax_series(self):
        self._checkCacheSeriesData('amax')
        return self.cache['amax'][1]

    @property
    def pot_series(self):
        self._checkCacheSeriesData('pot')
        return self.cache['pot'][1]

    @property
    def daily_flows_series(self):
        self._checkCacheSeriesData('daily_flows')
        return self.cache['daily_flows'][1]
    
    def _checkCacheSeriesData(self, cache_key):
        if self.cache[cache_key][0] != self.cur_station['id'] or self.cache[cache_key][1] is None:
            raise ValueError('Please load station data first')
        
    def fetchStations(self, nrfa_layer, search_radius):
        """Find all NRFA station within a given search radius.
        
        Identifies all NRFA gauging stations in the supplied nrfa_layer that are
        within the given search radius of the map canvas center.
        
        Creates a memory layer of the stations within the search radius containing
        the IDs and station names, labels the station IDs and adds the memory
        layer to the the the project.
        
        Args:
            nrfa_layer(VectorLayer): pre-compiled point layer containing the location
                and summary details of NRFA stations in the UK.
            search_radius(int): Number of kilometres to search for stations within.
            
        Return:
            station_ids(str): A list of the "(ID) Name" of all of the stations 
                identified within the search radius.
        """
        canvas_centre = self.iface.mapCanvas().center()
        distance = QgsDistanceArea()
        distance.setSourceCrs(nrfa_layer.crs(), self.project.transformContext())
        
        # Generate a list of all points in the nrfa_layer that are within the
        # search radius
        self.stations = {}
        self.station_points = None
        station_ids = []
        for point in nrfa_layer.getFeatures():
            p = point.geometry()
            name = point['name']
            id = point['id']
            p.convertToSingleType()
            if distance.measureLine(p.asPoint(), canvas_centre) <= search_radius:
                self.stations[id] = {'layer': point, 'name': name, 'id': id}
                s = '({0}) {1}'.format(id, name)
                station_ids.append(s)
                
        if len(station_ids) > 0:
#             self.stationInfoGroupbox.setEnabled(True)
            # Remove any existing temp stations scratch layer
            existing_layers = self.project.instance().mapLayersByName("NRFA Stations Selection")
            if existing_layers:
                self.project.instance().removeMapLayers([existing_layers[0].id()])
                
            # Create new points layer with the selected stations
            self.station_points = QgsVectorLayer("Point", "NRFA Stations Selection", "memory")
            self.station_points.setCrs(nrfa_layer.crs())
            provider = self.station_points.dataProvider()
            provider.addAttributes([
                QgsField("ID", QVariant.Int),
                QgsField("Name", QVariant.String),
            ])
            self.station_points.updateFields()
            for k, v in self.stations.items():
                feat = QgsFeature()
                feat.setGeometry(v['layer'].geometry())
                feat.setAttributes([k, v['name']])
                provider.addFeature(feat)
            self.station_points.updateExtents()
            
            # Add stations id labels to points
            text_format = QgsTextFormat()
            label = QgsPalLayerSettings()
            label.fieldName = 'ID'
            label.enabled = True
            label.setFormat(text_format)
            labeler = QgsVectorLayerSimpleLabeling(label)
            self.station_points.setLabelsEnabled(True)
            self.station_points.setLabeling(labeler)
            
            self.project.instance().addMapLayer(self.station_points)

        return station_ids 
    
    def fetchStationSummary(self, station_id):
        """Obtain basic summary info for a given NRFA station.
        
        Generates a list of formatted text for display for a particular NRFA
        station. Selected the station in the self.stations memory layers and 
        zooms the map window to that station.
        
        Note: Calling this function will set the self.cur_station value in this class.
            This is required before other functionality is used.
        
        Args:
            station_id(int): the NRFA ID of the station.
            
        Return:
            output(list): list of formatted text items summaries the station details.
                Will return an empty list if the station_id is not found in the
                self.station_points memory layer.
        """
        stn_type_link = 'https://nrfa.ceh.ac.uk/hydrometric-information'
        self.cur_station = self.stations[station_id]
        self.station_points.removeSelection()
#         selected_station = None
        ouput = []
        for f in self.station_points.getFeatures():
            id = f['ID']
            if id == station_id:
                self.station_points.select(f.id())
                selected_station = self.stations[self.cur_station['id']]['layer']
                box = self.station_points.boundingBoxOfSelected()
                self.iface.mapCanvas().setExtent(box)
                self.iface.mapCanvas().refresh()
                output = [
                    '{0:<20} {1}'.format('ID:', self.cur_station['id']),
                    '{0:<20} {1}'.format('Name:', selected_station['name']),
                    '{0:<20} {1}'.format('River:', selected_station['river']),
                    '{0:<20} {1}'.format('Location:', selected_station['location']),
                    '{0:<20} {1} (details - {2})'.format('Station Type:', selected_station['stn-type'], stn_type_link),
                    '{0:<20} {1}'.format('BNG:', selected_station['BNG']),
                    '{0:<20} {1}'.format('Easting:', selected_station['easting']),
                    '{0:<20} {1}'.format('Northing:', selected_station['northing']),
                    '{0:<20} {1} km2'.format('Catchment Area:', selected_station['catch-area']),
                    '{0:<20} {1} mAOD'.format('Station Level:', selected_station['stn-level']),
                ]
                break
        return output
    
    def fetchStationData(self, fields='all'):
        """Fetch all metadata for a station from the NRFA API.
        
        Calls the NRFA API 'station-info' url to obtain all of the metadata for
        the self.cur_station ID.
        
        Args:
            fields='all': fields parameter for the NRFA API call. The default 'all'
                value will return all of the metadata for the station.
                
        Return:
            list - containing formatted text for display for each value in the
                station metadata.
                
        Except:
            ConnectionError - If the call to the NRFA API fails (response code != 200).
            
        Note: the self.cur_station value must be set before calling this function.
            This is done by calling fetchStationSummary() with the station ID.
        """
        station_id = self.cur_station['id']
        # If it's already been fetched return the same results
        if self.cache['full_info'][0] == station_id and self.cache['full_info'][1]:
            return self.cache['full_info'][1]

        url = self.NRFA_BASE_URL + 'station-info?'
        params = {
            'format': 'json-object',
            'station': str(station_id),
            'fields': fields,
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise ConnectionError (
                'Failed to connect to NRFA API. Status code: {0}'.format(response.status_code)
            )
        data = response.json()
        
        output = []
        for k, v in data['data'][0].items():
            output.append('{0:<50} {1}'.format(k + ':', v))
        output = '\n'.join(output)
        self.cache['full_info'][0] = station_id
        self.cache['full_info'][1] = output
        return output
    
    def fetchAmaxData(self):
        """Fetch the AMAX data for a station from the NRFA API.
        
        Calls the NRFA API 'time-series' url to obtain all of the AMAX (Annual
        Maximums) data for the self.cur_station.
        
        Return:
            tuple - containing (metadata, series) where metadata is the AMAX summary
                data and series is a list of dicts containing {flow, str_datetime}.
                
        Except:
            ConnectionError - If the call to the NRFA API fails (response code != 200).
            
        Note: the self.cur_station value must be set before calling this function.
            This is done by calling fetchStationSummary() with the station ID.
        """
        station_id = self.cur_station['id']
        if (
            self.cache['amax'][0] == station_id and 
            self.cache['amax'][1] is not None and
            self.cache['amax'][2] is not None
            ):
            return self.cache['amax'][2], self.cache['amax'][1]

        url = self.NRFA_BASE_URL + 'time-series?'
        params = {
            'format': 'json-object',
            'station': str(station_id),
            'data-type': 'amax-flow',
        }

        flow_data = None
        response = requests.get(url, params=params)
        if response.status_code == 200:
            flow_data = response.json()
        else:
            raise ConnectionError(
                'Failed to connect to NRFA API. Status code: {0}'.format(response.status_code)
            )
        
        series = []
        count = 0
        dateval = None
        for i, value in enumerate(flow_data['data-stream']):
            if i == 0 or i % 2 == 0:
                dateval = value
            else:
                series.append({'flow': value, 'datetime': dateval})
            count += 1
            
        metadata = [
            '{0:<40} {1:<40}'.format('ID', 'amax-flow'),
            '{0:<40} {1:<40}'.format('Name', flow_data['data-type']['name']),
            '{0:<40} {1:<40}'.format('Parameter', flow_data['data-type']['parameter']),
            '{0:<40} {1:<40}'.format('Units', flow_data['data-type']['units']),
            '{0:<40} {1:<40}'.format('Measurement type', flow_data['data-type']['measurement-type']),
            '{0:<40} {1:<40}'.format('Period', flow_data['data-type']['period']),
        ]
        if not series:
            metadata.insert(
                0, '{0:<40}'.format('NO AMAX DATA FOUND FOR STATION')
            )
        self.cache['amax'][0] = station_id
        self.cache['amax'][1] = series
        self.cache['amax'][2] = metadata
        return metadata, series
    
    def fetchPotData(self):
        """Fetch the POT data for a station from the NRFA API.
        
        Calls the NRFA API 'time-series' url to obtain all of the POT (Peaks
        Over Threshold) data for the self.cur_station.
        
        Return:
            tuple - containing (metadata, series) where metadata is the POT summary
                data and series is a list of dicts containing {flow, str_datetime}.
                
        Except:
            ConnectionError - If the call to the NRFA API fails (response code != 200).
            
        Note: the self.cur_station value must be set before calling this function.
            This is done by calling fetchStationSummary() with the station ID.
        """
        station_id = self.cur_station['id']
        if (
            self.cache['pot'][0] == station_id and 
            self.cache['pot'][1] is not None and
            self.cache['pot'][2] is not None
            ):
            return self.cache['pot'][2], self.cache['pot'][1]

        url = self.NRFA_BASE_URL + 'time-series?'
        params = {
            'format': 'json-object',
            'station': str(station_id),
            'data-type': 'pot-flow',
        }
        response = requests.get(url, params=params)
        flow_data = None
        if response.status_code == 200:
            flow_data = response.json()
        else:
            raise ConnectionError(
                'Failed to connect to NRFA API. Status code: {0}'.format(response.status_code)
            )
        
        series = []
        count = 0
        dateval = None
        for i, value in enumerate(flow_data['data-stream']):
            if i == 0 or i % 2 == 0:
                dateval = value
            else:
                series.append({'flow': value, 'datetime': dateval})
            count += 1

        metadata = [
            '{0:<40} {1:<40}'.format('ID', 'POT-flow'),
            '{0:<40} {1:<40}'.format('Name', flow_data['data-type']['name']),
            '{0:<40} {1:<40}'.format('Parameter', flow_data['data-type']['parameter']),
            '{0:<40} {1:<40}'.format('Units', flow_data['data-type']['units']),
            '{0:<40} {1:<40}'.format('Measurement type', flow_data['data-type']['measurement-type']),
            '{0:<40} {1:<40}'.format('Period', flow_data['data-type']['period']),
        ]
        if not series:
            metadata.insert(
                0, '{0:<40}'.format('NO POT DATA FOUND FOR STATION')
            )
        self.cache['pot'][0] = station_id
        self.cache['pot'][1] = series
        self.cache['pot'][2] = metadata
        return metadata, series
    
    def fetchDailyFlowsData(self):
        """Fetch the daily flows data for a station from the NRFA API.
        
        Calls the NRFA API 'time-series' url to obtain all of the daily flows
        data for the self.cur_station. This is the NRFA API 'gdf' data-type.
        
        Return:
            tuple - containing (metadata, series, latest year) where metadata is 
                the daily flow summary data, series is a list of dicts containing 
                {flow, str_datetime}, and latest year is the most recent year in
                the dataset.
                
        Except:
            ConnectionError - If the call to the NRFA API fails (response code != 200).
            
        Note: the self.cur_station value must be set before calling this function.
            This is done by calling fetchStationSummary() with the station ID.
        """
        station_id = self.cur_station['id']
        if (
            self.cache['daily_flows'][0] == station_id and 
            self.cache['daily_flows'][1] is not None and
            self.cache['daily_flows'][2] is not None
            ):
            return (
                self.cache['daily_flows'][2], self.cache['daily_flows'][1], 
                list(self.cache['daily_flows'][1].keys())[-1]
            )

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
            raise ConnectionError(
                'Failed to connect to NRFA API. Status code: {0}'.format(response.status_code)
            )
        
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
        metadata = flow_data['data-type']
        metadata['interval'] = flow_data['interval']
        metadata['timestamp'] = flow_data['timestamp']
        self.cache['daily_flows'][0] = station_id
        self.cache['daily_flows'][1] = series
        self.cache['daily_flows'][2] = metadata
        return metadata, series, year
    
    def exportAmaxData(self, save_path):
        """Export AMAX data to csv at the given path.
        
        Args:
            save_path(str): file path to save the csv file to.
            
        Except:
            ValueError - if the AMAX data has not been loaded.
            OSError - if the file write fails.
        """
        series = self.amax_series
        with open(save_path, 'w', newline='\n') as save_file:
            writer = csv.writer(save_file, delimiter=',')
            writer.writerow(['Date', 'Flow (m3/s)'])
            for row in series:
                writer.writerow([row['datetime'], row['flow']])
    
    def exportPotData(self, save_path):
        """Export POT data to csv at the given path.
        
        Args:
            save_path(str): file path to save the csv file to.
            
        Except:
            ValueError - if the POT data has not been loaded.
            OSError - if the file write fails.
        """
        series = self.pot_series
        with open(save_path, 'w', newline='\n') as save_file:
            writer = csv.writer(save_file, delimiter=',')
            writer.writerow(['Date', 'Flow (m3/s)'])
            for row in series:
                writer.writerow([row['datetime'], row['flow']])

    def exportDailyFlowsData(self, save_path, export_year=None):
        """Export daily flows data to csv at the given path.
        
        Args:
            save_path(str): file path to save the csv file to.
            
        **kwargs:
            export_year=None: the year to export the data for. If None all
                years for the station will be exported.
            
        Except:
            ValueError - if the daily flows data has not been loaded.
            OSError - if the file write fails.
        """
        series = self.daily_flows_series
        if export_year is not None and not export_year in series.keys():
            raise AttributeError (
                'Export year {0} not available for daily flow series'.format(export_year)
            )

        with open(save_path, 'w', newline='\n') as save_file:
            writer = csv.writer(save_file, delimiter=',')
            writer.writerow(['Year', 'Date', 'Flow (m3/s)', 'Q Flag'])
            if export_year is not None:
                year_str = str(export_year)
                for row in series[export_year]:
                    writer.writerow([
                        year_str, row['date'], row['flow'], row['flag']
                    ])
            else:
                for year, data in series.items():
                    year_str = str(year)
                    for row in data:
                        writer.writerow([
                            year_str, row['date'], row['flow'], row['flag']
                        ])

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
        
        