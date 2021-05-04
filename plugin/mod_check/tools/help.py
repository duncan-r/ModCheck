'''
@summary: Handle the help dialog generation

@author: Duncan R.
@organization: Ermeview Environmental Ltd
@created 21st April 2021
@copyright: Ermeview Environmental Ltd
@license: LGPL v2
'''

OVERVIEW = """
ModCheck provides a suite of tools to help with the analysis and reviewing of 
1D-2D hydraulic models, including Flood Modeller Pro, ESTRY and TUFLOW.

Select a tool from the list to the left to find out more information about the 
tool and how to use it.

If there are any additional tools or features that you would like to include,
or you find any bugs / problems with the plugin, please let me know.
ModCheck is hosted on GitHub, where you can raise issues and feature requests:
https://github.com/duncan-r/ModCheck

If you would like to help contribute to the development of ModCheck please get
in touch. It would be better to contact me prior to working on anything in case
I'm already doing something similar.

Copyright 2021 Duncan. R @ Ermeview Environmental Ltd.

"""

CHECK_CHAINAGE = """
Check FMP-TUFLOW Chainage allows you to extract the chainage (node distance) values from
Flood Modeller and TUFLOW model nodes and compare them to ensure that they have similar 
values. This is currently only possible when the TUFLOW model includes a 1d_nwk line,
which is used to derive the distance between nodes in 2D (it is possible to extract
the FMP chainage values without comparing see the "FMP Only" section below).

Select an FMP .dat file in the FMP Model section, select the TUFLOW 1d_nwk line layer
in the TUFLOW inputs section, set the DX Tolerance value and click the 
Compare TUFLOW / FMP Chainage button.

The DX Tolerance value sets the limit at which a difference in the FMP and TUFLOW 
chainage values is considered acceptable. Any differences less than the tolerance
will not be flagged as failed in the status.

Once the model files have been analysed the Outputs tables will be populated with
the results. These include:

- FMP Chainage: The chainage values for each node that has a distance / chainage
  value, in the FMP model (river, interpolate, replicate, conduit).

- FMP Reach Table: A separate table that summarises the total chainage along an 
  individual reach. A reach is classes as a continues series of river, etc units 
  that are directly connected to each other.

- TUFLOW-FMP Comparison: The comparitive distance between the 1D FMP section
  chainage values and the 2D TUFLOW node chainage values. Only river, interpolate
  and replicate sections will be included in this table. If the difference 
  between the chainage values is greater than the tolerance they will have a
  status of "FAILED" and be highlighted red.

You can bring up a menu by right-clicking on a table row in the outputs and then
select "Locate Section" to view the location of a failed section. This will 
select the section of the 1d_nwk line that failed, re-centre and zoom the map 
window to that location.
  
The 2D TUFLOW chainage will report both the geometric line length along the 
1d_nwk line layer section and the Len_or_ANA value. If a Len_or_ANA value is
provided it will be used to calculate the chainage difference, if not the
line geometry will be used.

FMP Only:
If there is no 1d_nwk line available for the TUFLOW model you can tick the 
Calculate FMP chainage only checkbox and the Calculate FMP Chainage button and the
chainage values for the model will be added to the FMP Chainage tables.

You can export the results to a csv file with the Export Results button and 
select whichever tables you would like to export the results for.

"""

CHECK_WIDTH = """
Check 1D-2D Width allows you to compare the Flood Modeller 1D river section width
with the width - between the HX lines - at the 1D node locations in the TUFLOW model.

Select an FMP .dat file, select the TUFLOW 1d_nodes layer, select the TUFLOW layer
containing the CN lines, set the DW Tolerance value, and click the Check 1D-2D Widths button.

The DW Tolerance value sets the limit at which a difference in the FMP and TUFLOW 
width values is considered acceptable. It is best to base this value on what you think
will be acceptable based on the cell size used in the model (a 5m grid may mean that
a variation in width of up to 5m won't make any difference, for example). Any 
differences less than the tolerance will not be flagged as "FAIL" in the Failed table.

Once the model files have been analysed the Outputs tables will be populated with the 
results. There are two tables:

- Failed: A summary of all of the FMP sections that have an active width with a
  difference greater than the tolerance when compared to the 2D widths; these will
  be given a "FAIL" status. If an FMP node could not be found in the 2D model it 
  will be given a "MISSING" status. If a node only has a single CN line (so the
  width doesn't make any sense / can't be calculated) it will be given a "SINGLE_CN" status.

- All: A summary of all of the FMP nodes and the comparison widths, regardless of 
  whether they passed or failed the check.
  
The results of the check can be exported to a csv file with the Export Results button.
If you tick the Create failed nodes file? checkbox a second csv file that has the same
name as the first with "_failed" appended to it will be created. This file will 
include only the details of the FMP sections that failed the check.

You can bring up a menu by right-clicking on a table row in the outputs and then
select "Locate Section" to view the location of a failed section. This will 
select the 1D node that failed, re-centre and zoom the map window to that location.

The check works by calculating the active width of the river sections in the FMP
model - the non deactivated part of the section - and comparing it to the
distance between the end points of the CN lines in the TUFLOW model; the cartesian
distance between the two polyline nodes that are furthest away from each other.
Interpolate section widths are calculated based on the width of the two nearest
river sections and the position (chainage) of the interpolate between them. This is
essentially just a straight line calculation of width over distance.

Multipe Node / CN line layers:
If the model includes multiple nodes layers or multiple HX/CN line layers you
may want to combine the layers first, in order to avoid a lot of "MISSING" node
warnings. The easiest way to do this is with the "Toolbox" under the "Processing"
menu on the main QGIS menu bar. look under the "Vector general" tools and you
will find the "Merge vector layers" tool; use this to create two layers containing
all of the nodes in one and the cn lines in the other. At some point in the 
future I'll add a way to automatically combine the layers for checking, but
for the timebeing you'll need to do it manually.

"""

VARIABLES_SUMMARY = """
Run variables and summary allows you to review the 1D and 2D FMP and TUFLOW run
parameters, check them against the default values and interrogate some of the
diagnostic information from the simulation output files.

The are two main tabs, FMP and TUFLOW.


FMP:

The Multiple Summary tab will load key run parameter information from all FMP .ief
files in a folder (it will also search subfolders). These parameters will be loaded
into the table and any that have been changed from the default values will be
highlighted in red. By right-clicking on a row you can select to "Show detailed view"
and the full details and descriptions of the .ief file will be loaded into the 
Variables table.

The Variables tab contains a summary of all of the run parameters used in the FMP
model, whether they have been changed from the default, what the default value is and
a description explaining the parameter. It also includes a second table summarising
all of the files associated with the model (.dat, .iic, .ied, etc).
The tables can be loaded by either selecting an FMP .ief file in the file search box,
or by right-clicking on a row in the Multiple Summary tab table.

The Diagnostics tab will load key information from the FMP .zzd diagnostics file
outputs. The Run Summary table contains summary information about the details of the
simulation and the main diagnostic outputs. The Errors and Warnings table contains
a summary of all of the errors and/or warnings raised during the simulation, how many
times they occurred and a description of what it means. You can load the data into the
tables by selecting an FMP .zzd file in the file search box.


TUFLOW:

The variables tab contains a summary of all of the run parameter used in the TUFLOW model,
whether they have been changed from the default value, what the default value is and a
description explaining the parameter. There is also a second table summarising all of
the files used by the model (.tgc, .tbc, etc).

The diagnostics tab contains details about the simulation and the main diagnostics
outputs. These include summaries of the checks and warning, negative depths, 
model build, run dates, stability info, etc. The Checks, Warnings and Errors table 
contains a summary of all of the checks, warnings and errors that were raised during
the simulation, how many times they occurred, a description and a link to the 
TUFLOW wiki for more information.

"""

FMP_SECTIONS = """
Check FMP section properties allows you to review some key schematisation properties
of the Flood Modeller sections; primarily the river unit data.

Currently it supports reviewing the river section conveyance and banktop configuration.

When you select an FMP .dat file in the file search box it will load Flood Modeller
model and analyse it for sections that fail the checks.


Conveyance:

The conveyance check will populate the Conveyance table with the details of all of the
sections that have a negative conveyance with a value greater than the K Tolerance value.
The K Tolerance should be set to a value that is suitable for the size of the
flows that the model has (if max conveyance is ~10 m3/s it should be quite low, if it
is ~ 1000 m3/s it should be a bit higher). This will help to avoid identifying very
minor drops in conveyance that are unlikely to have any impact on the model results.

Banktop Check:

The banktop check will populate the Banktop Check table with the details of any section
that appears to have incorrectly configured banktops. These are sections in which the
highest elevations in the cross section are not at the extremes of the section geometry.
A dy tolerance can be used to only identify sections where there is a drop in
elevation, outside of the banktops, greater than the chosen value. Larger channels,
and consideration of the purpose of the model, may mean that a larger change is 
acceptable for some models. Ideally the extreme left/right values should be the
highest elevations in the section to avoid early overtopping of the channel and/or
artificially increased channel conveyance.

There is a right-click menu on both tables that allow you to locate the node
associated with the failed section and to graph the cross section and conveyance / 
banktop errors. 

"""

REFH_CHECK = """
Compare FMP ReFH units allows you to check the consistency of the values used in all
of the ReFH units in a Flood Modeller model.

Selecting an FMP .dat or .ied file in the file search box will load all of the ReFH
units in the model file and output the configuration values in the text box. The 
values for all of the different ReFH units will be displayed alongside each other 
for comparison.

Key values that should usually be the same across all ReFH boundaries are checked,
if there is a difference between some of the values they will be highlighted red
and should be investigated further to check that the value is correct.

The results of the check can be exported to a csv file with the Export to CSV button.
"""

CHECK_TUFLOW_MB = """
Check TUFLOW MB allows you to quickly review the cumulative mass balance and dVol
graphs from the TUFLOW csv result outputs. 

If you select an MB, MB1, or MB2 csv file in the TUFLOW MB file search box it will
load the cumulative mass balance and dVol data and graph it in the dialog.

Cumulative mass error percentage (CME) is graphed on the primary (left) y axis and
includes additional comparison lines (CME max recommended) to indicate the location
of +-1%; the recommended tolerance for CME.

The rate of change in volume (dVol) is graphed on the secondary (right) y axis.

"""

FILE_AUDIT = """
Audit model files allows you to check the contents of the FMP and TUFLOW model files
for file path references and checks that they exist under a user supplied folder.

Once the Model root folder is chosen all of the folders, including the one containing
the chosen folder, will be walked to create lookup table of files within the folder
structure. All model files will then be read (.tcf, .tgc, .ief, etc) to locate any
reference to another file. The lookup table is checked to see whether the files
referenced by the model files exist in the folders being checked. If they exist but
they are not in the path indicated by the model file they will be marked as being
Found Elsewhere, if the file can't be found it will be marked as Missing.

The results of the check will be output into the different tabs depending on how
the issues are categorised. When the check is complete the Search Summary tab will
be shown with:

- Search summary containing the numbers of different files checked.

- List of ignored files showing any files that have been deliberately ignored. This
  will include non model related files like the TUFLOW simulations log, .pdf files
  etc.
  
- List of model files reviewed giving a list of all of the model files that were
  parsed to check for references to other files. These are the .ief, .tcf, .tgc etc
  files.

  
The other tabs contain list of files that failed the check:

- Missing tab: contains all of the files that were referenced by a model file but
  could not be found anywhere in the folder structure being searched.
  
- Found Elsewhere tab: contains all of the files that were referenced by a model 
  file and were not in the location specified, but were found somewhere else.
  
- Ief Paths Found Elsewhere: this is exactly the same as the  Found Elsewhere tab
  in terms of functionality except it only applies to files referenced by an .ief
  file. Ief files are commonly delivered with absolute paths which means that all
  of the files they reference will fail. These failures are moved to their own
  table to make it easier to identify the more important issues in the main 
  Found Elsewhere tab.
  

All of the tabs contain the same setup of a table listing:

- File Name: the name of the file that could not be found (or was not where it should be).

- Found at: the path the the file was located at (this is not available for missing files).

- Original Path: the path referenced in the model file (the incorrect path).


Clicking on one of the rows in the tables will bring up a list of all of the 
model files that reference this missing/misplaced file, in the list below. If you
click on one of the model files in the list it will load the contents of the model
file into a new dialog window for you to view and highlight the section containing
the reference to the missing/misplaced file in yellow.

"""

NRFA_STATIONS = """
View NRFA station info allows you to identify gauging stations located near to the
current map window centre and review key hydrometric information relating to them.

Setting distance from the current map window center point (km's) and clicking the
Fetch Stations button will identify all of the NRFA registered river gauging stations
within the radius of the Max distance from map centre value. This will populate the
Station info dropdown box with all of the stations within the radius, create a
temporary layer containing the NRFA station ID and name for each station, select 
and zoom to the first station in the list, and show some summary info about the
selected gauging station. Changing the selected station in the dropdown box will
select and zoom to the new station and update the Station Info tab.

There are currently four other tabs for reviewing station information:

Full Details:
This will display all of the details currently held by NRFA for the station,
including useful information like pooling and qmed suitability, station type and
location, flow statistics and summary catchment descriptors.

AMAX:
This will load the AMAX series for the station (if available) and populate the
data in table, alongside some meta data for the data series. The AMAX data series
can be graphed with the Show Graph button and exported to csv via the Export CSV button.

POT:
This will load the POT series for the station (if available) and populate the
data in table, alongside some meta data for the data series. The POT data series
can be graphed with the Show Graph button and exported to csv via the Export CSV button.

Daily Flows:
This will load the gauged daily flows (gdf) data for the full record length of the station.
The data will be broken down by year (annual not water), which can be selected in
the Select Year dropdown box. When a year is selected the gdf data for that year 
will be added to the table. The flow series for the selected year can be graphed
with the Show Graph button. The data can also be export to csv with the Export CSV
button. The default is to export only the data for the currently selected year. If
you would like to export the complete record for the station to csv change the
dropdown box to "Export all years".

The NRFA viewer connects directly to the NRFA API to gather the data. This means
that it will require an internet connection to use. If there is a connection
issue it will raise an error. This does mean that the data that is loaded
will be the latest data that the NRFA has available for the gauging station.
The only exception to this is the station locations which are stored in a 
shapefile within the plugin. I'll add something to make it possible to update
this by connecting to the NRFA site and obtaining the station locations at some
point soon.

"""

HELP_LOOKUP = {
    'Overview': OVERVIEW,
    'Check Chainage': CHECK_CHAINAGE,
    'Check Width': CHECK_WIDTH,
    'Run Variables Summary': VARIABLES_SUMMARY,
    'Check FMP Sections': FMP_SECTIONS,
    'ReFH Check': REFH_CHECK,
    'Check TUFLOW MB': CHECK_TUFLOW_MB,
    'Model File Audit': FILE_AUDIT,
    'NRFA Station Viewer': NRFA_STATIONS,
}

def helpText(help_key):
    return HELP_LOOKUP[help_key]


class ModCheckHelp():
    
    def __init__(self):
        self.help_lookup = HELP_LOOKUP
#         {
#             'Overview': OVERVIEW,
#             'Check Chainage': CHECK_CHAINAGE,
#             'Check Width': CHECK_WIDTH,
#             'Run Variables Summary': VARIABLES_SUMMARY,
#             'Check FMP Sections': FMP_SECTIONS,
#             'ReFH Check': REFH_CHECK,
#             'Check TUFLOW MB': CHECK_TUFLOW_MB,
#             'Model File Audit': FILE_AUDIT,
#             'NRFA Station Viewer': NRFA_STATIONS,
#         }
        
    def helpList(self):
        return self.help_lookup.keys()
    
    def helpContents(self, tool_name):
        return self.help_lookup[tool_name]
    
    