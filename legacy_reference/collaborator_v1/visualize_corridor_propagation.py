
import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver


def main():

    # Enable both corridor walls and the PEC reflector
    solver = FDTDSolver(
        use_pec=True,
        use_walls=True
    )

    solver.print_grid_info()

    # Capture fields at selected time steps
    snapshot_steps = [2000, 2400, 2800, 3200, 3600, 4000]
    snapshots = {}

    print("\nRunning corridor propagation simulation...")

    for step in range(1, max(snapshot_steps) + 1):

        solver.step()

        if step in snapshot_steps:
            snapshots[step] = solver.Ez.copy()
            print(f"Captured snapshot at step {step}")

    # Use a common color scale for all snapshots
    vmax = max(
        np.max(np.abs(field))
        for field in snapshots.values()
    )

    X, Y = np.meshgrid(solver.x, solver.y)

    fig, axes = plt.subplots(2, 3, figsize=(17, 10))

    for ax, step in zip(axes.flat, snapshot_steps):

        field = np.ma.masked_where(
            solver.wall_mask,
            snapshots[step]
        )

        image = ax.pcolormesh(
            X,
            Y,
            field,
            shading="auto",
            cmap="RdBu_r",
            vmin=-vmax,
            vmax=vmax
        )

        # Mark transmitter and receiver
        ax.scatter(-1, 0, color="blue", s=45, label="Tx")
        ax.scatter(0, 1, color="green", s=45, label="Rx")

        # Draw the reflector
        half_length = solver.plate_length / 2

        x1 = -half_length * np.cos(solver.plate_angle)
        y1 = -half_length * np.sin(solver.plate_angle)
        x2 = half_length * np.cos(solver.plate_angle)
        y2 = half_length * np.sin(solver.plate_angle)

        ax.plot(
            [x1, x2],
            [y1, y2],
            color="black",
            linewidth=2
        )

        time_ns = step * solver.dt * 1e9

        ax.set_title(
            f"Step {step} | Time {time_ns:.2f} ns"
        )

        ax.set_xlim(-2.05, 0.65)
        ax.set_ylim(-0.35, 2.05)
        ax.set_aspect("equal")
        ax.set_xlabel("X position (m)")
        ax.set_ylabel("Y position (m)")
        ax.grid(alpha=0.15)

    fig.colorbar(
        image,
        ax=axes.ravel().tolist(),
        label="Ez (V/m)",
        shrink=0.85
    )

    fig.suptitle(
        "10 GHz Electromagnetic Wave Propagation "
        "in an L-Shaped Corridor",
        fontsize=15
    )

    plt.savefig(
        "corridor_propagation.png",
        dpi=200,
        bbox_inches="tight"
    )

    print("\nSaved corridor_propagation.png")

    plt.show()


if __name__ == "__main__":
    main()
