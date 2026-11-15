"""Baseline cycle-averaged Poynting-vector distribution."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.experiments.experiment_runner import CaseResult


def save_baseline_distribution(result: CaseResult, output_path: Path, dpi: int, cmap: str) -> None:
    if result.average_sx is None or result.average_sy is None:
        raise ValueError("Baseline result does not contain averaged field diagnostics.")
    mapper = result.simulation.mapper
    x_world, y_world = mapper.coordinate_arrays_world_m()
    magnitude = np.hypot(result.average_sx, result.average_sy)
    magnitude = np.ma.masked_where(result.simulation.solver.pec, magnitude)
    fig, ax = plt.subplots(figsize=(9, 7))
    image = ax.pcolormesh(x_world, y_world, magnitude.T, shading="auto", cmap=cmap)
    fig.colorbar(image, ax=ax, label="Mean Poynting-vector magnitude (diagnostic)")
    for monitor in (result.simulation.receiver_monitor, *result.simulation.off_axis_monitors):
        ax.plot(*monitor.center_world_m, marker="o", markersize=3, color="cyan")
    ax.plot(*result.simulation.geometry.transmitter_world_m, marker="*", color="white", markersize=10)
    ax.plot(*result.simulation.geometry.reflector_center_world_m, marker="x", color="yellow", markersize=8)
    ax.set_xlabel("World x (m)")
    ax.set_ylabel("World y (m)")
    ax.set_title("Baseline Cycle-Averaged Power-Flow Diagnostic")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(result.simulation.geometry.domain_x_min_m, result.simulation.geometry.domain_x_max_m)
    ax.set_ylim(result.simulation.geometry.domain_y_min_m, result.simulation.geometry.domain_y_max_m)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
