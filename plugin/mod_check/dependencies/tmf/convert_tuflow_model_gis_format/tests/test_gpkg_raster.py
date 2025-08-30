import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./gpkg_raster/TUFLOW/runs/gpkg_raster_test.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestGPKGRaster(unittest.TestCase):

    def test_raster_to_gpkg_raster_grouped(self):
        test_folder_name = 'gpkg_conversion_grouped_all'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'gpkg'
        op = 'grouped-by-tcf'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)

    def test_raster_to_gpkg_raster_separate(self):
        test_folder_name = 'gpkg_conversion_separate'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'gpkg'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)
