import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./number_filename/TUFLOW/runs/001.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestNumberFilename(unittest.TestCase):

    def test_number_filename(self):
        test_folder_name = 'number_filename'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'shp'
        grid = 'tif'
        op = 'grouped'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)
