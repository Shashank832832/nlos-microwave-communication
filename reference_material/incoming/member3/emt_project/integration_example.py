
"""

Assumption:
Ez[ix, iy] is Member 2's electric field array.
"""

import numpy as np

from source import (
    SourceConfig,
    ApertureSource
)


# ---------------------------------------------
# SIMULATION GRID
# ---------------------------------------------

nx = 400
ny = 300

dx = 1.0e-3
dy = 1.0e-3

C0 = 299792458.0

dt = (
    0.99 * dx
    / (C0 * np.sqrt(2))
)

Ez = np.zeros(
    (nx, ny),
    dtype=float
)

# Source location
source_x_index = 40


# ---------------------------------------------
# INITIALIZE APERTURE SOURCE
# ---------------------------------------------

config = SourceConfig(

    frequency=10e9,

    aperture_width=0.12,

    steering_angle_deg=20.0,

    waveform="gaussian",

    taper="hann",

    num_elements=81

)

source = ApertureSource(config)


# ---------------------------------------------
# MAP SOURCE TO FDTD GRID
# ---------------------------------------------

y_centre = (ny - 1) * dy / 2.0

y_indices = np.rint(
    y_centre / dy + source.y / dy
).astype(int)


# ---------------------------------------------
# TIME-STEPPING LOOP
# ---------------------------------------------

for n in range(2000):

    # -----------------------------------------
    # MEMBER 2'S FDTD UPDATE GOES HERE
    # -----------------------------------------

    # update_Hx(...)
    # update_Hy(...)
    # update_Ez(...)
    # apply_PEC(...)
    # apply_Mur_ABC(...)

    # -----------------------------------------
    # MEMBER 3'S SOURCE INJECTION
    # -----------------------------------------

    source.inject(

        ez=Ez,

        time_step=n,

        dt=dt,

        dx=dx,

        dy=dy,

        x_index=source_x_index,

        y_indices=y_indices,

        mode="add"

    )

print("Source integration example completed.")
