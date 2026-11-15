"""Physical dimensions and landmarks for the shared L-corridor model."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProjectGeometry:
    frequency_hz: float
    domain_x_min_m: float
    domain_x_max_m: float
    domain_y_min_m: float
    domain_y_max_m: float
    horizontal_x_m: tuple[float, float]
    horizontal_y_m: tuple[float, float]
    vertical_x_m: tuple[float, float]
    vertical_y_m: tuple[float, float]
    transmitter_world_m: tuple[float, float]
    reflector_center_world_m: tuple[float, float]
    receiver_world_m: tuple[float, float]
    reflector_nominal_angle_deg: float
    reflector_width_m: float
    reflector_height_m: float
    reflector_thickness_m: float

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "ProjectGeometry":
        sim = config["simulation"]
        geom = config["geometry"]
        return cls(
            frequency_hz=float(sim["frequency_hz"]),
            domain_x_min_m=float(sim["domain_x_min_m"]),
            domain_x_max_m=float(sim["domain_x_max_m"]),
            domain_y_min_m=float(sim["domain_y_min_m"]),
            domain_y_max_m=float(sim["domain_y_max_m"]),
            horizontal_x_m=tuple(map(float, geom["horizontal_corridor_x_m"])),
            horizontal_y_m=tuple(map(float, geom["horizontal_corridor_y_m"])),
            vertical_x_m=tuple(map(float, geom["vertical_corridor_x_m"])),
            vertical_y_m=tuple(map(float, geom["vertical_corridor_y_m"])),
            transmitter_world_m=tuple(map(float, geom["transmitter_world_m"])),
            reflector_center_world_m=tuple(map(float, geom["reflector_center_world_m"])),
            receiver_world_m=tuple(map(float, geom["receiver_world_m"])),
            reflector_nominal_angle_deg=float(geom["reflector_nominal_angle_deg"]),
            reflector_width_m=float(geom["reflector_width_m"]),
            reflector_height_m=float(geom["reflector_height_m"]),
            reflector_thickness_m=float(geom["reflector_thickness_m"]),
        )

    def contains_corridor_point(self, x_world_m: float, y_world_m: float) -> bool:
        horizontal = (
            self.horizontal_x_m[0] <= x_world_m <= self.horizontal_x_m[1]
            and self.horizontal_y_m[0] <= y_world_m <= self.horizontal_y_m[1]
        )
        vertical = (
            self.vertical_x_m[0] <= x_world_m <= self.vertical_x_m[1]
            and self.vertical_y_m[0] <= y_world_m <= self.vertical_y_m[1]
        )
        return horizontal or vertical

    def reflector_endpoints_world_m(
        self, width_m: float | None = None, angle_deg: float | None = None
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        import math

        width = self.reflector_width_m if width_m is None else width_m
        angle = self.reflector_nominal_angle_deg if angle_deg is None else angle_deg
        if width <= 0:
            raise ValueError("Reflector width must be positive.")
        half = 0.5 * width
        radians = math.radians(angle)
        dx_m = half * math.cos(radians)
        dy_m = half * math.sin(radians)
        cx, cy = self.reflector_center_world_m
        return (cx - dx_m, cy - dy_m), (cx + dx_m, cy + dy_m)
