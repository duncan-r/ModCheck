from pathlib import Path

import pandas as pd

from .xs import CrossSection
from .xsdb import XsDatabaseDriver
from .river_unit_handler import RiverUnit
from .dat import Dat
from ...dataclasses.types import PathLike


class FmCrossSection(RiverUnit, CrossSection):

    def __init__(self, *args, **kwargs) -> None:
        super(FmCrossSection, self).__init__(*args, **kwargs)
        self.type = 'RIVER'
        self.col_name_x = 'x'
        self.col_name_z = 'y'
        self.col_name_n = 'n'

    def __repr__(self) -> str:
        if self.name:
            return f'<DatCrossSection {self.name}>'
        return '<DatCrossSection>'

    @property
    def name(self) -> str:
        return self.id

    @name.setter
    def name(self, value: str) -> None:
        self.id = value


class FmCrossSectionDatabaseDriver(XsDatabaseDriver):
    """Flood Modeller DAT cross-section database driver."""

    def __init__(self, fpath: PathLike) -> None:
        """
        Parameters
        ----------
        fpath : PathLike
            The file path to the DAT file.
        """
        super().__init__(fpath)
        self.dat = Dat(fpath)
        self.dat.add_handler(FmCrossSection)

    def __repr__(self):
        if self.path:
            return f'<FmCrossSectionDatabaseDriver {self.path.stem}>'
        return '<FmCrossSectionDatabaseDriver>'

    def test_is_self(self, path: PathLike) -> bool:
        # docstring inherited
        return Path(path).suffix.lower() == '.dat'

    def name(self) -> str:
        # docstring inherited
        return 'dat_cross_section'

    def load(self, path: PathLike, *args, **kwargs) -> pd.DataFrame:
        """Load the DAT file.

        Parameters
        ----------
        path : PathLike
            The file path to the DAT file.

        Returns
        -------
        pd.DataFrame
            The cross-section data as a DataFrame.
        """
        self.dat.load()
        for xs in self.dat.units(FmCrossSection):
            self.cross_sections[xs.id] = xs
            self.name2id[xs.id] = xs.id
        return self.generate_df()
