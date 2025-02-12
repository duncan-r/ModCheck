import typing

import pandas as pd

from .drivers.xstf import TuflowCrossSectionDatabaseDriver
from .drivers.xsdb import XsDatabaseDriver
from ..dataclasses.scope import ScopeList, Scope
from ..dataclasses.types import PathLike
from ..db._db_build_state import DatabaseBuildState
from ..utils.patterns import expand_and_get_files
from .. import const

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class CrossSectionDatabase(DatabaseBuildState):
    """Database class for storing cross-sections.

    Currently, the Database class has not implemented the :meth:`write() <pytuflow.tmf.DatabaseBuildState.write>`
    method, so it should be initialised with a :code:`fpath` to an existing database file as it can't be edited.
    """
    TUFLOW_TYPE = const.DB.XS

    def __init__(self, path: PathLike = None, scope: ScopeList = None, var_names: list[str] = ()) -> None:
        # docstring inherited
        self._header_index = -1  # dummy value to indicate it has been set, otherwise error will be raised
        self._index_col = -1  # dummy value to indicate it has been set, otherwise error will be raised
        driver = None
        if TuflowCrossSectionDatabaseDriver(path).test_is_self(path):
            driver = TuflowCrossSectionDatabaseDriver(path)
        elif XsDatabaseDriver(path).test_is_self(path):  # database for mike (.txt) and FM (.dat or .pro - what the hell is .pro?)
            driver = XsDatabaseDriver(path)
        super().__init__(path, scope, var_names, driver)

    def value(self, item: str) -> typing.Any:
        """Returns the value of the given index.

        Parameters
        ----------
        index : str
            The index/key within the database.

        Returns
        -------
        Any
            The value of the given index.
        """
        if not self._driver:
            return
        id_ = self._driver.name2id.get(item)
        if id_ is None:
            return
        return self._driver.cross_sections[id_]

    def names(self) -> list[str]:
        """Returns the names of all the cross-sections in the database.

        Returns
        -------
        list[str]
            The names of all the cross-sections in the database.
        """
        if not self._driver:
            return []
        return list(self._driver.name2id.keys())

    def figure_out_file_scopes(self, scopes: ScopeList) -> None:
        # docstring inherited
        for xsid in self._driver.unresolved_xs:
            xs = self._driver.cross_sections[xsid]
            for f in self._index_to_file[xs.id]:
                source = {x.lower(): y for x, y in xs.attrs.items()}.get('source')
                Scope.resolve_scope(self._file_to_scope[str(f)], str((self.path.parent / source).resolve()), str(f), scopes)

    def _init_scope(self):
        """Overrides the parent method."""
        for xs in self._driver.cross_sections.values():
            if xs.id in self._driver.unresolved_xs:
                scopes = ScopeList()
                for value in xs.attrs.values():
                    if value:
                        for scope in Scope.from_string(str(value), str(value), event_var=self._var_names):
                            if scope not in scopes and scope != Scope('GLOBAL'):
                                scopes.append(scope)
                self._index_to_scopes[xs.id] = scopes
            else:
                self._index_to_scopes[xs.id] = []

    def _get_files(self):
        """Overrides the parent method."""
        for xs in self._driver.cross_sections.values():
            if xs.id in self._driver.unresolved_xs:
                self._index_to_file[xs.id] = expand_and_get_files(self.path.parent, xs.source)
            else:
                self._index_to_file[xs.id] = [xs.fpath]

    def _file_scopes(self):
        """Overrides the parent method."""
        if not self._driver.supports_separate_files:
            return
        for xs in self._driver.cross_sections.values():
            for f in self.index_to_file(xs.id):
                string = str(self.path.parent / {x.lower(): y for x, y in xs.attrs.items()}.get('source'))
                self._file_to_scope[str(f)] = Scope.from_string(string, str(f), self._var_names)

    @staticmethod
    def get_value(db_path: PathLike, df: pd.DataFrame, index: str) -> typing.Any:
        # docstring inherited
        logger.error('Cross-section database value method not implemented yet')
        NotImplementedError('Cross-section database value method not implemented yet')
