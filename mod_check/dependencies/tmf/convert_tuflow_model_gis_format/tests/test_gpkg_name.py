import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./gpkg_name/TUFLOW/runs/EG00_001.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestGPKGName(unittest.TestCase):

    def test_shp_to_gpkg_grouped_all(self):
        test_folder_name = 'gpkg_conversion_grouped_all'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'grouped-by-tcf'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-gpkg-name', 'model_gis', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)

    def test_shp_to_gpkg_grouped_cf1(self):
        test_folder_name = 'gpkg_conversion_grouped_cf1'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'grouped-by-cf-1'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-gpkg-name', 'model_gis', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)
