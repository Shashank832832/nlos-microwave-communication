# Submission checklist

- [x] Integration audit documents the solver/source/API differences and numerical limitations.
- [x] The canonical Member 2 solver and Member 3 source callback pass integration tests.
- [x] Automated suite passed: `python -m unittest discover -s tests -v` (9 tests, including Poynting signs, quick CSV/plot pipeline, and CST comparator schema).
- [x] Quick experiment command completed: `python -m src.experiments.run_experiments --config configs/quick_test.yaml`.
- [x] Full configured 20-cells/λ Member 4 experiment artifacts exist under `results/`.
- [x] Required three CSVs, four PNGs, and experiment summary are copied into `deliverables/results/`.
- [x] PowerPoint opens and contains 15 slides (maximum allowed: 15).
- [x] README and setup instructions describe the active package, configuration, commands, and limitations.
- [x] CST remains a separate verification model; no CST results are fabricated or implied.
- [x] Team names/IDs are explicitly pending because no roster was supplied.

## Validation scope

Quick mode verifies software integration and artifact generation only. It does not establish electromagnetic accuracy. The report states the signed per-unit-depth flux interpretation, uncorrected Yee temporal staggering in the Poynting diagnostic, first-order Mur boundaries, staircased PEC, and 2D-to-3D limitations.
