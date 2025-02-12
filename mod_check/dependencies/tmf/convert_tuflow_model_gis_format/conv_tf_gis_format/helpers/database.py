import os.path

from .parser import parse_database
from .command import Command
from .settings import MinorConvertException
from .file import replace_with_tuf_dir_struct, globify, copy_file2, tuflowify_value
from .gis import gdal_copy


def convert_database(database, settings, key=None):
    # output control file name
    if settings.tuf_dir_struct:
        output_file = replace_with_tuf_dir_struct(database, settings.output_folder, None, key)
    else:
        output_file = settings.output_folder / database.relative_to(settings.root_folder)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    settings_copy = settings.copy_settings(database, output_file)

    with output_file.open('w') as f:
        for entry in parse_database(database, settings_copy):
            if entry.header or entry.comment or entry.empty_line or not entry.file_ref:
                f.write(entry.replace_file_ref(None))
            else:
                # replace file ref and write to file - replacing with relative reference if necessary
                if settings.tuf_dir_struct:
                    relpath = replace_with_tuf_dir_struct(entry.file_ref, settings.output_folder, None, key)
                    relpath = os.path.relpath(relpath, output_file.parent)
                else:
                    relpath = os.path.relpath(entry.file_ref, database.parent)
                f.write(entry.replace_file_ref(relpath))

                # copy source files
                i = -1
                relpath = os.path.relpath(entry.file_ref, database.parent)
                relpath = globify(relpath, settings_copy.wildcards)
                if key == 'rf_grid_csv':  # grid copy
                    for i, grid_file in enumerate(database.parent.glob(relpath)):
                        src_file_grid = tuflowify_value(grid_file, settings_copy)
                        try:
                            command = Command('dummy', settings_copy)
                            dest_file_grid = command.get_gis_dest_file(src_file_grid, settings_copy)
                        except MinorConvertException as e:
                            settings_copy.errors = True
                            print(f'Error: Could not determine destination to copy file for {src_file_grid}')
                            continue

                        try:
                            gdal_copy(src_file_grid, dest_file_grid, settings_copy.projection_wkt,
                                      settings_copy.force_projection)
                        except MinorConvertException as e:
                            settings_copy.errors = True
                            print(f'Error: converting {src_file_grid} to {dest_file_grid}')
                else:  # system copy
                    for i, file in enumerate(database.parent.glob(relpath)):
                        file_src = file.resolve()
                        if file_src in settings.copied_bndry_files:
                            continue
                        else:
                            settings.copied_bndry_files[file_src] = True
                        if settings.tuf_dir_struct:
                            file_dest = replace_with_tuf_dir_struct(file_src, settings.output_folder, None, key)
                        else:
                            relpath_res = os.path.relpath(file_src, database.parent)
                            file_dest = (output_file.parent / relpath_res).resolve()
                        copy_file2(file_src, file_dest)

                if i == -1:
                    settings_copy.no_files_copied.append(('{0} Source'.format(key), entry.line, ''))

    if settings_copy.errors:
        settings.errors = True
    if settings_copy.warnings:
        settings.warnings = True
