'''
@summary: Main interface to be implemented by all tools.

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 29th September 2020
@copyright: Ermeview Environmental Ltd
@license: LGPL v2
'''


class ToolInterface():
    
    def __init__(self):
        pass
    
    def load_tool(self):
        pass
    
    def unload_tool(self):
        pass
    
    def run_tool(self):
        pass
    
    