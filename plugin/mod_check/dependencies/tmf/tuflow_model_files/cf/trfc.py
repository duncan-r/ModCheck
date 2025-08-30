from .cf_build_state import ControlFileBuildState
from .cf_load_factory import ControlFileLoadMixin
from .. import const


class TRFC(ControlFileLoadMixin, ControlFileBuildState):
    TUFLOW_TYPE = const.CONTROLFILE.TRFC
