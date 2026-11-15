"""Compare normalized CST monitor exports with Python off-axis flux trends."""

import argparse
import csv
import math
from pathlib import Path

from src.measurements.power_metrics import relative_power_db


CST_COLUMNS = {"case_type", "case_value", "sensor_name", "normalized_power"}
PYTHON_COLUMNS = {
    "case_type",
    "tilt_offset_deg",
    "plate_width_lambda",
    "sensor_name",
    "relative_flux_db_vs_same_sensor_baseline",
}


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no CSV header.")
        return list(reader)


def _close_value(left: str, right: str) -> bool:
    try:
        return math.isclose(float(left), float(right), rel_tol=1e-8, abs_tol=1e-8)
    except ValueError:
        return left == right


def compare_cst_exports(
    cst_csv_path: str | Path,
    python_csv_path: str | Path,
    case_type: str,
    case_value: float,
    output_csv_path: str | Path,
) -> int:
    cst_path = Path(cst_csv_path)
    python_path = Path(python_csv_path)
    cst_rows = _read_rows(cst_path)
    python_rows = _read_rows(python_path)
    if cst_rows and not CST_COLUMNS.issubset(cst_rows[0]):
        raise ValueError(
            "CST CSV requires columns: case_type, case_value, sensor_name, normalized_power."
        )
    if python_rows and not PYTHON_COLUMNS.issubset(python_rows[0]):
        raise ValueError(
            "Python CSV does not match the generated off_axis_sensors.csv schema."
        )

    cst_by_key: dict[tuple[str, float, str], float] = {}
    for row in cst_rows:
        try:
            numeric_case_value = float(row["case_value"])
            normalized_power = float(row["normalized_power"])
        except ValueError as error:
            raise ValueError(f"Invalid CST numeric value in row {row}.") from error
        key = (row["case_type"], numeric_case_value, row["sensor_name"])
        if key in cst_by_key:
            raise ValueError(f"Duplicate CST measurement row for {key}.")
        cst_by_key[key] = normalized_power

    cst_baseline = {
        sensor: value
        for (row_case, _value, sensor), value in cst_by_key.items()
        if row_case == "baseline"
    }
    if not cst_baseline:
        raise ValueError("CST export must include baseline rows with case_type=baseline.")

    output_rows = []
    for row in python_rows:
        if row["case_type"] != case_type:
            continue
        python_case_value = (
            row["tilt_offset_deg"] if case_type == "tilt" else row["plate_width_lambda"]
        )
        if not python_case_value or not _close_value(python_case_value, str(case_value)):
            continue
        sensor = row["sensor_name"]
        cst_power = next(
            (
                value
                for (export_case, export_value, export_sensor), value in cst_by_key.items()
                if export_case == case_type
                and export_sensor == sensor
                and math.isclose(export_value, case_value, rel_tol=1e-8, abs_tol=1e-8)
            ),
            None,
        )
        baseline_power = cst_baseline.get(sensor)
        if cst_power is None or baseline_power is None:
            continue
        cst_db = relative_power_db(cst_power, baseline_power)
        python_db = float(row["relative_flux_db_vs_same_sensor_baseline"])
        if not math.isfinite(python_db):
            python_db = float("nan")
        output_rows.append(
            {
                "case_type": case_type,
                "case_value": case_value,
                "sensor_name": sensor,
                "python_relative_flux_db": python_db,
                "cst_relative_power_db": cst_db,
                "cst_minus_python_db": cst_db - python_db
                if math.isfinite(cst_db) and math.isfinite(python_db)
                else float("nan"),
            }
        )
    if not output_rows:
        raise ValueError(
            "No matching sensor/case rows; check sensor names, case value, and CST baseline entries."
        )
    output_path = Path(output_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)
    return len(output_rows)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cst_csv", help="CST export: case_type,case_value,sensor_name,normalized_power")
    parser.add_argument("--python-csv", default="results/tables/off_axis_sensors.csv")
    parser.add_argument("--case-type", choices=("tilt", "width"), required=True)
    parser.add_argument("--case-value", type=float, required=True)
    parser.add_argument("--output", default="results/tables/cst_python_comparison.csv")
    args = parser.parse_args(argv)
    count = compare_cst_exports(
        args.cst_csv, args.python_csv, args.case_type, args.case_value, args.output
    )
    print(f"Compared {count} matched sensor(s); wrote {args.output}.")


if __name__ == "__main__":
    main()
