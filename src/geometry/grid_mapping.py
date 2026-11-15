"""Conversions between physical world coordinates and the solver's local grid."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GridMapper:
    x_min_world_m: float
    y_min_world_m: float
    dx_m: float
    dy_m: float
    nx: int
    ny: int

    def __post_init__(self) -> None:
        if self.dx_m <= 0 or self.dy_m <= 0 or self.nx < 1 or self.ny < 1:
            raise ValueError("Grid spacing and dimensions must be positive.")

    def world_to_local_m(self, x_world_m: float, y_world_m: float) -> tuple[float, float]:
        return x_world_m - self.x_min_world_m, y_world_m - self.y_min_world_m

    def world_to_index(self, x_world_m: float, y_world_m: float) -> tuple[int, int]:
        x_local_m, y_local_m = self.world_to_local_m(x_world_m, y_world_m)
        ix = round(x_local_m / self.dx_m)
        iy = round(y_local_m / self.dy_m)
        if not (0 <= ix < self.nx and 0 <= iy < self.ny):
            raise IndexError(
                f"World point ({x_world_m}, {y_world_m}) maps to "
                f"grid index ({ix}, {iy}), outside ({self.nx}, {self.ny})."
            )
        return ix, iy

    def index_to_world(self, ix: int, iy: int) -> tuple[float, float]:
        if not (0 <= ix < self.nx and 0 <= iy < self.ny):
            raise IndexError(f"Grid index ({ix}, {iy}) is out of bounds.")
        return self.x_min_world_m + ix * self.dx_m, self.y_min_world_m + iy * self.dy_m

    def coordinate_arrays_world_m(self):
        import numpy as np

        return (
            self.x_min_world_m + np.arange(self.nx) * self.dx_m,
            self.y_min_world_m + np.arange(self.ny) * self.dy_m,
        )
