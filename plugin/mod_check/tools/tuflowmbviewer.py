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


class TuflowMbViewer(ti.ToolInterface):
    
    def __init__(self, working_dir):
        super().__init__()
        self.working_dir = working_dir
    
    def run_tool(self):
        super()