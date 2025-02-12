from typing import Union
import pandas as pd
from pandas.errors import ParserError

from .driver import DatabaseDriver
from ...dataclasses.file import PathType, TuflowPath, is_file_binary
from ...utils.text_to_db_parser import text_to_db_parser

from ...utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class CsvDatabaseDriver(DatabaseDriver):
    """Driver for CSV database files. This class is responsible for parsing CSV files."""

    __slots__ = ()

    def __repr__(self):
        return '<CSVDatabaseDriver>'

    def test_is_self(self, path: PathType) -> bool:
        # docstring inherited
        if '|' in str(path):  # most likely FEWS type
            return False

        path = TuflowPath(path)
        if not path.exists():
            return path.suffix.lower() == '.csv'

        if path.suffix.lower() == '.csv':
            return True

        if path.suffix.lower() in ['.ts1', '.dss', '.out', '.loc', '.tot']:
            return False

        if is_file_binary(path):
            return False

        # basic check to see if it is comma delimited or tab delimited (it should be comma)
        with path.open() as f:
            while True:
                line = f.readline()
                if not line:
                    return False
                if not line.strip():
                    continue
                if len(line.split(',')) == 1 and len(line.split('\t')) > 1:
                    return False
                return True

        return False

    def name(self) -> str:
        # docstring inherited
        return 'csv'

    def load(self, path: PathType, header, index_col: Union[int, bool]):
        # docstring inherited
        if header is None or isinstance(header, int) or \
                (isinstance(header, list) and (header and isinstance(header[0], int) or not header)):
            header_row = header
        elif isinstance(header, str) or (isinstance(header, list) and header and isinstance(header[0], str)):
            with open(path, 'r') as f:
                for i, line in enumerate(f):
                    data = [x.strip() for x in line.split(',')]
                    found = True
                    if isinstance(header, list):
                        for h in header:
                            if h.strip() not in data:
                                found = False
                        if found:
                            header_row = i
                            break
                    elif header.strip() in data:
                        header_row = i
                        break
        try:
            return pd.read_csv(path, index_col=index_col, header=header_row, encoding_errors='ignore', comment='!')
        except ParserError:
            # file must be a little nasty - have to do it manually :(
            try:
                return text_to_db_parser(path)
            except Exception as e:
                logger.error('Failed to parse CVS file at: {}'.format(path))
                raise ParserError(f'Failed to parse CSV file {path}')
