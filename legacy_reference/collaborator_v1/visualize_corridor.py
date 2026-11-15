
import numpy as np
import matplotlib.pyplot as plt

from fdtd_solver import FDTDSolver

# Initialize solver with corridor walls enabled
solver = FDTDSolver(
    use_pec=True,
    use_walls=True
)

X, Y = np.meshgrid(solver.x, solver.y)

# Plot the open corridor and PEC walls
plt.figure(figsize=(9, 9))

plt.contourf(
    X, Y,
    solver.wall_mask.astype(int),
    levels=[-0.5, 0.5, 1.5],
    colors=["white", "lightgray"]
)

# Draw the reflector
half_length = solver.plate_length / 2

x1 = -half_length * np.cos(solver.plate_angle)
y1 = -half_length * np.sin(solver.plate_angle)
x2 = half_length * np.cos(solver.plate_angle)
y2 = half_length * np.sin(solver.plate_angle)

plt.plot(
    [x1, x2],
    [y1, y2],
    color="red",
    linewidth=3,
    label="PEC reflector"
)

# Transmitter and receiver
plt.scatter(-1, 0, color="blue", s=100, label="Transmitter")
plt.scatter(0, 1, color="green", s=100, label="Receiver")

# Reflector center
plt.scatter(0, 0, color="red", s=40)

plt.text(-1, 0.07, "Tx", color="blue", ha="center")
plt.text(0.08, 1, "Rx", color="green")

plt.xlabel("X position (m)")
plt.ylabel("Y position (m)")
plt.title("L-Shaped Corridor with PEC Reflector")

plt.xlim(-2.1, 0.7)
plt.ylim(-0.4, 2.1)

plt.gca().set_aspect("equal")
plt.grid(alpha=0.25)
plt.legend()
plt.tight_layout()

plt.savefig("corridor_mask.png", dpi=300)
plt.show()

print("Saved corridor_mask.png")
print("Wall grid points:", np.count_nonzero(solver.wall_mask))
print("Open corridor grid points:", np.count_nonzero(~solver.wall_mask))
print("Reflector grid points:", np.count_nonzero(solver.pec_mask))
