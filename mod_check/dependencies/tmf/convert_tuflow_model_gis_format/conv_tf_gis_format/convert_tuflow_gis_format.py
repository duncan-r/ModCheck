import sys
import datetime
from helpers.control_file import convert_control_file
from helpers.empty_files import TuflowEmptyFiles
from helpers.settings import ConvertSettings, FatalConvertException, PythonVersionError
from helpers.gis import init_gdal_error_handler


__VERSION__ = '0.137'


def main():
    """
    Tool to convert model to a specified TUFLOW supported vector and raster format.

    required inputs:
        -tcf <file path to tcf>

    optional inputs:
        -o <path to output folder>
        -op [{SEPARATE} | CF | TCF] - output profile, groups GPKG separately, by control file, or by TCF (all in one)
        -gis [{GPKG} | SHP | MIF] - output vector format the model will be converted into
        -grid [GPKG | {TIF} | ASC | FLT] - output raster format the model will be converted into
        -rf <path to root folder> - optional argument to specify the root folder (conventionally named 'TUFLOW')
        -use-scenarios - limit conversion to specified scenarios/events
        -s [scenario name] - scenario name to be used in conjunction with -use-scenarios.
                             Can be passed in multiple times.
        -e [event name] - event name to be used in conjunction with -use-scenarios. Can be passed in multiple times
        -gpkg-name - output GPKG database name if using a grouped output profile
        -write-empties [/rel-path/from/root] - writes TUFLOW empty files in the specified GIS format.
                                             Will guess where it should be written, or a relative path can be passed in.
                                             Will use the projection of the first 'Projection == ' command. If  no
                                             projection command is found, it will not write empty files.
        -crs [srs_def] - Forces output files to be in given projection (no reprojection, or warping is performed).
                         Useful when converting a model with a combination of SHP and MIF files as these can generate
                         slightly different projection definitions. srs_def should be in the style of "EPSG:XXXX" or
                         can pass in PRJ or MIF projection string.
        -tuflow-dir-struct - If this flag is present, the output files will try and be placed in a TUFLOW standard
                             directory structure.
    """

    print(f'Version: {__VERSION__}')
    print('Datetime stamp: {0:%d}/{0:%m}/{0:%Y} {0:%H}:{0:%M}:{0:%S}'.format(datetime.datetime.now()))

    init_gdal_error_handler()

    try:
        settings = ConvertSettings(*sys.argv)
    except PythonVersionError:
        print(f'Python version does not meet minimum requirement (requires Python 3.9+). '
              f'Installed version: Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')
        exit(1)
    try:
        settings.read_tcf()  # initial pass reading TCF to pull out some info
    except FatalConvertException as e:
        print(f'Error reading TCF: {e}')
        exit(1)

    # write empties
    try:
        if settings.write_empties:
            empties = TuflowEmptyFiles(settings.output_gis_format, settings.projection_wkt)
            empties.write_empties(settings.write_empties, settings)
    except FatalConvertException as e:
        print(f'Error writing empties: {e}')
        exit(1)

    # primary routine
    try:
        convert_control_file(settings.tcf, settings)
    except FatalConvertException as e:
        print(f'Error converting model: {e}')
        exit(1)

    # create any empty folders within tuflow directory structure
    try:
        settings.create_empty_folders()
    except Exception as e:
        print(f'Error creating empty folders: {e}')

    # finish up and notify if any errors occurred
    if settings.no_files_copied:
        print('\nCHECK - No files were copied for the following commands:\n- {0}'.format('"\n- '.join([': '.join(x) for x in settings.no_files_copied])))
    if settings.errors:
        print(f'\nFinished but some errors did occur - search output for "Error": {settings.model_name}')
    elif settings.warnings:
        print(f'\nFinished but some warnings did occur - search output for "Warning": {settings.model_name}')
    else:
        print(f'\nSuccessfully converted model: {settings.model_name}')


if __name__ == '__main__':
    main()
