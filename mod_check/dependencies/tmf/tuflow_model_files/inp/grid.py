from .file import FileInput
from .gis import GisInput_
from ..dataclasses.scope import Scope, ScopeList
from ..dataclasses.file import TuflowPath
from ..dataclasses.types import is_a_number_or_var
from .. import const

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class GridInput(GisInput_):
    """Class for handling GRID inputs.

    This class can handle the following scenarios:

    * reading multiple files on a single line: the first file is assumed to be a grid file, the second is
      a vector file.
    """
    TUFLOW_TYPE = const.INPUT.GRID

    def _get_files(self) -> None:
        """Overrides the _get_files method called in the initialisation of the FileInput class
        to handle specific GRID input requirements.
        """

        for i, type_ in enumerate(self._input.iter_grid(self._input.settings)):
            self._gather_attributes(i, type_)
        if not self.files:
            self.files = [TuflowPath(x.strip()) for x in self._expanded_value.split('|') if not is_a_number_or_var(x)]

    def _file_scopes(self) -> None:
        """Overrides the _file_scopes method called in the initialisation of the FileInput class
        to handle specific GRID input requirements.
        """

        if not self.multi_layer or self._input.settings.control_file is None:
            FileInput._file_scopes(self)
            return
        for _ in self._input.iter_grid(self._input.settings):
            for file in self._input.iter_files(self._input.settings):
                self._file_to_scope[str(file)] = Scope.from_string(str(self._input.value), str(file))

    def figure_out_file_scopes(self, scope_list: ScopeList) -> None:
        # docstring inherited
        if not self.multi_layer or self._input.settings.control_file is None:
            FileInput.figure_out_file_scopes(self, scope_list)
            return
        for _ in self._input.iter_grid(self._input.settings):
            for file in self._input.iter_files(self._input.settings):
                Scope.resolve_scope(self.file_scope(file), str(self._input.value), str(file), scope_list)
