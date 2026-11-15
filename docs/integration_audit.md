# Integration audit

## Solver and source integration

- The active FDTD engine is the canonical Member 2 solver in `src/fdtd/solver.py`. It preserves `Ez[nx, ny]`, `Hx[nx, ny - 1]`, and `Hy[nx - 1, ny]`, uses CFL-limited time stepping and first-order Mur boundaries, rasterizes PEC geometry, and accepts an external source callback.
- The active directional source is Member 3's `ApertureSource` in `src/sources/aperture_source.py`. Its `inject(solver, time_seconds)` callback works with the solver's `step(source=...)` and `run(..., source=...)` interfaces. The corridor baseline steers at 0 degrees toward +x.
- The duplicate incoming solver copies were byte-identical; the incompatible y-first collaborator solver and its comparison/visualization scripts are not part of the active package. Redundant archived copies and obsolete root modules have since been removed.

## Geometry and coordinates

- Shared geometry is defined in `src/geometry/project_geometry.py`; the baseline landmarks are Tx `(-1, 0) m`, reflector center `(0, 0) m`, and Rx `(0, 1) m`. The 0.30 m reflector tangent is +45 degrees.
- `src/geometry/grid_mapping.py` translates world coordinates with `x_local = x_world - x_min` and `y_local = y_world - y_min`, then rounds by `dx` and `dy`. This mapping is used for the source, PEC geometry, monitors, and plots.
- Corridor PEC walls leave the horizontal x-min and vertical y-max channel mouths open for absorbing boundaries; tests cover both openings.

## Measurements and limitations

- The solver's approximate Poynting diagnostic forms `Sx = -Ez * Hy` and `Sy = Ez * Hx` after spatially interpolating H onto E nodes. It does not time-center the leapfrog fields, so instantaneous flux is approximate. Cycle averaging improves stability but does not remove this temporal-staggering error.
- The model is 2D TMz. Line-integrated flux is per unit depth, not calibrated total power in watts or dBm; the physical 3D reflector height is not independently represented.
- First-order Mur boundaries, staircased PEC, finite resolution, and ideal PEC walls limit numerical fidelity. Quick runs validate software flow only. Electromagnetic validation requires convergence work and/or comparison with the separate CST model.

## Architecture

The generic solver remains independent of experiment logic. YAML-backed configuration, coordinate mapping, source construction, sensor validation, line-flux sampling, sweeps, dB metrics, plots, generated reports, and tests live in their respective `src/` modules. `reference_material/` and `legacy_reference/` archives are intentionally excluded from the cleaned project.
