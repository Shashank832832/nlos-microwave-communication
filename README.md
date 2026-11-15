# NLOS Microwave Communication Using a Passive Reflector

## Abstract

This project studies a 10 GHz non-line-of-sight (NLOS) microwave link routed around an L-shaped corridor corner by a finite passive perfect-electric-conductor (PEC) reflector. It combines first-order analytical geometry and link calculations with a modular 2D TMz Yee-grid FDTD model. A directional finite-aperture source illuminates a tilted plate; receiver and off-axis line monitors measure cycle-averaged power-flow diagnostics while reflector tilt and electrical width are varied.

The Python results are comparative 2D simulations, not calibrated link-budget measurements. The separate CST model is a 3D verification effort and is not an execution dependency of Python.

## Problem and objectives

A direct Tx-to-Rx path is blocked by the corridor turn. The nominal reflector is centered at the corner with a 45-degree tangent, redirecting a +x incident beam toward +y. The project aims to:

- preserve a shared, explicit physical geometry and coordinate convention;
- integrate the canonical Member 2 FDTD solver and Member 3 directional source;
- compare receiver flux across configured reflector-angle offsets and widths;
- sample off-axis interception with comparable line-flux monitors;
- retain an analytical unobstructed-LOS Friis reference without mislabeling it as the reflected NLOS prediction; and
- provide reproducible CSV, figure, report, and presentation outputs.

## Working principle

At the nominal plate angle, specular reflection changes an incident +x propagation direction into +y. The finite PEC plate is modeled in the corridor's 2D top view. A transverse aperture source (initial width 0.12 m) uses a CW waveform, zero-degree steering, and Hann taper by default. The receiver monitor is approximately perpendicular to the expected reflected direction. Additional short line monitors sample power crossing off-axis observation planes.

## System architecture

`configs/*.yaml` provide the experiment settings. `src/experiments/simulation_factory.py` translates world coordinates to the solver's local grid, builds corridor/reflector PEC masks, and configures the source and sensors. The generic solver updates TMz fields; separate experiment, measurement, analysis, and visualization modules perform the sweeps and deliverable generation.

| Area | Responsibility |
|---|---|
| `src/geometry/` | Shared corridor landmarks, reflector endpoints, world/grid mapping |
| `src/fdtd/solver.py` | Canonical Member 2 TMz Yee-grid solver, Mur ABC, PEC mask, Poynting diagnostic |
| `src/sources/aperture_source.py` | Reused Member 3 CW/Gaussian aperture, taper, steering and pattern helpers |
| `src/analysis/` | Analytical geometry and explicitly unobstructed LOS reference |
| `src/measurements/` | Validated line monitors, approximate Poynting flux, relative dB metrics |
| `src/experiments/` | YAML validation, fresh simulation construction, baseline, tilt and width runs |
| `src/visualization/` | Separate plots for sweep trends, interception and baseline flow |
| `tests/` | Geometry, mapping, callback, numerical smoke and quick-pipeline tests |
| `cst_verification/` | Independent CST 3D workflow and future export comparison |
| `results/` | Generated experiment tables, figures and report |
| `deliverables/` | Project presentation, submission checklist and packaged results |

## Python model and numerical scope

The active solver stores `Ez[nx, ny]`, `Hx[nx, ny-1]`, and `Hy[nx-1, ny]`. It uses a CFL-limited time step, first-order Mur absorbing edges, and rasterized PEC nodes. World coordinates are translated by subtracting `x_min` and `y_min`; the same mapping is used for source indices, plate endpoints, monitors, and figure axes.

The analytical model reports direct free-space loss only as an unobstructed LOS reference. The actual reflected NLOS response is measured numerically with line-integrated normal Poynting flux. Relative flux is `10 log10(P/P_ref)` only for positive finite values; field-amplitude comparisons would instead use `20 log10(A/A_ref)`.

The default sweep covers offsets `[-15, -10, -5, 0, 5, 10, 15]` degrees around 45 degrees and widths `[5, 10, 15]` wavelengths. These values, source settings, monitors, runtime, grid, and output paths are configurable in YAML.

## Team contributions

- **Member 1:** Analytical corridor geometry and first-order electromagnetic/link calculations.
- **Member 2:** Generic 2D TMz FDTD Yee-grid solver, PEC rasterization, Mur boundaries, source callback, and approximate Poynting diagnostic.
- **Member 3:** Directional finite-aperture source, CW/Gaussian waveforms, tapering, steering, and radiation-pattern utilities.
- **Member 4:** Configuration-driven simulation integration, tilt/width experiments, receiver/off-axis measurements, relative power analysis, tables, plots, and experiment report.
- **Member 5:** Standalone CST 3D verification model and comparison workflow.

## Expected outputs

The full Member 4 run creates:

- `results/tables/tilt_sweep.csv`
- `results/tables/width_sweep.csv`
- `results/tables/off_axis_sensors.csv`
- `results/figures/tilt_vs_receiver_power.png`
- `results/figures/width_vs_receiver_power.png`
- `results/figures/off_axis_interception_heatmap.png`
- `results/figures/baseline_power_distribution.png`
- `results/reports/member4_experiment_summary.md`

The project handover presentation is `deliverables/NLOS_Microwave_Project_Report.pptx`; roster details remain explicitly pending unless supplied by the team. See [setup.md](setup.md) for tested installation and execution instructions.

The independent CST setup and normalized-export comparison format are documented in [cst_verification/README.md](cst_verification/README.md).

## Repository map

```text
configs/                 YAML baseline, quick, and final experiment settings
cst_verification/        Independent CST model workflow
deliverables/            Presentation, checklist, and packaged results
docs/                     Integration audit
results/                  Generated experiment tables, figures, and report
src/                      Active Python package
tests/                    Automated integration and pipeline tests
README.md                 Project overview
setup.md                  Environment and run guide
```

## Limitations and future work

This is a 2D TMz model and omits finite out-of-plane reflector height and 3D spreading. Flux is per unit depth, not watts/dBm. The Poynting helper spatially interpolates H onto E nodes but does not correct Yee half-time staggering. First-order Mur boundaries, staircased PEC, and ideal PEC corridor walls are approximations. The quick configuration checks software integration and artifact generation only; it does not validate electromagnetic accuracy. Future work includes grid/time convergence, improved absorbing boundaries and temporal centering, justified wall materials, and a documented comparison with the independent CST 3D model.
