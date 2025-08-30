import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./tuf_dir/TUFLOW/tuf_dir.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestTufDir(unittest.TestCase):

    def test_tuf_dir(self):
        test_folder_name = 'tuf_dir'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-tuflow-dir-struct', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)
