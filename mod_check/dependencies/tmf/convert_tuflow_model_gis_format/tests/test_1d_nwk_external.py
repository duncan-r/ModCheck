import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./1d_nwk_external/TUFLOW/runs/1d_nwk_external.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class Test1DNwkExternal(unittest.TestCase):

    def test_1d_nwk_external(self):
        test_folder_name = '1d_nwk_external'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'shp'
        grid = 'tif'
        op = 'separate'
        prj = 'EPSG:32760'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir',
                '-crs', prj]
        test = TestFunction()
        test.conversion_test(args, template_dir)
