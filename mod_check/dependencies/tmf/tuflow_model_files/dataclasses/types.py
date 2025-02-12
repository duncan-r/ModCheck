import typing
from pathlib import Path
from typing import Union
import re

if typing.TYPE_CHECKING:
    from tmf.tuflow_model_files.abc.cf import ControlFile
    from tmf.tuflow_model_files.abc.db import Database


PathLike = Union[str, bytes, Path]
# Type hint for a context like object that can be passed into the Context class to initialise it
ContextLike = Union[list[str], tuple[str, ...], dict[str, str]]
# Type hint for a variable map that can be passed into a Context object
VariableMap = dict[str, str]


SearchTagListItem = Union[tuple[str, typing.Any], list[str, typing.Any]]
SearchTagList = Union[list[SearchTagListItem], tuple[SearchTagListItem, ...]]

# Type hint for a search tag list item used to filter inputs from a control file. Can be in the form of a :code:`str` or a tuple :code:`(str, typing.Any)` or a list of tuples :code:`[(str, typing.Any), ...]`.
SearchTagLike = Union[str, typing.Iterable[tuple[str, typing.Any]]]

#: ControlFile | Database: Type hint for a control file or database object.
ControlLike = Union['ControlFile', 'Database']


def is_a_number(value: any) -> bool:
    """Check if a value is a number or not."""
    try:
        float(value)
        b = True
    except ValueError:
        b = False
    return b


def is_a_number_or_var(value: typing.Any) -> bool:
    """
    Check if a value is a number including if the value is a variable reference to a number.

    This logic assumes that variables in TUFLOW are typically used in file paths or for a number value.
    e.g.
    Set Variable CELL_SIZE = 5
    Read GIS Code == ..\model\gis\2d_code_<<SCENARIO>>_001_R.shp

    It is very rare to use a variable for a string value in a setting, although could happen e.g.
    SGS == <<SGS_SWITCH>>  ! values ON or OFF
    In this case this routine would incorrectly flag this is a number value. It is up to the calling routine to check
    the context.
    """

    if is_a_number(value):
        return True
    if re.findall(r'<<.+?>>', value) and re.findall(r'<<.+?>>', value)[0] == value.strip():
        return True
    return False
