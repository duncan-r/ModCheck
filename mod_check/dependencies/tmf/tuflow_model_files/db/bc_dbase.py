import typing

import pandas as pd

from ._db_build_state import DatabaseBuildState
from .drivers.driver import DatabaseDriver
from ..dataclasses.types import PathLike, is_a_number
from ..dataclasses.file import TuflowPath
from ..dataclasses.scope import ScopeList
from .. import const

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


SOURCE_INDEX = 0
TIME_INDEX = 1
VALUE_INDEX = 2


class BCDatabase(DatabaseBuildState):
    """Database class for boundary conditions.

    Currently, the Database class has not implemented the :meth:`write() <pytuflow.tmf.DatabaseBuildState.write>`
    method, so it should be initialised with a :code:`fpath` to an existing database file as it can't be edited.
    """

    TUFLOW_TYPE = const.DB.BC_DBASE
    __slots__ = ('_source_index', '_header_index', '_index_col')

    def __init__(self, fpath: PathLike = None, scope: ScopeList = None, var_names: list[str] = (),
                 driver: DatabaseDriver = None) -> None:
        # docstring inherited
        self._source_index = SOURCE_INDEX
        self._header_index = 0
        self._index_col = 0
        super().__init__(fpath, scope, var_names)

    @staticmethod
    def get_value(db_path: PathLike, df: pd.DataFrame, index: str) -> typing.Any:
        # docstring inherited
        try:
            i = [x.lower() for x in df.index].index(index.lower())
        except Exception:
            i = -1
        if i == -1:
            logger.error('Item {0} was not found in bc database'.format(index))
            raise KeyError('Item {0} was not found in database'.format(index))
        row = df.iloc[i]
        if is_a_number(row.iloc[VALUE_INDEX]):
            return float(row.iloc[VALUE_INDEX])

        db_path = TuflowPath(db_path)
        source = db_path.parent / row.iloc[SOURCE_INDEX]
        if not source.exists():
            logger.error('Source file referenced by bcdatabase could not be found at: {}'.format(source))
            raise FileNotFoundError(f'Could not find source file {source}')

        driver = DatabaseDriver(source)
        if driver is None:
            logger.error('File format not implemented yet: {0}'.format(source.name))
            raise NotImplementedError('File format not implemented yet: {0}'.format(source.name))
        source_df = driver.load(source, header=row[1:3].tolist(), index_col=False)
        return source_df[row[1:3]]
