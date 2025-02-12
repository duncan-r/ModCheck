import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./file_reference_1d/TUFLOW/runs/file_reference_1d.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestFileReference1D(unittest.TestCase):

    def test_file_reference_1d(self):
        test_folder_name = 'file_reference_1d'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'grouped-by-tcf'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)