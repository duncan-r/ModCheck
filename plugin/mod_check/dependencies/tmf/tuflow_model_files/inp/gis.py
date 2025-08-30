import os
import re
import sys
import typing
from pathlib import Path

from .file import FileInput
from ..file import TuflowPath
from ..gis import tuflow_type_requires_feature_iter
from ..parsers.command import Command
from ..parsers.expand_tuflow_value import TuflowValueExpander
from .. import const, logging_ as tmf_logging
from ..gis import GisFormat, has_gdal
from ..tfstrings.patterns import globify
from .. db import xs
from ..context import Context
from .inp_run_state import InputRunState

if typing.TYPE_CHECKING:
    # noinspection PyUnusedImports
    from ..cf.cf_build_state import ControlFileBuildState
    # noinspection PyUnusedImports
    from ..cf.cf_run_state import ControlFileRunState

logger = tmf_logging.get_tmf_logger()


class GisInputBase(FileInput):
    """Generic class for GIS / GRID / TIN inputs. These inputs can have multiple files on a single line and this
    class has additional properties to record this.
    """
    TUFLOW_TYPE = const.UNKNOWN_TYPE

    def __init__(self, parent: 'ControlFileBuildState', command: Command) -> None:
        # docstring inherited
        self._prev_val = None
        self._rhs = []
        self._attr_idx = 0
        self._attr_idx_found = False
        super().__init__(parent, command)

    @property
    def value(self) -> TuflowPath | float | int | list[TuflowPath | float | int]:
        self._command.reload_value()
        if not self._rhs:
            for cmd in self._command.parts():
                if cmd.is_value_a_file():
                    self._rhs.append(TuflowPath(cmd.value_expanded_path) if cmd.value_expanded_path else TuflowPath(cmd.value))
                elif cmd.is_value_a_number_3():
                    self._attr_idx = cmd.return_number()
                    self._attr_idx_found = True
                    self._rhs.append(self._attr_idx)
        if len(self._rhs) == 1:
            return self._rhs[0]
        return self._rhs if self._rhs else ''

    @value.setter
    def value(self, value: typing.Any):
        raise AttributeError('The "value" attribute is read-only, use "rhs" to set the value of the input.')


class GisInputRunState(InputRunState):

    def __init__(self, build_state: 'GisInput', context: Context, parent: 'ControlFileRunState'):
        #: GisInput: the BuildState object that the RunState object is based on.
        self.bs = build_state
        #: int: index of the attribute column to use for the GIS input.
        self.attr_idx = build_state.attr_idx

        self._geoms = []

        self._rs: 'GisInput'

        super().__init__(build_state, context, parent)

    @property
    def geoms(self) -> list[int]:
        if not has_gdal:
            logger.error('GDAL is not available. GIS inputs cannot be processed.')
            raise ImportError('GDAL is not available. GIS inputs cannot be processed.')
        return self._geoms

    def _resolve_scope_in_context(self):
        super()._resolve_scope_in_context()
        self._geoms = self._rs.geoms if has_gdal else []
        for cf in self.bs.cf:
            if cf.fpath.resolve() == self.value.resolve():
                run_cf = cf.context(context=self.ctx, parent=self.parent)
                self.cf.append(run_cf)


class GisInput(GisInputBase):
    """Class for handling GIS inputs (Vector only).

    GIS inputs have very specific requirements. This class handles the following scenarios:

    * reading multiple files on a single line
    * reading a file then an index (indicating which column to attribute column to use)
      e.g. :code:`Read GIS Mat == 2d_mat.shp | 3`
    * reading a vector file | float value | raster file
      e.g. command :code:`Read GIS Zpts Modify Conveyance == river.shp | 3.2 | conv.tif`
    * read the vector file and find file references within the attribute table
      e.g. :code:`1d_nwk` layer using a :code:`M` channel which can reference files within the attribute table
    """
    TUFLOW_TYPE = const.INPUT.GIS

    def __init__(self, parent: 'ControlFileBuildState', command: Command):
        self._attr_idx = 0
        self._attr_idx_found = False
        self._geoms = []
        self._cf = []
        self._cf_loaded = False
        self.mod_conveyance_grid = None
        super().__init__(parent, command)

    @property
    def geoms(self) -> list[int]:
        if not has_gdal:
            logger.error('GDAL is not available. GIS inputs cannot be processed.')
            raise ImportError('GDAL is not available. GIS inputs cannot be processed.')
        if not self._files_loaded:
            self._load_files()
        return self._geoms

    @property
    def attr_idx(self) -> int:
        if self._attr_idx_found:
            return self._attr_idx
        for cmd in self._command.parts():
            if cmd.is_value_a_number_3():
                self._attr_idx = cmd.return_number()
                self._attr_idx_found = True
        return self._attr_idx

    @property
    def cf(self) -> list[xs.DatabaseBuildState]:
        if not self._cf_loaded:
            if not self._files_loaded:
                self._load_files()
            self._load_database_files()
        return self._cf

    @cf.setter
    def cf(self, value: list[xs.DatabaseBuildState]):
        self._cf = value
        if self._cf:
            self._cf_loaded = True

    def context(self,
                run_context: str | dict[str, str] = '',
                context: Context | None = None,
                parent: 'ControlFileRunState | None' = None) -> GisInputRunState:
        # docstring inherited
        ctx = context if context else Context(run_context, config=self.config)
        return GisInputRunState(self, ctx, parent)

    def _load_files(self):
        attr_files = []  # files referenced in the layer attribute table
        for cmd in self._command.parts():
            if cmd.is_value_a_file():
                at_least_once = False
                for file in cmd.iter_files():
                    at_least_once = True
                    file = TuflowPath(file)
                    self._files.append(file)
                    self._file_to_original[file] = cmd.value_expanded_path
                    geoms, ref_files = self._process_gis_file(file, cmd)
                    for geom in geoms:
                        if geom != 0 and geom not in self._geoms:  # ogr.wkbUnknown
                            self._geoms.append(geom)
                    attr_files.extend(ref_files)
                if not at_least_once:
                    self._has_missing_files = True
                    file = TuflowPath(cmd.value_expanded_path) if self._command.config.control_file != Path() else TuflowPath(cmd.value)
                    self._files.append(file)
                    self._file_to_original[file] = file

        self._rhs_files = self._files.copy()
        self._files.extend(attr_files)  # append attribute files to the end of the file list
        self._file_scopes()
        self._files_loaded = True

    def _load_database_files(self):
        if not self._command.is_table_link():
            self._cf_loaded = True
            return
        for file in self._rhs_files:
            try:
                db = xs.CrossSectionDatabase(file, self.config, self.parent, self.scope)
                self._cf.append(db)
            except Exception as e:
                logger.error(f'Error loading control file {file}. Command: {self._command}. Error: {e}')
        self._cf_loaded = True

    def _process_gis_file(self, file: TuflowPath, cmd: Command) -> tuple[list[int], list[TuflowPath]]:
        """Returns a list of geometry types and a list of files referenced in the attribute table."""
        geoms, attr_files = [], []
        gis_lyr, feat_iter = None, []

        # Check if GDAL is available. If not, iterate just over the attributes and ignore the geometry.
        # Create an abstract gis_layer and feature iterator
        if has_gdal:
            try:
                gis_lyr = TuflowPath(file).open_gis()
                feat_iter = gis_lyr.lyr
            except Exception as e:
                logger.warning(f'Error opening GIS layer with GDAL: {file}. Command: {self._command}. Error: {e}')
        else:
            try:
                gis_lyr = TuflowPath(file).gis_attributes()
                feat_iter = gis_lyr
            except Exception as e:
                logger.warning(f'Error opening GIS layer for attribute reading: {file}. Command: {self._command}. Error: {e}')
        if not gis_lyr:
            return [], []

        try:
            # get the geometry type
            if has_gdal:
                if gis_lyr.fmt == GisFormat.MIF:
                    geoms = gis_lyr.lyr.GetGeometryTypes()
                else:
                    geoms = [gis_lyr.lyr.GetGeomType()]

            # check if the layer might contain file path references in the attributes
            col_indexes = tuflow_type_requires_feature_iter(file.lyrname)
            if not col_indexes:
                return geoms, attr_files

            # find potential file references in the attributes
            for feat in feat_iter:
                for i in col_indexes:
                    field_count = feat.GetFieldCount() if has_gdal else len(feat)
                    attrs = feat if has_gdal else list(feat.values())
                    if field_count <= i or not attrs[i]:
                        continue
                    if '|' in str(attrs[i]):
                        op, file_ref = [x.strip() for x in attrs[i].split('|', 1)]  # operational control | file
                    else:
                        op, file_ref = None, attrs[i]
                    if 'NETWORK' in cmd.command and attrs[1] and attrs[1].lower()[0] == 'm' and op is not None:  # both are files
                        files = [Path(op), Path(file_ref)]
                    else:
                        files = [Path(file_ref)]
                    for f in files:
                        # tuflow treats "/path/to/file" the same as "./path/to/file" - therefore, so must this parser
                        abs_path = re.findall(r'(([A-Za-z]:\\)|\\\\)', str(f)) and sys.platform == 'win32'
                        if not abs_path and str(f)[0] in ['\\', '/']:
                            f = f'.{f}'
                        expander = TuflowValueExpander(self._command.config.variables, None)
                        f = Path(expander.expand(str(f)))
                        fpath = file.parent / f
                        try:
                            rel_path = os.path.relpath(fpath, file.parent)
                        except ValueError:
                            rel_path = f
                        rel_path = globify(rel_path, self._command.config.wildcards)
                        at_least_once = False
                        for attr_file in file.parent.glob(rel_path, self._command.config.wildcards):
                            at_least_once = True
                            attr_file = Path(attr_file)
                            attr_files.append(attr_file)
                            self._file_to_original[attr_file] = fpath
                        if not at_least_once:
                            self._has_missing_files = True
                            attr_files.append(fpath)
                            self._file_to_original[fpath] = fpath
        except Exception as e:
            logger.warning(f'Error reading GIS layer {file}. Command: {self._command}. Error: {e}')
        finally:
            if has_gdal:
                gis_lyr.close()

        return geoms, attr_files
