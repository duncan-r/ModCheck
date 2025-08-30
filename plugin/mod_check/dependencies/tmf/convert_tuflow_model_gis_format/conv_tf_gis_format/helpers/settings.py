import json
import re
import os
import sys
from pathlib import Path
import platform


SEPARATE = 1
GROUPED_BY_CONTROL_FILE_1 = 2
GROUPED_BY_CONTROL_FILE_2 = 3  # will include trd, tef as separate control file
GROUPED_BY_TCF = 4
GROUPED_TEMP = 5


with open(Path(__file__).parent.parent / 'data' / 'dir_relationships.json') as f:
    TUF_DIR = json.load(f)


tuf_dir_struct = TUF_DIR


def set_tuf_dir_struct(struct: dict = None):
    global tuf_dir_struct
    if struct:
        tuf_dir_struct.update(struct)
    tuf_dir_struct['folder_structure']['other'] = './other'


class FatalConvertException(Exception):
    """Exception that causes tool to exit."""

    pass


class MinorConvertException(Exception):
    """Exception that will allow tool to continue but notify that an error has occurred at the end of script."""

    pass


class PythonVersionError(Exception):
    """Exception that is called if Python version requirement is not met."""

    pass


class ConvertSettings:
    """Class for handling the conversion settings."""

    def __init__(self, *args, convert_settings=None):
        from .gis import GIS_GPKG, GRID_TIF

        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 9):
            raise PythonVersionError

        if convert_settings:
            for attr in dir(convert_settings):
                if not callable(eval(f'convert_settings.{attr}')) and not re.findall(r'__.*__', attr):
                    setattr(self, attr, getattr(convert_settings, attr))
        else:
            self.errors = False
            self.warnings = False
            self.verbose = 'high'
            self.no_ext = None
            self.output_profile = SEPARATE
            self.written_projection = False
            self.written_tif_projection = False
            self.tif_projection_path = None
            self.spatial_database = None
            self.read_spatial_database = None
            self.read_spatial_database_tcf = None
            self.tcf = None
            self.output_gis_format = GIS_GPKG
            self.output_grid_format = GRID_TIF
            self.control_file = None
            self.control_file_out = None
            self.written_spatial_database_header = True
            self.projection_wkt = None
            self.root_folder = None
            self.output_folder = None  # output_folder/root_model_folder
            self.output_folder_ = None  # output folder
            self.wildcards = [r'(<<.{1,}?>>)']
            self.map_output_grids = []
            self.grid_format_command_exists = False
            self.line_count = 0
            self.output_zones = []
            self.variables = {}
            self.scenarios = []
            self.use_scenarios = False
            self.gpkg_out_name = None
            self.write_empties = None
            self.no_files_copied = []
            self.force_projection = False
            self.gis_folder = None
            self.tuf_dir_struct = False
            self.tuf_dir_struct_settings = None
            self.always_use_root_dir = False
            self.check_file_prefix_2d = None
            self.check_file_prefix_1d = None
            self.explode_multipart = False
            self.copied_bndry_files = {}
            self.command = None
            self.parent_settings = None
            self.resolve_var = False

            if args:
                self._init_settings_with_args(*args)

    def _init_settings_with_args(self, *args):
        from .gis import GIS_GPKG, GRID_TIF

        self._parse_args(*args)
        if not self.tcf:
            raise FatalConvertException('Must provide TCF file location.')
        if not self.root_folder:
            self.root_folder = self._guess_root_folder()
            if self.root_folder is None:
                raise FatalConvertException('Unable to guess root folder from TCF. Please assign a root folder using argument -rf <folder name>')
        if not self.output_folder:
            self.output_folder = self.tcf.parent
            self.output_folder = self.output_folder / self.tcf.stem / self.root_folder.name
        elif self.always_use_root_dir:
            self.output_folder = self.output_folder / self.root_folder.name
        self.model_name = self.get_model_name(self.tcf)
        self.written_tif_projection = not self.output_grid_format == GRID_TIF
        if self.gpkg_out_name is None:
            self.gpkg_out_name = self.model_name
            if self.output_gis_format != GIS_GPKG:
                self.output_profile = SEPARATE

    def _parse_args(self, *args):
        """Routine to parse the CLI arguments."""
        from .file import TuflowPath
        from .gis import arg_to_ogr_format, arg_to_gdal_format, arg_to_projection
        while args:
            if args[0].lower() == '-rf':
                if len(args) < 2:
                    raise FatalConvertException('Root folder location required after -rf argument')
                self.root_folder = TuflowPath(args[1])
                args = args[1:]
            elif args[0].lower() == '-o':
                if len(args) < 2:
                    raise FatalConvertException('Output folder location required after -o argument')
                self.output_folder = TuflowPath(args[1])
                args = args[1:]
            elif args[0].lower() == '-tcf':
                if len(args) < 2:
                    raise FatalConvertException('TCF file location required after -tcf argument')
                self.tcf = TuflowPath(args[1]).resolve()
                self.control_file = self.tcf
                if not self.tcf.exists():
                    raise FatalConvertException(f'TCF does not exist: {self.tcf}')
                args = args[1:]
            elif re.findall(r'-gis([_-]?format)?', args[0], flags=re.IGNORECASE):
                if len(args) < 2:
                    raise FatalConvertException('GIS format (e.g. GPKG) required after -gis_format argument')
                self.output_gis_format = arg_to_ogr_format(args[1])
                if self.output_gis_format is None:
                    raise FatalConvertException(f'GIS format is not recognised: {args[1]}')
                args = args[1:]
            elif re.findall(r'-grid([_-]?format)?', args[0], flags=re.IGNORECASE):
                if len(args) < 2:
                    raise FatalConvertException('GRID format (e.g. TIF) required after -grid_format argument')
                self.output_grid_format = arg_to_gdal_format(args[1])
                if self.output_grid_format is None:
                    raise FatalConvertException(f'GRID format is not recognised: {args[1]}')
                args = args[1:]
            elif args[0].lower() == '-op':
                if len(args) < 2:
                    raise FatalConvertException('Output profile must be specified after -op argument. E.g. SEPARATE, TCF, CF')
                self.output_profile = self._arg_to_output_profile(args[1])
                if self.output_grid_format is None:
                    raise FatalConvertException(f'Output profile is not recognised: {args[1]}')
            elif re.findall(r'-use[_-]?scenarios', args[0], flags=re.IGNORECASE):
                self.use_scenarios = True
            elif re.findall(r'-s\d?$', args[0], flags=re.IGNORECASE):
                if len(args) < 2:
                    raise FatalConvertException('Scenario name must be specified after -s scenario argument. E.g. -s BASE')
                if re.findall(r'\d', args[0]):
                    i = int(re.findall(r'\d', args[0])[0]) - 1
                else:
                    i = 0
                self.scenarios.insert(i, args[1])
                args = args[1:]
            elif re.findall(r'-e\d?$', args[0], flags=re.IGNORECASE):
                if len(args) < 2:
                    raise FatalConvertException('Event name must be specified after -e event argument. E.g. -e Q100')
                if re.findall(r'\d', args[0]):
                    i = int(re.findall(r'\d', args[0])[0]) - 1
                else:
                    i = 0
                self.scenarios.insert(i, args[1])
                args = args[1:]
            elif re.findall(r'-gpkg[_-]name', args[0], flags=re.IGNORECASE):
                if len(args) < 2:
                    raise FatalConvertException('GPKG name must be specified after -gpkg-name scenario argument. E.g. -gpkg-name model_gis')
                self.gpkg_name = self._arg_to_gpkg_name(args[1])
                args = args[1:]
            elif args[0].lower() == '-verbose':
                if len(args) < 2:
                    raise FatalConvertException('Verbose must be specified after -verbose argument. E.g. ON, OFF')
                self.verbose = 'high' if re.findall(r'(on)|(t(rue)?)|(1)', args[1], flags=re.IGNORECASE) else 'low'
            elif args[0].lower() == '-write-empties':
                self.write_empties = ''
                if len(args) >= 2 and args[1] and args[1][0] != '-':
                    self.write_empties = args[1].strip()
                    args = args[1:]
            elif args[0].lower() == '-crs':
                if len(args) < 2:
                    raise FatalConvertException('-crs flag must be followed by coordinate reference system reference e.g. "EPSG:32760"')
                args = args[1:]
                self.force_projection = True
                self.projection_wkt = arg_to_projection(args[0])
                if not self.projection_wkt:
                    self.force_projection = False
                    self.errors = True
                    print('Error reading/parsing crs argument')
            elif re.findall(r'tuf(?:low)?[_-]dir[_-]struct$', args[0], flags=re.IGNORECASE):
                self.tuf_dir_struct = True
            elif re.findall(r'tuf(?:low)?[_-]dir[_-]struct[_-]settings', args[0], flags=re.IGNORECASE):
                if len(args) < 2:
                    raise FatalConvertException('TUFLOW directory structure settings file must be specified after -tuf_dir_struct_settings argument')
                self.tuf_dir_struct_settings = json.loads(args[1])
                args = args[1:]
            elif args[0].lower() == '-always-use-root-dir':
                self.always_use_root_dir = True
            elif args[0].lower() == '-explode-multipart':
                self.explode_multipart = True

            args = args[1:]

        set_tuf_dir_struct(self.tuf_dir_struct_settings)

    def _arg_to_output_profile(self, arg):
        """Helper to convert OUTPUT PROFILE (-op) to the correct setting."""

        if re.findall(r'^(SEP(ARATE)?)$', arg.strip(' \t"\''), flags=re.IGNORECASE):
            return SEPARATE
        if re.findall(r'^((GROUPED[_\s-]BY[_\s-])?TCF)$', arg.strip(' \t"\''), flags=re.IGNORECASE):
            return GROUPED_BY_TCF
        if re.findall(r'^((GROUPED[_\s-]BY[_\s-])?CF[_\s-]?1?|(GROUPED[_\s-]BY\s)?CONTROL[_\s-]FILE[_\s-]?1?)$', arg.strip(' \t"\''), flags=re.IGNORECASE):
            return GROUPED_BY_CONTROL_FILE_1
        if re.findall(r'^((GROUPED[_\s-]BY[_\s-])?CF[_\s-]?2|(GROUPED[_\s-]BY\s)?CONTROL[_\s-]FILE[_\s-]?2)$', arg.strip(' \t"\''), flags=re.IGNORECASE):
            return GROUPED_BY_CONTROL_FILE_2

        return None

    def _arg_to_gpkg_name(self, arg):
        """Helper to convert argument to gpkg name - deal with extension etc"""

        name, suffix = os.path.splitext(os.path.basename(arg))
        if not suffix or suffix.lower() == '.gpkg':
            self.gpkg_out_name = name
        else:
            self.gpkg_out_name = f'{name}{suffix}'

    def _guess_root_folder(self):
        """Routine to find the root folder if one hasn't been given."""

        from .file import TuflowWindowsPath, TuflowPosixPath

        # see if there's a folder named TUFLOW up to 5 folders above TCF
        if not isinstance(self.tcf, TuflowWindowsPath) and not isinstance(self.tcf, TuflowPosixPath):
            return

        root = self.tcf.find_parent('TUFLOW', 5)
        if root:
            return root

        # adopt the folder above 'runs' or 'model' which ever is highest
        runs = self.tcf.find_parent('RUNS', 4)
        model = self.tcf.find_in_walk_dir('MODEL', 3, True)
        root = self.tcf.read_file_for_parent()

        if runs and model and root:  # indicates a standard TUFLOW model folder structure
            if len(root.parts) < len(runs.parent.parts) and len(root.parts) < len(model.parent.parts):
                return root
            if len(runs.parts) <= len(model.parts):
                return runs.parent
            else:
                return model.parent
        elif runs:
            if len(root.parts) < len(runs.parent.parts) or not runs.is_relative_to(root):
                return root
            return runs.parent
        elif model:
            if len(root.parts) < len(model.parent.parts) or not model.is_relative_to(root):
                return root
            return model.parent
        return root

    def _guess_empties_folder(self):
        """Routine to guess the empties folder."""
        from .gis import GIS_MIF, GIS_SHP
        from .file import change_gis_mi_folder, TuflowPath, tuflow_stnd_path

        # if using tuflow dir structure, location is pre-ordained
        if self.tuf_dir_struct:
            if self.output_gis_format == GIS_MIF:
                return self.output_folder / tuflow_stnd_path(None, 'mi/empty')
            else:
                return self.output_folder / tuflow_stnd_path(None, 'gis/empty')
        # first see if there is an existing empties folder
        if self.gis_folder:
            empty_folder = self.gis_folder / 'empty'
        else:
            empty_folder = self.root_folder.find_in_walk_dir('EMPTY', 0, True, self.output_folder_)
            gis_folder = self.root_folder.find_in_walk_dir('GIS', 0, True, self.output_folder_)
            mi_folder = self.root_folder.find_in_walk_dir('MI', 0, True, self.output_folder_)
            if not mi_folder or gis_folder:
                gis_folder = self.find_gis_folder(self.control_file)

        if empty_folder:
            empty_folder = change_gis_mi_folder(empty_folder, None, self.output_gis_format)
        elif gis_folder:
            empty_folder = change_gis_mi_folder(str(gis_folder) + os.sep, GIS_SHP, self.output_gis_format)
            empty_folder = TuflowPath(empty_folder) / 'empty'
        elif mi_folder:
            empty_folder = change_gis_mi_folder(str(mi_folder) + os.sep, GIS_MIF, self.output_gis_format)
            empty_folder = TuflowPath(empty_folder) / 'empty'
        else:
            return

        try:
            return self.output_folder / os.path.relpath(empty_folder, self.root_folder)
        except ValueError:
            return

    def is_grouped_database(self):
        """Will return whether the output profile is a grouped database."""

        return self.output_profile in (GROUPED_BY_TCF, GROUPED_BY_CONTROL_FILE_1, GROUPED_BY_CONTROL_FILE_2,
                                       GROUPED_TEMP)

    def get_model_name(self, tcf):
        """Extract the model name from the tcf minus all the wildcards."""

        from .file import TuflowPath

        p1 = r'[_\s]?~[es]\d?~'
        p2 = r'~[es]\d?~[_\s]?'
        m1 = re.sub(p1, '', tcf.name, flags=re.IGNORECASE)
        m2 = re.sub(p2, '', tcf.name, flags=re.IGNORECASE)
        if m1.count('_') != m2.count('_'):
            model_name = m1 if m1.count('_') > m2.count('_') else m2
        else:
            model_name = m1

        if model_name[-1] == '_':
            model_name = model_name[:-1]

        return str(TuflowPath(model_name).with_suffix(''))

    def copy_settings(self, control_file, output_file, command=None):
        """Copy the settings to a new object. Will update the settings based on the control file and output file."""

        from .file import TuflowPath

        cf_ = control_file
        if (command is not None and command.is_read_file()) or control_file.suffix.upper() == '.TRD':
            control_file = self.control_file.parent / control_file.name

        settings = ConvertSettings(None, convert_settings=self)
        if self.output_profile == GROUPED_BY_CONTROL_FILE_1:
            if control_file.suffix.upper() == '.TCF':
                settings.spatial_database = TuflowPath(
                    '..') / 'model' / 'gis' / f'{settings.gpkg_out_name}_{control_file.suffix.upper()[1:]}.gpkg'
            elif control_file.suffix.upper() in ['.TRD', '.TEF']:
                settings.spatial_database = self.spatial_database
            else:
                settings.spatial_database = TuflowPath(
                    'gis') / f'{settings.gpkg_out_name}_{control_file.suffix.upper()[1:]}.gpkg'
        elif self.output_profile == GROUPED_BY_CONTROL_FILE_2:
            if control_file.suffix.upper() == '.TCF':
                settings.spatial_database = TuflowPath('..') / TuflowPath('model') / TuflowPath(
                    'gis') / f'{settings.gpkg_out_name}_{control_file.suffix.upper()[1:]}.gpkg'
            elif control_file.suffix.upper() in ['.TRD', '.TEF'] or (command is not None and command.is_read_file()):
                if control_file.suffix.upper() == '.TEF':
                    name_ = f'{settings.gpkg_out_name}_{control_file.suffix.upper()[1:]}.gpkg'
                else:
                    name_ = f'{control_file.stem}_TRD.gpkg'
                gpkg_path = TuflowPath('..') / 'model' / 'gis' / name_
                try:
                    settings.spatial_database = os.path.relpath((control_file.parent / gpkg_path).resolve(), control_file.parent)
                except ValueError:
                    settings.spatial_database = gpkg_path
            else:
                settings.spatial_database = TuflowPath(
                    'gis') / f'{settings.gpkg_out_name}_{control_file.suffix.upper()[1:]}.gpkg'
        elif self.output_profile == GROUPED_BY_TCF:
            settings.spatial_database = TuflowPath('..') / TuflowPath('model') / TuflowPath('gis') / f'{self.gpkg_out_name}.gpkg'

        settings.control_file = control_file
        settings.control_file_out = output_file
        settings.command = command
        settings.parent_settings = self

        if self.need_to_write_spatial_database(settings, cf_):
            settings.written_spatial_database_header = False

        return settings

    def find_gis_folder(self, control_file):
        from .parser import get_commands
        from .file import TuflowPath
        for command in get_commands(control_file, self):
            if command.is_read_gis():
                return TuflowPath(command.value_expanded_path).parent
            elif command.is_control_file():
                gis_folder = self.find_gis_folder((control_file.parent / command.value).resolve())
                if gis_folder:
                    return gis_folder

    def need_to_write_spatial_database(self, settings, control_file=None):
        """Will return whether a SPATIAL DATABASE == .. command has already been written to the control file."""

        from .gis import GIS_GPKG, GRID_GPKG
        from .control_file import get_commands

        if control_file is None:
            control_file = settings.control_file

        gis_found = False
        for command in get_commands(control_file, settings):
            if command.is_read_gis() or command.is_read_grid() or command.is_read_projection():
                gis_found = True
                break

        if settings.output_gis_format == GIS_GPKG or settings.output_grid_format == GRID_GPKG:
            if settings.output_profile == GROUPED_BY_CONTROL_FILE_2:
                return gis_found
            if settings.output_profile == GROUPED_BY_CONTROL_FILE_1 and \
                    settings.control_file.suffix.upper() not in ['.TRD', '.TEF']:
                return gis_found
            if settings.output_profile == GROUPED_BY_TCF and settings.control_file.suffix.upper() == '.TCF':
                return True
        else:
            return False

    def read_tcf(self, scenarios=()):
        """Routine to make an initial read of the TCF to extract some settings."""

        from .parser import get_commands, EventCommand
        from .gis import GIS_GPKG, GIS_MIF, GIS_SHP, GRID_TIF, ogr_projection, gdal_format_2_ext, get_database_name
        from .file import globify, TuflowPath, replace_with_tuf_dir_struct

        if self.tcf is None:
            return
        self.control_file = self.tcf
        if self.tuf_dir_struct:
            self.control_file_out = replace_with_tuf_dir_struct(self.control_file, self.output_folder, None, None)
        else:
            self.control_file_out = self.output_folder / self.control_file.relative_to(self.root_folder)

        if scenarios:
            self.scenarios = scenarios[:]

        if (self.use_scenarios and self.scenarios) or self.resolve_var:  # if scenarios are specified we want to limit what is copied - so first thing is to grab variables
            copy_ = self.copy_settings(self.control_file, self.output_folder)
            for command in get_commands(self.tcf, copy_):
                if command.is_read_file():
                    self.read_file_for_variables((self.control_file.parent / command.value).resolve(), self)
                elif command.is_set_variable():
                    var_name, var_val = command.parse_variable()
                    if command.in_scenario_block() and not self.use_scenarios:  # this is for the tmf lib - if variable is in a scenario/event block then it can't be resolved straight away
                        continue
                    elif command.in_scenario_block() and not command.in_scenario_block(copy_.scenarios):  # don't read the variable if it's in a different scenario
                        continue
                    self.variables[var_name] = var_val

            self.variables = copy_.variables

        self.written_projection = False
        for command in get_commands(self.tcf, self):
            if self.scenarios and command.in_scenario_block() and not command.in_scenario_block(self.scenarios):
                continue

            event_command = EventCommand(command.original_text, self)

            if command.is_read_projection():
                if self.output_gis_format == GIS_GPKG:
                    if 'GPKG' in command.command:
                        self.written_projection = True
                if self.output_gis_format == GIS_SHP:
                    if 'SHP' in command.command:
                        self.written_projection = True
                if self.output_gis_format == GIS_MIF:
                    if 'MIF' in command.command:
                        self.written_projection = True
                if not self.projection_wkt:
                    self.projection_wkt = ogr_projection(command.get_gis_src_file())
                if 'gis' in command.get_gis_src_file().lower() or 'mi' in command.get_gis_src_file().lower():
                    tf_path = TuflowPath(command.get_gis_src_file())
                    gis_folder = tf_path.find_folder_in_path('gis')
                    if gis_folder:
                        self.gis_folder = gis_folder
                        continue
                    mi_folder = tf_path.find_folder_in_path('mi')
                    if mi_folder:
                        self.gis_folder = mi_folder

            elif command.is_grid_format():
                self.grid_format_command_exists = True
            elif command.is_spatial_database_command():
                self.process_spatial_database_command(command.value)
            elif command.is_event_file():
                self.read_tef((self.control_file.parent / command.value).resolve(), self)
            elif event_command.is_event_source():
                event_wildcard, _ = event_command.get_event_source()
                if event_wildcard is not None and re.escape(event_wildcard) not in self.wildcards:
                    self.wildcards.append(re.escape(event_wildcard))
            elif command.is_map_output_format():
                if re.findall(rf'{gdal_format_2_ext(self.output_grid_format).upper()[1:]}',
                                  command.value, flags=re.IGNORECASE):
                    self.map_output_grids = re.findall(rf'{gdal_format_2_ext(self.output_grid_format).upper()[1:]}',
                                                       command.value, flags=re.IGNORECASE)
                else:
                    self.map_output_grids = [f'{gdal_format_2_ext(self.output_grid_format).upper()[1:]}']
                if 'TIF' not in self.map_output_grids:
                    self.written_tif_projection = True
            elif self.output_grid_format == GRID_TIF and command.command == 'TIF PROJECTION':
                self.written_tif_projection = True
            elif self.output_grid_format == GRID_TIF and command.command == 'GEOMETRY CONTROL FILE':
                gcf = (self.tcf.parent / command.value).resolve()
                settings = self.copy_settings(gcf, gcf)
                if gcf.exists():
                    for g_command in get_commands(gcf, settings):
                        if g_command.is_spatial_database_command():
                            settings.read_spatial_database = command.value
                        elif g_command.is_read_grid():
                            for _ in g_command.iter_grid(settings):  # consider READ GRID ZPTS == GRID | POLYGON
                                # expand glob
                                try:
                                    rel_path = os.path.relpath(g_command.value, gcf.parent)
                                except ValueError:
                                    rel_path = g_command.value
                                rel_path = globify(rel_path, settings.wildcards)
                                for src_file in gcf.parent.glob(rel_path, settings.wildcards):
                                    db, _ = get_database_name(src_file)
                                    if self.tuf_dir_struct:
                                        db = replace_with_tuf_dir_struct(src_file, self.output_folder, None, 'grid')
                                        db, _ = get_database_name(db)
                                        self.tif_projection_path = os.path.relpath(TuflowPath(db).with_suffix('.tif'), self.control_file_out.parent)
                                    else:
                                        try:
                                            self.tif_projection_path = os.path.relpath(TuflowPath(db).with_suffix('.tif'), self.tcf.parent)
                                        except ValueError:
                                            self.tif_projection_path = TuflowPath(db)
                                    break
                                if self.tif_projection_path is not None:
                                    break
                        elif self.tif_projection_path is not None and self.gis_folder is not None:
                            break
                        elif g_command.is_read_gis() and not self.gis_folder:
                            for _ in g_command.iter_geom(settings):
                                try:
                                    rel_path = os.path.relpath(g_command.value, gcf.parent)
                                except ValueError:
                                    rel_path = g_command.value
                                rel_path = globify(rel_path, settings.wildcards)
                                for src_file in gcf.parent.glob(rel_path, settings.wildcards):
                                    gis_folder = src_file.find_folder_in_path('gis')
                                    if gis_folder:
                                        self.gis_folder = gis_folder
                                        continue
                                    mi_folder = src_file.find_folder_in_path('mi')
                                    if mi_folder:
                                        self.gis_folder = mi_folder

            elif command.is_output_zone():
                self.output_zones.extend(command.specified_output_zones())
            elif command.is_read_file():
                self.read_file((self.control_file.parent / command.value).resolve(), self)

        tcf_override = self.tuflow_override(self.tcf)
        if tcf_override:
            tcf, self.tcf = self.tcf, tcf_override
            self.read_tcf()
            self.tcf = tcf

        if self.write_empties is not None:
            if not self.projection_wkt:
                self.write_empties = None
                self.errors = True
                print('Error: "Projection == " command not found... not writing empty files.')

            if self.write_empties:
                self.write_empties = self.output_folder / self.write_empties
            elif self.write_empties is not None:
                self.write_empties = self._guess_empties_folder()
                if self.write_empties is None:
                    self.errors = True
                    print('Error: Could not guess directoy to write empty files... pass in relative path to write empties')

        self.read_spatial_database = None

    def read_tef(self, event_file, settings):
        """Routine to make an initial read of the TEF and extract wildcard names."""

        from .parser import get_event_commands

        for command in get_event_commands(event_file, settings):
            if command.is_event_source():
                event_wildcard, _ = command.get_event_source()
                if event_wildcard is not None and re.escape(event_wildcard) not in settings.wildcards:
                    settings.wildcards.append(re.escape(event_wildcard))
            elif command.is_output_zone():
                self.output_zones.extend(command.specified_output_zones())


    def read_file(self, read_file, settings):
        from .control_file import get_commands

        for command in get_commands(read_file, settings):
            if command.is_output_zone():
                self.output_zones.extend(command.specified_output_zones())

    def read_file_for_variables(self, read_file, settings):
        from .control_file import get_commands

        for command in get_commands(read_file, settings):
            if command.is_set_variable():
                var_name, var_val = command.parse_variable()
                self.variables[var_name] = var_val

    def process_spatial_database_command(self, value):
        """Process a SPATIAL DATABASE command and set the read spatial database setting to an appropriate value."""

        value = str(value)

        if value.upper() == 'TCF':
            self.read_spatial_database = self.read_spatial_database_tcf
        elif value.upper() == 'NONE':
            self.read_spatial_database = None
            self.read_spatial_database_tcf = None
        else:
            self.read_spatial_database = (self.control_file.parent / value).resolve()

        if self.control_file.suffix.upper() == '.TCF':
            self.read_spatial_database_tcf = self.read_spatial_database

    def create_empty_folders(self):
        if self.tuf_dir_struct:
            for relpath in tuf_dir_struct.get('always_create', []):
                p = self.output_folder / relpath
                if not p.exists():
                    print('Making empty folder: ', p.resolve())
                    p.mkdir(parents=True, exist_ok=True)

    def copy_global_values(self, other_settings):
        if not other_settings:
            return
        if other_settings.check_file_prefix_2d:
            self.check_file_prefix_2d = other_settings.check_file_prefix_2d
        if other_settings.check_file_prefix_1d:
            self.check_file_prefix_1d = other_settings.check_file_prefix_1d

    def tuflow_override(self, tcf):
        from .file import TuflowPath
        if TuflowPath(tcf).stem.lower().startswith('_tuflow_override'):
            return
        compname = platform.node()
        tcf_override = TuflowPath(tcf).parent / f'_TUFLOW_Override_{compname}.tcf'
        if tcf_override.exists():
            return tcf_override
        tcf_override = TuflowPath(tcf).parent / f'_TUFLOW_Override.tcf'
        if tcf_override.exists():
            return tcf_override

    def tuflow_override_iter(self, tcf):
        from .file import TuflowPath
        tcf_override = TuflowPath(tcf).parent / f'_TUFLOW_Override.tcf'
        if tcf_override.exists():
            yield tcf_override
        for tcf_override in TuflowPath(tcf).parent.glob(f'_TUFLOW_Override_*.tcf'):
            yield tcf_override

