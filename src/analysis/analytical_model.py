"""First-order analytical values; LOS Friis remains a reference, not NLOS power."""

import math
from typing import Any

import numpy as np

from src.geometry.project_geometry import ProjectGeometry

C0 = 299_792_458.0
MU0 = 4.0e-7 * math.pi
EPS0 = 1.0 / (MU0 * C0**2)


def calculate(
    geometry: ProjectGeometry, cells_per_wavelength: int, courant_factor: float = 0.99
) -> dict[str, Any]:
    frequency_hz = geometry.frequency_hz
    wavelength_m = C0 / frequency_hz
    if cells_per_wavelength <= 0:
        raise ValueError("Cells per wavelength must be positive.")
    dx_m = wavelength_m / cells_per_wavelength
    dt_max_s = 1.0 / (C0 * math.sqrt(1 / dx_m**2 + 1 / dx_m**2))
    tx = np.asarray(geometry.transmitter_world_m)
    reflector = np.asarray(geometry.reflector_center_world_m)
    rx = np.asarray(geometry.receiver_world_m)
    d1_m = float(np.linalg.norm(reflector - tx))
    d2_m = float(np.linalg.norm(rx - reflector))
    direct_distance_m = float(np.linalg.norm(rx - tx))
    tangent_angle_rad = math.radians(geometry.reflector_nominal_angle_deg)
    normal = np.asarray(
        [math.sin(tangent_angle_rad), -math.cos(tangent_angle_rad)]
    )
    incident = np.asarray([1.0, 0.0])
    reflected_direction = incident - 2 * np.dot(incident, normal) * normal
    return {
        "frequency_hz": frequency_hz,
        "wavelength_m": wavelength_m,
        "dx_final_m": dx_m,
        "dt_final_s": courant_factor * dt_max_s,
        "d_tx_reflector_m": d1_m,
        "d_reflector_rx_m": d2_m,
        "reflected_path_length_m": d1_m + d2_m,
        "first_fresnel_radius_m": math.sqrt(wavelength_m * d1_m * d2_m / (d1_m + d2_m)),
        "plate_width_lambda": geometry.reflector_width_m / wavelength_m,
        "direct_distance_m": direct_distance_m,
        "unobstructed_direct_fspl_db": 20 * math.log10(
            4 * math.pi * direct_distance_m / wavelength_m
        ),
        "reflected_direction_xy": reflected_direction,
    }
