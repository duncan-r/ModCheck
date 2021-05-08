'''
@summary: View tuflow MB / dvol etc outputs

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 10th March 2021
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


class TuflowStabilityCheck(ti.ToolInterface):
    
    def __init__(self):
        super().__init__()
    
    def findMbFiles(self, root_folder, mb_types=['_MB']):
        """
        """
        mb_paths = []
        for root, dirs, files in os.walk(root_folder):
            for f in files:
                filepath = os.path.join(root,f)
                # Skip the differently formatted files for section MB
                if '_1d_MB.csv' in filepath: continue
                # Otherwise grab the file path
                for mbt in mb_types:
                    if mbt + '.csv' in filepath:
                        mb_paths.append(filepath)
        return mb_paths
    
    def loadMultipleFiles(self, mb_files, headers=['Cum ME (%)', 'dVol']):
        results = []
        for mb in mb_files:
            contents = self.loadMbFile(mb, headers)
            if contents is not None:
                run_name = os.path.split(mb)[1]
                run_name = os.path.splitext(run_name)[0]
                max_mb = max(contents['Cum ME (%)'])
                min_mb = min(contents['Cum ME (%)'])
                big_mb = round(max_mb, 2) if max_mb > -min_mb else round(min_mb, 2)
                fail = big_mb > 1 or big_mb < -1
                results.append({
                    'path': mb, 'name': run_name, 'data': contents, 'max_mb': big_mb,
                    'fail': fail,
                })
        return results

    def loadMbFile(self, mb_path, headers=['Cum ME (%)', 'dVol']):
        """Load the contents of TUFLOW MB/MB1D/MB2D.csv file.
        
        Need to be a bit careful about how we load this because the exact string used
        as the header changes between MB file types and I'm not sure that the columns
        always occur in the same place. So we search the headers for what we want and
        then grab the data from the columns that we identify.
        
        Args:
            mb_path(str): file path for the mass balance results file (MB.csv)
            headers(list): containing the header strings. Time will be included
                automatically.
        
        Return:
            Dict containing {time, header1, header2, etc} for the loaded file.
        """
        results = {'Time (h)': []}
        col_lookup = {'Time (h)': -1}
        for h in headers:
            results[h] = []
            col_lookup[h] = -1

        with open(mb_path, 'r') as mb_file:
            reader = csv.reader(mb_file, delimiter=',')
            count = 0
            for r in reader:
                if count == 0:
                    # This is a dirty approach but there will only ever be about 20
                    # columns and it's only run on one row so it shouldn't take too long
                    for i, col in enumerate(r):
                        strip_col = col.strip()
                        for l in col_lookup.keys():
                            if l == strip_col: col_lookup[l] = i 
                else:
                    for res in results.keys():
                        results[res].append(float(r[col_lookup[res]]))
                count += 1
                
        # Return None if there is no data in the file
        if len(results['Time (h)']) < 2:
            return None
        else:
            return results
        
    def loadMbCsv(self, mb_path, include_dvol=True):
        """Load the contents of TUFLOW MB/MB1D/MB2D.csv file.
        
        Need to be a bit careful about how we load this because the exact string used
        as the header changes between MB file types and I'm not sure that the columns
        always occur in the same place. So we search the headers for what we want and
        then grab the data from the columns that we identify.
        
        Return:
            Dict containing {time, dvol, cme} for the loaded file.
        """
        TIME = -1
        DVOL = -1
        CME = -1
        if include_dvol:
            results = {'time': [], 'dvol': [], 'cme': []}
        else:
            results = {'time': [], 'cme': []}

        with open(mb_path, 'r') as mb_file:
            reader = csv.reader(mb_file, delimiter=',')
            count = 0
            for r in reader:
                if count == 0:
                    for i, col in enumerate(r):
                        if 'Time (h)' in col: TIME = i
                        if 'dVol' in col and include_dvol: DVOL = i
                        if 'Cum ME (%)' in col: CME = i
                    count += 1
                else:
                    results['time'].append(float(r[TIME]))
                    if include_dvol:
                        results['dvol'].append(float(r[DVOL]))
                    results['cme'].append(float(r[CME]))
        return results
    
    
    