"""Focused geometry, solver/source, monitor, metrics, and pipeline tests."""

import csv
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import yaml

from src.experiments.experiment_config import (
    actual_plate_angle_deg,
    load_config,
    width_lambda_from_m,
    width_m_from_lambda,
)
from src.analysis.cst_comparison import compare_cst_exports
from src.analysis.analytical_model import calculate as calculate_analytical
from src.experiments.run_experiments import run
from src.experiments.simulation_factory import create_simulation
from src.fdtd.solver import FDTDSolver
from src.geometry.grid_mapping import GridMapper
from src.geometry.project_geometry import ProjectGeometry
from src.measurements.field_monitors import LineFluxMonitor
from src.measurements.power_metrics import (
    poynting_components,
    relative_field_db,
    relative_power_db,
)
from src.sources.aperture_source import ApertureSource, SourceConfig


ROOT = Path(__file__).resolve().parents[1]


class GeometryAndMappingTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / "configs" / "baseline.yaml")
        self.geometry = ProjectGeometry.from_config(self.config)

    def test_landmarks_and_reflector_endpoints(self):
        self.assertEqual(self.geometry.transmitter_world_m, (-1.0, 0.0))
        self.assertEqual(self.geometry.reflector_center_world_m, (0.0, 0.0))
        self.assertEqual(self.geometry.receiver_world_m, (0.0, 1.0))
        p1, p2 = self.geometry.reflector_endpoints_world_m()
        self.assertAlmostEqual(math.hypot(p2[0] - p1[0], p2[1] - p1[1]), 0.30)
        self.assertAlmostEqual((p2[1] - p1[1]) / (p2[0] - p1[0]), 1.0)
        reflected = calculate_analytical(self.geometry, 20)["reflected_direction_xy"]
        self.assertAlmostEqual(reflected[0], 0.0, places=12)
        self.assertAlmostEqual(reflected[1], 1.0, places=12)

    def test_world_coordinate_mapping_and_bounds(self):
        mapper = GridMapper(-2.0, -0.3, 0.01, 0.01, 300, 240)
        self.assertEqual(mapper.world_to_local_m(-1.0, 0.0), (1.0, 0.3))
        self.assertEqual(mapper.world_to_local_m(0.0, 0.0), (2.0, 0.3))
        self.assertEqual(mapper.world_to_local_m(0.0, 1.0), (2.0, 1.3))
        self.assertEqual(mapper.world_to_index(-1.0, 0.0), (100, 30))
        self.assertEqual(mapper.world_to_index(0.0, 1.0), (200, 130))
        with self.assertRaises(IndexError):
            mapper.world_to_index(2.0, 0.0)


class SolverSourceAndMeasurementTests(unittest.TestCase):
    def test_member2_arrays_and_member3_callback(self):
        solver = FDTDSolver(
            nx=80, ny=70, dx=1e-3, frequency=10e9,
            source_x=20, source_y=35, use_builtin_source=False,
        )
        source = ApertureSource(
            SourceConfig(
                frequency=10e9, aperture_width=0.012, steering_angle_deg=0,
                waveform="cw", taper="hann",
            )
        )
        source.configure_grid(solver)
        solver.run(5, source=source.inject)
        self.assertEqual(solver.Ez.shape, (80, 70))
        self.assertEqual(solver.Hx.shape, (80, 69))
        self.assertEqual(solver.Hy.shape, (79, 70))
        self.assertTrue(np.isfinite(solver.Ez).all())
        self.assertTrue(np.isfinite(solver.Hx).all())
        self.assertTrue(np.isfinite(solver.Hy).all())
        sx, sy = poynting_components(solver)
        self.assertEqual(sx.shape, solver.Ez.shape)
        self.assertEqual(sy.shape, solver.Ez.shape)
        self.assertTrue(np.isfinite(sx).all())
        self.assertTrue(np.isfinite(sy).all())

    def test_power_ratio_tilt_and_width_conversions(self):
        self.assertAlmostEqual(relative_power_db(2.0, 1.0), 10 * math.log10(2.0))
        self.assertAlmostEqual(relative_field_db(2.0, 1.0), 20 * math.log10(2.0))
        self.assertTrue(math.isnan(relative_power_db(0.0, 1.0)))
        self.assertTrue(math.isnan(relative_power_db(1.0, 0.0)))
        self.assertEqual(actual_plate_angle_deg(45.0, -10.0), 35.0)
        width_m = width_m_from_lambda(10.0, 10e9)
        self.assertAlmostEqual(width_m, 0.299792458)
        self.assertAlmostEqual(width_lambda_from_m(width_m, 10e9), 10.0)

    def test_poynting_component_signs_and_values(self):
        solver = FDTDSolver(nx=5, ny=6, dx=1e-3, frequency=10e9)
        solver.Ez.fill(2.0)
        solver.Hx.fill(3.0)
        solver.Hy.fill(4.0)
        sx, sy = poynting_components(solver)
        np.testing.assert_allclose(sx, -8.0)
        np.testing.assert_allclose(sy, 6.0)

    def test_sensor_validation_and_baseline_factory(self):
        config = load_config(ROOT / "configs" / "quick_test.yaml")
        simulation = create_simulation(config)
        self.assertEqual(simulation.solver.source_x, simulation.mapper.world_to_index(-1.0, 0.0)[0])
        plate_center = simulation.mapper.world_to_index(0.0, 0.0)
        self.assertTrue(simulation.solver.pec[plate_center])
        for monitor in (simulation.receiver_monitor, *simulation.off_axis_monitors):
            self.assertAlmostEqual(math.hypot(*monitor.normal_xy), 1.0, places=5)
            monitor.validate_clear(
                simulation.mapper, simulation.geometry, simulation.solver.pec
            )
        with self.assertRaises(ValueError):
            LineFluxMonitor("bad", (0.0, 1.0), (0.0, 2.0), 0.2)

    def test_corridor_mouths_are_open(self):
        config = load_config(ROOT / "configs" / "quick_test.yaml")
        simulation = create_simulation(config)
        solver = simulation.solver
        x_world, y_world = simulation.mapper.coordinate_arrays_world_m()
        horizontal_rows = np.flatnonzero(
            (y_world >= simulation.geometry.horizontal_y_m[0])
            & (y_world <= simulation.geometry.horizontal_y_m[1])
        )
        vertical_cols = np.flatnonzero(
            (x_world >= simulation.geometry.vertical_x_m[0])
            & (x_world <= simulation.geometry.vertical_x_m[1])
        )
        self.assertFalse(solver.pec[0, horizontal_rows].any())
        self.assertFalse(solver.pec[vertical_cols, -1].any())


class QuickPipelineTests(unittest.TestCase):
    def test_quick_mode_generates_csv_and_plots(self):
        config = load_config(ROOT / "configs" / "quick_test.yaml")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            config["outputs"] = {
                "tables_dir": str(output_root / "tables"),
                "figures_dir": str(output_root / "figures"),
                "reports_dir": str(output_root / "reports"),
            }
            config_path = output_root / "quick.yaml"
            config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
            run(config_path)
            expected = [
                output_root / "tables" / "tilt_sweep.csv",
                output_root / "tables" / "width_sweep.csv",
                output_root / "tables" / "off_axis_sensors.csv",
                output_root / "figures" / "tilt_vs_receiver_power.png",
                output_root / "figures" / "width_vs_receiver_power.png",
                output_root / "figures" / "off_axis_interception_heatmap.png",
                output_root / "figures" / "baseline_power_distribution.png",
                output_root / "reports" / "member4_experiment_summary.md",
            ]
            for path in expected:
                self.assertTrue(path.is_file(), f"Missing generated output {path}")
            with (output_root / "tables" / "tilt_sweep.csv").open(
                newline="", encoding="utf-8"
            ) as stream:
                tilt_rows = list(csv.DictReader(stream))
            self.assertEqual(len(tilt_rows), 3)
            self.assertIn("relative_receiver_flux_db_vs_aligned", tilt_rows[0])

    def test_cst_comparison_normalizes_each_sensor(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            cst_path = root / "cst.csv"
            python_path = root / "python.csv"
            output_path = root / "comparison.csv"
            cst_path.write_text(
                "case_type,case_value,sensor_name,normalized_power\n"
                "baseline,0,monitor_a,1\n"
                "tilt,5,monitor_a,0.5\n",
                encoding="utf-8",
            )
            python_path.write_text(
                "case_type,tilt_offset_deg,plate_width_lambda,sensor_name,"
                "relative_flux_db_vs_same_sensor_baseline\n"
                "tilt,5,,monitor_a,-3.0102999566\n",
                encoding="utf-8",
            )
            rows = compare_cst_exports(
                cst_path, python_path, "tilt", 5.0, output_path
            )
            self.assertEqual(rows, 1)
            with output_path.open(newline="", encoding="utf-8") as stream:
                result = next(csv.DictReader(stream))
            self.assertAlmostEqual(float(result["cst_relative_power_db"]), -3.0103, places=3)


if __name__ == "__main__":
    unittest.main()
