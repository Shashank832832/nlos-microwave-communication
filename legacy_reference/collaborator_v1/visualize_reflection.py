
import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver


def main():
    solver = FDTDSolver()
    solver.print_grid_info()

    # Steps selected to observe the wave approaching
    # and interacting with the reflector.
    snapshot_steps = [700, 1300, 1900, 2200]
    snapshots = []

    for target_step in snapshot_steps:
        while solver.time_step < target_step:
            solver.step()

        snapshots.append(solver.Ez.copy())

        print(
            f"Captured step {solver.time_step}, "
            f"time = {solver.time_step * solver.dt * 1e9:.3f} ns"
        )

    # Common colour scale
    vmax = max(
        np.max(np.abs(field)) for field in snapshots
    )

    extent = [
        solver.x[0], solver.x[-1],
        solver.y[0], solver.y[-1]
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    for ax, field, step in zip(
        axes.flat, snapshots, snapshot_steps
    ):
        image = ax.imshow(
            field,
            extent=extent,
            origin="lower",
            cmap="RdBu_r",
            aspect="equal",
            vmin=-vmax,
            vmax=vmax
        )

        # Draw the finite PEC reflector
        half = solver.plate_length / 2
        angle = solver.plate_angle

        x1 = -half * np.cos(angle)
        y1 = -half * np.sin(angle)
        x2 = half * np.cos(angle)
        y2 = half * np.sin(angle)

        ax.plot(
            [x1, x2],
            [y1, y2],
            color="black",
            linewidth=3,
            label="PEC reflector"
        )

        # Mark transmitter
        ax.plot(
            solver.x[solver.source_i],
            solver.y[solver.source_j],
            "ko",
            markersize=5,
            label="Transmitter"
        )

        # Mark intended receiver
        ax.plot(
            0.0, 1.0,
            "g^",
            markersize=8,
            label="Intended receiver"
        )

        time_ns = step * solver.dt * 1e9

        ax.set_title(
            f"Step {step} | Time = {time_ns:.3f} ns"
        )
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.legend(loc="upper right")

        fig.colorbar(image, ax=ax, label="Ez (V/m)")

    fig.suptitle(
        "10 GHz TMz FDTD: Reflection from a Finite PEC Plate",
        fontsize=15
    )

    plt.tight_layout()
    plt.savefig("pec_reflection.png", dpi=200)
    plt.show()

    print("\nSaved pec_reflection.png")


if __name__ == "__main__":
    main()
