"""Minimal team-integration example."""
from fdtd_solver import FDTDSolver


def team_source(solver, time_seconds):
    """Placeholder for Member 3's source.inject implementation."""
    amplitude = solver.gaussian_pulse(time_seconds)
    solver.Ez[solver.source_x, solver.source_y] += amplitude


solver = FDTDSolver(
    nx=400,
    ny=400,
    dx=1e-3,
    dy=1e-3,
    frequency=10e9,
    use_builtin_source=False,
)

# Member 1 supplies these physical coordinates.
solver.add_tilted_pec_plate(
    center_x=0.18,
    center_y=0.20,
    length=0.10,
    angle_deg=22.5,
    thickness=0.003,
)

# Member 3 supplies the actual source callback.
solver.run(n_steps=100, source=team_source)

# Member 4 reads fields/sensors after each step.
Sx, Sy = solver.calculate_poynting()
print("Ez:", solver.Ez.shape)
print("Sx/Sy:", Sx.shape, Sy.shape)
print("Elapsed time (ns):", solver.time * 1e9)
