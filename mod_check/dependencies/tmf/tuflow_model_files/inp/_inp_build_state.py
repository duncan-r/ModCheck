import typing
from typing import TYPE_CHECKING, TextIO
from uuid import uuid4

from ..dataclasses.types import PathLike
from ..dataclasses.inputs import Inputs
from ..dataclasses.scope import Scope, EventScope, ScenarioScope, ScopeList, EventVariableScope
from ..abc.build_state import BuildState
from ..abc.input import Input
from ..utils.commands import Command
from ..utils.scope_writer import ScopeWriter
from ..dataclasses.scope import Scope, ScopeList
from .. import const

if TYPE_CHECKING:
    from ..abc.build_state import BuildState

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class InputBuildState(BuildState, Input):
    """Input class for the 'BuildState' of the model. The build state input contains extra information on the scope,
    of the input (e.g. it may be within a scenario block).

    It also collects all the associated files e.g. input paths can contain variables names so
    :code:`2d_zsh_<<~s1~>>_001.shp` could expand to

    * :code:`2d_zsh_D01_001.shp`
    * :code:`2d_zsh_D02_001.shp`

    if both files exist. It will collect information on the scope of files it finds.
    """
    TUFLOW_TYPE = const.INPUT.INPUT

    __slots__ = ('_input', '_command', '_value', '_index', '_scope', '_searchable', '_transferable', 'uuid', 'parent')

    def __new__(cls, parent: 'BuildState', command: Command) -> 'InputBuildState':
        """:code:`__new__` is used to create an appropriate instance of the input class based on the type of command.
        e.g. :code:`Read GIS Z shape` will create a GisInput instance.
        """
        if command.command == 'ATTRIBUTE FILE REFERENCE':
            from .attr import AttrInput
            cls = AttrInput
        elif command.is_read_gis():
            from .gis import GisInput
            cls = GisInput
        elif command.is_read_grid():
            from .grid import GridInput
            cls = GridInput
        elif command.is_read_tin():
            from .tin import TinInput
            cls = TinInput
        elif command.is_read_database():
            from .db import DatabaseInput
            cls = DatabaseInput
        elif command.is_control_file() and not (command.is_quadtree_control_file() and command.is_quadtree_single_level()):
            from .cf import ControlFileInput
            cls = ControlFileInput
        elif command.is_value_a_file():
            from .file import FileInput
            cls = FileInput
        elif command.is_valid():
            from .setting import SettingInput
            cls = SettingInput
        elif command.command is None:
            from .comment import CommentInput
            cls = CommentInput
        self = object.__new__(cls)
        return self

    def __init__(self, parent: 'BuildState', command: Command) -> None:
        """Initialises the input object.

        The command argument expects a Command object which is imported from the "convert_tuflow_model_gis_format"
        library and is largely responsible for all the heavy lifting in parsing the command.
        The command object very much underpins the input object!

        The command object can be initialised manually using Command(input_text: str, settings: Settings), however it is
        best obtained from the control file parser function "get_commands" (from the same library) which allows for the
        Settings object to be passed through all the commands and updated as necessary
        (e.g. "Spatial Database == " is a command that will affect future commands). It also adds context to the
        command object regarding whether the command is sitting in a define block
        (e.g "If Scenario" or "Start 1D Domain") and this information will automatically be added to the input object.

        Parameters
        ----------
        parent : BuildState
            The parent build state object (most likely a ControlFile).
        command : Command
            Command object which unpins the input.
        """
        #: list[ControlLike]: list of loaded control file/database objects associated with the input
        self.cf = []
        #: ControlFile: control file parent the input belongs to
        self.parent = parent
        self.set_raw_command_obj(command)
        #: UUID: unique identifier for the input
        self.uuid = uuid4()
        self._scope = self._init_scope()
        #: Path: path to the TRD file if the input sits within one
        self.trd = None
        #: bool: whether the input has been changed
        self.dirty = False
        self._transferable = ['trd', 'parent']
        self._searchable = ['_scope', 'trd']

    @property
    def resolved_value(self) -> typing.Any:
        """Returns the resolved value if possible. This is useful when using variables in TUFLOW and
        the variables are not scenario or event dependent.

        If the value cannot be resolved without context, then the returned value will be the same as the
        :attr:`value` property.

        Value can be any type, and should be returned as its intended type e.g. :code:`Set Code == 0`
        should return an integer.

        Path values will return a string. Use expanded_value for the expanded path.
        """
        if self.raw_command_obj() is not None and isinstance(self._value_orig, str):
            val = self.raw_command_obj().value
            if self.raw_command_obj().is_value_a_folder() or self.raw_command_obj().is_value_a_file():
                return val
            elif self.raw_command_obj().is_value_a_number(val):
                return self.raw_command_obj().return_number(val)
            elif self.raw_command_obj().is_value_a_number_tuple(val):
                return self.raw_command_obj().return_number_tuple(val)
            else:
                return val

    @property
    def resolved(self) -> bool:
        return '<<' not in str(self.resolved_value)

    def update_properties(self) -> None:
        """Updates the properties of this object. E.g. if there are any missing files etc."""
        pass

    def figure_out_file_scopes(self, scopes: ScopeList) -> None:
        """
        [OVERRIDDEN in child classes where appropriate, not used in this class]

        Resolve unknown scopes by passing in a list of known scopes.

        Unknown scopes are when :code:`<<~s~>>`, :code:`<<~e~>>`, :code:`<<variable>>`, or :code:`~event~`
        are encountered in file names and they cannot be resolved due to ambiguity, missing files,
        or missing information.

        This is not the same as using context to resolve scopes into a RunState. The method populates scope information
        where any is missing where variable names have been used in file names.

        Parameters
        ----------
        scopes : ScopeList
            List of known scopes.
        """
        pass

    def is_start_block(self) -> bool:
        """Returns whether this input is the start of a block.
        e.g. :code:`If Scenario == DEV` is the start of a block.

        A start of a block can be any block that starts with

        * :code:`IF  [Scenario | Event]`
        * :code:`ELSE IF  [Scenario | Event]`
        * :code:`ELSE`
        * :code:`DEFINE  [Map Output Zone | ...]`
        * :code:`Start 1D`

        Returns
        -------
        bool
            Whether the input is the start of a block.
        """
        return self._input.is_start_define()

    def is_end_block(self) -> bool:
        """Returns whether this input is the end of a block.
        e.g. :code:`End if` is the end of a block.

         An end of a block can be any block that starts with

        * :code:`END IF`
        * :code:`ELSE IF  [Scenario | Event]`
        * :code:`ELSE`
        * :code:`END DEFINE`

        Returns
        -------
        bool
            Whether the input is the end of a block.
        """
        return self._input.is_end_define() or self._input.is_else()

    def raw_command_obj(self) -> Command:
        """Returns the Command object created during file parsing. This command object contains a lot more information
        on the given command and has a lot of useful methods for determining what the command is doing.

        Returns
        -------
        Command
            Command object that is the base of the input.
        """
        return self._input

    def set_raw_command_obj(self, command: Command) -> None:
        """Set the raw command object. This is used when the command object is updated e.g. the value is changed.

        Parameters
        ----------
        command : Command
            Command object to set.
        """
        inp_exists = hasattr(self, '_input')
        if inp_exists:
            if self.raw_command_obj().is_control_file():
                orig_value = self.parent.input_to_loaded_value(self)
            else:
                orig_value = self.value
        if not command:
            self.parent._remove_attr(self, orig_value)
            return
        self._input = command
        self._command = command.command
        self._value = command.value
        self._value_orig = command.value_orig
        self._expanded_value = self._input.value_expanded_path
        if inp_exists:
            self.parent._replace_attr(self, orig_value)

    def get_files(self) -> list[PathLike]:
        """Get a list of files referenced in this object. Files should be absolute paths
        and can return multiple files even if only one input is referenced.

        At least one file per file reference should be returned even if the file does not exist.

        Returns
        -------
        list[PathLike]
            List of files referenced in this object.
        """
        return []

    def write(self, fo: TextIO, scope_writer: ScopeWriter) -> str:
        """Write the object to file. Users probably shouldn't be using this method directly in this class.

        Parameters
        ----------
        fo : TextIO
            Text buffer object to write to.
        scope_writer : ScopeWriter
            Scope writer object that helps convert the input scope to a string (i.e. adds indentation).

        Returns
        -------
        str
            Text written to the file.
        """
        text = scope_writer.write(self._input.original_text)
        fo.write(text)
        return text

    def record_change(self, inputs: Inputs, change_type: str) -> None:
        """Not private, but not for users to use directly either.

        Record a change to the input. The record change is passed to the parent control file to record the change to.

        Parameters
        ----------
        inputs : Inputs
            List of inputs that have been changed. Use Inputs class, and not just a list of inputs.
        change_type : str
            Type of change that has occurred. e.g. 'update_value', 'update_command', 'set_scope'
        """
        self.dirty = True
        if self.parent:
            self.parent.record_change(inputs, change_type)

    def update_value(self, value: PathLike) -> 'InputBuildState':
        """Update the input value. Does not change the command or the input type.

        Parameters
        ----------
        value : PathLike
            New value to set.

        Returns
        -------
        InputBuildState
            Updated input object.
        """
        inputs = Inputs()
        inputs.append(self)
        self.record_change(inputs, 'update_value')
        cmd = Command(self._input.original_text, self._input.settings)
        cmd.value = str(value)
        new_value = '{0} == {1}'.format(cmd.command_orig, cmd.value)
        new_value = cmd.re_add_comments(new_value, True)
        cmd = Command(new_value, cmd.settings)
        self.set_raw_command_obj(cmd)
        return self

    def update_command(self, command: str) -> 'InputBuildState':
        """Update the input command.

        Parameters
        ----------
        command : str
            New command to set.

        Returns
        -------
        InputBuildState
            Updated input object.
        """
        inputs = Inputs()
        inputs.append(self)
        self.record_change(inputs, 'update_command')
        cmd = Command(self._input.original_text, self._input.settings)
        cmd.command = command.upper()
        cmd.command_orig = command
        text = cmd.make_new_text(cmd.settings)
        if cmd.is_read_gis() or cmd.is_read_grid() or cmd.is_read_tin():
            text = cmd.re_add_comments(text, rel_gap=False)
        cmd = Command(text, cmd.settings)
        # test
        inp = InputBuildState(self.parent, cmd)
        if not isinstance(inp, type(self)):
            logger.error('Cannot change input type. Existing and provided inputs are not the same type')
            raise ValueError('Cannot change input type')
        self.set_raw_command_obj(cmd)
        return self

    def set_scope(self, scope: list[tuple[str, str]]) -> ScopeList:
        """Sets the input scope based on a list of tuples (scenario_type, scenario_name).

        Parameters
        ----------
        scope : list[tuple[str, str]]
            List of tuples containing the scenario type and name.

        Returns
        -------
        ScopeList
            List of scope objects.
        """
        scope_list = ScopeList()
        if not isinstance(scope, list):
            scope = [scope]
        for s in scope:
            scope_list.append(Scope(s[0], s[1]))
        self._set_scope(scope_list)
        return self._scope

    def _init_scope(self) -> list[Scope]:
        """Defines the scope of the input based on whether the command is sitting within a Define Block.

        A define block can be any block that starts with

        * :code:`IF  [Scenario | Event]`
        * :code:`ELSE IF  [Scenario | Event]`
        * :code:`ELSE`
        * :code:`DEFINE  [Map Output Zone | ...]`
        * :code:`Start 1D`

        If the input is not within a 'Scenario' or 'Event' block then the scope is also given a 'GLOBAL' scope.

        The list of scopes should be considered 'stacked' or 'nested' i.e. if 2 scenario scopes exist, then
        the input is within a nested if statement. Blocks that use '|' to indicate 'OR' will be within a single
        Scope object (i.e. it won't be a list of scope objects).

        Returns
        -------
        list[Scope]
            List of scope objects.
        """

        if self._input.define_blocks:
            scope = ScopeList()
            for db in self._input.define_blocks:
                s = Scope(db.type, db.name)
                if not scope.contains(s, explode=False):
                    scope.append(s)
                # check if scope already exists - if it does but it is not from an else statement,
                # then replace it with the new scope
                if s._else and not [x for x in scope if x == s][0]._else:
                    i = scope.index(s)
                    scope[i] = s

            if not [x for x in scope if isinstance(x, EventScope) or isinstance(x, ScenarioScope) or isinstance(x, EventVariableScope)]:
                scope.insert(0, Scope('GLOBAL', ''))
            return scope

        return [Scope('GLOBAL', '')]

    def _set_scope(self, scope: ScopeList):
        inputs = Inputs()
        inputs.append(self)
        self.record_change(inputs, 'set_scope')
        self._scope = scope
