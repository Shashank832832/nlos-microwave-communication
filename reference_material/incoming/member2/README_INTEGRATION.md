# Member 2 — 2D TMz FDTD Solver Engine

## Deliverable

`fdtd_solver.py` is the reusable 2-D TMz FDTD engine for the project
"Non-Line-of-Sight Microwave Communication Using Passive Electromagnetic
Reflectors".

It implements:

- Yee-grid fields `Ez`, `Hx`, `Hy`
- Vectorized TMz magnetic/electric field updates
- 2-D CFL time-step calculation
- First-order Mur absorbing boundary conditions
- PEC line-segment and tilted-plate rasterization
- Built-in Gaussian point source for standalone tests
- External source callback for integration with Member 3
- Approximate spatially collocated Poynting-vector diagnostics

## Requirements

```powershell
python -m pip install numpy matplotlib
```

NumPy is required by the solver. Matplotlib is only needed by example
visualization scripts.

## Quick start

```python
from fdtd_solver import FDTDSolver

solver = FDTDSolver(
    nx=400,
    ny=400,
    dx=1e-3,
    dy=1e-3,
    frequency=10e9,
)

solver.add_tilted_pec_plate(
    center_x=0.18,
    center_y=0.20,
    length=0.10,
    angle_deg=22.5,
    thickness=0.003,
)

solver.run(1000)

print(solver.Ez.shape)
print(solver.time, solver.dt)
```

## Integration contract for the team

### Member 1 — Analytical geometry

Member 1 provides coordinates in metres and angles in degrees. Use:

```python
solver.add_pec_plate(x1, y1, x2, y2, thickness)
solver.add_tilted_pec_plate(
    center_x, center_y, length, angle_deg, thickness
)
```

The solver owns grid rasterization and the PEC mask. Analytical geometry
should not directly edit `solver.Ez`.

### Member 3 — Source and directivity

Member 3 owns `source.py`. The source module should expose a callback with
this signature:

```python
def inject(solver, time_seconds):
    # Update solver.Ez at source aperture/grid indices.
    # Example only:
    solver.Ez[source_i, source_j] += waveform(time_seconds)
```

Then Member 3 or the integration script calls:

```python
from source import inject

solver.step(source=inject)
# or
solver.run(n_steps=2000, source=inject)
```

The external callback replaces the built-in Gaussian source for that step.
Set `use_builtin_source=False` when constructing the solver to make the
ownership explicit.

The source module should not update H fields, apply ABCs, or modify the
solver time counter.

### Member 4 — Parametric experiments and sensors

Member 4 should import the engine and control simulation parameters:

```python
solver = FDTDSolver(nx=400, ny=400, frequency=10e9,
                    use_builtin_source=False)
```

At each step, read:

- `solver.Ez` — electric field
- `solver.Hx`, `solver.Hy` — magnetic fields
- `solver.time`, `solver.time_step` — simulation time
- `solver.pec` — PEC mask
- `solver.calculate_poynting()` — approximate `Sx`, `Sy`

Member 4 owns angle/width sweeps, sensor locations, data recording,
relative dB comparisons and interception maps. Do not put those loops
inside `fdtd_solver.py`.

### Member 5 — Validation/documentation

Member 5 can use the same field arrays and solver configuration to compare
2-D trends against CST. Record grid spacing, time step, source definition,
plate dimensions, boundary conditions and simulation duration.

## Numerical conventions and limitations

- Coordinates are in metres.
- `angle_deg` is measured counter-clockwise from +x.
- The grid uses `Ez.shape == (nx, ny)`,
  `Hx.shape == (nx, ny-1)`, and `Hy.shape == (nx-1, ny)`.
- `dt` is calculated from the 2-D CFL condition:
  `dt = courant_factor / (c * sqrt(1/dx**2 + 1/dy**2))`.
- Mur ABC is first order. It is approximate, especially for oblique
  incidence; UPML is a possible later improvement.
- Tilted PEC geometry is rasterized onto the grid. This introduces
  staircase error; refine the grid to test convergence.
- PEC is currently enforced by setting `Ez=0` on masked nodes. A more
  rigorous conformal/interface treatment may be needed for high-accuracy
  angled conductors.
- `calculate_poynting()` spatially interpolates H onto E locations, but
  does not yet correct the half-time-step Yee staggering. Treat it as a
  diagnostic until temporal centering and energy-balance validation are
  completed.
- The built-in Gaussian source is a simple point-source test source, not
  the team's final directional microwave aperture.
- This is a 2-D TMz model, not a full 3-D corridor simulation.

## Ownership boundary

Keep the solver engine generic. The following belong in other modules:

- `source.py`: CW/Gaussian waveform, aperture distribution, directivity
- `geometry.py` or analytical-model module: corridor/wall/reflector layout
- `experiments.py`: tilt and width sweeps, sensors, interception analysis
- `visualization.py`: plots and animations
- `validation.py`: stability, propagation, reflection and convergence tests
