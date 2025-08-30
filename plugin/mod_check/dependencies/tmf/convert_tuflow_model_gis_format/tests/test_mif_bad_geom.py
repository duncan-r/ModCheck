import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./mif_bad_geom/TUFLOW/runs/mif_bad_geom.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestMifBadGeom(unittest.TestCase):

    def test_mif_bad_geom(self):
        test_folder_name = 'mif_bad_geom'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'grouped-by-tcf'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir)
