import unittest
from .test_mif import TestMif
from .test_shp import TestShp
from .test_gpkg import TestGpkg
from .test_variables import TestVariables
from .test_trcf import TestTuflowRainfallControlFile
from .test_mid import TestReadMID
from .test_scenarios import TestScenarios
from .test_gpkg_name import TestGPKGName
from .test_estry import TestEstry
from .test_gpkg_raster import TestGPKGRaster
from .test_write_empties import TestWriteEmpties
from .test_no_copy import TestNoCopy
from .test_rf_nc import TestRFNC
from .test_rf_csv import TestRFCSV
from .test_separate_to_grouped import TestSeparateToGrouped
from .test_file_reference_1d import TestFileReference1D
from .test_mif_bad_geom import TestMifBadGeom
from .test_oned import TestOneD
from .test_shp_to_mif import TestShpToMif
from .test_dbase_w_scen import TestDbaseWithScenario
from .test_variables_w_scenarios import TestVariablesWithScenarios
from .test_number_filename import TestNumberFilename
from .test_tin import TestTin
from .test_tuf_dir import TestTufDir
from .test_mat_dep_var import TestMatDepVar
from .test_mif_empty_proj import TestMifEmptyProj
from .test_crs import TestCRS
from .test_empty_geometry import TestEmptyGeometry


if __name__ == '__main__':
    unittest.main()
