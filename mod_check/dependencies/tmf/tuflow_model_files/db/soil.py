import typing

import pandas as pd

from ._db_build_state import DatabaseBuildState
from ..dataclasses.types import PathLike
from ..dataclasses.scope import ScopeList
from .. import const

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class SoilDatabase(DatabaseBuildState):
    """Database class for soil properties.

    Currently, the Database class has not implemented the :meth:`write() <pytuflow.tmf.DatabaseBuildState.write>`
    method, so it should be initialised with a :code:`fpath` to an existing database file as it can't be edited.
    """

    TUFLOW_TYPE = const.DB.SOIL
    __slots__ = ('_source_index', '_header_index', '_index_col')

    def __init__(self, path: PathLike = None, scope: ScopeList = None, var_names: list[str] = ()) -> None:
        # docstring inherited
        self._source_index = -1
        self._header_index = 0
        self._index_col = 0
        super().__init__(path, scope, var_names)

    @staticmethod
    def get_value(db_path: PathLike, df: pd.DataFrame, index: str) -> typing.Any:
        # docstring inherited
        logger.error('Soil database value method not implemented yet')
        NotImplementedError('Soil database value method not implemented yet')
