import typing
from typing import TYPE_CHECKING
import json
from pathlib import Path

from .settings import get_cache_dir

if TYPE_CHECKING:
    from ..dataclasses.types import PathLike

from ..utils import logging as tmf_logging
logger = tmf_logging.get_tmf_logger()


class TuflowBinaries:
    """Class for managing TUFLOW binary versions and paths. A single instance of this class is created and used
    globally. This instance should be used rather than manually initialising this class.
    To access the instance, import the :data:`tuflow_binaries` variable:

    Examples
    --------
    >>> from pytuflow.util import tuflow_binaries
    >>> tuflow_binaries.get('2023-03-AE')
    'C:/TUFLOW/releases/2023-03-AE/TUFLOW_iSP_w64.exe'
    """

    def __init__(self):
        self._tuflow_version_json = self.tuflow_version_json()
        self._settings = self.load_tuflow_settings_cache()
        #: dict: Registered TUFLOW binaries {version name: path} - versions registered by the user only (not registered by folder)
        self.reg_version2bin = self.load_reg_tuflow_version_cache()
        #: list[Path]: Registered TUFLOW binary folders
        self.folders = self.load_reg_tuflow_folder_cache()
        #: dict: TUFLOW binaries {version name: path}
        self.version2bin = self.reg_version2bin.copy()

    def __repr__(self):
        return '<TuflowBinaries>'

    def __contains__(self, item):
        return item in self.version2bin

    def __getitem__(self, item):
        return self.version2bin[item]

    def get(self, item: str, default: typing.Any = None) -> str:
        return self.version2bin.get(item, default)

    @staticmethod
    def tuflow_version_json() -> Path:
        """Returns the path to the JSON file containing stored TUFLOW version info.

        Returns
        -------
        Path
            Path to the JSON file containing stored TUFLOW version info.
        """
        return Path(get_cache_dir()) / 'tuflow_versions.json'

    def load_tuflow_settings_cache(self) -> dict:
        """Load the TuflowVersions object from the JSON file.

        Returns
        -------
        dict
            The settings dictionary containing the registered TUFLOW binaries and folders.
        """
        if self._tuflow_version_json.exists():
            with self._tuflow_version_json.open() as fo:
                return json.load(fo)
        return {}

    def save_tuflow_settings_cache(self) -> None:
        """Saves the tuflow versions to the cache (JSON file)."""
        self._settings = {'bin': self.reg_version2bin, 'folders': self.folders}
        if not Path(get_cache_dir()).exists():
            Path(get_cache_dir()).mkdir(parents=True)
        with self._tuflow_version_json.open('w') as fo:
            json.dump(self._settings, fo, indent=4)

    def load_reg_tuflow_version_cache(self) -> dict:
        """Load the registered TUFLOW binary versions into its own dictionary.

        Returns
        -------
        dict
            The registered TUFLOW binaries.
        """
        if self._settings and 'bin' not in self._settings:
            self.convert_old_settings()
        return self._settings.get('bin', {})

    def load_reg_tuflow_folder_cache(self) -> list[Path]:
        """Load the registered TUFLOW binary folders into its own dictionary.

        Returns
        -------
        list[Path]
            The registered TUFLOW binary folders.
        """
        return self._settings.get('folders', [])

    def convert_old_settings(self) -> None:
        """Converts the old settings to the new settings. Only required for backwards compatibility to older versions
        of the cache file.
        """
        self.reg_version2bin = self._settings
        self.folders = []
        self.save_tuflow_settings_cache()

    def check_tuflow_folders(self) -> None:
        """Check the registered TUFLOW folders for new versions of TUFLOW binaries and update the
        version2bin dictionary.
        """
        self.version2bin = self.reg_version2bin.copy()
        for folder in self.folders:
            p = Path(folder)
            for f in p.glob('**/TUFLOW_iSP_w64*'):
                version = f.parent.stem
                if version not in self.reg_version2bin:
                    self.version2bin[version] = str(f)


#: TuflowBinaries: Global instance of the TuflowBinaries class. See :class:`TuflowBinaries` for class information.
tuflow_binaries = TuflowBinaries()


def register_tuflow_binary(version_name: str, version_path: 'PathLike') -> None:
    """Register (save) a TUFLOW binary version path. Versions saved via this method will take precedence over versions
    found in registered folders :func:`register_tuflow_binary_folder <pytuflow.util.register_tuflow_binary_folder>`.

    Parameters
    ----------
    version_name : str
        Name of the TUFLOW binary version e.g. '2023-03-AE'
    version_path : PathLike
        Path to the TUFLOW binary executable
    """
    tuflow_binaries.reg_version2bin[version_name] = str(version_path)
    tuflow_binaries.save_tuflow_settings_cache()
    logger.info('New TUFLOW binary registered: {} - {}'.format(version_name, version_path))


def register_tuflow_binary_folder(folder: 'PathLike') -> None:
    """Register a directory containing TUFLOW releases. The directory should contain subdirectories (folders)
    named after the TUFLOW version and each subdirectory should contain the TUFLOW binaries
    (i.e. no further subdirectories should be present). The directory names are used as the registered version
    name and the available binaries are refreshed each time a TUFLOW binary is requested (i.e. a simulation is run).

    It is best if this directory is a local directory and not a network drive. Binaries registered via
    :func:`register_tuflow_binary <pytuflow.util.register_tuflow_binary>` are given priority over
    binaries found using this method.

    Parameters
    ----------
    folder : PathLike
        Directory containing TUFLOW binaries
    """
    if folder not in tuflow_binaries.folders:
        tuflow_binaries.folders.append(folder)
        logger.info('New TUFLOW binary folder registered: {}'.format(folder))
        tuflow_binaries.save_tuflow_settings_cache()
