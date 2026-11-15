"""Tilt-sweep receiver flux figure."""

from pathlib import Path

import matplotlib.pyplot as plt

from src.measurements.power_metrics import relative_power_db


def save_tilt_plot(
    rows: list[dict],
    reference_flux: float,
    nominal_angle_deg: float,
    output_path: Path,
    dpi: int,
) -> None:
    offsets = [row["tilt_offset_deg"] for row in rows]
    values = [relative_power_db(row["receiver_flux_W_per_m"], reference_flux) for row in rows]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(offsets, values, marker="o", linewidth=2)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", label="Aligned reference")
    ax.axvline(0, color="gray", linewidth=0.8, linestyle=":")
    ax.set_xlabel(f"Tilt offset from nominal {nominal_angle_deg:g}° (degrees)")
    ax.set_ylabel("Relative receiver flux (dB)")
    ax.set_title("Reflector Tilt vs Receiver Flux")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
