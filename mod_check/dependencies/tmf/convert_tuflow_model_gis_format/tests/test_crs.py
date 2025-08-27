import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./crs/TUFLOW/runs/test_crs.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestCRS(unittest.TestCase):

    def test_crs(self):
        test_folder_name = 'crs'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'shp'
        grid = 'tif'
        op = 'separate'
        prj = 'PROJCS["WGS_1984_UTM_Zone_60S",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",10000000.0],PARAMETER["Central_Meridian",177.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-crs', prj, '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, check_consistent_crs=True)
