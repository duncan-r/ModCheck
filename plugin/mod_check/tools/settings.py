
from qgis.core import QgsProject, QgsSettings
from builtins import isinstance


PLUGIN = 'ermeview_model_tools'
PLUGIN_PREFIX = PLUGIN + '/' 

PROJECT = 'project'
GLOBAL = 'global'
SETTING_TYPES = (PROJECT, GLOBAL)


def saveSetting(setting_type, name, value):
    if setting_type == GLOBAL:
        saveGlobalSetting(name, value)
    elif setting_type == PROJECT:
        saveProjectSetting(name, value)
    else:
        raise ValueError('Setting type not recognised')
    

def saveGlobalSetting(name, value):
    settings = QgsSettings()
    settings.setValue(PLUGIN_PREFIX + name, value)
    
def loadGlobalSetting(name, default=None):
    settings = QgsSettings()
    
    if default is None:
        return settings.value(PLUGIN_PREFIX + name, None)
    else:
        return settings.value(PLUGIN_PREFIX + name, default)


def saveProjectSetting(name, value):
    proj = QgsProject.instance()
    
    if isinstance(value, float):
        proj.writeEntryDouble(PLUGIN, name, value)
    elif isinstance(value, bool):
        proj.writeEntryBook(PLUGIN, name, value)
    else:
        proj.writeEntry(PLUGIN, name, value)
        
def loadProjectSetting(name, value_type, default):
    proj = QgsProject.instance()
    
    value = None
    if isinstance(value_type, float):
        value, conversion_ok = proj.readEntryDouble(PLUGIN, name, default)
    if isinstance(value_type, bool):
        value, conversion_ok = proj.readEntryBool(PLUGIN, name, default)
    else:
        value, conversion_ok = proj.readEntry(PLUGIN, name, default)
    
    if not conversion_ok:
        #raise ValueError('Value, or default, could not be converted to type')
        return default
    else:
        return value