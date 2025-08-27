import unittest
from pathlib import Path
from .test_function import TestFunction


class TestEstry(unittest.TestCase):

    def test_estry_auto(self):
        test_folder_name = 'estry'
        tcf = Path(__file__).parent / r'./estry/TUFLOW/runs/test_auto_estry.tcf'
        template_folder = tcf.parent.parent.parent / r'./templates'
        out_folder = tcf.parent / test_folder_name
        template_dir = template_folder / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_auto_estry_old'])

    def test_estry_auto_old(self):
        test_folder_name = 'estry_old'
        tcf = Path(__file__).parent / r'./estry/TUFLOW/runs/test_auto_estry_old.tcf'
        template_folder = tcf.parent.parent.parent / r'./templates'
        out_folder = tcf.parent / test_folder_name
        template_dir = template_folder / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_auto_estry'])
