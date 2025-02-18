import os
from pathlib import Path
from typing import Union

from ...convert_tuflow_model_gis_format.conv_tf_gis_format.helpers.gis import (
    tuflow_type_requires_feature_iter, ogr_format, get_database_name, ogr_iter_geom, gdal_format
)

def get_driver_name_from_extension(driver_type: str, ext: Union[str, Path]) -> str:
    """Return the GDAL/OGR driver name based on the file extension. This routine requires GDAL.

    Parameters
    ----------
    driver_type : str
        'raster' or 'vector'
    ext : PathLike
        File or file extension to search for.

    Returns
    -------
    str
        GDAL/OGR driver name.
    """
    try:
        from osgeo import gdal
    except ImportError:
        raise ImportError('GDAL is required to get driver name from extension.')

    if not ext:
        return

    if ext[0] != '.':
        ext = os.path.splitext(ext)[1]

    ext = ext.lower()
    if ext[0] == '.':
        ext = ext[1:]

    for i in range(gdal.GetDriverCount()):
        drv = gdal.GetDriver(i)
        md = drv.GetMetadata_Dict()
        if ('DCAP_RASTER' in md and driver_type == 'raster') or ('DCAP_VECTOR' in md and driver_type == 'vector'):
            if not drv.GetMetadataItem(gdal.DMD_EXTENSIONS):
                continue
            driver_extensions = drv.GetMetadataItem(gdal.DMD_EXTENSIONS).split(' ')
            for drv_ext in driver_extensions:
                if drv_ext.lower() == ext:
                    return drv.ShortName
