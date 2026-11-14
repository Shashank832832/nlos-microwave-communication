
import numpy as np

# Physical constants
C0 = 299_792_458.0
MU0 = 4.0 * np.pi * 1e-7
EPS0 = 1.0 / (MU0 * C0**2)


class FDTDSolver:
    """
    2D TMz FDTD solver.

    Ez: electric field (V/m)
    Hx: magnetic field (A/m), x-directed
    Hy: magnetic field (A/m), y-directed

    Features:
    - Yee staggered grid
    - Leapfrog time stepping
    - 10 GHz continuous-wave point source
    - First-order Mur absorbing boundaries
    """

    def __init__(
        self,
        frequency=10e9,
        cells_per_wavelength=20,
        x_bounds=(-2.0, 0.6),
        y_bounds=(-0.3, 2.0),
        courant_factor=0.99,
        use_pec=True
    ):
        self.frequency = frequency
        self.wavelength = C0 / frequency
        self.omega = 2.0 * np.pi * frequency

        # Spatial grid
        self.dx = self.wavelength / cells_per_wavelength
        self.dy = self.dx

        self.x_min, self.x_max = x_bounds
        self.y_min, self.y_max = y_bounds

        self.nx = int(np.ceil(
            (self.x_max - self.x_min) / self.dx
        )) + 1

        self.ny = int(np.ceil(
            (self.y_max - self.y_min) / self.dy
        )) + 1

        self.x = self.x_min + np.arange(self.nx) * self.dx
        self.y = self.y_min + np.arange(self.ny) * self.dy

        # CFL time step
        self.dt_max = 1.0 / (
            C0 * np.sqrt(
                1.0 / self.dx**2 + 1.0 / self.dy**2
            )
        )

        self.dt = courant_factor * self.dt_max

        # TMz Yee field arrays
        self.Ez = np.zeros(
            (self.ny, self.nx), dtype=np.float32
        )

        self.Hx = np.zeros(
            (self.ny - 1, self.nx), dtype=np.float32
        )

        self.Hy = np.zeros(
            (self.ny, self.nx - 1), dtype=np.float32
        )

        self.time_step = 0

        # Point source position: transmitter at (-1, 0)
        self.source_x = -1.0
        self.source_y = 0.0

        self.source_i = np.argmin(
            np.abs(self.x - self.source_x)
        )
        self.source_j = np.argmin(
            np.abs(self.y - self.source_y)
        )

        self.source_amplitude = 1.0
        
        # Finite PEC reflector
        self.plate_length = 0.30
        self.plate_angle = np.deg2rad(45.0)

        self.pec_mask = self.create_pec_mask()
        
        self.use_pec = use_pec

        # Mur first-order absorbing boundary coefficients
        sx = C0 * self.dt / self.dx
        sy = C0 * self.dt / self.dy

        self.mur_x = (sx - 1.0) / (sx + 1.0)
        self.mur_y = (sy - 1.0) / (sy + 1.0)

    def print_grid_info(self):
        print("\n=== FDTD YEE GRID INITIALIZED ===")
        print(f"Frequency: {self.frequency / 1e9:.3f} GHz")
        print(f"Wavelength: {self.wavelength * 1000:.3f} mm")
        print(f"Grid spacing: {self.dx * 1000:.3f} mm")
        print(f"Grid dimensions: {self.nx} x {self.ny}")
        print(f"Ez shape: {self.Ez.shape}")
        print(f"Hx shape: {self.Hx.shape}")
        print(f"Hy shape: {self.Hy.shape}")
        print(f"Chosen time step: {self.dt * 1e12:.3f} ps")
        print(f"Source location: ({self.x[self.source_i]:.4f}, "
              f"{self.y[self.source_j]:.4f}) m")
        
    def create_pec_mask(self):
        """
        Create a finite diagonal PEC plate centred at (0, 0).
        Ez is forced to zero on the plate.
        """

        half_length = self.plate_length / 2

        # Endpoints of the plate
        x1 = -half_length * np.cos(self.plate_angle)
        y1 = -half_length * np.sin(self.plate_angle)

        x2 = half_length * np.cos(self.plate_angle)
        y2 = half_length * np.sin(self.plate_angle)

        # Grid coordinates
        X, Y = np.meshgrid(self.x, self.y)

        # Vector along the plate
        vx = x2 - x1
        vy = y2 - y1

        # Project each grid point onto the plate segment
        t = (
            (X - x1) * vx + (Y - y1) * vy
        ) / (vx**2 + vy**2)

        t = np.clip(t, 0.0, 1.0)

        closest_x = x1 + t * vx
        closest_y = y1 + t * vy

        distance_squared = (
            (X - closest_x)**2 + (Y - closest_y)**2
        )

        # Approximate the thin plate on the discrete grid
        mask = distance_squared <= (0.75 * self.dx)**2

        return mask

    def inject_source(self):
        """Inject a smoothly ramped 10 GHz sinusoidal point source."""

        time = (self.time_step + 1) * self.dt

        # Smoothly turn on the source over approximately 5 cycles
        ramp_time = 5.0 / self.frequency
        ramp = 1.0 - np.exp(
            -(time / ramp_time)**2
        )

        signal = (
            self.source_amplitude
            * np.sin(self.omega * time)
            * ramp
        )

        self.Ez[self.source_j, self.source_i] = signal

    def apply_mur_boundary(self, ez_old):
        """Apply first-order Mur absorbing conditions on four edges."""

        # Left and right boundaries
        self.Ez[1:-1, 0] = (
            ez_old[1:-1, 1]
            + self.mur_x * (
                self.Ez[1:-1, 1] - ez_old[1:-1, 0]
            )
        )

        self.Ez[1:-1, -1] = (
            ez_old[1:-1, -2]
            + self.mur_x * (
                self.Ez[1:-1, -2] - ez_old[1:-1, -1]
            )
        )

        # Bottom and top boundaries
        self.Ez[0, 1:-1] = (
            ez_old[1, 1:-1]
            + self.mur_y * (
                self.Ez[1, 1:-1] - ez_old[0, 1:-1]
            )
        )

        self.Ez[-1, 1:-1] = (
            ez_old[-2, 1:-1]
            + self.mur_y * (
                self.Ez[-2, 1:-1] - ez_old[-1, 1:-1]
            )
        )

        # Simple corner treatment
        self.Ez[0, 0] = 0.5 * (
            self.Ez[0, 1] + self.Ez[1, 0]
        )
        self.Ez[0, -1] = 0.5 * (
            self.Ez[0, -2] + self.Ez[1, -1]
        )
        self.Ez[-1, 0] = 0.5 * (
            self.Ez[-1, 1] + self.Ez[-2, 0]
        )
        self.Ez[-1, -1] = 0.5 * (
            self.Ez[-1, -2] + self.Ez[-2, -1]
        )

    def step(self):
        """Advance the electromagnetic fields by one time step."""

        # Save old electric field for Mur boundary calculation
        ez_old = self.Ez.copy()

        # 1. Update Hx
        self.Hx -= (
            self.dt / (MU0 * self.dy)
        ) * (self.Ez[1:, :] - self.Ez[:-1, :])

        # 2. Update Hy
        self.Hy += (
            self.dt / (MU0 * self.dx)
        ) * (self.Ez[:, 1:] - self.Ez[:, :-1])

        # 3. Update Ez
        curl_h = (
            (self.Hy[1:-1, 1:] - self.Hy[1:-1, :-1]) / self.dx
            -
            (self.Hx[1:, 1:-1] - self.Hx[:-1, 1:-1]) / self.dy
        )

        self.Ez[1:-1, 1:-1] += (
            self.dt / EPS0
        ) * curl_h

        # 4. Absorb outgoing waves at the domain edges
        self.apply_mur_boundary(ez_old)

        # 5. Enforce PEC boundary condition
        if self.use_pec:
            self.Ez[self.pec_mask] = 0.0

        # 6. Inject the continuous-wave source
        self.inject_source()

        self.time_step += 1


if __name__ == "__main__":
    solver = FDTDSolver()
    solver.print_grid_info()

    # Run 500 time steps
    for _ in range(500):
        solver.step()

    print("\n=== CONTINUOUS-WAVE TEST ===")
    print(f"Time steps: {solver.time_step}")
    print(
        f"Simulation time: "
        f"{solver.time_step * solver.dt * 1e9:.3f} ns"
    )
    print(f"Maximum |Ez|: {np.max(np.abs(solver.Ez)):.6e}")
    print(f"Maximum |Hx|: {np.max(np.abs(solver.Hx)):.6e}")
    print(f"Maximum |Hy|: {np.max(np.abs(solver.Hy)):.6e}")

    assert np.isfinite(solver.Ez).all()
    assert np.isfinite(solver.Hx).all()
    assert np.isfinite(solver.Hy).all()

    print("PASS: All fields contain finite values.")
    print("PASS: Continuous-wave source and Mur boundaries executed.")
