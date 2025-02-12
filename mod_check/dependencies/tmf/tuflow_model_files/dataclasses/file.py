from typing import Union
from pathlib import Path
from ...convert_tuflow_model_gis_format.conv_tf_gis_format.helpers.file import TuflowPath

PathType = Union[str, Path, TuflowPath, None]


def is_file_binary(path: PathType) -> bool:
    """
    Tests if a file is binary or not.

    Uses method from file(1) behaviour.
    https://github.com/file/file/blob/f2a6e7cb7db9b5fd86100403df6b2f830c7f22ba/src/encoding.c#L151-L228
    """

    textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7f})
    is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
    with open(path, 'rb') as f:
        return is_binary_string(f.read(1024))
