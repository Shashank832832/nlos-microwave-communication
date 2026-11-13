"""First-order analytical calculations for the 10 GHz NLOS reflector project."""
import math
import numpy as np
from geometry import G

C0 = 299_792_458.0
MU0 = 4.0e-7 * math.pi
EPS0 = 1.0 / (MU0 * C0**2)

def calculate():
    f = G.frequency_hz
    wavelength = C0 / f
    omega = 2.0 * math.pi * f
    k0 = 2.0 * math.pi / wavelength

    dx = wavelength / G.cells_per_wavelength_final
    dt_max = dx / (C0 * math.sqrt(2.0))
    dt = 0.99 * dt_max

    tx = np.array(G.tx, dtype=float)
    p = np.array(G.reflector_center, dtype=float)
    rx = np.array(G.rx, dtype=float)
    d1 = float(np.linalg.norm(p - tx))
    d2 = float(np.linalg.norm(rx - p))
    d_total = d1 + d2

    # First Fresnel-zone radius at the specular point for the unfolded two-leg path.
    fresnel_r1 = math.sqrt(wavelength * d1 * d2 / (d1 + d2))

    # Unobstructed free-space reference only. This is NOT the reflected-link prediction.
    direct_distance = float(np.linalg.norm(rx - tx))
    fspl_direct_db = 20.0 * math.log10(4.0 * math.pi * direct_distance / wavelength)
    fspl_leg1_db = 20.0 * math.log10(4.0 * math.pi * d1 / wavelength)
    fspl_leg2_db = 20.0 * math.log10(4.0 * math.pi * d2 / wavelength)

    # Incident +x and reflected +y; normal (1,-1)/sqrt(2), plate tangent at +45 deg.
    ki = np.array([1.0, 0.0])
    n = np.array([1.0, -1.0]) / math.sqrt(2.0)
    kr = ki - 2.0 * np.dot(ki, n) * n
    plate_angle_deg = 45.0

    return {
        "frequency_hz": f,
        "wavelength_m": wavelength,
        "omega_rad_s": omega,
        "k0_rad_m": k0,
        "dx_m": dx,
        "dt_max_s": dt_max,
        "dt_used_s": dt,
        "d_tx_reflector_m": d1,
        "d_reflector_rx_m": d2,
        "reflected_path_length_m": d_total,
        "first_fresnel_radius_m": fresnel_r1,
        "plate_length_over_lambda": G.reflector_length_m / wavelength,
        "direct_distance_m": direct_distance,
        "unobstructed_direct_fspl_db": fspl_direct_db,
        "leg1_fspl_reference_db": fspl_leg1_db,
        "leg2_fspl_reference_db": fspl_leg2_db,
        "reflected_direction": kr,
        "plate_angle_deg": plate_angle_deg,
    }

if __name__ == "__main__":
    for key, value in calculate().items():
        print(f"{key}: {value}")
