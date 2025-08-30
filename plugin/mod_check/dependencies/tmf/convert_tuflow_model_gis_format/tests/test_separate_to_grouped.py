import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./separate_to_grouped/TUFLOW/runs/separate_to_grouped.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestSeparateToGrouped(unittest.TestCase):

    def test_separate_to_grouped(self):
        test_folder_name = 'separate_to_grouped'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'grouped-by-tcf'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)