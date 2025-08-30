import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./shp_to_mif/TUFLOW/runs/shp_to_mif.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestShpToMif(unittest.TestCase):

    def test_shp_to_mif(self):
        test_folder_name = 'shp_to_mif'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'mif'
        grid = 'flt'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)
