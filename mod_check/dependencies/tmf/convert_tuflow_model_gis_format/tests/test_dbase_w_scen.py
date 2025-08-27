import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./dbase_w_scen/TUFLOW/runs/dbase_w_scen.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestDbaseWithScenario(unittest.TestCase):

    def test_dbase_with_scenario(self):
        test_folder_name = 'dbase_w_scen'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)