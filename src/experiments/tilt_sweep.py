"""Reflector tangent-angle sweep around the nominal specular orientation."""

from typing import Any

from src.experiments.experiment_config import actual_plate_angle_deg
from src.experiments.experiment_runner import CaseResult, run_case
from src.experiments.simulation_factory import create_simulation


def run_tilt_sweep(config: dict[str, Any]) -> list[tuple[dict, CaseResult]]:
    geometry = config["geometry"]
    nominal_angle_deg = float(geometry["reflector_nominal_angle_deg"])
    results = []
    for offset_deg in config["experiments"]["tilt_offsets_deg"]:
        actual_deg = actual_plate_angle_deg(nominal_angle_deg, float(offset_deg))
        print(f"  Tilt offset {float(offset_deg):+.1f} deg (plate {actual_deg:.1f} deg)")
        result = run_case(
            config,
            create_simulation(config, plate_angle_deg=actual_deg),
        )
        solver = result.simulation.solver
        row = {
                "tilt_offset_deg": float(offset_deg),
                "actual_plate_angle_deg": actual_deg,
                "receiver_flux_W_per_m": result.receiver_flux_per_depth,
                "cells_per_wavelength": solver.cells_per_wavelength_x,
                "dx_m": solver.dx,
                "dt_s": result.time_step_s,
                "simulation_duration_s": result.simulation_duration_s,
                "measurement_duration_s": result.measurement_duration_s,
                "warmup_steps": result.warmup_steps,
                "measurement_steps": result.measurement_steps,
                "elapsed_wall_s": result.elapsed_wall_s,
            }
        results.append((row, result))
    return results
