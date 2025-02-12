import typing
import subprocess

from ._cf_run_state import ControlFileRunState
from ..abc.tcf_base import TCFBase
from ..dataclasses.file import TuflowPath
from ..dataclasses.types import PathLike

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()

if typing.TYPE_CHECKING:
    from pytuflow.results import TPC


class TCFRunState(ControlFileRunState, TCFBase):

    def __init__(self, *args, **kwargs) -> None:
        super(ControlFileRunState, self).__init__(*args, **kwargs)
        self._tpc = None

    def result_name(self) -> str:
        """Return the name of the result file without any extension of file path.

        Returns
        -------
        str
            Name of the result file.
        """
        return self.ctx.translate_result_name(self.path.name)

    def tpc(self) -> 'TPC':
        """Returns the TPC result from the simulation.

        Returns
        -------
        TPC
            The TPC result.
        """
        if self._tpc is not None:
            return self._tpc

        try:
            from pytuflow.results import TPC
        except ImportError:
            logger.error('Cannot import TPC from pytuflow.results. This method can only used when tmf has been '
                         'installed via the PyTuflow library.')
            raise ImportError('Cannot import TPC from pytuflow.results. This method can only used when tmf has been '
                              'installed via the PyTuflow library.')
        self._tpc = TPC(self.tpc_path())
        return self._tpc

    def tpc_path(self) -> TuflowPath:
        """Returns the path to the expected tpc file. Does not check it exists.

        Returns
        -------
        TuflowPath
            Path to the tpc file.
        """
        return (self.output_folder_2d() / 'plot' / self.result_name()).with_suffix('.tpc')

    def tlf_path(self) -> TuflowPath:
        """Returns the path to the expected tlf file. Does not check it exists.

        Returns
        -------
        TuflowPath
            Path to the tlf file.
        """
        return (self.log_folder_path() / self.result_name()).with_suffix('.tlf')

    def run(self, tuflow_bin: PathLike, prec: str = 'sp', add_tf_flags: list[str] = (), *args, **kwargs):
        """Run the control file in context using the specified TUFLOW binary.

        * TUFLOW binary can be a file path to the executable or a version name that has been registered using
          the register_tuflow_binary function.

        Can pass additional arguments that will be passed to the subprocess.Popen call. By default,
        a new console will be created for the subprocess.

        Must be done via the TCF.

        Parameters
        ----------
        tuflow_bin : PathLike
            Path to the TUFLOW binary or a registered version name.
        prec : str
            Precision of the run. Default is 'sp' (single precision).
            Other option is to use 'dp' (double precision) (accepted  synonyms 'idp' and 'double').
        add_tf_flags : list[str]
            list of additional flags specific to TUFLOW that will be passed directly to the subprocess.Popen call.
            e.g. :code:`add_tf_flags=['-t']` to pass in the :code:`-t` flag to run TUFLOW in test mode.
        *args, **kwargs:
            Will be passed to subprocess.Popen call.

        Returns
        -------
        subprocess.Popen
            The subprocess.Popen object that is created when the control file is run.
        """
        tuflow_bin_ = self._find_tuflow_bin(tuflow_bin, prec)
        return self._run(tuflow_bin_, add_tf_flags, *args, **kwargs)

    def test(self, tuflow_bin: PathLike, prec: str = 'sp') -> tuple[str, str]:
        """Run the control file in context using the specified TUFLOW binary in test mode.

        The stdout and stderr is automatically captured (no console window is produced) and once complete, the
        return values are the captured stdout and stderr.

        Must be done via the TCF.

        Parameters
        ----------
        tuflow_bin : PathLike
            Path to the TUFLOW binary or a registered version name.
        prec : str
            Precision of the run. Default is 'sp' (single precision).
            Other option is to use 'dp' (double precision) (accepted  synonyms 'idp' and 'double').

        Returns
        -------
        tuple[str, str]
            Captured stdout and stderr from the run.
        """
        proc = self.run(tuflow_bin, prec, add_tf_flags=['-t', '-nmb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW)
        out, err = proc.communicate()
        if isinstance(out, bytes):
            out = out.decode('utf-8')
        if isinstance(err, bytes):
            err = err.decode('utf-8')
        return out, err
