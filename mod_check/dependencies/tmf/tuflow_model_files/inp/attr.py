from .file import FileInput
from .. import const


class AttrInput(FileInput):
    """Class for handling attribute files references within a vector file."""
    TUFLOW_TYPE = const.INPUT.ATTR

