"""Build the 15-slide project handover presentation from generated results."""

import csv
from pathlib import Path

import yaml
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deliverables" / "NLOS_Microwave_Project_Report.pptx"
NAVY = RGBColor(12, 27, 48)
PANEL = RGBColor(22, 43, 69)
CYAN = RGBColor(52, 205, 220)
WHITE = RGBColor(241, 246, 252)
MUTED = RGBColor(170, 190, 208)
ORANGE = RGBColor(255, 175, 85)


def add_text(slide, text, x, y, w, h, size=18, color=WHITE, bold=False, align=None):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.03)
    frame.margin_right = Inches(0.03)
    frame.margin_top = Inches(0.02)
    frame.vertical_anchor = MSO_ANCHOR.TOP
    for index, line in enumerate(text.split("\n")):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = line
        paragraph.font.name = "Aptos"
        paragraph.font.size = Pt(size)
        paragraph.font.bold = bold
        paragraph.font.color.rgb = color
        if align is not None:
            paragraph.alignment = align
    return box


def add_bullets(slide, items, x, y, w, h, size=17, color=WHITE):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(0.08)
    frame.margin_right = Inches(0.08)
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = f"•  {item}"
        paragraph.level = 0
        paragraph.font.name = "Aptos"
        paragraph.font.size = Pt(size)
        paragraph.font.color.rgb = color
        paragraph.space_after = Pt(11)
    return box


def add_footer(slide, number):
    add_text(slide, "NLOS microwave • 2D TMz comparative simulation • flux per unit depth",
             0.55, 7.12, 11.5, 0.2, 9, MUTED)
    add_text(slide, f"{number:02d} / 15", 12.0, 7.1, 0.8, 0.22, 9, CYAN, align=PP_ALIGN.RIGHT)


def new_slide(prs, title, number, kicker=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NAVY
    if kicker:
        add_text(slide, kicker.upper(), 0.65, 0.32, 11.5, 0.25, 10, CYAN, bold=True)
    add_text(slide, title, 0.65, 0.66, 12.0, 0.55, 27, WHITE, bold=True)
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.65), Inches(1.32), Inches(1.0), Inches(0.035))
    line.fill.solid()
    line.fill.fore_color.rgb = CYAN
    line.line.fill.background()
    add_footer(slide, number)
    return slide


def add_panel(slide, x, y, w, h, fill=PANEL):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.color.rgb = fill
    return shape


def add_image_contain(slide, image_path, x, y, w, h):
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Presentation input image is missing: {path}")
    with Image.open(path) as image:
        aspect = image.width / image.height
    box_aspect = w / h
    if aspect > box_aspect:
        width = w
        height = w / aspect
    else:
        height = h
        width = h * aspect
    return slide.shapes.add_picture(
        str(path), Inches(x + (w - width) / 2), Inches(y + (h - height) / 2),
        width=Inches(width), height=Inches(height)
    )


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def add_architecture(slide):
    blocks = [
        ("YAML\nconfiguration", 0.8, 2.15, 2.2, 1.0),
        ("Geometry +\ngrid mapping", 3.45, 2.15, 2.2, 1.0),
        ("FDTD + aperture\nsource", 6.1, 2.15, 2.2, 1.0),
        ("Line monitors +\ncycle averages", 8.75, 2.15, 2.2, 1.0),
        ("CSV • plots\n• report", 10.9, 4.1, 1.8, 1.0),
    ]
    for label, x, y, w, h in blocks:
        add_panel(slide, x, y, w, h)
        add_text(slide, label, x + 0.08, y + 0.18, w - 0.16, h - 0.25, 14, WHITE, bold=True, align=PP_ALIGN.CENTER)
    for x1, y1, x2, y2 in [(3.0, 2.65, 3.4, 2.65), (5.65, 2.65, 6.05, 2.65),
                           (8.3, 2.65, 8.7, 2.65), (10.4, 2.85, 11.2, 4.0)]:
        line = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
        )
        line.line.color.rgb = CYAN
        line.line.width = Pt(2)
    add_text(slide, "Fresh simulation per sweep point", 2.0, 4.35, 4.6, 0.4, 15, ORANGE, bold=True)
    add_text(slide, "Independent 3D CST verification → exported data comparison (future)",
             6.2, 5.1, 6.0, 0.6, 14, MUTED)


def main():
    config_path = ROOT / "configs" / "member4_experiments.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    sim = config["simulation"]
    geom = config["geometry"]
    tilt_rows = read_csv(ROOT / "results" / "tables" / "tilt_sweep.csv")
    width_rows = read_csv(ROOT / "results" / "tables" / "width_sweep.csv")
    off_axis_rows = read_csv(ROOT / "results" / "tables" / "off_axis_sensors.csv")
    figures = ROOT / "results" / "figures"
    image_inputs = [
        figures / "baseline_power_distribution.png",
        figures / "tilt_vs_receiver_power.png",
        figures / "width_vs_receiver_power.png",
        figures / "off_axis_interception_heatmap.png",
    ]
    for image_path in image_inputs:
        if not image_path.is_file():
            raise FileNotFoundError(f"Required generated result is missing: {image_path}")
    if not tilt_rows or not width_rows or not off_axis_rows:
        raise ValueError("Generated sweep CSVs must contain result rows before building slides.")

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NAVY
    add_text(slide, "NLOS MICROWAVE\nCOMMUNICATION", 0.8, 1.25, 8.5, 1.45, 34, WHITE, bold=True)
    add_text(slide, "Passive finite-reflector link around an L-corridor corner",
             0.82, 3.0, 8.6, 0.6, 20, CYAN)
    add_text(slide, "Project report • Python FDTD + analytical model • CST verification kept separate",
             0.82, 3.82, 8.8, 0.65, 15, MUTED)
    add_panel(slide, 9.8, 1.3, 2.55, 2.5)
    add_text(slide, "10 GHz\n2D TMz\nPEC reflector", 10.0, 1.8, 2.15, 1.4, 23, WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Team details: names / IDs to be completed by the project team",
             0.82, 5.85, 10.5, 0.45, 13, ORANGE)
    add_footer(slide, 1)

    slide = new_slide(prs, "Abstract & problem statement", 2, "Project context")
    add_panel(slide, 0.8, 1.65, 5.75, 4.9)
    add_text(slide, "PROBLEM", 1.1, 1.95, 4.8, 0.35, 13, CYAN, bold=True)
    add_bullets(slide, [
        "An L-shaped corridor blocks the direct Tx–Rx path.",
        "A passive finite PEC plate at the corner redirects energy into the second arm.",
        "The reflected link depends on plate alignment, electrical width, source directivity, and boundaries.",
    ], 1.05, 2.5, 5.2, 3.5, 17)
    add_panel(slide, 6.8, 1.65, 5.65, 4.9)
    add_text(slide, "APPROACH", 7.1, 1.95, 4.8, 0.35, 13, CYAN, bold=True)
    add_bullets(slide, [
        "Analytical geometry + unobstructed LOS reference.",
        "Canonical 2D TMz Yee-grid solver and directional aperture excitation.",
        "Cycle-averaged receiver and off-axis line-flux comparisons.",
        "CST is a separate 3D verification model; no CST results are claimed here.",
    ], 7.05, 2.5, 5.1, 3.6, 16)

    slide = new_slide(prs, "Objectives & operating principle", 3, "Passive reflection")
    add_bullets(slide, [
        "Route a beam from the horizontal arm into the vertical arm without an active relay at the corner.",
        f"Use the nominal {config['geometry']['reflector_nominal_angle_deg']}° reflector tangent for the baseline reflection geometry.",
        "Quantify relative receiver flux versus tilt offset and plate width.",
        "Measure off-axis flux with line monitors and preserve unit/depth interpretation.",
    ], 0.95, 1.75, 6.0, 4.4, 18)
    add_panel(slide, 7.45, 1.8, 4.7, 3.95)
    add_text(slide, "Tx  →  PEC corner  →  Rx", 7.8, 2.45, 4.0, 0.55, 22, CYAN, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, f"Incident direction: +x\nBaseline reflected direction: +y\nSource steering: {config['source']['steering_angle_deg']}°\nNominal plate tangent: {config['geometry']['reflector_nominal_angle_deg']}°",
             8.0, 3.35, 3.6, 1.7, 17, WHITE, align=PP_ALIGN.CENTER)

    slide = new_slide(prs, "Electromagnetic theory & reflection geometry", 4, "Analytical model")
    add_panel(slide, 0.8, 1.65, 5.65, 4.75)
    add_text(slide, "Specular reflection", 1.1, 1.95, 4.8, 0.4, 17, CYAN, bold=True)
    add_text(slide, f"kᵣ = kᵢ − 2 (kᵢ · n) n\n\nFor the baseline {config['geometry']['reflector_nominal_angle_deg']}° tangent,\nincident +x reflects toward +y.",
             1.12, 2.55, 4.8, 2.0, 20, WHITE)
    add_text(slide, "The 2D plan-view plate is finite and PEC. Its physical height is a parameter, not a modeled 2D dimension.",
             1.12, 5.05, 4.9, 0.8, 13, MUTED)
    add_panel(slide, 6.75, 1.65, 5.7, 4.75)
    add_text(slide, "Path and reference discipline", 7.05, 1.95, 4.8, 0.4, 17, CYAN, bold=True)
    add_bullets(slide, [
        f"Tx {tuple(geom['transmitter_world_m'])} m → corner {tuple(geom['reflector_center_world_m'])} m → Rx {tuple(geom['receiver_world_m'])} m.",
        "Direct Tx–Rx line is not the reflected path.",
        "Friis LOS loss is only an unobstructed reference.",
        "Receiver trends come from FDTD line-flux measurements.",
    ], 7.0, 2.55, 5.1, 3.2, 16)

    slide = new_slide(prs, "System architecture", 5, "Modular implementation")
    add_architecture(slide)

    slide = new_slide(prs, "Components & simulation setup", 6, "Baseline configuration")
    dx = float(tilt_rows[0]["dx_m"])
    dt = float(tilt_rows[0]["dt_s"])
    add_panel(slide, 0.8, 1.65, 4.5, 4.95)
    add_bullets(slide, [
        f"Frequency: {sim['frequency_hz']/1e9:g} GHz",
        f"Final grid: {sim['cells_per_wavelength']} cells / λ; dx = {dx*1e3:.3f} mm",
        f"CFL time step: {dt*1e12:.3f} ps",
        f"Corridor: {geom['horizontal_corridor_x_m']} × {geom['horizontal_corridor_y_m']} m; vertical arm to y = {geom['vertical_corridor_y_m'][1]} m",
        f"Reflector: {geom['reflector_width_m']:.2f} m nominal width; PEC thickness parameter {geom['reflector_thickness_m']*1e3:g} mm",
    ], 1.05, 2.05, 4.0, 4.0, 15)
    add_panel(slide, 5.65, 1.65, 6.75, 4.95)
    add_text(slide, "Physical landmarks in world coordinates", 5.95, 1.95, 5.8, 0.35, 16, CYAN, bold=True)
    add_text(slide, f"Tx  {tuple(geom['transmitter_world_m'])} m\nReflector  {tuple(geom['reflector_center_world_m'])} m\nRx  {tuple(geom['receiver_world_m'])} m\n\nWorld → local: (x − x_min, y − y_min)\nSolver fields: Ez[nx, ny], Hx[nx, ny−1], Hy[nx−1, ny]",
             6.0, 2.55, 5.7, 3.5, 18, WHITE)

    slide = new_slide(prs, "Design steps, FDTD model & source", 7, "Numerical implementation")
    add_image_contain(slide, figures / "baseline_power_distribution.png", 0.7, 1.6, 7.6, 5.2)
    add_panel(slide, 8.55, 1.7, 3.95, 4.9)
    add_bullets(slide, [
        "Load YAML and validate physical parameters.",
        "Map world landmarks and build PEC corridor/plate.",
        "Configure Member 3 source on the canonical Yee grid.",
        "Run fresh cases; sample receiver/off-axis lines after warm-up.",
        "Member 2 Yee updates with first-order Mur boundaries.",
        f"Member 3 {config['source']['aperture_width_m']} m {config['source']['taper']} aperture; {config['source']['waveform']}, amplitude {config['source']['amplitude']}, {config['source']['steering_angle_deg']}° steering.",
        "Plot is a diagnostic, not calibrated power.",
    ], 8.8, 1.95, 3.45, 4.4, 12)

    slide = new_slide(prs, "Team-wise contributions", 8, "Members 1–5")
    contributions = [
        ("Member 1", "Shared corridor geometry and analytical calculations."),
        ("Member 2", "Generic 2D TMz FDTD solver and PEC/Mur implementation."),
        ("Member 3", "Directional aperture source, waveforms, taper, and steering."),
        ("Member 4", "Integration, sensors, parameter sweeps, CSVs, plots, and report."),
        ("Member 5", "Independent CST 3D verification model and export workflow."),
    ]
    for index, (member, contribution) in enumerate(contributions):
        y = 1.62 + index * 0.91
        add_panel(slide, 0.9, y, 11.5, 0.72)
        add_text(slide, member, 1.2, y + 0.16, 1.55, 0.3, 15, CYAN, bold=True)
        add_text(slide, contribution, 2.85, y + 0.13, 9.2, 0.38, 15, WHITE)
    add_text(slide, "Names, roll numbers, and individual acknowledgments: pending team roster.",
             1.0, 6.35, 11.2, 0.35, 13, ORANGE)

    slide = new_slide(prs, "Member 4 parametric methodology", 9, "Experiments & measurements")
    add_bullets(slide, [
        f"Tilt: offsets {config['experiments']['tilt_offsets_deg']}°; actual angle = {config['geometry']['reflector_nominal_angle_deg']}° + offset.",
        f"Width: {config['experiments']['plate_widths_lambda']} λ; physical width = λ·c/f.",
        f"Warm-up: {sim['warmup_cycles']} CW cycles; averaging: {sim['measurement_cycles']} cycles.",
        "Receiver line normal approximately +y; off-axis line normals rotated about the expected reflected direction.",
        "Signed normal Poynting flux integrated along each line; relative power uses 10 log₁₀(flux/reference).",
        "New solver for each case; source, grid, corridor, and monitors are held fixed.",
    ], 0.95, 1.75, 11.3, 4.75, 17)

    slide = new_slide(prs, "Reflector tilt sweep", 10, "FDTD result • relative to aligned case")
    add_image_contain(slide, figures / "tilt_vs_receiver_power.png", 1.0, 1.55, 11.2, 5.25)
    add_text(slide, f"Cases completed: {len(tilt_rows)}. CSV records actual angle, grid, dt, duration, and relative receiver flux.",
             1.0, 6.67, 11.0, 0.28, 11, MUTED)

    slide = new_slide(prs, "Width & off-axis interception", 11, "FDTD results")
    add_image_contain(slide, figures / "width_vs_receiver_power.png", 0.65, 1.6, 6.0, 4.9)
    add_image_contain(slide, figures / "off_axis_interception_heatmap.png", 6.85, 1.6, 5.85, 4.9)
    add_text(slide, f"Width cases: {len(width_rows)} • sensor records across baseline and sweeps: {len(off_axis_rows)}",
             1.0, 6.62, 11.2, 0.3, 11, MUTED)

    slide = new_slide(prs, "Observations & discussion", 12, "Interpretation")
    valid_tilt = [
        (float(row["tilt_offset_deg"]), float(row["relative_receiver_flux_db_vs_aligned"]))
        for row in tilt_rows
        if row.get("relative_receiver_flux_db_vs_aligned", "") not in ("", "nan", "NaN")
    ]
    valid_width = [
        (float(row["plate_width_lambda"]), float(row["relative_receiver_flux_db_vs_baseline"]))
        for row in width_rows
        if row.get("relative_receiver_flux_db_vs_baseline", "") not in ("", "nan", "NaN")
    ]
    discussion = []
    if valid_tilt:
        best = max(valid_tilt, key=lambda item: item[1])
        discussion.append(f"Highest measured relative tilt flux in this run: {best[0]:g}° offset ({best[1]:.2f} dB vs aligned).")
    else:
        discussion.append("Tilt relative dB values are unavailable for nonpositive/invalid signed reference flux.")
    if valid_width:
        best = max(valid_width, key=lambda item: item[1])
        discussion.append(f"Highest measured relative width flux in this run: {best[0]:g} λ ({best[1]:.2f} dB vs baseline).")
    else:
        discussion.append("Width relative dB values are unavailable for nonpositive/invalid signed reference flux.")
    discussion.extend([
        "Off-axis map shows the configured baseline monitor readings; it is not a continuous spatial survey.",
        "Trends are numerical and configuration-specific; grid convergence and CST comparison remain separate validation steps.",
    ])
    add_bullets(slide, discussion, 1.0, 1.8, 11.1, 4.6, 17)

    slide = new_slide(prs, "Limitations & future improvements", 13, "Engineering caveats")
    add_panel(slide, 0.9, 1.65, 5.5, 4.85)
    add_text(slide, "CURRENT LIMITS", 1.2, 1.95, 4.6, 0.35, 14, ORANGE, bold=True)
    add_bullets(slide, [
        "2D TMz, infinitely extruded model; line flux is per unit depth.",
        "Poynting H field is spatially interpolated, not time-centered.",
        "First-order Mur edges and rasterized PEC introduce numerical error.",
        "Ideal PEC walls do not represent measured concrete properties.",
    ], 1.15, 2.45, 4.9, 3.7, 15)
    add_panel(slide, 6.75, 1.65, 5.6, 4.85)
    add_text(slide, "NEXT STEPS", 7.05, 1.95, 4.7, 0.35, 14, CYAN, bold=True)
    add_bullets(slide, [
        "Grid/time-step convergence and improved absorbing boundary.",
        "Temporal centering and energy-balance diagnostics.",
        "Material-aware corridor model and finite 3D reflector.",
        "Compare normalized results with exported CST monitors.",
    ], 7.0, 2.45, 5.0, 3.7, 15)

    slide = new_slide(prs, "Validation status & references", 14, "Reproducibility")
    add_bullets(slide, [
        "Member 2 canonical solver and integration notes: reference_material/incoming/member2/.",
        "Member 3 aperture source and validation: reference_material/incoming/member3/emt_project/.",
        "Project settings: configs/member4_experiments.yaml.",
        "Integration findings: docs/integration_audit.md.",
        "CST is an independent 3D model; no CST results are included unless separately exported and validated.",
        "Submission status: see deliverables/submission_checklist.md.",
    ], 0.95, 1.75, 11.3, 4.75, 16)

    slide = new_slide(prs, "Conclusion & acknowledgments", 15, "Handover")
    add_text(slide, "A reproducible, configuration-driven 2D simulation now links the canonical solver and directional source to Member 4 tilt, width, receiver, and off-axis measurements.",
             1.0, 1.75, 11.1, 1.25, 22, WHITE, bold=True)
    add_bullets(slide, [
        "Results are relative numerical flux comparisons, not calibrated absolute received power.",
        "Analytical LOS reference, Python FDTD result, and CST verification are explicitly separated.",
        "All sweep inputs and generated outputs are reproducible from the documented YAML configuration.",
        "Acknowledgments, team names, and roll numbers: to be completed by the project team.",
    ], 1.05, 3.3, 10.9, 2.6, 16)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUTPUT)
    print(f"Saved {OUTPUT} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
