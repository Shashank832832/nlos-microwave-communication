
import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver


def main():

    # -----------------------------------------
    # 1. Initialize two identical corridor models
    # -----------------------------------------

    print("Initializing corridor WITHOUT reflector...")

    solver_without = FDTDSolver(
        use_pec=False,
        use_walls=True
    )

    print("Initializing corridor WITH reflector...")

    solver_with = FDTDSolver(
        use_pec=True,
        use_walls=True
    )

    # Snapshot times
    snapshot_steps = [2000, 2800, 3600, 4000]

    fields_without = {}
    fields_with = {}

    # -----------------------------------------
    # 2. Run both simulations
    # -----------------------------------------

    print("\nRunning field comparison...")

    for step in range(1, max(snapshot_steps) + 1):

        solver_without.step()
        solver_with.step()

        if step in snapshot_steps:

            fields_without[step] = solver_without.Ez.copy()
            fields_with[step] = solver_with.Ez.copy()

            print(f"Captured step {step}")

    # -----------------------------------------
    # 3. Calculate common color scales
    # -----------------------------------------

    field_max = max(
        max(np.max(np.abs(fields_without[s])) for s in snapshot_steps),
        max(np.max(np.abs(fields_with[s])) for s in snapshot_steps)
    )

    difference_fields = {}

    for step in snapshot_steps:
        difference_fields[step] = (
            fields_with[step] - fields_without[step]
        )

    difference_max = max(
        np.max(np.abs(difference_fields[s]))
        for s in snapshot_steps
    )

    # Avoid zero color limits
    field_max = max(field_max, 1e-12)
    difference_max = max(difference_max, 1e-12)

    X, Y = np.meshgrid(
        solver_with.x,
        solver_with.y
    )

    # Mask PEC walls for display
    wall_mask = solver_with.wall_mask

    # -----------------------------------------
    # 4. Plot the three field distributions
    # -----------------------------------------

    fig, axes = plt.subplots(
        len(snapshot_steps),
        3,
        figsize=(17, 16)
    )

    for row, step in enumerate(snapshot_steps):

        time_ns = step * solver_with.dt * 1e9

        fields = [
            fields_without[step],
            fields_with[step],
            difference_fields[step]
        ]

        titles = [
            "Without reflector",
            "With reflector",
            "Difference field"
        ]

        for col in range(3):

            ax = axes[row, col]

            field = np.ma.masked_where(
                wall_mask,
                fields[col]
            )

            if col == 2:
                vmax = difference_max
            else:
                vmax = field_max

            mesh = ax.pcolormesh(
                X,
                Y,
                field,
                shading="auto",
                cmap="RdBu_r",
                vmin=-vmax,
                vmax=vmax
            )

            # Transmitter and receiver
            ax.scatter(-1, 0, color="blue", s=35)
            ax.scatter(0, 1, color="green", s=35)

            # Draw reflector in the reflector and difference plots
            if col != 0:

                half_length = solver_with.plate_length / 2

                x1 = -half_length * np.cos(
                    solver_with.plate_angle
                )
                y1 = -half_length * np.sin(
                    solver_with.plate_angle
                )

                x2 = half_length * np.cos(
                    solver_with.plate_angle
                )
                y2 = half_length * np.sin(
                    solver_with.plate_angle
                )

                ax.plot(
                    [x1, x2],
                    [y1, y2],
                    color="black",
                    linewidth=2
                )

            ax.set_title(
                f"{titles[col]}\nTime = {time_ns:.2f} ns"
            )

            ax.set_xlim(-2.05, 0.65)
            ax.set_ylim(-0.35, 2.05)
            ax.set_aspect("equal")

            ax.set_xlabel("X position (m)")
            ax.set_ylabel("Y position (m)")

            ax.grid(alpha=0.15)

            fig.colorbar(
                mesh,
                ax=ax,
                label="Ez (V/m)",
                fraction=0.046,
                pad=0.04
            )

    fig.suptitle(
        "10 GHz FDTD: Corridor Field Comparison",
        fontsize=17
    )

    fig.tight_layout(rect=[0, 0, 1, 0.97])

    plt.savefig(
        "corridor_field_comparison.png",
        dpi=200,
        bbox_inches="tight"
    )

    print("\nSaved corridor_field_comparison.png")

    plt.show()


if __name__ == "__main__":
    main()

