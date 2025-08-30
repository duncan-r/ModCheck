import typing
from collections import OrderedDict

import pandas as pd

from .mat_db_entry import MatDBEntry
from .drivers.xstf import TuflowCrossSection
from .drivers.fm_unit_handler import Handler


class XSDBEntry(MatDBEntry):
    SOURCE_INDEX = 1

    def cross_section(self) -> pd.DataFrame:
        attrs = self.line.split(self.string)
        d = OrderedDict({
            'Source': attrs[1],
            'Type': attrs[2],
            'Flags': attrs[3] if attrs[3] not in [None, 'None'] else '',
            'Column_1': attrs[4] if attrs[4] not in [None, 'None'] else '',
            'Column_2': attrs[5] if attrs[5] not in [None, 'None'] else '',
            'Column_3': attrs[6] if attrs[6] not in [None, 'None'] else '',
            'Column_4': attrs[7] if attrs[7] not in [None, 'None'] else '',
            'Column_5': attrs[8] if attrs[8] not in [None, 'None'] else '',
            'Column_6': attrs[9] if attrs[9] not in [None, 'None'] else '',
        })
        xs = TuflowCrossSection(self.parent.fpath.parent, d)
        xs.load()
        return xs.df


class FMXSDBEntry:

    def __init__(self, index: str | typing.Hashable, unit: Handler):
        self._index = index
        self.unit = unit

    def __repr__(self):
        return f'<{self.__class__.__name__} index={self._index} values={self.unit}>'

    def cross_section(self) -> pd.DataFrame:
        return self.unit.df
