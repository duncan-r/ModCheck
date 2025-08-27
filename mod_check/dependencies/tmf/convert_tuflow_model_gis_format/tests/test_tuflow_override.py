import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./tuflow_override/TUFLOW/runs/model.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestTuflowOverride(unittest.TestCase):

    def test_tuflow_override(self):
        test_folder_name = 'tuflow_override'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)
