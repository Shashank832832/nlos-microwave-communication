"""Construct a fresh canonical FDTD/source pair from validated configuration."""

from dataclasses import dataclass
import math
from typing import Any

import numpy as np

from src.fdtd.solver import FDTDSolver
from src.geometry.grid_mapping import GridMapper
from src.geometry.project_geometry import ProjectGeometry
from src.measurements.field_monitors import LineFluxMonitor, monitors_from_config
from src.sources.aperture_source import ApertureSource, SourceConfig


@dataclass
class Simulation:
    solver: FDTDSolver
    source: ApertureSource
    mapper: GridMapper
    geometry: ProjectGeometry
    receiver_monitor: LineFluxMonitor
    off_axis_monitors: list[LineFluxMonitor]
    plate_angle_deg: float
    plate_width_m: float


def create_simulation(
    config: dict[str, Any],
    plate_angle_deg: float | None = None,
    plate_width_m: float | None = None,
) -> Simulation:
    sim_config = config["simulation"]
    geometry = ProjectGeometry.from_config(config)
    frequency_hz = geometry.frequency_hz
    wavelength_m = FDTDSolver.C0 / frequency_hz
    cells_per_wavelength = int(sim_config["cells_per_wavelength"])
    dx_m = wavelength_m / cells_per_wavelength
    dy_m = dx_m
    nx = math.ceil((geometry.domain_x_max_m - geometry.domain_x_min_m) / dx_m) + 1
    ny = math.ceil((geometry.domain_y_max_m - geometry.domain_y_min_m) / dy_m) + 1
    mapper = GridMapper(
        geometry.domain_x_min_m, geometry.domain_y_min_m, dx_m, dy_m, nx, ny
    )
    tx_i, tx_j = mapper.world_to_index(*geometry.transmitter_world_m)
    solver = FDTDSolver(
        nx=nx,
        ny=ny,
        dx=dx_m,
        dy=dy_m,
        courant_factor=float(sim_config["courant_factor"]),
        frequency=frequency_hz,
        source_x=tx_i,
        source_y=tx_j,
        use_builtin_source=False,
    )

    x_world, y_world = mapper.coordinate_arrays_world_m()
    x_grid, y_grid = np.meshgrid(x_world, y_world, indexing="ij")
    horizontal = (
        (x_grid >= geometry.horizontal_x_m[0])
        & (x_grid <= geometry.horizontal_x_m[1])
        & (y_grid >= geometry.horizontal_y_m[0])
        & (y_grid <= geometry.horizontal_y_m[1])
    )
    vertical = (
        (x_grid >= geometry.vertical_x_m[0])
        & (x_grid <= geometry.vertical_x_m[1])
        & (y_grid >= geometry.vertical_y_m[0])
        & (y_grid <= geometry.vertical_y_m[1])
    )
    horizontal_mouth = (
        (np.arange(nx)[:, None] == 0)
        & (y_grid >= geometry.horizontal_y_m[0])
        & (y_grid <= geometry.horizontal_y_m[1])
    )
    vertical_mouth = (
        (np.arange(ny)[None, :] == ny - 1)
        & (x_grid >= geometry.vertical_x_m[0])
        & (x_grid <= geometry.vertical_x_m[1])
    )
    solver.pec |= ~(horizontal | vertical | horizontal_mouth | vertical_mouth)

    width_m = geometry.reflector_width_m if plate_width_m is None else float(plate_width_m)
    angle_deg = (
        geometry.reflector_nominal_angle_deg
        if plate_angle_deg is None
        else float(plate_angle_deg)
    )
    first, second = geometry.reflector_endpoints_world_m(width_m, angle_deg)
    mapper.world_to_index(*first)
    mapper.world_to_index(*second)
    first_local = mapper.world_to_local_m(*first)
    second_local = mapper.world_to_local_m(*second)
    solver.add_pec_plate(
        first_local[0],
        first_local[1],
        second_local[0],
        second_local[1],
        geometry.reflector_thickness_m,
    )

    source_config = config["source"]
    source = ApertureSource(
        SourceConfig(
            frequency=frequency_hz,
            aperture_width=float(source_config["aperture_width_m"]),
            steering_angle_deg=float(source_config["steering_angle_deg"]),
            waveform=str(source_config["waveform"]),
            amplitude=float(source_config["amplitude"]),
            taper=str(source_config["taper"]),
        )
    )
    source.configure_grid(solver)
    if solver.pec[source.source_x, source.y_indices].any():
        raise ValueError("The aperture source intersects a PEC cell.")

    receiver, off_axis = monitors_from_config(config["sensors"])
    for monitor in (receiver, *off_axis):
        monitor.validate_clear(mapper, geometry, solver.pec)

    # Channel mouths remain unmasked at their absorbing domain edges.
    for iy, y_m in enumerate(y_world):
        if geometry.horizontal_y_m[0] <= y_m <= geometry.horizontal_y_m[1]:
            if solver.pec[0, iy]:
                raise ValueError("Horizontal corridor mouth is blocked by PEC at x_min.")
    for ix, x_m in enumerate(x_world):
        if geometry.vertical_x_m[0] <= x_m <= geometry.vertical_x_m[1]:
            if solver.pec[ix, -1]:
                raise ValueError("Vertical corridor mouth is blocked by PEC at y_max.")

    return Simulation(
        solver, source, mapper, geometry, receiver, off_axis, angle_deg, width_m
    )
