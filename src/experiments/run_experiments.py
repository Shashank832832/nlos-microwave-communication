"""Run baseline, tilt, width, CSV, plot, and report generation from YAML."""

import argparse
import csv
import math
from pathlib import Path

from src.analysis.analytical_model import calculate as calculate_analytical
from src.experiments.experiment_config import (
    actual_plate_angle_deg,
    load_config,
    width_lambda_from_m,
)
from src.experiments.experiment_runner import CaseResult, run_case
from src.experiments.simulation_factory import create_simulation
from src.experiments.tilt_sweep import run_tilt_sweep
from src.experiments.width_sweep import run_width_sweep
from src.measurements.power_metrics import relative_power_db
from src.visualization.baseline_plot import save_baseline_distribution
from src.visualization.interception_plot import save_interception_heatmap
from src.visualization.tilt_plot import save_tilt_plot
from src.visualization.width_plot import save_width_plot


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _off_axis_rows(
    result: CaseResult,
    case_type: str,
    baseline_sensor_fluxes: dict[str, float] | None = None,
    tilt_offset_deg: float | None = None,
    width_lambda: float | None = None,
) -> list[dict]:
    baseline_sensor_fluxes = baseline_sensor_fluxes or result.off_axis_flux_per_depth
    rows = []
    for monitor in result.simulation.off_axis_monitors:
        flux = result.off_axis_flux_per_depth[monitor.name]
        rows.append(
            {
                "case_type": case_type,
                "tilt_offset_deg": tilt_offset_deg,
                "plate_angle_deg": result.simulation.plate_angle_deg,
                "plate_width_lambda": width_lambda
                if width_lambda is not None
                else width_lambda_from_m(
                    result.simulation.plate_width_m,
                    result.simulation.geometry.frequency_hz,
                ),
                "sensor_name": monitor.name,
                "center_x_world_m": monitor.center_world_m[0],
                "center_y_world_m": monitor.center_world_m[1],
                "normal_x": monitor.normal_xy[0],
                "normal_y": monitor.normal_xy[1],
                "integration_length_m": monitor.integration_length_m,
                "flux_W_per_m": flux,
                "relative_flux_db_vs_same_sensor_baseline": relative_power_db(
                    flux, baseline_sensor_fluxes[monitor.name]
                ),
                "measurement_duration_s": result.measurement_duration_s,
                "dt_s": result.time_step_s,
            }
        )
    return rows


def _write_report(
    config: dict,
    baseline: CaseResult,
    tilt_rows: list[dict],
    width_rows: list[dict],
    output_path: Path,
) -> None:
    geometry = baseline.simulation.geometry
    analytical = calculate_analytical(
        geometry,
        int(config["simulation"]["cells_per_wavelength"]),
        float(config["simulation"]["courant_factor"]),
    )
    tilt_db = [
        (row["tilt_offset_deg"], relative_power_db(row["receiver_flux_W_per_m"], baseline.receiver_flux_per_depth))
        for row in tilt_rows
    ]
    valid_tilt = [(x, y) for x, y in tilt_db if math.isfinite(y)]
    width_db = [
        (row["plate_width_lambda"], relative_power_db(row["receiver_flux_W_per_m"], baseline.receiver_flux_per_depth))
        for row in width_rows
    ]
    valid_width = [(x, y) for x, y in width_db if math.isfinite(y)]
    tilt_observation = (
        f"Highest measured receiver flux in the configured tilt set: offset {max(valid_tilt, key=lambda x: x[1])[0]:g}°."
        if valid_tilt
        else "No positive finite receiver flux was available for relative tilt comparisons."
    )
    width_observation = (
        f"Highest measured receiver flux in the configured width set: {max(valid_width, key=lambda x: x[1])[0]:g} lambda."
        if valid_width
        else "No positive finite receiver flux was available for relative width comparisons."
    )
    cfg_sim = config["simulation"]
    cfg_source = config["source"]
    text = f"""# Member 4 experiment summary

## Geometry and baseline assumptions

The simulation uses a 10 GHz-class 2D TMz model (configured frequency: {geometry.frequency_hz:.6g} Hz) of a PEC L corridor. Horizontal arm: x={geometry.horizontal_x_m} m, y={geometry.horizontal_y_m} m; vertical arm: x={geometry.vertical_x_m} m, y={geometry.vertical_y_m} m. Tx={geometry.transmitter_world_m} m, reflector center={geometry.reflector_center_world_m} m, and Rx={geometry.receiver_world_m} m. The nominal reflector is {geometry.reflector_width_m:.4f} m wide, {geometry.reflector_height_m:.4f} m high as a physical design parameter, and has a {geometry.reflector_nominal_angle_deg:.1f}° tangent angle. Its height is not represented independently in the 2D top-view solver.

The active engine is the canonical Member 2 solver, with first-order Mur absorbing boundaries. PEC walls are masked outside the open L-shaped corridor; the horizontal x-min and vertical y-max channel mouths remain open. Negative world coordinates are translated to solver-local coordinates by subtracting the configured domain minima before index conversion.

## Source, grid, and duration

Member 3's aperture source uses waveform `{cfg_source['waveform']}`, {cfg_source['amplitude']} amplitude, {cfg_source['aperture_width_m']} m width, {cfg_source['steering_angle_deg']}° steering, and `{cfg_source['taper']}` taper. The configured source steering is {cfg_source['steering_angle_deg']}°; the baseline 0° setting directs the initial beam along +x. The grid uses {cfg_sim['cells_per_wavelength']} cells per wavelength, dx=dy={baseline.simulation.solver.dx:.6g} m, Courant factor {cfg_sim['courant_factor']}, and CFL time step dt={baseline.time_step_s:.6g} s. Each run uses {cfg_sim['warmup_cycles']} warm-up cycles and {cfg_sim['measurement_cycles']} measurement cycles. The baseline used {baseline.total_steps} steps total ({baseline.warmup_steps} warm-up and {baseline.measurement_steps} measurement); its measured runtime was {baseline.elapsed_wall_s:.3f} s.

## Sweep configurations

Tilt offsets (from nominal): {', '.join(f'{float(value):g}°' for value in config['experiments']['tilt_offsets_deg'])}. Absolute angles use nominal angle + offset. Widths: {', '.join(f'{float(value):g} lambda' for value in config['experiments']['plate_widths_lambda'])}, converted using lambda=c/f. Every case creates a new solver and changes only its requested reflector parameter.

## Measurement and dB methodology

Receiver and off-axis readings are line-integrated normal components of the solver's approximate Poynting vector averaged over the measurement window. The receiver monitor center is {baseline.simulation.receiver_monitor.center_world_m} m, normal {baseline.simulation.receiver_monitor.normal_xy}, and integration length {baseline.simulation.receiver_monitor.integration_length_m} m. The configured off-axis line monitors lie within the vertical corridor around the expected reflected +y direction; their positions, normals, fluxes, and comparisons are in `off_axis_sensors.csv`.

Relative flux is `10 log10(measured_flux/reference_flux)` for positive finite per-unit-depth fluxes. Nonpositive or invalid values are reported as NaN rather than converted to a misleading dB result. The 2D line integral is W/m per unit depth, not calibrated total watts or dBm. The analytical unobstructed direct Friis reference is {analytical['unobstructed_direct_fspl_db']:.2f} dB at {analytical['direct_distance_m']:.3f} m and is not a prediction of the reflected NLOS receiver power.

## Results and observations

- Baseline receiver flux: {baseline.receiver_flux_per_depth:.8g} W/m per unit depth.
- {tilt_observation}
- {width_observation}
- Configured measurement records: {len(tilt_rows)} tilt cases and {len(width_rows)} width cases.
- Failed or excluded simulations: none recorded. A simulation exception stops the runner and is surfaced; incomplete CSV/report output must not be interpreted as a completed run.

## Numerical and physical limitations

`calculate_poynting()` spatially interpolates H to E locations but does not correct Yee half-time staggering. Cycle averaging is a stability aid, not a temporal-centering correction. Mur boundaries are first order; PEC edges are staircased; ideal PEC walls and material properties are simplified; and the 2D model omits finite reflector height and all out-of-plane spreading. Results are relative diagnostics only. A quick/debug run validates software/data flow, not electromagnetic accuracy. Final claims require grid/time convergence and separately documented comparison against the CST 3D model.
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def run(config_path: str | Path, baseline_only: bool = False) -> None:
    config = load_config(config_path)
    output_dirs = {key: Path(value) for key, value in config["outputs"].items()}
    tables_dir = output_dirs["tables_dir"]
    figures_dir = output_dirs["figures_dir"]
    reports_dir = output_dirs["reports_dir"]
    for directory in output_dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    dpi = int(config["plotting"]["dpi"])

    nominal_angle = float(config["geometry"]["reflector_nominal_angle_deg"])
    baseline_simulation = create_simulation(config, plate_angle_deg=nominal_angle)
    print("Running baseline benchmark and reference measurement...")
    baseline = run_case(config, baseline_simulation, keep_average_field=True)
    save_baseline_distribution(
        baseline,
        figures_dir / "baseline_power_distribution.png",
        dpi,
        str(config["plotting"]["color_map"]),
    )
    baseline_sensors = _off_axis_rows(baseline, "baseline")
    if baseline_only:
        _write_csv(
            tables_dir / "off_axis_sensors.csv",
            list(baseline_sensors[0]) if baseline_sensors else [],
            baseline_sensors,
        )
        estimated_cases = len(config["experiments"]["tilt_offsets_deg"]) + len(
            config["experiments"]["plate_widths_lambda"]
        )
        print(
            f"Single-simulation benchmark: {baseline.elapsed_wall_s:.3f} s "
            f"({baseline.total_steps} steps). Estimated configured sweep: "
            f"{estimated_cases} additional simulations, approximately "
            f"{estimated_cases * baseline.elapsed_wall_s:.1f} s."
        )
        print(f"Baseline diagnostics saved under {figures_dir} and {tables_dir}.")
        return

    remaining = len(config["experiments"]["tilt_offsets_deg"]) + len(
        config["experiments"]["plate_widths_lambda"]
    )
    print(
        f"Benchmark: {baseline.elapsed_wall_s:.3f} s for {baseline.total_steps} steps; "
        f"rough remaining sweep estimate: {remaining * baseline.elapsed_wall_s:.1f} s "
        f"({remaining} fresh simulations)."
    )
    print("Running reflector tilt sweep...")
    tilt_results = run_tilt_sweep(config)
    print("Running reflector width sweep...")
    width_results = run_width_sweep(config)

    tilt_rows = [entry[0] for entry in tilt_results]
    width_rows = [entry[0] for entry in width_results]
    aligned = next(
        row for row in tilt_rows if row["tilt_offset_deg"] == 0.0
    )
    save_tilt_plot(
        tilt_rows, aligned["receiver_flux_W_per_m"],
        float(config["geometry"]["reflector_nominal_angle_deg"]),
        figures_dir / "tilt_vs_receiver_power.png", dpi
    )
    save_width_plot(
        width_rows, baseline.receiver_flux_per_depth,
        float(config["geometry"]["reflector_width_m"]),
        figures_dir / "width_vs_receiver_power.png", dpi
    )
    save_interception_heatmap(
        baseline_sensors, figures_dir / "off_axis_interception_heatmap.png", dpi
    )

    tilt_sensor_rows = []
    for row, result in tilt_results:
        tilt_sensor_rows.extend(
            _off_axis_rows(
                result, "tilt", baseline.off_axis_flux_per_depth,
                tilt_offset_deg=row["tilt_offset_deg"],
            )
        )
    width_sensor_rows = []
    for row, result in width_results:
        width_sensor_rows.extend(
            _off_axis_rows(
                result, "width", baseline.off_axis_flux_per_depth,
                width_lambda=row["plate_width_lambda"],
            )
        )
    all_sensor_rows = baseline_sensors + tilt_sensor_rows + width_sensor_rows
    for row in tilt_rows:
        row["relative_receiver_flux_db_vs_aligned"] = relative_power_db(
            row["receiver_flux_W_per_m"], aligned["receiver_flux_W_per_m"]
        )
    for row in width_rows:
        row["relative_receiver_flux_db_vs_baseline"] = relative_power_db(
            row["receiver_flux_W_per_m"], baseline.receiver_flux_per_depth
        )

    _write_csv(tables_dir / "tilt_sweep.csv", list(tilt_rows[0]), tilt_rows)
    _write_csv(tables_dir / "width_sweep.csv", list(width_rows[0]), width_rows)
    _write_csv(
        tables_dir / "off_axis_sensors.csv",
        list(all_sensor_rows[0]),
        all_sensor_rows,
    )
    _write_report(
        config, baseline, tilt_rows, width_rows,
        reports_dir / "member4_experiment_summary.md",
    )
    print("Member 4 experiments complete.")
    print(f"Tables: {tables_dir.resolve()}")
    print(f"Figures: {figures_dir.resolve()}")
    print(f"Report: {(reports_dir / 'member4_experiment_summary.md').resolve()}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/member4_experiments.yaml")
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Run one baseline simulation and generate baseline diagnostics only.",
    )
    args = parser.parse_args(argv)
    run(args.config, baseline_only=args.baseline_only)


if __name__ == "__main__":
    main()
