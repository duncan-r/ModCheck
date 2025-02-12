import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./variables_w_scenarios/TUFLOW/runs/var_w_scen.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestVariablesWithScenarios(unittest.TestCase):

    def test_variables_with_scenarios(self):
        test_folder_name = 'variables_w_scenarios'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'gpkg'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off', '-use-scenarios', '-s1', 'TEST',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)
