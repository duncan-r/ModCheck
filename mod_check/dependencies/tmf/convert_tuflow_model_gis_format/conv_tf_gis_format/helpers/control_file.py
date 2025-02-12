import re
import os

from .empty_files import Schema
from .file import (copy_file, tuflowify_value,
                   globify, TuflowPath,
                   copy_rainfall_grid_csv, copy_file2,
                   replace_with_tuf_dir_struct)
from .settings import MinorConvertException, FatalConvertException, SEPARATE
from .gis import (ogr_copy, ogr_format, gdal_copy, gdal_format_2_ext, GIS_MIF, ogr_create)
from .parser import get_commands
from .command import EventCommand
from .database import convert_database


def convert_control_file(control_file, settings, command=None):
    """Convert a TUFLOW Control file from one GIS and GRID format to another."""

    if not control_file.is_relative_to(settings.root_folder):
        if control_file.suffix.upper() == '.TCF':
            raise FatalConvertException(f'{control_file} is not relative to {settings.root_folder}')
        else:
            settings.errors = True
            raise MinorConvertException(f'Error: {control_file} is not relative to {settings.root_folder}')

    # output control file name
    if settings.tuf_dir_struct:
        output_file = replace_with_tuf_dir_struct(control_file, settings.output_folder, None, None)
    else:
        output_file = settings.output_folder / control_file.relative_to(settings.root_folder)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if settings.verbose == 'high':
        print(f'OUTPUT FILE: {output_file}')

    # copy settings so each control file can have its own
    # IMPORTANT NOTE: control_file and settings_copy.control_file can be different for TRD files!
    settings_copy = settings.copy_settings(control_file, output_file, command)

    # copy any/all tcf_override.tcf files
    if control_file.suffix.upper() == '.TCF' and settings_copy.tuflow_override(control_file):
        for tcf_override in settings_copy.tuflow_override_iter(control_file):
            convert_control_file(tcf_override, settings_copy)

    # iterate through control file, test what the command is, and act accordingly
    with output_file.open('w') as f:
        for command in get_commands(control_file, settings_copy):

            if settings_copy.use_scenarios and command.command is not None and command.in_scenario_block() and not command.in_scenario_block(settings_copy.scenarios):
                if len(command.command) >= 2 and command.command[:2] == 'IF':
                    command.set_first_scenario_if_written(False)  # set this to false so if an 'else if' is valid, replace with 'if' when written to new control file
                elif len(command.command) >= 6 and command.command[:6] == 'END IF' and command.any_scenario_if_written():
                    f.write(command.make_new_text(settings_copy))
                continue
            elif settings_copy.use_scenarios and command.command is not None and command.in_scenario_block():
                command.set_any_scenario_if_written(True)

            # insert spatial database command at top of file (just before first valid command)
            if command.is_valid() and not settings_copy.written_spatial_database_header:
                f.write(f'Spatial Database == {settings_copy.spatial_database}\n\n')
                settings_copy.written_spatial_database_header = True

            # GIS FORMAT ==
            if command.is_gis_format():
                if settings.verbose == 'high':
                    print(f'format GIS: {command.command} == {command.value_orig}')

                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error writing new GIS FORMAT command to {control_file}: {e}')

                if not settings_copy.grid_format_command_exists:
                    f.write(f'GRID Format == {gdal_format_2_ext(settings_copy.output_grid_format).upper()[1:]}\n')

            # READ GIS [..] ==
            elif command.is_read_gis():
                if settings.verbose == 'high':
                    print(f'Read GIS: {command.command} == {command.value_orig}')

                new_command = ''
                copy_count = None
                for type_ in command.iter_geom(settings_copy):
                    if type_ == 'GRID':
                        geom = None
                    elif type_ == 'VALUE':
                        geom = None
                    else:
                        geom = type_

                    try:
                        new_command = f'{new_command}{command.make_new_text(settings_copy, geom)}'
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: writing new READ GIS command to {control_file} - {command.command_orig}: {e}')
                        continue

                    if not command.can_use_multiple_gis_inputs(control_file):
                        new_command = command.re_add_comments(new_command)
                        command.iter_geom_index = -1

                    if type_ == 'VALUE':
                        continue  # don't need to copy any layers

                    # expand glob
                    for src_file in command.iter_files(settings_copy):
                        if copy_count is None:
                            copy_count = 1
                        else:
                            copy_count += 1

                        try:
                            dest_file = command.get_gis_dest_file(src_file, settings_copy, geom)
                        except MinorConvertException as e:
                            settings_copy.errors = True
                            print(f'Error: Could not determine destination to copy file for {src_file}')
                            continue

                        try:
                            if type_ == 'GRID':
                                gdal_copy(src_file, dest_file, settings_copy.projection_wkt, settings_copy.force_projection)
                            else:
                                ogr_copy(src_file, dest_file, geom, settings_copy)
                        except MinorConvertException as e:
                            settings_copy.errors = True
                            print(f'Error: converting {src_file} to {dest_file}')

                if copy_count is None:
                    reason = ''
                    if command.empty_geom:
                        reason = 'Empty layer - Empty MIF files cannot be converted as geometry type must be set.'
                    settings_copy.no_files_copied.append((settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), reason))

                try:
                    new_command_2 = command.retro_fix(new_command, settings_copy)
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: Problem encountered correcting single line - multiple layer READ GIS command {new_command}: {e}')

                if command.can_use_multiple_gis_inputs(control_file):
                    new_command_2 = command.re_add_comments(new_command_2)

                f.write(new_command_2)

            # READ GRID [..] ==
            elif command.is_read_grid():
                if settings.verbose == 'high':
                    print(f'Read GRID: {command.command} == {command.value_orig}')

                if command.is_rainfall_grid_nc():  # don't convert or parse this one
                    try:
                        f.write(command.make_new_text(settings))
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: writing new READ GRID NC command {command.command_orig}: {e}')
                        continue

                    # glob is expanded in 'copy_file' routine
                    try:
                        dest = copy_file(control_file, TuflowPath(command.value), output_file, settings_copy.wildcards, settings.tuf_dir_struct, 'bc_dbase', settings.output_folder)
                        if dest is None:
                            settings_copy.no_files_copied.append((settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: copying NC grid: {e}')

                    continue

                new_command = ''
                copy_count = None
                for type_ in command.iter_grid(settings_copy):  # consider READ GRID ZPTS == GRID | POLYGON
                    geom = None if type_ == 'GRID' else type_

                    try:
                        new_command = f'{new_command}{command.make_new_text(settings_copy, geom)}'
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: writing new READ GRID command to {control_file} - {command.command_orig}: {e}')
                        continue

                    # expand glob
                    for src_file in command.iter_files(settings_copy):
                        if copy_count is None:
                            copy_count = 1
                        else:
                            copy_count += 1

                        try:
                            dest_file = command.get_gis_dest_file(src_file, settings_copy, geom)
                        except MinorConvertException as e:
                            settings_copy.errors = True
                            print(f'Error: Could not determine destination to copy file for {src_file}')
                            continue

                        if type_ == 'GRID':
                            try:
                                gdal_copy(src_file, dest_file, settings_copy.projection_wkt, settings_copy.force_projection)
                            except MinorConvertException as e:
                                settings_copy.errors = True
                                print(f'Error: converting {src_file} to {dest_file}\n{e}')
                        else:
                            try:
                                ogr_copy(src_file, dest_file, geom, settings_copy)
                            except MinorConvertException as e:
                                settings_copy.errors = True
                                print(f'Error: converting {src_file} to {dest_file}')

                if copy_count is None:
                    settings_copy.no_files_copied.append((settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))

                new_command = command.re_add_comments(new_command)

                f.write(new_command)

            # READ TIN [..] ==
            elif command.is_read_tin():
                if settings.verbose == 'high':
                    print(f'Read TIN: {command.command} == {command.value_orig}')

                new_command = ''
                copy_count = None
                for type_ in command.iter_tin(settings_copy):  # consider READ TIN ZPTS == TIN | POLYGON
                    geom = None if type_ == 'TIN' else type_

                    try:
                        new_command = f'{new_command}{command.make_new_text(settings_copy, geom)}'
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: writing new READ TIN command to {control_file} - {command.command_orig}: {e}')
                        continue

                    # expand glob
                    for src_file in command.iter_files(settings_copy):
                        if copy_count is None:
                            copy_count = 1
                        else:
                            copy_count += 1

                        if type_ == 'TIN':
                            try:
                                if settings.tuf_dir_struct:
                                    file_dest = replace_with_tuf_dir_struct(src_file, settings.output_folder, command, None)
                                else:
                                    rp = os.path.relpath(src_file, control_file.parent.resolve())
                                    file_dest = (output_file.parent / rp).resolve()
                                copy_file2(src_file, file_dest)
                            except MinorConvertException as e:
                                settings_copy.errors = True
                                print(f'Error: converting {src_file} to {dest_file}\n{e}')
                        else:
                            try:
                                dest_file = command.get_gis_dest_file(src_file, settings_copy, geom)
                                ogr_copy(src_file, dest_file, geom)
                            except MinorConvertException as e:
                                settings_copy.errors = True
                                print(f'Error: converting {src_file} to {dest_file}')

                if copy_count is None:
                    settings_copy.no_files_copied.append(
                        (settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))

                new_command = command.re_add_comments(new_command)

                f.write(new_command)

            # [MI | SHP | GPKG] PROJECTION ==
            elif command.is_read_projection():
                if settings.verbose == 'high':
                    print(f'Read PROJECTION: {command.command} == {command.value_orig}')

                # copy original projection for reference
                if ogr_format(command.value) == settings_copy.output_gis_format:  # output format is the same as input
                    settings_copy.written_projection = True
                settings_copy.output_gis_format = ogr_format(command.value)  # temporarily change output gis format

                # check if converting GPKG to GPKG and changing output profile - if so then just write new command, don't copy original proj command
                if 'GPKG' in command.command and (
                        (not re.findall(r'\.gpkg', str(command.value_orig), flags=re.IGNORECASE) and not settings_copy.output_profile != SEPARATE)
                        or
                        (re.findall(r'\.gpkg', str(command.value_orig), flags=re.IGNORECASE) and settings_copy.output_profile != SEPARATE)
                ):
                    try:
                        f.write(command.make_new_text(settings_copy))
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: writing new PROJECTION command to {control_file} - {command.command_orig}: {e}')
                else:
                    f.write(command.make_new_text(settings_copy))

                # expand glob
                copy_count = None
                for copy_count, src_file in enumerate(command.iter_files(settings_copy)):
                    try:
                        dest_file = command.get_gis_dest_file(src_file, settings_copy)
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: Could not determine destination to copy file for {src_file}')
                        continue

                    gis_format = ogr_format(src_file)
                    geom = None
                    if gis_format == GIS_MIF:
                        for i, geom_ in enumerate(command.iter_geom(settings_copy)):
                            if i == 0:
                                geom = geom_

                    try:
                        ogr_copy(src_file, dest_file, geom, settings_copy)
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: converting {src_file} to {dest_file}')

                if copy_count is None and not command.is_mi_prj_string():
                    settings_copy.no_files_copied.append((settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))

                settings_copy.output_gis_format = settings.output_gis_format  # reset output gis format

                # write out converted projection file - if not already written
                if not settings_copy.written_projection:
                    try:
                        f.write(command.make_new_text(settings_copy))
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: writing new PROJECTION command to {control_file} - {command.command_orig}: {e}')

                    # expand glob
                    for src_file in command.iter_files(settings_copy):

                        gis_format = ogr_format(src_file)
                        geom = None
                        if gis_format == GIS_MIF:
                            for i, geom_ in enumerate(command.iter_geom(settings_copy)):
                                if i == 0:
                                    geom = geom_

                        try:
                            dest_file = command.get_gis_dest_file(src_file, settings_copy)
                            ogr_copy(src_file, dest_file, geom, settings_copy)
                        except MinorConvertException as e:
                            settings_copy.errors = True
                            print(f'Error: converting {src_file} to {dest_file}')

                    # mi projection string - need to create rather than copy
                    if command.is_mi_prj_string() and not settings_copy.written_projection:
                        dest_file = command.get_gis_dest_file(command.value, settings_copy)
                        ogr_create(dest_file, '_P', [Schema('ID', 4, 36)], settings_copy.projection_wkt, settings_copy)

                    settings_copy.written_projection = True

                if not settings_copy.written_tif_projection and settings.tif_projection_path is not None:
                    f.write(f'TIF Projection == {settings.tif_projection_path}\n')
                    settings_copy.written_tif_projection = True

            # SPATIAL DATABASE ==
            elif command.is_spatial_database_command():
                if settings.verbose == 'high':
                    print(f'Set SPATIAL DATABASE: {command.command} == {command.value_orig}')

                settings_copy.process_spatial_database_command(command.value)

            # CONTROL FILE
            elif command.is_control_file():
                if settings.verbose == 'high':
                    print(f'Control FILE: {command.command} == {command.value_orig}')

                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: writing new CONTROL FILE command to {control_file} - {command.command_orig}: {e}')

                if command.is_quadtree_single_level():
                    continue

                # expand glob
                copy_count = None
                for copy_count, cf in enumerate(command.iter_files(settings_copy)):
                    cf = cf.resolve()

                    try:
                        convert_control_file(cf, settings_copy, command)
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: Could not convert control file {cf}: {e}')

                if copy_count is None:
                    settings_copy.no_files_copied.append((settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))

            # BC DATABASE ==
            elif command.is_bc_dbase_file():
                if settings.verbose == 'high':
                    print(f'BC DATABASE: {command.command} == {command.value_orig}')

                in_bc_dbase = (settings_copy.control_file.parent / command.value).resolve()

                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: writing new BC DATABASE command to {control_file} - {command.command_orig}: {e}')

                something_copied = False
                for dbase in command.iter_files(settings_copy):
                    something_copied = True
                    dbase = dbase.resolve()
                    try:
                        convert_database(dbase, settings_copy, 'bc_dbase')
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: Could not convert database {dbase}: {e}')

                if not something_copied:
                    settings_copy.no_files_copied.append((settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))

            # PIT INLET DATABASE == | DEPTH DISCHARGE DATABASE ==
            elif command.is_pit_inlet_dbase_file():
                if settings.verbose == 'high':
                    print(f'Pit DATABASE: {command.command} == {command.value_orig}')

                in_pit_dbase = (settings_copy.control_file.parent / command.value).resolve()

                # glob is expanded in 'copy_file' routine
                # copy bc_dbase.csv
                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: writing new PIT INLET DATABASE command to {control_file} - {command.command_orig}: {e}')

                something_copied = False
                for dbase in command.iter_files(settings_copy):
                    something_copied = True
                    dbase = dbase.resolve()
                    try:
                        convert_database(dbase, settings_copy, 'pit_dbase')
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: Could not convert database {dbase}: {e}')

                if not something_copied:
                    settings_copy.no_files_copied.append(
                        (settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))

            # READ GRID RF == CSV
            elif command.is_rainfall_grid_csv():
                if settings.verbose == 'high':
                    print(f'RAINFALL GRID CSV: {command.command} == {command.value_orig}')

                # copy csv and command
                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: writing new READ GRID RF (CSV) command to {control_file} - {command.command_orig}: {e}')

                # expand glob
                something_copied = False
                for dbase in command.iter_files(settings_copy):
                    something_copied = True
                    dbase = dbase.resolve()
                    try:
                        convert_database(dbase, settings_copy, 'rf_grid_csv')
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: Could not convert database {dbase}: {e}')

                if not something_copied:
                    settings_copy.no_files_copied.append(
                        (settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))
                    # # copy src_file
                    # try:
                    #     rel_path = os.path.relpath(src_file, settings_copy.control_file.parent)
                    #     dest_file = (output_file.parent / rel_path).resolve()
                    # except ValueError:
                    #     dest_file = src_file
                    #
                    # if dest_file != src_file:
                    #     try:
                    #         copy_rainfall_grid_csv(src_file, dest_file, settings_copy)
                    #     except MinorConvertException as e:
                    #         settings_copy.errors = True
                    #         print(f'Error: Could not copy READ GRID RF CSV file {source}')

                    # for rf_grid in get_bc_dbase_sources(src_file):
                    #     # expand glob
                    #     pattern = globify(rf_grid, settings_copy.wildcards)
                    #     for src_file_grid in src_file.parent.glob(pattern):
                    #         if copy_count is None:
                    #             copy_count = 1
                    #         else:
                    #             copy_count += 1
                    #
                    #         src_file_grid = tuflowify_value(src_file_grid, settings_copy)
                    #
                            # try:
                            #     dest_file_grid = command.get_gis_dest_file(src_file_grid, settings_copy)
                            # except MinorConvertException as e:
                            #     settings_copy.errors = True
                            #     print(f'Error: Could not determine destination to copy file for {src_file_grid}')
                            #     continue
                            #
                            # try:
                            #     gdal_copy(src_file_grid, dest_file_grid, settings_copy.projection_wkt, settings_copy.force_projection)
                            # except MinorConvertException as e:
                            #     settings_copy.errors = True
                            #     print(f'Error: converting {src_file_grid} to {dest_file_grid}')

                # if copy_count is None:
                #     settings_copy.no_files_copied.append((settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))

            # READ FILE ==
            elif command.is_read_file():
                if settings.verbose == 'high':
                    print(f'Read FILE: {command.command} == {command.value_orig}')

                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: writing new CONTROL FILE command to {control_file} - {command.command_orig}: {e}')

                ext = control_file.suffix.upper()

                # expand glob
                copy_count = None
                for copy_count, cf in enumerate(command.iter_files(settings_copy)):
                    cf = cf.resolve()

                    try:
                        convert_control_file(cf, settings_copy, ext)
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: Could not convert control file {cf}: {e}')

                if copy_count is None:
                    settings_copy.no_files_copied.append((settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))

            elif command.is_mat_csv():
                if settings.verbose == 'high':
                    print(f'Read Material FILE: {command.command} == {command.value_orig}')

                in_mat_file = (settings_copy.control_file.parent / command.value).resolve()

                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: writing new READ FILE command to {control_file} - {command.command_orig}: {e}')

                something_copied = False
                for dbase in command.iter_files(settings_copy):
                    something_copied = True
                    dbase = dbase.resolve()
                    try:
                        convert_database(dbase, settings_copy, 'mat')
                    except MinorConvertException as e:
                        settings_copy.errors = True
                        print(f'Error: Could not convert database {dbase}: {e}')

                if not something_copied:
                    settings_copy.no_files_copied.append(
                        (settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))

            #  any command that has a value that is a file and hasn't been processed yet
            elif command.is_value_a_file():
                if settings.verbose == 'high':
                    print(f'Read Other FILE: {command.command} == {command.value_orig}')

                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: writing new READ FILE command to {control_file} - {command.command_orig}: {e}')

                event_command = EventCommand(command.original_text, settings_copy)
                if event_command.is_event_source():
                    continue

                # glob is expanded in 'copy_file' routine
                try:
                    dest = copy_file(control_file, TuflowPath(command.value), output_file, settings_copy.wildcards, settings.tuf_dir_struct, 'model', settings.output_folder)
                    if dest is None:
                        settings_copy.no_files_copied.append((settings_copy.control_file.suffix[1:].upper(), command.original_text.strip(), ''))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: Could not copy READ FILE file {command.value}')

            # LOG FOLDER == | OUTPUT FOLDER == | WRITE CHECK FILES  ==
            elif command.is_value_a_folder():
                if settings.verbose == 'high':
                    if command.value_orig is not None:
                        print(f'TUFLOW FOLDER COMMAND: {command.command_orig} == {command.value_orig}')
                    else:
                        print(f'TUFLOW FOLDER COMMAND: {command.command_orig}')

                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: writing new COMMAND to {control_file} - {command.command_orig}: {e}')

            # CONTAINS COMMAND
            elif command.is_valid():
                if settings.verbose == 'high':
                    if command.value_orig is not None:
                        print(f'TUFLOW COMMAND: {command.command_orig} == {command.value_orig}')
                    else:
                        print(f'TUFLOW COMMAND: {command.command_orig}')

                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException as e:
                    settings_copy.errors = True
                    print(f'Error: writing new COMMAND to {control_file} - {command.command_orig}: {e}')

            # COMMENT or BLANK line
            else:
                if settings.verbose == 'high':
                    if command.original_text.strip():
                        print(f'Comment: {command.original_text}')

                try:
                    f.write(command.make_new_text(settings_copy))
                except MinorConvertException:
                    pass

    settings.copy_global_values(settings_copy)

    if settings_copy.errors:
        settings.errors = True
    if settings_copy.warnings:
        settings.warnings = True
