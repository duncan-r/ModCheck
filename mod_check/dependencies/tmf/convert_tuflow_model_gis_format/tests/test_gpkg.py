import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./gpkg/TUFLOW/runs/EG00_001.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestGpkg(unittest.TestCase):

    def test_gpkg_to_shp_separate(self):
        test_folder_name = 'shp'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'shp'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)

    def test_gpkg_to_gpkg_grouped(self):
        test_folder_name = 'gpkg'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'tcf'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)
