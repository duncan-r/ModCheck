import unittest
from pathlib import Path
from .test_function import TestFunction


class TestWriteEmpties(unittest.TestCase):

    def test_write_empties_1(self):
        tcf = Path(__file__).parent / r'./write_empties1/TUFLOW/runs/write_empties_test.tcf'
        template_folder = tcf.parent.parent.parent / r'./templates'
        test_folder_name = 'write_empty_test'
        out_folder = tcf.parent / test_folder_name
        template_dir = template_folder / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-write-empties', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)

    def test_write_empties_2(self):
        tcf = Path(__file__).parent / r'./write_empties2/TUFLOW/runs/write_empties_test.tcf'
        template_folder = tcf.parent.parent.parent / r'./templates'
        test_folder_name = 'write_empty_test'
        out_folder = tcf.parent / test_folder_name
        template_dir = template_folder / test_folder_name
        gis = 'shp'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-write-empties', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)

    def test_write_empties_3(self):
        tcf = Path(__file__).parent / r'./write_empties3/TUFLOW/runs/write_empties_test.tcf'
        template_folder = tcf.parent.parent.parent / r'./templates'
        test_folder_name = 'write_empty_test'
        out_folder = tcf.parent / test_folder_name
        template_dir = template_folder / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-write-empties', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)

    def test_write_empties_4(self):
        tcf = Path(__file__).parent / r'./write_empties4/TUFLOW/runs/write_empties_test.tcf'
        template_folder = tcf.parent.parent.parent / r'./templates'
        test_folder_name = 'write_empty_test'
        out_folder = tcf.parent / test_folder_name
        template_dir = template_folder / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-write-empties', r'model\gis\empty', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)
