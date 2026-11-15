"""Compatibility entry point for the active canonical-solver experiment suite."""

from src.experiments.run_experiments import main


if __name__ == "__main__":
    main(["--config", "configs/member4_experiments.yaml"])
