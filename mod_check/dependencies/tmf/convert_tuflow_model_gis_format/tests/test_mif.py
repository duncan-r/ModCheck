import unittest
from pathlib import Path
from .test_function import TestFunction
from osgeo import ogr


TCF = Path(__file__).parent / r'./mif/TUFLOW/runs/EG00_001.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestMif(unittest.TestCase):

    def test_mif_to_gpkg_separate(self):
        test_folder_name = 'gpkg'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['mi_proj'])

    def test_mif_to_shp_separate(self):
        test_folder_name = 'shp'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'shp'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['mi_proj'])

    def test_mif_proj_string(self):
        tcf = Path(__file__).parent / r'./mif/TUFLOW/runs/mi_proj.tcf'
        test_folder_name = 'mi_proj'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'shp'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['EG00_001', 'projection', '2d_zsh_EG03_Rd_Crest_001', '2d_zsh_EG03_Rd_Crest_001_L'])

        # additional test
        output_prj = out_folder / 'TUFLOW' / 'runs' / 'projection.shp'
        ds = ogr.GetDriverByName('Esri Shapefile').Open(str(output_prj))
        lyr = ds.GetLayer()
        srs = lyr.GetSpatialRef()
        expected_wkt = 'PROJCS["unnamed",GEOGCS["GCS_unnamed",DATUM["D_GRS_80",SPHEROID["GRS_80",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",153],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",10000000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'
        self.assertEqual(srs.ExportToWkt(), expected_wkt)
        lyr = None
        ds = None

    def test_mif_proj_string_tf_dir(self):
        tcf = Path(__file__).parent / r'./mif/TUFLOW/runs/mi_proj.tcf'
        test_folder_name = 'mi_proj_tuf_dir_struct'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'shp'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir', '-tuflow-dir-struct']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['EG00_001', 'projection', '2d_zsh_EG03_Rd_Crest_001', '2d_zsh_EG03_Rd_Crest_001_L'])

        # additional test
        output_prj = out_folder / 'TUFLOW' / 'model' / 'gis' / 'projection.shp'
        ds = ogr.GetDriverByName('Esri Shapefile').Open(str(output_prj))
        lyr = ds.GetLayer()
        srs = lyr.GetSpatialRef()
        expected_wkt = 'PROJCS["unnamed",GEOGCS["GCS_unnamed",DATUM["D_GRS_80",SPHEROID["GRS_80",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",153],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",10000000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'
        self.assertEqual(srs.ExportToWkt(), expected_wkt)
        lyr = None
        ds = None
