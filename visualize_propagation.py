
import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver


def main():
    solver = FDTDSolver()

    # Initialize a Gaussian pulse
    x0 = -1.0
    y0 = 0.0
    sigma = 0.03

    gaussian = np.exp(
        -(
            (solver.x[None, :] - x0)**2
            + (solver.y[:, None] - y0)**2
        ) / (2 * sigma**2)
    )

    solver.Ez[:] = gaussian.astype(np.float32)

    # Save the initial field and later snapshots
    snapshot_steps = [0, 100, 200, 400]
    snapshots = []

    for target_step in snapshot_steps:
        while solver.time_step < target_step:
            solver.step()

        snapshots.append(solver.Ez.copy())

    # Plot the four snapshots
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    extent = [
        solver.x[0], solver.x[-1],
        solver.y[0], solver.y[-1]
    ]

    for ax, field, step in zip(
        axes.flat, snapshots, snapshot_steps
    ):
        image = ax.imshow(
            field,
            extent=extent,
            origin="lower",
            cmap="RdBu_r",
            aspect="equal"
        )

        time_ns = step * solver.dt * 1e9

        ax.set_title(
            f"Step {step} | Time = {time_ns:.3f} ns"
        )
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")

        fig.colorbar(image, ax=ax, label="Ez (V/m)")

    fig.suptitle(
        "TMz FDTD: Gaussian Pulse Propagation",
        fontsize=15
    )

    plt.tight_layout()
    plt.savefig("wave_propagation.png", dpi=200)
    plt.show()

    print("Saved wave_propagation.png")


if __name__ == "__main__":
    main()
