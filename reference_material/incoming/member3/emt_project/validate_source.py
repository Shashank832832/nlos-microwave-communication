
"""

Tests:
1. Directional aperture radiation pattern.
2. CW excitation.
3. Gaussian excitation.
4. Half Power Beamwidth.

Requires:
    source.py
    fdtd_solver.py
"""

import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver

from source import (
    SourceConfig,
    ApertureSource,
    half_power_beamwidth
)


def main():

    # ------------------------------------------
    # INITIALIZE FDTD GRID
    # ------------------------------------------

    solver = FDTDSolver(

        nx=200,
        ny=200,

        dx=1e-3,
        dy=1e-3,

        frequency=10e9,

        use_builtin_source=False
    )

    # ------------------------------------------
    # CONFIGURE APERTURE SOURCE
    # ------------------------------------------

    config = SourceConfig(

        frequency=10e9,

        aperture_width=0.12,

        steering_angle_deg=20.0,

        waveform="cw",

        taper="hann"

    )

    source = ApertureSource(config)

    source.configure_grid(solver)

    # ------------------------------------------
    # ANALYTICAL RADIATION PATTERN
    # ------------------------------------------

    angles = np.linspace(
        -90,
        90,
        1801
    )

    linear, pattern_db = source.analytical_pattern(
        angles
    )

    hpbw, left, right = half_power_beamwidth(
        angles,
        pattern_db
    )

    plt.figure(figsize=(9, 5))

    plt.plot(
        angles,
        pattern_db,
        label="Analytical aperture pattern"
    )

    plt.axvline(
        config.steering_angle_deg,
        linestyle="--",
        label="Steering angle"
    )

    plt.axhline(
        -3,
        linestyle=":",
        color="gray",
        label="-3 dB level"
    )

    if left is not None:

        plt.axvline(
            left,
            linestyle=":",
            color="gray"
        )

    if right is not None:

        plt.axvline(
            right,
            linestyle=":",
            color="gray"
        )

    plt.xlabel("Observation angle (degrees)")
    plt.ylabel("Normalized field magnitude (dB)")

    plt.title(
        "10 GHz Directional Aperture Radiation Pattern"
    )

    plt.xlim(-90, 90)
    plt.ylim(-60, 2)

    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        "radiation_pattern.png",
        dpi=200
    )

    plt.close()

    # ------------------------------------------
    # CW AND GAUSSIAN WAVEFORMS
    # ------------------------------------------

    times = np.linspace(
        0,
        15 / config.frequency,
        2500
    )

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(9, 7),
        sharex=True
    )

    for ax, waveform in zip(
        axes,
        ["cw", "gaussian"]
    ):

        test_config = SourceConfig(

            frequency=10e9,

            aperture_width=0.12,

            steering_angle_deg=20.0,

            waveform=waveform,

            taper="uniform"

        )

        test_source = ApertureSource(
            test_config
        )

        test_source.configure_grid(solver)

        centre = len(test_source.weights) // 2
        edge = 0

        values = np.array([

            test_source.element_values(t)

            for t in times

        ])

        ax.plot(
            times * 1e9,
            values[:, centre],
            label="Centre element"
        )

        ax.plot(
            times * 1e9,
            values[:, edge],
            label="Edge element"
        )

        ax.set_title(
            waveform.upper() + " Excitation"
        )

        ax.set_ylabel("Ez amplitude")

        ax.grid(True, alpha=0.3)
        ax.legend()

    axes[-1].set_xlabel("Time (ns)")

    fig.tight_layout()

    fig.savefig(
        "source_waveforms.png",
        dpi=200
    )

    plt.close(fig)

    # ------------------------------------------
    # SAVE NUMERICAL RESULTS
    # ------------------------------------------

    np.savez(

        "source_validation.npz",

        angles_deg=angles,

        analytical_linear=linear,

        analytical_db=pattern_db,

        aperture_y_m=source.y_positions,

        aperture_weights=source.weights

    )

    # ------------------------------------------
    # PRINT RESULTS
    # ------------------------------------------

    print("\nSOURCE VALIDATION RESULTS")
    print("-------------------------")

    print(
        "Frequency:",
        config.frequency / 1e9,
        "GHz"
    )

    print(
        "Wavelength:",
        source.wavelength * 100,
        "cm"
    )

    print(
        "Aperture width:",
        config.aperture_width * 100,
        "cm"
    )

    print(
        "Aperture width/lambda:",
        config.aperture_width / source.wavelength
    )

    print(
        "Steering angle:",
        config.steering_angle_deg,
        "degrees"
    )

    print(
        "Aperture elements:",
        len(source.weights)
    )

    print(
        "Analytical HPBW:",
        round(hpbw, 3),
        "degrees"
    )

    print("\nGenerated:")
    print("radiation_pattern.png")
    print("source_waveforms.png")
    print("source_validation.npz")


if __name__ == "__main__":

    main()
