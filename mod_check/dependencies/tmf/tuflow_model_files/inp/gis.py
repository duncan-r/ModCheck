import os
import typing
from typing import Union

from ._inp_build_state import InputBuildState
from .file import FileInput
from ..dataclasses.file import TuflowPath
from ..dataclasses.inputs import Inputs
from ..dataclasses.scope import Scope, ScopeList
from ..dataclasses.types import is_a_number_or_var, PathLike
from ..utils.gis import tuflow_type_requires_feature_iter, ogr_format
from ..utils.settings import Settings
from ..utils.commands import Command, concat_command_values
from .. import const

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class GisInput_(FileInput):
    """Generic class for GIS / GRID / TIN inputs. These inputs can have multiple files on a single line and this
    class has additional properties to record this.
    """
    TUFLOW_TYPE = const.UNKNOWN_TYPE


    __slots__ = ('multi_layer', 'multi_layer_value', 'geom_count', 'has_raster',
                 'has_vector', 'has_tin', 'geoms', 'has_number', 'numeric_type',
                 'layer_count', '_prev_val')

    def __init__(self, parent: 'BuildState', command: Command) -> None:
        # docstring inherited
        self.has_tin = False
        self.has_raster = False
        self.has_vector = False
        self.has_number = False
        self.numeric_type = None
        self.geoms = []
        self.layer_count = 0
        self.multi_layer = False
        self.multi_layer_value = []
        self.file_count = 0
        self._prev_val = None
        super().__init__(parent, command)
        self.geom_count = len(self.geoms)
        self._transferable.extend(['multi_layer', 'geom_count', 'has_raster', 'has_vector', 'has_tin', 'has_number',
                                   'numeric_type', 'layer_count', 'geoms', 'layer_count'])
        self._searchable.extend(['multi_layer', 'geom_count', 'has_raster', 'has_vector', 'has_tin', 'has_number',
                                 'numeric_type', 'layer_count', 'geoms', 'layer_count'])

    def update_value(self, value: Union[PathLike, list[PathLike]]) -> 'InputBuildState':
        # docstring inherited
        inputs = Inputs()
        inputs.append(self)
        self.record_change(inputs, 'update_value')
        cmd = Command(self._input.original_text, self._input.settings)
        if not isinstance(value, list):
            value = [value]
        for i, v in enumerate(value[:]):
            if cmd.is_value_a_number(v):
                pass
            elif not TuflowPath(v).is_file() and cmd.settings.read_spatial_database:
                value[i] = f'{cmd.settings.read_spatial_database} >> {v}'
            else:
                value[i] = TuflowPath(v)
        cmd.value = concat_command_values(self._input.settings.control_file, value, self._input.settings.read_spatial_database)
        new_value = '{0} == {1}'.format(cmd.command_orig, cmd.value)
        new_value = cmd.re_add_comments(new_value, True)
        cmd = Command(new_value, cmd.settings)
        self.set_raw_command_obj(cmd)
        self.update_properties()
        return self

    def update_properties(self) -> None:
        # docstring inherited
        self.has_tin = False
        self.has_raster = False
        self.has_vector = False
        self.has_number = False
        self.numeric_type = None
        self.geoms = []
        self.layer_count = 0
        self.multi_layer = False
        self.multi_layer_value = []
        self.file_count = 0
        super().update_properties()

    def _gather_attributes(self, ind: int, type_: typing.Any) -> None:
        """Gathers various properties/attributes from the input which the user may be interested in.

        Parameters
        ----------
        ind : int
            The index of the attribute
        type\_ : typing.Any
            The type of attribute
        """
        if not isinstance(type_, int):
            self.layer_count += 1
            if ind == 1:
                self.multi_layer = True
        if type_ == 'VALUE':
            self.has_number = True
            try:
                if self._input.is_modify_conveyance():
                    self.numeric_type = float
                    val = float(self._input.value)
                else:
                    self.numeric_type = int
                    val = int(self._input.value)
            except ValueError:
                val = self._input.value.strip()  # variable e.g. <<value>>
            self.multi_layer_value.append(val)
        else:
            files = [x for x in self._input.iter_files(self._input.settings)]
            if not files:
                self.missing_files = True
            if type_ == 'GRID':
                self.has_raster = True
            elif type_ == 'TIN':
                self.has_tin = True
            elif type_ is None:  # shp or gpkg
                self.has_vector = True
                for file in files:
                    if file.exists():
                        try:
                            with TuflowPath(file).open_gis() as ogr_open:
                                geom = ogr_open.lyr.GetGeomType()
                                if geom not in self.geoms:
                                    self.geoms.append(geom)
                        except Exception:
                            pass
            elif isinstance(type_, int):
                if self._input.value != self._prev_val:
                    self._prev_val = self._input.value
                    self.layer_count += 1
                    if self.layer_count > 1:
                        self.multi_layer = True
                self.has_vector = True
                if type_ not in self.geoms:
                    self.geoms.append(type_)
            self.multi_layer_value.append(TuflowPath(self._input.value))
            for file in files.copy():
                if file not in self.files:
                    self.files.append(file)
                    self.file_count += 1


class GisInput(GisInput_):
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

    __slots__ = ('_attr_inputs')

    @property
    def user_def_index(self) -> Union[int, None]:
        #: int: The user defined index for the GIS input e.g. :code:`Read GIS Mat == 2d_mat.shp | 3`
        if self.multi_layer and self.numeric_type == int and len(self.multi_layer_value) > 1:
            return self.multi_layer_value[1]
        return 0

    def _get_files(self) -> None:
        """Overrides the _get_files method called in the initialisation of the FileInput class
        to handle specific GIS input requirements.
        """
        for i, type_ in enumerate(self._input.iter_geom(self._input.settings)):
            self._gather_attributes(i, type_)
        if not self.files:
            self.files = [x for x in self.multi_layer_value if not is_a_number_or_var(str(x))]

    def _file_scopes(self) -> None:
        """
        Overrides the _file_scopes method called in the initialisation of the FileInput class
        to handle specific GIS input requirements.
        """

        if not self.multi_layer or self._input.settings.control_file is None:
            GisInput_._file_scopes(self)
            return
        for type_ in self._input.iter_geom(self._input.settings):
            if type_ == 'VALUE':
                continue
            for file in self._input.iter_files(self._input.settings):
                self._file_to_scope[str(file)] = Scope.from_string(str(self._input.value), str(file))

    def figure_out_file_scopes(self, scope_list: ScopeList) -> None:
        # docstring inherited
        if not self.multi_layer or self._input.settings.control_file is None:
            GisInput_.figure_out_file_scopes(self, scope_list)
            return
        for type_ in self._input.iter_geom(self._input.settings):
            if type_ == 'VALUE':
                continue
            for file in self._input.iter_files(self._input.settings):
                Scope.resolve_scope(self.file_scope(file), str(self._input.value), str(file), scope_list)

    def load_attribute_file_ref(self) -> None:
        """Iterates through the vector file and finds any files references in the attribute table.
        Only opens the files for specific file types based on the input name.

        This routine is not called when the input is initialised as it could take a moment to load for big
        vector files. It is called when the get_files() method is called.
        """
        self._attr_inputs = []
        for file in GisInput_.get_files(self):
            col_indexes = tuflow_type_requires_feature_iter(file.lyrname)
            if not col_indexes:
                continue
            try:
                settings = Settings(convert_settings=self.raw_command_obj().settings)
                settings.control_file = file
                with file.open_gis() as f:
                    for feat in f:
                        for i in col_indexes:
                            if '|' in feat[i]:
                                op, file_ref = [x.strip() for x in feat[i].split('|', 1)]  # operational control | file
                            else:
                                op, file_ref = None, feat[i]
                            if TuflowPath(file_ref).suffix:
                                attr_input = InputBuildState(
                                    self, Command('ATTRIBUTE FILE REFERENCE == {0}'.format(file_ref), settings)
                                )
                                self._attr_inputs.append(attr_input)
                            # M channels can contain 2 files - Q.csv | A.csv
                            if '1d_nwk' in file.lyrname.lower() and feat[1] and feat[1].lower()[0] == 'm' and op:
                                if TuflowPath(op).suffix:
                                    attr_input = InputBuildState(
                                        self, Command('ATTRIBUTE FILE REFERENCE == {0}'.format(op), settings)
                                    )
                                    self._attr_inputs.append(attr_input)
            except FileExistsError as e:
                continue
            except Exception as e:
                continue

    def get_files(self) -> list[PathLike]:
        # docstring inherited
        files = GisInput_.get_files(self)
        self.load_attribute_file_ref()
        for inp in self._attr_inputs:
            files.extend(inp.get_files())
        return files
