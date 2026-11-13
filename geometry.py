"""Shared geometry definition for analytical calculations and plotting."""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class ProjectGeometry:
    frequency_hz: float = 10e9
    corridor_length_m: float = 2.0
    corridor_width_m: float = 0.6
    reflector_length_m: float = 0.30
    reflector_height_m: float = 0.30
    reflector_thickness_m: float = 0.001
    tx: tuple = (-1.0, 0.0)
    reflector_center: tuple = (0.0, 0.0)
    rx: tuple = (0.0, 1.0)
    cells_per_wavelength_final: int = 20
    cells_per_wavelength_debug: int = 10

G = ProjectGeometry()

def in_corridor(x, y, tol=0.0):
    """True for points in either open rectangular arm of the L corridor."""
    horizontal = (-2.0 - tol <= x <= 0.0 + tol and
                  -0.3 - tol <= y <= 0.3 + tol)
    vertical = (-0.3 - tol <= x <= 0.3 + tol and
                0.0 - tol <= y <= 2.0 + tol)
    return horizontal or vertical

def direct_path_visibility(samples=2001):
    """Sample the direct Tx-Rx segment; return visibility and outside samples."""
    t = np.linspace(0.0, 1.0, samples)
    tx = np.array(G.tx, dtype=float)
    rx = np.array(G.rx, dtype=float)
    pts = tx[None, :] + t[:, None] * (rx - tx)[None, :]
    inside = np.array([in_corridor(x, y, tol=1e-9) for x, y in pts])
    return bool(np.all(inside)), pts[~inside]

def reflector_endpoints():
    """Endpoints of a 0.30 m plate whose tangent is at +45 degrees."""
    center = np.array(G.reflector_center, dtype=float)
    tangent = np.array([1.0, 1.0]) / np.sqrt(2.0)
    half = 0.5 * G.reflector_length_m
    return center - half * tangent, center + half * tangent
