import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver
from source import SourceConfig, ApertureSource, half_power_beamwidth


# --------------------------------------------------
# 1. SIMULATION CONFIGURATION
# --------------------------------------------------

frequency = 10e9
wavelength = 299792458.0 / frequency

solver = FDTDSolver(
    nx=250,
    ny=600,
    dx=1e-3,
    dy=1e-3,
    frequency=frequency,
    source_x=50,
    source_y=300,
    use_builtin_source=False
)

config = SourceConfig(
    frequency=frequency,
    aperture_width=0.12,
    steering_angle_deg=20,
    waveform="cw",
    amplitude=1.0,
    taper="hann"
)

source = ApertureSource(config)
source.configure_grid(solver)

# Observation plane, in front of the aperture.
observation_x = 140

if observation_x <= source.source_x:
    raise ValueError("Observation plane must be in front of the source.")

# --------------------------------------------------
# 2. FDTD SIMULATION AND FREQUENCY EXTRACTION
# --------------------------------------------------

period = 1.0 / frequency

warmup_steps = int(20 * period / solver.dt)
measurement_steps = int(40 * period / solver.dt)

print("Running FDTD simulation...")
print("Warm-up steps:", warmup_steps)
print("Measurement steps:", measurement_steps)

# Complex frequency-domain field accumulator.
field_phasor = np.zeros(solver.ny, dtype=complex)

total_steps = warmup_steps + measurement_steps

for step in range(total_steps):

    solver.step(source=source.inject)

    if step >= warmup_steps:
        field_phasor += (
            solver.Ez[observation_x, :]
            * np.exp(-1j * 2 * np.pi * frequency * solver.time)
        )

    if (step + 1) % 500 == 0:
        print(f"Completed {step + 1}/{total_steps} steps")

field_phasor /= measurement_steps

# --------------------------------------------------
# 3. ANGULAR SPECTRUM
# --------------------------------------------------

# Window the observation line to reduce edge effects.
spatial_window = np.hanning(solver.ny)

windowed_field = field_phasor * spatial_window

# Zero-padding interpolates the angular spectrum.
nfft = 8192

spectrum = np.fft.fftshift(
    np.fft.fft(windowed_field, n=nfft)
)

ky = 2 * np.pi * np.fft.fftshift(
    np.fft.fftfreq(nfft, d=solver.dy)
)

k0 = 2 * np.pi / wavelength

# Only propagating spatial frequencies are retained.
valid = np.abs(ky) <= k0

# With this temporal Fourier convention, positive
# physical observation angles correspond to negative ky.
angles = -np.rad2deg(
    np.arcsin(np.clip(ky[valid] / k0, -1.0, 1.0))
)

fdtd_magnitude = np.abs(spectrum[valid])

# Restrict comparison to the forward angular region.
forward = np.abs(angles) <= 80

angles = angles[forward]
fdtd_magnitude = fdtd_magnitude[forward]

order = np.argsort(angles)
angles = angles[order]
fdtd_magnitude = fdtd_magnitude[order]

fdtd_normalized = fdtd_magnitude / np.max(fdtd_magnitude)

fdtd_db = 20 * np.log10(
    np.maximum(fdtd_normalized, 1e-3)
)

# --------------------------------------------------
# 4. ANALYTICAL PATTERN
# --------------------------------------------------

analytical_linear, analytical_db = source.analytical_pattern(
    angles,
    dy=solver.dy
)

# --------------------------------------------------
# 5. BEAM PARAMETERS
# --------------------------------------------------

fdtd_hpbw, fdtd_left, fdtd_right = half_power_beamwidth(
    angles,
    fdtd_db
)

analytical_hpbw, analytical_left, analytical_right = (
    half_power_beamwidth(angles, analytical_db)
)

fdtd_peak_angle = angles[np.argmax(fdtd_db)]
analytical_peak_angle = angles[np.argmax(analytical_db)]

print("\n========== RADIATION PATTERN RESULTS ==========")

print(f"Expected steering angle: {config.steering_angle_deg:.2f} deg")
print(f"FDTD peak angle:         {fdtd_peak_angle:.2f} deg")
print(f"Analytical peak angle:   {analytical_peak_angle:.2f} deg")

print(f"\nFDTD HPBW:               {fdtd_hpbw:.2f} deg")
print(f"Analytical HPBW:         {analytical_hpbw:.2f} deg")

print("================================================")

# --------------------------------------------------
# 6. PLOT COMPARISON
# --------------------------------------------------

plt.figure(figsize=(11, 6))

plt.plot(
    angles,
    fdtd_db,
    label="FDTD angular spectrum",
    linewidth=2
)

plt.plot(
    angles,
    analytical_db,
    "--",
    label="Analytical aperture pattern",
    linewidth=2
)

plt.axvline(
    config.steering_angle_deg,
    color="black",
    linestyle=":",
    label="Expected steering angle"
)

plt.axhline(-3, color="gray", linestyle=":")

plt.xlabel("Observation angle (degrees)")
plt.ylabel("Normalized magnitude (dB)")
plt.title("FDTD vs Analytical Radiation Pattern at 10 GHz")

plt.xlim(-80, 80)
plt.ylim(-40, 2)
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig("fdtd_vs_analytical_pattern.png", dpi=300)
plt.show()

# --------------------------------------------------
# 7. SAVE NUMERICAL RESULTS
# --------------------------------------------------

np.savez(
    "fdtd_radiation_pattern_results.npz",
    angles=angles,
    fdtd_pattern_db=fdtd_db,
    analytical_pattern_db=analytical_db,
    fdtd_peak_angle=fdtd_peak_angle,
    analytical_peak_angle=analytical_peak_angle,
    fdtd_hpbw=fdtd_hpbw,
    analytical_hpbw=analytical_hpbw
)

print("\nSaved:")
print("fdtd_vs_analytical_pattern.png")
print("fdtd_radiation_pattern_results.npz")