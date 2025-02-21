import typing
from typing import Union

from .gis import GisInput
from ..abc.run_state import RunState
from ..abc.input import Input
from ..dataclasses.file import PathType, TuflowPath
from ..utils.commands import Command

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class InputRunState(RunState, Input):
    """Input class for RunState model. Adds methods from RunState class to resolve scopes."""

    def __init__(self, *args, **kwargs) -> None:
        super(InputRunState, self).__init__(*args, **kwargs)
        self.cf = None

    def __repr__(self):
        """Input name is BuildState type + Context."""
        if hasattr(self, 'command') and hasattr(self, 'value'):
            return '<{0}Context> {1} == {2}'.format(self._name, self.command, self.value)
        elif hasattr(self, 'command'):
            return '<{0}Context> {1}'.format(self._name, self.command)
        return '<{0}Context>'.format(self._name)

    @property
    def value(self) -> typing.Any:
        if self.raw_command_obj() is not None and isinstance(self._value_orig, str):
            if self.raw_command_obj().is_value_a_folder() or self.raw_command_obj().is_value_a_file():
                return self._value_orig
            elif self.raw_command_obj().is_value_a_number(self._value):
                return self.raw_command_obj().return_number(self._value)
            elif self.raw_command_obj().is_value_a_number_tuple(self._value):
                return self.raw_command_obj().return_number_tuple(self._value)
            else:
                return self._value_orig

    def _init(self) -> None:
        """Called after the generic initialisation.

        Sets the unique index (used for hashing) and sets a couple of other properties from the original
        BuildState object if they exist.
        """

        self.uuid = self.bs.uuid
        for attr in self.bs._transferable:
            setattr(self, attr, getattr(self.bs, attr))
        if isinstance(self.bs, GisInput):
            self._loaded_attr_ref = False

    def _resolve_scope_in_context(self) -> None:
        """Method called after all initialisation and resolves all inputs to remove variable names and unused inputs.
        Also resolve any numeric and file references in command value.

        e.g.
        File references can be using variable names (either user defined or scenario/event)
        or
        Some commands can contain numeric values that have been replaced by a variable name
        even GIS inputs can contain numeric values:
            - Read GIS Mat == 2d_mat.shp | 3  ! 3 is the column index to use
            - Read GIS Zpts Conveyance == <gis file> | <float> | <grid>  ! second value is the numeric value

        GIS inputs also may have file references in the attribute table - these are resolved lazily (when required).
        """

        self._value = self.ctx.translate(self.bs.value)
        self._value_orig = self.ctx.translate(self.bs._value_orig)
        self._expanded_value = self.ctx.translate(self.bs.expanded_value)

        # not every input has a file reference - so don't need to continue
        if not self._value or not hasattr(self.bs, 'files'):
            return

        # get files - some inputs can have multiple files references
        files = [x.strip() for x in self._expanded_value.split('|')]

        # check all variable names in file have been resolved
        if [x for x in files if not self.ctx.is_resolved(x)]:
            raise AttributeError('Input has not been completely resolved - {0}'.format(self._expanded_value))

        # resolve any numeric values in value
        if hasattr(self, 'numeric_type') and self.numeric_type in [float, int]:
            self.number_value = files.pop(1)
            self.number_value = self.numeric_type(self.number_value)

        # note: gis inputs can have file references in the attribute table
        # - these are populated lazily (i.e. only when required)
        if len(files) == 1:
            self.file = TuflowPath(files[0])
        else:
            self.file = [TuflowPath(x) for x in files]
        self.file_count = len(files)
        self.missing_files = any([not TuflowPath(x).exists() for x in files])

    # @property
    # def parent(self) -> '':

    @property
    def user_def_index(self) -> Union[int, None]:
        #: int: The user defined index for the GIS input e.g. :code:`Read GIS Mat == 2d_mat.shp | 3`
        if not isinstance(self.bs, GisInput):
            logger.error('Build state instance is not GisInput type')
            raise NotImplementedError
        if isinstance(self.number_value, int):
            return self.number_value

    def raw_command_obj(self) -> Command:
        """Returns the Command object created during file parsing. This command object contains a lot more information
        on the given command and has a lot of useful methods for determining what the command is doing.

        Returns
        -------
        Command
            Command object that is the base of the input.
        """
        return self.bs.raw_command_obj()

    def get_files(self) -> list[PathType]:
        """Get a list of files referenced in this object. Files should be absolute paths
        and can return multiple files even if only one input is referenced.

        At least one file per file reference should be returned even if the file does not exist.

        Returns
        -------
        list[PathLike]
            List of files referenced in this object.
        """
        if hasattr(self, 'file'):
            if not isinstance(self.bs, GisInput) or self._loaded_attr_ref:
                if isinstance(self.file, list):
                    return self.file
                else:
                    return [self.file]

            # gis inputs get special treatment as they can contain file references inside the attribute table
            # do this here to avoid having to parse gis files unless required
            self.bs.load_attribute_file_ref()
            for inp in self.bs._attr_inputs:
                inp_ctx = inp.context(context=self.ctx)
                for file in inp_ctx.get_files():
                    if not isinstance(self.file, list):
                        self.file = [self.file]
                    self.file.append(file)
            self._loaded_attr_ref = True

            if isinstance(self.file, list):
                return self.file
            else:
                return [self.file]

        return []
