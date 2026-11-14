
import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver


def main():

    # -----------------------------------------
    # 1. Experiment settings
    # -----------------------------------------

    angles = [30, 35, 40, 45, 50, 55, 60]

    total_steps = 4000
    samples_for_rms = 1000

    receiver_x = 0.0
    receiver_y = 1.0

    rms_results = []

    print("\n=== REFLECTOR ANGLE SWEEP ===")
    print("Frequency: 10 GHz")
    print("Plate length: 0.30 m")
    print("Corridor walls: Enabled")
    print(f"Simulation steps per angle: {total_steps}")

    # -----------------------------------------
    # 2. Run simulation for each angle
    # -----------------------------------------

    for angle in angles:

        print(f"\nRunning simulation at {angle} degrees...")

        solver = FDTDSolver(
            use_pec=True,
            use_walls=True,
            plate_angle_deg=angle
        )

        # Find nearest receiver grid point
        rx_i = np.argmin(
            np.abs(solver.x - receiver_x)
        )

        rx_j = np.argmin(
            np.abs(solver.y - receiver_y)
        )

        receiver_values = []

        # Run FDTD simulation
        for step in range(total_steps):

            solver.step()

            receiver_values.append(
                solver.Ez[rx_j, rx_i]
            )

            if (step + 1) % 1000 == 0:
                print(
                    f"  Completed {step + 1}/{total_steps}"
                )

        receiver_values = np.array(receiver_values)

        # RMS over the final 1000 samples
        receiver_rms = np.sqrt(
            np.mean(
                receiver_values[-samples_for_rms:] ** 2
            )
        )

        rms_results.append(receiver_rms)

        print(
            f"  Angle: {angle} degrees | "
            f"Receiver RMS: {receiver_rms:.6e} V/m"
        )

        del solver

    rms_results = np.array(rms_results)

    # -----------------------------------------
    # 3. Print final results
    # -----------------------------------------

    print("\n=== FINAL ANGLE SWEEP RESULTS ===")

    for angle, value in zip(angles, rms_results):

        print(
            f"{angle:2d} degrees : {value:.6e} V/m"
        )

    best_index = np.argmax(rms_results)

    print("\nHighest measured receiver RMS:")
    print(f"Angle: {angles[best_index]} degrees")
    print(f"RMS: {rms_results[best_index]:.6e} V/m")

    # -----------------------------------------
    # 4. Save numerical results
    # -----------------------------------------

    results = np.column_stack(
        (angles, rms_results)
    )

    np.savetxt(
        "angle_sweep_results.csv",
        results,
        delimiter=",",
        header="Angle_degrees,Receiver_RMS_Ez_V_per_m",
        comments="",
        fmt=["%d", "%.8e"]
    )

    print("\nSaved angle_sweep_results.csv")

    # -----------------------------------------
    # 5. Plot angle versus receiver RMS
    # -----------------------------------------

    plt.figure(figsize=(10, 6))

    plt.plot(
        angles,
        rms_results,
        marker="o",
        linewidth=2,
        markersize=8,
        label="Receiver RMS electric field"
    )

    plt.axvline(
        x=45,
        linestyle="--",
        label="Theoretical angle: 45 degrees"
    )

    plt.scatter(
        angles[best_index],
        rms_results[best_index],
        s=120,
        marker="*",
        label=f"Highest RMS: {angles[best_index]} degrees"
    )

    plt.xlabel("Reflector Angle (degrees)")
    plt.ylabel("Receiver RMS Electric Field (V/m)")

    plt.title(
        "Effect of Reflector Orientation "
        "on Receiver Electric Field"
    )

    plt.xticks(angles)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "angle_sweep_results.png",
        dpi=300
    )

    print("Saved angle_sweep_results.png")

    plt.show()


if __name__ == "__main__":
    main()
