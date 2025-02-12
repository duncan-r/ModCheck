import itertools
import re
from typing import Union

from .file import TuflowPath
from ..utils.patterns import extract_names_from_pattern, var_regex

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class ScopeList(list):
    """Custom container for a list of scope objects.

    Allows for overriding the use of the 'in' operator.
    Scope can contain multiple names (e.g. :code:`EXG | D01 | D02`) and this allows for checking if a scope is in
    the list. Scope will be considered in a list if any of the names match any of the expanded names in the scope list.

    e.g.

    * :code:`Scope('SCENARIO', 'test') in ScopeList([Scope('SCENARIO', 'test | test2')]) == True`
    * :code:`Scope('SCENARIO', 'test | test2') in ScopeList([Scope('SCENARIO', 'test2)]) == True`
    """

    def __contains__(self, item):
        return self.contains(item, True, True)

    def __add__(self, other):
        if isinstance(other, ScopeList):
            return ScopeList(list.__add__(self, other))
        elif isinstance(other, Scope):
            return ScopeList(list.__add__(self, [other]))
        else:
            logger.error('Cannot add ScopeList and {0}'.format(type(other)))
            raise TypeError('Cannot add ScopeList and {0}'.format(type(other)))

    def index(self, item):
        """Overrides the index method and will return the index based on the same logic as the __contains__ method.

        Parameters
        ----------
        item : Scope
            The scope to get the index of.

        Returns
        -------
        int
            The index of the scope in the ScopeList.
        """
        if not isinstance(item.name, list):
            if item.is_neg():
                scope = Scope(item._type, f'!{item.name}', var=item.var())
            else:
                scope = Scope(item._type, item.name, var=item.var())
            if not isinstance(scope.name, list):
                scope.name = [scope.name]
        try:
            for i, scope in enumerate(self):
                if not isinstance(item, scope.__class__):
                    continue
                for name in scope.name:
                    for name_ in item.name:
                        if name == name_:
                            return i
        except AttributeError:
            pass
        raise ValueError('{0} not in scope list'.format(item))

    def contains(self, item, neg: bool = True, explode: bool = True):
        """Returns True if the scope is contained with the ScopeList.

        Parameters
        ----------
        item : Scope
            The scope to check for.
        neg : bool, optional
            If True, will also check whether negative status matches.
        explode : bool, optional
            If True, will explode the scope before checking. E.g. Scenario D01 | D02 will explode to two separate
            scopes, otherwise if set to False, the item must match the scope exactly.

        Returns
        -------
        bool
            True if the scope is contained within the ScopeList, False otherwise.
        """
        if isinstance(item, Scope):
            if not isinstance(item.name, list):
                if item.is_neg():
                    scope = Scope(item._type, f'!{item.name}', var=item.var())
                else:
                    scope = Scope(item._type, item.name, var=item.var())
                if not isinstance(scope.name, list):
                    scope.name = [scope.name]
            if explode:
                self_scope_list = sum([x.explode(neg) for x in self], [])
                other_scope_list = sum([x.explode(neg) for x in item.explode()], [])
                for s1 in self_scope_list:
                    for s2 in other_scope_list:
                        if s1 == s2:
                            return True
            else:
                for scope in self:
                    if scope == item:
                        return True
        return False


class Scope:
    """Scope class for storing information about the input in regards to where/when it is used in the model.

    Scope objects typically store the scope names in a list (e.g. Scope = SCENARIO, names = ['D01', 'D02']). This
    is due to how the model defines blocks (e.g. :code:`If Scenario == D01 | D02)`. This means that when checking for
    a scope, scopes names within a single Scope class are considered to be 'or' (i.e. D01 or D02). e.g.:

    ::

        If Scenario == D01 | D02
            Read GIS Z shape == 2d_zsh_D01.shp
        End if

    The above is represented by:
    * :code:`Scope('SCENARIO', ['D01', 'D02'])`

    Even though TUFLOW does not support 'AND' logic in a single IF statement, it does support nested IF statements
    which is pretty much the same as 'AND'. This is treated by using a list of Scope objects. e.g.:

    ::

        If Scenario == D01
            If Scenario == D02
                Read GIS Z shape == 2d_zsh_D01_D02.shp
            End if
        End if

    The above is represented by:
    * :code:`[Scope('SCENARIO', ['D01']), Scope('SCENARIO', ['D02'])]`

    Because TUFLOW supports "Else IF" and "ELSE" blocks, the scope object can also store negative scopes prefixed
    with "!". Consider the example below:

    ::

        If Scenario == D01 | D02
            Read GIS Z shape == 2d_zsh_D01.shp
        Else if Scenario == D03
            Read GIS Z shape == 2d_zsh_D03.shp
        Else
            Read GIS Z shape == 2d_zsh_EXG.shp
        End if

    The Scope objects for each input would look like:
    * code:`"Read GIS Z shape == 2d_zsh_D01.shp" -> Scope('SCENARIO', ['D01', 'D02])`
    * code:`"Read GIS Z shape == 2d_zsh_D03.shp" -> [Scope('SCENARIO', ['D03']), Scope('SCENARIO', ['!D01', '!D02'])]`
    * code:`"Read GIS Z shape == 2d_zsh_EXG.shp" -> [Scope('SCENARIO', ['!D01', '!D02']), Scope('SCENARIO', ['!D03'])]`
    """

    __slots__ = ('name', '_known', '_var', '_else', '_neg')

    def __new__(cls, type_: str, name: str = '', var: str = None) -> object:
        """:code:`__new__` is used to create a new instance of the appropriate Scope class based on the
        type_ attribute that is passed in.

        Parameters
        ----------
        type_ : str
            The type of scope (e.g. 'SCENARIO', 'EVENT', 'VARIABLE', etc.)
        name : str, optional
            The name/value of the scope e.g. D01, or EXG
        var : str, optional
            The variable name. e.g. for variables it would be Scope('Variable', '5', var='CELL_SIZE')

        Returns
        -------
        object
            A new instance of the appropriate Scope class based on the type_ attribute.
        """

        if name and name[0] == '!':
            name = '| '.join([x.strip(' \t\n!') for x in name.split('|')])
            neg = True
        else:
            neg = False

        if not isinstance(type_, str):
            logger.error('type_ argument must be a string.')
            raise AttributeError('type_ argument must be a string.')

        type_ = type_.upper()
        if type_ == 'GLOBAL':
            cls = GlobalScope
        elif type_ in ['SCENARIO', 'SCENARIO (ELSE)', 's', 'S']:
            cls = ScenarioScope
        elif type_ == 'EVENT VARIABLE':
            cls = EventVariableScope
        elif type_ in ['EVENT', 'EVENT (ELSE)', 'e', 'E']:
            cls = EventScope
        elif type_ == '1D DOMAIN':
            cls = OneDimScope
        elif type_ == 'OUTPUT ZONE':
            cls = OutputZoneScope
        elif type_ == 'CONTROL':
            cls = ControlScope
        elif type_ == 'VARIABLE':
            cls = VariableScope
        else:
            logger.error('Scope type not recognised - {0}'.format(type_))
            raise TypeError('Scope type not recognised - {0}'.format(type_))

        self = object.__new__(cls)
        self._type = re.sub(r'\s+(ELSE)\s+', '', type_, flags=re.IGNORECASE)
        if self._type.lower() == 's':
            self._type = 'SCENARIO'
        elif self._type.lower() == 'e':
            self._type = 'EVENT'
        if not name or (len(name) >= 2 and name[:2] == '<<') or (var and name == var):
            self.name = name
            self._var = name
            self._known = False
        else:
            self.name = [x.strip() for x in name.split('|')]
            self._var = var
            self._known = True

        self._else = '(ELSE)' in type_
        self._neg = neg

        # if encounter <<~s~>> in a file name, convert the variable name to <<~s1~>> so
        # it can be replaced appropriately later (and do the same for <<~e~>>)
        if isinstance(self._var, str):
            if re.findall('<<~[EeSs]~>>', self._var):
                self._var = re.sub('~>>', '1~>>', self._var)

        return self

    def __init__(self, type_: str, name: str = '', var: str = None) -> None:
        """
        Parameters
        ----------
        type\_ : str
            The type of scope (e.g. 'SCENARIO', 'EVENT', 'VARIABLE', etc.)
        name : str, optional
            The name/value of the scope e.g. D01, or EXG
        var : str, optional
            The variable name. e.g. for variables it would be Scope('Variable', '5', var='CELL_SIZE')
        """
        pass

    def __str__(self):
        """Returns the Class name and a string representation of the scope names.
        Adds a "!" to the start of the scope name if the scope is negative. Will separate the
        scope names using "|" if there are multiple.
        """

        if self._neg:
            if isinstance(self.name, list):
                names = ['!{0}'.format(x) for x in self.name]
            else:
                names = '!{0}'.format(self.name)
        else:
            names = self.name
        if self._known:
            return '{0}: {1}'.format(self.__class__.__name__, ' | '.join(names))
        else:
            return '{0}: {1}'.format(self.__class__.__name__, names)

    def __repr__(self):
        """Similar to str() except adds fancy <> on either side of the class name."""

        if self._neg:
            if isinstance(self.name, list):
                names = ['!{0}'.format(x) for x in self.name]
            else:
                names = '!{0}'.format(self.name)
        else:
            names = self.name
        if self._known:
            return '<{0}> {1}'.format(self.__class__.__name__, ' | '.join(names))
        else:
            return '<{0}> {1}'.format(self.__class__.__name__, names)

    def __eq__(self, other):
        """Compares 2 Scope objects (if they are not the same Scope type, then it always returns False)
        * if other has no name, returns true if it is the same type
          (allows for testing if a scope type is in a list - e.g. Scope('SCENARIO') in ScopeList)
        * if other is known (i.e. not <<~s~>> or <<~e~>>), returns true if the names
          are the same (essentially an exact match)
        * if other is not known, return True if the names are the same (exact match) or if the
          var names are the same (i.e. they are both derived from the same variable name)

        The scope names or variable names are not case sensitive.
        """

        if isinstance(other, type(self)) or (isinstance(self, EventScope) and isinstance(other, EventVariableScope)) or (isinstance(self, EventVariableScope) and isinstance(other, EventScope)):
            if self.is_neg() != other.is_neg():
                return False
            if other._known:
                if self._known:
                    return sorted([x.lower() for x in self.name]) == sorted([x.lower() for x in other.name])
                else:
                    if other.var():
                        return other.var().lower() == self.var().lower()
                    else:
                        return False
            else:
                if self.name and other.name:
                    if self._known and self._var is not None:
                        return other.name.lower() == self._var.lower()
                    elif self._known and isinstance(self.name, list):
                        return False
                    return self.name.lower() == other.name.lower()
                else:
                    return True
        return False

    def __contains__(self, item):
        """Overrides the 'in' operator to search through the scope names as there can be more than one name
        associated with a single Scope instance.
        """

        if isinstance(self.name, list):
            return item.lower() in [x.lower() for x in self.name]
        return item.lower() == self.name.lower()
    
    def __lt__(self, object):
        """Allows for sorted lists. Sort based the string representation of the Scope class."""
        if isinstance(object, Scope):
            return str(self).lower() < str(object).lower()

    def known(self) -> bool:
        """Returns if the scope name is known (i.e. not :code:`<<~s~>>` or :code:`<<~e~>>`).

        Returns
        -------
        bool
            True if the scope name is known, False otherwise.
        """
        return self._known

    def is_neg(self) -> bool:
        """Returns whether the scope object is negative or not.

        Returns
        -------
        bool
            True if the scope object is negative, False otherwise.
        """
        return self._neg

    def is_else(self) -> bool:
        """Returns whether the scope object is from an ELSE block.

        Returns
        -------
        bool
            True if the scope object is from an ELSE block, False otherwise.
        """
        return self._else

    def explode(self, neg: bool = False) -> list['Scope']:
        """Explodes a Scope instance that may have multiple names into a list of Scope instances.

        Parameters
        ----------
        neg : bool, optional
            If True, will also retain the negative scope status.

        Returns
        -------
        list[Scope]
            A list of Scope instances where each instance has a single name.
        """
        if isinstance(self.name, list):
            if self._neg and neg:
                return [Scope(self._type, f'!{x}', var=self.var()) for x in self.name]
            else:
                return [Scope(self._type, x, var=self.var()) for x in self.name]
        return [self]

    def var(self) -> Union[str, None]:
        """Returns the variable name if there is one.

        Returns
        -------
        str
            The variable name if there is one, None otherwise.
        """
        return self._var

    def to_string_start(self) -> str:
        """Returns a TUFLOW string representation of the start of the scope object.

        Returns
        -------
        str
            A TUFLOW string representation of the start of the scope object.
        """

    def to_string_end(self) -> str:
        """Returns a TUFLOW string representation of the end of the scope object.

        Returns
        -------
        str
            A TUFLOW string representation of the end of the scope object.
        """

    def supports_else_if(self) -> bool:
        """Returns whether the scope object supports ELSE IF statements.

        Returns
        -------
        bool
            True if the scope object supports ELSE IF statements, False otherwise.
        """
        return True

    def resolvable(self) -> bool:
        """Returns whether the scope object can be resolved.

        e.g.

        ::

            If Scenario == D01  ! is resolvable
            Start 1D Domain  ! is not resolvable

        Returns
        -------
        bool
            True if the scope object can be resolved, False otherwise.
        """
        return False

    @staticmethod
    def from_string(template: str, string: str, event_var: list[str] = None) -> ScopeList:
        """Extracts scope from a string. It will also try and extract the scope name based on another string object.

        e.g.

        ::

            template = 'test_files_<<~s~>>.txt'
            string = 'test_files_scenario1.txt'
            scope = Scope('SCENARIO', name='scenario1', var='<<~s~>>')

        If it can't figure out the scope name, the name will be the same as the variable name.
        There is no obligation to be able to extract the scope name, it just may be useful later
        to get the user a list of possible scope names.

        Parameters
        ----------
        template : str
            the raw string that contains variables in it
        string : str
            the completed string that has been filled in with values
        event_var : list[str], optional
            a list of patterns to search for in the string to try and extract event variable names

        Returns
        -------
        ScopeList
            A list of Scope objects that represent the scopes in the string.
        """
        scopes = ScopeList()

        # find any <<~s~>> in file path
        scenario_scopes = extract_names_from_pattern(template, string, r'<<~s\d?~>>')
        scenario_scopes = [Scope('SCENARIO', v, var=k) for k, v in scenario_scopes.items()]
        scopes.extend(scenario_scopes)

        # find any <<~e~>> in file path
        event_scopes = extract_names_from_pattern(template, string, r'<<~e\d?~>>')
        event_scopes = [Scope('EVENT', v, var=k) for k, v in event_scopes.items()]
        scopes.extend(event_scopes)

        # find any variable names in file path
        var_names, var_scopes = [], []
        for var_name in var_regex.findall(template):
            if var_name in var_names:
                continue
            var_names.append(var_name)
            var_scopes.append(Scope('VARIABLE', var_name))
        scopes.extend(var_scopes)

        event_var_scopes = False
        if event_var:
            for pattern in event_var:
                if re.findall(r'<<~[EeSs]\d?~>>', pattern) or pattern == '(<<.{1,}?>>)':
                    continue
                event_variable_scopes = extract_names_from_pattern(template, string, pattern)
                for k, v in event_variable_scopes.items():
                    scope = Scope('EVENT VARIABLE', v, var=k)
                    if scope not in scopes:
                        scopes.append(scope)
                        event_var_scopes = True

        if not scenario_scopes and not event_scopes and not var_names and not event_var_scopes:
            scopes.append(Scope('GLOBAL', ''))

        return scopes

    @staticmethod
    def resolve_scope(req_scope_list: ScopeList, var_string: str, compare_string: str, test_scopes: ScopeList) -> None:
        """Resolve scope names from a list of scopes and a string to compare to.

        Allows the user to give a list of scope names to try and help resolve scope names. This still requires
        a template string to compare to and the scope names must be in the list that is passed in. The routine
        simply goes through every permutation of the known scope names and then compares the result to the
        input string for a match.

        Parameters
        ----------
        req_scope_list : ScopeList
            a list of scope names that are unknown
        var_string : str
            the template string that contains the variable names in it
        compare_string : str
            the completed/resolved string to compare to
        test_scopes : ScopeList
            a list of scope names that are known
        """
        unknown_scopes = {x.var(): x for x in req_scope_list if not x.known() and x.name and x.var()}
        if not unknown_scopes:
            return

        # replace all <<~s~>> and <<~e~>> with <<~s1~>> and <<~e1~>> to be consistent
        for wc in re.findall(r'<<~[EeSs]~>>', var_string):
            wc_ = re.sub(r'~>>', '1~>>', wc)
            var_string = re.sub(wc, wc_, var_string)

        # find all unique wildcards var_string
        wild_cards_ = re.findall(r'<<.+?>>', var_string, flags=re.IGNORECASE)
        wild_cards = []
        for wc in wild_cards_:
            if wc.lower() not in [x.lower() for x in wild_cards]:
                wild_cards.append(wc)

        # count the unique wildcards and then go through every permutation and try and match the compare_string
        nscope = len(wild_cards)
        for perm in itertools.permutations(test_scopes, nscope):
            test_name = var_string
            for wild_card, replacement in zip(wild_cards, perm):
                repl_name = replacement.name[0]
                test_name = re.sub(wild_card, repl_name, test_name, flags=re.IGNORECASE)
            # test if the names match, if they do, update the scope with the new name
            if TuflowPath(test_name) == TuflowPath(compare_string):
                for var, scope in unknown_scopes.items():
                    if var in wild_cards:
                        scope.name = perm[wild_cards.index(var)].name
                        scope._known = True
                return


class GlobalScope(Scope):
    """Scope class for when there is no scope."""

    def __repr__(self):
        return '<{0}>'.format(self.__class__.__name__)


class ScenarioScope(Scope):
    """
    Used for scenarios:

    * IF Scenario blocks
    * :code:`<<~s~>>` in file paths

    """

    def to_string_start(self) -> str:
        # docstring inherited
        return 'If Scenario == {0}'.format(' | '.join(self.name))

    def to_string_end(self) -> str:
        # docstring inherited
        return 'End If'

    def resolvable(self) -> bool:
        # docstring inherited
        return True


class EventScope(Scope):
    """
    Used for events:

    * IF Event blocks
    * :code:`<<~s~>>` in file paths

    See :class:`EventVariableScope <pytuflow.tmf.EventVariableScope>` for define blocks in TEF files.
    """

    def to_string_start(self) -> str:
        # docstring inherited
        return 'If Event == {0}'.format(' | '.join(self.name))

    def to_string_end(self) -> str:
        # docstring inherited
        return 'End If'

    def resolvable(self) -> bool:
        # docstring inherited
        return True


class EventVariableScope(Scope):
    """
    Used for event variables:

    * DEFINE blocks in TEF files

    Different from IF logic and :code:`<<~e~>>` in file paths, those are more
    similar to scenario scopes. This is more similar to user defined variable scopes except
    more difficult to recognise as they don't necessarily follow any pattern.
    """

    def to_string_start(self) -> str:
        # docstring inherited
        return 'Define Event == {0}'.format(self.name[0])

    def to_string_end(self) -> str:
        # docstring inherited
        return 'End Define'

    def supports_else_if(self) -> bool:
        # docstring inherited
        return False

    def resolvable(self) -> bool:
        # docstring inherited
        return True


class OneDimScope(Scope):
    """
    Used for 1D blocks found in TCF files:

    ::

        Start 1D Domain
        ...
        End 1D Domain

    """

    def to_string_start(self) -> str:
        # docstring inherited
        return 'Start 1D Domain'

    def to_string_end(self) -> str:
        # docstring inherited
        return 'End 1D Domain'

    def supports_else_if(self) -> bool:
        # docstring inherited
        return False


class OutputZoneScope(Scope):
    """
    Used for map output zones found in TCF files:

    ::

        Define Map Output Zone == ZoneA
        ...
        End Define

    """

    def to_string_start(self) -> str:
        # docstring inherited
        return 'Define Map Output Zone'

    def to_string_end(self) -> str:
        # docstring inherited
        return 'End Define'

    def supports_else_if(self) -> bool:
        # docstring inherited
        return False


class ControlScope(Scope):
    """TOC file blocks."""

    def to_string_start(self) -> str:
        # docstring inherited
        # TODO
        pass

    def to_string_end(self) -> str:
        # docstring inherited
        # TODO
        pass


class VariableScope(Scope):
    """
    User defined variables

    * :code:`Set Variable CELL_SIZE == 1`

    These variables can be used in a lot of different places.
    e.g. filenames or as values in control file commands.
    """

    def resolvable(self) -> bool:
        # docstring inherited
        return True
