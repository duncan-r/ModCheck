import typing

import pandas as pd

from ._db_build_state import DatabaseBuildState
from ..dataclasses.types import PathLike
from ..dataclasses.scope import ScopeList
from .. import const

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class MatDatabase(DatabaseBuildState):
    """Database class for material properties.

    Currently, the Database class has not implemented the :meth:`write() <pytuflow.tmf.DatabaseBuildState.write>`
    method, so it should be initialised with a :code:`fpath` to an existing database file as it can't be edited.
    """

    TUFLOW_TYPE = const.DB.MAT
    __slots__ = ('_source_index', '_header_index', '_index_col', '_tmf')

    def __init__(self, path: PathLike = None, scope: ScopeList = None, var_names: list[str] = ()) -> None:
        # docstring inherited
        if path and path.suffix.lower() == '.tmf':
            self._source_index = -1
            self._tmf = True
        else:
            self._source_index = 0
            self._tmf = False
        self._header_index = 0
        self._index_col = 0
        if path:
            try:
                with open(path, 'r') as f:
                    for i, line in enumerate(f):
                        data = line.split(',')
                        try:
                            int(data[0])
                            self._header_index = i - 1
                            break
                        except ValueError:
                            continue
                        except Exception:
                            continue
            except FileNotFoundError:
                logger.warning('Materials file not found at: {}'.format(path))
                pass
        super().__init__(path, scope, var_names)

    @staticmethod
    def get_value(db_path: PathLike, df: pd.DataFrame, index: str) -> typing.Any:
        # docstring inherited
        logger.error('Material database value method not implemented yet')
        NotImplementedError('Material database value method not implemented yet')
