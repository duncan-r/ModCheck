from ...convert_tuflow_model_gis_format.conv_tf_gis_format.helpers.settings import ConvertSettings as Settings
from ...convert_tuflow_model_gis_format.conv_tf_gis_format.helpers.settings import MinorConvertException
from pathlib import Path


def get_cache_dir() -> str:
    """Return the cache directory for this package."""
    return str(Path.home() / '.tuflow_model_files')
