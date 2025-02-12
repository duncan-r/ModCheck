from .file import FileInput
from .. import const


class DatabaseInput(FileInput):
    """Input class for database inputs.

    | e.g.
    | :code:`BC Database == bc_database.csv`
    | :code:`Read Materials File == materials.csv`
    """
    TUFLOW_TYPE = const.INPUT.DB

