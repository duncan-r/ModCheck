import unittest
from pathlib import Path
from .test_function import TestFunction
from osgeo import ogr


TCF = Path(__file__).parent / r'./mif_empty_proj/TUFLOW/runs/mif_empty_proj.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestMifEmptyProj(unittest.TestCase):

    def test_mif_empty_proj(self):
        test_folder_name = 'mif_empty_proj'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        prj = 'EPSG:32760'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir',
                '-crs', prj]
        test = TestFunction()
        test.conversion_test(args, template_dir)

        # additional test
        output_prj = out_folder / 'TUFLOW' / 'runs' / 'projection.gpkg'
        ds = ogr.GetDriverByName('GPKG').Open(str(output_prj))
        lyr = ds.GetLayer('projection')
        srs = lyr.GetSpatialRef()
        self.assertEqual('WGS 84 / UTM zone 60S', srs.GetName())
        lyr = None
        ds = None
