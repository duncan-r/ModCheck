import re
import os
import sys
from copy import deepcopy
from pathlib import Path

from .stubs import ogr
from itertools import permutations
from .file import (add_geom_suffix, remove_geom_suffix, change_gis_mi_folder, tuflowify_value,
                   replace_with_output_filepath, get_geom_suffix, globify, TuflowPath,
                   insert_variables, expand_path,
                   replace_with_tuf_dir_struct)
from .settings import MinorConvertException, SEPARATE, GROUPED_TEMP, ConvertSettings
from .gis import (GIS_UNKNOWN, GIS_GPKG, GIS_MIF, GIS_SHP, GRID_ASC, GRID_FLT, GRID_GPKG, GRID_TIF, GRID_NC,
                  ogr_format, ogr_format_2_ext, gdal_format_2_ext,
                  ogr_iter_geom, geom_type_2_suffix, get_database_name)


CONTROL_FILES = [
    'GEOMETRY CONTROL FILE', 'BC CONTROL FILE', 'ESTRY CONTROL FILE', 'EVENT FILE', 'READ FILE',
    'RAINFALL CONTROL FILE', 'EXTERNAL STRESS FILE', 'QUADTREE CONTROL FILE', 'AD CONTROL FILE',
    'ESTRY CONTROL FILE AUTO', 'SWMM CONTROL FILE'
    ]


class Command:
    """Class for handling TUFLOW command."""

    def __init__(self, line, settings):
        self.comment_index = 0
        self.prefix = ''
        self.original_text = line
        self.command_orig, self.value_orig = self.strip_command(line)
        self.iter_geom_index = -1
        self.geom_count = 0
        self.multi_geom_db = None
        self.in_define_block = False
        self._define_blocks = []
        self.auto_estry = False
        self.auto_estry_old = False
        # self.settings = deepcopy(settings)
        self.settings = ConvertSettings(convert_settings=settings)
        self.empty_geom = None
        self.check_file_prefix = None

        self.command = self.command_orig.upper() if self.command_orig is not None else None

        abs_path = re.findall(r'(([A-Za-z]:\\)|\\\\)', str(self.value_orig)) and sys.platform == 'win32'
        if not abs_path and self.is_value_a_file() and str(self.value_orig)[0] in ['\\', '/']:
            self.value_orig = f'.{self.value_orig}'

        if self.is_read_gis() or (self.is_read_grid() and not self.is_rainfall_grid_nc()) or self.is_read_projection():
            self.value = tuflowify_value(self.value_orig, settings)
            self.value_expanded_path = expand_path(self.value, settings, gis_file=True)
        elif self.is_read_tin():
            self.value = tuflowify_value(self.value_orig, settings)
            self.value = TuflowPath(str(self.value).split(' >> ')[0])
            self.value_expanded_path = expand_path(self.value, settings)
        elif self.is_value_a_file():
            self.value = TuflowPath(insert_variables(self.value_orig, settings.variables))
            self.value_ = tuflowify_value(self.value_orig, settings)
            self.value_ = TuflowPath(str(self.value_).split(' >> ')[0])
            self.value_expanded_path = expand_path(self.value_, settings)
        elif self.is_value_a_folder():
            self.value = TuflowPath(insert_variables(self.value_orig, settings.variables))
            self.value_ = tuflowify_value(self.value_orig, settings, True)
            self.value_ = TuflowPath(str(self.value_).split(' >> ')[0]).with_suffix('')
            self.value_expanded_path = expand_path(self.value_, settings)
        else:
            self.value = insert_variables(self.value_orig, settings.variables)
            self.value_expanded_path = self.value

        if self.is_control_file() and str(self.value).upper() == 'AUTO' or self.command == 'ESTRY CONTROL FILE AUTO':
            self.auto_estry = True
            self.auto_estry_old = self.command == 'ESTRY CONTROL FILE AUTO'
            self.value = settings.control_file.with_suffix('.ecf').name
            self.value_ = tuflowify_value(str(self.value), settings)
            self.value_ = TuflowPath(str(self.value).split(' >> ')[0])
            self.value_expanded_path = expand_path(self.value, settings)

        if self.is_spatial_database_command():
            settings.process_spatial_database_command(self.value)
            self.settings.process_spatial_database_command(self.value)

        if self.is_check_folder():
            self.check_file_prefix = self.check_folder_prefix()  # local to this command (i.e. not aware if referring to 1d or 2d)

    def __str__(self):
        return self.original_text

    @property
    def define_blocks(self):
        return self._define_blocks

    @define_blocks.setter
    def define_blocks(self, value):
        if value:
            self._define_blocks = value
        # update anything that this may affect
        if self.is_check_folder():
            self.set_check_folder_prefix()


    def count_geom(self, settings):
        """
        Returns the number of geometry types in the READ GIS command.

        E.g.
         - MIF file with 2 geometry types will return 2
         - "gis\\shape_file_L.shp | gis\\shape_file_P.shp" - will return 2
        """

        count = 0
        for i, value in enumerate(str(self.value).split('|')):
            value = tuflowify_value(value.strip(), settings)
            if self.is_value_a_number(value=value, iter_index=i):
                pass
            elif self.is_modify_conveyance() and i > 0:
                pass
            elif self.gis_format(settings, value) != GIS_MIF:
                count += 1
            else:
                for _ in ogr_iter_geom(value):
                    count += 1

        return count

    def iter_geom(self, settings):
        """
        Iterate through the geometry types in the READ GIS command.

        While iterating, self.value can be modified so that each geometry on the line is considered separately.

        E.g.
         - for a mif file containing points an lines - will return all points, then next iteration will return lines.
        """

        value_orig = self.value  # store original value
        self.geom_count = self.count_geom(settings)
        self.empty_geom = False
        for value in str(self.value).split('|'):
            if not value.strip():
                continue

            # change value so that other routines will work automatically
            self.value = tuflowify_value(value.strip(), settings)

            # store the database so if converting to gpkg can all be written to the same file
            if self.multi_geom_db is None:
                self.multi_geom_db, _ = get_database_name(self.value)
                self.multi_geom_db = TuflowPath(self.multi_geom_db).with_suffix('.gpkg')

            self.iter_geom_index += 1
            if self.is_value_a_number(value=value):
                self.value = value.strip()
                yield 'VALUE'
            elif self.is_modify_conveyance() and self.iter_geom_index > 0:
                self.command = re.sub(r'(?<=\s)GIS(?=\s)', 'GRID', self.command)
                yield 'GRID'
            elif self.gis_format(settings) != GIS_MIF:
                yield None
            else:  # for mif files, need to open the file and see what's in there
                self.iter_geom_index -= 1  # wind back one and iterate through layer
                i = -1
                for i, geom_type in enumerate(ogr_iter_geom(self.get_gis_src_file())):
                    self.iter_geom_index += 1
                    yield geom_type
                if i == -1:
                    self.empty_geom = True

        # reset all these values
        self.value = value_orig
        self.iter_geom_index = -1
        self.multi_geom_db = None

    def iter_grid(self, settings):
        """Iterate READ GRID command values - this is to handle READ GRID == grid | polygon"""

        if '|' in str(self.value):
            value_orig = self.value
            self.geom_count = 2

            grid, gis = [x.strip() for x in str(self.value).split('|', 1)]

            self.value = tuflowify_value(grid.strip(), settings)
            self.iter_geom_index += 1
            yield 'GRID'

            command_orig = self.command
            self.command = 'READ GIS'  # trick into thinking this is now a READ GIS
            self.value = tuflowify_value(gis.strip(), settings)

            if self.gis_format(settings) == GIS_MIF:
                for geom_type in ogr_iter_geom(self.get_gis_src_file()):
                    if geom_type == ogr.wkbPolygon:
                        self.iter_geom_index += 1
                        yield geom_type
            else:
                self.iter_geom_index += 1
                yield None

            # reset all these values
            self.value = value_orig
            self.command = command_orig
            self.iter_geom_index = -1

        else:
            yield 'GRID'

    def iter_tin(self, settings):
        if '|' in str(self.value):
            value_orig = self.value
            self.geom_count = 2

            tin, gis = [x.strip() for x in self.value.split('|', 1)]

            if settings.control_file:
                self.value = (settings.control_file.parent / tin).resolve()
            else:
                self.value = tin.strip()
            self.iter_geom_index += 1
            yield 'TIN'

            command_orig = self.command
            self.command = 'READ GIS'  # trick into thinking this is now a READ GIS
            self.value = tuflowify_value(gis.strip(), settings)

            if self.gis_format(settings) == GIS_MIF:
                for geom_type in ogr_iter_geom(self.get_gis_src_file()):
                    if geom_type == ogr.wkbPolygon:
                        self.iter_geom_index += 1
                        yield geom_type
            else:
                self.iter_geom_index += 1
                yield None

            # reset all these values
            self.value = value_orig
            self.command = command_orig
            self.iter_geom_index = -1

        else:
            yield 'TIN'

    def iter_files(self, settings):
        if settings.control_file is None:
            return
        if self.is_read_gis() or (self.is_read_grid() and not self.is_rainfall_grid_nc()) or self.is_read_projection() or self.is_read_tin():
            try:
                rel_path = os.path.relpath(self.value, settings.control_file.parent)
            except ValueError:
                rel_path = self.value
        elif self.is_value_a_file():
            try:
                rel_path = os.path.relpath(self.value_, settings.control_file.parent)
            except ValueError:
                rel_path = self.value_
        else:
            rel_path = TuflowPath(self.value)
        if not settings.use_scenarios or not re.findall(r'<<~?[s]\d?~?>>', str(rel_path), flags=re.IGNORECASE):
            rel_path = globify(rel_path, settings.wildcards)
            for file in settings.control_file.parent.glob(rel_path, settings.wildcards):
                yield file
        else:
            wild_cards = list(set([x.strip() for x in re.findall(r'<<~?s\d?~?>>', str(rel_path), flags=re.IGNORECASE)]))
            if wild_cards and not settings.scenarios:
                return
            if len(wild_cards) > len(settings.scenarios):
                scenarios = settings.scenarios + ['*' for x in range(len(wild_cards) - len(settings.scenarios))]
            else:
                scenarios = settings.scenarios[:]

            files = []
            for i in range(len(scenarios) - len(wild_cards) + 1):
                scenario_slice = scenarios[i:i+len(wild_cards)]
                for perm in permutations(scenario_slice):
                    rp = str(rel_path)
                    for wc, s in zip(wild_cards, perm):
                        rp = re.sub(re.escape(wc), s, rp, flags=re.IGNORECASE)
                    rp = globify(rp, settings.wildcards)
                    for file in settings.control_file.parent.glob(rp, settings.wildcards):
                        if file not in files:
                            yield file
                            files.append(file)

    def gis_format(self, settings, value=None):
        """
        Return GIS vector format as an OGR Format driver name (.e.g. 'ESRI Shapefile')
        of input file in READ GIS command.
        """

        if not self.is_valid() or self.value is None and not self.is_read_gis():
            return None

        no_ext_is_gpkg = settings.read_spatial_database is not None \
                          and settings.no_ext != GIS_MIF or settings.no_ext == GIS_GPKG
        no_ext_is_mif = settings.read_spatial_database is None \
                        and settings.no_ext != GIS_GPKG or settings.no_ext == GIS_MIF

        if value is None:
            value = self.value

        return ogr_format(value, no_ext_is_mif, no_ext_is_gpkg)

    def needs_grouped_database(self, settings):
        """Returns whether the converted output GIS file is going to a grouped database."""

        return settings.is_grouped_database() and (
                (self.is_read_gis() and settings.output_gis_format == GIS_GPKG) or
                (self.is_read_grid() and settings.output_grid_format == GRID_GPKG) or
                (self.is_read_projection() and settings.output_gis_format == GIS_GPKG)) and \
                not self.is_read_tin()

    def is_one_line_multi_layer(self, settings):
        """
        Returns True/False if the multiple output GIS layers
        are going to be written to one line - also outputs true only if each layer needs a full path
        """

        return self.is_read_gis() and self.geom_count > 1 and not self.needs_grouped_database(settings)

    def get_gis_src_file(self, db=True, lyrname=True, combine=None):
        """Returns full path to GIS input file in a 'database >> layername' format even if not required."""

        if db and lyrname:
            if combine is None:
                if self.is_mi_prj_string():
                    return self.value_orig
                return self.value
            else:
                if 'generate_from_db' in combine:
                    return f'{combine["generate_from_db"]} >> {TuflowPath(combine["generate_from_db"]).with_suffix("").name}'
                elif 'db' in combine and 'lyrname' in combine:
                    return f'{combine["db"]} >> {combine["lyrname"]}'
                elif 'db' in combine:
                    return f'{combine["db"]} >> {get_database_name(self.value)[1]}'
                elif 'lyrname' in combine:
                    return f'{get_database_name(self.value)[0]} >> {combine["lyrname"]}'
                else:
                    return self.value
        elif not lyrname:
            return get_database_name(self.value)[0]
        elif not db:
            return get_database_name(self.value)[1]

    def get_gis_dest_file(self, input_file, settings, geom=None, return_relative=False):
        """Returns full path to GIS output file in a 'database >> layername' format even if not required."""

        try:
            # input database and layer name
            db, lyr = get_database_name(input_file)
            mi_prj_string = False
            if self.is_mi_prj_string():
                gis_format = GIS_MIF
                mi_prj_string = True
                if settings.output_gis_format == GIS_MIF:
                    return self.value_orig
                lyr = 'projection'
            else:
                gis_format = GIS_UNKNOWN if self.is_read_xf() or (self.is_prj_file() and settings.output_gis_format == GIS_SHP) else GIS_GPKG  # either GIS_UNKNOWN or anything else

            if not self.needs_grouped_database(settings) and TuflowPath(db).stem != lyr and gis_format != GIS_UNKNOWN:
                # don't name the file after the database - name it after the layer
                db = (TuflowPath(db).parent / lyr).with_suffix(TuflowPath(db).suffix)
                if self.geom_count > 1 and settings.output_gis_format == GIS_GPKG:
                    db = remove_geom_suffix(db)
                    if self.iter_geom_index == 0:
                        self.multi_geom_db = db

            if geom and gis_format != GIS_UNKNOWN:  # if there is a geom type, make sure it's added to the lyr name
                lyr = add_geom_suffix(lyr, geom_type_2_suffix(geom))
                if settings.output_gis_format != GIS_GPKG or self.geom_count < 2:
                    db = add_geom_suffix(db, geom_type_2_suffix(geom))

            if self.is_one_line_multi_layer(settings) and gis_format != GIS_UNKNOWN:
                # temporarily switch this to a single database so that output GIS files are written to a single database
                settings.spatial_database = remove_geom_suffix(self.multi_geom_db)
                if re.findall(settings.wildcards[0], str(settings.spatial_database)):
                    settings.spatial_database = TuflowPath(remove_geom_suffix(get_database_name(input_file)[0])).with_suffix('.gpkg')
                settings.output_profile = GROUPED_TEMP

            # figure out the output database
            if self.needs_grouped_database(settings) and settings.spatial_database is not None and gis_format != GIS_UNKNOWN:
                db = (settings.control_file.parent / settings.spatial_database).resolve()
            elif self.is_read_tin() and gis_format != GIS_UNKNOWN:
                pass
            elif mi_prj_string:
                if settings.output_gis_format == GIS_MIF:
                    return lyr
                db = (TuflowPath(db).parent / 'projection').with_suffix(ogr_format_2_ext(settings.output_gis_format))
            elif (self.is_read_gis() or self.is_read_projection()) and gis_format != GIS_UNKNOWN:
                db = TuflowPath(db).with_suffix(ogr_format_2_ext(settings.output_gis_format))
            elif gis_format != GIS_UNKNOWN:
                db = TuflowPath(db).with_suffix(gdal_format_2_ext(settings.output_grid_format))

            # for control file text, return relative reference
            control_file = None
            if return_relative:
                control_file = settings.control_file

            # convert input filepath to output filepath
            db = replace_with_output_filepath(db, settings.root_folder, settings.output_folder, control_file)
            if self.is_read_gis() or self.is_read_projection():
                input_gis_format = ogr_format(input_file)
                db = change_gis_mi_folder(db, input_gis_format, settings.output_gis_format)  # change any mi folder to gis (and vise/versa)
                if settings.output_profile == GROUPED_TEMP:  # reset these values
                    settings.spatial_database = None
                    settings.output_profile = SEPARATE

            if settings.tuf_dir_struct:
                db = replace_with_tuf_dir_struct(Path(db), settings.output_folder, self, None)
                if return_relative:
                    if settings.command is not None and settings.command.is_read_file():
                        db = os.path.relpath(db, settings.parent_settings.control_file_out.parent)
                    else:
                        db = os.path.relpath(db, settings.control_file_out.parent)

            return TuflowPath(f'{db} >> {lyr}')

        except Exception as e:
            settings.errors = True
            raise MinorConvertException(f'Error: {e}')

    def is_spatial_database_command(self):
        """Returns True/False if command is setting the spatial database."""

        return self.command == 'SPATIAL DATABASE'

    def make_new_text(self, settings, geom=None, comment_use_rel_gap: bool = False):
        """Generate new text to be inserted into the control file."""

        if not self.is_valid():
            return self.original_text

        if self.iter_geom_index > 0:  # multi GIS layer on single line and not the first layer
            text = f' | {self.make_new_value(settings, geom)}'
        elif self.value is None or self.auto_estry_old:
            text = f'{self.make_new_command(settings)}'
        else:
            text = f'{self.make_new_command(settings)} == {self.make_new_value(settings, geom)}'

        if self.is_read_gis() or self.is_read_grid() or self.is_read_tin():
            return text  # add comments only after whole line has been completed (in case of multiple layers)
        else:
            return self.re_add_comments(text, comment_use_rel_gap)

    def re_add_comments(self, new_command, rel_gap = False):
        """Re-add any comments after the command - try and maintain their position as best as possible."""

        if self.comment:
            if len(new_command) >= self.comment_index and not rel_gap:
                self.comment_index = len(new_command) + 1
            if rel_gap and self.comment_index > 0:
                i = self.comment_index - 1
                orig_text = self.original_text.replace('\t', '    ')
                while i + 1 > len(orig_text) or orig_text[i] == ' ' and i > 0:
                    if orig_text[i] == ' ':
                        i -= 1
                dif = max(self.comment_index - i - 1, 1)
            else:
                dif = self.comment_index - len(new_command)
            new_command = f'{new_command}{" " * dif}{self.comment}'

        return f'{new_command}\n'

    def make_new_value(self, settings, geom=None):
        """Generate a new value for the output control file text 'command == value'"""

        if self.value is None:
            return None

        outpath = self.value

        try:
            # get the output path
            if self.is_value_a_number(value=self.value):
                db, lyr = get_database_name(self.value)
                if self.iter_geom_index == 0:
                    return lyr
                else:
                    return str(TuflowPath(db).name)
            elif self.is_read_gis() or (self.is_read_grid() and not self.is_rainfall_grid_nc()) or self.is_read_projection() or self.is_read_tin():
                outpath = self.get_gis_dest_file(self.value, settings, geom, return_relative=True)
            else:
                if isinstance(self.value, str) or isinstance(self.value, TuflowPath):
                    if settings.tuf_dir_struct and (self.is_value_a_file() or self.is_value_a_folder()):
                        outpath = replace_with_tuf_dir_struct(self.value, settings.output_folder, self, None)
                        outpath = os.path.relpath(outpath, settings.control_file_out.parent)
                        if self.is_check_folder():
                            outpath = f'{outpath}{os.sep}'
                    else:
                        outpath = str(TuflowPath(self.value))

            if self.is_read_gis() or self.is_read_projection():
                db, lyr = get_database_name(outpath)
                if ogr_format(db) != GIS_UNKNOWN and settings.output_gis_format == GIS_GPKG and settings.is_grouped_database():
                    return TuflowPath(lyr)
                elif TuflowPath(db).stem.lower() != lyr.lower():
                    return outpath
                else:
                    return TuflowPath(db)

            if self.is_read_grid():
                db, lyr = get_database_name(outpath)
                if settings.output_grid_format == GRID_GPKG and settings.is_grouped_database():
                    return TuflowPath(lyr)
                elif TuflowPath(db).with_suffix('').name != lyr:
                    return self.value
                else:
                    return TuflowPath(db)

            if self.is_read_tin():
                db, lyr = get_database_name(outpath)
                return TuflowPath(db)

            if self.is_gis_format():
                if settings.output_gis_format == GIS_GPKG:
                    return 'GPKG'
                if settings.output_gis_format == GIS_MIF:
                    return 'MI'
                if settings.output_gis_format == GIS_SHP:
                    return 'SHP'
            elif self.is_grid_format():
                if settings.output_grid_format == GRID_ASC:
                    return 'ASC'
                if settings.output_grid_format == GRID_FLT:
                    return 'FLT'
                if settings.output_grid_format == GRID_GPKG:
                    return 'GPKG'
                if settings.output_grid_format == GRID_TIF:
                    return 'TIF'
                if settings.output_grid_format == GRID_NC:
                    return 'NC'

            if self.is_map_output_format():
                if not re.findall(rf'{gdal_format_2_ext(settings.output_grid_format).upper()[1:]}',
                                  self.value, flags=re.IGNORECASE):
                    return re.sub(r'(ASC|FLT|GPKG|TIF|NC)',
                                  f'{gdal_format_2_ext(settings.output_grid_format).upper()[1:]}',
                                  self.value, flags=re.IGNORECASE)

            if settings.use_scenarios and self.is_start_define() and self.define_blocks[-1].type in ['SCENARIO', 'EVENT']:
                scenarios_upper = [x.upper() for x in settings.scenarios]
                return ' | '.join([x.strip() for x in self.value.split('|') if x.upper().strip() in scenarios_upper])

            if self.auto_estry:
                return self.value_orig

        except Exception as e:
            settings.errors = True
            raise MinorConvertException(f'Error: {e}')

        return outpath

    def make_new_command(self, settings):
        """Generate a new command for the output control file text 'command == value'"""

        if self.is_read_projection():
            return f'{self.prefix}{self.new_prj_command(settings)}'

        if self.is_read_gis():
            return f'{self.prefix}{self.new_gis_command(settings)}'

        if self.is_map_output_setting():
            return f'{self.prefix}{self.new_map_output_setting_command(settings)}'

        if self.command[:4] == 'ELSE' and not self.first_scenario_if_written():
            self.set_first_scenario_if_written(True)
            if 'IF' in self.command:
                return f'{self.prefix}{self.command_orig[4:]}'
            else:
                return f'{self.prefix}{self.new_if_statement_for_else_block()}\n{self.prefix}{self.command_orig}'

        return f'{self.prefix}{self.command_orig}'

    def new_gis_command(self, settings):
        if settings.output_gis_format != GIS_MIF:
            return re.sub(r'(?<=\s)MI(?=\s)', 'GIS', self.command_orig, flags=re.IGNORECASE)

        return self.command_orig

    def new_prj_command(self, settings):
        """Output projection command."""
        if settings.output_gis_format == GIS_MIF:
            return 'MI Projection'
        else:
            return f'{ogr_format_2_ext(settings.output_gis_format).upper()[1:]} Projection'

    def new_map_output_setting_command(self, settings):
        """
        New grid specific map output setting command.

        e.g. ASC MAP OUTPUT INTERVAL -> TIF MAP OUTPUT INTERVAL
        """

        grid_type = re.findall(r'(ASC|FLT|GPKG|TIF|NC)', self.command)
        if not grid_type:
            return self.command_orig

        grid_type = grid_type[0]

        if grid_type in settings.map_output_grids:
            return self.command_orig

        return re.sub(rf'{grid_type}', f'{gdal_format_2_ext(settings.output_grid_format).upper()[1:]}',
                      self.command_orig, flags=re.IGNORECASE)

    def is_valid(self):
        """Returns if command contains a valid command (i.e. not a comment or blank)."""

        return self.command is not None

    def is_control_file(self):
        """Returns whether command is referencing a control file."""
        if self.command and re.findall(r'^READ\s', str(self.command)) and self.command != 'READ FILE':
            cmd = re.sub(r'^READ\s', '', self.command)
        else:
            cmd = self.command
        return cmd in CONTROL_FILES and self.value is not None and TuflowPath(self.value).suffix.upper() != '.CSV'

    def is_event_file(self):
        """Return whether command is referencing the TUFLOW EVENT FILE."""

        return self.command == 'EVENT FILE'

    def is_quadtree_control_file(self):
        """Return whether command is referencing QUADTREE CONTROL FILE."""

        return self.command == 'QUADTREE CONTROL FILE'

    def is_quadtree_single_level(self):
        """Return whether command is referencing a single level quadtree domain."""

        return self.is_quadtree_control_file() and self.value.upper() == 'SINGLE LEVEL'

    def is_bc_dbase_file(self):
        """Returns whether command is referencing the bc_dbase.csv."""

        return self.command == 'BC DATABASE' or self.command == 'AD BC DATABASE'

    def is_pit_inlet_dbase_file(self):
        """Returns whether command is referecing the pit_inlet_dbase.csv"""

        return self.command and ('PIT INLET DATABASE' in self.command or 'DEPTH DISCHARGE DATABASE' in self.command)

    def is_rainfall_grid(self):
        """Returns whether command is referencing READ GRID RF"""

        return self.is_rainfall_grid_nc() or self.is_rainfall_grid_csv()

    def is_rainfall_grid_csv(self):
        """Returns whether the command is referencing READ GRID RF == CSV"""

        return self.command == 'READ GRID RF' and self.value is not None \
               and self.value.suffix.upper() == '.CSV'

    def is_rainfall_grid_nc(self):
        """Returns whether the command is referencing READ GRID RF == NC"""

        return self.command == 'READ GRID RF' and self.value_orig is not None \
               and TuflowPath(self.value_orig).suffix.upper() == '.NC'

    def is_prj_file(self):
        return self.is_valid and self.is_read_projection() and TuflowPath(self.value_orig).suffix.upper() == '.PRJ'

    def is_read_xf(self):
        return self.is_valid and self.value_orig and TuflowPath(self.value_orig).suffix.upper() in ['.XF4', '.XF8']

    def is_read_swmm_inp(self):
        return self.is_valid and self.value_orig and self.command == 'READ SWMM'

    def is_read_gis(self):
        """Returns whether command is a 'READ GIS' command."""

        return self.is_valid() \
               and ('READ GIS' in self.command or 'CREATE TIN ZPTS' in self.command or 'READ MI' in self.command or
                    'READ MID' in self.command)

    def is_read_grid(self):
        """Returns whether command is a 'READ GRID' command."""

        return self.is_valid() and 'READ GRID' in self.command and self.value_orig is not None \
               and TuflowPath(self.value_orig).suffix.upper() != '.CSV' and 'RF' not in self.command

    def is_read_file(self):
        """Returns whether command is a 'READ FILE' command."""

        return self.command == 'READ FILE'

    def is_read_tin(self):
        """Returns whether command is a 'READ TIN' command."""

        return self.is_valid() and 'READ TIN' in self.command

    def is_log_folder(self):
        """Returns whether command is a 'LOG FILE' command."""

        return self.is_valid() and self.command == 'LOG FOLDER'

    def is_output_folder(self):
        """Returns whether command is a 'OUTPUT FOLDER' command."""

        return self.is_valid() and bool(re.findall(r'(1D\s+)?OUTPUT FOLDER$', self.command))

    def is_check_folder(self):
        """Returns whether command is a 'CHECK FOLDER' command."""

        return self.is_valid() and bool(re.findall(r'(1D\s+)?WRITE CHECK FILES?$', self.command)) and 'OFF' not in self.value_orig

    def check_folder_prefix(self):
        check_file_prefix = None
        if self.value_orig and self.value_orig[-1] in ['\\', '/']:
            return
        elif self.value_orig:
            p = Path(self.value_orig)
            return p.stem

    def set_check_folder_prefix(self):
        check_file_prefix = self.check_folder_prefix()
        if check_file_prefix:
            if self.settings.control_file.suffix.lower() == '.tcf' and '1D' not in self.command and '1D DOMAIN' not in [x.type for x in sum([], self.define_blocks)]:
                self.settings.check_file_prefix_2d = check_file_prefix
                if not self.settings.check_file_prefix_1d:
                    self.settings.check_file_prefix_1d = check_file_prefix
            else:
                self.settings.check_file_prefix_1d = check_file_prefix

    def is_value_a_folder(self):
        return self.is_log_folder() or self.is_output_folder() or self.is_check_folder()

    def is_value_a_file(self):
        """
        Returns whether the value is pointing to a file.

        E.g.
        Can include 'Read Materials == CSV/TMF' or 'Read Soils == TSOILF'
        """

        return self.value_orig is not None and TuflowPath(self.value_orig).suffix and not self.is_value_a_number() \
            and not self.is_value_a_number_tuple() and not self.is_start_define()

    def is_mi_prj_string(self):
        return self.command is not None and self.value_orig and self.value_orig.startswith('CoordSys')

    def is_read_projection(self):
        """Returns whether command is a set model projection command."""

        return self.command is not None and 'PROJECTION' in self.command and 'CHECK' not in self.command \
            and (bool(re.findall(r'\.(shp)|(prj)|(mi)|(gpkg)', str(self.value_orig), flags=re.IGNORECASE)) or
                 TuflowPath(self.value_orig).suffix == '' or self.is_mi_prj_string())

    def is_value_a_number(self, value=None, iter_index=None):
        """Returns whether the value of the command is a number."""

        if not self.is_valid() or not self.value_orig:
            return False

        if iter_index is None:
            iter_index = self.iter_geom_index

        try:
            if value is not None:
                float(value)
            else:
                float(str(self.value_orig))
            return True
        except (ValueError, TypeError):
            if iter_index == 1 and re.findall('^<<.+?>>$', value.strip()) and re.findall('<<.+?>>', value)[0] == value.strip():
                return True
            return False

    def return_number(self, value):
        if self.is_set_code() or self.is_set_mat() or self.is_set_soil():
            return int(value)
        else:
            return float(value)

    def is_value_a_number_tuple(self, value=None, iter_index=None):
        if not self.is_valid() or not self.value_orig:
            return False

        if iter_index is None:
            iter_index = self.iter_geom_index

        try:
            if value is not None:
                db, lyr = get_database_name(value)
                if re.match(r'\d+(?:\.\d+)?(,\s?\d+(?:\.\d+)?)+', lyr):
                    return True
                try:
                    if TuflowPath(db).suffix:
                        return False
                except:
                    pass
                try:
                    values = re.split(r',\s?|\s+|\t+', lyr)
                    [float(v) for v in values]
                except (TypeError, ValueError):
                    values = re.split(r',\s?|\s+|\t+', str(TuflowPath(db).name))
                    [float(v) for v in values]
            else:
                values = re.split(r',\s?|\s+|\t+', self.value_orig)
                [float(v) for v in values]
            return True
        except (TypeError, ValueError):
            return False

    def return_number_tuple(self, value):
        values = re.split(r',\s?|\s+|\t+', value)
        return tuple([float(x) for x in values])

    def is_map_output_format(self):
        """
        Returns whether command is READ MAP OUTPUT FORMAT and
        contains any output grids formats that should be converted.
        """

        if self.command == 'MAP OUTPUT FORMAT':
            return re.findall(r'(ASC|FLT|GPKG|TIF|NC)', self.value, flags=re.IGNORECASE)

        return False

    def is_map_output_setting(self):
        """
        Returns whether command is a setting for a grid map output

        e.g. ASC Map Output Interval
        """

        return 'MAP OUTPUT INTERVAL' in self.command or 'MAP OUTPUT DATA TYPES' in self.command \
               and re.findall(r'(ASC|FLT|GPKG|TIF|NC)', self.command)

    def is_table_link(self):
        """Returns whether READ GIS command is also a Read GIS Table Links command."""

        return self.is_valid() and self.is_read_gis() and 'TABLE LINK' in self.command

    def is_z_shape(self):
        """Returns whether READ GIS command is also a READ GIS Z SHAPE command."""

        return self.is_valid() and self.is_read_gis() \
               and ('Z SHAPE' in self.command or 'Z LINE' in self.command or 'CREATE TIN ZPTS' in self.command)

    def is_2d_zpts(self):
        """Returns whether READ GIS command is also a READ GIS Zpts command."""

        return self.is_valid() and (self.is_read_gis() or self.is_read_grid) \
               and 'ZPTS' in self.command

    def is_modify_conveyance(self):
        """Returns whether READ GIS command is also a READ GIS Zpts Modify Conveyance command."""

        return self.is_2d_zpts() and 'MODIFY CONVEYANCE' in self.command

    def is_2d_lfcsh(self):
        """Returns whether READ GIS command is also a READ GIS LAYERED FC SHAPE command."""

        return self.is_valid() and self.is_read_gis() \
                and 'LAYERED FC SHAPE' in self.command or 'FLC' in self.command

    def is_2d_bc(self, control_file = None):
        """Returns whether READ GIS command is also a 2d READ GIS BC command."""

        if control_file is None:
            control_file = self.settings.control_file
        if control_file is None:
            return self.is_valid() and self.is_read_gis() and 'BC' in self.command
        else:
            return self.is_valid() and self.is_read_gis() and 'BC' in self.command and control_file.suffix.upper() == '.TBC'

    def is_set_code(self):
        return self.is_valid() and 'SET CODE' in self.command

    def is_set_mat(self):
        return self.is_valid() and 'SET MAT' in self.command

    def is_set_soil(self):
        return self.is_valid() and 'SET SOIL' in self.command

    def can_use_multiple_gis_inputs(self, control_file):
        """Returns whether the command can use multiple files on the same line (usually separated by | )."""

        return self.is_z_shape() or self.is_2d_bc(control_file) or self.is_2d_lfcsh() or self.is_2d_zpts()

    def is_gis_format(self):
        """Returns whether command is setting the model GIS FORMAT."""

        return self.command == 'GIS FORMAT'

    def is_grid_format(self):
        """Returns whether command is setting the model GRID FORMAT."""

        return self.command == 'GRID FORMAT' or self.command == 'RF GRID FORMAT'

    def is_read_database(self):
        """Returns whether command is a database command."""

        return self.is_mat_csv() or self.is_bc_dbase_file() or self.is_rainfall_grid() \
            or self.is_pit_inlet_dbase_file() or self.is_soil_dbase() or self.is_xs_dbase()

    def is_mat_dbase(self):
        """Returns whether command is a Read Material(s) File"""

        return self.is_mat_csv() or self.is_mat_tmf()

    def is_mat_csv(self):
        """Returns whether command is a Read Material(s) File == .CSV"""

        return self.is_valid() and self.is_value_a_file() and TuflowPath(self.value).suffix.upper() == '.CSV'\
               and bool(re.findall(r'^READ MATERIALS? FILE', self.command))

    def is_mat_tmf(self):
        """Returns whether command is a Read Material(s) File == .TMF"""

        return self.is_valid() and self.is_value_a_file() and TuflowPath(self.value).suffix.upper() == '.TMF'\
               and bool(re.findall(r'^READ MATERIALS? FILE', self.command))

    def is_soil_dbase(self):
        """Returns whether command is a Read Soil(s) File"""

        return self.is_valid() and self.is_value_a_file() and TuflowPath(self.value).suffix.upper() == '.TSOILF' \
                  and bool(re.findall(r'^READ SOILS? FILE', self.command))

    def is_xs_dbase(self):
        """Returns whether command is a XS Database command"""
        return self.is_valid() and self.is_value_a_file() and 'XS DATABASE' in self.command

    def is_start_define(self):
        """Returns whether command is the start of a define block."""

        return self.is_valid() and bool(re.findall(r'^(DEFINE|(ELSE\s*)?IF|START 1D)', self.command))

    def is_end_define(self):
        if self.is_valid():
            return bool(re.findall(r'^(END DEFINE|END\s*IF|END 1D|ELSE IF)', self.command))

        return False

    def is_else_if(self):
        if self.is_valid():
            return bool(re.findall(r'^(ELSE\s*IF)', self.command))

        return False

    def is_else(self):
        if self.is_valid():
            return bool(re.findall(r'^(ELSE)$', self.command.strip()))

        return False

    def define_start_type(self):
        """Returns the type of block the define block is."""

        if not self.is_valid():
            return None

        if self.command == 'DEFINE EVENT':
            return 'EVENT VARIABLE'
        elif re.findall(r'^(DEFINE|(ELSE\s*)?IF)', self.command):
            return re.sub(r'^(DEFINE|(ELSE\s*)?IF)', '', self.command).strip()
        elif self.command == 'START 1D DOMAIN':
            return '1D DOMAIN'
        else:
            return None

    def in_1d_domain_block(self):
        for define_block in self.define_blocks:
            if define_block.type == '1D DOMAIN':
                return True

        return False

    def in_scenario_block(self, scenario_name=None):
        if not self.define_blocks:
            return False

        in_scenario = True
        if isinstance(scenario_name, str):
            scenario_name = [scenario_name]
        for define_block in reversed(self.define_blocks):
            if define_block.type in ['EVENT', 'SCENARIO']:
                if scenario_name is None:
                    return True
                elif not scenario_name:
                    return False
                found = False
                for sn in scenario_name:
                    if not [x.strip().upper() for x in define_block.name.split('|') if x.strip()[0] != '!']:
                        found = True
                        break
                    if sn.upper() in [x.strip().upper() for x in define_block.name.split('|') if x.strip()[0] != '!']:
                        found = True
                        break

                if not found:
                    in_scenario = False

        return in_scenario

    def set_first_scenario_if_written(self, b):
        for define_block in reversed(self.define_blocks):
            if define_block.type in ['EVENT', 'SCENARIO']:
                define_block.first_if_written = False
                break

    def first_scenario_if_written(self):
        for define_block in reversed(self.define_blocks):
            if define_block.type in ['EVENT', 'SCENARIO', 'SCENARIO (ELSE)']:
                return define_block.first_if_written

        return True

    def set_any_scenario_if_written(self, b):
        for define_block in reversed(self.define_blocks):
            if define_block.type in ['EVENT', 'SCENARIO']:
                define_block.any_if_written = b
                break

    def any_scenario_if_written(self):
        for define_block in reversed(self.define_blocks):
            if define_block.type in ['EVENT', 'SCENARIO']:
                return define_block.any_if_written

        return True

    def new_if_statement_for_else_block(self):
        text = ''
        for define_block in reversed(self.define_blocks):
            if 'SCENARIO' in define_block.type:
                text = 'IF Scenario == '
            else:
                text = 'IF Event == '
            text = '{0}{1}'.format(text, ' | '.join([x.strip(' \t\n!') for x in define_block.name.split('|')]))
            return text
        return text

    def in_output_zone_block(self, output_zone_name=None):
        for define_block in self.define_blocks:
            if define_block.type == 'OUTPUT ZONE':
                if output_zone_name is None:
                    return True
                if isinstance(output_zone_name, str):
                    if output_zone_name.upper() in [x.strip().upper() for x in define_block.name.split('|')]:
                        return True
                elif isinstance(output_zone_name, list):
                    for sn in output_zone_name:
                        if sn.upper() in [x.strip().upper() for x in define_block.name.split('|')]:
                            return True

        return False

    def is_output_zone(self):
        return self.command and 'MODEL OUTPUT ZONE' in self.command

    def specified_output_zones(self):
        return [x.strip() for x in re.split(r'[\s|]', self.value) if x.strip()]

    def is_set_variable(self):
        return self.is_valid() and 'SET VARIABLE' in self.command

    def parse_variable(self):
        return self.command.split('SET VARIABLE')[1].strip(), self.value

    def is_set_command(self):
        return self.is_valid() and not self.is_set_variable() and re.findall('^SET', self.command)

    def retro_fix(self, txt, settings):
        """
        Retroactively fixes a command line that is reading multiple layers on a single line
        and the output format is GPKG. The retroactive fix converts from:

        gis\file.gpkg >> layer1 | gis\file.gpkg >> layer2
        to
        gis\file.gpkg >> layer1 && layer2
        """

        try:
            if '|' not in txt or self.geom_count == 1 or settings.is_grouped_database() or self.is_modify_conveyance():
                return txt

            command, value = [x.strip() for x in txt.split('==')]
            files = [x.strip() for x in value.split('|')]

            if settings.output_gis_format == GIS_GPKG:
                db, _ = get_database_name(files[0])
                layers = sorted([get_database_name(x)[1] for x in files],
                                key=lambda x: {'_R': 0, '_L': 1, '_P': 2, '': -1}[get_geom_suffix(x)])

                return f'{self.prefix}{command} == {db} >> {" && ".join(layers)}'
            else:
                files = sorted(files, key=lambda x: {'_R': 0, '_L': 1, '_P': 2, '': -1}[get_geom_suffix(x)])
                return f'{self.prefix}{command} == {" | ".join(files)}'

        except Exception as e:
            settings.errors = True
            raise MinorConvertException(f'Error: {e}')

    def correct_comment_index(self, command, index_):
        """Fix comment index by turning tabs into spaces."""

        TAB_LEN = 4

        command_len = len(command.strip())
        tab_count = command[command_len:].count('\t')
        if tab_count == 0:
            return

        i = command_len
        for c in command[command_len:]:
            if c == ' ':
                i += 1
            elif c == '\t':
                if i % TAB_LEN != 0:
                    i = (int(i / TAB_LEN) + 1) * TAB_LEN
                else:
                    i += TAB_LEN

        self.comment_index = i

    def strip_command(self, text):
        """
        Strip command into components:

        'Command == Value  ! comment  # comment'
        """

        t = text
        c, v, self.comment = None, None, ''
        if t.strip() and not t[0] in ('!', '#'):
            if '!' in t or '#' in t:
                i = t.index('!') if '!' in t else 9e29
                j = t.index('#') if '#' in t else 9e29
                self.comment_index = k = min(i, j)
                t, self.comment = t[:k], t[k:].strip()
                self.correct_comment_index(t, k)
            if '==' in t:
                c, v = t.split('==', 1)
                v = v.strip()
            else:
                c, v = t, None
            if c.strip():
                self.prefix = re.split(r'\w', c, flags=re.IGNORECASE)[0]  # prefix is leading spaces / tabs
            c = c.strip(' \n\t|')

        return c, v


class EventCommand(Command):
    """Class for handling commands in the TEF."""

    def is_start_define(self):
        """Returns whether command is starting a DEFINE EVENT block."""

        return self.command == 'DEFINE EVENT'

    def is_end_define(self):
        """Returns whether command is ending a DEFINE EVENT black."""

        return self.command == 'END DEFINE'

    def is_event_source(self):
        """Returns whether command is defining the event source."""

        return self.command == 'BC EVENT SOURCE'

    def get_event_source(self):
        """Parse the event source command and return the wildcard and replacement text."""

        if not self.is_valid():
            return None, None

        if not self.is_event_source():
            return None, None

        event_def = [x.strip() for x in str(self.value).split('|', 1)]
        if len(event_def) >= 2:
            return event_def[0], event_def[1]
        elif event_def:
            return event_def[0], None
        else:
            return None, None