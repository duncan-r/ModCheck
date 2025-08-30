from .grid import GridInput
from .. import const, logging_ as tmf_logging

logger = tmf_logging.get_tmf_logger()


class TinInput(GridInput):
    """Class for handling TIN inputs.

    This class can handle the following scenarios:

    * reading multiple files on a single line: the first file is assumed to be a tin file, the second is
      a vector file.
    """
    TUFLOW_TYPE = const.INPUT.TIN
