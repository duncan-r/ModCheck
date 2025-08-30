from .stubs import ogr
from .gis import ogr_format_2_ext, ogr_create, GIS_MIF, GIS_GPKG, GIS_SHP, get_database_name
from .settings import MinorConvertException
from .file import TuflowPath


class TuflowEmptyType:

    def __init__(self, name, geom, gis_format, projection_wkt):
        self.name = name
        self.geom = geom
        self.gis_format = gis_format
        self.projection_wkt = projection_wkt

    def count(self):
        return len(self.geom)

    def get_schema(self):
        return EmptySchemas.get_schema(self.name)

    def write_empty(self, dir_path, settings):
        schema = self.get_schema()
        if schema is None:
            raise MinorConvertException(f'Error: schema not found for {self.name}_empty')

        if 'pts' in self.name:
            table_name = f'{self.name[:-4]}_empty_pts'
        else:
            table_name = f'{self.name}_empty'
        if self.gis_format == GIS_MIF:
            uris = [(f'{dir_path / table_name}{ogr_format_2_ext(self.gis_format)} >> {table_name}', self.geom[0])]
        elif self.gis_format == GIS_GPKG:
            uris = []
            for g in self.geom:
                uris.append((f'{dir_path / table_name}{ogr_format_2_ext(self.gis_format)} >> {table_name}_{g}', g))
        else:
            uris = []
            for g in self.geom:
                uris.append((f'{dir_path / table_name}_{g}{ogr_format_2_ext(self.gis_format)} >> {table_name}_{g}', g))

        for uri, geom in uris:
            if settings.verbose == 'high':
                if self.gis_format in [GIS_MIF, GIS_SHP]:
                    print(f'... Creating {TuflowPath(get_database_name(uri)[0]).name}')
                else:
                    print(f'... Creating {TuflowPath(uri).name}')
            ogr_create(uri, f'_{geom}', schema, self.projection_wkt, settings)


class TuflowEmptyFiles:

    def __init__(self, gis_format, projection_wkt):
        self.empty_types = [
            TuflowEmptyType('1d_nd', 'P', gis_format, projection_wkt),
            TuflowEmptyType('1d_nwk', 'PL', gis_format, projection_wkt),
            TuflowEmptyType('1d_nwke', 'PL', gis_format, projection_wkt),
            TuflowEmptyType('1d_nwkb', 'PL', gis_format, projection_wkt),
            TuflowEmptyType('1d_mh', 'P', gis_format, projection_wkt),
            TuflowEmptyType('1d_bc', 'PR', gis_format, projection_wkt),
            TuflowEmptyType('1d_iwl', 'P', gis_format, projection_wkt),
            TuflowEmptyType('1d_tab', 'PL', gis_format, projection_wkt),
            TuflowEmptyType('1d_xs', 'L', gis_format, projection_wkt),
            TuflowEmptyType('1d_na', 'P', gis_format, projection_wkt),
            TuflowEmptyType('1d_WLL', 'LR', gis_format, projection_wkt),
            TuflowEmptyType('1d_pit', 'P', gis_format, projection_wkt),
            TuflowEmptyType('2d_po', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_lp', 'L', gis_format, projection_wkt),
            TuflowEmptyType('2d_fc', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_glo', 'P', gis_format, projection_wkt),
            TuflowEmptyType('2d_bc', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_code', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_mat', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_sa', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_rf', 'PR', gis_format, projection_wkt),
            TuflowEmptyType('2d_sa_rf', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_sa_tr', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_z__', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_zsh', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_zshr', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_ztin', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_vzsh', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_fcsh', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_lfcsh', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_lfcsh_pts', 'P', gis_format, projection_wkt),
            TuflowEmptyType('2d_iwl', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_loc', 'LR', gis_format, projection_wkt),
            TuflowEmptyType('2d_oz', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_soil', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_gw', 'R', gis_format, projection_wkt),
            TuflowEmptyType('0d_rl', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_at', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_qnl', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_cwf', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_flc', 'R', gis_format, projection_wkt),
            TuflowEmptyType('2d_obj', 'PR', gis_format, projection_wkt),
            TuflowEmptyType('2d_rec', 'PR', gis_format, projection_wkt),
            TuflowEmptyType('2d_wrf', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_bg', 'PLR', gis_format, projection_wkt),
            TuflowEmptyType('2d_bg_pts', 'P', gis_format, projection_wkt),
            TuflowEmptyType('swmm_iu', 'P', gis_format, projection_wkt),
        ]

    def write_empties(self, dir_path, settings):
        if settings.verbose == 'high':
            print('Writing Empty Files... [{0}]'.format(dir_path))
        for empty_type in self.empty_types:
            try:
                empty_type.write_empty(dir_path, settings)
            except MinorConvertException as e:
                continue
            except Exception as e:
                settings.error = True
                print(f'Error: Unexpected error writing empty file {empty_type.name}_empty: {e}')

    @staticmethod
    def empty_count():
        count = 0
        self = TuflowEmptyFiles(None, None)
        for empty_type in self.empty_types:
            count += empty_type.count()

        return count


class Schema:

    def __init__(self, name, type_, width=None, prec=None):
        self.name = name
        self.type = type_
        self.width = width
        self.prec = prec


class EmptySchemas:

    @staticmethod
    def get_schema(name):
        if hasattr(EmptySchemas, f'_{name}'):
            return eval(f'EmptySchemas._{name}()')

    @staticmethod
    def _1d_nwk():
        return [
            Schema('ID', ogr.OFTString, 36),
            Schema('Type', ogr.OFTString, 8),
            Schema('Ignore', ogr.OFTString, 1),
            Schema('UCS', ogr.OFTString, 1),
            Schema('Len_or_ANA', ogr.OFTReal, 15, 5),
            Schema('n_nF_Cd', ogr.OFTReal, 15, 5),
            Schema('US_Invert', ogr.OFTReal, 15, 5),
            Schema('DS_Invert', ogr.OFTReal, 15, 5),
            Schema('Form_Loss', ogr.OFTReal, 15, 5),
            Schema('pBlockage', ogr.OFTReal, 15, 5),
            Schema('Inlet_Type', ogr.OFTString, 12),
            Schema('Conn_1D_2D', ogr.OFTString, 4),
            Schema('Conn_No', ogr.OFTInteger, 8),
            Schema('Width_or_Dia', ogr.OFTReal, 15, 5),
            Schema('Height_or_WF', ogr.OFTReal, 15, 5),
            Schema('Number_of', ogr.OFTInteger, 8),
            Schema('HConF_or_WC', ogr.OFTReal, 15, 5),
            Schema('WConF_or_WEx', ogr.OFTReal, 15, 5),
            Schema('EntryC_or_WSa', ogr.OFTReal, 15, 5),
            Schema('ExitC_or_WSb', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _1d_nwke():
        schema = EmptySchemas._1d_nwk()
        schema.extend([
            Schema('eS1', ogr.OFTString, 50),
            Schema('eS2', ogr.OFTString, 50),
            Schema('eN1', ogr.OFTReal, 15, 5),
            Schema('eN2', ogr.OFTReal, 15, 5),
            Schema('eN3', ogr.OFTReal, 15, 5),
            Schema('eN4', ogr.OFTReal, 15, 5),
            Schema('eN5', ogr.OFTReal, 15, 5),
            Schema('eN6', ogr.OFTReal, 15, 5),
            Schema('eN7', ogr.OFTReal, 15, 5),
            Schema('eN8', ogr.OFTReal, 15, 5),
        ])
        return schema

    @staticmethod
    def _1d_nwkb():
        schema = EmptySchemas._1d_nwk()
        schema[9] = Schema('pBlockage', ogr.OFTString, 12)
        return schema

    @staticmethod
    def _1d_nd():
        return [
            Schema('ID', ogr.OFTString, 36),
            Schema('Type', ogr.OFTString, 8),
            Schema('Ignore', ogr.OFTString, 1),
            Schema('Bed_Level', ogr.OFTReal, 15, 5),
            Schema('ANA', ogr.OFTReal, 15, 5),
            Schema('Conn_1D_2D', ogr.OFTString, 4),
            Schema('Conn_Width', ogr.OFTReal, 15, 5),
            Schema('R1', ogr.OFTReal, 15, 5),
            Schema('R2', ogr.OFTReal, 15, 5),
            Schema('R3', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _1d_mh():
        return [
            Schema('ID', ogr.OFTString, 36),
            Schema('Type', ogr.OFTString, 8),
            Schema('Loss_Approach', ogr.OFTString, 4),
            Schema('Ignore', ogr.OFTString, 1),
            Schema('Invert_Level', ogr.OFTReal, 15, 5),
            Schema('Flow_Width', ogr.OFTReal, 15, 5),
            Schema('Flow_Length', ogr.OFTReal, 15, 5),
            Schema('ANA', ogr.OFTReal, 15, 5),
            Schema('K_Fixed', ogr.OFTReal, 15, 5),
            Schema('Km', ogr.OFTReal, 15, 5),
            Schema('K_Bend_Max', ogr.OFTReal, 15, 5),
            Schema('C_reserved', ogr.OFTString, 12),
            Schema('N1_reserved', ogr.OFTReal, 15, 5),
            Schema('N2_reserved', ogr.OFTReal, 15, 5),
            Schema('N3_reserved', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _1d_bc():
        return [
            Schema('Type', ogr.OFTString, 2),
            Schema('Flags', ogr.OFTString, 6),
            Schema('Name', ogr.OFTString, 50),
            Schema('Description', ogr.OFTString, 250),
        ]

    @staticmethod
    def _1d_tab():
        return [
            Schema('Source', ogr.OFTString, 50),
            Schema('Type', ogr.OFTString, 2),
            Schema('Flags', ogr.OFTString, 8),
            Schema('Column_1', ogr.OFTString, 20),
            Schema('Column_2', ogr.OFTString, 20),
            Schema('Column_3', ogr.OFTString, 20),
            Schema('Column_4', ogr.OFTString, 20),
            Schema('Column_5', ogr.OFTString, 20),
            Schema('Column_6', ogr.OFTString, 20),
            Schema('Z_Increment', ogr.OFTReal, 15, 5),
            Schema('Z_Maximum', ogr.OFTReal, 15, 5),
            Schema('Skew', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _1d_xs():
        return EmptySchemas._1d_tab()

    @staticmethod
    def _1d_na():
        return [
            Schema('Source', ogr.OFTString, 50),
            Schema('Type', ogr.OFTString, 2),
            Schema('Flags', ogr.OFTString, 8),
            Schema('Column_1', ogr.OFTString, 20),
            Schema('Column_2', ogr.OFTString, 20),
            Schema('not_used_6', ogr.OFTString, 20),
            Schema('not_used_7', ogr.OFTString, 20),
            Schema('not_used_8', ogr.OFTString, 20),
            Schema('not_used_9', ogr.OFTString, 20),
            Schema('not_used_10', ogr.OFTReal, 15, 5),
            Schema('not_used_11', ogr.OFTReal, 15, 5),
            Schema('not_used_12', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _1d_WLL():
        return [
            Schema('Dist_for_Add_Points', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _1d_iwl():
        return [
            Schema('IWL', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _1d_pit():
        return [
            Schema('ID', ogr.OFTString, 12),
            Schema('Type', ogr.OFTString, 4),
            Schema('VP_Network_ID', ogr.OFTInteger, 8),
            Schema('Inlet_Type', ogr.OFTString, 32),
            Schema('VP_Sur_Index', ogr.OFTReal, 15, 5),
            Schema('VP_QMax', ogr.OFTReal, 15, 5),
            Schema('Width', ogr.OFTReal, 15, 5),
            Schema('Conn_2D', ogr.OFTString, 8),
            Schema('Conn_No', ogr.OFTInteger, 8),
            Schema('pBlockage', ogr.OFTReal, 15, 5),
            Schema('Number_of', ogr.OFTInteger, 8),
        ]

    @staticmethod
    def _2d_po():
        return [
            Schema('Type', ogr.OFTString, 20),
            Schema('Label', ogr.OFTString, 30),
            Schema('Comment', ogr.OFTString, 250),
        ]

    @staticmethod
    def _2d_lp():
        return EmptySchemas._2d_po()

    @staticmethod
    def _2d_loc():
        return [
            Schema('Comment', ogr.OFTString, 250),
        ]

    @staticmethod
    def _2d_code():
        return [
            Schema('Code', ogr.OFTInteger, 8),
        ]

    @staticmethod
    def _2d_mat():
        return [
            Schema('Material', ogr.OFTInteger, 8),
        ]

    @staticmethod
    def _2d_z__():
        return [
            Schema('Elevation', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_zsh():
        return [
            Schema('Z', ogr.OFTReal, 15, 5),
            Schema('dZ', ogr.OFTReal, 15, 5),
            Schema('Shape_Width_or_dMax', ogr.OFTReal, 15, 5),
            Schema('Shape_Options', ogr.OFTString, 20),
        ]

    @staticmethod
    def _2d_zshr():
        schema = EmptySchemas._2d_zsh()
        schema.extend([
            Schema('Route_Name', ogr.OFTString, 40),
            Schema('Cut_Off_Type', ogr.OFTString, 40),
            Schema('Cut_Off_Values', ogr.OFTString, 80),
        ])
        return schema

    @staticmethod
    def _2d_ztin():
        return [
            Schema('Z', ogr.OFTReal, 15, 5),
            Schema('dZ', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_vzsh():
        schema = EmptySchemas._2d_zsh()
        schema.extend([
            Schema('Trigger_1', ogr.OFTString, 20),
            Schema('Trigger_2', ogr.OFTString, 20),
            Schema('Trigger_Value', ogr.OFTReal, 15, 5),
            Schema('Period', ogr.OFTReal, 15, 5),
            Schema('Restore_Interval', ogr.OFTReal, 15, 5),
            Schema('Restore_Period', ogr.OFTReal, 15, 5),
        ])
        return schema

    @staticmethod
    def _2d_fcsh():
        return [
            Schema('Invert', ogr.OFTReal, 15, 5),
            Schema('Obvert_or_BC_Height', ogr.OFTReal, 15, 5),
            Schema('Shape_Width_or_dMax', ogr.OFTReal, 15, 5),
            Schema('Shape_Options', ogr.OFTString, 20),
            Schema('FC_Type', ogr.OFTString, 2),
            Schema('pBlockage', ogr.OFTReal, 15, 5),
            Schema('FLC_or_FLCpm_below_Obv', ogr.OFTReal, 15, 5),
            Schema('FLC_or_FLCpm_above_Obv', ogr.OFTReal, 15, 5),
            Schema('Mannings_n', ogr.OFTReal, 15, 5),
            Schema('BC_Width', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_lfcsh():
        return [
            Schema('Invert', ogr.OFTReal, 15, 5),
            Schema('dZ', ogr.OFTReal, 15, 5),
            Schema('Shape_Width_or_dMax', ogr.OFTReal, 15, 5),
            Schema('Shape_Options', ogr.OFTString, 20),
            Schema('L1_Obvert', ogr.OFTReal, 15, 5),
            Schema('L1_pBlockage', ogr.OFTReal, 15, 5),
            Schema('L1_FLC', ogr.OFTReal, 15, 5),
            Schema('L2_Depth', ogr.OFTReal, 15, 5),
            Schema('L2_pBlockage', ogr.OFTReal, 15, 5),
            Schema('L2_or_L23_FLC', ogr.OFTReal, 15, 5),
            Schema('L3_Depth', ogr.OFTReal, 15, 5),
            Schema('L3_pBlockage', ogr.OFTReal, 15, 5),
            Schema('L3_FLC_or_fIP', ogr.OFTReal, 15, 5),
            Schema('Notes', ogr.OFTString, 40),
        ]

    @staticmethod
    def _2d_lfcsh_pts():
        schema = EmptySchemas._2d_lfcsh()
        schema.pop(13)
        schema.pop(12)
        schema.pop(11)
        schema.pop(9)
        schema.pop(8)
        schema.pop(6)
        schema.pop(5)
        schema.pop(3)
        schema.pop(2)
        schema.pop(1)
        return schema

    @staticmethod
    def _2d_bg():
        return [
            Schema('ID', ogr.OFTString, 32),
            Schema('Options', ogr.OFTString, 32),
            Schema('Pier_pBlockage', ogr.OFTReal, 15, 5),
            Schema('Pier_FLC', ogr.OFTReal, 15, 5),
            Schema('Deck_Soffit', ogr.OFTReal, 15, 5),
            Schema('Deck_Depth', ogr.OFTReal, 15, 5),
            Schema('Deck_width', ogr.OFTReal, 15, 5),
            Schema('Deck_pBlockage', ogr.OFTReal, 15, 5),
            Schema('Rail_Depth', ogr.OFTReal, 15, 5),
            Schema('Rail_pBlockage', ogr.OFTReal, 15, 5),
            Schema('SuperS_FLC', ogr.OFTReal, 15, 5),
            Schema('SuperS_IPf', ogr.OFTReal, 15, 5),
            Schema('Notes', ogr.OFTString, 64),
        ]

    @staticmethod
    def _2d_bg_pts():
        return [
            Schema('Deck_Soffit', ogr.OFTReal, 15, 5),
            Schema('Deck_Depth', ogr.OFTReal, 15, 5),
            Schema('Rail_Depth', ogr.OFTReal, 15, 5),
            Schema('R1', ogr.OFTReal, 15, 5),
            Schema('R2', ogr.OFTReal, 15, 5),
            Schema('R3', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_iwl():
        return [
            Schema('IWL', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_fc():
        return [
            Schema('Type', ogr.OFTString, 2),
            Schema('Invert', ogr.OFTReal, 15, 5),
            Schema('Obvert_or_BC_height', ogr.OFTReal, 15, 5),
            Schema('u_width_factor', ogr.OFTReal, 15, 5),
            Schema('v_width_factor', ogr.OFTReal, 15, 5),
            Schema('Add_form_loss', ogr.OFTReal, 15, 5),
            Schema('Mannings_n', ogr.OFTReal, 15, 5),
            Schema('No_walls_or_neg_width', ogr.OFTReal, 15, 5),
            Schema('Blocked_sides', ogr.OFTString, 10),
            Schema('Invert_2', ogr.OFTString, 10),
            Schema('Obvert_2', ogr.OFTString, 10),
            Schema('Comment', ogr.OFTString, 250),
        ]

    @staticmethod
    def _2d_glo():
        return [
            Schema('Datafile', ogr.OFTString, 254),
            Schema('Bottom_Elevation', ogr.OFTReal, 15, 5),
            Schema('Top_Elevation', ogr.OFTReal, 15, 5),
            Schema('Increment', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_bc():
        return [
            Schema('Type', ogr.OFTString, 2),
            Schema('Flags', ogr.OFTString, 3),
            Schema('Name', ogr.OFTString, 100),
            Schema('f', ogr.OFTReal, 15, 5),
            Schema('d', ogr.OFTReal, 15, 5),
            Schema('td', ogr.OFTReal, 15, 5),
            Schema('a', ogr.OFTReal, 15, 5),
            Schema('b', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_sa():
        return [
            Schema('Name', ogr.OFTString, 100),
        ]

    @staticmethod
    def _2d_sa_rf():
        schema = EmptySchemas._2d_sa()
        schema.extend([
            Schema('Catchment_Area', ogr.OFTReal, 15, 5),
            Schema('Rain_Gauge_Factor', ogr.OFTReal, 15, 5),
            Schema('IL', ogr.OFTReal, 15, 5),
            Schema('CL', ogr.OFTReal, 15, 5),
        ])
        return schema

    @staticmethod
    def _2d_sa_tr():
        schema = EmptySchemas._2d_sa()
        schema.extend([
            Schema('Trigger_Type', ogr.OFTString, 40),
            Schema('Trigger_Location', ogr.OFTString, 40),
            Schema('Trigger_Value', ogr.OFTReal, 15, 5),
        ])
        return schema

    @staticmethod
    def _2d_rf():
        return [
            Schema('Name', ogr.OFTString, 100),
            Schema('f1', ogr.OFTReal, 15, 5),
            Schema('f2', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_oz():
        return [
            Schema('Not_Used', ogr.OFTString, 20),
        ]

    @staticmethod
    def _2d_soil():
        return [
            Schema('SoilID', ogr.OFTInteger, 8),
        ]

    @staticmethod
    def _2d_gw():
        return [
            Schema('Groundwater', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _0d_rl():
        return [
            Schema('Name', ogr.OFTString, 32),
        ]

    @staticmethod
    def _2d_at():
        return [
            Schema('AT', ogr.OFTInteger, 8),
        ]

    @staticmethod
    def _2d_qnl():
        return [
            Schema('Nest_Level', ogr.OFTInteger, 8),
        ]

    @staticmethod
    def _2d_cwf():
        return [
            Schema('CWF', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_flc():
        return [
            Schema('FLC', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_obj():
        return [
            Schema('Trigger_Level', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _2d_rec():
        return EmptySchemas._2d_obj()

    @staticmethod
    def _2d_wrf():
        return [
            Schema('WrF', ogr.OFTReal, 15, 5),
        ]

    @staticmethod
    def _swmm_iu():
        return [
            Schema('Inlet', ogr.OFTString, 50),
            Schema('StreetXSEC', ogr.OFTString, 50),
            Schema('Elevation', ogr.OFTReal, 15, 5),
            Schema('SlopePct_Longitudinal', ogr.OFTReal, 15, 5),
            Schema('Number', ogr.OFTInteger, 8),
            Schema('CloggedPct', ogr.OFTReal, 15, 5),
            Schema('Qmax', ogr.OFTReal, 15, 5),
            Schema('aLocal', ogr.OFTReal, 15, 5),
            Schema('wLocal', ogr.OFTReal, 15, 5),
            Schema('Placement', ogr.OFTString, 10),
            Schema('Conn1D_2D', ogr.OFTString, 10),
            Schema('Conn_Width', ogr.OFTReal, 15, 5),
        ]

