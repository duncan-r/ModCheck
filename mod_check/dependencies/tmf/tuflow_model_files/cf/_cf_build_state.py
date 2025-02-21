import io

from ..inp._inp_build_state import *
from ..dataclasses.inputs import Inputs
from ..dataclasses.file import TuflowPath
from ..dataclasses.types import PathLike
from ..db.bc_dbase import BCDatabase
from ..db.soil import SoilDatabase
from ..db.mat import MatDatabase
from ..db.pit_inlet import PitInletDatabase
from ..db.rf import RainfallDatabase
from ..db.xs import CrossSectionDatabase
from ..abc.cf import ControlFile
from ..abc.build_state import BuildState
from ..inp.cf import ControlFileInput
from ..inp.db import DatabaseInput
from ..inp.file import FileInput
from ..utils.patterns import increment_fpath, get_iter_number, get_geom_ext
from ..utils.settings import Settings
from ..utils.commands import get_commands, build_tuflow_command_string
from ..utils.scope_writer import ScopeWriter
from ..dataclasses.altered_input import AlteredInputs
from .. import const

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class ControlFileBuildState(BuildState, ControlFile):
    """Abstract control file class for the build state.

    This class contains all information in the control file, including all information
    in all IF statements. It will also try and collect all files that could be associated
    with it.
    """
    TUFLOW_TYPE = 'ControlFile'

    def __new__(cls,
                path: PathLike = None,
                settings: Settings = None,
                parent: BuildState = None,
                scope: ScopeList = None,
                **kwargs) -> 'ControlFileBuildState':
        """:code:`__new__` is used to create an appropriate instance of the Control File class based on the
        file extension. e.g. geometry_control_file.tgc => TGC

        See :meth:`__init__ <pytuflow.tmf.ControlFileBuildState.__init__>` for description of parameters.
        """

        if path and TuflowPath(path).suffix.lower() == '.tcf':
            from ..cf.tcf import TCF
            cls = TCF
        elif path and TuflowPath(path).suffix.lower() == '.tgc':
            from ..cf.tgc import TGC
            cls = TGC
        elif path and TuflowPath(path).suffix.lower() == '.tbc':
            from ..cf.tbc import TBC
            cls = TBC
        elif path and TuflowPath(path).suffix.lower() == '.ecf':
            from ..cf.ecf import ECF
            cls = ECF
        elif path and TuflowPath(path).suffix.lower() == '.tef':
            from ..cf.tef import TEF
            cls = TEF
        elif path and TuflowPath(path).suffix.lower() == '.qcf':
            from ..cf.qcf import QCF
            cls = QCF
        elif path and TuflowPath(path).suffix.lower() == '.adcf':
            from ..cf.adcf import ADCF
            cls = ADCF
        elif path and TuflowPath(path).suffix.lower() in ['.trfc', '.trfcf']:
            from ..cf.trfc import TRFC
            cls = TRFC
        elif path and TuflowPath(path).suffix.lower() == '.toc':
            from ..cf.toc import TOC
            cls = TOC
        elif path and TuflowPath(path).suffix.lower() == '.tesf':
            from ..cf.tesf import TESF
            cls = TESF
        elif path and TuflowPath(path).suffix.lower() == '.tscf':
            from ..cf.tscf import TSCF
            cls = TSCF
        elif path and TuflowPath(path).suffix.lower() == '.trd':
            from ..cf.trd import TRD
            cls = TRD
        self = object.__new__(cls)
        return self

    def __init__(self,
                 path: PathLike = None,
                 settings: Settings = None,
                 parent: ControlFile = None,
                 scope: ScopeList = None,
                 **kwargs) -> None:
        """Initialises the control file class (BuildState). This is the main entry point for reading/writing
        control files.

        Parameters
        ----------
        path : PathLike, optional
            The path to the control file. If set to None, will initialise an empty control file.
        settings : Settings, optional
            A Settings object ("ConvertSettings" object from the convert_tuflow_model_gis_format library).
            This object stores useful information such as variable mappings, current spatial database etc. If
            set to None, a new Settings object will be created.
        parent : ControlFile, optional
            Will set the parent of the control file to another control file e.g. for a TGC, the parent
            should be set to the TCF.
        scope : ScopeList, optional
            A list of scope objects that will be inherited by the control file itself. Not currently used
            but reserved in case this is useful information in the future.
        """
        self._priv_prop = {}
        #: TuflowPath: the path to the control file
        self.path = path
        self._settings = settings
        self._input_to_loaded_value = {}
        self._in_trd_load = False
        self._trd_index = None
        #: Inputs: list of inputs and comments in the control file
        self.inputs = Inputs()
        #: bool: True if the control file has been altered since the last write
        self.dirty = False
        #: ControlFile: the parent control file
        self.parent = parent
        #: AlteredInputs: a list of all changes made to the control file since the last write
        self.altered_inputs = AlteredInputs()
        self._scope = scope
        
        if self.path:
            try:
                self.load(path, settings)
                self._loaded = True
            except FileNotFoundError:
                self._loaded = False
        else:
            self._loaded = False

    def __repr__(self):
        return f'<{self.TUFLOW_TYPE}> {str(self)}'

    def __str__(self):
        if self.path:
            if self._loaded:
                return self.path.name
            else:
                return f'{self.path.name} (not found)'
        return 'Empty Control File'

    def __repr__(self) -> str:
        return f'<{self.TUFLOW_TYPE}> {str(self)}'

    def load(self, path: PathLike, settings: Settings = None) -> None:
        """Loads control file from path - loops through commands in control file.
        Called by :meth:`__init__ <pytuflow.tmf.ControlFileBuildState.__init__>`.

        This method should not be called by the user.

        Parameters
        ----------
        path : PathLike
            The path to the control file. If set to None, will initialise an empty control file.
        settings : Settings
            A Settings object ("ConvertSettings" object from the convert_tuflow_model_gis_format library).
            This object stores useful information such as variable mappings, current spatial database etc. If
            set to None, a new Settings object will be created.
        """
        p = TuflowPath(path)
        if not self._in_trd_load:
            self.path = p
        if not p.exists():
            logger.error('Control file not found: {}'.format(path))
            raise FileNotFoundError(f'Control file not found: {p}')
        logger.info('Loading control file at: {}'.format(p))

        if not settings:
            settings = Settings(*['-tcf', str(path)])
            settings.resolve_var = True
            settings.read_tcf()
            self._settings = settings
        else:
            self._settings = Settings(convert_settings=settings)
            self._settings.control_file = self.path

        for command in get_commands(p, self._settings):
            trd = p if self._in_trd_load else None
            self._append_input(command, trd)

    def figure_out_file_scopes(self, scope_list: ScopeList) -> None:
        """Overrides abstract method from BuildState.

        Try and resolve unknown scope variable values based on a known scope list. Not currently connected to anything
        (previously was connected to the load method).

        This method is designed to trickle through all
        BuildState objects and figure out scope definitions when scenarios/variables are used in file names and the
        scope is guessed based on the file name and any files it found

        e.g. :code:`M01_<<s1>>_001.tgc` - :code:`M01_5m_001.tgc` - would guess that the file
        has a :code:`Scope(Scenario, '5m')`

        Parameters
        ----------
        scope_list: ScopeList
            list of known scopes
        """
        for input_ in self.inputs:
            input_.figure_out_file_scopes(scope_list)

    def get_files(self, recursive: bool = True) -> list[PathLike]:
        """Overrides abstract method from BuildState.

        Returns a list of all the files referenced in the control file. This includes files referenced in
        input GIS layers. The routine will only search through other control files if recursive is set to True.

        Parameters
        ----------
        recursive : bool
            if set to True, will search through other control files for files. If set to False, will only
            search through the current control file.

        Returns
        -------
        list[PathLike]
            A list of all files referenced in the control file.
        """
        files = []
        for input_ in self.inputs:
            if isinstance(input_, FileInput):
                for file in input_.get_files():
                    if file not in files:
                        files.append(file)
            if isinstance(input_, ControlFileInput) or isinstance(input_, DatabaseInput):
                loaded_value = self.input_to_loaded_value(input_)
                if recursive:
                    for inp in loaded_value:
                        for file in inp.get_files(recursive):
                            if file not in files:
                                files.append(file)
        return files

    def record_change(self, inputs: Inputs, change_type: str) -> None:
        """Record a user change to the inputs.

        Not private, but should not be called by the user.

        Parameters
        ----------
        inputs : Inputs
            list of inputs that have been changed. Should use the "Inputs" class as this contains extra
            information about the inputs.
        change_type : str
            the type of change that has been made. This is used to determine what to do when storing and
            undoing the change. See AlteredInputs class for change_type options.
        """
        uuid = uuid4()  # allows input changes to be grouped together by giving the same uuid
        for inp, ind in inputs.iter_indexes():
            inp.dirty = True
            self.dirty = True
            self.tcf.dirty = True
            self.tcf.altered_inputs.add(inp, ind[0], ind[1], uuid, change_type)

    def undo(self, reset_children: bool = True) -> InputBuildState:
        """Undoes the last change as recorded by the record_change method. Returns the input that was changed.

        Parameters
        ----------
        reset_children : bool
            only applicable for TCF class. If set to True, will undo the last change in the TCF or other
            control files. If set to False, will only undo the last change in the current control file.

        Returns
        -------
        InputBuildState
            the input(s) that were reverted
        """
        if self.tcf != self and reset_children:
            reset_children = False
            # logger.error('No arguments expected. Can only undo children from the TCF.')
            # raise TypeError('No arguments expected. Can only undo children from the TCF.')
        return self.tcf.altered_inputs.undo(self, reset_children)

    def reset(self, reset_children: bool = True) -> None:
        """Resets all changes made to the control file since last call to write().

        Parameters
        ----------
        reset_children : bool
            only applicable for TCF class. If set to True, will reset changes in the TCF and other
            control files. If set to False, will only reset the changes in the current control file.
        """
        if self.tcf != self and reset_children:
            reset_children = False
            # logger.error('No arguments expected. Can only undo children from the TCF.')
            # raise TypeError('No arguments expected. Can only undo children from the TCF.')
        self.tcf.altered_inputs.reset(self, reset_children)

    def remove_input(self, inp: 'InputBuildState') -> 'InputBuildState':
        """Removes an input from the control file.

        Parameters
        ----------
        inp : InputBuildState
            the input to remove from the control file.

        Returns
        -------
        InputBuildState
            the input that was removed
        """
        if inp in self.inputs:
            inputs = Inputs()
            inputs.append(inp)
            orig_val = inp.value
            self.inputs.remove(inp)
            self._remove_attr(inp, orig_val)
            self.record_change(inputs, 'remove_input')
            if self.tcf and self.tcf != self:
                self.tcf.record_change(inputs, 'remove_input')
            return inp
        else:
            for input_ in self.inputs:
                if isinstance(input_, ControlFileInput):
                    loaded_value = self.input_to_loaded_value(input_)
                    if loaded_value is None:
                        continue
                    for cls_ in loaded_value:
                        inp_ = cls_.remove_input(inp)
                        if inp_:
                            return inp_

    def append_input(self, input_text: str, gap: int = 0) -> 'InputBuildState':
        """Appends a new input to the end of the control file.

        Parameters
        ----------
        input_text : str
            the text of the input to add to the control file. This can be a full command or a
            file name for GIS inputs.
        gap : str
            the number of blank lines to add before the new input.

        Returns
        -------
        InputBuildState
            the input that was added
        """
        return self._add_input(None, input_text, True, gap)

    def insert_input(self, inp: 'Input', input_text: str, after: bool = False, gap: int = 0) -> 'InputBuildState':
        """Inserts an input before or after another input.

        Parameters
        ----------
        inp : InputBuildState
            the input to place the new command before or after
        input_text : str
            the text of the input to add to the control file. This can be a full command or a
            file name for GIS inputs.
        after : bool
            True to place the new command after the referenced input, False to place before. Default is False.
        gap : int
            the number of blank lines to separate the new input from the specified "inp".

        Returns
        -------
        InputBuildState
            the input that was added
        """
        return self._add_input(inp, input_text, after, gap)

    def comment_out(self, inp: InputBuildState) -> InputBuildState:
        """Comments out a given input.

        Parameters
        ----------
        inp : InputBuildState
            the input to comment out

        Returns
        -------
        InputBuildState
            the new, commented out input
        """
        new_inp = self._comment_out(inp)
        inputs = Inputs()
        inputs.append(new_inp)
        self.record_change(inputs, 'comment_out')
        if self.tcf and self.tcf != self:
            self.tcf.record_change(inputs, 'comment_out')
        return new_inp

    def uncomment(self, inp: 'InputBuildState') -> InputBuildState:
        """Uncomment a given input.

        Parameters
        ----------
        inp : InputBuildState
            the input to uncomment

        Returns
        -------
        InputBuildState
            the new, uncommented input
        """
        new_inp = self._uncomment(inp)
        inputs = Inputs()
        inputs.append(new_inp)
        self.record_change(inputs, 'uncomment')
        if self.tcf and self.tcf != self:
            self.tcf.record_change(inputs, 'uncomment')
        return new_inp

    def write(self, inc: str = 'auto') -> 'ControlFileBuildState':
        """Write the object to file. From the TCF class, other control files will also be written if they are 'dirty'.

        options for 'inc' are:

        * :code:`'auto'` - automatically increments the file name
          (adds + 1 to the number at the end of the file name if it exists - otherwise will append 001)
        * :code:`'inplace'` - overwrites the existing file
        * :code:`str` - user defined suffix to add to the file name - will replace the existing suffix if it is a number

        Parameters
        ----------
        inc : str
            the increment method

        Returns
        -------
        ControlFileBuildState
            the control file that was written
        """
        if not self._loaded:
            inc = 'inplace'
        fpath = increment_fpath(self.path, inc)
        geom_ext = get_geom_ext(fpath.stem)
        inc_ = inc if inc.lower() == 'inplace' else get_iter_number(fpath.stem, geom_ext)
        with fpath.open('w') as fo:
            scope_writer = ScopeWriter()
            for i, inp in enumerate(self.inputs._inputs):
                if not inp.trd:
                    self._write(fo, inp, scope_writer, inc_)
            fo.write(scope_writer.write_scope([]))
        self.path = fpath
        self._loaded = True
        self.altered_inputs.clear()
        return self

    def preview(self) -> None:
        """Preview the control file in the console."""
        fo = io.StringIO()
        scope_writer = ScopeWriter()
        for i, inp in enumerate(self.inputs._inputs):
            fo.write(scope_writer.write_scope(inp.scope()))
            inp.write(fo, scope_writer)
        fo.write(scope_writer.write_scope([]))
        print(fo.getvalue())

    def _write(self, fo: TextIO, inp: InputBuildState, scope_writer: ScopeWriter, inc: str) -> None:
        """Private routine for writing the control file."""
        fo.write(scope_writer.write_scope(inp.scope()))
        if (isinstance(inp, ControlFileInput) or isinstance(inp, DatabaseInput)) and self.input_to_loaded_value(inp):
            loaded_value = self.input_to_loaded_value(inp)
            for class_ in loaded_value:
                if class_.dirty:
                    class_.write(inc)
                    inp.update_value(increment_fpath(inp.expanded_value, inc))
        elif isinstance(inp, ControlFileInput):  # trd
            from .trd import TRD
            for file in inp.get_files():
                trd_inputs = TRD.get_inputs(self, file)
                dirty = bool([x for x in trd_inputs if x.dirty])
                if dirty:
                    outfpath = increment_fpath(file, inc)
                    with outfpath.open('w') as trd_fo:
                        for inp_ in trd_inputs:
                            self._write(trd_fo, inp_, scope_writer, inc)
                    inp.update_value(increment_fpath(inp.expanded_value, inc))

        inp.write(fo, scope_writer)
        inp.dirty = False

    def _load_input_value(self, inp: 'InputBuildState') -> None:
        if inp.raw_command_obj().is_read_file():  # special treatment of read files
            non_exist_files = [x for x in inp.files if not x.exists()]
            if not non_exist_files:
                self.inputs.pop()
                self._in_trd_load = True
                [self.load(x, inp.raw_command_obj().settings) for x in inp.files]
                self._in_trd_load = False
                return

        loaded_values = None
        if isinstance(inp, ControlFileInput):
            loaded_values = Inputs([ControlFileBuildState(x, settings=self._settings, parent=self) for x in inp.files])
        elif isinstance(inp, DatabaseInput) or inp.raw_command_obj().is_table_link():
            loaded_values = Inputs([])
            for file in inp.files:
                class_ = None
                if not file.exists():
                    logger.error('Input file not found: {}'.format(file))
                    file = None
                if inp.raw_command_obj().is_bc_dbase_file():
                    class_ = BCDatabase(file, var_names=self._settings.wildcards)
                elif inp.raw_command_obj().is_mat_dbase():
                    class_ = MatDatabase(file)
                elif inp.raw_command_obj().is_soil_dbase():
                    class_ = SoilDatabase(file)
                elif inp.raw_command_obj().is_pit_inlet_dbase_file():
                    class_ = PitInletDatabase(file)
                elif inp.raw_command_obj().is_rainfall_grid():
                    class_ = RainfallDatabase(file)
                elif inp.raw_command_obj().is_table_link():
                    class_ = CrossSectionDatabase(file)
                elif inp.raw_command_obj().is_xs_dbase():
                    class_ = CrossSectionDatabase(file)
                if class_:
                    loaded_values.append(class_)

        self._input_to_loaded_value[inp] = loaded_values  # ES Note: to be deleted later
        inp.cf = loaded_values  # ES Note: this replaces the above line as the correct way to store the loaded values
        self._input_as_attr(inp)

    def _append_input(self, cmd: Command, trd: TuflowPath):
        if cmd.original_text and cmd.original_text[-1] != '\n':
            cmd = Command(cmd.original_text + '\n', cmd.settings)
        inp = InputBuildState(self, cmd)
        self.inputs.append(inp)
        inp.trd = trd
        self._settings = cmd.settings
        self._load_input_value(inp)
        return inp

    def _insert_input(self, ind: int, cmd: Command, trd: TuflowPath, after: bool, hidden_index: bool = False) -> 'InputBuildState':
        inp = InputBuildState(self, cmd)
        if self.inputs._inputs and len(self.inputs._inputs) > ind:
            self.inputs.insert(ind, inp, after, hidden_index)
        else:
            self.inputs.append(inp)
        inp.trd = trd
        self._settings = cmd.settings
        self._load_input_value(inp)
        return inp

    def _add_input(self, inp: Input, input_text: str, after: bool = True, gap: int = 0) -> InputBuildState:
        """
        Adds a new input to the control file.

        input_text: can a string with a full command: "Hardware == GPU" or it can be a file or list of files and the
                    left hand side of the command will be guessed from the file name.
        inp: the input to place the new command after or before
        after: bool - True to place the new command after the referenced input, False to place before
        blank_lines: number of blank lines to add before this command
        """
        if not inp or inp in self.inputs:
            if inp:
                cmd_ = inp.raw_command_obj()
            else:
                settings = Settings()
                if self.path:
                    settings.control_file = TuflowPath(self.path)
                cmd_ = Command('', settings)
            inputs = Inputs()  # list to pass into record_change
            if not inp:
                for j in range(gap):
                    blank_inp = self._append_input(Command('\n', cmd_.settings), None)
            if cmd_.is_read_gis() or cmd_.is_read_grid() or cmd_.is_read_tin() or cmd_.is_read_projection():
                input_text = build_tuflow_command_string(input_text, cmd_.settings.control_file, cmd_.settings.read_spatial_database)
            else:
                input_text = f'{input_text.rstrip()}\n'
            cmd = Command(input_text, cmd_.settings)
            if inp:
                i = self.inputs.index(inp)
                inp_ = self._insert_input(i, cmd, None, after)
            else:
                inp_ = self._append_input(cmd, None)
            inputs.append(inp_)  # must be done after adding to list of control_file.inputs
            for j in range(gap):
                if inp:
                    i = self.inputs.index(inp)
                    blank_inp = self._insert_input(i, Command('\n', cmd_.settings), None, after)
                    inputs.append(blank_inp)  # must be done after adding to list of control_file.inputs
            self.record_change(inputs, 'add_input')
            if self.tcf and self.tcf != self:
                self.tcf.record_change(inputs, 'add_input')
            return inp_
        else:
            for input_ in self.inputs:
                # if 'ControlFileInput' in repr(input_):
                if isinstance(input_, ControlFileInput):
                    loaded_value = self.input_to_loaded_value(input_)
                    if loaded_value is None:
                        continue
                    for cls_ in loaded_value:
                        inp_ = cls_._add_input(inp, input_text, after, gap)
                        if inp_:
                            return inp_

    def _comment_out(self, inp: InputBuildState) -> InputBuildState:
        if inp is None:
            if inp is not None:
                return inp  # already a comment

        settings = inp.raw_command_obj().settings
        text = inp.raw_command_obj().original_text
        trd = inp.trd
        i = -1
        for i, t in enumerate(text):
            if t not in  [' ', '\t']:
                break
        if i == -1:
            return
        if i == len(text) - 1:
            i = 0
        if i < 2:
            new_text = f'! {text}'
        else:
            new_text = text[:i] + '! ' + text[i:]

        new_inp = InputBuildState(self, Command(new_text, settings))
        new_inp.trd = trd
        self.inputs.amend(inp, new_inp)
        new_inp.uuid = inp.uuid
        return new_inp

    def _uncomment(self, inp: 'InputBuildState') -> InputBuildState:
        if inp:
            return inp  # a valid input already

        settings = inp.raw_command_obj().settings
        text = inp.raw_command_obj().original_text
        trd = inp.trd

        if '!' not in text and '#' not in text:
            logger.warning('Blank line')
            raise ValueError('Blank line')

        if '!' in text:
            i = text.index('!')
            if i + 1 < len(text) and text[i+1] == ' ':
                new_text = text.replace('! ', '', 1)
            else:
                new_text = text.replace('!', '', 1)
        else:
            i = text.index('#')
            if i + 1 < len(text) and text[i+1] == ' ':
                new_text = text.replace('# ', '', 1)
            else:
                new_text = text.replace('#', '', 1)

        new_inp = InputBuildState(self, Command(new_text, settings))
        new_inp.trd = trd
        self.inputs.amend(inp, new_inp)
        new_inp.uuid = inp.uuid
        return new_inp
