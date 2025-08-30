import unittest
from pathlib import Path
from .test_function import TestFunction


class TestReadTRD(unittest.TestCase):

    def test_read_trd(self):
        test_folder_name = 'trd'
        TCF = Path(__file__).parent / r'./trd/TUFLOW/runs/cf_w_trd.tcf'
        TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'shp'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['cf_w_trd_tuf_dir_struct'])

    def test_read_trd_tuf_dir_struct(self):
        test_folder_name = 'trd_tuf_dir_struct'
        TCF = Path(__file__).parent / r'./trd/TUFLOW/runs/cf_w_trd_tuf_dir_struct.tcf'
        TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir', '-tuflow-dir-struct']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['cf_w_trd'])
