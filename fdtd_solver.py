
import numpy as np

# Physical constants
C0 = 299_792_458.0
MU0 = 4.0 * np.pi * 1e-7
EPS0 = 1.0 / (MU0 * C0**2)


class FDTDSolver:
    """
    2D TMz FDTD grid.

    Ez: electric field, located at cell centers
    Hx: magnetic field, staggered in the y direction
    Hy: magnetic field, staggered in the x direction
    """

    def __init__(
        self,
        frequency=10e9,
        cells_per_wavelength=20,
        x_bounds=(-2.0, 0.6),
        y_bounds=(-0.3, 2.0),
        courant_factor=0.99
    ):
        self.frequency = frequency
        self.wavelength = C0 / frequency

        # Spatial resolution
        self.dx = self.wavelength / cells_per_wavelength
        self.dy = self.dx

        # Computational domain
        self.x_min, self.x_max = x_bounds
        self.y_min, self.y_max = y_bounds

        self.nx = int(np.ceil(
            (self.x_max - self.x_min) / self.dx
        )) + 1

        self.ny = int(np.ceil(
            (self.y_max - self.y_min) / self.dy
        )) + 1

        # Coordinate arrays
        self.x = self.x_min + np.arange(self.nx) * self.dx
        self.y = self.y_min + np.arange(self.ny) * self.dy

        # 2D CFL stability limit
        self.dt_max = 1.0 / (
            C0 * np.sqrt(
                1.0 / self.dx**2 + 1.0 / self.dy**2
            )
        )

        self.dt = courant_factor * self.dt_max

        # TMz field arrays (float32 saves memory)
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

    def print_grid_info(self):
        print("\n=== FDTD YEE GRID INITIALIZED ===")
        print(f"Frequency: {self.frequency / 1e9:.3f} GHz")
        print(f"Wavelength: {self.wavelength * 1000:.3f} mm")
        print(f"Grid spacing dx: {self.dx * 1000:.3f} mm")
        print(f"Grid spacing dy: {self.dy * 1000:.3f} mm")
        print(f"Grid dimensions: {self.nx} x {self.ny}")
        print(f"Ez array shape: {self.Ez.shape}")
        print(f"Hx array shape: {self.Hx.shape}")
        print(f"Hy array shape: {self.Hy.shape}")
        print(f"Maximum time step: {self.dt_max * 1e12:.3f} ps")
        print(f"Chosen time step: {self.dt * 1e12:.3f} ps")
        print(f"Total grid cells: {self.nx * self.ny:,}")


if __name__ == "__main__":
    solver = FDTDSolver()
    solver.print_grid_info()
