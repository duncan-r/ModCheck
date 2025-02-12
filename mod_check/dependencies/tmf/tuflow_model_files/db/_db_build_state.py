import itertools
import re
import typing
from typing import TYPE_CHECKING, Union
import numpy as np
import pandas as pd

from ..dataclasses.inputs import Inputs
from ..db.drivers.driver import DatabaseDriver
from ..utils.context import Context
from ..dataclasses.file import TuflowPath
from ..dataclasses.scope import Scope, GlobalScope, ScopeList
from ..dataclasses.types import is_a_number, PathLike
from ..dataclasses.event import EventDatabase
from ..abc.build_state import BuildState
from ..abc.db import Database
from ..utils.patterns import globify
from .. import const


if TYPE_CHECKING:
    from ..inp._inp_build_state import InputBuildState

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class DatabaseBuildState(BuildState, Database):
    """Abstract class for storing database information when the model is in the build state."""

    TUFLOW_TYPE = const.DB.DATABASE
    __slots__ = ('path', '_loaded', '_df', '_driver', '_index_to_file', '_index_to_scopes',
                 '_file_to_scope')

    def __init__(self, fpath: PathLike = None, scope: ScopeList = None, var_names: list[str] = (),
                 driver: DatabaseDriver = None) -> None:
        """Initialises the database build state.

        Parameters
        ----------
        fpath : PathLike, optional
            Path to the database file.
        scope : ScopeList, optional
            A list of scope objects that will be inherited by the control file itself. Not currently used
            but reserved in case this is useful information in the future.
        var_names : list[str], optional
            A list of variable names that are used to identify variables in the database. This is used to
            help identify event variable names which do not have to follow the TUFLOW pattern for calling
            variables (i.e. << >>)
        driver : DatabaseDriver, optional
            A driver object that can be used to load the database file. If not provided, the driver
            will be guessed based on file extension and content.
        """
        self._scope = scope
        self._var_names = [r'(<<.{1,}?>>)']
        self._var_names.extend([re.escape(x) for x in var_names if x not in self._var_names])
        #: TuflowPath: Path to the database file.
        self.path = TuflowPath(fpath) if fpath is not None else None
        self._df = None
        self._index_to_file = {}
        self._index_to_scopes = {}
        self._file_to_scope = {}
        #: bool: Whether the database has been altered since it was last written
        self.dirty = False
        if driver:
            self._driver = driver
        elif self.path:
            self._driver = DatabaseDriver(fpath)
        else:
            self._driver = None
        if fpath:
            try:
                self.load(fpath)
                self._loaded = True
                logger.info('Database file loaded at: {}'.format(fpath))
            except FileNotFoundError:
                self._loaded = False
                logger.warning('Database file could not be found at: {}'.format(fpath))
        else:
            self._loaded = False

    def __repr__(self):
        if self.path:
            if self._loaded:
                return '<{0}> {1}'.format(self.__class__.__name__, self.path.name)
            else:
                return '<{0}> {1} (not found)'.format(self.__class__.__name__, self.path.name)
        else:
            return '<{0}> (empty)'.format(self.__class__.__name__)

    def load(self, path: PathLike) -> None:
        """Loads database from path. Child subclasses should override this method and assign "_head_index" and "_index_col"
        properties before calling this method.

        Parameters
        ----------
        path : PathLike
            PathLike - Path to the database file.
        """

        if not hasattr(self, '_header_index') or not hasattr(self, '_index_col'):
            raise NotImplementedError

        if not TuflowPath(path).exists():
            logger.warning('Database file could not be loaded at: {}'.format(path))
            raise FileNotFoundError

        if not self._driver:
            self.path = path
            self._driver = DatabaseDriver(path)

        self._df = self._driver.load(path, self._header_index, self._index_col)
        self._init_scope()
        self._get_files()
        self._file_scopes()
        self._loaded = True

    def load_variables(self, var_names: list[str]) -> None:
        """Allows loading of variables (e.g. Event Variables) after initialisation.
        This method will also automatically update the file scopes.

        This routine is useful for the BC_Dbase as the event variables may not be known at initialisation.

        Parameters
        ----------
        var_names : list[str]
            A list of variable names that are used to identify variables in the database. This is used to
            help identify event variable names which do not have to follow the TUFLOW pattern for calling
            variables (i.e. << >>)
        """

        for v in var_names:
            if re.escape(v) not in self._var_names:
                self._var_names.append(re.escape(v))
        if self.path is None:
            return
        self._index_to_file = {}
        self._index_to_scopes = {}
        self._file_to_scope = {}
        self._init_scope()
        self._get_files()
        self._file_scopes()

    def figure_out_file_scopes(self, scopes: ScopeList) -> None:
        """Overrides the abstract method in BuildState.

        Try and resolve unknown scope variable values based on a known scope list.

        Parameters
        ----------
        scopes : ScopeList
            A list of known scopes that can be used to resolve unknown scopes.
        """
        if not hasattr(self, '_source_index'):
            logger.error('Database class has not implemented the _source_index attr')
            raise NotImplementedError
        if self._df is None or self._source_index < 0:
            return

        for index, row in self._df.iterrows():
            for f in self._index_to_file[index]:
                Scope.resolve_scope(self._file_to_scope[str(f)], str(self.path.parent / row.iloc[self._source_index]), str(f), scopes)

    def file_scope(self, file: PathLike) -> list[Scope]:
        """Public function that will return the scope of a given file based on the loaded variables.

        Parameters
        ----------
        file : PathLike
            Path to the file to get the scope of.

        Returns
        -------
        list[Scope]
            List of Scope objects that represent the scope of the file.
        """
        return self._file_to_scope.get(str(file), [])

    def value(self, item: str, **kwargs) -> Union[any, dict[str, any]]:
        """Returns a DatabaseValue from the database based on an index. A database value can be a scalar or a dataframe.

        Multiple values can be returned by passing in keyword arguments listing the events/scenarios to return
        Valid keyword arguments:

        |    - "event_db": EventDatabase object - most likely required for bc_dbase to resolve event variables.
        |    - "event_groups": dict of event groups .e.g. {'e1': ['Q50', 'Q100'], 'e2': ['1hr', '2hr']}
        |    - "scenario_groups": dict of scenario groups e.g. {'s1': ['D01', 'D02'], 's2': ['5m', '10m']}
        |    - "variables": dict of variables names with either with their values
        |            - e.g. {'WATER_LEVEL': 10}
        |            or with a list of input objects that contain their scope if more than one value is possible
        |            - e.g  {'WATER_LEVEL': Inputs(input1, input2,... )} where inputs is a list of
        |            inputs that contain scope
        |                input1.scope = Scope('SCENARIO', 'D01')
        |                input2.scope = Scope('SCENARIO', 'D02')

        The order of event and scenario groups above doesn't really matter (unlike with the run state).

        For multiple events/scenarios the return object will be a dictionary of returned values. The key will be
        the combination of event/scenario names. For single returns, the return type will be a DatabaseValue.

        .. note::
            ES Note:
                I think this function can be improved to make it a little more simple. I also think if multiple events
                are returned, we should find a way to return them in a single DataFrame rather than a dictionary.

        Parameters
        ----------
        item : str
            The index to return the value for.

        Returns
        -------
        typing.Any
        """

        if item not in self:
            logger.error(f'Item {item} not found in database')
            raise KeyError(f'Item {item} not found in database')

        unrecog_kwarg = [x for x in kwargs.keys() if x not in ['event_db', 'event_groups', 'scenario_groups', 'variables']]
        if unrecog_kwarg:
            logger.error('Unrecognised keyword argument for method: {}'.format(unrecog_kwarg[0]))
            raise AttributeError(f'Unrecognised keyword argument for method: {unrecog_kwarg[0]}')

        if 'event_db' in kwargs or 'event_groups' in kwargs or 'scenario_groups' in kwargs or 'variables' in kwargs:
            return self._value_from_event_map(item, **kwargs)  # allows for multiple events to be returned from database
        else:  # try and get value using an empty context
            ctx = self.context()
            return self.get_value(self.path, ctx.df(), item)

    def get_files(self, *args, **kwargs) -> list[PathLike]:
        """Returns a list of files associated with this database.

        Returns
        -------
        list[PathLike]
            List of files associated with the database.
        """
        if self._df is None:
            return []
        files = []
        for index in self._df.index:
            for file in self.index_to_file(index):
                if file not in files:
                    files.append(file)
        return files

    def write(self, fpath: PathLike) -> None:
        """Writes the database to a file.

        Parameters
        ----------
        fpath : PathLike
            Path to write the database to.
        """
        pass

    def _init_scope(self):
        """
        Defines the scope of the database entries.

        Scope is determined by any variable names in the database entries or their values. BC_Dbase may miss
        some scope objects as event variables are completely user defined and don't necessarily follow
        a pattern so it isn't possible to recognise them.
        """

        for index, row in self._df.iterrows():
            scopes = ScopeList()
            scopes.extend(Scope.from_string(str(index), str(index), event_var=self._var_names))
            for i, item in enumerate(row):
                if (isinstance(item, np.float64) or isinstance(item, float)) and np.isnan(item):
                    continue
                for scope in Scope.from_string(str(item), str(item), event_var=self._var_names):
                    if scope not in scopes:
                        scopes.append(scope)

            # remove duplicates
            scopes_ = []
            for scope in scopes:
                if scope not in scopes_:
                    scopes_.append(scope)
            scopes = scopes_

            # remove GLOBAL scope if it is not the only scope
            if [x for x in scopes if not isinstance(x, GlobalScope)]:
                self._index_to_scopes[index] = [x for x in scopes if not isinstance(x, GlobalScope)]
            else:
                self._index_to_scopes[index] = scopes

    def _get_files(self):
        """Called during the initialisation of this class and finds all possible files associated with each entry."""
        if not hasattr(self, '_source_index'):
            raise NotImplementedError

        self._index_to_file = {}
        if self._df is None or self._source_index < 0:
            return
        for index, row in self._df.iterrows():
            if (isinstance(row.iloc[self._source_index], np.float64) or isinstance(row.iloc[self._source_index], float)) and np.isnan(row.iloc[self._source_index]):
                continue
            pattern = globify(row.iloc[self._source_index], self._var_names)
            self._index_to_file[index] = [x for x in self.path.parent.glob(pattern)]
            if not self._index_to_file[index] and not is_a_number(row.iloc[self._source_index]):
                self._index_to_file[index] = [self.path.parent / row.iloc[self._source_index]]

    def _file_scopes(self):
        """
        Called after files are collected in the initialisation of this class and finds the scope of each file. The
        scope of the file is independent of the scope of the input i.e. a file with a 'GLOBAL' scope does not
        reflect that the input itself may be within an 'IF Scenario' block, it indicates that the file does
        not contain any variable names that could potentially be expanded to a different files.

        It will try and resolve the scope of the input by comparing the name to any existing files
        it finds that match the input name pattern.
        e.g.
        Read File == input_file_<<~s~>>.trd
        Existing files:
            - input_file_exg.trd
            - input_file_dev.trd
        File scopes:
            - input_file_exg.trd -> Scope = SCENARIO, name = exg, var = <<~s~>>
            - input_file_dev.trd -> Scope = SCENARIO, name = dev, var = <<~s~>>
        If the scope name can't be resolved then the scope name will be set to the variable name.
        If the there are no variables in the file name then a 'GLOBAL' scope will be assigned to the file.
        """

        if not hasattr(self, '_source_index'):
            logger.error('Database class has not implemented the _source_index attr')
            raise NotImplementedError

        if self._df is None:
            return

        for index, row in self._df.iterrows():
            for f in self.index_to_file(index):
                string = str(self.path.parent / str(row.iloc[self._source_index]))
                self._file_to_scope[str(f)] = Scope.from_string(string, str(f), self._var_names)

    def _value_from_event_map(self, item: str, **kwargs) -> dict[str, any]:
        """
        Returns a dictionary of values from a single index based on the keyword arguments.

        Valid keyword arguments:
            - "event_db": EventDatabase object - most likely required for bc_dbase to resolve event variables.
            - "event_groups": dict of event groups .e.g. {'e1': ['Q50', 'Q100'], 'e2': ['1hr', '2hr']}
            - "scenario_groups": dict of scenario groups e.g. {'s1': ['D01', 'D02'], 's2': ['5m', '10m']}
            - "variables": dict of variables names with either with their values
                    - e.g. {'WATER_LEVEL': 10}
                    or with a list of input objects that contain their scope if more than one value is possible
                    - e.g  {'WATER_LEVEL': Inputs(input1, input2,... )} where inputs is a list of
                        inputs that contain the scope property e.g.
                           input1.scope = Scope('SCENARIO', 'D01')
                           input2.scope = Scope('SCENARIO', 'D02')

        The order of event and scenario groups above doesn't really matter (unlike with the run state).
        """

        def group_name(id_: str, names: list[str], groups: dict[str, str]) -> str:
            """Short helper function to convert permutations of event/scenario names into s1... e1 based on order."""
            i = 0
            for x in names:
                if x in groups:
                    i += 1
                    yield f'{id_}{i}', x

        def create_key(index_scopes: ScopeList, ctx_dict: dict[str, str], event_db: EventDatabase,
                       var_scopes: dict[str, ScopeList], perm: list[str]):
            """
            Short(ish) helper function to create a key based on the input permutation
            (that worked in the function below) that only returns the name of the permutation
            items that were needed.
            """
            keys = []
            event_names = list(event_db.keys()) if event_db is not None else []
            var_scope_list = ScopeList()
            var_scopes_ = {k.lower(): v for k, v in var_scopes.items()}
            for scope in index_scopes:
                if scope == Scope('VARIABLE'):
                    scope_name = scope.name.strip('<>').lower()
                    if scope_name in var_scopes_:
                        var_scope_list.extend(var_scopes_[scope_name])
            for p in perm:
                group = [k for k, v in ctx_dict.items() if v.lower() == p.lower()][0]
                scope = None
                if group[0].lower() == 's':
                    scope = Scope('SCENARIO', p, var=f'<<~{group.lower()}~>>')
                elif group[0].lower() == 'e':
                    if p in event_names:
                        scope = Scope('EVENT VARIABLE', p, var=event_db[p].variable)
                if scope in index_scopes or scope in var_scope_list:
                    keys.append(p)
            return ' '.join(keys)

        all_groups = []
        all_groups.extend([x for x in kwargs.get('event_groups', {}).values()])
        event_to_group = {}
        for key, value in kwargs.get('event_groups', {}).items():
            for v in value:
                event_to_group[v] = key
        all_groups.extend([x for x in kwargs.get('scenario_groups', {}).values()])
        scen_to_group = {}
        for key, value in kwargs.get('scenario_groups', {}).items():
            for v in value:
                scen_to_group[v] = key
        var_map = kwargs.get('variables', {})
        event_db = kwargs.get('event_db', None)
        if event_db:
            self.load_variables([x.variable for x in event_db.values()])

        values = {}
        for comb in itertools.product(*all_groups):
            for perm in itertools.permutations(comb, len(comb)):
                ctx_dict = {grp_name: name_ for grp_name, name_ in group_name('S', perm, scen_to_group)}
                ctx_dict.update({grp_name: name_ for grp_name, name_ in group_name('E', perm, event_to_group)})
                ctx = Context(ctx_dict)
                d = {}
                req_var_scopes = {}
                for k, v in var_map.items():
                    if isinstance(v, Inputs):
                        for inp in v:
                            if ctx.in_context_by_scope(inp._scope):
                                var_name, var_val = inp.raw_command_obj().parse_variable()
                                d[var_name] = var_val
                                req_var_scopes[var_name] = inp._scope
                    else:
                        d[k] = v
                ctx.load_variables(d)
                if 'event_db' in kwargs:
                    ctx.load_events(kwargs.get('event_db'))
                db_ctx = self.context(context=ctx)
                try:
                    value = self.get_value(self.path, db_ctx.df(), item)
                    key = create_key(self._index_to_scopes[item], ctx_dict, event_db, req_var_scopes, perm)
                    if not key:
                        key = 0
                    if key not in values:
                        values[key] = value
                    break  # don't need to keep to keep trying permutations if we found the correct order
                except Exception as e:
                    continue

        return values

    @staticmethod
    def get_value(db_path: PathLike, df: pd.DataFrame, index: str) -> typing.Any:
        """Static abstract method that should be overridden by a child class.

        Requires database path, pandas dataframe of the database, and index to return value for.
        This routine should return a DatabaseValue object which can be a pandas dataframe or a scalar value.

        This is a static method so it can be called from the run state version of a database back to the build state
        version of the database.

        Parameters
        ----------
        db_path : PathLike
            Path to the database file.
        df : pd.DataFrame
            Pandas dataframe of the database.
        index : str
            Index to return the value for.

        Returns
        -------
        typing.Any
            Database value
        """
        logger.error('get_value method must be overriden by database class')
        raise NotImplementedError
