# Integration audit

## Incoming source review

- `reference_material/incoming/member2/fdtd_solver.py` is the canonical solver candidate. It uses `Ez[nx, ny]`, `Hx[nx, ny - 1]`, and `Hy[nx - 1, ny]`, advances TMz fields with a CFL-derived time step, applies first-order Mur boundaries, rasterizes finite PEC segments, accepts `step(source=callback)` / `run(..., source=callback)`, and supplies an approximate Poynting diagnostic.
- `reference_material/incoming/member2/README_INTEGRATION.md` documents that API and explicitly limits the Poynting calculation: H is interpolated spatially to E nodes, but Yee half-time staggering is not corrected.
- `reference_material/incoming/member2/integration_example.py` demonstrates the generic callback contract, but its placeholder source is not the final aperture implementation.
- `reference_material/incoming/member3/emt_project/source.py` defines `SourceConfig`, `ApertureSource`, aperture discretization/tapering, CW and Gaussian waveforms, beam steering, analytical patterns, and HPBW. `ApertureSource.inject(solver, time_seconds)` matches Member 2's callback signature and writes Ez only.
- Member 3's runner, validation script, and FDTD radiation-pattern script demonstrate standalone source use; their 20-degree steering setup is not appropriate for the corridor's initial +x propagation, so the integrated baseline must use 0 degrees.
- `reference_material/incoming/member3/emt_project/integration_example.py` is an older illustrative interface, not a compatible entry point: it expects `source.inject(ez=..., time_step=..., x_index=..., y_indices=...)`, refers to source attributes absent from the delivered `source.py`, and passes an unsupported `num_elements` argument. The delivered `ApertureSource.inject(solver, time_seconds)` is the interface compatible with Member 2's solver and is what the active factory uses.
- SHA-256 comparison confirmed Member 2's and Member 3's incoming `fdtd_solver.py` copies are identical (`8940676205bac4a92e196344ef90544a57e9b2679e1e56ffea3b926d64a00a51`). The repository-root `fdtd_solver.py` is not identical.

## Existing project geometry and solver conflicts

- The root `geometry.py` provides the desired physical landmarks: Tx `(-1, 0) m`, reflector center `(0, 0) m`, Rx `(0, 1) m`, 0.30 m plate tangent at +45 degrees, and corridor arms `[-2, 0] x [-0.3, 0.3] m` and `[-0.3, 0.3] x [0, 2] m`. Its reflector endpoint helper agrees with the specified tangent convention.
- The root analytical model distinguishes unobstructed direct Friis loss from the reflected NLOS path and should retain that distinction.
- The root `fdtd_solver.py` stores fields with y as the first array dimension (`Ez[ny, nx]`) and has different step/source APIs. Its active use alongside the incoming implementation would silently transpose coordinates/fields. It is therefore excluded from the active package.
- The root solver's old comparisons and visualizers are coupled to that implementation and are retained as legacy references rather than imported by experiments.
- For the canonical solver's local origin, physical positions must be translated by `x_local = x_world - x_min`, `y_local = y_world - y_min`, then rounded by `dx`/`dy`. Under the baseline bounds this maps Tx to `(1.0, 0.3) m`, the reflector center to `(2.0, 0.3) m`, and Rx to `(2.0, 1.3) m`.
- The baseline directional source is a vertical aperture in the transverse y direction, positioned on the Tx x coordinate and centered at Tx y. Its 0-degree steering points along +x; source aperture limits must remain inside the grid and clear of PEC.

## PEC, channel openings, and field diagnostics

- The canonical solver's PEC mask acts on Ez nodes. A world-coordinate geometry adapter can therefore rasterize corridor regions outside the L-shaped free-space arms while leaving the horizontal mouth at the x-min boundary and vertical mouth at the y-max boundary clear for Mur absorption. This boundary/opening convention must be tested.
- The collaborator root solver is not an alternative to this adapter: its wall treatment and array layout differ.
- `calculate_poynting()` forms `Sx = -Ez * Hy` and `Sy = Ez * Hx` after spatially interpolating H onto E nodes. It does not time-center the leapfrog fields; its instantaneous result is approximate. Cycle averaging improves measurement stability but does not remove this temporal-staggering error.
- The model is 2-D TMz. Flux integrated along a 2-D line is per unit depth, not calibrated total power in watts or dBm. The physical 3-D reflector height is not represented independently.
- First-order Mur boundaries, staircased PEC, finite resolution, and ideal PEC walls are additional numerical/modeling limits. Electromagnetic accuracy requires convergence and/or comparison with the separate CST model; a quick run validates software flow only.

## Integration decisions

1. Copy the incoming Member 2 solver and Member 3 source unchanged into `src/fdtd/solver.py` and `src/sources/aperture_source.py`; adapt project-specific behavior in other modules.
2. Keep the existing root files and incoming originals intact. Move root collaborators' incompatible solver-dependent scripts into a named legacy-reference area; do not import them from `src/`.
3. Use a single YAML-backed experiment configuration and a coordinate mapper for sources, PEC geometry, sensors, and plotting.
4. Put monitoring, line-flux sampling, sweep orchestration, dB comparisons, plots, generated reports, and tests outside the generic solver.
