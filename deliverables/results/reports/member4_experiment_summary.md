# Member 4 experiment summary

## Geometry and baseline assumptions

The simulation uses a 10 GHz-class 2D TMz model (configured frequency: 1e+10 Hz) of a PEC L corridor. Horizontal arm: x=(-2.0, 0.0) m, y=(-0.3, 0.3) m; vertical arm: x=(-0.3, 0.3) m, y=(0.0, 2.0) m. Tx=(-1.0, 0.0) m, reflector center=(0.0, 0.0) m, and Rx=(0.0, 1.0) m. The nominal reflector is 0.3000 m wide, 0.3000 m high as a physical design parameter, and has a 45.0° tangent angle. Its height is not represented independently in the 2D top-view solver.

The active engine is the canonical Member 2 solver, with first-order Mur absorbing boundaries. PEC walls are masked outside the open L-shaped corridor; the horizontal x-min and vertical y-max channel mouths remain open. Negative world coordinates are translated to solver-local coordinates by subtracting the configured domain minima before index conversion.

## Source, grid, and duration

Member 3's aperture source uses waveform `cw`, 1.0 amplitude, 0.12 m width, 0.0° steering, and `hann` taper. The baseline uses 0° steering so the initial beam travels along +x. The grid uses 20 cells per wavelength, dx=dy=0.00149896 m, and CFL time step dt=3.50018e-12 s. Each run uses 75 warm-up cycles and 12 measurement cycles. The baseline used 2486 steps total (2143 warm-up and 343 measurement); its measured runtime was 179.755 s.

## Sweep configurations

Tilt offsets (from nominal): -15°, -10°, -5°, 0°, 5°, 10°, 15°. Absolute angles use nominal angle + offset. Widths: 5 lambda, 10 lambda, 15 lambda, converted using lambda=c/f. Every case creates a new solver and changes only its requested reflector parameter.

## Measurement and dB methodology

Receiver and off-axis readings are line-integrated normal components of the solver's approximate Poynting vector averaged over the measurement window. The receiver monitor center is (0.0, 0.8) m, normal (0.0, 1.0), and integration length 0.4 m. The configured off-axis line monitors lie within the vertical corridor around the expected reflected +y direction; their positions, normals, fluxes, and comparisons are in `off_axis_sensors.csv`.

Relative flux is `10 log10(measured_flux/reference_flux)` for positive finite per-unit-depth fluxes. Nonpositive or invalid values are reported as NaN rather than converted to a misleading dB result. The 2D line integral is W/m per unit depth, not calibrated total watts or dBm. The analytical unobstructed direct Friis reference is 55.46 dB at 1.414 m and is not a prediction of the reflected NLOS receiver power.

## Results and observations

- Baseline receiver flux: 1.4239973e-05 W/m per unit depth.
- Highest measured receiver flux in the configured tilt set: offset 0°.
- Highest measured receiver flux in the configured width set: 15 lambda.
- Configured measurement records: 7 tilt cases and 3 width cases.
- Failed or excluded simulations: none recorded. A simulation exception stops the runner and is surfaced; incomplete CSV/report output must not be interpreted as a completed run.

## Numerical and physical limitations

`calculate_poynting()` spatially interpolates H to E locations but does not correct Yee half-time staggering. Cycle averaging is a stability aid, not a temporal-centering correction. Mur boundaries are first order; PEC edges are staircased; ideal PEC walls and material properties are simplified; and the 2D model omits finite reflector height and all out-of-plane spreading. Results are relative diagnostics only. A quick/debug run validates software/data flow, not electromagnetic accuracy. Final claims require grid/time convergence and separately documented comparison against the CST 3D model.
