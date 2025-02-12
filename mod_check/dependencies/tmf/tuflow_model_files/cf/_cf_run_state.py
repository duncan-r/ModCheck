import re
import subprocess
from pathlib import Path

from ..dataclasses.types import PathLike
from ..dataclasses.inputs import Inputs
from ..abc.cf import ControlFile
from ..abc.run_state import RunState
from ..abc.db import Database
from ..cf.tcf import TCF
from ..utils.tuflow_binaries import tuflow_binaries

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class ControlFileRunState(RunState, ControlFile):
    """Class for storing the run state of a control file.
    Adds methods from RunState class to resolve scopes.
    """

    def __str__(self):
        if self.path:
            if self._loaded:
                return self.path.name
            else:
                logger.warning('Stored filepath not found for {}'.format(self.path.name))
                return f'{self.path.name} (not found)'
        return 'Empty Control File'

    def __repr__(self):
        return '<{0}Context> {1}'.format(self._name, str(self))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _init(self) -> None:
        """Called after the generic initialisation. Sets a number of generic properties for the class."""
        self._priv_prop = {}
        #: TuflowPath: Path to the control file.
        self.path = self.bs.path
        self._loaded = self.bs._loaded
        self._inputs = self.bs.inputs
        self._input_to_loaded_value = {}
        #: Inputs: list of inputs associated with this control file.
        self.inputs = Inputs()
        self.proc = -1

    def get_files(self, recursive: bool = False) -> list[PathLike]:
        """Public method that returns the list of files associated with this control file.

        Parameters
        ----------
        recursive : bool, optional
            If True, will also return files associated with control files and databases loaded by this control file.
            Default is False.

        Returns
        -------
        list of PathLike
            List of file paths associated with this control file.
        """
        files = []
        for inp in self.inputs:
            for file in inp.get_files():
                if file not in files:
                    files.append(file)
            if isinstance(inp, ControlFileRunState) or isinstance(inp, RunState):
                if not recursive:
                    continue
                loaded_value = self.input_to_loaded_value(inp)
                if isinstance(loaded_value, ControlFile) or isinstance(loaded_value, Database):
                    for file in loaded_value.get_files(recursive=True):
                        if file not in files:
                            files.append(file)

        return files

    def _find_tuflow_bin(self, tuflow_bin: PathLike, prec: str) -> str:
        """Returns the path to the TUFLOW binary to use for the run."""
        if Path(tuflow_bin).is_file() and not Path(tuflow_bin).exists():
            logger.error('tuflow binary not found: {0}'.format(tuflow_bin))
            raise FileNotFoundError('tuflow binary not found: {0}'.format(tuflow_bin))
        elif not Path(tuflow_bin).is_file():
            if tuflow_bin not in tuflow_binaries:
                # search for available tuflow versions in registered folders
                # do this only now (after checking explicitly registered binaries first)
                # just in case this is a slow step (network drives etc.)
                tuflow_binaries.check_tuflow_folders()
                if tuflow_bin not in tuflow_binaries:
                    logger.error('TUFLOW binary version not found: {0}'.format(tuflow_bin))
                    raise AttributeError('TUFLOW binary version not found: {0}'.format(tuflow_bin))
        tuflow_bin_ = str(tuflow_bin) if Path(tuflow_bin).is_file() else tuflow_binaries[tuflow_bin]
        if prec.upper() in ['DP', 'IDP', 'DOUBLE']:
            p = Path(tuflow_bin_)
            if 'dp' not in p.stem.lower():
                tuflow_bin_ = p.parent / str(p.name).replace('SP', 'DP')
        elif prec.upper() not in ['SP', 'ISP', 'SINGLE']:
            logger.error('Unrecognised "prec" argument: {0}'.format(prec))
            raise AttributeError('Unrecognised "prec" argument: {0}'.format(prec))

        return tuflow_bin_

    def _resolve_scope_in_context(self) -> None:
        """Method called after all initialisation and resolves all inputs to
        remove variable names and unused inputs.
        """

        # if context is empty, look for model events / scenario commands in file
        if self.ctx.is_empty():
            d = {}
            model_scenarios = self.bs.find_input(command='model scenario')
            for s in reversed(model_scenarios):
                d.update({'s{0}'.format(i+1): v for i, v in enumerate(re.split(r'[\t\s|,]+', s.value))})
                break
            model_events = self.bs.find_input(command='model event')
            for e in reversed(model_events):
                d.update({'e{0}'.format(i+1): v for i, v in enumerate(re.split(r'[\t\s|,]+', e.value))})
                break
            self.ctx.load_context_from_dict(d)

        # try and resolve variables
        if not self.ctx.var_loaded:
            var_inputs = self.bs.find_input(command='set variable', recursive=True)
            var_map = {}
            for var_input in var_inputs:
                if self.ctx.in_context_by_scope(var_input._scope):
                    var_name, var_val = var_input.raw_command_obj().parse_variable()
                    var_map[var_name] = var_val
            self.ctx.load_variables(var_map)

        # try and resolve events
        if not self.ctx.events_loaded:
            if isinstance(self.bs, TCF):
                event_db = self.bs.event_database(self.ctx)
                if event_db:
                    self.ctx.load_events(event_db)

        for input_ in self._inputs:
            if not self.ctx.in_context_by_scope(input_._scope):
                continue

            if input_.command.upper() == 'PAUSE':
                raise AttributeError('Pause command encountered: {0}'.format(input_.value))

            input_ctx = input_.context(context=self.ctx, parent=self)
            self.inputs.append(input_ctx)

            loaded_value = self.bs.input_to_loaded_value(input_)

            if loaded_value:  # either control files or databases
                path = input_ctx.file
                complex_input = [x for x in loaded_value if x.path == path]
                if not complex_input:
                    complex_input_ctx = loaded_value[0].context(context=self.ctx, parent=self)
                else:
                    complex_input_ctx = complex_input[0].context(context=self.ctx, parent=self)
                self._input_to_loaded_value[input_ctx] = complex_input_ctx  # ES Note: to be deleted in the future
                input_.cf = complex_input_ctx

            self._input_as_attr(input_ctx)

    def _run(self, bin_path: str, add_tf_flags: list[str], *args, **kwargs):
        """Method for running the control file using the tuflow binary specified."""
        if 'creationflags' not in kwargs:
            kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE
        args_ = [bin_path, '-b']
        for flag in add_tf_flags:
            if flag != '-b':
                args_.append(flag)
        args_.extend(self.ctx.context_args)
        args_.append(self.path)
        self.proc = subprocess.Popen(args_, *args, **kwargs)
        return self.proc
