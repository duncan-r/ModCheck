# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ModelReviewTools
                                 A QGIS plugin
 A collection of tools for reviewing hydraulic models
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-02-23
        copyright            : (C) 2021 by Duncan Runnacles
        email                : info@ermeviewenvironmental.co.uk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
import os
import sys

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.core import *

from builtins import IOError

ICON_NAME = 'icon.png'
MENU_NAME = 'ModCheck'
TR_MENU_NAME = '&ModCheck'
SHIP_VERSION = 'ship-0.3.3.dev0-py3.8.egg'

# Make sure we have access to the SHIP library
ship_path = os.path.join(os.path.dirname(__file__), 'dependencies', SHIP_VERSION)
try:
    sys.path.append(ship_path)
    import ship
except ImportError:
    raise ('Unable to load SHIP library')
from .dialogs import *

class Menu:

    def __init__(self, iface):
        
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)


        # Declare instance attributes
        #000  self.actions = []
        #self.menu = self.tr(u'&ModCheck')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        #self.first_start = None
        
    
    def initGui(self):
        self.dir = os.path.dirname(__file__)
        self.icon_dir = self.dir
        icon = QIcon(os.path.join(self.icon_dir, "icon.png"))
        
        self.dialogs = {
            'FMP_TUFLOW_Chainage': {'dialog': None, 'class': ChainageCalculatorDialog},
            'FMP_TUFLOW_Width_Check': {'dialog': None, 'class': FmpTuflowWidthCheckDialog},
            'FMP_Section_Check': {'dialog': None, 'class': FmpSectionCheckDialog},
            'View_NRFA_Station': {'dialog': None, 'class': NrfaStationViewerDialog},
            'FMP_REFH_Check': {'dialog': None, 'class': FmpRefhCheckDialog},
            'TUFLOW_Stability_Check': {'dialog': None, 'class': TuflowStabilityCheckDialog},
            'FMP_Stability_Check': {'dialog': None, 'class': FmpStabilityCheckDialog},
            'Model_File_Audit': {'dialog': None, 'class': FileCheckDialog},
            'Model_Variables_Check': {'dialog': None, 'class': FmpTuflowVariablesCheckDialog},
        }

        # submenu example: Chainage submenu
#         self.chainage_menu = QMenu(QCoreApplication.translate("ModCheck", "&Chainage"))
#         self.iface.addPluginToMenu("&ModCheck", self.chainage_menu.menuAction())
#         self.calc_fmp_chainage_action = QAction(icon, "Calculate FMP Chainage", self.iface.mainWindow())
#         self.calc_fmp_chainage_action.triggered.connect(self.calc_fmp_chainage)
#         self.chainage_menu.addAction(self.calc_fmp_chainage_action)
        # unloading the menu item (put in unload)
#         self.iface.removePluginMenu("&ModCheck", self.chainage_menu.menuAction())

        # Help page
        self.help_page_action = QAction(icon, "Help", self.iface.mainWindow())
        self.help_page_action.triggered.connect(self.help_page)
        self.iface.addPluginToMenu("&ModCheck", self.help_page_action)

        # Chainage / node distance check
        self.check_fmptuflow_chainage_action = QAction(icon, "Check FMP-TUFLOW Chainage", self.iface.mainWindow())
        self.check_fmptuflow_chainage_action.triggered.connect(self.check_fmptuflow_chainage)
        self.iface.addPluginToMenu("&ModCheck", self.check_fmptuflow_chainage_action)
        
        # 1D2D width check
        self.check_1d2dWidth_action = QAction(icon, "Check 1D-2D width", self.iface.mainWindow())
        self.check_1d2dWidth_action.triggered.connect(self.check_1d2d_width)
        self.iface.addPluginToMenu("&ModCheck", self.check_1d2dWidth_action)

        # FMP / TUFLOW default variables check
        self.get_runsummary_action = QAction(icon, "Run variables and summary", self.iface.mainWindow())
        self.get_runsummary_action.triggered.connect(self.get_runsummary)
        self.iface.addPluginToMenu("&ModCheck", self.get_runsummary_action)
        
        # FMP section property check
        self.check_fmpsections_action = QAction(icon, "Check FMP section properties", self.iface.mainWindow())
        self.check_fmpsections_action.triggered.connect(self.check_fmp_sections)
        self.iface.addPluginToMenu("&ModCheck", self.check_fmpsections_action)
        
        # FMP REFH unit compare
        self.check_fmprefh_action = QAction(icon, "Compare FMP refh units", self.iface.mainWindow())
        self.check_fmprefh_action.triggered.connect(self.check_fmp_refh)
        self.iface.addPluginToMenu("&ModCheck", self.check_fmprefh_action)
        
        # TUFLOW stability outputs viewer (MB, Dvol, etc)
        self.check_tuflowstability_action = QAction(icon, "Check TUFLOW MB", self.iface.mainWindow())
        self.check_tuflowstability_action.triggered.connect(self.check_tuflow_stability)
        self.iface.addPluginToMenu("&ModCheck", self.check_tuflowstability_action)

        # FMP stability outputs viewer (Stage and Flow oscillations)
        self.check_fmpstability_action = QAction(icon, "Check FMP Stability Plots", self.iface.mainWindow())
        self.check_fmpstability_action.triggered.connect(self.check_fmp_stability)
        self.iface.addPluginToMenu("&ModCheck", self.check_fmpstability_action)

        # TUFLOW stability outputs viewer (MB, Dvol, etc)
        self.filecheck_action = QAction(icon, "Audit Model Files", self.iface.mainWindow())
        self.filecheck_action.triggered.connect(self.check_files)
        self.iface.addPluginToMenu("&ModCheck", self.filecheck_action)

        # NRFA Station viewer
        self.nrfa_stationviewer_action = QAction(icon, "View NRFA Station Info", self.iface.mainWindow())
        self.nrfa_stationviewer_action.triggered.connect(self.view_nrfa_station)
        self.iface.addPluginToMenu("&ModCheck", self.nrfa_stationviewer_action)
        
    def unload(self):
        self.iface.removePluginMenu("&ModCheck", self.help_page_action)
        self.iface.removePluginMenu("&ModCheck", self.check_fmptuflow_chainage_action)
        self.iface.removePluginMenu("&ModCheck", self.check_1d2dWidth_action)
        self.iface.removePluginMenu("&ModCheck", self.get_runsummary_action)
        self.iface.removePluginMenu("&ModCheck", self.check_fmpsections_action)
        self.iface.removePluginMenu("&ModCheck", self.check_fmprefh_action)
        self.iface.removePluginMenu("&ModCheck", self.check_tuflowstability_action)
        self.iface.removePluginMenu("&ModCheck", self.check_fmpstability_action)
        self.iface.removePluginMenu("&ModCheck", self.nrfa_stationviewer_action)
        self.iface.removePluginMenu("&ModCheck", self.filecheck_action)
        
    def launchDialog(self, dialog_name):
        dialog_class = self.dialogs[dialog_name]['class']
        if self.dialogs[dialog_name]['dialog'] is None:
            self.dialogs[dialog_name]['dialog']= dialog_class(dialog_name, self.iface, QgsProject.instance())
            self.dialogs[dialog_name]['dialog'].closing.connect(self._closeDialog)
            self.dialogs[dialog_name]['dialog'].show()
        else:
            self.dialogs[dialog_name]['dialog'].setWindowState(
                self.dialogs[dialog_name]['dialog'].windowState() & ~Qt.WindowMinimized | Qt.WindowActive
            )
            
    def _closeDialog(self, dialog_name):
        self.dialogs[dialog_name]['dialog'] = None
        
    def check_fmptuflow_chainage(self):
        self.launchDialog('FMP_TUFLOW_Chainage')

    def check_1d2d_width(self):
        self.launchDialog('FMP_TUFLOW_Width_Check')
        
    def check_fmp_sections(self):
        self.launchDialog('FMP_Section_Check')
        
    def view_nrfa_station(self):
        self.launchDialog('View_NRFA_Station')

    def check_fmp_refh(self):
        self.launchDialog('FMP_REFH_Check')

    def check_tuflow_stability(self): 
        self.launchDialog('TUFLOW_Stability_Check')

    def check_fmp_stability(self): 
        self.launchDialog('FMP_Stability_Check')

    def check_files(self):
        self.launchDialog('Model_File_Audit')

    def get_runsummary(self):
        self.launchDialog('Model_Variables_Check')
        
    def help_page(self):
        dialog = HelpPageDialog(self.iface, QgsProject.instance())
        dialog.exec_()
        
        
        