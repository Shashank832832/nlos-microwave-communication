"""Physical-coordinate line monitors for receiver and interception flux."""

from dataclasses import dataclass
import math

import numpy as np

from src.geometry.grid_mapping import GridMapper
from src.geometry.project_geometry import ProjectGeometry


@dataclass(frozen=True)
class LineFluxMonitor:
    name: str
    center_world_m: tuple[float, float]
    normal_xy: tuple[float, float]
    integration_length_m: float

    def __post_init__(self) -> None:
        nx, ny = self.normal_xy
        if not self.name:
            raise ValueError("Monitor name cannot be empty.")
        if self.integration_length_m <= 0:
            raise ValueError("Monitor integration length must be positive.")
        if not np.isfinite([*self.center_world_m, nx, ny]).all():
            raise ValueError("Monitor coordinates and normal must be finite.")
        if not math.isclose(math.hypot(nx, ny), 1.0, rel_tol=1e-5, abs_tol=1e-5):
            raise ValueError(f"Monitor {self.name!r} normal must be a unit vector.")

    @classmethod
    def from_config(cls, config: dict) -> "LineFluxMonitor":
        return cls(
            name=str(config["name"]),
            center_world_m=tuple(map(float, config["center_world_m"])),
            normal_xy=tuple(map(float, config["normal_xy"])),
            integration_length_m=float(config["integration_length_m"]),
        )

    def sample_points(self, dx_m: float, dy_m: float) -> np.ndarray:
        count = max(3, int(math.ceil(self.integration_length_m / min(dx_m, dy_m))) + 1)
        offsets = np.linspace(-self.integration_length_m / 2, self.integration_length_m / 2, count)
        nx, ny = self.normal_xy
        tangent = np.asarray([-ny, nx])
        center = np.asarray(self.center_world_m)
        return center[None, :] + offsets[:, None] * tangent[None, :]

    def validate_clear(
        self, mapper: GridMapper, geometry: ProjectGeometry, pec_mask: np.ndarray
    ) -> None:
        points = self.sample_points(mapper.dx_m, mapper.dy_m)
        for x_world_m, y_world_m in points:
            if not geometry.contains_corridor_point(float(x_world_m), float(y_world_m)):
                raise ValueError(
                    f"Monitor {self.name!r} extends outside the open corridor at "
                    f"({x_world_m:.4f}, {y_world_m:.4f}) m."
                )
            ix, iy = mapper.world_to_index(float(x_world_m), float(y_world_m))
            if pec_mask[ix, iy]:
                raise ValueError(f"Monitor {self.name!r} intersects a PEC cell.")

    def integrated_flux(self, sx: np.ndarray, sy: np.ndarray, mapper: GridMapper) -> float:
        points = self.sample_points(mapper.dx_m, mapper.dy_m)
        indices = [mapper.world_to_index(float(x), float(y)) for x, y in points]
        values = np.asarray(
            [sx[ix, iy] * self.normal_xy[0] + sy[ix, iy] * self.normal_xy[1] for ix, iy in indices]
        )
        spacing_m = self.integration_length_m / (len(values) - 1)
        return float(spacing_m * (values.sum() - 0.5 * (values[0] + values[-1])))


def monitors_from_config(config: dict) -> tuple[LineFluxMonitor, list[LineFluxMonitor]]:
    return (
        LineFluxMonitor.from_config(config["receiver"]),
        [LineFluxMonitor.from_config(item) for item in config["off_axis"]],
    )
