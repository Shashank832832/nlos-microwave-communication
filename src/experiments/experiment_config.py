"""YAML loading and validation for all simulation and sweep settings."""

from pathlib import Path
import math
from typing import Any

import yaml


REQUIRED_SECTIONS = ("project", "simulation", "geometry", "source", "sensors", "experiments", "outputs", "plotting")


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Experiment configuration not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError(f"{config_path} must contain a YAML mapping.")
    validate_config(config, config_path)
    return config


def validate_config(config: dict[str, Any], source: str | Path = "configuration") -> None:
    missing = [section for section in REQUIRED_SECTIONS if section not in config]
    if missing:
        raise ValueError(f"{source}: missing required sections: {', '.join(missing)}")
    required_keys = {
        "simulation": (
            "frequency_hz", "cells_per_wavelength", "courant_factor", "warmup_cycles",
            "measurement_cycles", "domain_x_min_m", "domain_x_max_m",
            "domain_y_min_m", "domain_y_max_m",
        ),
        "geometry": (
            "horizontal_corridor_x_m", "horizontal_corridor_y_m", "vertical_corridor_x_m",
            "vertical_corridor_y_m", "transmitter_world_m", "reflector_center_world_m",
            "receiver_world_m", "reflector_nominal_angle_deg", "reflector_width_m",
            "reflector_height_m", "reflector_thickness_m",
        ),
        "source": ("waveform", "amplitude", "aperture_width_m", "steering_angle_deg", "taper"),
        "experiments": ("tilt_offsets_deg", "plate_widths_lambda"),
        "outputs": ("tables_dir", "figures_dir", "reports_dir"),
        "plotting": ("dpi", "color_map"),
    }
    for section, keys in required_keys.items():
        if not isinstance(config.get(section), dict):
            raise ValueError(f"{source}: {section} must be a mapping.")
        absent = [key for key in keys if key not in config[section]]
        if absent:
            raise ValueError(f"{source}: {section} missing parameters: {', '.join(absent)}")
    simulation = config["simulation"]
    for key in ("frequency_hz", "cells_per_wavelength", "warmup_cycles", "measurement_cycles"):
        value = float(simulation[key])
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{source}: simulation.{key} must be positive.")
    if not float(simulation["cells_per_wavelength"]).is_integer():
        raise ValueError(f"{source}: simulation.cells_per_wavelength must be an integer.")
    if not 0 < float(simulation["courant_factor"]) <= 1:
        raise ValueError(f"{source}: simulation.courant_factor must be in (0, 1].")
    if simulation["domain_x_max_m"] <= simulation["domain_x_min_m"]:
        raise ValueError(f"{source}: domain x limits must increase.")
    if simulation["domain_y_max_m"] <= simulation["domain_y_min_m"]:
        raise ValueError(f"{source}: domain y limits must increase.")
    geometry = config["geometry"]
    for key in (
        "horizontal_corridor_x_m", "horizontal_corridor_y_m", "vertical_corridor_x_m",
        "vertical_corridor_y_m", "transmitter_world_m", "reflector_center_world_m", "receiver_world_m",
    ):
        value = geometry[key]
        if not isinstance(value, list) or len(value) != 2:
            raise ValueError(f"{source}: geometry.{key} must contain two numeric coordinates.")
        if not all(isinstance(item, (int, float)) for item in value):
            raise ValueError(f"{source}: geometry.{key} must contain numeric values.")
    for key in ("reflector_width_m", "reflector_height_m", "reflector_thickness_m"):
        if float(geometry[key]) <= 0:
            raise ValueError(f"{source}: geometry.{key} must be positive.")
    source_config = config["source"]
    if source_config["waveform"].lower() not in ("cw", "gaussian"):
        raise ValueError(f"{source}: source.waveform must be 'cw' or 'gaussian'.")
    if source_config["taper"].lower() not in ("hann", "uniform"):
        raise ValueError(f"{source}: source.taper must be 'hann' or 'uniform'.")
    if float(source_config["aperture_width_m"]) <= 0:
        raise ValueError(f"{source}: source.aperture_width_m must be positive.")
    if not math.isfinite(float(source_config["amplitude"])):
        raise ValueError(f"{source}: source.amplitude must be finite.")
    if not isinstance(config["sensors"].get("receiver"), dict):
        raise ValueError(f"{source}: sensors.receiver must be a mapping.")
    if not isinstance(config["sensors"].get("off_axis"), list) or not config["sensors"]["off_axis"]:
        raise ValueError(f"{source}: sensors.off_axis must be a non-empty list.")
    for sensor in [config["sensors"]["receiver"], *config["sensors"]["off_axis"]]:
        for key in ("name", "center_world_m", "normal_xy", "integration_length_m"):
            if key not in sensor:
                raise ValueError(f"{source}: sensor definition missing {key!r}.")
    offsets = config["experiments"]["tilt_offsets_deg"]
    widths = config["experiments"]["plate_widths_lambda"]
    if not isinstance(offsets, list) or not offsets:
        raise ValueError(f"{source}: experiments.tilt_offsets_deg must be a non-empty list.")
    if not isinstance(widths, list) or not widths or any(float(width) <= 0 for width in widths):
        raise ValueError(f"{source}: experiments.plate_widths_lambda must contain positive widths.")
    if not any(float(offset) == 0 for offset in offsets):
        raise ValueError(f"{source}: tilt offsets must include 0 degrees for the aligned reference.")
    for key in ("tables_dir", "figures_dir", "reports_dir"):
        if not isinstance(config["outputs"][key], str) or not config["outputs"][key]:
            raise ValueError(f"{source}: outputs.{key} must be a non-empty path.")
    if int(config["plotting"]["dpi"]) <= 0 or not config["plotting"]["color_map"]:
        raise ValueError(f"{source}: plotting.dpi and plotting.color_map must be valid.")


def actual_plate_angle_deg(nominal_angle_deg: float, tilt_offset_deg: float) -> float:
    return nominal_angle_deg + tilt_offset_deg


def width_m_from_lambda(width_lambda: float, frequency_hz: float) -> float:
    if width_lambda <= 0 or frequency_hz <= 0:
        raise ValueError("Electrical width and frequency must be positive.")
    return width_lambda * 299_792_458.0 / frequency_hz


def width_lambda_from_m(width_m: float, frequency_hz: float) -> float:
    if width_m <= 0 or frequency_hz <= 0:
        raise ValueError("Physical width and frequency must be positive.")
    return width_m * frequency_hz / 299_792_458.0
