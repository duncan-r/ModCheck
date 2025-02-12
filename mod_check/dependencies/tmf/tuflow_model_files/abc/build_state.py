import io
from abc import abstractmethod

from .run_state import RunState
from ..utils.context import Context
from ..dataclasses.types import PathLike
from ..dataclasses.scope import ScopeList, Scope


class BuildState:
    """Abstract model class containing information when the model is in 'Build State' or 'Configuration State'.

    i.e. inputs from all scenarios/events are included and variable names haven't been resolved yet.
    """

    def scope(self, else_: bool = True) -> ScopeList:
        """Returns a list of scopes.

        If else\_ is set to True, removes negative scopes and adds anything
        in an ELSE statement with scope name 'ELSE'. This essentially presents it as the user would
        see it in a text editor.

        e.g.

        In control file

        ::

            If Scenario == D01
                <input 1>
            else
                <input 2>
            end if

        | input 1 would be stored with scope [Scope(Scenario, 'D01')]
        | input 2 would be stored with scope [Scope(Scenario, '!D01')]
        | input 2 with "else\_" set to True would be returned as [Scope(Scenario, 'ELSE')]

        Parameters
        ----------
        else\_ : bool
            if set to True, negative scopes are removed and ELSE scopes are added. If set to False, the
            scope list is returned as it is stored internally.

        Returns
        -------
        ScopeList
            List of scopes in the object.
        """
        if not hasattr(self, '_scope') or self._scope is None:
            return ScopeList()

        if not else_:
            return self._scope

        # highlight where else block is used - this is not how it is stored internally but may be nice for the user
        scope_list = ScopeList()
        for s in self._scope:
            if not s.is_neg():
                if s not in scope_list:
                    scope_list.append(s)
            elif s.is_else():
                s2 = Scope(s._type, 'ELSE')
                if s2 not in scope_list:
                    scope_list.append(s2)

        return scope_list

    @abstractmethod
    def figure_out_file_scopes(self, scope_list: ScopeList) -> None:
        """Resolve unknown scopes by passing in a list of known scopes.

        Unknown scopes are when <<~s~>>, <<~e~>>, <<variable>>, or ~event~ are encountered in file names and they
        cannot be resolved due to ambiguity, missing files, or missing information.

        This is not the same as using context to resolve scopes into a RunState. The method populates scope information
        where any is missing where variable names have been used in file names.

        Parameters
        ----------
        scope_list : ScopeList
            List of known scopes to resolve unknown scopes.
        """
        pass

    @abstractmethod
    def get_files(self, *args, **kwargs) -> list[PathLike]:
        """Get a list of files referenced in this object. Files should be absolute paths
        and can return multiple files even if only one input is referenced.

        At least one file per file reference should be returned even if the file does not exist.

        Returns
        -------
        list[PathLike]
            List of files referenced in the object.
        """
        pass

    @abstractmethod
    def write(self, *args, **kwargs) -> str:
        """Write the object to file."""
        pass

    def context(self, *args, **kwargs) -> RunState:
        """Create a RunState version of this object.

        When called, expects a ContextLike argument to be passed in. Generally from a user point of view, this
        is a list of batch file run arguments as either a string or list object. A dictionary object can also be used in
        the form of {'s1': 'value', 's2': 'value'}, however an OrderedDict is preferred to maintain the order of the
        input arguments as this can be important for output naming in TUFLOW.

        A Context object, that has already been initialised, can also be passed using the 'context' keyword argument.

        Returns
        -------
        RunState
            RunState object with the context passed in.
        """
        if kwargs.get('context'):
            ctx = kwargs['context']
        else:
            ctx = Context(args, kwargs)
        parent = kwargs['parent'] if 'parent' in kwargs else None
        return RunState(self, ctx, parent)
