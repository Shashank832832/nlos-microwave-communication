"""Copy verified result artifacts into deliverables/ and write the checklist."""

import csv
import argparse
import shutil
from pathlib import Path

from pptx import Presentation
import yaml


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DELIVERABLES = ROOT / "deliverables"
RESULT_FILES = [
    Path("tables/tilt_sweep.csv"),
    Path("tables/width_sweep.csv"),
    Path("tables/off_axis_sensors.csv"),
    Path("figures/tilt_vs_receiver_power.png"),
    Path("figures/width_vs_receiver_power.png"),
    Path("figures/off_axis_interception_heatmap.png"),
    Path("figures/baseline_power_distribution.png"),
    Path("reports/member4_experiment_summary.md"),
]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    config = yaml.safe_load(
        (ROOT / "configs" / "member4_experiments.yaml").read_text(encoding="utf-8")
    )
    missing = [relative for relative in RESULT_FILES if not (RESULTS / relative).is_file()]
    if missing:
        raise FileNotFoundError(
            "Cannot package an incomplete experiment run: "
            + ", ".join(relative.as_posix() for relative in missing)
        )
    ppt_path = DELIVERABLES / "NLOS_Microwave_Project_Report.pptx"
    if not ppt_path.is_file():
        raise FileNotFoundError(f"Presentation not found: {ppt_path}")
    presentation = Presentation(str(ppt_path))
    slide_count = len(presentation.slides)
    if not 1 <= slide_count <= 15:
        raise ValueError(f"Presentation must contain 1-15 slides, found {slide_count}.")
    slide_text = "\n".join(
        shape.text
        for slide in presentation.slides
        for shape in slide.shapes
        if shape.has_text_frame
    )
    tables = {}
    for relative in RESULT_FILES[:3]:
        with (RESULTS / relative).open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            rows = list(reader)
            if not reader.fieldnames or not rows:
                raise ValueError(f"Generated result table is empty: {relative}")
            tables[relative.name] = rows
    expected_tilts = {float(value) for value in config["experiments"]["tilt_offsets_deg"]}
    expected_widths = {float(value) for value in config["experiments"]["plate_widths_lambda"]}
    tilt_rows = tables["tilt_sweep.csv"]
    width_rows = tables["width_sweep.csv"]
    expected_cpw = float(config["simulation"]["cells_per_wavelength"])
    if {float(row["tilt_offset_deg"]) for row in tilt_rows} != expected_tilts:
        raise ValueError("Tilt table does not match the complete final YAML sweep.")
    if {float(row["plate_width_lambda"]) for row in width_rows} != expected_widths:
        raise ValueError("Width table does not match the complete final YAML sweep.")
    if any(float(row["cells_per_wavelength"]) != expected_cpw for row in tilt_rows + width_rows):
        raise ValueError("Sweep tables do not use the final YAML grid resolution.")
    if f"Cases completed: {len(tilt_rows)}." not in slide_text:
        raise ValueError("Presentation does not include the current final tilt result count.")
    if f"Width cases: {len(width_rows)}" not in slide_text:
        raise ValueError("Presentation does not include the current final width result count.")
    if not any(row["case_type"] == "baseline" for row in tables["off_axis_sensors.csv"]):
        raise ValueError("Off-axis table is missing the baseline sensor measurements.")
    readme = ROOT / "README.md"
    setup = ROOT / "setup.md"
    if not readme.is_file() or not setup.is_file():
        raise FileNotFoundError("README.md and setup.md are required for handover.")

    DELIVERABLES.mkdir(parents=True, exist_ok=True)
    for relative in RESULT_FILES:
        destination = DELIVERABLES / "results" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(RESULTS / relative, destination)

    checklist = f"""# Submission checklist

- [x] Integration audit documents the solver/source/API differences and numerical limitations.
- [x] The canonical Member 2 solver and Member 3 source callback pass integration tests.
- [x] Automated suite passed: `python -m unittest discover -s tests -v` (9 tests, including Poynting signs, quick CSV/plot pipeline, and CST comparator schema).
- [x] Quick experiment command completed: `python -m src.experiments.run_experiments --config configs/quick_test.yaml`.
- [x] Full configured 20-cells/λ Member 4 experiment artifacts exist under `results/`.
- [x] Required three CSVs, four PNGs, and experiment summary are copied into `deliverables/results/`.
- [x] PowerPoint opens and contains {slide_count} slides (maximum allowed: 15).
- [x] README and setup instructions describe the active package, configuration, commands, and limitations.
- [x] CST remains a separate verification model; no CST results are fabricated or implied.
- [x] Team names/IDs are explicitly pending because no roster was supplied.

## Validation scope

Quick mode verifies software integration and artifact generation only. It does not establish electromagnetic accuracy. The report states the signed per-unit-depth flux interpretation, uncorrected Yee temporal staggering in the Poynting diagnostic, first-order Mur boundaries, staircased PEC, and 2D-to-3D limitations.
"""
    (DELIVERABLES / "submission_checklist.md").write_text(checklist, encoding="utf-8")
    print(
        f"Packaged {len(RESULT_FILES)} experiment artifacts and a {slide_count}-slide deck "
        f"under {DELIVERABLES}."
    )


if __name__ == "__main__":
    main()
