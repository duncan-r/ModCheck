import typing

from ..abc.run_state import RunState
from ..abc.db import Database
from ..dataclasses.types import PathLike
from ..dataclasses.file import TuflowPath
from ..db.bc_dbase import BCDatabase

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class DatabaseRunState(RunState, Database):
    """Database class for run state."""

    def __repr__(self):
        if self.path:
            if self.path.exists():
                return '<{0}Context> {1}'.format(self.bs.__class__.__name__, self.path.name)
            return '<{0}Context> {1} (not found)'.format(self.bs.__class__.__name__, self.path.name)
        else:
            return '<DatabaseContext> (empty)'

    def value(self, index: str) -> typing.Any:
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
        if not self._loaded:
            raise ValueError('Database not loaded')
        if index not in self:
            raise KeyError(f'Item {index} not found in database')
        return BCDatabase.get_value(self.path, self._df, index)

    def get_files(self, recursive: bool = False) -> list[PathLike]:
        # docstring inherited
        if self._df is None:
            return []
        files = []
        for index in self._df.index:
            file = self._index_to_file.get(index)
            if file and file not in files:
                files.append(file)
        return files

    def _init(self) -> None:
        """Called after the generic initialisation.

        Sets a number of generic properties for the class.
        """

        self.path = self.bs.path
        self._loaded = self.bs._loaded
        if self.bs._df is not None:
            self._df = self.bs._df.copy()
        else:
            self._df = None
        self._driver = self.bs._driver
        self._index_to_file = {}

    def _resolve_scope_in_context(self) -> None:
        """Method called after all initialisation and resolves all inputs to
        remove variable names and unused inputs.
        """

        if not self._loaded:
            return

        for index, row in self._df.iterrows():
            new_row = [self.ctx.translate(x) for x in row]
            self._df.loc[index] = new_row
            if not self.bs._index_to_file.get(index):
                continue
            input_path = self.ctx.translate(self.path.parent / row.iloc[self.bs._source_index])
            self._index_to_file[index] = TuflowPath(input_path)
