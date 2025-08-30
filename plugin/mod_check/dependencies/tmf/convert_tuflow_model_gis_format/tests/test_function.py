import re
import sys
import os
import stat
import errno
import unittest
from pathlib import Path
import shutil
from osgeo import ogr
from conv_tf_gis_format.convert_tuflow_gis_format import main
from conv_tf_gis_format.helpers.file import remove_geom_suffix, add_geom_suffix, get_geom_suffix, change_gis_mi_folder
from conv_tf_gis_format.helpers.gis import ogr_iter_geom, geom_type_2_suffix, get_database_name, GPKG, GIS_MIF, GIS_SHP


class TestFunction(unittest.TestCase):

    def conversion_test(self, args, template_dir, **kwargs):
        # delete any previous test outputs
        o = get_arg('-o', args)
        if o is not None:
            path = Path(o)
            if path.exists():
                shutil.rmtree(str(path), ignore_errors=False, onerror=handleRemoveReadonly)

        # run main script
        sys.argv = ['python'] + args
        main()

        # check all files have been copied
        test_files_exist = TestFilesExist()
        test_files_exist.run_test(args, **kwargs)

        # check control files match templates
        test_control_file_contents = TestControlFileContents()
        test_control_file_contents.run_test(args, template_dir)

        # check file references in layer have been maintained for GPKG grouped output
        test_gis_file_references = TestReferencesInGISLayer()
        test_gis_file_references.run_test(args)

        if kwargs.get('check_consistent_crs'):
            test_files_exist.check_crs(args)

        if kwargs.get('check_geometry'):
            test_files_exist.check_geom(args)


def handleRemoveReadonly(func, path, exc):
    excvalue = exc[1]
    if func in (os.rmdir, os.remove, os.unlink) and excvalue.errno == errno.EACCES:
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def get_arg(arg, args):
    return args[args.index(arg) + 1]


class TestFilesExist(unittest.TestCase):

    def run_test(self, args, exclude=(), **kwargs):
        o = get_arg('-o', args)
        tcf = get_arg('-tcf', args)
        chk_path = Path(tcf).parent.parent

        for file1 in chk_path.glob('**/*'):
            if str(Path(tcf).parent) in str(file1) and len(Path(tcf).parts) < len(file1.parts):
                continue

            if file1.stem in exclude:
                continue

            rel_path = os.path.relpath(file1, chk_path)
            file2 = Path(o) / chk_path.stem / rel_path
            if '-tuflow-dir-struct' in args:
                for f in Path(o).glob('**/*'):
                    if file1.stem == f.stem:
                        file2 = f.resolve()
                        break

            if file1.suffix.lower() in ['.csv', '.tcf', '.tgc', '.tbc', '.ecf', '.tef', '.tsoilf', '.toc', '.qcf',
                                        '.adcf', '.trfc']:
                self.assertTrue(file2.exists(), f'File does not exist: {file2}')

            elif file1.suffix.lower() in ['.shp', '.mif', '.gpkg']:
                if file1.suffix.lower() == '.gpkg':
                    layers = [f'{file1} >> {x}' for x in GPKG(file1).layers()]
                else:
                    layers = [file1]
                gis = get_arg('-gis', args).lower()
                file_ = file2.with_suffix(f'.{gis}')
                if file1.stem == 'projection' and file1.suffix.lower() != file2.suffix.lower():
                    self.assertTrue(file2.exists(), f'File does not exist: {file2}')
                if file1.suffix.lower() == '.mif':
                    file_ = Path(change_gis_mi_folder(file_, GIS_MIF, GIS_SHP))
                elif gis == 'mif':
                    file_ = Path(change_gis_mi_folder(file_, GIS_SHP, GIS_MIF))

                for layer in layers:
                    for geom_type in ogr_iter_geom(layer):
                        if file1.suffix.lower() == '.gpkg' and Path(get_database_name(layer)[0]).stem.lower() != get_database_name(layer)[1].lower():
                            file2 = file_.parent / '{0}.{1}'.format(get_database_name(layer)[1], gis)
                        elif file1.suffix.lower() == '.shp' and not get_geom_suffix(file1):
                            file2 = Path(file_)
                        elif file1.stem == 'projection':
                            file2 = Path(file_)
                        else:
                            file2 = Path(add_geom_suffix(file_, geom_type_2_suffix(geom_type)))

                        if not file2.exists() and gis.lower() == 'gpkg':
                            op = get_arg('-op', args)
                            if op == 'separate':
                                f = remove_geom_suffix(file2)
                                if not f.exists():
                                    self.assertTrue(False, f'File does not exist: {file2}')
                                if file2.stem not in GPKG(f).layers():
                                    self.assertTrue(False, f'Layer does not exist: {file2.stem}')
                            else:
                                found = False
                                for gpkg in chk_path.glob('**/*.gpkg'):
                                    if file2.stem in GPKG(gpkg).layers():
                                        found = True
                                        break
                                if not found:
                                    self.assertTrue(False, f'Layer does not exist: {file2.stem}')

                        elif not file2.exists():
                            self.assertTrue(False, f'File does not exist: {file2}')

            elif file1.suffix.lower() in ['.asc', '.flt', '.tif']:
                grid = get_arg('-grid', args)
                file2 = file2.with_suffix(f'.{grid}')
                if not file2.exists() and grid.lower() == 'gpkg':
                    op = get_arg('-op', args)
                    if op == 'separate':
                        f = remove_geom_suffix(file2)
                        if not f.exists():
                            self.assertTrue(False, f'File does not exist: {file2}')
                        if file2.stem not in GPKG(f).layers():
                            self.assertTrue(False, f'Layer does not exist: {file2.stem}')
                    else:
                        found = False
                        for gpkg in chk_path.glob('**/*.gpkg'):
                            if file2.stem in GPKG(gpkg).layers():
                                found = True
                                break
                        if not found:
                            self.assertTrue(False, f'Layer does not exist: {file2.stem}')
                else:
                    self.assertTrue(file2.exists(), f'File does not exist: {file2}')

    def check_crs(self, args):
        o = get_arg('-o', args)
        proj_wkt = None
        for file in Path(o).glob(f'**/*.prj'):
            proj_wkt_ = None
            with file.open() as f:
                proj_wkt_ = f.readlines()

            if proj_wkt is None:
                proj_wkt = proj_wkt_
            else:
                self.assertEqual(proj_wkt, proj_wkt_)

    def check_geom(self, args):
        o = get_arg('-o', args)
        for file in Path(o).glob(f'**/*.gpkg'):
            gpkg = GPKG(file)
            for layer_name in gpkg.layers():
                self.assertTrue(gpkg.geometry_type(layer_name) in ['POINT', 'LINESTRING', 'POLYGON'])



class TestControlFileContents(unittest.TestCase):

    def run_test(self, args, template_dir):
        o = get_arg('-o', args)
        for file1 in template_dir.glob('**/*'):
            found = False
            for file2 in Path(o).glob(f'**/*{file1.suffix}'):
                if file1.name == file2.name:
                    found = True
                    with file1.open('r') as f1:
                        with file2.open('r') as f2:
                            for i, line1 in enumerate(f1):
                                if self.is_read_file_text(line1):
                                    line1 = re.sub(r'\\|/', re.escape(os.sep), line1)
                                line2 = f2.readline()
                                self.assertEqual(line1, line2,
                                                 f'Lines do not match in file ({file1} Line {i + 1}):\n{line1}\n{line2}')
                    break
            if not found:
                self.assertTrue(False, f'File does not exist: {file1.name}')

    def is_read_file_text(self, text):
        if 'Read' in text and '==' in text and not ('!' in text and text.index('!') < text.index('Read')):
            return True

        if 'File' in text and '==' in text and not ('!' in text and text.index('!') < text.index('File')):
            return True

        if 'Folder' in text and '==' in text and not ('!' in text and text.index('!') < text.index('Folder')):
            return True

        if 'Projection' in text and '==' in text and not ('!' in text and text.index('!') < text.index('Projection')):
            return True

        if 'Database' in text and '==' in text and not ('!' in text and text.index('!') < text.index('Database')):
            return True

        if 'Create' in text and '==' in text and not ('!' in text and text.index('!') < text.index('Create')):
            return True

        return False


class TestReferencesInGISLayer(unittest.TestCase):

    def run_test(self, args):
        o = get_arg('-o', args)
        gis = get_arg('-gis', args)
        op = get_arg('-op', args)
        if gis == 'gpkg' and op != 'separate':
            for file in Path(o).glob('**/*.gpkg'):
                gpkg = GPKG(file)
                for layer_name in gpkg.layers():
                    if '1d_xs' in layer_name.lower() or '1d_nwk' in layer_name.lower():
                        ds = ogr.GetDriverByName('GPKG').Open(str(file))
                        lyr = ds.GetLayer(layer_name)
                        for feat in lyr:
                            if '1d_xs' in layer_name.lower():
                                source = feat['Source']
                                source = (file.parent / source).resolve()
                                self.assertTrue(source.exists(), f'File reference incorrect: {source}')
                            elif feat['Type'].lower() == 'm':
                                source = feat['Inlet_Type']
                                source = (file.parent / source).resolve()
                                self.assertTrue(source.exists(), f'File reference incorrect: {source}')
                            elif feat['Type'].lower() == 'q' and lyr.GetGeomType() == ogr.wkbPoint:
                                source = feat['Inlet_Type']
                                self.assertTrue('/' not in source and '\\' not in source, f'{feat["ID"]} should not contain file path: {source}')
                        ds, lyr = None, None
