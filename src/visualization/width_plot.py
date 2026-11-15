"""Reflector-width receiver flux figure."""

from pathlib import Path

import matplotlib.pyplot as plt

from src.measurements.power_metrics import relative_power_db


def save_width_plot(
    rows: list[dict],
    reference_flux: float,
    nominal_width_m: float,
    output_path: Path,
    dpi: int,
) -> None:
    widths = [row["plate_width_lambda"] for row in rows]
    values = [relative_power_db(row["receiver_flux_W_per_m"], reference_flux) for row in rows]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(widths, values, marker="s", linewidth=2, color="#b34f26")
    ax.axhline(
        0,
        color="black",
        linewidth=0.8,
        linestyle="--",
        label=f"Nominal {nominal_width_m:.3f} m reference",
    )
    ax.set_xlabel("Reflector width (wavelengths)")
    ax.set_ylabel("Relative receiver flux (dB)")
    ax.set_title("Reflector Width vs Receiver Flux")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)
