"""Draw the top-view L-corridor geometry and specular ray path."""
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from geometry import G, reflector_endpoints, direct_path_visibility

def make_plot(output="geometry.png"):
    fig, ax = plt.subplots(figsize=(8, 8))

    # Corridor floor-plan regions (schematic open interior).
    ax.add_patch(Rectangle((-2.0, -0.3), 2.0, 0.6,
                           facecolor="#e8eef7", edgecolor="black", lw=2))
    ax.add_patch(Rectangle((-0.3, 0.0), 0.6, 2.0,
                           facecolor="#e8eef7", edgecolor="black", lw=2))

    tx = G.tx
    ref = G.reflector_center
    rx = G.rx
    a, b = reflector_endpoints()

    # Intended specular path.
    ax.plot([tx[0], ref[0]], [tx[1], ref[1]], color="tab:blue", lw=2.5,
            label="Incident path")
    ax.plot([ref[0], rx[0]], [ref[1], rx[1]], color="tab:green", lw=2.5,
            label="Reflected path")

    # Blocked direct geometric segment.
    ax.plot([tx[0], rx[0]], [tx[1], rx[1]], "--", color="tab:red", lw=1.8,
            label="Direct path (blocked by corner geometry)")

    # Finite PEC plate.
    ax.plot([a[0], b[0]], [a[1], b[1]], color="black", lw=7,
            solid_capstyle="butt", label="0.30 m PEC reflector")

    ax.scatter(*tx, s=100, marker="^", color="tab:blue", zorder=5)
    ax.scatter(*rx, s=100, marker="s", color="tab:green", zorder=5)
    ax.scatter(*ref, s=55, color="black", zorder=6)

    ax.annotate("Tx (-1, 0)", tx, xytext=(-1.65, -0.52),
                arrowprops=dict(arrowstyle="->"))
    ax.annotate("Reflector (0, 0)", ref, xytext=(0.35, -0.38),
                arrowprops=dict(arrowstyle="->"))
    ax.annotate("Rx (0, 1)", rx, xytext=(0.42, 1.15),
                arrowprops=dict(arrowstyle="->"))

    visible, _ = direct_path_visibility()
    ax.text(-1.85, 1.65, f"Direct LOS inside corridor: {visible}",
            fontsize=9, bbox=dict(boxstyle="round", fc="white", ec="gray"))

    ax.set_xlim(-2.1, 0.8)
    ax.set_ylim(-0.8, 2.1)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("10 GHz NLOS Microwave Link — Initial Top View")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    print(f"Saved {output}")
    plt.show()

if __name__ == "__main__":
    make_plot()
