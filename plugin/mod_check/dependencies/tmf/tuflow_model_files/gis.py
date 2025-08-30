import os
import re
import typing
from pathlib import Path
from enum import Enum
from contextlib import contextmanager

from .file import TuflowPath
from .stubs import ogr, osr
# noinspection PyUnusedImports
from .gis_attr_driver import GISAttributes

try:
    from osgeo import gdal
    has_gdal = True
except ImportError:
    from .stubs.gdal_ import gdal_ as gdal
    has_gdal = False


SPLIT_DATABASE_REGEX = re.compile(r'>>(?![^<]*>>)')


class GisFormat(Enum):
    Unknown = 0
    MIF = 1
    SHP = 2
    GPKG = 3
    ASC = 4
    TIF = 5
    FLT = 6
    NC = 7


def get_database_name(file):
    """Strip the file reference into database name >> layer name."""
    if '>>' in str(file) and str(file).count('>>') > str(file).count('<<'):
        return [x.string() for x in SPLIT_DATABASE_REGEX.split(file, maxsplit=1)]
    else:
        if Path(file).suffix.upper() == '.PRJ':
            file = Path(file).with_suffix('.shp')
        return [str(file), Path(file).stem]


def ogr_format(file: str | Path, no_ext_is_mif: bool = True) -> GisFormat:
    if str(file).startswith('CoordSys') or TuflowPath(file).stem.startswith('CoordSys'):
        return GisFormat.MIF
    db, layer = get_database_name(file)
    if TuflowPath(db).suffix.upper() in ['.XF4', '.XF8']:
        return GisFormat.Unknown
    if TuflowPath(db).suffix.upper() in ['.SHP', '.PRJ']:
        return GisFormat.SHP
    if TuflowPath(db).suffix.upper() in ['.MIF', '.MID']:
        return GisFormat.MIF
    if TuflowPath(db).suffix.upper() == '.GPKG':
        return GisFormat.GPKG
    if TuflowPath(db).suffix.upper() == '' and no_ext_is_mif:
        return GisFormat.MIF
    if TuflowPath(db).suffix.upper() == '' and not no_ext_is_mif:
        return GisFormat.GPKG
    return GisFormat.Unknown


def gdal_format(file, no_ext_is_gpkg=False, no_ext_is_nc=False) -> GisFormat:
    """Returns the GDAL driver name based on the extension of the file reference."""

    db, layer = get_database_name(file)
    if TuflowPath(db).suffix.upper() in ['.XF4', '.XF8']:
        return GisFormat.Unknown
    if TuflowPath(db).suffix.upper() == '.ASC' or TuflowPath(db).suffix.upper() == '.TXT' or TuflowPath(db).suffix.upper() == '.DEM':
        return GisFormat.ASC
    if TuflowPath(db).suffix.upper() == '.FLT':
        return GisFormat.FLT
    if TuflowPath(db).suffix.upper() == '.GPKG':
        return GisFormat.GPKG
    if TuflowPath(db).suffix.upper() == '.NC':
        return GisFormat.NC
    if TuflowPath(db).suffix.upper() == '.TIF' or TuflowPath(db).suffix.upper() == '.TIFF' or TuflowPath(db).suffix.upper() == '.GTIF' \
            or TuflowPath(db).suffix.upper() == '.GTIFF':
        return GisFormat.TIF
    if TuflowPath(db).suffix.upper() == '' and no_ext_is_gpkg:
        return GisFormat.GPKG
    if TuflowPath(db).suffix.upper() == '' and no_ext_is_nc:
        return GisFormat.NC
    return GisFormat.Unknown


def get_driver_name_from_extension(driver_type: str, ext: str | Path) -> str | None:
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
        return None

    if isinstance(ext, TuflowPath):
        ext = str(ext.dbpath)

    if ext[0] != '.' or (ext[0] == '.' and len(ext) > 1 and ext[1] == '.'):
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
                if drv_ext.lower() == ext or (drv_ext.lower() == 'bil' and ext.lower() == 'flt'):
                    return drv.ShortName

    return None


def get_driver_name_from_gis_format(gis_format: GisFormat) -> str | None:
    """Returns the GDAL/OGR driver name based on the GIS format."""
    if gis_format == GisFormat.SHP:
        return 'ESRI Shapefile'
    elif gis_format == GisFormat.MIF:
        return 'MapInfo File'
    elif gis_format == GisFormat.GPKG:
        return 'GPKG'
    elif gis_format == GisFormat.ASC:
        return 'AAIGrid'
    elif gis_format == GisFormat.TIF:
        return 'GTiff'
    elif gis_format == GisFormat.FLT:
        return 'ENVI'
    elif gis_format == GisFormat.NC:
        return 'NetCDF'
    else:
        return None


def gdal_projection(raster_file: str | Path) -> str | None:
    try:
        from osgeo import gdal
    except ImportError:
        raise ImportError('GDAL is required to extract a projection from a raster layer.')

    if isinstance(raster_file, TuflowPath):
        raster_file = raster_file.dbpath

    driver = get_driver_name_from_extension('raster', raster_file)
    if driver is None:
        raise ValueError(f'Could not find GDAL driver for {raster_file}')
    dataset = gdal.Open(str(raster_file), gdal.GA_ReadOnly)
    if dataset is None:
        raise RuntimeError(f'Could not open raster file {raster_file} with GDAL driver {driver}')
    if dataset.GetSpatialRef() is None:
        return None
    return dataset.GetSpatialRef().ExportToWkt()


def ogr_geom_types(fpath: str | Path) -> list[int]:
    fpath = TuflowPath(fpath)
    with fpath.open_gis('r') as f:
        if f.fmt == GisFormat.MIF:
            return list(f.lyr.GetGeometryTypes().keys())
        return [f.lyr.GetGeomType()]


def ogr_iter_geom(fpath: str | Path) -> typing.Generator[int, None, None]:
    fpath = TuflowPath(fpath)
    if not fpath.dbpath.exists():
        raise FileNotFoundError(f'File {fpath.dbpath} does not exist.')
    types = []
    with fpath.open_gis('r') as f:
        if f.fmt == GisFormat.MIF:
            for geom_type in f.lyr.GetGeometryTypes().keys():
                if geom_type not in types:
                    types.append(geom_type)
                    yield geom_type
        else:
            yield f.lyr.GetGeomType()


def tuflow_type_requires_feature_iter(layername):
    """
    Returns the indexes of fields that could require a file copy e.g. for 1d_xs.

    This will require manual feature iteration and copy in the OGR copy routine.
    """

    req_iter_types = {
        r'^1d_nwk[eb]?_': [10],
        r'^1d_pit_': [3],
        r'^1d_(xs|tab|xz|bg|lc|cs|hw)_': [0],
        r'^1d_na_': [0]
    }

    for pattern, indexes in req_iter_types.items():
        if re.findall(pattern, layername, flags=re.IGNORECASE):
            return indexes

    return []


def mi_projection(mi_proj):
    sr = osr.SpatialReference()
    sr.ImportFromMICoordSys(mi_proj)
    return sr.ExportToWkt()


def ogr_projection(filepath):
    """Return the projection as WKT from a given layer."""
    if str(filepath).startswith('CoordSys'):
        return mi_projection(str(filepath))

    db, layername = get_database_name(filepath)

    if not TuflowPath(db).exists():
        raise FileNotFoundError(f'File {db} does not exist.')

    if TuflowPath(db).suffix.upper() == '.PRJ':
        with open(db, 'r') as f:
            return f.readline()

    fmt = ogr_format(db)
    driver_name = get_driver_name_from_gis_format(fmt)
    try:
        datasource = ogr.GetDriverByName(driver_name).Open(db)
    except RuntimeError:
        datasource = None

    if datasource is None:
        raise RuntimeError(f'Could not open {db} with driver {driver_name}')

    lyr = datasource.GetLayer(layername)
    if lyr is None:
        raise RuntimeError(f'Layer {layername} not found in {db} or could not be loaded.')

    sr = lyr.GetSpatialRef()
    if sr is None:
        raise RuntimeError(f'Layer {layername} in {db} has no spatial reference.')

    wkt = sr.ExportToWkt()

    # noinspection PyUnusedLocal
    datasource, lyr = None, None

    return wkt


def get_all_layers_in_gpkg(db):
    """Returns all layers in a GPKG database."""

    return GPKG(db).layers()


def ogr_basic_geom_type(geom_type, force_single_part=True):
    """Convert OGR geometry type to a basic type e.g. PointM -> Point"""

    while geom_type - 1000 > 0:
        geom_type -= 1000

    if force_single_part:
        if geom_type == ogr.wkbMultiPoint:
            geom_type = ogr.wkbPoint
        elif geom_type == ogr.wkbMultiLineString:
            geom_type = ogr.wkbLineString
        elif geom_type == ogr.wkbMultiPolygon:
            geom_type = ogr.wkbPolygon

    return geom_type


class GPKG:
    """A class to help understand what is inside a GPKG database.
     This class does not read geometry or attribute data."""

    def __init__(self, gpkg_path):
        """
        Parameters
        ----------
        gpkg_path : PathLike
        """
        self.gpkg_path = str(gpkg_path)

    def glob(self, pattern):
        """Do a glob search of the database for tables matching the pattern.

        Parameters
        ----------
        pattern : str
            The glob pattern.

        Yields
        -------
        str
            The table names that match the pattern.
        """
        p = pattern.replace('*', '.*')
        for lyr in self.layers():
            if re.findall(p, lyr, flags=re.IGNORECASE):
                yield lyr

    def layers(self):
        """Return the GPKG layers in the database.

        Returns
        -------
        list[str]
            The layer names.
        """
        import sqlite3
        res = []

        if not TuflowPath(self.gpkg_path).exists():
            return res

        conn = sqlite3.connect(self.gpkg_path)
        cur = conn.cursor()

        try:
            cur.execute(f"SELECT table_name FROM gpkg_contents;")
            res = [x[0] for x in cur.fetchall()]
        except sqlite3.Error:
            pass
        finally:
            cur.close()

        return res

    @contextmanager
    def gpkg_connect(self, gpkg_path):
        import sqlite3
        res = []

        if not TuflowPath(gpkg_path).exists():
            return res

        conn = None
        try:
            conn = sqlite3.connect(gpkg_path)
            cur = conn.cursor()
            yield cur
        except sqlite3.Error:
            pass
        finally:
            if conn:
                conn.close()

        return res

    def vector_layers(self):
        """Vector layers contained within the GPKG.

        Returns
        -------
        list[str]
            The vector layer names.
        """
        sql = (f'SELECT contents.table_name FROM gpkg_contents AS contents '
               f'  INNER JOIN gpkg_geometry_columns AS columns ON contents.table_name = columns.table_name '
               f' WHERE columns.geometry_type_name != "GEOMETRY";')
        with self.gpkg_connect(self.gpkg_path) as cur:
            cur.execute(sql)
            res = [x[0] for x in cur.fetchall()]

        return res

    def non_spatial_layers(self):
        """Non-spatial layers contained within the GPKG.

        Returns
        -------
        list[str]
            The non-spatial layer names.
        """
        sql = (f'SELECT contents.table_name FROM gpkg_contents AS contents '
               f'  INNER JOIN gpkg_geometry_columns AS columns ON contents.table_name = columns.table_name '
               f' WHERE columns.geometry_type_name = "GEOMETRY";')
        with self.gpkg_connect(self.gpkg_path) as cur:
            cur.execute(sql)
            res = [x[0] for x in cur.fetchall()]

        return res

    def geometry_type(self, layer_name):
        """Return the basic geometry type of the given layer (assuming it's a valid vector layer).

        Parameters
        ----------
        layer_name : str
            The layer name.

        Returns
        -------
        str
            The (basic) geometry type. One of 'POINT', 'LINE', 'POLYGON'.
        """
        import sqlite3
        conn = sqlite3.connect(self.gpkg_path)
        cur = conn.cursor()
        res = None
        try:
            cur.execute(f"SELECT geometry_type_name FROM gpkg_geometry_columns where table_name = '{layer_name}';")
            res = [x[0] for x in cur.fetchall()][0]
        except sqlite3.Error:
            pass
        finally:
            cur.close()

        return res

    def __contains__(self, item):
        """Returns a bool on whether a certain layer is in the database."""
        import sqlite3
        if not TuflowPath(self.gpkg_path).exists():
            return False

        conn = sqlite3.connect(self.gpkg_path)
        cur = conn.cursor()
        res = None
        try:
            cur.execute(f"SELECT table_name FROM gpkg_contents WHERE table_name='{item}';")
            res = [x[0] for x in cur.fetchall()]
        except sqlite3.Error:
            pass
        finally:
            cur.close()

        return bool(res)
