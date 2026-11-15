# Setup and execution guide

These commands were run in the repository's Windows PowerShell environment with Python 3.14.4. The project requires Python 3.10 or later. Run commands from the repository root in the VS Code integrated terminal.

## 1. Prerequisites

- Windows 10/11, VS Code, and Python 3.10+ (Python 3.12+ recommended).
- `python` available in PowerShell; verify with `python --version`.
- Internet access for the first dependency installation.

## 2. Create and activate an isolated environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, allow scripts for the current process only and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

In VS Code, select `.venv` using **Python: Select Interpreter**, then open a new integrated terminal.

## 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

This installs NumPy, Matplotlib, PyYAML, python-pptx, and Pillow (used to preserve generated-figure aspect ratios in the presentation). No CST package or API is used by the Python engine.

## 4. Verify installation

```powershell
python --version
python -c "import numpy, matplotlib, yaml, pptx; print('NumPy', numpy.__version__); print('Matplotlib', matplotlib.__version__); print('PyYAML', yaml.__version__); print('python-pptx', pptx.__version__)"
python -m unittest discover -s tests -v
```

The tests cover geometry and coordinates, solver/source integration, field and Poynting array sizes, finite short-run fields, dB conversions, monitor validation, open corridor mouths, and the quick CSV/plot pipeline. A passing quick test indicates software behavior only, not physical accuracy.

## 5. Run a baseline simulation

```powershell
python -m src.experiments.run_experiments --config configs/baseline.yaml --baseline-only
```

This performs one baseline run at 20 cells/wavelength, times the simulation, and writes the baseline power-flow figure and baseline sensor table. The YAML sets a 75-cycle warm-up and 12-cycle measurement window. The runner reports an estimated sweep duration based on this single-simulation benchmark.

## 6. Run quick/debug experiments

```powershell
python -m src.experiments.run_experiments --config configs/quick_test.yaml
```

Quick mode uses 10 cells/wavelength, three tilt offsets, two width cases, and a shorter measurement interval. It runs the complete simulation-to-CSV-to-plot pipeline. Do not use quick-mode results as a claim of converged or physically validated performance.

## 7. Run the full Member 4 experiment

```powershell
python -m src.experiments.run_experiments --config configs/member4_experiments.yaml
```

The final configuration uses 20 cells/wavelength, all configured tilt offsets and widths, and a per-run runtime estimate based on an actual baseline. Each case constructs a new solver. This may take several minutes or longer depending on machine performance.

After the final run has produced all plots and CSVs, build the slide deck:

```powershell
python scripts/build_presentation.py
python scripts/package_submission.py
```

The presentation builder reads the actual generated Member 4 plots and tables, limits the deck to 15 slides, and marks missing team roster details as pending. The packaging command validates required outputs and slide count, copies the experiment outputs under `deliverables/results/`, and writes the submission checklist.

## 8. Generated output locations

| Output | Location |
|---|---|
| Tilt, width, off-axis CSV data | `results/tables/` |
| Tilt, width, interception, and baseline figures | `results/figures/` |
| Member 4 results and limitations | `results/reports/member4_experiment_summary.md` |
| Final project presentation | `deliverables/NLOS_Microwave_Project_Report.pptx` |
| Submission status checklist | `deliverables/submission_checklist.md` |

Directories are created automatically. The sweep does not save every timestep's field history.

## 9. Change experiment parameters

All experimental values are loaded from YAML. The three files share the same schema:

- `configs/baseline.yaml`: one 20-cells/λ baseline setup.
- `configs/quick_test.yaml`: 10-cells/λ software-pipeline subset.
- `configs/member4_experiments.yaml`: complete final sweep.

Edit the file passed by `--config`; do not change Python modules for ordinary parameter sweeps.

| Parameter | YAML key |
|---|---|
| Frequency and cells per wavelength | `simulation.frequency_hz`, `simulation.cells_per_wavelength` |
| CFL factor and durations | `simulation.courant_factor`, `simulation.warmup_cycles`, `simulation.measurement_cycles` |
| Domain/world landmarks and corridor | `simulation.domain_*_m`, `geometry.*` |
| Nominal reflector angle, dimensions, thickness | `geometry.reflector_nominal_angle_deg`, `geometry.reflector_width_m`, `geometry.reflector_height_m`, `geometry.reflector_thickness_m` |
| Tilt offsets and electrical widths | `experiments.tilt_offsets_deg`, `experiments.plate_widths_lambda` |
| Waveform, amplitude, aperture, steering, taper | `source.waveform`, `source.amplitude`, `source.aperture_width_m`, `source.steering_angle_deg`, `source.taper` |
| Receiver and off-axis monitors | `sensors.receiver` and `sensors.off_axis` entries |
| Output paths and figure styling | `outputs.*`, `plotting.*` |

Examples (edit the selected YAML):

- Change nominal plate tilt: `geometry.reflector_nominal_angle_deg: 45.0`; set the experimental offsets separately in `experiments.tilt_offsets_deg`.
- Change sweep widths: set `experiments.plate_widths_lambda: [5, 10, 15]`. Values are converted using wavelength `c/f`.
- Change frequency: edit `simulation.frequency_hz`; electrical widths remain wavelength-normalized.
- Change source steering: edit `source.steering_angle_deg`. The physical baseline should remain 0 degrees for initial +x propagation.
- Change grid: set `simulation.cells_per_wavelength` (10 debug, 20 default final).
- Move a sensor: edit `center_world_m`, `normal_xy` (unit vector), and `integration_length_m` for that sensor. Startup validation rejects points outside the open corridor or on PEC.

## 10. Run the baseline-only option

The same runner offers a baseline-only mode for quick inspection:

```powershell
python -m src.experiments.run_experiments --config configs/baseline.yaml --baseline-only
```

Full experiments are run without `--baseline-only`.

## 11. CST separation and future comparison

The 3D CST workflow is independent and documented in [cst_verification/README.md](cst_verification/README.md). Export CST field or monitor data with explicit units and coordinates before comparison. Compare normalized spatial/trend results first; do not compare absolute 2D flux with 3D port power without a justified depth/source normalization.

## 12. Troubleshooting

- **`ModuleNotFoundError`**: activate `.venv`, confirm VS Code selected the same interpreter, and reinstall with `python -m pip install -r requirements.txt`.
- **PyYAML/config errors**: use spaces rather than tabs, preserve the required shared YAML schema, and check the missing key named in the startup exception.
- **Monitor validation errors**: verify world-coordinate placement, ensure its whole integration line stays inside the open L corridor, use a unit normal, and keep it clear of the PEC plate/walls.
- **Out-of-grid error**: check that source, reflector, or sensor coordinates lie within the configured domain.
- **Long sweep**: run `quick_test.yaml` first or use `--baseline-only`; use the actual benchmark output to plan a full run. Do not shorten final warm-up without checking propagation and boundary transients.
- **NaN relative dB**: the measured or reference signed flux was nonpositive or invalid. Review monitor orientation and fields; the code deliberately does not convert invalid flux to positive power.
- **Plot backend/display issues**: figures are written directly to PNG and do not require an interactive display.
- **CST import/execution errors**: the Python package does not call CST. Follow the separate CST workflow and version-specific installation.

## 13. Automated tests

```powershell
python -m unittest discover -s tests -v
```

This command has been run successfully in the project environment. Tests generate quick-pipeline outputs in a temporary directory and clean them afterward.
