
import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver


def main():
    solver = FDTDSolver()
    solver.print_grid_info()

    # Capture the continuous wave at different times
    snapshot_steps = [50, 100, 200, 400]
    snapshots = []

    for target_step in snapshot_steps:
        while solver.time_step < target_step:
            solver.step()

        snapshots.append(solver.Ez.copy())

    # Use a common colour scale for all snapshots
    vmax = max(
        np.max(np.abs(field)) for field in snapshots
    )
    vmin = -vmax

    extent = [
        solver.x[0], solver.x[-1],
        solver.y[0], solver.y[-1]
    ]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    for ax, field, step in zip(
        axes.flat, snapshots, snapshot_steps
    ):
        image = ax.imshow(
            field,
            extent=extent,
            origin="lower",
            cmap="RdBu_r",
            aspect="equal",
            vmin=vmin,
            vmax=vmax
        )

        time_ns = step * solver.dt * 1e9

        ax.set_title(
            f"Step {step} | Time = {time_ns:.3f} ns"
        )
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")

        # Mark the transmitter
        ax.plot(
            solver.x[solver.source_i],
            solver.y[solver.source_j],
            "ko",
            markersize=4,
            label="Transmitter"
        )

        ax.legend(loc="upper right")
        fig.colorbar(image, ax=ax, label="Ez (V/m)")

    fig.suptitle(
        "10 GHz TMz FDTD Continuous-Wave Propagation",
        fontsize=15
    )

    plt.tight_layout()
    plt.savefig("cw_propagation.png", dpi=200)
    plt.show()

    print("\nSaved cw_propagation.png")


if __name__ == "__main__":
    main()
