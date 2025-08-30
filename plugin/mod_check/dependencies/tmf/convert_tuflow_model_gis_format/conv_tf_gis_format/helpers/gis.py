import re
import os
import numpy as np
from .settings import MinorConvertException
from .file import copy_file, copy_file2, TuflowPath
from .stubs import ogr, osr, gdal


GIS_SHP = 'Esri Shapefile'
GIS_MIF = 'Mapinfo File'
GIS_GPKG = 'GPKG'
GRID_ASC = 'AAIGrid'
GRID_FLT = 'EHdr'
GRID_GPKG = 'GPKG'
GRID_TIF = 'GTiff'
GRID_NC = 'netCDF'
GIS_UNKNOWN = 'UNKNOWN'


def init_gdal_error_handler() -> None:
    """Initialise GDAL error handler"""

    global b_gdal_error
    global gdal_err_msg_
    b_gdal_error = False
    gdal_err_msg_ = ""
    gdal.PushErrorHandler(gdal_error_handler)


def gdal_error_handler(err_class: int, err_num: int, err_msg: str) -> None:
    """Custom python gdal error handler - if there is a failure, need to let GDAL finish first."""

    errtype = {
            gdal.CE_None:'None',
            gdal.CE_Debug:'Debug',
            gdal.CE_Warning:'Warning',
            gdal.CE_Failure:'Failure',
            gdal.CE_Fatal:'Fatal'
    }
    err_msg = err_msg.replace('\n',' ')
    err_class = errtype.get(err_class, 'None')
    if err_class.lower() == 'failure':
        global b_gdal_error
        b_gdal_error = True

    # skip these warning msgs
    if 'Normalized/laundered field name:' in err_msg:
        return
    if 'width 256 truncated to 254' in err_msg:
        return

    print('GDAL {0}'.format(err_class.upper()))
    print('{1} Number: {0}'.format(err_num, err_class))
    print('{1} Message: {0}'.format(err_msg, err_class))


def gdal_error() -> bool:
    """Returns a bool if there was a GDAL error or not"""

    global b_gdal_error
    try:
        return b_gdal_error
    except NameError:  # uninitialised
        init_gdal_error_handler()
        return gdal_error()


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
        except Exception:
            pass
        finally:
            cur.close()

        return res

    def vector_layers(self):
        """Vector layers contained within the GPKG.

        Returns
        -------
        list[str]
            The vector layer names.
        """
        import sqlite3
        res = []

        if not TuflowPath(self.gpkg_path).exists():
            return res

        conn = sqlite3.connect(self.gpkg_path)
        cur = conn.cursor()

        try:
            cur.execute(
                f'SELECT contents.table_name FROM gpkg_contents AS contents '
                f'  INNER JOIN gpkg_geometry_columns AS columns ON contents.table_name = columns.table_name '
                f' WHERE columns.geometry_type_name != "GEOMETRY";'
            )
            res = [x[0] for x in cur.fetchall()]
        except Exception:
            pass
        finally:
            cur.close()

        return res

    def non_spatial_layers(self):
        """Non-spatial layers contained within the GPKG.

        Returns
        -------
        list[str]
            The non-spatial layer names.
        """
        import sqlite3
        res = []

        if not TuflowPath(self.gpkg_path).exists():
            return res

        conn = sqlite3.connect(self.gpkg_path)
        cur = conn.cursor()

        try:
            cur.execute(
                f'SELECT contents.table_name FROM gpkg_contents AS contents '
                f'  INNER JOIN gpkg_geometry_columns AS columns ON contents.table_name = columns.table_name '
                f' WHERE columns.geometry_type_name = "GEOMETRY";'
            )
            res = [x[0] for x in cur.fetchall()]
        except Exception:
            pass
        finally:
            cur.close()

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
        try:
            cur.execute(f"SELECT geometry_type_name FROM gpkg_geometry_columns where table_name = '{layer_name}';")
            res = [x[0] for x in cur.fetchall()][0]
        except Exception:
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
        except:
            pass
        finally:
            cur.close()

        return bool(res)


class FLT:
    """Class to help out with FLT writing - mainly to convert header from EHdr format to hdr format."""

    def __init__(self, flt_path):
        self.flt_path = TuflowPath(flt_path)
        self.hdr_path = TuflowPath(flt_path).with_suffix(('.hdr'))
        self.ox = 0.
        self.oy = 0.
        self.ncol = 0
        self.nrow = 0
        self.dx = 0.
        self.dy = 0.
        self.ndv = -999.
        self.byteorder = 'LSBFIRST'
        self.parse_header()

    def iter_hdr(self):
        """Iterate through a EHdr or hdr header file and return the header value."""

        if not self.hdr_path.exists():
            return

        with self.hdr_path.open() as f:
            for line in f:
                a = sum([[y.strip() for y in x.strip().split('\t') if y.strip()] for x in line.split(' ') if x.strip()], [])
                if len(a) >= 2:
                    yield a[0].upper(), a[1].upper()
                elif a:
                    yield a[0].upper(), ''
                else:
                    yield '', ''

    def parse_header(self):
        """Parse the header into class variables."""

        ulymap = False
        ulxmap = False
        for header, value in self.iter_hdr():
            try:
                if header == 'NROWS':
                    self.nrow = int(value)
                elif header == 'NCOLS':
                    self.ncol = int(value)
                elif header in ['ULXMAP', 'XLLCORNER']:
                    ulxmap = header == 'ULXMAP'
                    self.ox = float(value)
                elif header in ['ULYMAP', 'YLLCORNER']:
                    ulymap = header == 'ULYMAP'
                    self.oy = float(value)
                elif header in ['XDIM', 'CELLSIZE']:
                    self.dx = float(value)
                elif header in ['YDIM']:
                    self.dy = float(value)
                elif header in ['NODATA', 'NODATA_VALUE']:
                    self.ndv = float(value)
            except ValueError:
                continue

        if np.isclose(self.dy, 0.):
            self.dy = self.dx

        # ulxmap and ulymap reference cell centres - need to be shifted to corners for FLT
        if ulxmap:
            self.ox -= self.dx / 2.

        if ulymap:   # this is ref. top corner - needs to be converted to bottom corner for FLT
            self.oy -= self.nrow * self.dy - self.dy / 2.

    def write_header(self):
        """Write the header into hdr format."""

        with self.hdr_path.open('w') as f:
            f.write(f'ncols {self.ncol}\n'
                    f'nrows {self.nrow}\n'
                    f'xllcorner {self.ox}\n'
                    f'yllcorner {self.oy}\n'
                    f'cellsize {self.dx}\n'
                    f'NODATA_value {self.ndv}\n'
                    f'byteorder {self.byteorder}\n')


def ogr_copy(src_file, dest_file, geom=None, settings=None, **kwargs):
    """
    Copy vector file from one format to another (or the same format).

    If converting from a MIF file, geom should be specified to indicate which geometry type to copy across.

    Some TUFLOW layers (1d_nwk, 1d_tab) contain references to files, these will also be copied and references
    updated if required (output layer can be in a different folder if it's going to a centralised database).
    """

    db_in, lyrname_in = get_database_name(src_file)
    db_out, lyrname_out = get_database_name(dest_file)

    prj_only = False
    sr = None
    if TuflowPath(db_in).suffix.upper() == '.PRJ' and not TuflowPath(db_in).with_suffix('.shp').exists() and TuflowPath(db_out).suffix.upper() == '.SHP':
        if settings and settings.force_projection:
            sr = osr.SpatialReference()
            sr.ImportFromWkt(settings.projection_wkt)
            if not TuflowPath(db_out).parent.exists():
                TuflowPath(db_out).parent.mkdir(parents=True)
            ds = ogr.GetDriverByName('ESRI Shapefile').CreateDataSource(str(TuflowPath(db_out).with_suffix('.shp')))
            if ds is None or gdal_error():
                raise MinorConvertException(f'Error: Failed to open: {db_out}')
            lyr = ds.CreateLayer(TuflowPath(db_in).stem, sr, ogr.wkbPoint)
            if lyr is None or gdal_error():
                raise MinorConvertException(f'Error: Failed to create layer: {TuflowPath(db_in).stem}')
            ds, lyr = None, None
        else:
            copy_file2(TuflowPath(db_in), TuflowPath(db_out).with_suffix('.prj'))
        return
    elif TuflowPath(db_in).suffix.upper() == '.PRJ' and not TuflowPath(db_in).with_suffix('.shp').exists():
        if settings and settings.force_projection:
            sr = osr.SpatialReference()
            sr.ImportFromWkt(settings.projection_wkt)
        else:
            with open(db_in, 'r') as f:
                try:
                    sr = osr.SpatialReference(f.readline())
                except Exception as e:
                    raise MinorConvertException(f'Error reading spatial reference.\n{e}')
        prj_only = True
    elif TuflowPath(db_in).suffix.upper() == '.PRJ':
        db_in = str(TuflowPath(db_in).with_suffix('.shp'))
    elif TuflowPath(db_in).suffix.upper() == '.MID':
        db_in = str(TuflowPath(db_in).with_suffix('.mif'))

    if TuflowPath(db_out).suffix.upper() == '.PRJ':
        db_out = str(TuflowPath(db_out).with_suffix('.shp'))

    lyr_in = None
    fmt_in = ogr_format(db_in)
    if fmt_in == 'UNKNOWN':
        copy_file2(TuflowPath(db_in), TuflowPath(db_out))
        return

    if not prj_only:
        driver_in = ogr.GetDriverByName(fmt_in)
        datasource_in = driver_in.Open(db_in)
        if gdal_error() or datasource_in is None:
            if settings is not None:
                settings.errors = True
            raise MinorConvertException(f'Error: Failed to open {db_in}')
        lyr_in = datasource_in.GetLayer(lyrname_in)
        if gdal_error() or lyr_in is None:
            if settings is not None:
                settings.errors = True
            raise MinorConvertException(f'Error: Failed to open layer {lyrname_in}')

    fmt_out = ogr_format(db_out)
    driver_out = ogr.GetDriverByName(fmt_out)
    if TuflowPath(db_out).exists() and fmt_out == GIS_GPKG:
        datasource_out = driver_out.Open(db_out, 1)
    elif TuflowPath(db_out).exists():
        datasource_out = driver_out.Open(db_out, 1)
        if datasource_out is not None:
            datasource_out.DeleteLayer(0)
        elif fmt_out == GIS_MIF:
            try:
                err = driver_out.DeleteDataSource(db_out)
                if err != ogr.OGRERR_NONE:
                    gis_manual_delete(db_out, fmt_out)
            except Exception as e:
                if settings is not None:
                    settings.errors = True
                raise MinorConvertException(f'Error: Could not overwrite existing file: {db_out}')
            datasource_out = driver_out.CreateDataSource(db_out)
    else:
        TuflowPath(db_out).parent.mkdir(parents=True, exist_ok=True)
        datasource_out = driver_out.CreateDataSource(db_out)
    if gdal_error() or datasource_out is None:
        if settings is not None:
            settings.errors = True
        raise MinorConvertException(f'Error: Failed to open: {db_out}')

    options = ['OVERWRITE=YES'] if fmt_out == GIS_GPKG else []
    geom_type = 0
    if lyr_in is not None:
        geom_type = geom if geom is not None else lyr_in.GetGeomType()
    elif prj_only:
        geom_type = ogr.wkbPoint

    if geom_type == 0 and fmt_out != GIS_MIF:
        geom_type = ogr.wkbPoint

    file_indexes = tuflow_type_requires_feature_iter(lyrname_in)  # is there a file reference in the features
    wildcards = settings.wildcards if settings else []

    # if fmt_out == GIS_MIF or fmt_in == GIS_MIF or prj_only or file_indexes or is_multi_part(lyr=lyr_in):
    if settings is not None and settings.force_projection:
        if lyr_in is not None:  # i think there's a bug in older GDAL python versions that causes crash later if SpatialReference is initialised, so avoid if possiblw
            sr = lyr_in.GetSpatialRef()
        else:
            sr = osr.SpatialReference()
        sr.ImportFromWkt(settings.projection_wkt)
    elif lyr_in:
        sr = lyr_in.GetSpatialRef()
    if sr is None:
        lyr_out = datasource_out.CreateLayer(lyrname_out, geom_type=geom_type, options=options)
    else:
        lyr_out = datasource_out.CreateLayer(lyrname_out, sr, geom_type, options)
    if gdal_error() or lyr_out is None:
        if settings is not None:
            settings.errors = True
        raise MinorConvertException(f'Error: Failed to create layer {lyrname_out}')
    if prj_only:
        fielDefn = ogr.FieldDefn('ID', ogr.OFTString)
        lyr_out.CreateField(fielDefn)
    else:
        layer_defn = lyr_in.GetLayerDefn()
        for i in range(0, layer_defn.GetFieldCount()):
            fieldDefn = copy_field_defn(layer_defn.GetFieldDefn(i))
            fieldDefn = sanitise_field_defn(fieldDefn, fmt_out)
            lyr_out.CreateField(fieldDefn)
        if fmt_out == GIS_GPKG:
            datasource_out.StartTransaction()

        empty_geom_warning_issued = False
        for feat in lyr_in:
            if feat.geometry() and geom and ogr_basic_geom_type(feat.geometry().GetGeometryType()) != geom_type:
                continue

            explode_multipart = kwargs.get('explode_multipart', False) or (settings and settings.explode_multipart)
            if is_multi_part(feat) and explode_multipart:
                geom_parts = [x for x in feat.GetGeometryRef()]
            else:
                geom_parts = [feat.GetGeometryRef()]

            for gp in geom_parts:
                if gp is None:
                    if not empty_geom_warning_issued:
                        print(f'Warning: {lyrname_in} has features that contain empty geometry - not copying these features.')
                        empty_geom_warning_issued = True
                    if settings is not None:
                        settings.warnings = True
                    continue

                new_feat = ogr.Feature(lyr_out.GetLayerDefn())
                panMap = list(range(feat.GetFieldCount()))
                new_feat.SetFromWithMap(feat, True, panMap)
                for i in range(new_feat.GetFieldCount()):
                    new_feat.SetField(i, new_field_value(new_feat.GetFieldDefnRef(i), new_feat[i], fmt_out))
                new_feat.SetGeometry(gp)

                if not kwargs.get('copy_associated_files') == False:  # double negative, but default should be to copy
                    for i in file_indexes:  # check if there's a file that needs to be copied e.g. 1d_xs.csv
                        if feat.GetFieldCount() > i and feat[i]:
                            if '|' in feat[i]:
                                op, file = [x.strip() for x in feat[i].split('|', 1)]
                            else:
                                op, file = None, feat[i]
                            if not (TuflowPath(db_in).parent / file).is_file():
                                continue
                            dest_file = (TuflowPath(db_out).parent / file).resolve()
                            dest_file2 = TuflowPath(dest_file)
                            if settings:
                                try:
                                    rel_path = os.path.relpath((TuflowPath(db_in).parent / file).resolve(), settings.root_folder)
                                    dest_file2 = (settings.output_folder / rel_path).resolve()
                                except ValueError:
                                    continue
                            if dest_file == dest_file2:
                                copy_file(TuflowPath(db_in), file, TuflowPath(db_out), wildcards, settings.tuf_dir_struct, 'gis', settings.output_folder)
                            else:  # this means that we are using a grouped database that will screw up copy - req correction
                                try:
                                    rel_path = os.path.relpath(db_in, settings.root_folder)
                                except ValueError:
                                    continue
                                fake_db_out = (TuflowPath(settings.output_folder) / rel_path).resolve()
                                copy_file(TuflowPath(db_in), file, fake_db_out, wildcards, settings.tuf_dir_struct, 'gis', settings.output_folder)
                                try:
                                    if op is None:
                                        new_feat[i] = os.path.relpath(dest_file2, TuflowPath(db_out).parent)
                                    else:
                                        new_feat[i] = f'{op} | {os.path.relpath(dest_file2, TuflowPath(db_out).parent)}'
                                except ValueError:
                                    continue

                lyr_out.CreateFeature(new_feat)

        if fmt_out == GIS_GPKG:
            datasource_out.CommitTransaction()

    datasource_out, lyr_out = None, None
    datasource_in, lyr_in = None, None


def gdal_copy(src_file, dest_file, projection_wkt, force_projection=False):
    """Copy from one raster format to another (or can be the same)."""

    db_in, lyrname_in = get_database_name(src_file)
    fmt_in = gdal_format(db_in)

    if fmt_in == GRID_GPKG or fmt_in == GRID_NC:
        raster_in = gdal.OpenEx(db_in, options=[f'TABLE={lyrname_in}'])
    else:
        raster_in = gdal.Open(db_in)
    if gdal_error() or raster_in.RasterCount == 0:
        raise MinorConvertException(f'Error: Failed to open: {db_in}')

    db_out, lyrname_out = get_database_name(dest_file)
    TuflowPath(db_out).parent.mkdir(parents=True, exist_ok=True)
    fmt_out = gdal_format(db_out)

    options = ['-of', fmt_out]
    if fmt_out == GRID_TIF:
        options = ['-co', 'COMPRESS=DEFLATE', '-co', 'PREDICTOR=2', '-co', 'ZLEVEL=1', '-co', 'GEOTIFF_VERSION=1.1',
                   '-co', 'NUM_THREADS=ALL_CPUS']
        if (fmt_in in [GRID_ASC, GRID_FLT] and projection_wkt is not None) or force_projection:
            options.extend(['-a_srs', projection_wkt])
    elif fmt_out == GRID_GPKG:
        if lyrname_out in GPKG(db_out):
            raster_in = None
            return
        options = ['-co', f'RASTER_TABLE={lyrname_out}', '-co', f'RASTER_IDENTIFIER={lyrname_out}',
                   '-co', 'TILE_FORMAT=TIFF', '-co', 'APPEND_SUBDATASET=YES']
        if (fmt_in in [GRID_ASC, GRID_FLT] and projection_wkt) or force_projection:
            options.extend(['-a_srs', projection_wkt])

    translate_options = gdal.TranslateOptions(options=options)
    raster_out = gdal.Translate(db_out, raster_in, options=translate_options)
    if raster_out is None or gdal_error():
        raise MinorConvertException(f'Error: Failed to translate: {db_in}\n{gdal_err_msg()}')
    gdal.PopErrorHandler()

    raster_in, raster_out = None, None

    if fmt_out == GRID_FLT:
        FLT(db_out).write_header()


def gdal_error_handler(err_class, err_num, err_msg):
    global b_gdal_error
    global gdal_err_msg_
    errtype = {
            gdal.CE_None:'None',
            gdal.CE_Debug:'Debug',
            gdal.CE_Warning:'Warning',
            gdal.CE_Failure:'Failure',
            gdal.CE_Fatal:'Fatal'
    }
    err_msg = err_msg.replace('\n',' ')
    err_class = errtype.get(err_class, 'None')

    if err_class in ['Failure', 'Fatal']:
        gdal_err_msg_ = f'GDAL Error {err_num}: {err_msg}'


def gdal_err_msg():
    global gdal_err_msg_
    return gdal_err_msg_


def get_database_name(file):
    """Strip the file reference into database name >> layer name."""

    if re.findall(r'\s+>>\s+', str(file)):
        return re.split(r'\s+>>\s+', str(file), 1)
    else:
        if TuflowPath(file).suffix.upper() == '.PRJ':
            file = TuflowPath(file).with_suffix('.shp')
        return [str(file), TuflowPath(file).stem]


def ogr_format(file, no_ext_is_mif=False, no_ext_is_gpkg=False):
    """Returns the OGR driver name based on the extension of the file reference."""
    if str(file).startswith('CoordSys') or TuflowPath(file).stem.startswith('CoordSys'):
        return GIS_MIF
    db, layer = get_database_name(file)
    if TuflowPath(db).suffix.upper() in ['.XF4', '.XF8']:
        return GIS_UNKNOWN
    if TuflowPath(db).suffix.upper() in ['.SHP', '.PRJ']:
        return GIS_SHP
    if TuflowPath(db).suffix.upper() in ['.MIF', '.MID']:
        return GIS_MIF
    if TuflowPath(db).suffix.upper() == '.GPKG':
        return GIS_GPKG
    if TuflowPath(db).suffix.upper() == '' and no_ext_is_mif:
        return GIS_MIF
    if TuflowPath(db).suffix.upper() == '' and no_ext_is_gpkg:
        return GIS_GPKG

    if not TuflowPath(db).suffix.upper():
        raise MinorConvertException(f'Error: Unable to determine Vector format from blank file extension: {db}')

    raise MinorConvertException(f'Error: Vector format not supported by TUFLOW: {TuflowPath(db).suffix}')


def gdal_format(file, no_ext_is_gpkg=False, no_ext_is_nc=False):
    """Returns the GDAL driver name based on the extension of the file reference."""

    db, layer = get_database_name(file)
    if TuflowPath(db).suffix.upper() in ['.XF4', '.XF8']:
        return GIS_UNKNOWN
    if TuflowPath(db).suffix.upper() == '.ASC' or TuflowPath(db).suffix.upper() == '.TXT' or TuflowPath(db).suffix.upper() == '.DEM':
        return GRID_ASC
    if TuflowPath(db).suffix.upper() == '.FLT':
        return GRID_FLT
    if TuflowPath(db).suffix.upper() == '.GPKG':
        return GRID_GPKG
    if TuflowPath(db).suffix.upper() == '.NC':
        return GRID_NC
    if TuflowPath(db).suffix.upper() == '.TIF' or TuflowPath(db).suffix.upper() == '.TIFF' or TuflowPath(db).suffix.upper() == '.GTIF' \
            or TuflowPath(db).suffix.upper() == '.GTIFF':
        return GRID_TIF
    if TuflowPath(db).suffix.upper() == '' and no_ext_is_gpkg:
        return GRID_GPKG
    if TuflowPath(db).suffix.upper() == '' and no_ext_is_nc:
        return GRID_NC

    if not TuflowPath(db).suffix.upper():
        raise MinorConvertException(f'Error: Unable to determine GRID format from blank file extension: {db}')

    raise MinorConvertException(f'Error: GRID format not supported by TUFLOW: {TuflowPath(db).suffix}')


def ogr_format_2_ext(ogr_format):
    """Convert OGR driver name to a file extension."""

    if ogr_format == GIS_SHP:
        return '.shp'
    if ogr_format == GIS_MIF:
        return '.mif'
    if ogr_format == GIS_GPKG:
        return '.gpkg'


def gdal_format_2_ext(gdal_format):
    """Convert GDAL driver name to extension."""

    if gdal_format == GRID_ASC:
        return '.asc'
    if gdal_format == GRID_FLT:
        return '.flt'
    if gdal_format == GRID_TIF:
        return '.tif'
    if gdal_format == GRID_GPKG:
        return '.gpkg'
    if gdal_format == GRID_NC:
        return '.nc'


def geom_type_2_suffix(geom_type):
    """Convert OGR geometry type to TUFLOW suffix."""

    if geom_type == ogr.wkbPoint:
        return '_P'
    if geom_type == ogr.wkbLineString:
        return '_L'
    if geom_type == ogr.wkbPolygon:
        return '_R'


def suffix_2_geom_type(suffix):
    """Convert OGR geometry type to TUFLOW suffix."""

    if suffix == '_P':
        return ogr.wkbPoint
    if suffix == '_L':
        return ogr.wkbLineString
    if suffix == '_R':
        return ogr.wkbPolygon


def ogr_iter_geom(filepath):
    """Iterate through the different geometry types in a given layer."""

    db, layername = get_database_name(filepath)
    if not TuflowPath(db).exists():
        yield None
        return

    fmt = ogr_format(db)
    driver = ogr.GetDriverByName(fmt)
    if fmt == GIS_SHP and TuflowPath(db).suffix.lower() == '.prj':
        db = str(TuflowPath(db).with_suffix('.shp'))
    datasource = driver.Open(db)
    if gdal_error() or datasource is None:
        yield None
        return

    lyr = datasource.GetLayer(layername)
    if gdal_error() or lyr is None:
        yield None
        datasource = None
        return

    if lyr.GetGeomType() != 0:
        yield ogr_basic_geom_type(lyr.GetGeomType())
        datasource, lyr = None, None
        return

    geom_types = []
    once = False
    for feat in lyr:
        once = True
        if feat.geometry():
            geom_type = ogr_basic_geom_type(feat.geometry().GetGeometryType(), True)
            if geom_type not in geom_types:
                geom_types.append(geom_type)
                yield geom_type

    if not once:
        yield None

    datasource, lyr = None, None


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


def ogr_geometry_name(geom_type):
    if geom_type == ogr.wkbPoint:
        return 'Point'
    elif geom_type == ogr.wkbLineString:
        return 'LineString'
    elif geom_type == ogr.wkbPolygon:
        return 'Polygon'


def ogr_projection(filepath):
    """Return the projection as WKT from a given layer."""
    if str(filepath).startswith('CoordSys'):
        return mi_projection(str(filepath))

    db, layername = get_database_name(filepath)

    if not TuflowPath(db).exists():
        return

    if TuflowPath(db).suffix.upper() == '.PRJ':
        with open(db, 'r') as f:
            return f.readline()

    fmt = ogr_format(db)
    driver = ogr.GetDriverByName(fmt)
    datasource = driver.Open(db)
    if gdal_error() or datasource is None:
        return

    lyr = datasource.GetLayer(layername)
    if gdal_error() or lyr is None:
        datasource = None
        return

    sr = lyr.GetSpatialRef()
    if sr is None:
        datasource, lyr = None, None
        return

    wkt = sr.ExportToWkt()

    datasource, lyr = None, None

    return wkt


def mi_projection(mi_proj):
    sr = osr.SpatialReference()
    sr.ImportFromMICoordSys(mi_proj)
    return sr.ExportToWkt()


def get_all_layers_in_gpkg(db):
    """Returns all layers in a GPKG database."""

    return GPKG(db).layers()


def gis_manual_delete(file, fmt):
    """Manually delete a GIS file - can be required if GIS file is corrupt -> OGR won't delete it then."""

    file = TuflowPath(file)
    if fmt == GIS_MIF:
        for file in file.parent.re(rf'{re.escape(file.stem)}\.(mif|mid)', flags=re.IGNORECASE):
            file.unlink()
    elif fmt == GIS_SHP:
        for file in file.parent.re(rf'{re.escape(file.stem)}\.(shp|prj|dbf|shx|sbn|sbx)', flags=re.IGNORECASE):
            file.unlink()


def copy_field_defn(field_defn):
    """Copy field defn to new object."""

    new_field_defn = ogr.FieldDefn()
    new_field_defn.SetName(field_defn.GetName())
    new_field_defn.SetType(field_defn.GetType())
    new_field_defn.SetSubType(field_defn.GetSubType())
    new_field_defn.SetJustify(field_defn.GetJustify())
    new_field_defn.SetWidth(field_defn.GetWidth())
    new_field_defn.SetPrecision(field_defn.GetPrecision())
    new_field_defn.SetNullable(field_defn.IsNullable())
    new_field_defn.SetUnique(field_defn.IsUnique())
    new_field_defn.SetDefault(field_defn.GetDefault())
    new_field_defn.SetDomainName(field_defn.GetDomainName())

    return new_field_defn


def new_field_value(field_defn, field_value, output_format):
    if field_value is not None or output_format != GIS_MIF:
        return field_value
    if field_defn.GetType() in [ogr.OFTInteger, ogr.OFTInteger64]:
        return 0
    elif field_defn.GetType() in [ogr.OFTReal]:
        return 0.

    return field_value


def sanitise_field_defn(field_defn, fmt):
    """
    For MIF output only.
    MIF doesn't support all OGR field types, so convert fields to a simpler format that is compatible in MIF.
    """

    SHP_MAX_FIELD_NAME_LEN = 10

    if fmt == GIS_MIF:
        if field_defn.type in [ogr.OFTInteger64, ogr.OFTIntegerList, ogr.OFTInteger64List]:
            field_defn.type = ogr.OFTInteger
        elif field_defn.type in [ogr.OFTRealList]:
            field_defn.type = ogr.OFTReal
        elif field_defn.type in [ogr.OFTStringList, ogr.OFTWideString, ogr.OFTWideStringList]:
            field_defn.type = ogr.OFTString

    if fmt == GIS_SHP:
        if len(field_defn.name) > SHP_MAX_FIELD_NAME_LEN:
            field_defn.name = field_defn.name[:SHP_MAX_FIELD_NAME_LEN]

    return field_defn


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


def arg_to_ogr_format(arg):
    """Helper function to convert CLI argument for vector format to OGR driver name."""

    if re.findall(r'^(GPKG|GEO\s?PACKAGE)$', arg.strip(' \t"\''), flags=re.IGNORECASE):
        return GIS_GPKG
    if re.findall(r'^(MI[F]?|MAPINFO(\sFILE)?|MITAB)$', arg.strip(' \t"\''), flags=re.IGNORECASE):
        return GIS_MIF
    if re.findall(r'^(SHP|(ESRI\s)?SHAPE\s?FILE)$', arg.strip(' \t"\''), flags=re.IGNORECASE):
        return GIS_SHP

    return None


def arg_to_gdal_format(arg):
    """Helper function to convert CLI argument for raster format to GDAL driver name."""

    if re.findall(r'^(GPKG|GEO\s?PACKAGE)$', arg.strip(' \t"\''), flags=re.IGNORECASE):
        return GRID_GPKG
    if re.findall(r'^(ASC(I){0,2}|TXT|DEM|AAIGRID)$', arg.strip(' \t"\''), flags=re.IGNORECASE):
        return GRID_ASC
    if re.findall(r'^(FLT|E?HDR|BINARY|FLOAT)$', arg.strip(' \t"\''), flags=re.IGNORECASE):
        return GRID_FLT
    if re.findall(r'^(G?TIF{1,2}|GEOTIF{1,2})$', arg.strip(' \t"\''), flags=re.IGNORECASE):
        return GRID_TIF

    return None


def is_multi_part(feat=None, lyr=None):
    MULTIPART = [ogr.wkbMultiPoint, ogr.wkbMultiLineString, ogr.wkbMultiPolygon]
    if feat is not None and feat.geometry() is not None:
        return ogr_basic_geom_type(feat.geometry().GetGeometryType(), False) in MULTIPART

    if lyr is not None:
        return bool([f for f in lyr if ogr_basic_geom_type(f.geometry().GetGeometryType(), False) in MULTIPART])

    return False


def ogr_create(uri, geom_suffix, schema, projection_wkt, settings=None):
    db, lyrname = get_database_name(uri)
    sr = osr.SpatialReference(projection_wkt)

    fmt = ogr_format(db)
    driver = ogr.GetDriverByName(fmt)
    if TuflowPath(db).exists() and fmt == GIS_GPKG:
        datasource = driver.Open(db, 1)
    elif TuflowPath(db).exists():
        datasource = driver.Open(db, 1)
        if datasource is not None:
            datasource.DeleteLayer(0)
        elif fmt == GIS_MIF:
            try:
                err = driver.DeleteDataSource(db)
                if err != ogr.OGRERR_NONE:
                    gis_manual_delete(db, fmt)
            except Exception as e:
                if settings is not None:
                    settings.errors = True
                raise MinorConvertException(f'Error: Could not overwrite existing file: {db}')
            datasource = driver.CreateDataSource(db)
    else:
        TuflowPath(db).parent.mkdir(parents=True, exist_ok=True)
        datasource = driver.CreateDataSource(db)
    if gdal_error() or datasource is None:
        if settings is not None:
            settings.errors = True
        raise MinorConvertException(f'Error: Failed to open: {db}')

    options = ['OVERWRITE=YES'] if fmt == GIS_GPKG else []
    geom_type = suffix_2_geom_type(geom_suffix)

    lyr = datasource.CreateLayer(lyrname, sr, geom_type, options)
    if gdal_error() or lyr is None:
        if settings is not None:
            settings.errors = True
        datasource = None
        raise MinorConvertException(f'Error: Failed to create layer {lyrname}')

    for field in schema:
        f = ogr.FieldDefn(field.name, field.type)
        if field.width is not None:
            f.SetWidth(field.width)
        if field.prec is not None:
            f.SetPrecision(field.prec)
        lyr.CreateField(f)

    datasource, lyr = None, None

def arg_to_projection(crs_ref):
    if ':' in crs_ref:
        auth, id_ = [x.strip() for x in crs_ref.split(':')]
        return authid_to_wkt(auth, int(id_))
    elif 'PROJCS' in crs_ref.upper():
        # return authid_to_wkt('WKT', crs_ref)
        return crs_ref
    elif 'coordsys earth projection' in crs_ref.lower():
        return authid_to_wkt('MI', crs_ref)
    else:
        return crs_ref


def authid_to_wkt(auth, id_):
    sr = osr.SpatialReference()
    try:
        if auth.lower() == 'epsg':
            sr.ImportFromEPSG(id_)
        elif auth.lower() == 'esri':
            sr.ImportFromESRI(id_)
        elif auth.lower() == 'epsga':
            sr.ImportFromEPSGA(id_)
        elif auth.lower() == 'wkt':
            sr.ImportFromWkt(id_)
        elif auth.lower() == 'mi':
            sr.ImportFromMICoordSys(id_)

        if gdal_error() or sr is None:
            return
    except Exception as e:
        return

    return sr.ExportToWkt()

