from .cf_build_state import ControlFileBuildState
from .cf_load_factory import ControlFileLoadMixin
from .. import const


class TOC(ControlFileLoadMixin, ControlFileBuildState):
    TUFLOW_TYPE = const.CONTROLFILE.TOC
