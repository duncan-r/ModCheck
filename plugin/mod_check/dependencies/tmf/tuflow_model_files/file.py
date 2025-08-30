import os
import re
import sys
import typing
from contextlib import contextmanager
from pathlib import Path, PosixPath, WindowsPath
from typing import OrderedDict


class OGROpen:

    def __init__(self, path, mode):
        self.fpath = path
        self.mode = mode
        self.driver = None
        self.ds = None
        self.lyr = None
        self.fmt = None
        self.open(path, mode)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __next__(self):
        for feat in self.lyr:
            yield feat

    def __iter__(self):
        return self.__next__()

    def open(self, path, mode):
        from .gis import ogr_format, ogr, get_driver_name_from_gis_format
        self.fmt = ogr_format(self.fpath)
        driver_name = get_driver_name_from_gis_format(self.fmt)
        self.driver = ogr.GetDriverByName(driver_name)
        if self.mode == 'r':
            if not path.exists():
                raise FileExistsError(f'Could not open {path} for reading')
            self.ds = self.driver.Open(str(path.dbpath))
        else:
            if os.path.exists(path.dbpath):
                self.ds = self.driver.Open(str(path.dbpath), 1)
            else:
                self.ds = self.driver.CreateDataSource(str(path.dbpath))
        if self.ds is None:
            raise Exception(f'Could not open {path.dbpath}')
        self.lyr = self.ds.GetLayer(path.lyrname)
        if mode == 'w' and self.lyr is not None:
            self.ds.DeleteLayer(path.lyrname)
            self.lyr = None
        if mode == 'w' or mode == 'r+' and self.lyr is None:
            self.lyr = self.ds.CreateLayer(path.lyrname)
        if self.lyr is None:
            raise Exception(f'Could not open layer {path.lyrname}')

    def close(self):
        for k, v in globals().copy().items():
            if v == self.lyr or v == self.ds:
                del globals()[k]
        self.ds, self.lyr = None, None


class TuflowPath(Path):
    """Extension of the :code:`Path` class - :code:`Path` is nicer to use than :code:`os`, but doesn't resolve
    TUFLOW wildcards/variables '<< >>'  that can appear in file path references with TUFLOW control files,
    nor does it handle TUFLOW GPKG style paths :code:`'database >> layername'` very well.

    A number of methods have been overridden to handle GPKG databases, such as the 'glob' method which now works
    to search for layers within a GPKG database.
    """

    def __new__(cls, *args, **kwargs):
        cls = TuflowWindowsPath if os.name == 'nt' else TuflowPosixPath
        if os.name != 'nt' and len(args) == 1 and '\\' in str(args[0]):
            # This is probably a Windows path being read on a POSIX system
            parts = (str(args[0]).replace('\\', '/'),)
        else:
            parts = args

        # noinspection PyUnreachableCode
        if sys.version_info >= (3, 12):
            self = object.__new__(cls)
        else:
            try:
                self = cls._from_parts(parts, init=False)
                self._init()
            except TypeError:
                self = cls._from_parts(parts)

        if args and str(args[0]) and (str(args[0])[-1] == '\\' or str(args[0])[-1] == '/'):
            self._end_slash = True
        else:
            self._end_slash = False

        return self

    def __init__(self, *args):
        if sys.version_info >= (3, 12):
            if os.name != 'nt' and '\\' in str(args[0]):
                args_ = [str(a).replace('\\', '/') for a in args]
                super().__init__(*args_)
            else:
                super().__init__(*args)

    def __contains__(self, item):
        if isinstance(item, str):
            return item in str(self)
        else:
            raise TypeError(f'unsupported operand type(s) for in: {type(self)} and {type(item)}')

    def __eq__(self, other):
        from .gis import get_database_name
        if isinstance(other, Path):
            db1, lyr1 = get_database_name(self)
            db2, lyr2 = get_database_name(other)
            return Path(db1) == Path(db2) and lyr1.lower() == lyr2.lower()
        else:
            return False

    def __hash__(self):
        return hash(str(self))

    @property
    def suffix(self):
        return os.path.splitext(self.dbname)[1]

    @property
    def dbname(self):
        #: str: The database basename with the extension.
        if ' >> ' in str(self):
            return os.path.basename(str(self).split(' >> ')[0])
        if '|' in str(self):
            return os.path.basename(str(self).split('|')[0])
        return self.name

    @property
    def dbpath(self):
        #: TuflowPath: The database path.
        if ' >> ' in str(self):
            return TuflowPath(str(self).split(' >> ')[0])
        if '|' in str(self):
            return TuflowPath(str(self).split('|')[0])
        return self

    @property
    def lyrname(self):
        #: str: The layer name.
        if ' >> ' in str(self):
            return str(self).split(' >> ')[1]
        if '|layername=' in str(self):
            return str(self).split('|')[1].split('=')[1]
        if '|' in str(self):
            return os.path.splitext(os.path.basename(str(self).split('|')[0]))[0]
        return self.stem

    @contextmanager
    def connect(self):
        """Context manager to open a connection to the database."""
        import sqlite3
        conn = None
        try:
            conn = sqlite3.connect(self.dbpath)
            yield conn
        finally:
            if conn:
                conn.close()

    def is_relative_to(self, other, **kwargs):
        from .gis import get_database_name
        db1, _ = get_database_name(self)
        db2, _ = get_database_name(other)
        return Path(db1).is_relative_to(Path(db2))

    def relative_to(self, other, **kwargs):
        from .gis import get_database_name
        db1, _ = get_database_name(self)
        db2, lyr = get_database_name(other)
        p = Path(db1).relative_to(Path(db2))
        if lyr != Path(db2).stem:
            p = TuflowPath(str(p) + ' >> ' + lyr)
        return p

    def open_gis(self, mode='r'):
        """Open the path as a GDAL dataset. Only supports vector layers.

        Parameters
        ----------
        mode : str, optional
            The mode to open the dataset in. The default is 'r'.

        Returns
        -------
        OGROpen
            The opened dataset. OGROpen opens the dataset with a context manager and contains the attributes
            :code:`ds` and :code:`lyr` which are the dataset and layer respectively. Normal OGR methods can be used on
            these attributes.
        """
        return OGROpen(self, mode)

    def gis_attributes(self) -> typing.Generator[OrderedDict[str, typing.Any], None, None]:
        """Yield GIS attributes from the layer. Does not require GDAL, but also does not read geometry and
        only supports GPKG, MIF, and SHP files.
        """
        from .gis import GISAttributes
        with GISAttributes(self) as attr:
            yield from attr

    def split(self, separator, maxsplit=-1):
        """Split the path into parts based on the given separator.

        Parameters
        ----------
        separator : str
            The separator to split the path on.
        maxsplit : int, optional
            The maximum number of splits to perform. The default is -1.

        Returns
        -------
        list[str]
            The split parts of the path.
        """
        return str(self).split(separator, maxsplit)

    def exists(self, **kwargs) -> bool:
        import sqlite3
        if self.suffix.lower() == '.gpkg':
            if ' >> ' not in str(self):
                return os.path.exists(self.dbpath)
            else:
                if not os.path.exists(self.dbpath):
                    return False
            try:
                with self.connect() as conn:
                    cur = conn.cursor()
                    cur.execute(f"SELECT COUNT(*) FROM gpkg_contents WHERE UPPER(table_name)='{self.lyrname.upper()}';")
                    count = cur.fetchone()[0]
            except sqlite3.Error:
                count = 0
            return count > 0

        return os.path.exists(self.dbpath)

    def with_suffix(self, suffix: str):
        return TuflowPath(Path.with_suffix(self, suffix))

    def upper(self):
        """Converts the path to an uppercase string object.

        Returns
        -------
        str
            The path as an uppercase string.
        """
        return str(self).upper()

    def lower(self):
        """Converts the path to an lowercase string object.

        Returns
        -------
        str
            The path as an lowercase string.
        """
        return str(self).lower()

    def resolve(self, strict=...):
        """Override method so it will work with TUFLOW style wildcards/variables."""

        try:
            return TuflowPath(Path(os.path.abspath(self)))
        except OSError:
            found = True
            path = TuflowPath(os.path.abspath(self))
            i = 0
            for i, part in enumerate(path.parts):
                if '~' in part:
                    found = True
                    break
            if not found:
                return path
            p = Path(*path.parts[:i])
            try:
                p = p.resolve()
            except OSError:
                pass
            for part in path.parts[i:]:
                p = p / part
            return TuflowPath(p)

    def glob(self, pattern, wildcards=()):
        """Override method so can do some stuff with TUFLOW style wildcards/variables and also GPKG databases."""

        from .gis import get_database_name, GPKG
        from .tfstrings.patterns import globify

        if str(pattern).count('>>') > str(pattern).count('<<') and str(pattern).count('>>') > 1:
            db, lyr = get_database_name(pattern)
        elif '>>' in str(pattern):
            db, lyr = [x.strip() for x in str(pattern).split('>>', 1)]
            if not db:
                db = str(self.dbpath)
            if lyr == '':
                lyr = None
        else:
            db, lyr = pattern, None

        def glob_consider_gpkg(file_path, lyr_name):
            if file_path.suffix.upper() != '.GPKG':
                if lyr_name is not None:
                    yield TuflowPath(f'{file_path.absolute()} >> {file_path.with_suffix("").name}')
                else:
                    yield TuflowPath(file_path.absolute())
            else:
                lyr_name = globify(lyr_name, wildcards)
                for lyr_name_1 in GPKG(file_path).glob(lyr_name):
                    yield TuflowPath(f'{file_path.absolute()} >> {lyr_name_1}')

        try:
            for file in Path(self).glob(db):
                yield from glob_consider_gpkg(file, lyr)
        except NotImplementedError:
            if '*' not in db:
                for file in Path(db).parent.glob(Path(db).name):
                    yield from glob_consider_gpkg(file, lyr)
            else:
                lowest_part = db.split('*')[0]
                p = Path(lowest_part).parent
                n = Path(lowest_part).name
                rel_path = n + '*'.join(db.split('*')[1:])
                for file in p.glob(rel_path):
                    yield from glob_consider_gpkg(file, lyr)

    def re(self, pattern, flags=None):
        """Similar to glob, but use regular expression pattern.

        Parameters
        ----------
        pattern : str
            The regular expression pattern to search for.
        flags : int, optional
            The regular expression flags to use. The default is None.

        Yields
        ------
        TuflowPath
            The path that matches the regular expression pattern.
        """

        for dir_, filenames in {dir_: [y for y in x] for dir_, _, x in os.walk(self)}.items():
            for filename in filenames:
                if re.findall(pattern, filename, flags=flags):
                    yield (TuflowPath(dir_) / filename).absolute()

    def read_file_for_parent(self):
        """TUFLOW control file specific method. Searches control file for file references to try and find
        the root model directory e.g. typically what is called the 'TUFLOW' folder.

        Returns
        -------
        TuflowPath
            The root model directory if found, otherwise the parent directory.
        """
        max_count = 0
        if not self.exists():
            return self.parent

        with self.open() as f:
            for line in f:
                if '==' in line:
                    if '!' in line and line.index('!') < line.index('=='):
                        continue
                    _, value = [x.strip() for x in line.split('==', 1)]
                    count = len(re.findall(r'\.{2}[\\/]', value))
                    max_count = max(count, max_count)
        if max_count:
            return (self.parent / (f'..{os.sep}' * max_count)).absolute()

        return self.parent

    def find_folder_in_path(self, folder_name):
        """Returns the path to the folder name if it exists.

        | e.g. C:/tuflow/path/gis/control_file.tcf
        | :code:`find_folder_in_path('gis')` returns C:/tuflow/path/gis

        Parameters
        ----------
        folder_name : str
            The folder name to search for.

        Returns
        -------
        TuflowPath
            The path to the folder if found, otherwise None.
        """
        parts = [x.lower() for x in self.parts]
        if folder_name.lower() not in parts:
            return None
        i = parts.index(folder_name)
        j = len(parts) - i - 1
        folder_path = TuflowPath(self)
        for i in range(j):
            folder_path = folder_path.parent
        return folder_path

    def find_in_walk_dir(self, name, index_=None, ignore_case=True, exclude=None):
        """Similar to find_parent but is not restrained by it having to be a direct parent, and will look into
        other folders.

        Parameters
        ----------
        name : str
            The folder name to search for.
        index_ : int, optional
            The number of folders to search up from the path. The default is None.
        ignore_case : bool, optional
            Whether to ignore case when searching. The default is False.
        exclude : str, optional
            The folder to exclude from the search. The default is None.

        Returns
        -------
        TuflowPath
            The path to the folder if found, otherwise None.
        """
        if index_ is None:
            p = TuflowPath(self.parts[0])
        else:
            i = -index_ + 1
            if i >= 0:
                p = TuflowPath('').joinpath(*self.parts[:])
            else:
                p = TuflowPath('').joinpath(*self.parts[:-index_ + 1])

        folders = sum([[y for y in names] for dir_, names, _ in os.walk(p) if not exclude or str(exclude) not in dir_],
                      [])
        if ignore_case:
            if name.lower() in [x.lower() for x in folders]:
                return self._walk_dir(p, name, ignore_case)
            return None
        else:
            if name in folders:
                return self._walk_dir(p, name)
            return None

    def _walk_dir(self, dir_, name, ignore_case=False):
        """Helper routine for 'find_in_walk_dir'."""
        if ignore_case:
            for _, dirname, _ in os.walk(dir_):
                for dn in dirname:
                    if dn.lower() == name.lower():
                        return TuflowPath(str(os.path.join(dir_, dn)))
                    else:
                        dir_found = self._walk_dir(os.path.join(dir_, dn), name, ignore_case)
                        if dir_found:
                            return dir_found
                break
        else:
            for _, dirname, _ in os.walk(dir_):
                for dn in dirname:
                    if dn == name:
                        return TuflowPath(str(os.path.join(dir_, dn)))
                    else:
                        dir_found = self._walk_dir(os.path.join(dir_, dn), name)
                        if dir_found:
                            return dir_found
                break
        raise NotImplementedError('Unable to walk directory to find folder: {0}'.format(name))

    def is_file_binary(self) -> bool:
        """Tests if a file is binary or not.

        Uses method from file(1) behaviour.
        https://github.com/file/file/blob/f2a6e7cb7db9b5fd86100403df6b2f830c7f22ba/src/encoding.c#L151-L228
        """
        textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
        is_binary_string = lambda b: bool(b.translate(None, textchars))
        try:
            with self.open('rb') as f:
                return is_binary_string(f.read(1024))
        except (FileNotFoundError, OSError, TypeError, AttributeError, ValueError):
            return False


class TuflowWindowsPath(WindowsPath, TuflowPath):

    def __str__(self):
        str_ = super().__str__()
        try:
            if self._end_slash:
                str_ = '{0}{1}'.format(str_, os.sep)
        except AttributeError:
            pass

        return str_

    def __truediv__(self, other):
        return TuflowPath(WindowsPath.__truediv__(self, other))

    def __hash__(self):
        return hash(str(self))


class TuflowPosixPath(PosixPath, TuflowPath):

    def __str__(self):
        str_ = str(PosixPath.__str__(self))
        try:
            if self._end_slash:
                str_ = '{0}{1}'.format(str_, os.sep)
        except AttributeError:
            pass

        return str_

    def __truediv__(self, other):
        return TuflowPath(PosixPath.__truediv__(self, other))

    def __hash__(self):
        return hash(str(self))

    def find_in_walk_dir(self, name, index_=None, ignore_case=False, exclude=None):
        """Similar to find_parent but is not restrained by it having to be a direct parent, and will look into
        other folders.

        Parameters
        ----------
        name : str
            The folder name to search for.
        index_ : int, optional
            The number of folders to search up from the path. The default is None.
        ignore_case : bool, optional
            Whether to ignore case when searching. The default is False.
        exclude : str, optional
            The folder to exclude from the search. The default is None.

        Returns
        -------
        TuflowPath
            The path to the folder if found, otherwise None.
        """
        return super().find_in_walk_dir(name, index_, ignore_case, exclude)
