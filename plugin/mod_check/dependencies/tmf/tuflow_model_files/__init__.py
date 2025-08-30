# control files
from .cf.tcf import TCF
from .cf.tgc import TGC
from .cf.tbc import TBC
from .cf.ecf import ECF
from .cf.tef import TEF
from .cf.qcf import QCF
from .cf.adcf import ADCF
from .cf.tesf import TESF
from .cf.trd import TRD
from .cf.trfc import TRFC
from .cf.toc import TOC
from .cf.tscf import TSCF

# databases
from .db.bc_dbase import BCDatabase
from .db.mat import MatDatabase
from .db.pit_inlet import PitInletDatabase
from .db.rf import RainfallDatabase
from .db.soil import SoilDatabase
from .db.xs import CrossSectionDatabase
from .db.xs_run_state import CrossSectionRunState
from .db.drivers.xstf import TuflowCrossSection

# base classes
# from .abc.build_state import BuildState
# from .abc.run_state import RunState
# from .abc.cf import ControlFile
# from .abc.db import Database
# from .abc.input import Input
# from .abc.tcf_base import TCFBase
# from .cf.cf_build_state import ControlFileBuildState
# from .cf.cf_run_state import ControlFileRunState
# from .cf.cf_load_factory import ControlFileLoadMixin
# from .cf.tcf_build_state import TCFBuildState
# from .cf.tcf_run_state import TCFRunState
# from .db.db_build_state import DatabaseBuildState
# from .db.db_run_state import DatabaseRunState
# from .inp.inp_run_state import InputRunState

# inputs
from .inp.cf import ControlFileInput
from .inp.comment import CommentInput
from .inp.db import DatabaseInput
from .inp.file import FileInput
from .inp.gis import GisInput
from .inp.grid import GridInput
from .inp.tin import TinInput
from .inp.setting import SettingInput
from .inp.folder import FolderInput

# run state
from .cf.cf_run_state import ControlFileRunState
from .cf.tcf_run_state import TCFRunState
from .cf.tef_run_state import TEFRunState
from .db.db_run_state import DatabaseRunState
from .db.bc_dbase_run_state import BCDatabaseRunState
from .db.mat import MatDatabaseRunState
from .db.soil import SoilDatabaseRunState
from .db.xs_run_state import CrossSectionRunState
from .inp.inp_run_state import InputRunState
from .inp.gis import GisInputRunState

# misc / common
from .gis import GISAttributes, has_gdal, get_driver_name_from_extension
from .file import TuflowPath
from .misc.append_dict import AppendDict
from .scope import Scope
from .tuflow_binaries import tuflow_binaries, register_tuflow_binary, register_tuflow_binary_folder
from .const import short_tuflow_type
from .inp.altered_input import (AlteredInput, AlteredInputUpdatedValue, AlteredInputUpdatedCommand,
                                AlteredInputAddedInput, AlteredInputRemovedInput, AlteredInputSetScope,
                                AlteredInputs)
from .event import EventDatabase
# from .inp.inputs import Inputs
# from .scope import (ScopeList, Scope, GlobalScope, ScenarioScope, EventScope, EventDefineScope,
#                                                         OneDimScope, OutputZoneScope, ControlScope, VariableScope)
from .scope import Scope
# from .scope_writer import ScopeWriter
from .context import Context
# from .logging import WarningLog
# from .db.drivers.driver import DatabaseDriver
# from .db.drivers.csv import CsvDatabaseDriver
# from .db.drivers.xs import CrossSection, CrossSectionDatabaseDriver
# from .db.drivers.xsdat import FmCrossSection, FmCrossSectionDatabaseDriver
# from .db.drivers.xsdb import XsDatabaseDriver
# from .db.drivers.xsm11 import MikeCrossSectionDatabaseDriver
# from .db.drivers.xspro import ProCrossSectionDatabaseDriver
from .db.drivers.xstf import (TuflowCrossSection, UnresolvedAttributeError, TuflowCrossSectionHW, TuflowLossTable,
                              TuflowNATable, TuflowCrossSectionDatabaseDriver)
# from .utils.unpack_fixed_field import unpack_fixed_field
from .logging_ import set_logging_level, get_tmf_logger



# Setup default logging handlers for the API.
# If there is an existing logging configuration, no logger is configured, the
# calling code will override with its preferences
import logging
import sys


# Retrieve the "tmf" logger and check whether there are any existing logging handlers.
# If not, setup the default console StreamHandler with level set to WARNING
tmf_logger = logging.getLogger('tmf')
tmf_handler = None
if not tmf_logger.hasHandlers():
    tmf_handler = logging.StreamHandler()
    tmf_handler.setFormatter(logging.Formatter("%(asctime)s %(module)-30s line:%(lineno)-4d %(levelname)-8s %(message)s"))
    tmf_handler.setStream(sys.stdout)
    tmf_logger.setLevel(logging.WARNING)
    tmf_logger.addHandler(tmf_handler)
    tmf_logger.warning("Add a console logging handler to tmf logger. Use log_level keyword to change level")


# noinspection PyUnusedLocal
def disable_log_handler(log_name: str = 'tmf', handler: logging.Handler = tmf_handler) -> None:
    """Disable default log handler added to tmf_logger when the module is imported.
    
    Default kwargs are placeholders for possible future use, they are not used and
    have no impact on the behaviour of the function at the moment.
    """
    if tmf_logger.hasHandlers() and tmf_handler is not None:
        tmf_logger.removeHandler(tmf_handler)