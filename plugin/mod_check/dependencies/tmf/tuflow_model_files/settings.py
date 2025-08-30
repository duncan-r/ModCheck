import typing
from pathlib import Path
from dataclasses import dataclass, field
import re
import platform

from .event import EventDatabase
from .file import TuflowPath
from .gis import GisFormat


def get_cache_dir() -> str:
    """Return the cache directory for this package."""
    return str(Path.home() / '.tuflow_model_files')


@dataclass
class TCFConfig:
    """Config class for parsing TUFLOW model files. Collects various settings from the TCF file in an initial
    pass of the TCF that can be passed into the TUFLOW model file parser e.g., variables, GIS projection, etc.

    This class also holds the current global settings defined in the TCF that can change depending on the cursor
    position in the TCF. An example of this is the spatial database which can be changed in the TCF which will
    affect the parsing of later control files.
    """
    tcf: str | Path | None = TuflowPath()
    control_file: Path = TuflowPath()
    spatial_database: Path = field(default_factory=TuflowPath, repr=False)
    spatial_database_tcf: Path = field(default_factory=TuflowPath, repr=False)
    projection_wkt: str = field(default='', repr=False)
    tif_projection: str = field(default='', repr=False)
    root_folder: Path = field(default_factory=TuflowPath, repr=False)
    output_folder: Path = field(default_factory=TuflowPath, repr=False)
    output_zones: list = field(default_factory=list, repr=False)
    wildcards: list = field(default_factory=list, repr=False)
    variables: dict | typing.Callable[[str], str] = field(default_factory=dict)
    scenarios: list = field(default_factory=list)
    event_db: EventDatabase = field(default_factory=EventDatabase)
    errors: bool = field(default=False, repr=False)
    warning: bool = field(default=False, repr=False)
    model_name: str = ''
    gis_format: GisFormat = GisFormat.MIF
    grid_format: GisFormat = GisFormat.TIF
    init_from_tcf: bool = field(default=True, repr=False)
    _event_text: str = field(default='', init=False, repr=False)
    _event_name: str = field(default='', init=False, repr=False)

    def __post_init__(self):
        if not self.wildcards:
            self.wildcards = [r'(<<.{1,}?>>)']
        self.tcf = TuflowPath(self.tcf) if self.tcf else TuflowPath()  # ensure tcf is a TuflowPath object
        if self.tcf != TuflowPath() and self.init_from_tcf:
            self.model_name = self.get_model_name(self.tcf)
            self.read_tcf()

    def __bool__(self):
        return self.tcf != Path()

    @staticmethod
    def from_tcf_config(config: 'TCFConfig') -> 'TCFConfig':
        """Create a new TCFConfig object from an existing one."""
        return TCFConfig(
            tcf=config.tcf,
            control_file=config.control_file,
            spatial_database=config.spatial_database,
            spatial_database_tcf=config.spatial_database_tcf,
            projection_wkt=config.projection_wkt,
            tif_projection=config.tif_projection,
            root_folder=config.root_folder,
            output_folder=config.output_folder,
            output_zones=config.output_zones,
            wildcards=config.wildcards,
            variables=config.variables,
            scenarios=config.scenarios,
            event_db=config.event_db,
            model_name=config.model_name,
            gis_format=config.gis_format,
            grid_format=config.grid_format,
            init_from_tcf=False
        )

    @staticmethod
    def get_model_name(tcf):
        """Extract the model name from the tcf minus all the wildcards."""
        p1 = r'[_\s]?~[es]\d?~'
        p2 = r'~[es]\d?~[_\s]?'
        m1 = re.sub(p1, '', tcf.name, flags=re.IGNORECASE)
        m2 = re.sub(p2, '', tcf.name, flags=re.IGNORECASE)
        if m1.count('_') != m2.count('_'):
            model_name = m1 if m1.count('_') > m2.count('_') else m2
        else:
            model_name = m1

        if model_name[-1] == '_':
            model_name = model_name[:-1]

        return str(Path(model_name).with_suffix(''))

    def read_tcf(self):
        """Routine to make an initial read of the TCF to extract some settings."""
        from .inp.event import EventInput
        from .parsers.command import EventCommand
        self.control_file = self.tcf

        # first pass - find variable definitions
        self.read_file_for_variables(self.control_file)
        self.set_spatial_database(None)  # reset spatial database to None

        # second pass - find event database
        self.read_file_for_event_db(self.control_file)
        if self._event_name and self._event_text:
            inp = EventInput(None, EventCommand(f'BC Event Source == {self._event_text} | {self._event_name}', self))
            self.event_db.inputs.append(inp)
        self.set_spatial_database(None)

        # third pass - find other information
        self.read_file_for_config(self.control_file)
        self.set_spatial_database(None)  # reset spatial database to None

        tcf_override = self.tuflow_override(self.tcf)
        if tcf_override:
            tcf, self.tcf = self.tcf, tcf_override
            self.read_tcf()
            self.set_spatial_database(None)  # reset spatial database to None
            self.tcf = tcf

    def read_file_for_variables(self, control_file: Path):
        """Search for variable definitions in the TCF and any read files that are called in the TCF."""
        from .parsers.non_recursive_basic_parser import get_commands
        for command in get_commands(control_file, self):
            if command.is_read_file() and not command.in_scenario_block():
                self.read_file_for_variables(self.control_file.parent / command.value)
            elif command.is_set_variable() and not command.in_scenario_block():
                var_name, var_val = command.parse_variable()
                self.variables[var_name] = var_val

    def read_file_for_event_db(self, control_file: Path):
        from .parsers.non_recursive_basic_parser import get_commands
        from .parsers.command import EventCommand
        from .cf.tef import TEF
        from .inp.event import EventInput
        for command in get_commands(control_file, self):
            if command.is_read_file() and not command.in_scenario_block():
                self.read_file_for_event_db(self.control_file.parent / command.value)
            elif command.is_event_file():
                event_file = self.control_file.parent / command.value
                self.event_db.update(TEF.parse_event_file(event_file, self))
            elif command.is_event_source():
                event_command = EventCommand.from_command(command)
                inp = EventInput(None, event_command)
                self.event_db.inputs.append(inp)
                if inp.event_name:
                    if inp.event_name not in self.event_db:
                        self.event_db[inp.event_name] = {inp.event_var: inp.event_value}
                    else:
                        self.event_db[inp.event_name][inp.event_var] = inp.event_value
            elif command.is_bc_event_name():
                self._event_name = command.value
            elif command.is_bc_event_text():
                self._event_text = command.value

    def set_spatial_database(self, value: str | Path | None):
        value = str(value)
        if value.upper() == 'TCF':
            self.spatial_database = self.spatial_database_tcf
        elif value.upper() == 'NONE':
            self.spatial_database = TuflowPath()
            self.spatial_database_tcf = TuflowPath()
        else:
            self.spatial_database = self.control_file.parent / value

        if self.control_file.suffix.upper() == '.TCF':
            self.spatial_database_tcf = self.spatial_database

    @staticmethod
    def tuflow_override(tcf: Path) -> Path | None:
        if tcf.stem.lower().startswith('_tuflow_override'):
            return None
        comp_name = platform.node()
        tcf_override = tcf.parent / f'_TUFLOW_Override_{comp_name}.tcf'
        if tcf_override.exists():
            return tcf_override
        tcf_override = tcf.parent / f'_TUFLOW_Override.tcf'
        if tcf_override.exists():
            return tcf_override
        return None

    def read_file_for_config(self, control_file: Path):
        from .parsers.command import EventCommand
        from .parsers.non_recursive_basic_parser import get_commands
        from .gis import ogr_projection, gdal_projection, GisFormat

        gis_format = {'GPKG': GisFormat.GPKG, 'SHP': GisFormat.SHP, 'ASC': GisFormat.ASC,
                      'TIF': GisFormat.TIF, 'FLT': GisFormat.FLT, 'NC': GisFormat.NC,
                      'MIF': GisFormat.MIF}
        for command in get_commands(control_file, self):
            event_command = EventCommand(command.original_text, self)
            # spatial database
            if command.is_spatial_database_command():
                self.set_spatial_database(command.value)
            # projection
            elif command.is_read_projection():
                try:
                    self.projection_wkt = ogr_projection(command.value_expanded_path)
                except (ImportError, FileNotFoundError, RuntimeError):
                    continue
            # tif projection
            elif command.is_tif_projection():
                try:
                    self.tif_projection = gdal_projection(command.value_expanded_path)
                except (ImportError, FileNotFoundError, RuntimeError):
                    continue
            # gis format
            elif command.is_gis_format():
                self.gis_format = gis_format.get(command.value.upper(), GisFormat.Unknown)
            # grid format
            elif command.is_grid_format():
                self.grid_format = gis_format.get(command.value.upper(), GisFormat.Unknown)
            # event source
            elif event_command.is_event_source():
                event_wildcard, _ = event_command.get_event_source()
                if event_wildcard is not None and re.escape(event_wildcard) not in self.wildcards:
                    self.wildcards.append(re.escape(event_wildcard))
            # output zones
            elif command.is_output_zone():
                self.output_zones.extend(command.specified_output_zones())
            # read file / event file
            elif command.is_read_file() or command.is_event_file():
                self.read_file_for_config(self.control_file.parent / command.value)
