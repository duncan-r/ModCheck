from abc import abstractmethod
from typing import TYPE_CHECKING

from .cf import ControlFile
from .db import Database
from .input import Input
from ..dataclasses.types import PathLike
from ..dataclasses.scope import ScopeList, Scope
from ..utils.context import Context

if TYPE_CHECKING:
    from .build_state import BuildState


class RunState:
    """Abstract model class containing information when the model is in 'Run State'.

    i.e. context information on a given run has been provided (if any) and only inputs within the scope of
    the run are included also variable names have been resolved.

    This class should only be generated from an instance of a BuildState class using the 'context' method.
    """

    def __new__(cls, build_state: 'BuildState', context: Context, parent) -> object:
        """:code:`__new__` is used to create a new instance of the appropriate run class based on the
        type of BuildState class that is passed in.
        """
        from ..db.xs import CrossSectionDatabase

        if isinstance(build_state, ControlFile):
            from ..cf._cf_run_state import ControlFileRunState
            from ..cf.tcf_run_state import TCFRunState
            from ..cf.tef_run_state import TEFRunState
            if build_state.TUFLOW_TYPE == 'TuflowControlFile':
                cls = TCFRunState
            elif build_state.TUFLOW_TYPE == 'TuflowEventFile':
                cls = TEFRunState
            else:
                cls = ControlFileRunState
        elif isinstance(build_state, CrossSectionDatabase):  # special case, database is too different from others and req. runstate to be overridden
            from ..db.xs_run_state import CrossSectionRunState
            cls = CrossSectionRunState
        elif isinstance(build_state, Database):
            from ..db._db_run_state import DatabaseRunState
            cls = DatabaseRunState
        elif isinstance(build_state, Input):
            from ..inp._inp_run_state import InputRunState
            cls = InputRunState
        else:
            raise NotImplementedError('BuildState must be subclassed into either '
                                      'ControlFile, Database, or Input classes')
        self = object.__new__(cls)
        self.parent = parent
        self.bs = build_state
        self.ctx = context
        self._name = build_state.__class__.__name__
        # Note (DR): What does this do? Is it a fallback to handle unknown CF types? I can't see why it would resolve to True?
        if '<ControlFile>' in repr(self.bs):
            self._name = 'ControlFile'
        self._init()
        self._resolve_scope_in_context()

        return self

    def __init__(self, build_state: 'BuildState', context: Context, parent: ControlFile) -> None:
        """
        Parameters
        ----------
        build_state : BuildState
            The BuildState object that the RunState object is based on.
        context : Context
            The context object that the RunState object is based on.
        parent : ControlFile
            The parent control file.
        """
        #: ControlFile: the parent control file
        self.parent = parent
        #: BuildState: the BuildState object that the RunState object is based on.
        self.bs = build_state
        #: Context: the context object that the RunState object is based on.
        self.ctx = context
        super().__init__()

    @abstractmethod
    def _init(self) -> None:
        """Method called after generic initialisation to allow custom initialisation in subclasses."""

    @abstractmethod
    def _resolve_scope_in_context(self) -> None:
        """Method called after all initialisation and resolves all inputs to remove variable names and unused inputs."""

    @abstractmethod
    def get_files(self, *args, **kwargs) -> list[PathLike]:
        """Get a list of files referenced in this object. Returned files should reference absolute paths and
         be resolved (i.e. no variables or event/scenario wildcards).

        Paths should still be returned even if the file does not exist.

        Returns
        -------
        list[PathLike]
            A list of files referenced in this object.
        """
        pass

    def scope(self, *args, **kwargs) -> ScopeList:
        """Returns the object's scope.

        Unlike :meth:`BuildState.scope() <pytuflow.tmf.BuildState.scope()>`, :code:`else\_` argument
        isn't required as any scope that uses 'else' in the logic should be resolved.

        Returns
        -------
        ScopeList
            The object's scope.
        """
        if hasattr(self, 'bs') and hasattr(self.bs, 'scope'):
            return self._cull_scope_list(self.bs.scope(False))
        return ScopeList()

    def context(self) -> ScopeList:
        """Returns the ScopeList that makes up the objects Context for the given RunState Object.

        Returns
        -------
        ScopeList
            The ScopeList for the given RunState Object.
        """
        scope_list = ScopeList()
        for scope in self.ctx.available_scopes:
            scopes = scope.explode()
            for scope2 in scopes:
                if scope2 == Scope('EVENT') and self.ctx.events_loaded:
                    if isinstance(scope2.name, list):
                        name = scope2.name[0]
                    else:
                        name = scope2.name
                    event = self.ctx._event_db.get(name)
                    if event is None:
                        scope_list.append(scope2)
                    else:
                        scope3 = Scope('EVENT', event.value, var=event.variable)
                        scope_list.append(scope3)
                if scope2 == Scope('EVENT VARIABLE'):
                    pass
                else:
                    scope_list.append(scope2)

        return scope_list

    def _cull_scope_list(self, scope_list: ScopeList) -> ScopeList:
        """Cull the scope list to remove resolved scopes.
        E.g. Scenario/Event/Event Variable scope should all be resolved.
        """
        # assume all resolvable scopes are resolved!
        ret_scope_list = ScopeList([x for x in scope_list if not x.resolvable()])
        if not ret_scope_list:
            ret_scope_list.append(Scope('GLOBAL'))
        return ret_scope_list
