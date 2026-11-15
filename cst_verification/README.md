# CST Studio Suite 2026 — standalone verification workflow

CST is a separate 3D verification model. The Python FDTD package neither imports CST APIs nor reads CST project files. No CST simulation result is included in the generated Python report or presentation unless the project team runs CST and exports data.

## Export format for later comparison

Export normalized positive linear power/flux values to CSV with exactly these required columns:

```csv
case_type,case_value,sensor_name,normalized_power
baseline,0,off_axis_center_mid,1.0
tilt,5,off_axis_center_mid,0.82
```

Include one `case_type=baseline` row per sensor and rows for the tested `tilt` offset (degrees) or `width` (wavelengths). `normalized_power` must be a positive linear power-like quantity normalized consistently for each sensor, not dB or field amplitude. Sensor names must match the Python `off_axis_sensors.csv`. The comparator computes `10 log10(case/baseline)` and writes matched trends to CSV; it does not merge engines or claim absolute CST/Python agreement.

From the repository root, after both exports exist:

```powershell
python -m src.analysis.cst_comparison cst_export.csv --python-csv results/tables/off_axis_sensors.csv --case-type tilt --case-value 5 --output results/tables/cst_python_comparison.csv
```

The comparator is exercised with a synthetic schema test only; a real CST export has not been produced or validated by this Python task.

Use CST for two progressively harder models. Save separate projects and keep a written record of all solver settings.

## Model A: isolated finite-plate reflection (first CST milestone)
Purpose: verify the law of reflection and finite-plate edge effects before building the full corridor.

1. Create a new high-frequency electromagnetic project.
2. Set geometry units to metres (or millimetres consistently) and frequency range around 10 GHz.
3. Create an air background / open simulation region.
4. Insert a finite PEC rectangular plate, 0.30 m long and 0.30 m high, with its surface orientation corresponding to a 45-degree top-view reflector.
5. Excite with a plane wave or a suitable directional source incident at 45 degrees to the plate normal. Confirm the incident and reflected directions in the coordinate system.
6. Set open/radiating boundaries on the outer region.
7. Use the time-domain solver (FIT) for a broadband pulse or the frequency-domain solver for a single-frequency 10 GHz study. Keep the source and solver choice consistent across the comparison.
8. Add a 10 GHz E-field monitor and, where useful, surface-current monitor.
9. Run the model and inspect the field distribution and reflected beam direction.
10. Repeat with plate lengths 0.15 m, 0.30 m, and 0.45 m.

Record: mesh settings, solver type, boundary padding, excitation definition, monitor frequency, plate dimensions, field maximum location, and exported field data.

## Model B: simplified 3D L-corridor
Purpose: compare the principal trends with the 2D Python model.

1. Build the horizontal and vertical corridor air volumes using the agreed 2 m arm lengths, 0.6 m width, and 0.3 m height.
2. Represent the walls with the same idealized PEC assumption used by the first Python model. This is a controlled idealization, not a claim that real concrete is PEC.
3. Place the finite PEC reflector at the corner, 0.30 m by 0.30 m, with its plan-view line at 45 degrees.
4. Place a directional antenna/horn at the transmitter location and orient it toward the reflector.
5. Place a receive antenna or a defined field probe at the receiver location. If using ports, document the excited port mode; a large 0.6 m by 0.3 m cross-section can support multiple modes at 10 GHz.
6. Use open boundaries at the ends / exterior region as appropriate for the chosen geometry and excitation.
7. Add a 10 GHz E-field monitor and field probes at the intended receiver and off-axis points.
8. Run the baseline and reflector cases, then sweep reflector tilt and dimensions.

## Comparison discipline
- Match frequency, polarization, incident direction, plate dimensions, and observation locations.
- Compare normalized field patterns and trend curves first.
- Do not claim absolute Python/CST agreement until the source normalization and 2D-to-3D scaling are justified.
- Export CST field data and document units and coordinate conventions.
