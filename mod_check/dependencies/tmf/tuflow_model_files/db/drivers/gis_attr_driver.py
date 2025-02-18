from collections import OrderedDict
from collections.abc import Iterable
from pathlib import Path
from ...dataclasses.file import TuflowPath

from ...dataclasses.types import PathLike

try:
    from osgeo import ogr
    has_gdal = True
except ImportError:
    has_gdal = False


class GISAttributes(Iterable):
    """Utility class for iterating over a GIS layer to obtain the attributes."""

    def __new__(cls, fpath: PathLike) -> object:
        if has_gdal:
            cls = GDALGISAttributes
            return super().__new__(cls)
        fpath = TuflowPath(fpath)
        if '>>' in fpath:
            fpath = fpath.split(' >> ')[0]
        fpath = Path(fpath)
        if fpath.suffix.lower() == '.dbf' or fpath.suffix.lower() == '.shp':
            cls = DBFAttributes
        elif fpath.suffix.lower() == '.mid' or fpath.suffix.lower() == '.mif':
            cls = MIDAttributes
        elif fpath.suffix.lower() == '.gpkg':
            cls = GPKGAttributes
        return super().__new__(cls)

    def __init__(self, fpath: PathLike) -> None:
        """
        Parameters
        ----------
        fpath : PathLike
            The file path to the GIS file.
        """
        self.fpath = TuflowPath(fpath)
        self._db = None
        self.open()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self) -> None:
        """Open the GIS file for reading."""
        raise NotImplementedError

    def close(self) -> None:
        """Close the GIS file."""
        raise NotImplementedError


class GDALGISAttributes(GISAttributes):

    def __init__(self, fpath: PathLike) -> None:
        from ...utils.gis import get_driver_name_from_extension
        fpath = TuflowPath(fpath)
        self._driver = get_driver_name_from_extension('vector', fpath.suffix)

        super().__init__(fpath)

    def __iter__(self):
        for feat in self._lyr:
            d = OrderedDict()
            for i in range(feat.GetFieldCount()):
                fld = feat.GetFieldDefnRef(i)
                d[fld.GetName()] = feat.GetField(i)
            yield d

    def open(self) -> None:
        self._ds = ogr.Open(str(self.fpath.dbpath))
        self._lyr = self._ds.GetLayer(self.fpath.lyrname)

    def close(self) -> None:
        self._lyr = None
        self._ds = None


class DBFAttributes(GISAttributes):
    """Utility class for iterating over a SHP/DBF file to obtain the attributes."""

    def __init__(self, fpath: PathLike) -> None:
        # docstring inherited
        fpath = TuflowPath(fpath).dbpath
        if fpath.suffix.lower() == '.shp':
            if fpath.with_suffix('.dbf').exists():
                fpath = fpath.with_suffix('.dbf')
            elif fpath.with_suffix('.DBF').exists():
                fpath = fpath.with_suffix('.DBF')
            else:
                raise FileNotFoundError(f'Accompanying DBF file not found for: {self.fpath}')
        super().__init__(fpath)

    def __iter__(self) -> OrderedDict:
        for record in self._db:
            yield record

    def open(self) -> None:
        # docstring inherited
        from dbfread import DBF
        self._db = DBF(self.fpath)

    def close(self) -> None:
        # docstring inherited
        self._db = None


class MIDAttributes(GISAttributes):
    """Utility class for iterating over a MIF/MID file to obtain the attributes."""

    def __init__(self, fpath: PathLike) -> None:
        # docstring inherited
        fpath = TuflowPath(fpath).dbpath
        self._col_names = []
        if fpath.suffix.lower() == '.mif':
            self._mif = fpath
            if fpath.with_suffix('.mid').exists():
                fpath = fpath.with_suffix('.mid')
            elif fpath.with_suffix('.MID').exists():
                fpath = fpath.with_suffix('.MID')
            else:
                raise FileNotFoundError(f'Accompanying MID file not found for: {fpath}')
        else:
            if fpath.with_suffix('.mif').exists():
                self._mif = fpath.with_suffix('.mif')
            elif fpath.with_suffix('.MIF').exists():
                self._mif = fpath.with_suffix('.MIF')
            else:
                raise FileNotFoundError(f'Accompanying MIF file not found for: {fpath}')
        super().__init__(fpath)

    def __iter__(self) -> OrderedDict:
        for line in self._db:
            yield OrderedDict(zip(self._col_names, [x.strip(' \t\n"\'') for x in line.split(',')]))

    def open(self) -> None:
        # docstring inherited
        self._db = self.fpath.open()
        ncol = 0
        with self._mif.open() as f:
            for line in f:
                if line.startswith('Columns'):
                    ncol = int(line.split()[1])
                    for i in range(ncol):
                        self._col_names.append(f.readline().split()[0])
                    break
        if not ncol:
            raise Exception(f'MIF file must have at least one attribute column: {self._mif}')

    def close(self) -> None:
        # docstring inherited
        self._db.close()
        self._db = None


class GPKGAttributes(GISAttributes):
    """Utility class for iterating over a GPKG file to obtain the attributes."""

    def __init__(self, fpath: TuflowPath) -> None:
        fpath = TuflowPath(fpath)
        self._tname = fpath.lyrname
        fpath = fpath.dbpath
        self._tname = self._get_case_insensitive_table_name(fpath, self._tname)
        self._geom_col = self._get_geom_col(fpath, self._tname)
        self._fid_col = self._get_fid_col(fpath, self._tname)
        super().__init__(fpath)

    def __iter__(self) -> OrderedDict:
        import sqlite3
        try:
            self._db = sqlite3.connect(self.fpath)
            self._cursor = self._db.cursor()
            self._cursor.execute(f'SELECT * FROM "{self._tname}";')
            for row in self._cursor:
                inds = [i for i, x in enumerate(self._cursor.description) if x[0] not in (self._fid_col, self._geom_col)]
                yield OrderedDict([(self._cursor.description[i][0], row[i]) for i in inds])
        except:
            pass
        finally:
            self._db.close()
            self._cursor = None
            self._db = None

    def open(self) -> None:
        # docstring inherited
        pass

    def close(self) -> None:
        # docstring inherited
        pass

    def _get_case_insensitive_table_name(self, fpath: PathLike, tname: str) -> str:
        import sqlite3
        db = sqlite3.connect(fpath)
        try:
            cursor = db.cursor()
            cursor.execute(f'SELECT name FROM sqlite_master WHERE type="table" AND name="{tname}" COLLATE NOCASE;')
            tname = cursor.fetchone()[0]
        except:
            tname = tname
        finally:
            db.close()
            return tname

    def _get_geom_col(self, fpath: PathLike, tname: str) -> str:
        import sqlite3
        db = sqlite3.connect(fpath)
        try:
            cursor = db.cursor()
            cursor.execute(f'SELECT column_name FROM gpkg_geometry_columns WHERE table_name="{tname}";')
            geom_col = cursor.fetchone()[0]
        except:
            geom_col = 'geometry'
        finally:
            db.close()
        return geom_col

    def _get_fid_col(self, fpath: PathLike, tname: str) -> str:
        import sqlite3
        db = sqlite3.connect(fpath)
        try:
            cursor = db.cursor()
            cursor.execute(f'SELECT name FROM PRAGMA_TABLE_INFO("{self._tname}") WHERE pk = 1;')
            fid_col = cursor.fetchone()[0]
        except:
            fid_col = 'fid'
        finally:
            db.close()
        return fid_col
