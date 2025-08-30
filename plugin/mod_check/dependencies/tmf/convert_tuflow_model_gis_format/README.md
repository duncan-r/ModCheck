# Convert TUFLOW Model GIS Format

Python script that will convert a given TUFLOW model's vector and raster GIS files 
into another, or same, supported TUFLOW format. The script is similar to the package model
functionality that exists in TUFLOW and will try and package files from all
scenarios/events. The difference between the package model functionality and this script
is that this script will perform additional format conversion steps and update relevant control files.

The tool also gives additional options when converting to GPKG vector and raster formats. The
GPKG format is a database and allows multiple layers within one file (including a mixture of vector and raster)
and the tool gives the option to convert into:

- each layer into separate GPKG databases
- group layers into GPKGs that corresponds to each control file
- output all layers into a single GPKG database

## Supported formats

### Vector formats

- MIF
- SHP
- GPKG

### Raster formats

- ASC
- FLT
- GeoTIFF
- GPKG

## Dependencies

- Python 3.9+
- GDAL
- Numpy

## Quickstart

`python convert_tuflow_gis_format.py -tcf <filepath_to_tcf>`

Selecting an output vector format:

`python convert_tuflow_gis_format.py -tcf <filepath_to_tcf> -gis <vector_format>`

Selecting an output raster format:

`python convert_tuflow_gis_format.py -tcf <filepath_to_tcf> -grid <raster_format>`

Selecting an output profile with GPKG:

`python convert_tuflow_gis_format.py -tcf <filepath_to_tcf> -gis GPKG -op <output_profile>`

Choosing an output folder:

`python convert_tuflow_gis_format.py -tcf <filepath_to_tcf> -o <path_to_output_folder>`

## Options

required inputs:

- `-tcf [file path to tcf]`

optional inputs:

- `-o [path to output folder]`
- `-op [{SEPARATE} | CF | TCF]` - output profile, groups GPKG separately, by control file, or by TCF (all in one)
- `-gis [{GPKG} | SHP | MIF]` - output vector format the model will be converted into
- `-grid [GPKG | {TIF} | ASC | FLT]` - output raster format the model will be converted into
- `-rf [path to root folder]` - optional argument to specify the root folder (conventionally named 'TUFLOW')
- `-use-scenarios` - optional argument to switch on a more restrictive set of layers to convert.
The tool will also clean up control files if there is an `IF Scenario` that becomes unused. This also works for `IF Event` logic,
but will not parse the TUFLOW Event File so all event sources will still be copied.
- `-s [scenario name]` - optional argument that can be used multiple times to pass in scenario names to be used with `-use-scenarios`
- `-e [event name]` - optional argument that can be used multiple times to pass in event names to be used with `-use-scenarios`
- `-gpkg-name` - optional argument to specify an output name for the GPKG database when using a grouped output profile
- `-write-empties [/relpath/to/emptyfolder]` - optional argument to create empty files for the converted model.
The location of the empty files will be guessed by the tool unless a relative path from the TUFLOW 
root directory is provided. The projection of the empty files will be determined by the first `Projection == ` command 
encountered. If no `Projection == ` command is present, empty files will not be created.
- `-crs [srs_ref]` Forces output files to be in given projection (no reprojection, or warping is performed). 
                   Useful when converting a model with a combination of SHP and MIF files as these can generate 
                   slightly different projection definitions. srs_def should be in the style of "EPSG:XXXX" or 
                   can pass in PRJ or MIF projection string.
- `-tuflow-dir-struct` - If this flag is present, the output files will try and be placed in a TUFLOW standard
                         directory structure. 

## Windows Installation


<b>Note:</b> The steps below are now out of date and the GDAL distributions provided by Christopher Gohlke are no 
longer maintained. It's still possible to use the old steps if using a supported Python version - 
please check [https://www.lfd.uci.edu/~gohlke/pythonlibs/](www.lfd.uci.edu/~gohlke/pythonlibs)
for compatible Python and GDAL versions.

### GDAL Installation Using Gohlke

The easiest way to install GDAL Python bindings is to use [Precompiled Wheels by Christopher Gohlke](https://github.com/cgohlke/geospatial-wheels/)

1. Download the wheel for the desired GDAL and Python versions
2. Use pip to install the downloaded wheel<br>
`pip install </path/to/wheel>`

### GDAL Installation Using Conda

The easiest way to install GDAL Python binding is to use a Conda environment 
(the steps below are an example, you should check and update version numbers where appropriate):

1. Install Miniconda - [https://docs.conda.io/en/latest/miniconda.html](https~~://docs.conda.io/en/latest/miniconda.html)
2. Open the Anaconda command prompt - search `Anaconda Prompt` in the windows start bar
3. Create a new environment (optional) - replace python version and environment name as desired<Br>
`conda create -n convert_tuflow_model_gis_format python=3.10`
4. Activate environment<br>
`conda activate convert_tuflow_model_gis_format`
5. Install GDAL (make sure to use an appropriate GDAL version - [https://anaconda.org/conda-forge/gdal]())<Br>
`conda install -c conda-forge gdal=3.5.2`
6. Check the installation has worked by starting the Python interpreter and importing the ogr and gdal libraries<br>
`python`<br>
`from osgeo import ogr, gdal`

## Linux Installation

The following link steps through how to get gdal python bindings on Ubuntu:<br>
[https://mothergeo-py.readthedocs.io/en/latest/development/how-to/gdal-ubuntu-pkg.html](https://mothergeo-py.readthedocs.io/en/latest/development/how-to/gdal-ubuntu-pkg.html)

## Running Tests

Use Pycharm or:

### Windows

1. In the terminal, navigate to parent folder `convert_tuflow_model_gis_format`
2. Add `conv_tf_gis_format` folder to the `PYTHONPATH`<br>
`set PYTHONPATH=%PYTHONPATH%;conv_tf_gis_format`
3. Run desired test case<br>
e.g. `python -m unittest tests.test_all`

### Linux

1. In the terminal, navigate to parent folder `convert_tuflow_model_gis_format`
2. Add `conv_tf_gis_format` folder to the `PYTHONPATH`<br>
`export PYTHONPATH=${PYTHONPATH}:conv_tf_gis_format`
3. Run desired test case<br>
e.g. `python -m unittest tests.test_all`

## Support

For any issues please get into contact with [support@tuflow.com](mailto:support@tuflow.com).

## License
This project is licensed under GNU GENERAL PUBLIC LICENSE Version 3.

## Changelog

- 0.84
  - TIN inputs are now supported

- 0.33
  - Updated tests to work on Linux

- 0.30
  - GeoTIFF output will now use zlevel = 1

- 0.29
  - GeoTIFF output will now use all CPU threads for output

- 0.23
  - Adds option to specify output CRS (overrides output, does not perform reprojection)

- 0.20
  - Report commands that do not copy any files (but are meant to)

- 0.19
  - Adds option to create empty files

- 0.16
  - Adds file encoding prediction

- 0.15
  - Adds option to specify output GPKG name for grouped profiles

- 0.13
  - Adds support to limit conversion by scenarios/events and simplify control files

- 0.1
  - First version