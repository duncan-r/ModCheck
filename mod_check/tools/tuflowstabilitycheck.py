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
    
    def __init__(self, mb_path):
        super().__init__()
        self.mb_path = mb_path
    
    def run_tool(self):
        super()
        return self.loadMbCsv()
        
    def loadMbCsv(self):
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
        results = {'time': [], 'dvol': [], 'cme': []}
        with open(self.mb_path, 'r') as mb_file:
            reader = csv.reader(mb_file, delimiter=',')
            count = 0
            for r in reader:
                if count == 0:
                    for i, col in enumerate(r):
                        if 'Time (h)' in col: TIME = i
                        if 'dVol' in col: DVOL = i
                        if 'Cum ME (%)' in col: CME = i
                    count += 1
                else:
                    results['time'].append(float(r[TIME]))
                    results['dvol'].append(float(r[DVOL]))
                    results['cme'].append(float(r[CME]))
        return results