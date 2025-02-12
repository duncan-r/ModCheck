from ._cf_build_state import ControlFileBuildState
from ._cf_load_factory import ControlFileLoadMixin
from ..dataclasses.scope import ScopeList
from ..dataclasses.types import PathLike
from ..utils.settings import Settings
from ..abc.build_state import BuildState
from ..dataclasses.event import EventDatabase
from ..dataclasses.scope import Scope
from ..utils.context import Context
from ..dataclasses.file import TuflowPath
from ..abc.cf import ControlFile
from ..db.bc_dbase import BCDatabase
from ..db.mat import MatDatabase
from ..db.soil import SoilDatabase
from .. import const
from .tcf_build_state import TCFBuildState


class TCF(ControlFileLoadMixin, TCFBuildState):
    """Initialises the TCF class in a build state. This is the main entry point for reading/writing
    control files.

    If the class is initialised with the :code:`fpath` parameter set to None, an empty class will be initialised.

    Typically, this class is initialised with only the :code:`fpath` parameter set to the path of the control file.
    """
    TUFLOW_TYPE = const.CONTROLFILE.TCF

    def __new__(cls,
                path: PathLike = None,
                settings: Settings = None,
                parent: BuildState = None,
                scope: ScopeList = None,
                **kwargs) -> object:
        """Override __new__ to make sure a TCF class is returned."""
        return object.__new__(cls)
    
    def __init__(self,
                path: PathLike = None,
                settings: Settings = None,
                parent: BuildState = None,
                scope: ScopeList = None,
                **kwargs) -> None:
        """
        Parameters
        ----------
        path : PathLike, optional
            The path to the control file. If set to None, will initialise an empty control file.
        settings : Settings, optional
            A Settings object ("ConvertSettings" object from the convert_tuflow_model_gis_format library).
            This object stores useful information such as variable mappings, current spatial database etc. If
            set to None, a new Settings object will be created. For TCFs, the settings object should be left as None.
        parent : ControlFile, optional
            Will set the parent of the control file to another control file e.g. for a TGC, the parent
            should be set to the TCF. For TCFs, the parent should be set to None.
        scope : ScopeList, optional
            A list of scope objects that will be inherited by the control file itself. Not currently used
            but reserved in case this is useful information in the future.
        log_level : str, optional
            The logging level to use for the control file. Options are 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
            Default is 'WARNING'.
        log_to_file : PathLike, optional
            If set, will log the control file to the given file path. Default is None.
        """
        super(TCF, self).__init__(path, settings, parent, scope, **kwargs)

