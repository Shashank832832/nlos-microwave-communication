"""Normalized electrical-width sweep at the nominal reflector orientation."""

from typing import Any

from src.experiments.experiment_config import width_m_from_lambda
from src.experiments.experiment_runner import CaseResult, run_case
from src.experiments.simulation_factory import create_simulation


def run_width_sweep(config: dict[str, Any]) -> list[tuple[dict, CaseResult]]:
    frequency_hz = float(config["simulation"]["frequency_hz"])
    nominal_angle_deg = float(config["geometry"]["reflector_nominal_angle_deg"])
    results = []
    for width_lambda in config["experiments"]["plate_widths_lambda"]:
        width_m = width_m_from_lambda(float(width_lambda), frequency_hz)
        print(f"  Plate width {float(width_lambda):.2f} lambda ({width_m:.5f} m)")
        result = run_case(
            config,
            create_simulation(
                config, plate_angle_deg=nominal_angle_deg, plate_width_m=width_m
            ),
        )
        solver = result.simulation.solver
        row = {
                "plate_width_lambda": float(width_lambda),
                "plate_width_m": width_m,
                "actual_plate_angle_deg": nominal_angle_deg,
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
