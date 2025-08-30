import unittest
from pathlib import Path
from .test_function import TestFunction


TCF = Path(__file__).parent / r'./scenarios/TUFLOW/runs/test_scenarios.tcf'
TEMPLATE_FOLDER = TCF.parent.parent.parent / r'./templates'


class TestScenarios(unittest.TestCase):

    def test_scenarios_not_switched_on(self):
        test_folder_name = 'scenarios_not_on'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off', '-s', 'TEST',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios_nested', 'test_scenarios_in_fname',
                                                          'test_events', 'test_scenarios_nested_2',
                                                          'test_scenarios_nested_3', 'test_scenarios_2'])

    def test_no_scenarios(self):
        test_folder_name = 'no_scenarios'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off', '-use-scenarios',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios_nested', 'test_scenarios_in_fname', 'test_events',
                                                          '2d_po_EG02_010_P', '0d_rl_EG02_013_L', '0d_rl_EG02_013_P',
                                                          'test_scenarios_nested_2', 'test_scenarios_nested_3',
                                                          'test_scenarios_2'])

    def test_test_scenarios(self):
        test_folder_name = 'test'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off', '-use-scenarios', '-s1', 'TEST',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios_nested', 'test_scenarios_in_fname', 'test_events',
                                                          '0d_rl_EG02_013_P', 'test_scenarios_nested_2',
                                                          'test_scenarios_nested_3', 'test_scenarios_2'])

    def test_test2_scenarios(self):
        test_folder_name = 'test2'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-use-scenarios', '-s1', 'TEST_2', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios_nested', 'test_scenarios_in_fname',
                                                          'test_events', '2d_po_EG02_010_P', '0d_rl_EG02_013_P',
                                                          'test_scenarios_nested_2', 'test_scenarios_nested_3',
                                                          'test_scenarios_2'])

    def test_test3_scenarios(self):
        test_folder_name = 'test3'
        out_folder = TCF.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(TCF), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-use-scenarios', '-s1', 'TEST_3', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios_nested', 'test_scenarios_in_fname',
                                                          'test_events', '2d_po_EG02_010_P', '0d_rl_EG02_013_L',
                                                          'test_scenarios_nested_2', 'test_scenarios_nested_3',
                                                          'test_scenarios_2'])

    def test_test_scenarios_nested(self):
        tcf = Path(__file__).parent / r'./scenarios/TUFLOW/runs/test_scenarios_nested.tcf'
        test_folder_name = 'nested_test'
        out_folder = tcf.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-use-scenarios', '-s1', 'TEST', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios','test_scenarios_in_fname', 'test_events',
                                                          '2d_po_EG02_010_P', '0d_rl_EG02_013_P', '0d_rl_EG02_013_L',
                                                          'test_scenarios_nested_2', 'test_scenarios_nested_3',
                                                          'test_scenarios_2'])

    def test_test2_scenarios_nested(self):
        tcf = Path(__file__).parent / r'./scenarios/TUFLOW/runs/test_scenarios_nested.tcf'
        test_folder_name = 'nested_test2'
        out_folder = tcf.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-use-scenarios', '-s1', 'TEST_2', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios', 'test_scenarios_in_fname', 'test_events',
                                                          '2d_po_EG02_010_P', '0d_rl_EG02_013_P', '0d_rl_EG02_013_L',
                                                          'test_scenarios_nested_2', 'test_scenarios_nested_3',
                                                          'test_scenarios_2'])

    def test_test3_scenarios_nested(self):
        tcf = Path(__file__).parent / r'./scenarios/TUFLOW/runs/test_scenarios_nested.tcf'
        test_folder_name = 'nested_test3'
        out_folder = tcf.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-use-scenarios', '-s1', 'TEST', '-s2', 'TEST_2', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios', 'test_scenarios_in_fname', 'test_events',
                                                          '0d_rl_EG02_013_P', '0d_rl_EG02_013_L', 'test_scenarios_nested_2',
                                                          'test_scenarios_nested_3', 'test_scenarios_2'])

    def test_test4_scenarios_nested(self):
        tcf = Path(__file__).parent / r'./scenarios/TUFLOW/runs/test_scenarios_nested_2.tcf'
        test_folder_name = 'test_scenarios_nested_2'
        out_folder = tcf.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-use-scenarios', '-s1', 'SGS', '-s2', '10m', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios', 'test_scenarios_in_fname', 'test_events',
                                                          'test_scenarios_nested', '2d_po_EG02_010_P',
                                                          '2d_po_EG02_010_L', '0d_rl_EG02_013_P', '0d_rl_EG02_013_L',
                                                          'test_scenarios_nested_3', 'test_scenarios_2'])

    def test_test5_scenarios_nested(self):
        tcf = Path(__file__).parent / r'./scenarios/TUFLOW/runs/test_scenarios_nested_3.tcf'
        test_folder_name = 'test_scenarios_nested_3'
        out_folder = tcf.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-use-scenarios', '-s1', 'TEST', '-s2', 'TEST_3', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios', 'test_scenarios_in_fname', 'test_events',
                                                          'test_scenarios_nested', '2d_po_EG02_010_P',
                                                          '2d_po_EG02_010_L', '0d_rl_EG02_013_P', 'test_scenarios_nested_2',
                                                          'test_scenarios_2'])

    def test_scenarios_in_fname_no_scenarios(self):
        tcf = Path(__file__).parent / r'./scenarios/TUFLOW/runs/test_scenarios_in_fname.tcf'
        test_folder_name = 'fname_no_scenarios'
        out_folder = tcf.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-use-scenarios', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios', 'test_scenarios_nested', 'test_events',
                                                          '2d_po_EG02_010_P', '0d_rl_EG02_013_P', '0d_rl_EG02_013_L',
                                                          'test_scenarios_nested_2', 'test_scenarios_nested_3',
                                                          'test_scenarios_2'])

    def test_scenarios_in_fname_EG02(self):
        tcf = Path(__file__).parent / r'./scenarios/TUFLOW/runs/test_scenarios_in_fname.tcf'
        test_folder_name = 'fname_scenarios_EG02'
        out_folder = tcf.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-use-scenarios', '-s1', 'EG02', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios', 'test_scenarios_nested', 'test_events',
                                                          '0d_rl_EG02_013_P', '0d_rl_EG02_013_L', 'test_scenarios_nested_2',
                                                          'test_scenarios_nested_3', 'test_scenarios_2'])

    def test_event_also_works(self):
        tcf = Path(__file__).parent / r'./scenarios/TUFLOW/runs/test_events.tcf'
        test_folder_name = 'test_event'
        out_folder = tcf.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-use-scenarios', '-e1', 'TEST', '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios', 'test_scenarios_nested', 'test_scenarios_in_fname',
                                                          '0d_rl_EG02_013_P', 'test_scenarios_nested_2',
                                                          'test_scenarios_nested_3', 'test_scenarios_2'])

    def test_scenario_2(self):
        tcf = Path(__file__).parent / r'./scenarios/TUFLOW/runs/test_scenarios_2.tcf'
        test_folder_name = 'test_scenarios_2'
        out_folder = tcf.parent / test_folder_name
        template_dir = TEMPLATE_FOLDER / test_folder_name
        gis = 'gpkg'
        grid = 'tif'
        op = 'separate'
        args = ['-tcf', str(tcf), '-o', str(out_folder), '-gis', gis, '-grid', grid, '-op', op, '-verbose', 'off',
                '-always-use-root-dir']
        test = TestFunction()
        test.conversion_test(args, template_dir, exclude=['test_scenarios', 'test_scenarios_nested', 'test_scenarios_in_fname',
                                                          '0d_rl_EG02_013_P', 'test_scenarios_nested_2',
                                                          'test_scenarios_nested_3', 'test_events',
                                                          '2d_po_EG02_010_L', '2d_po_EG02_010_P', '0d_rl_EG02_013_L',
                                                          '0d_rl_EG02_013_P'])
