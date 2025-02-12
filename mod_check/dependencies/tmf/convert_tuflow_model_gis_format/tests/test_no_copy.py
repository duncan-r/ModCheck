import unittest
from pathlib import Path
from .test_function import TestFunction


class TestNoCopy(unittest.TestCase):

    def test_no_copy_gis(self):
        tcf = Path(__file__).parent / r'./no_copy/TUFLOW/runs/no_copy_gis_test.tcf'
        template_folder = tcf.parent.parent.parent / r'./templates'
        test_folder_name = 'no_copy_gis'
        out_folder = tcf.parent / test_folder_name
        template_dir = template_folder / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['no_copy_file_test', 'bc_dbase_EG00_001'])

    def test_no_copy_file(self):
        tcf = Path(__file__).parent / r'./no_copy/TUFLOW/runs/no_copy_file_test.tcf'
        template_folder = tcf.parent.parent.parent / r'./templates'
        test_folder_name = 'no_copy_file'
        out_folder = tcf.parent / test_folder_name
        template_dir = template_folder / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['no_copy_gis_test'])
