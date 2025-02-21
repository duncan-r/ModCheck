import json
import shutil
import re
import os
import sys
from pathlib import Path, WindowsPath, PosixPath, PurePath

from .stubs import ogr

from .settings import MinorConvertException
from .settings import tuf_dir_struct


def copy_file(parent_file, rel_path, output_parent, wildcards, tuf_dir_struct, key, root_output_folder):
    """Copy file routine that will also expand glob patterns."""

    file_dest = None
    rel_path_ = globify(rel_path, wildcards)
    copy_count = None
    try:
        if output_parent is not None:
            for copy_count, file_src in enumerate(parent_file.parent.glob(rel_path_)):
                file_src = file_src.resolve()
                try:
                    if tuf_dir_struct:
                        file_dest = replace_with_tuf_dir_struct(file_src, root_output_folder, None, key)
                    else:
                        rp = os.path.relpath(file_src, parent_file.parent.resolve())
                        file_dest = (output_parent.parent / rp).resolve()
                    file_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(file_src, file_dest)
                except ValueError:
                    rp = file_src
    except Exception as e:
        raise MinorConvertException(f'Error: {e}')

    if copy_count is not None:
        return file_dest
    else:
        return None


def copy_file2(file_src, file_dest):
    """More basic copy file routine with a different signature. Does not expand glob."""

    try:
        file_dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file_src, file_dest)
    except Exception as e:
        raise MinorConvertException(f'Error: {e}')


def copy_rainfall_grid_csv(file_src, file_dest, settings):
    """
    Routine that will loop through a CSV file specified by READ GRID RF == <csv>
    and convert the grid names to have the correct extension.
    """

    from .gis import get_database_name, gdal_format_2_ext

    try:
        regex = re.compile(r'\.(FLT|ASC|TIF|TIFF|GTIFF|TXT|DEM|GPKG).*', flags=re.IGNORECASE)
        out_ext = gdal_format_2_ext(settings.output_grid_format)
        file_dest.parent.mkdir(parents=True, exist_ok=True)
        with file_src.open() as f1:
            with file_dest.open('w') as f2:
                for i, line in enumerate(f1):
                    try:
                        float(line.split(',')[0])
                    except Exception:
                        f2.write(line)
                        continue

                    rf_timestep = line.split(',', 1)
                    if len(rf_timestep) < 2:
                        f2.write(line)
                        continue

                    time, source = [x.strip() for x in rf_timestep]

                    db, lyr = get_database_name(source)
                    if lyr is not None:
                        db = f'{TuflowPath(db).parent / lyr}{TuflowPath(db).suffix}'  # don't need to use with_suffix() as lyr has had suffix stripped
                    new_source = regex.sub(out_ext, str(db))
                    new_line = f'{time},{new_source}'

                    f2.write(new_line)
    except Exception as e:
        settings.errors = True
        raise MinorConvertException(f'Error: {e}')


def globify(infile, wildcards):
    """Converts TUFLOW wildcards (variable names, scenario/event names) to '*' for glob pattern."""

    infile = str(infile)
    if wildcards is None:
        return infile

    for wc in wildcards:
        infile = re.sub(wc, '*', infile, flags=re.IGNORECASE)
    if re.findall(r'\*\*(?![\\/])', infile):
        infile = re.sub(re.escape(r'**'), '*', infile)

    return infile


def insert_variables(line, variables):
    from .command import Command
    if line is None:
        return line

    line = str(line)
    for var_name, var_val in variables.items():
        if f'<<{var_name.upper()}>>' in line.upper():
            if Command.is_value_a_number_2(var_val, '', 0):
                var_val_ = str(var_val)
            else:
                var_val_ = re.escape(str(var_val))
            line = re.sub(re.escape(rf'<<{var_name}>>'), var_val_, line, flags=re.IGNORECASE)

    return line


def tuflowify_value(value, settings, is_folder=False):
    """
    Converts READ GIS and READ GRID commands to all follow a
    database >> layername structure. Useful to keep everything consistent.

    Will correct GPKG specific commands that use '&&' and 'ALL' to database >> layername | database >> layername
    """

    from .gis import get_all_layers_in_gpkg, get_database_name

    value = insert_variables(value, settings.variables)
    value = value.strip(' \t\n|')

    if value.count('>>') > value.count('<<'):
        if 'ALL' in value.upper():
            if '|' in value:
                lyrs = [x.strip() for x in value.split('|')]
            else:
                lyrs = [value]

            for i, lyr in enumerate(lyrs[:]):
                if lyr.count('>>') > lyr.count('<<'):
                    db, lyr_ = get_database_name(lyr)
                    if lyr_.upper() == 'ALL':
                        lyr_ = ' && '.join(get_all_layers_in_gpkg((settings.control_file.parent / db).resolve()))
                        lyrs[i] = f'{db} >> {lyr_}'

            value = ' | '.join(lyrs)

        if '&&' in value:
            if '|' in value:
                lyrs = [x.strip() for x in value.split('|')]
            else:
                lyrs = [value]
            lyrs_ = []
            for lyr in lyrs:
                if lyr.count('>>') > lyr.count('<<'):
                    db, lyr_ = get_database_name(lyr)
                    lyrs_.extend([f'{db} >> {x.strip()}' for x in lyr_.split('&&')])
                else:
                    lyrs_.append(lyr)
            return ' | '.join(lyrs_)
        elif '|' in value:
            return value
        else:
            db, lyr = get_database_name(value)
            if settings.control_file is not None:
                db = (settings.control_file.parent / db).resolve()
    else:
        if '&&' in value:
            return value.replace('&&', '|')
        if '|' in value:
            return value

        db = TuflowPath(value)
        try:
            lyr = db.with_suffix('').name
        except Exception:
            # not a file
            if settings.control_file is not None:
                db = (settings.control_file.parent / db).resolve()
            return str(db)

        if settings.control_file:
            if is_folder:
                db = (settings.control_file.parent / db).resolve()
            elif db.suffix:
                db = (settings.control_file.parent / db).resolve()
            elif settings.read_spatial_database:
                db = settings.read_spatial_database
            else:
                db = db.with_suffix('.mif')
                db = (settings.control_file.parent / db).resolve()

    return f'{db} >> {lyr}'


def expand_path(value, settings, gis_file=False):
    value = str(value)
    if gis_file:
        if '|' in value:
            layers = []
            for file in value.split('|'):
                file = file.strip()
                try:
                    float(file)
                    is_a_number = True
                except ValueError:
                    is_a_number = False
                if not is_a_number:
                    if re.findall(r'<<.+?>>', file) and re.findall(r'<<.+?>>', file) == file:
                        is_a_number = True
                if is_a_number:
                    layers.append(file)
                else:
                    layers.append(tuflowify_value(file, settings))
            return ' | '.join([str(x) for x in layers])
        else:
            return tuflowify_value(value.strip(), settings)

    if settings.control_file is None:
        return value

    if '|' in value:
        layers = []
        for file in value.split('|'):
            file = file.strip()
            try:
                float(file)
                is_a_number = True
            except ValueError:
                is_a_number = False
            if not is_a_number:
                if re.findall(r'<<.+?>>', file) and re.findall(r'<<.+?>>', file) == file:
                    is_a_number = True
            if is_a_number:
                layers.append(file)
            else:
                layers.append(tuflowify_value(file, settings))
        return ' | '.join([str(x) for x in layers])
    else:
        return value.strip()


def add_geom_suffix(name_, suffix):
    """Add geometry suffix to name if it doesn't already exist."""

    name_ = str(name_)

    if not suffix or re.findall(rf'{re.escape(suffix)}$', TuflowPath(name_).with_suffix("").name, flags=re.IGNORECASE):
        return name_

    return f'{TuflowPath(name_).with_suffix("")}{suffix}{TuflowPath(name_).suffix}'


def remove_geom_suffix(name_):
    """Removes geometry suffix from name if it exists."""

    if name_ is None:
        return None

    new_name =  re.sub(r'_[PLR]$', '', str(TuflowPath(name_).with_suffix("")), flags=re.IGNORECASE)

    return TuflowPath(new_name).with_suffix(TuflowPath(name_).suffix)


def get_geom_suffix(name_):
    """Returns geometry suffix from the name if it exists."""

    if re.findall(r'_[PLR]$', str(TuflowPath(name_).with_suffix("")), flags=re.IGNORECASE):
        return re.findall(r'_[PLR]$', str(TuflowPath(name_).with_suffix("")), flags=re.IGNORECASE)[0]

    return ''


def change_gis_mi_folder(path, in_gis_format, out_gis_format):
    """Switches the mi and gis folder path depending on whether the output is MIF format or not."""

    from .gis import GIS_MIF

    path = str(path)

    if in_gis_format == out_gis_format:
        return path

    if out_gis_format == GIS_MIF:
        return re.sub(r'(?:(?<=[\\/])|(?<=^))gis(?=[\\/])', 'mi', path, flags=re.IGNORECASE)
    else:
        return re.sub(r'(?:(?<=[\\/])|(?<=^))mi(?=[\\/])', 'gis', path, flags=re.IGNORECASE)


def replace_with_output_filepath(inpath, inparent, outparent, control_file):
    """Replace input path with output path."""

    if control_file is not None:
        try:
            return os.path.relpath(inpath, control_file.parent)
        except ValueError:
            return inpath
    else:
        try:
            relpath = TuflowPath(inpath).relative_to(TuflowPath(inparent))
            return (outparent / relpath).resolve()
        except Exception:
            return TuflowPath(inpath)


def tuflow_stnd_path(inpath, key):
    if key and key in tuf_dir_struct['folder_structure']:
        return tuf_dir_struct['folder_structure'][key]
    elif inpath.suffix and inpath.suffix.lower() in tuf_dir_struct['mappings']:
        return tuf_dir_struct['folder_structure'][tuf_dir_struct['mappings'][inpath.suffix.lower()]]
    return tuf_dir_struct['folder_structure']['other']


def replace_with_tuf_dir_struct(inpath, outparent, command, key):
    if command and command.is_bc_dbase_file():
        return (outparent / tuflow_stnd_path(inpath, 'bc_dbase') / inpath.name).resolve()
    elif command and command.is_read_grid() and command.is_read_xf():
        return (outparent / tuflow_stnd_path(inpath, 'grid/xf') / inpath.name).resolve()
    elif command and command.is_read_grid():
        return (outparent / tuflow_stnd_path(inpath, 'grid') / inpath.name).resolve()
    elif command and command.is_read_tin():
        return (outparent / tuflow_stnd_path(inpath, 'tin') / inpath.name).resolve()
    elif command and command.is_log_folder():
        return (outparent / tuflow_stnd_path(inpath, 'log') / inpath.name).resolve()
    elif command and command.is_output_folder():
        return (outparent / tuflow_stnd_path(inpath, 'results') / inpath.name).resolve()
    elif command and command.is_check_folder():
        return (outparent / tuflow_stnd_path(inpath, 'check') / inpath.name).resolve()
    elif command and command.is_rainfall_grid_nc():
        return (outparent / tuflow_stnd_path(inpath, 'bc_dbase') / inpath.name).resolve()
    elif command and command.is_read_gis() and command.is_read_xf():
        return (outparent / tuflow_stnd_path(inpath, 'gis/xf') / inpath.name).resolve()
    elif command and command.is_read_gis():
        return (outparent / tuflow_stnd_path(inpath, 'gis') / inpath.name).resolve()
    elif key:
        return (outparent / tuflow_stnd_path(inpath, key) / inpath.name).resolve()
    return (outparent / tuflow_stnd_path(inpath, None) / inpath.name).resolve()


def predict_encoding(file):
    all_codecs = ['utf_8', 'ascii', 'utf_32', 'utf_32_be', 'utf_32_le', 'utf_16', 'utf_16_be', 'utf_16_le', 'utf_7',
                  'utf_8_sig', 'big5', 'big5hkscs', 'cp037', 'cp273', 'cp424', 'cp437',
                  'cp500', 'cp720', 'cp737', 'cp775', 'cp850', 'cp852', 'cp855', 'cp856', 'cp857',
                  'cp858', 'cp860', 'cp861', 'cp862', 'cp863', 'cp864', 'cp865', 'cp866', 'cp869',
                  'cp874', 'cp875', 'cp932', 'cp949', 'cp950', 'cp1006', 'cp1026', 'cp1125',
                  'cp1140', 'cp1250', 'cp1251', 'cp1252', 'cp1253', 'cp1254', 'cp1255', 'cp1256',
                  'cp1257', 'cp1258', 'euc_jp', 'euc_jis_2004', 'euc_jisx0213', 'euc_kr',
                  'gb2312', 'gbk', 'gb18030', 'hz', 'iso2022_jp', 'iso2022_jp_1', 'iso2022_jp_2',
                  'iso2022_jp_2004', 'iso2022_jp_3', 'iso2022_jp_ext', 'iso2022_kr', 'latin_1',
                  'iso8859_2', 'iso8859_3', 'iso8859_4', 'iso8859_5', 'iso8859_6', 'iso8859_7',
                  'iso8859_8', 'iso8859_9', 'iso8859_10', 'iso8859_11', 'iso8859_13',
                  'iso8859_14', 'iso8859_15', 'iso8859_16', 'johab', 'koi8_r', 'koi8_t', 'koi8_u',
                  'kz1048', 'mac_cyrillic', 'mac_greek', 'mac_iceland', 'mac_latin2', 'mac_roman',
                  'mac_turkish', 'ptcp154', 'shift_jis', 'shift_jis_2004', 'shift_jisx0213']
    for e in all_codecs:
        try:
            with open(file, 'r', encoding=e) as fh:
                fh.readline()
                fh.seek(0)
        except (UnicodeDecodeError, UnicodeError):
            # print('got unicode error with %s , trying different encoding' % e)
            pass
        else:
            return e


class OGROpen:

    def __init__(self, path, mode):
        self.path = path
        self.mode = mode
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
        from .gis import ogr_format
        format = ogr_format(self.path)
        if self.mode == 'r':
            if not path.exists():
                raise FileExistsError(f'Could not open {path} for reading')
            self.ds = ogr.GetDriverByName(format).Open(str(path.dbpath))
        else:
            if os.path.exists(path.dbpath):
                self.ds = ogr.GetDriverByName(format).Open(str(path.dbpath), 1)
            else:
                self.ds = ogr.GetDriverByName(format).CreateDataSource(str(path.dbpath))
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

    __slots__ = '_end_slash'

    def __new__(cls, *args, **kwargs):
        cls = TuflowWindowsPath if os.name == 'nt' else TuflowPosixPath
        if os.name != 'nt' and len(args) == 1 and '\\' in str(args[0]):
            # This is probably a Windows path being read on a POSIX system
            parts = (str(args[0]).replace('\\','/'), )
        else:
            parts = args

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

    def __init__(self, *args, **kwargs):
        if sys.version_info >= (3, 12):
            if os.name != 'nt' and '\\' in str(args[0]):
                args_ = [str(a).replace('\\','/') for a in args]
                super().__init__(*args_)
            else:
                super().__init__(*args)

    def __contains__(self, item):
        if isinstance(item, str):
            return item in str(self)
        else:
            raise TypeError(f'unsupported operand type(s) for in: {type(self)} and {type(item)}')

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

    def is_relative_to(self, other):
        from .gis import get_database_name
        if str(self).count('>>') > str(self).count('<<'):
            db1, lyr = get_database_name(self)
        else:
            db1, lyr = str(self), None
        if str(other).count('>>') > str(other).count('<<'):
            db2, lyr = get_database_name(other)
        else:
            db2, lyr = str(other), None
        return Path(db1).resolve().is_relative_to(Path(db2).resolve())

    def relative_to(self, other):
        from .gis import get_database_name
        if str(self).count('>>') > str(self).count('<<'):
            db1, lyr = get_database_name(self)
        else:
            db1, lyr = str(self), None
        if str(other).count('>>') > str(other).count('<<'):
            db2, lyr = get_database_name(other)
        else:
            db2, lyr = str(other), None
        p = Path(db1).resolve().relative_to(Path(db2).resolve())
        if lyr:
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

    def exists(self) -> bool:
        if self.suffix.lower() == '.gpkg':
            if ' >> ' not in str(self):
                return os.path.exists(self.dbpath)
            else:
                if not os.path.exists(self.dbpath):
                    return False
            try:
                import sqlite3
                conn = sqlite3.connect(self.dbpath)
                cur = conn.cursor()
                cur.execute(f"SELECT COUNT(*) FROM gpkg_contents WHERE UPPER(table_name)='{self.lyrname.upper()}';")
                count = cur.fetchone()[0]
            except Exception as e:
                count = 0
            finally:
                conn.close()
                return os.path.exists(self.dbpath) and count > 0

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
            return TuflowPath(Path(os.path.abspath(self)).resolve())
        except OSError:
            found = True
            path = TuflowPath(os.path.abspath(self))
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

        if str(pattern).count('>>') > str(pattern).count('<<'):
            db, lyr = get_database_name(pattern)
        else:
            db, lyr = pattern, None

        try:
            for file in Path(self).glob(db):
                if file.suffix.upper() != '.GPKG' or lyr is None:
                    if lyr is not None:
                        yield TuflowPath(f'{file.resolve()} >> {file.with_suffix("").name}')
                    else:
                        yield TuflowPath(file.resolve())
                else:
                    lyr = globify(lyr, wildcards)
                    for lyrname in GPKG(file).glob(lyr):
                        yield TuflowPath(f'{file.resolve()} >> {lyrname}')
        except NotImplementedError:
            if '*' not in db:
                for file in Path(db).parent.glob(Path(db).name):
                    if file.suffix.upper() != '.GPKG':
                        if lyr is not None:
                            yield TuflowPath(f'{file.resolve()} >> {file.with_suffix("").name}')
                        else:
                            yield TuflowPath(file.resolve())
                    else:
                        lyr = globify(lyr, wildcards)
                        for lyrname in GPKG(file).glob(lyr):
                            yield TuflowPath(f'{file.resolve()} >> {lyrname}')
            else:
                lowest_part = db.split('*')[0]
                p = Path(lowest_part).parent
                n = Path(lowest_part).name
                rel_path = n + '*'.join(db.split('*')[1:])
                for file in p.glob(rel_path):
                    if file.suffix.upper() != '.GPKG':
                        if lyr is not None:
                            yield TuflowPath(f'{file.resolve()} >> {file.with_suffix("").name}')
                        else:
                            yield TuflowPath(file.resolve())
                    else:
                        lyr = globify(lyr, wildcards)
                        for lyrname in GPKG(file).glob(lyr):
                            yield TuflowPath(f'{file.resolve()} >> {lyrname}')

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
                    yield (TuflowPath(dir_) / filename).resolve()


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
            return (self.parent / (f'..{os.sep}' * max_count)).resolve()

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

    def find_parent(self, name, index_=None):
        """Find parent with 'name' that is directly up from the path. Index will limit how far up the path tree
        the search will go.

        e.g. index_=5 will only search 5 folders higher.

        Parameters
        ----------
        name : str
            The folder name to search for.
        index_ : int, optional
            The number of folders to search up from the path. The default is None.

        Returns
        -------
        TuflowPath
            The path to the parent folder if found, otherwise None.
        """
        raise NotImplementedError

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
        raise NotImplementedError

    def _walk_dir(self, dir_, name, ignore_case=False):
        """Helper routine for 'find_in_walk_dir'."""

        if ignore_case:
            for _, dirname, _ in os.walk(dir_):
                for dn in dirname:
                    if dn.lower() == name.lower():
                        return TuflowPath(os.path.join(dir_, dn))
                    else:
                        dir_found = self._walk_dir(os.path.join(dir_, dn), name, ignore_case)
                        if dir_found:
                            return dir_found
                break
        else:
            for _, dirname, _ in os.walk(dir_):
                for dn in dirname:
                    if dn == name:
                        return TuflowPath(os.path.join(dir_, dn))
                    else:
                        dir_found = self._walk_dir(os.path.join(dir_, dn), name)
                        if dir_found:
                            return dir_found
                break


class TuflowWindowsPath(WindowsPath, TuflowPath):

    def __str__(self):
        str_ = str(WindowsPath.__str__(self))
        try:
            if self._end_slash:
                str_ = '{0}{1}'.format(str_, os.sep)
        except AttributeError:
            pass

        return str_

    def __truediv__(self, other):
        return TuflowPath(WindowsPath.__truediv__(self, other))

    def __eq__(self, other):
        if isinstance(other, Path):
            if ' >> ' not in str(self) and ' >> ' not in str(other):
                return WindowsPath.__eq__(self, other)
            else:
                if ' >> ' in str(self):
                    db1, lyr1 = str(self).split(' >> ', 1)
                else:
                    db1 = str(self)
                    lyr1 = self.stem
                if ' >> ' in str(other):
                    db2, lyr2 = str(other).split(' >> ', 1)
                else:
                    db2 = str(other)
                    lyr2 = other.stem
                return db1.lower() == db2.lower() and lyr1.lower() == lyr2.lower()

    def __hash__(self):
        return hash(str(self))

    def find_parent(self, name, index_=None):
        """Find parent with 'name' that is directly up from the path. Index will limit how far up the path tree
        the search will go.

        e.g. index_=5 will only search 5 folders higher.

        Parameters
        ----------
        name : str
            The folder name to search for.
        index_ : int, optional
            The number of folders to search up from the path. The default is None.

        Returns
        -------
        TuflowPath
            The path to the parent folder if found, otherwise None.
        """

        if index_ is None:
            for i, part in enumerate(self.parts[:1:-1]):  # assume it would never sit right next to drive letter e.g. C:\TUFLOW
                if part.lower() == name.lower():
                    return TuflowPath('').joinpath(*self.parts[:-i])
        else:
            ind = -1 - index_
            for i, part in enumerate(self.parts[:max(ind,1):-1]):
                if part.lower() == name.lower():
                    return TuflowPath('').joinpath(*self.parts[:-i])

        return None

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

        if index_ is None:
            p = TuflowPath(self.parts[0])
        else:
            i = -index_ + 1
            if i >= 0:
                p = TuflowPath('').joinpath(*self.parts[:])
            else:
                p = TuflowPath('').joinpath(*self.parts[:-index_ + 1])

        folders = sum([[y for y in names] for dir_, names, _ in os.walk(p) if not exclude or str(exclude) not in dir_], [])
        if ignore_case:
            if name.lower() in [x.lower() for x in folders]:
                return self._walk_dir(p, name, ignore_case)
        else:
            if name in folders:
                return self._walk_dir(p, name)


class TuflowPosixPath(PosixPath, TuflowPath):

    __slots__ = '_end_slash'

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
    
    def __eq__(self, other):
        if isinstance(other, Path):
            if ' >> ' not in str(self) and ' >> ' not in str(other):
                return PosixPath.__eq__(self, other)
            else:
                if ' >> ' in str(self):
                    db1, lyr1 = str(self).split(' >> ', 1)
                else:
                    db1 = str(self)
                    lyr1 = self.stem
                if ' >> ' in str(other):
                    db2, lyr2 = str(other).split(' >> ', 1)
                else:
                    db2 = str(other)
                    lyr2 = other.stem
                return db1 == db2 and lyr1.lower() == lyr2.lower()

    def __hash__(self):
        return hash(str(self))

    def find_parent(self, name, index_=None):
        """Find parent with 'name' that is directly up from the path. Index will limit how far up the path tree
        the search will go.

        e.g. index_=5 will only search 5 folders higher.

        Parameters
        ----------
        name : str
            The folder name to search for.
        index_ : int, optional
            The number of folders to search up from the path. The default is None.

        Returns
        -------
        TuflowPath
            The path to the parent folder if found, otherwise None.
        """

        if index_ is None:
            for i, part in enumerate(
                    self.parts[:1:-1]):  # assume it would never sit right next to drive letter e.g. C:\TUFLOW
                if part.lower() == name.lower():
                    return TuflowPath('').joinpath(*self.parts[:-i])
        else:
            ind = -1 - index_
            for i, part in enumerate(self.parts[:max(ind, 1):-1]):
                if part.lower() == name.lower():
                    return TuflowPath('').joinpath(*self.parts[:-i])

        return None

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

        if index_ is None:
            p = TuflowPath(self.parts[0])
        else:
            i = -index_ + 1
            if i >= 0:
                p = TuflowPath('').joinpath(*self.parts[:])
            else:
                p = TuflowPath('').joinpath(*self.parts[:-index_ + 1])

        folders = sum([[y for y in names] for dir_, names, _ in os.walk(p) if not exclude or str(exclude) not in dir_], [])
        if ignore_case:
            if name.lower() in [x.lower() for x in folders]:
                return self._walk_dir(p, name, ignore_case)
        else:
            if name in folders:
                return self._walk_dir(p, name)
