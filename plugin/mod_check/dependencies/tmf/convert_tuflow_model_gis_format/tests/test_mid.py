import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./mid/TUFLOW/runs/read_mid_zpts.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestReadMID(unittest.TestCase):

    def test_read_mid(self):
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