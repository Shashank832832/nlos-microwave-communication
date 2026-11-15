"""Spatial distribution of measured off-axis line flux."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def save_interception_heatmap(
    sensor_rows: list[dict], output_path: Path, dpi: int
) -> None:
    valid_rows = []
    for row in sensor_rows:
        flux = float(row["flux_W_per_m"])
        if np.isfinite(flux):
            valid_rows.append((row, flux))
    if not valid_rows:
        raise ValueError("No finite off-axis sensor flux values are available to plot.")
    x = np.asarray([float(row["center_x_world_m"]) for row, _flux in valid_rows])
    y = np.asarray([float(row["center_y_world_m"]) for row, _flux in valid_rows])
    flux = np.asarray([value for _row, value in valid_rows]) * 1e6
    fig, ax = plt.subplots(figsize=(8, 6))
    scatter = ax.scatter(
        x, y, c=flux, s=360, marker="s", cmap="coolwarm", edgecolors="black"
    )
    fig.colorbar(scatter, ax=ax, label="Signed line flux (µW/m per unit depth)")
    ax.set_xlabel("World x (m)")
    ax.set_ylabel("World y (m)")
    ax.set_title("Baseline Off-Axis Interception Measurements")
    x_padding = max(0.25 * (y.max() - y.min()), 0.05)
    y_padding = max(0.08 * (y.max() - y.min()), 0.05)
    ax.set_xlim(x.min() - x_padding, x.max() + x_padding)
    ax.set_ylim(y.min() - y_padding, y.max() + y_padding)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
