from .tef_build_state import TEFBuildState
from .tef_run_state import TEFRunState
from .cf_load_factory import ControlFileLoadMixin
from ..context import Context
from .cf_run_state import ControlFileRunState
from .. import const


class TEF(ControlFileLoadMixin, TEFBuildState):
    TUFLOW_TYPE = const.CONTROLFILE.TEF

    def context(self,
                run_context: str | dict[str, str] = '',
                context: Context | None = None,
                parent: ControlFileRunState | None = None) -> TEFRunState:
        # docstring inherited
        from .tef_run_state import TEFRunState
        ctx = context if context else Context(run_context, config=self.config)
        return TEFRunState(self, ctx, parent)
