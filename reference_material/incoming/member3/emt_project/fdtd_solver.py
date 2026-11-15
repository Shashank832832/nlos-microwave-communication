"""
fdtd_solver.py
--------------
Reusable 2-D TMz FDTD engine for the passive microwave reflector project.

Field arrangement:
    Ez : (nx, ny)
    Hx : (nx, ny - 1)
    Hy : (nx - 1, ny)

Coordinates are in metres. Ez is stored at integer grid nodes; Hx and Hy
are spatially staggered according to the Yee grid.

The source is deliberately externalizable:
    solver.step(source=source.inject)
where source.inject(solver, time_seconds) modifies solver.Ez.

A built-in Gaussian point source is provided for standalone smoke tests.
The Poynting-vector method spatially interpolates H onto Ez locations.
It is a useful diagnostic; rigorous instantaneous flux should also account
for the Yee half-time-step staggering and calibrated SI source amplitudes.
"""

from __future__ import annotations

from typing import Callable, Optional, Tuple

import numpy as np


SourceCallback = Callable[["FDTDSolver", float], None]


class FDTDSolver:
    """2-D TMz FDTD solver with first-order Mur ABC and PEC geometry."""

    C0 = 299_792_458.0
    MU0 = 4.0e-7 * np.pi
    EPS0 = 1.0 / (MU0 * C0**2)

    def __init__(
        self,
        nx: int = 200,
        ny: int = 200,
        dx: float = 1.0e-3,
        dy: Optional[float] = None,
        courant_factor: float = 0.99,
        frequency: float = 10.0e9,
        source_x: Optional[int] = None,
        source_y: Optional[int] = None,
        use_builtin_source: bool = True,
    ) -> None:
        if nx < 4 or ny < 4:
            raise ValueError("nx and ny must both be at least 4.")
        if dx <= 0:
            raise ValueError("dx must be positive.")
        if dy is None:
            dy = dx
        if dy <= 0:
            raise ValueError("dy must be positive.")
        if not (0.0 < courant_factor <= 1.0):
            raise ValueError("courant_factor must be in (0, 1].")
        if frequency <= 0:
            raise ValueError("frequency must be positive.")

        self.nx = int(nx)
        self.ny = int(ny)
        self.dx = float(dx)
        self.dy = float(dy)
        self.frequency = float(frequency)
        self.courant_factor = float(courant_factor)

        # 2-D CFL limit, valid for unequal dx and dy.
        self.dt_max = 1.0 / (
            self.C0 * np.sqrt(1.0 / self.dx**2 + 1.0 / self.dy**2)
        )
        self.dt = self.courant_factor * self.dt_max

        # Yee-grid fields.
        self.Ez = np.zeros((self.nx, self.ny), dtype=np.float64)
        self.Hx = np.zeros((self.nx, self.ny - 1), dtype=np.float64)
        self.Hy = np.zeros((self.nx - 1, self.ny), dtype=np.float64)

        # PEC mask applies to Ez nodes.
        self.pec = np.zeros((self.nx, self.ny), dtype=bool)

        self.source_x = self.nx // 4 if source_x is None else int(source_x)
        self.source_y = self.ny // 2 if source_y is None else int(source_y)
        self._validate_grid_index(self.source_x, self.source_y)

        self.use_builtin_source = bool(use_builtin_source)
        self.tau = 1.0 / self.frequency
        self.t0 = 4.0 * self.tau

        # First-order Mur coefficients for each axis.
        self.mur_x = (
            self.C0 * self.dt - self.dx
        ) / (
            self.C0 * self.dt + self.dx
        )
        self.mur_y = (
            self.C0 * self.dt - self.dy
        ) / (
            self.C0 * self.dt + self.dy
        )

        self.time_step = 0
        self.time = 0.0

    @property
    def shape(self) -> Tuple[int, int]:
        return self.Ez.shape

    @property
    def wavelength(self) -> float:
        return self.C0 / self.frequency

    @property
    def cells_per_wavelength_x(self) -> float:
        return self.wavelength / self.dx

    @property
    def cells_per_wavelength_y(self) -> float:
        return self.wavelength / self.dy

    def _validate_grid_index(self, ix: int, iy: int) -> None:
        if not (0 <= ix < self.nx and 0 <= iy < self.ny):
            raise IndexError(
                f"Grid index ({ix}, {iy}) is outside "
                f"the grid ({self.nx}, {self.ny})."
            )

    # ------------------------------------------------------------------
    # Yee updates
    # ------------------------------------------------------------------

    def update_hx(self) -> None:
        """Update Hx at its Yee locations."""
        self.Hx -= (
            self.dt / (self.MU0 * self.dy)
        ) * (
            self.Ez[:, 1:] - self.Ez[:, :-1]
        )

    def update_hy(self) -> None:
        """Update Hy at its Yee locations."""
        self.Hy += (
            self.dt / (self.MU0 * self.dx)
        ) * (
            self.Ez[1:, :] - self.Ez[:-1, :]
        )

    def update_magnetic_fields(self) -> None:
        self.update_hx()
        self.update_hy()

    def update_ez(self) -> None:
        """Update interior Ez nodes from the discrete curl of H."""
        curl_h = (
            (self.Hy[1:, 1:-1] - self.Hy[:-1, 1:-1]) / self.dx
            -
            (self.Hx[1:-1, 1:] - self.Hx[1:-1, :-1]) / self.dy
        )
        self.Ez[1:-1, 1:-1] += (
            self.dt / self.EPS0
        ) * curl_h

    # ------------------------------------------------------------------
    # Absorbing boundary condition
    # ------------------------------------------------------------------

    def apply_mur_abc(self, old_ez: np.ndarray) -> None:
        """Apply first-order Mur ABC on four edges.

        The simple corner treatment is an average of adjacent edge values.
        First-order Mur is approximate and is less effective at oblique
        incidence than higher-order ABC or PML.
        """
        sx = self.mur_x
        sy = self.mur_y

        # Left and right edges.
        self.Ez[0, 1:-1] = (
            old_ez[1, 1:-1]
            + sx * (self.Ez[1, 1:-1] - old_ez[0, 1:-1])
        )
        self.Ez[-1, 1:-1] = (
            old_ez[-2, 1:-1]
            + sx * (self.Ez[-2, 1:-1] - old_ez[-1, 1:-1])
        )

        # Bottom and top edges.
        self.Ez[1:-1, 0] = (
            old_ez[1:-1, 1]
            + sy * (self.Ez[1:-1, 1] - old_ez[1:-1, 0])
        )
        self.Ez[1:-1, -1] = (
            old_ez[1:-1, -2]
            + sy * (self.Ez[1:-1, -2] - old_ez[1:-1, -1])
        )

        # Approximate corner values.
        self.Ez[0, 0] = 0.5 * (self.Ez[0, 1] + self.Ez[1, 0])
        self.Ez[0, -1] = 0.5 * (self.Ez[0, -2] + self.Ez[1, -1])
        self.Ez[-1, 0] = 0.5 * (self.Ez[-1, 1] + self.Ez[-2, 0])
        self.Ez[-1, -1] = 0.5 * (
            self.Ez[-1, -2] + self.Ez[-2, -1]
        )

    # ------------------------------------------------------------------
    # Source interface
    # ------------------------------------------------------------------

    def gaussian_pulse(self, time_seconds: float) -> float:
        """Built-in Gaussian-modulated sinusoidal test pulse."""
        envelope = np.exp(
            -((time_seconds - self.t0) / self.tau) ** 2
        )
        carrier = np.sin(
            2.0 * np.pi * self.frequency
            * (time_seconds - self.t0)
        )
        return float(envelope * carrier)

    def inject_builtin_source(self, time_seconds: float) -> None:
        if self.use_builtin_source:
            self.Ez[self.source_x, self.source_y] = (
                self.gaussian_pulse(time_seconds)
            )

    # ------------------------------------------------------------------
    # PEC geometry
    # ------------------------------------------------------------------

    def add_pec_plate(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        thickness: float,
    ) -> None:
        """Rasterize a finite-thickness PEC line segment.

        Endpoints and thickness are in metres. The resulting mask is a
        staircase/grid approximation of the physical conducting plate.
        """
        if thickness <= 0:
            raise ValueError("Plate thickness must be positive.")

        vx = x2 - x1
        vy = y2 - y1
        length_squared = vx * vx + vy * vy

        if length_squared == 0:
            raise ValueError("Plate endpoints must be different.")

        x = np.arange(self.nx) * self.dx
        y = np.arange(self.ny) * self.dy
        X, Y = np.meshgrid(x, y, indexing="ij")

        projection = (
            (X - x1) * vx + (Y - y1) * vy
        ) / length_squared
        projection = np.clip(projection, 0.0, 1.0)

        closest_x = x1 + projection * vx
        closest_y = y1 + projection * vy

        distance_squared = (
            (X - closest_x) ** 2 + (Y - closest_y) ** 2
        )

        self.pec |= distance_squared <= (thickness / 2.0) ** 2
        self.apply_pec()

    def add_tilted_pec_plate(
        self,
        center_x: float,
        center_y: float,
        length: float,
        angle_deg: float,
        thickness: float,
    ) -> None:
        """Add a plate specified by centre, length and angle from +x."""
        if length <= 0:
            raise ValueError("Plate length must be positive.")

        angle = np.deg2rad(angle_deg)
        half_dx = 0.5 * length * np.cos(angle)
        half_dy = 0.5 * length * np.sin(angle)

        self.add_pec_plate(
            center_x - half_dx,
            center_y - half_dy,
            center_x + half_dx,
            center_y + half_dy,
            thickness,
        )

    def apply_pec(self) -> None:
        """Enforce Ez = 0 on PEC mask nodes."""
        self.Ez[self.pec] = 0.0

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def calculate_poynting(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return spatially collocated approximate Sx and Sy arrays.

        H is spatially interpolated onto Ez locations. Since the Yee
        scheme staggers E and H in time as well, this method is intended
        for visualization and preliminary relative comparisons. For
        publication-grade flux, time-centre H and validate energy balance.
        """
        hx_padded = np.pad(
            self.Hx, ((0, 0), (1, 1)), mode="edge"
        )
        hx_at_e = 0.5 * (
            hx_padded[:, :-1] + hx_padded[:, 1:]
        )

        hy_padded = np.pad(
            self.Hy, ((1, 1), (0, 0)), mode="edge"
        )
        hy_at_e = 0.5 * (
            hy_padded[:-1, :] + hy_padded[1:, :]
        )

        sx = -self.Ez * hy_at_e
        sy = self.Ez * hx_at_e
        return sx, sy

    def total_electric_energy_proxy(self) -> float:
        """Return sum(Ez**2) as a numerical stability diagnostic.

        This is not the complete electromagnetic energy because H fields,
        material weighting and Yee-grid cell volumes are not included.
        """
        return float(np.sum(self.Ez * self.Ez))

    # ------------------------------------------------------------------
    # Time integration
    # ------------------------------------------------------------------

    def step(self, source: Optional[SourceCallback] = None) -> None:
        """Advance the fields by one time step.

        External source callback contract:
            source(solver, time_seconds)

        If no callback is supplied, the built-in Gaussian source is used
        when use_builtin_source=True.
        """
        self.update_magnetic_fields()

        old_ez = self.Ez.copy()
        self.update_ez()
        self.apply_mur_abc(old_ez)

        next_time = (self.time_step + 1) * self.dt

        if source is not None:
            source(self, next_time)
        else:
            self.inject_builtin_source(next_time)

        self.apply_pec()

        self.time_step += 1
        self.time = self.time_step * self.dt

    def run(
        self,
        n_steps: int,
        source: Optional[SourceCallback] = None,
        callback: Optional[Callable[["FDTDSolver"], None]] = None,
    ) -> None:
        """Run n_steps; optional callback is called after every step."""
        if n_steps < 0:
            raise ValueError("n_steps cannot be negative.")

        for _ in range(n_steps):
            self.step(source=source)
            if callback is not None:
                callback(self)

    def reset_fields(self) -> None:
        """Clear fields and reset time without changing geometry/settings."""
        self.Ez.fill(0.0)
        self.Hx.fill(0.0)
        self.Hy.fill(0.0)
        self.time_step = 0
        self.time = 0.0
