"""Reusable simulation execution and cycle-averaged line-flux sampling."""

from dataclasses import dataclass
import time
from typing import Any

import numpy as np

from src.experiments.simulation_factory import Simulation
from src.measurements.power_metrics import cycle_window_steps, poynting_components


@dataclass
class CaseResult:
    simulation: Simulation
    receiver_flux_per_depth: float
    off_axis_flux_per_depth: dict[str, float]
    time_step_s: float
    total_steps: int
    warmup_steps: int
    measurement_steps: int
    elapsed_wall_s: float
    average_sx: np.ndarray | None = None
    average_sy: np.ndarray | None = None

    @property
    def simulation_duration_s(self) -> float:
        return self.total_steps * self.time_step_s

    @property
    def measurement_duration_s(self) -> float:
        return self.measurement_steps * self.time_step_s


def run_case(
    config: dict[str, Any],
    simulation: Simulation,
    keep_average_field: bool = False,
) -> CaseResult:
    solver = simulation.solver
    sim_config = config["simulation"]
    warmup_steps = cycle_window_steps(
        solver.frequency, solver.dt, float(sim_config["warmup_cycles"])
    )
    measurement_steps = cycle_window_steps(
        solver.frequency, solver.dt, float(sim_config["measurement_cycles"])
    )
    monitor_flux_sums = {m.name: 0.0 for m in (simulation.receiver_monitor, *simulation.off_axis_monitors)}
    average_sx_sum = np.zeros_like(solver.Ez) if keep_average_field else None
    average_sy_sum = np.zeros_like(solver.Ez) if keep_average_field else None
    started = time.perf_counter()
    total_steps = warmup_steps + measurement_steps
    report_interval = max(1, total_steps // 4)

    for step_index in range(total_steps):
        solver.step(source=simulation.source.inject)
        if step_index >= warmup_steps:
            sx, sy = poynting_components(solver)
            for monitor in (simulation.receiver_monitor, *simulation.off_axis_monitors):
                monitor_flux_sums[monitor.name] += monitor.integrated_flux(
                    sx, sy, simulation.mapper
                )
            if keep_average_field:
                average_sx_sum += sx
                average_sy_sum += sy
        if (step_index + 1) % report_interval == 0 or step_index + 1 == total_steps:
            print(f"    steps {step_index + 1}/{total_steps}", flush=True)

    elapsed = time.perf_counter() - started
    mean_flux = {name: value / measurement_steps for name, value in monitor_flux_sums.items()}
    return CaseResult(
        simulation=simulation,
        receiver_flux_per_depth=mean_flux[simulation.receiver_monitor.name],
        off_axis_flux_per_depth={
            monitor.name: mean_flux[monitor.name] for monitor in simulation.off_axis_monitors
        },
        time_step_s=solver.dt,
        total_steps=total_steps,
        warmup_steps=warmup_steps,
        measurement_steps=measurement_steps,
        elapsed_wall_s=elapsed,
        average_sx=average_sx_sum / measurement_steps if keep_average_field else None,
        average_sy=average_sy_sum / measurement_steps if keep_average_field else None,
    )
