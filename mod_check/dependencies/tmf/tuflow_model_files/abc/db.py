import typing
from abc import abstractmethod
from typing import Union

import pandas as pd

from ..dataclasses.inputs import Inputs
from ..dataclasses.types import PathLike


class Database:
    """Abstract base class for database objects e.g. bc_dbase, materials, soil etc."""

    def __getitem__(self, item):
        if self._df is not None:
            try:
                i = [x.lower() for x in self._df.index].index(item.lower())
            except Exception as e:
                i = -1
            if i == -1:
                raise KeyError('Item {0} not found in database'.format(item))
            return self._df.iloc[i]

    def __contains__(self, item):
        if self._df is not None:
            if isinstance(item, str):
                return item.lower() in [x.lower() for x in self._df.index]
            else:
                return item in self._df.index
        return False

    def df(self) -> pd.DataFrame:
        """Returns the database as a DataFrame.

        Returns
        -------
        pd.DataFrame
            The database as a DataFrame.
        """
        return self._df

    def index_to_file(self, index: Union[str, int]) -> list[PathLike]:
        """Returns files associated with the given database index/key. e.g. a boundary name may return the associated
        source file.

        Parameters
        ----------
        index : str | int
            The index/key within the database (e.g. boundary name, material ID).

        Returns
        -------
        list[PathLike]
            A list of file paths associated with the given index.
        """
        return self._index_to_file.get(index, [])

    def gis_inputs(self, recursive: bool = True) -> Inputs:
        """Here so that parent classes can call these on all child classes without type checking. Typically, this won't
        return anything. The only exception is the AD Global Database (not implemented yet) that can contain
        a GIS initial condition

        Parameters
        ----------
        recursive : bool, optional
            Whether to return inputs from child databases.

        Returns
        -------
        Inputs
            An Inputs object containing GIS inputs.
        """
        return Inputs([])

    def grid_inputs(self, recursive: bool = True) -> Inputs:
        """Here so that parent classes can call these on all child classes without type checking. Typically, this won't
        return anything.

        Parameters
        ----------
        recursive : bool, optional
            Whether to return inputs from child databases.

        Returns
        -------
        Inputs
            An Inputs object containing GIS inputs.
        """
        return Inputs([])

    def tin_inputs(self, recursive: bool = True) -> Inputs:
        """Here so that parent classes can call these on all child classes without type checking. Typically, this won't
        return anything.

        Parameters
        ----------
        recursive : bool, optional
            Whether to return inputs from child databases.

        Returns
        -------
        Inputs
            An Inputs object containing GIS inputs.
        """
        return Inputs([])

    def get_inputs(self, recursive: bool = True) -> Inputs:
        """Here so that parent classes can call these on all child classes without type checking.Typically, this won't
        return anything.

        Parameters
        ----------
        recursive : bool, optional
            Whether to return inputs from child databases.

        Returns
        -------
        Inputs
            An Inputs object containing GIS inputs.
        """
        return Inputs([])

    @abstractmethod
    def value(self, item: Union[str, int], *args, **kwargs) -> typing.Any:
        """Returns the value of the given item from the database.

        Parameters
        ----------
        item : str | int
            The item to get the value of.

        Returns
        -------
        Any
            The value of the item.
        """
