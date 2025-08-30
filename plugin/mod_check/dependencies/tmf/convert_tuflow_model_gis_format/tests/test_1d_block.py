import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./1d_block/TUFLOW/runs/1d_block.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class Test1DBlock(unittest.TestCase):

    def test_1d_block(self):
        test_folder_name = '1d_block'
        out_folder = TCF.parent / test_folder_name
        gis = 'SHP'
        grid = 'TIF'
        op = 'tcf'
        template_dir = TEMPLATE_FOLDER / test_folder_name
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)