
import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver


def main():

    # -----------------------------------------
    # 1. Initialize both simulations
    # -----------------------------------------

    print("Running simulation WITHOUT reflector...")
    free_solver = FDTDSolver(
        use_pec=False,
        use_walls=True
    )

    print("Running simulation WITH reflector...")
    pec_solver = FDTDSolver(
        use_pec=True,
        use_walls=True
    )

    # Receiver coordinates
    receiver_x = 0.0
    receiver_y = 1.0

    # Find the nearest FDTD grid point to the receiver
    rx_i = np.argmin(np.abs(pec_solver.x - receiver_x))
    rx_j = np.argmin(np.abs(pec_solver.y - receiver_y))

    actual_rx_x = pec_solver.x[rx_i]
    actual_rx_y = pec_solver.y[rx_j]

    print("\n=== RECEIVER MONITOR ===")
    print(f"Requested position: ({receiver_x}, {receiver_y}) m")
    print(f"Actual grid position: ({actual_rx_x:.5f}, {actual_rx_y:.5f}) m")
    print(f"Grid indices: i={rx_i}, j={rx_j}")

    # -----------------------------------------
    # 2. Run both simulations
    # -----------------------------------------

    total_steps = 4000

    free_receiver = []
    pec_receiver = []
    time_values = []

    print("\nRunning both simulations...")

    for step in range(total_steps):

        free_solver.step()
        pec_solver.step()

        # Record Ez at the receiver
        free_receiver.append(free_solver.Ez[rx_j, rx_i])
        pec_receiver.append(pec_solver.Ez[rx_j, rx_i])

        time_values.append(
            (step + 1) * pec_solver.dt * 1e9
        )

        if (step + 1) % 500 == 0:
            print(f"Completed {step + 1}/{total_steps} steps")

    free_receiver = np.array(free_receiver)
    pec_receiver = np.array(pec_receiver)
    time_values = np.array(time_values)

    # Difference between fields
    scattered_receiver = pec_receiver - free_receiver

    # -----------------------------------------
    # 3. Calculate RMS values
    # -----------------------------------------

    # Use the final 1000 samples for RMS calculation
    # This excludes much of the initial source ramp-up.

    samples_for_rms = 1000

    free_rms = np.sqrt(
        np.mean(free_receiver[-samples_for_rms:] ** 2)
    )

    pec_rms = np.sqrt(
        np.mean(pec_receiver[-samples_for_rms:] ** 2)
    )

    scattered_rms = np.sqrt(
        np.mean(scattered_receiver[-samples_for_rms:] ** 2)
    )

    print("\n=== RECEIVER FIELD RESULTS ===")
    print(f"Corridor without reflector RMS Ez: {free_rms:.6e} V/m")
    print(f"Corridor with reflector RMS Ez:    {pec_rms:.6e} V/m")
    print(f"Difference-field RMS Ez:           {scattered_rms:.6e} V/m")

    print(
        f"Measurement interval: "
        f"{time_values[-samples_for_rms]:.3f} ns "
        f"to {time_values[-1]:.3f} ns"
    )

    
    # -----------------------------------------
    # 4. Plot receiver field versus time
    # -----------------------------------------

    fig1, axes = plt.subplots(2, 1, figsize=(12, 9))

    axes[0].plot(
        time_values,
        free_receiver,
        label="Corridor without reflector",
        linewidth=1
    )

    axes[0].plot(
        time_values,
        pec_receiver,
        label="Corridor with reflector",
        linewidth=1
    )

    axes[0].set_title("Electric Field at Receiver")
    axes[0].set_xlabel("Time (ns)")
    axes[0].set_ylabel("Ez (V/m)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(
        time_values,
        scattered_receiver,
        color="purple",
        linewidth=1
    )

    axes[1].set_title("Reflector-Induced Field at Receiver")
    axes[1].set_xlabel("Time (ns)")
    axes[1].set_ylabel("Difference in Ez (V/m)")
    axes[1].grid(True, alpha=0.3)

    fig1.suptitle(
        "10 GHz FDTD: Receiver Field Comparison",
        fontsize=15
    )

    fig1.tight_layout()
    fig1.savefig("receiver_field_comparison.png", dpi=200)

    # -----------------------------------------
    # 5. Plot RMS comparison
    # -----------------------------------------

    labels = [
        "No reflector",
        "With reflector",
        "Difference field"
    ]

    rms_values = [
        free_rms,
        pec_rms,
        scattered_rms
    ]

    fig2, ax = plt.subplots(figsize=(9, 5))

    bars = ax.bar(labels, rms_values)

    ax.set_ylabel("RMS Electric Field (V/m)")
    ax.set_title("Receiver RMS Electric Field Comparison")
    ax.grid(axis="y", alpha=0.3)

    for bar, value in zip(bars, rms_values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.3e}",
            ha="center",
            va="bottom"
        )

    fig2.tight_layout()
    fig2.savefig("receiver_rms_comparison.png", dpi=200)

    # -----------------------------------------
    # 6. Display both graphs
    # -----------------------------------------

    print("\nSaved receiver_field_comparison.png")
    print("Saved receiver_rms_comparison.png")

    plt.show()


if __name__ == "__main__":
    main()
