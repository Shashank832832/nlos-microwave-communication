"""Relative power/flux metrics for the approximate 2-D TMz Poynting field."""

import math

import numpy as np

from src.fdtd.solver import FDTDSolver


def poynting_components(solver: FDTDSolver) -> tuple[np.ndarray, np.ndarray]:
    """Return approximate Sx=-Ez*Hy and Sy=Ez*Hx from solver diagnostics."""
    sx, sy = solver.calculate_poynting()
    if sx.shape != solver.Ez.shape or sy.shape != solver.Ez.shape:
        raise ValueError("Solver Poynting arrays must match the Ez grid shape.")
    if not np.isfinite(sx).all() or not np.isfinite(sy).all():
        raise FloatingPointError("Non-finite Poynting values detected.")
    return sx, sy


def relative_power_db(measured_flux: float, reference_flux: float) -> float:
    """Return 10*log10(measured/reference), or NaN for invalid/nonpositive flux."""
    if not math.isfinite(measured_flux) or not math.isfinite(reference_flux):
        return float("nan")
    if measured_flux <= 0.0 or reference_flux <= 0.0:
        return float("nan")
    return 10.0 * math.log10(measured_flux / reference_flux)


def relative_field_db(measured_amplitude: float, reference_amplitude: float) -> float:
    """Return 20*log10(amplitude ratio); kept distinct from power dB."""
    if not math.isfinite(measured_amplitude) or not math.isfinite(reference_amplitude):
        return float("nan")
    if measured_amplitude <= 0.0 or reference_amplitude <= 0.0:
        return float("nan")
    return 20.0 * math.log10(measured_amplitude / reference_amplitude)


def cycle_window_steps(frequency_hz: float, dt_s: float, cycles: float) -> int:
    if frequency_hz <= 0 or dt_s <= 0 or cycles <= 0:
        raise ValueError("Frequency, time step, and cycle count must be positive.")
    return max(1, int(round(cycles / (frequency_hz * dt_s))))
