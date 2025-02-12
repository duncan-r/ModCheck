import os.path
from typing import TYPE_CHECKING

from ._inp_build_state import InputBuildState
from ..dataclasses.file import TuflowPath
from ..dataclasses.inputs import Inputs
from ..dataclasses.scope import Scope, ScopeList
from ..dataclasses.types import PathLike
from ..utils.commands import Command
from ..utils.patterns import contains_variable
from .. import const

if TYPE_CHECKING:
    from ..abc.build_state import BuildState

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class FileInput(InputBuildState):
    """Class for handling inputs that reference files.

    This class will record all associated files and their scopes. This class assumes only one input
    file per line but the input can have variable names in it which expand to multiple files.

    | e.g.
    | :code:`Read File == input_file_<<~s~>>.trd`
    """
    TUFLOW_TYPE = const.INPUT.FILE

    __slots__ = ('files', '_file_to_scope', 'file_count', 'uses_wild_card', 'missing_files')

    def __init__(self, parent: 'BuildState', command: Command) -> None:
        # docstring inherited
        super().__init__(parent, command)
        self.uses_wild_card = contains_variable(str(self._input.value_orig))
        self.missing_files = False
        self.file_count = 0
        self.files = []
        self._file_to_scope = {}
        self._get_files()
        self._file_scopes()
        self._searchable.extend(['uses_wild_card', 'file_count', '_file_to_scope', 'missing_files'])

    def update_properties(self) -> None:
        # docstring inherited
        self.uses_wild_card = contains_variable(str(self._input.value_orig))
        self.missing_files = False
        self.file_count = 0
        self.files = []
        self._file_to_scope = {}
        self._get_files()
        self._file_scopes()

    def _get_files(self) -> None:
        """Called during the initialisation of this class and finds all possible files associated with this input."""
        if self._input.settings.control_file is not None:
            self.files = [x for x in self._input.iter_files(self._input.settings)]
        if not self.files:
            self.missing_files = True
            self.files = [TuflowPath(self._input.value_expanded_path)]
        self.file_count = len(self.files)

    def _file_scopes(self) -> None:
        """
        Called after files are collected in the initialisation of this class and finds the scope of each file. The
        scope of the file is independent of the scope of the input i.e. a file with a 'GLOBAL' scope does not
        reflect that the input itself may be within an 'IF Scenario' block, it indicates that the file does
        not contain any variable names that could potentially be expanded to a different files.

        It will try and resolve the scope of the input by comparing the name to any existing files
        it finds that match the input name pattern.
        e.g.
        Read File == input_file_<<~s~>>.trd
        Existing files:
            - input_file_exg.trd
            - input_file_dev.trd
        File scopes:
            - input_file_exg.trd -> Scope = SCENARIO, name = exg, var = <<~s~>>
            - input_file_dev.trd -> Scope = SCENARIO, name = dev, var = <<~s~>>
        If the scope name can't be resolved then the scope name will be set to the variable name.
        If the there are no variables in the file name then a 'GLOBAL' scope will be assigned to the file.
        """
        for file in self.files:
            self._file_to_scope[str(file)] = Scope.from_string(str(self._input.value_expanded_path), str(file))

    def file_scope(self, file: PathLike) -> ScopeList:
        """Public function that will return the scope of a given file.

        Parameters
        ----------
        file : PathLike
            The file to get the scope of.

        Returns
        -------
        ScopeList
            The scope of the file.
        """
        return self._file_to_scope.get(str(file), ScopeList([Scope('GLOBAL', '')]))

    def figure_out_file_scopes(self, scope_list: ScopeList) -> None:
        """Given a list of known scopes (unordered) this function will try and resolve the names
        of the scopes for each file. Only affects scope names that have not been resolved yet and will
        only work if there are existing files to compare to as it will loop through every possible permutation of
        variable names and check if they exist once inserted into the file name.

        This is different from resolving scope through the 'run state' context which uses an ordered list of scopes
        which can simply be used to replace the variable names in the file name.

        Parameters
        ----------
        scope_list : ScopeList
            The list of known scopes.
        """
        for file in self.files:
            Scope.resolve_scope(self.file_scope(file), str(self._input.value_expanded_path), str(file), scope_list)

    def get_files(self) -> list[PathLike]:
        """Public method that returns the list of files associated with this input.

        Returns
        -------
        list[PathLike]
            The list of files.
        """
        return self.files

    def update_value(self, value: PathLike) -> 'InputBuildState':
        """Update the input value. Does not change the command or the input type.

        Parameters
        ----------
        value : PathLike
            The new value to update to.

        Returns
        -------
        InputBuildState
            The updated input object.
        """
        inputs = Inputs()
        inputs.append(self)
        self.record_change(inputs, 'update_value')
        cmd = Command(self._input.original_text, self._input.settings)
        if cmd.settings.control_file:
            value_ = (cmd.settings.control_file.parent / value).resolve()
            relpath = os.path.relpath(value_, cmd.settings.control_file.parent)
        else:
            relpath = value
        cmd.value = TuflowPath(relpath)
        new_value = '{0} == {1}'.format(cmd.command_orig, cmd.value)
        new_value = cmd.re_add_comments(new_value, True)
        cmd = Command(new_value, cmd.settings)
        self.set_raw_command_obj(cmd)
        self.update_properties()
        return self
