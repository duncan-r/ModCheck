from pathlib import Path
from typing import Union

from ...dataclasses.types import PathLike

from ...utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class DatabaseDriver:
    """Base class for database format drivers. This class is responsible for parsing different database formats
    e.g. CSV files.
    """

    __slots__ = ('path')

    def __new__(cls, fpath: PathLike) -> object:
        from .csv import CsvDatabaseDriver

        if not fpath:
            logger.error('DatabaseDriver must be initialised with a str or Path object')
            raise ValueError('DatabaseDriver must be initialised with a str or Path object')

        # csv database
        self = object.__new__(CsvDatabaseDriver)
        if self.test_is_self(fpath):
            return self

        logger.error('Drive initialisation failed: could not determine database type')
        raise ValueError('Could not determine database type')

    def __init__(self, fpath: PathLike) -> None:
        """Initialise the database driver with the file path.

        Parameters
        ----------
        fpath : PathLike
            The file path to the database file.
        """
        pass

    def test_is_self(self, path: PathLike) -> bool:
        """Test if the database driver looks like the correct driver for the file.

        Parameters
        ----------
        path : PathLike
            The file path to the database file.

        Returns
        -------
        bool
            True if the driver is the correct driver for the file, False otherwise.
        """
        logger.error('_test method must be implemented by driver class')
        raise NotImplementedError

    def name(self) -> str:
        """Return the name of the driver.

        Returns
        -------
        str
            The name of the driver.
        """
        logger.error('name method must be implemented by driver class')
        raise NotImplementedError

    def load(self, path: PathLike, header: int, index_col: Union[int, bool]) -> None:
        """Load the database file.

        Parameters
        ----------
        path : PathLike
            The file path to the database file.
        header : int
            The row number to use as the column names.
        index_col : Union[int, bool]
            The column to use as the row labels. If False, nothing is used.
        """
        logger.error('load method must be implemented by driver class')
        raise NotImplementedError
