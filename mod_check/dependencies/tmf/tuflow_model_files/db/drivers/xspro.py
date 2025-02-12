from pathlib import Path
from typing import Union

from .xsdb import XsDatabaseDriver
from ...dataclasses.types import PathLike


class ProCrossSectionDatabaseDriver(XsDatabaseDriver):
    """ISIS Pro cross-section database driver.

    .. note::

        This driver is not implemented yet.
    """

    def __init__(self, fpath: PathLike) -> None:
        super().__init__(fpath)

    def test_is_self(self, path: PathLike) -> bool:
        # docstring inherited
        return Path(path).suffix.lower() == '.pro'

    def name(self) -> str:
        # docstring inherited
        return 'isis_pro_cross_section'

    def load(self, path: PathLike, *args, **kwargs):
        # docstring inherited
        # logging handled by caller
        raise NotImplementedError('ISIS ".pro" cross-section database not implemented yet')
