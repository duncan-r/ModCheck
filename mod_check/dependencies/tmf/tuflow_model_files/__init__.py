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

# base classes
from .abc.build_state import BuildState
from .abc.run_state import RunState
from .abc.cf import ControlFile
from .abc.db import Database
from .abc.input import Input
from .abc.tcf_base import TCFBase
from .cf._cf_build_state import ControlFileBuildState
from .cf._cf_run_state import ControlFileRunState
from .cf._cf_load_factory import ControlFileLoadMixin
from .cf.tcf_build_state import TCFBuildState
from .cf.tcf_run_state import TCFRunState
from .db._db_build_state import DatabaseBuildState
from .db._db_run_state import DatabaseRunState
from .inp._inp_build_state import InputBuildState
from .inp._inp_run_state import InputRunState
from .utils.commands import Command
from .utils.settings import Settings

# inputs
from .inp.attr import AttrInput
from .inp.cf import ControlFileInput
from .inp.comment import CommentInput
from .inp.db import DatabaseInput
from .inp.file import FileInput
from .inp.gis import GisInput, GisInput_
from .inp.grid import GridInput
from .inp.tin import TinInput
from .inp.setting import SettingInput

# misc / common
from .dataclasses.scope import Scope
from .utils.tuflow_binaries import tuflow_binaries, register_tuflow_binary, register_tuflow_binary_folder
from .const import short_tuflow_type
from .dataclasses.altered_input import (AlteredInput, AlteredInputUpdatedValue, AlteredInputUpdatedCommand,
                                        AlteredInputAddedInput, AlteredInputRemovedInput, AlteredInputSetScope,
                                        AlteredInputs)
from .dataclasses.event import EventDatabase, Event
from .dataclasses.inputs import Inputs
from .dataclasses.scope import (ScopeList, Scope, GlobalScope, ScenarioScope, EventScope, EventVariableScope,
                                OneDimScope, OutputZoneScope, ControlScope, VariableScope)
from .utils.scope_writer import ScopeWriter
from .utils.context import Context
from .utils.logging import WarningLog
from .db.drivers.driver import DatabaseDriver
from .db.drivers.csv import CsvDatabaseDriver
from .db.drivers.xs import CrossSection, CrossSectionDatabaseDriver
from .db.drivers.xsdat import FmCrossSection, FmCrossSectionDatabaseDriver
from .db.drivers.xsdb import XsDatabaseDriver
from .db.drivers.xsm11 import MikeCrossSectionDatabaseDriver
from .db.drivers.xspro import ProCrossSectionDatabaseDriver
from .db.drivers.xstf import (TuflowCrossSection, UnresolvedAttributeError, TuflowCrossSectionHW, TuflowLossTable,
                              TuflowNATable, TuflowCrossSectionDatabaseDriver)
from .utils.settings import Settings
from .utils.commands import Command
from .utils.unpack_fixed_field import unpack_fixed_field
from .utils.scope_writer import ScopeWriter
from .utils.logging import set_logging_level, get_tmf_logger



# Setup default logging handlers for the API.
# If there is an existing logging configuration, no logger is configured, the
# calling code will override with its preferences
import logging
import sys


# Retrieve the "tmf" logger and check whether there are any existing logging handlers.
# If not, setup the default console StreamHandler with level set to WARNING
tmf_logger = logging.getLogger('tmf')
tmf_handler = None
if tmf_logger.hasHandlers() is False:
    tmf_handler = logging.StreamHandler()
    tmf_handler.setFormatter(logging.Formatter("%(asctime)s %(module)-30s line:%(lineno)-4d %(levelname)-8s %(message)s"))
    tmf_handler.setStream(sys.stdout)
    tmf_logger.setLevel(logging.WARNING)
    tmf_logger.addHandler(tmf_handler)
    tmf_logger.warning("Add a console logging handler to tmf logger. Use log_level keyword to change level")


def disable_log_handler(log_name: str = 'tmf', handler: logging.Handler = tmf_handler) -> None:
    """Disable default log handler added to tmf_logger when the module is imported.
    
    Default kwargs are placeholders for possible future use, they are not used and
    have no impact on the behaviour of the function at the moment.
    """
    if tmf_logger.hasHandlers() and tmf_handler is not None:
        tmf_logger.removeHandler(tmf_handler)