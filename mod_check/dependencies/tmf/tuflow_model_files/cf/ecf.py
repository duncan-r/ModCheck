import re
import typing

from .cf_build_state import ControlFileBuildState
from .cf_run_state import ControlFileRunState
from .cf_load_factory import ControlFileLoadMixin
from ..context import Context
from .. import const

if typing.TYPE_CHECKING:
    from ..db.pit_inlet import PitInletDatabase, PitInletDatabaseRunState


class ECFRunState(ControlFileRunState):

    def pit_dbase(self) -> 'PitInletDatabaseRunState':
        """Returns the model's PitInletDatabaseRunState instance.

        Returns
        -------
        PitInletDatabaseRunState
            The PitInletDatabaseRunState instance.

        Raises
        ------
        KeyError
            If the pit inlet database is not found in the control file.

        Example
        -------
        >>> tcf = ... # assuming is an instance of TCF
        >>> pit_dbase = pit_dbase.context().ecf().pit_dbase()
        """
        return self._find_control_file('pit inlet database|depth discharge database', None, regex=True, regex_flags=re.IGNORECASE)


class ECF(ControlFileLoadMixin, ControlFileBuildState):
    TUFLOW_TYPE = const.CONTROLFILE.ECF

    def pit_dbase(self, context: Context = None) -> 'PitInletDatabase':
        """Returns the PitInletDatabase database instance.

        If more than one PitInletDatabase database instance exists, a Context object must be provided to resolve to the correct
        Pit Inlet Database.

        Parameters
        ----------
        context : Context, optional
            A context object to resolve the correct PitInletDatabase instance. Not required unless more than one
            PitInletDatabase file instance exists.

        Returns
        -------
        PitInletDatabase
            The PitInletDatabase instance.

        Raises
        ------
        KeyError
            If the PitInletDatabase database is not found in the control file.
        ValueError
            If more than one PitInletDatabase database is found and no context is provided to resolve the correct, or
            if the context does not resolve into a single PitInletDatabase database.

        Example
        -------
        >>> tcf = ... # assuming is an instance of TCF
        >>> bc_dbase = tcf.ecf().pit_dbase()
        """
        return self._find_control_file('pit inlet database|depth discharge database', context, regex=True, regex_flags=re.IGNORECASE)

    def context(self,
                run_context: str | dict[str, str] = '',
                context: Context | None = None,
                parent: ControlFileRunState | None = None) -> ECFRunState:
        # docstring inherited
        ctx = context if context else Context(run_context, config=self.config)
        return ECFRunState(self, ctx, parent)
