
"""

Generates:
1. fdtd_field.png
2. poynting_distribution.png
3. member3_fdtd_results.npz
"""

import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver

from source import (
    SourceConfig,
    ApertureSource
)


def main():

    # ------------------------------------------
    # INITIALIZE FDTD SOLVER
    # ------------------------------------------

    solver = FDTDSolver(

        nx=200,
        ny=200,

        dx=1e-3,
        dy=1e-3,

        courant_factor=0.99,

        frequency=10e9,

        source_x=50,
        source_y=100,

        use_builtin_source=False

    )

    # ------------------------------------------
    # INITIALIZE DIRECTIONAL SOURCE
    # ------------------------------------------

    config = SourceConfig(

        frequency=10e9,

        aperture_width=0.12,

        steering_angle_deg=20.0,

        waveform="cw",

        taper="hann",

        amplitude=1.0

    )

    source = ApertureSource(config)

    source.configure_grid(solver)

    # ------------------------------------------
    # SOURCE INFORMATION
    # ------------------------------------------

    print("\nMEMBER 3 SOURCE CONFIGURATION")
    print("-----------------------------")

    print(
        "Frequency:",
        solver.frequency / 1e9,
        "GHz"
    )

    print(
        "Wavelength:",
        solver.wavelength * 100,
        "cm"
    )

    print(
        "Grid spacing:",
        solver.dx * 1000,
        "mm"
    )

    print(
        "Time step:",
        solver.dt,
        "seconds"
    )

    print(
        "Aperture width:",
        config.aperture_width * 100,
        "cm"
    )

    print(
        "Aperture samples:",
        len(source.y_positions)
    )

    print(
        "Steering angle:",
        config.steering_angle_deg,
        "degrees"
    )

    # ------------------------------------------
    # RUN FDTD SIMULATION
    # ------------------------------------------

    total_steps = 2000

    print("\nStarting FDTD simulation...")

    for step in range(total_steps):

        solver.step(
            source=source.inject
        )

        if step % 500 == 0:

            print(
                "Completed:",
                step,
                "/",
                total_steps
            )

    print("\nSimulation completed.")

    # ------------------------------------------
    # ELECTRIC FIELD DISTRIBUTION
    # ------------------------------------------

    plt.figure(figsize=(9, 7))

    plt.imshow(

        solver.Ez.T,

        origin="lower",

        extent=[

            0,
            solver.nx * solver.dx,

            0,
            solver.ny * solver.dy

        ],

        aspect="equal",

        cmap="RdBu_r"

    )

    plt.colorbar(
        label="Electric field Ez"
    )

    plt.xlabel("X position (m)")
    plt.ylabel("Y position (m)")

    plt.title(
        "2D TMz FDTD Electric Field Distribution"
    )

    plt.tight_layout()

    plt.savefig(
        "fdtd_field.png",
        dpi=200
    )

    plt.close()

    # ------------------------------------------
    # POYNTING VECTOR DISTRIBUTION
    # ------------------------------------------

    sx, sy = solver.calculate_poynting()

    poynting_magnitude = np.sqrt(
        sx**2 + sy**2
    )

    plt.figure(figsize=(9, 7))

    plt.imshow(

        poynting_magnitude.T,

        origin="lower",

        extent=[

            0,
            solver.nx * solver.dx,

            0,
            solver.ny * solver.dy

        ],

        aspect="equal",

        cmap="inferno"

    )

    plt.colorbar(
        label="Poynting magnitude (relative)"
    )

    plt.xlabel("X position (m)")
    plt.ylabel("Y position (m)")

    plt.title(
        "Electromagnetic Energy Flow Distribution"
    )

    plt.tight_layout()

    plt.savefig(
        "poynting_distribution.png",
        dpi=200
    )

    plt.close()

    # ------------------------------------------
    # SAVE SIMULATION DATA
    # ------------------------------------------

    np.savez(

        "member3_fdtd_results.npz",

        Ez=solver.Ez,

        Hx=solver.Hx,

        Hy=solver.Hy,

        Sx=sx,

        Sy=sy,

        dx=solver.dx,

        dy=solver.dy,

        dt=solver.dt,

        frequency=solver.frequency,

        source_y=source.y_positions,

        source_weights=source.weights

    )

    print("\nGenerated files:")

    print("1. fdtd_field.png")
    print("2. poynting_distribution.png")
    print("3. member3_fdtd_results.npz")


if __name__ == "__main__":

    main()
