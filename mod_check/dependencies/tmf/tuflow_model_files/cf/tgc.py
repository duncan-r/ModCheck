from ._cf_build_state import ControlFileBuildState
from ._cf_load_factory import ControlFileLoadMixin
from ..dataclasses.scope import ScopeList
from ..dataclasses.types import PathLike
from ..utils.settings import Settings
from ..abc.build_state import BuildState
from .. import const


class TGC(ControlFileLoadMixin, ControlFileBuildState):
    """Initialises the TGC class in a build state.

    If the class is initialised with the :code:`fpath` parameter set to None, an empty class will be initialised.
    """
    TUFLOW_TYPE = const.CONTROLFILE.TGC

    def __new__(cls,
                path: PathLike = None,
                settings: Settings = None,
                parent: BuildState = None,
                scope: ScopeList = None,
                **kwargs) -> 'TGC':
        """Override __new__ to make sure a TGC class is returned."""
        return object.__new__(cls)
    
    def __init__(self,
                path: PathLike = None,
                settings: Settings = None,
                parent: BuildState = None,
                scope: ScopeList = None,
                **kwargs) -> 'TGC':
        """
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
        super(TGC, self).__init__(path, settings, parent, scope, **kwargs)

