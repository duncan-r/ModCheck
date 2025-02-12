from ._inp_build_state import InputBuildState
from .. import const


class SettingInput(InputBuildState):
    """
    Input for Settings or Set commands.

    e.g.

    | :code:`TUTORIAL Model == ON`
    | :code:`Set Code == 0`
    """
    TUFLOW_TYPE = const.INPUT.SETTING

