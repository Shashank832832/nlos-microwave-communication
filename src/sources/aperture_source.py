
"""

TMz fields:
Ez, Hx, Hy

Operating frequency:
10 GHz
"""

from dataclasses import dataclass
import numpy as np


C0 = 299792458.0


@dataclass
class SourceConfig:

    frequency: float = 10e9
    aperture_width: float = 0.12
    steering_angle_deg: float = 0.0

    waveform: str = "gaussian"
    amplitude: float = 1.0
    taper: str = "hann"

    gaussian_t0: float = None
    gaussian_sigma: float = None

    def __post_init__(self):

        if self.frequency <= 0:
            raise ValueError("Frequency must be positive")

        if self.aperture_width <= 0:
            raise ValueError("Aperture width must be positive")

        if self.waveform.lower() not in ("cw", "gaussian"):
            raise ValueError("Waveform must be cw or gaussian")

        if self.taper.lower() not in ("hann", "uniform"):
            raise ValueError("Taper must be hann or uniform")

        if abs(self.steering_angle_deg) >= 80:
            raise ValueError(
                "Steering angle must be between -80 and 80 degrees"
            )


class ApertureSource:

    def __init__(self, config):

        self.config = config

        self.frequency = config.frequency
        self.wavelength = C0 / self.frequency

        self.omega = 2 * np.pi * self.frequency
        self.k0 = 2 * np.pi / self.wavelength

        self.theta0 = np.deg2rad(
            config.steering_angle_deg
        )

        self.t0 = (
            config.gaussian_t0
            if config.gaussian_t0 is not None
            else 4 / self.frequency
        )

        self.sigma = (
            config.gaussian_sigma
            if config.gaussian_sigma is not None
            else 1.5 / self.frequency
        )

        self.y_positions = None
        self.weights = None
        self.y_indices = None
        self.source_x = None

    # --------------------------------------------------
    # APERTURE DISCRETIZATION
    # --------------------------------------------------

    def configure_grid(self, solver):

        dy = solver.dy

        intervals = int(
            np.floor(self.config.aperture_width / dy)
        )

        # Ensure symmetric aperture around its centre.
        if intervals % 2 != 0:
            intervals -= 1

        offsets = np.arange(
            -(intervals // 2),
            intervals // 2 + 1
        )

        self.y_positions = offsets * dy

        self.y_indices = (
            solver.source_y + offsets
        ).astype(int)

        self.source_x = solver.source_x

        if np.any(self.y_indices < 0) or np.any(
            self.y_indices >= solver.ny
        ):
            raise ValueError(
                "Aperture extends outside the FDTD grid. "
                "Increase ny or reduce aperture width."
            )

        if self.config.taper.lower() == "hann":

            self.weights = np.hanning(
                len(self.y_positions)
            )

        else:

            self.weights = np.ones(
                len(self.y_positions)
            )

        self.weights /= np.max(self.weights)

        self.configured_frequency = solver.frequency
        self.configured_dy = solver.dy

    # --------------------------------------------------
    # SOURCE WAVEFORM GENERATION
    # --------------------------------------------------

    def element_values(self, time_seconds):

        if self.y_positions is None:
            raise RuntimeError(
                "Call configure_grid(solver) before generating source values"
            )

        # Progressive time delay for beam steering.
        delayed_time = (
            time_seconds
            - self.y_positions * np.sin(self.theta0) / C0
        )

        if self.config.waveform.lower() == "cw":

            signal = np.cos(
                self.omega * delayed_time
            )

        else:

            envelope = np.exp(
                -0.5 *
                (
                    (delayed_time - self.t0)
                    / self.sigma
                ) ** 2
            )

            signal = envelope * np.cos(
                self.omega * (delayed_time - self.t0)
            )

        return (
            self.config.amplitude
            * self.weights
            * signal
        )

    # --------------------------------------------------
    # MEMBER 2 FDTD CALLBACK INTERFACE
    # --------------------------------------------------

    def inject(self, solver, time_seconds):

        if self.y_indices is None:
            self.configure_grid(solver)

        if not np.isclose(
            solver.frequency,
            self.frequency,
            rtol=1e-9
        ):
            raise ValueError(
                "Source frequency does not match FDTD frequency"
            )

        if not np.isclose(
            solver.dy,
            self.configured_dy
        ):
            raise ValueError(
                "FDTD grid spacing changed after source configuration"
            )

        values = self.element_values(time_seconds)

        # Inject Ez along the vertical aperture.
        solver.Ez[
            self.source_x,
            self.y_indices
        ] += values

    # --------------------------------------------------
    # ANALYTICAL RADIATION PATTERN
    # --------------------------------------------------

    def analytical_pattern(
        self,
        angles_deg,
        dy=None
    ):

        if self.y_positions is None:

            if dy is None:

                positions = np.linspace(
                    -self.config.aperture_width / 2,
                    self.config.aperture_width / 2,
                    121
                )

            else:

                intervals = int(
                    np.floor(
                        self.config.aperture_width / dy
                    )
                )

                if intervals % 2:
                    intervals -= 1

                offsets = np.arange(
                    -(intervals // 2),
                    intervals // 2 + 1
                )

                positions = offsets * dy

            if self.config.taper.lower() == "hann":

                weights = np.hanning(len(positions))

            else:

                weights = np.ones(len(positions))

            weights /= np.max(weights)

        else:

            positions = self.y_positions
            weights = self.weights

        angles = np.deg2rad(
            np.asarray(angles_deg, dtype=float)
        )

        phase = self.k0 * np.outer(
            np.sin(angles) - np.sin(self.theta0),
            positions
        )

        array_factor = (
            np.exp(1j * phase) @ weights
        )

        magnitude = np.abs(array_factor)

        peak = np.max(magnitude)

        normalized = (
            magnitude / peak
            if peak > 0
            else magnitude
        )

        pattern_db = 20 * np.log10(
            np.maximum(normalized, 1e-3)
        )

        return normalized, pattern_db


# ------------------------------------------------------
# HALF POWER BEAMWIDTH
# ------------------------------------------------------

def half_power_beamwidth(
    angles_deg,
    pattern_db
):

    angles = np.asarray(
        angles_deg,
        dtype=float
    )

    db = np.asarray(
        pattern_db,
        dtype=float
    )

    if angles.ndim != 1 or db.ndim != 1:
        raise ValueError("Inputs must be one-dimensional")

    if len(angles) != len(db):
        raise ValueError("Input lengths must match")

    peak_index = np.argmax(db)

    threshold = db[peak_index] - 3.0

    left = None
    right = None

    # Left -3 dB crossing.
    for i in range(peak_index - 1, -1, -1):

        if db[i] <= threshold < db[i + 1]:

            fraction = (
                threshold - db[i]
            ) / (
                db[i + 1] - db[i]
            )

            left = (
                angles[i]
                + fraction * (angles[i + 1] - angles[i])
            )

            break

    # Right -3 dB crossing.
    for i in range(peak_index, len(db) - 1):

        if db[i] > threshold >= db[i + 1]:

            fraction = (
                threshold - db[i]
            ) / (
                db[i + 1] - db[i]
            )

            right = (
                angles[i]
                + fraction * (angles[i + 1] - angles[i])
            )

            break

    if left is None or right is None:

        return np.nan, left, right

    return right - left, left, right
