"""
Wavelength-Ternary Hybrid SFG Chip — Fabrication-Level GDS
============================================================
Real component geometries for LNOI (thin-film lithium niobate on insulator).

Components:
  - Waveguides:     800 nm wide ridge, ≥50 μm bend radius
  - Edge couplers:  200 μm taper (800 nm → 200 nm tip)
  - MZI gates:      Mach-Zehnder interferometer with EO electrodes (~300 μm)
  - SFG elements:   PPLN sections with poling period markers (~500 μm)
  - Detectors:      Ge-on-LN photodiode pads (30 × 30 μm)
  - Electrodes:     5 μm wide metal for EO tuning

Wavelengths (from wavelength_design.py):
  Inputs:  R=1560 nm, G=1540 nm, B=1520 nm
  Weights: +1=1070 nm, -1=1040 nm
  SFG out: 617-635 nm (visible, Si detectable)

Poling periods: 12.55 - 13.55 μm
"""

import gdstk
import math

# =====================================================================
# Layer definitions (fab-level)
# =====================================================================
LY_WG_RIDGE    = (1, 0)    # Waveguide ridge etch
LY_WG_SLAB     = (1, 1)    # Slab region (partial etch)
LY_PPLN        = (2, 0)    # Poling electrode pattern (defines domain inversion)
LY_METAL_EL    = (3, 0)    # Metal electrodes (EO tuning, MZI phase shifters)
LY_METAL_PAD   = (3, 1)    # Bond pads
LY_DETECTOR    = (4, 0)    # Photodetector active area (Ge or bonded InGaAs)
LY_DET_CONTACT = (4, 1)    # Detector metal contacts
LY_CLAD_OPEN   = (5, 0)    # Cladding opening (for detectors, pads)
LY_DEEP_ETCH   = (6, 0)    # Deep etch (chip facets, isolation)
LY_LABEL       = (10, 0)   # Labels
LY_FLOORPLAN   = (11, 0)   # Floorplan outlines (non-fab, reference only)

# =====================================================================
# Physical dimensions (all in microns)
# =====================================================================
WG_W = 0.8          # Waveguide width (single-mode @ 1550 nm on LNOI)
WG_SLAB_W = 4.0     # Slab width around ridge
BEND_R = 50.0        # Minimum bend radius

# Edge coupler
TAPER_L = 200.0      # Taper length
TAPER_TIP = 0.2      # Tip width

# MZI gate
MZI_SPLIT_L = 30.0   # Y-splitter length
MZI_ARM_SEP = 10.0   # Arm separation
MZI_ARM_L = 150.0    # Arm length (electrode region)
MZI_EL_W = 5.0       # Electrode width
MZI_EL_GAP = 2.0     # Gap between electrode and waveguide
MZI_TOTAL_L = MZI_SPLIT_L * 2 + MZI_ARM_L  # ~210 μm

# SFG element (PPLN section)
SFG_L = 500.0         # PPLN interaction length
SFG_PPLN_W = 4.0      # Width of poling pattern

# Poling periods (from wavelength_design.py, in μm)
POLING_PERIODS = {
    "R+1": 13.549,
    "R-1": 12.975,
    "G+1": 13.331,
    "G-1": 12.765,
    "B+1": 13.111,
    "B-1": 12.553,
}

# Detector
DET_SIZE = 30.0       # Square detector pad
DET_CONTACT = 20.0    # Contact opening

# Bond pad
PAD_SIZE = 80.0       # Bond pad for wire bonding
PAD_PITCH = 150.0

# Chip layout
CHAMBER_PITCH_X = 800.0   # Column spacing (center to center)
CHAMBER_PITCH_Y = 700.0   # Row spacing
N_ROWS = 3
N_COLS = 3

# MMI combiner
MMI_W = 6.0           # MMI coupler width
MMI_L = 40.0          # MMI coupler length


# =====================================================================
# Helper functions
# =====================================================================
def waveguide_straight(cell, x0, y0, x1, y1):
    """Add a straight waveguide from (x0,y0) to (x1,y1)."""
    dx = x1 - x0
    dy = y1 - y0
    length = math.sqrt(dx*dx + dy*dy)
    angle = math.atan2(dy, dx)

    path = gdstk.FlexPath(
        [(x0, y0), (x1, y1)],
        WG_W,
        layer=LY_WG_RIDGE[0], datatype=LY_WG_RIDGE[1]
    )
    cell.add(path)


def waveguide_sbend(cell, x0, y0, x1, y1):
    """Add an S-bend waveguide connecting two points at different y."""
    dx = x1 - x0
    dy = y1 - y0
    mid_x = (x0 + x1) / 2

    path = gdstk.FlexPath(
        [(x0, y0), (mid_x, y0), (mid_x, y1), (x1, y1)],
        WG_W,
        bend_radius=BEND_R,
        layer=LY_WG_RIDGE[0], datatype=LY_WG_RIDGE[1]
    )
    cell.add(path)


def add_edge_coupler(lib, name="EDGE_COUPLER"):
    """Create an edge coupler cell (taper from tip to WG_W)."""
    cell = lib.new_cell(name)

    # Taper polygon (trapezoid)
    cell.add(gdstk.Polygon([
        (0, -TAPER_TIP / 2),
        (0, TAPER_TIP / 2),
        (TAPER_L, WG_W / 2),
        (TAPER_L, -WG_W / 2),
    ], layer=LY_WG_RIDGE[0], datatype=LY_WG_RIDGE[1]))

    # Slab under taper for mode confinement
    cell.add(gdstk.rectangle(
        (0, -WG_SLAB_W / 2), (TAPER_L, WG_SLAB_W / 2),
        layer=LY_WG_SLAB[0], datatype=LY_WG_SLAB[1]
    ))

    cell.add(gdstk.Label(name, (TAPER_L / 2, WG_SLAB_W / 2 + 3),
                          layer=LY_LABEL[0], texttype=LY_LABEL[1]))
    return cell


def add_mzi_gate(lib, name="MZI_GATE"):
    """
    Create an MZI switch cell.
    Input on left (0,0), output on right (MZI_TOTAL_L, 0).
    Two arms with electrodes for push-pull EO phase shifting.
    """
    cell = lib.new_cell(name)
    half_sep = MZI_ARM_SEP / 2

    # Input Y-splitter
    # Trunk
    waveguide_straight(cell, 0, 0, MZI_SPLIT_L * 0.3, 0)
    # Upper branch
    waveguide_sbend(cell, MZI_SPLIT_L * 0.3, 0, MZI_SPLIT_L, half_sep)
    # Lower branch
    waveguide_sbend(cell, MZI_SPLIT_L * 0.3, 0, MZI_SPLIT_L, -half_sep)

    # Parallel arms (electrode region)
    arm_start = MZI_SPLIT_L
    arm_end = MZI_SPLIT_L + MZI_ARM_L

    # Upper arm waveguide
    waveguide_straight(cell, arm_start, half_sep, arm_end, half_sep)
    # Lower arm waveguide
    waveguide_straight(cell, arm_start, -half_sep, arm_end, -half_sep)

    # Electrodes (ground-signal-ground)
    el_y_top = half_sep + WG_W / 2 + MZI_EL_GAP
    el_y_mid_top = half_sep - WG_W / 2 - MZI_EL_GAP
    el_y_mid_bot = -half_sep + WG_W / 2 + MZI_EL_GAP
    el_y_bot = -half_sep - WG_W / 2 - MZI_EL_GAP

    # Signal electrode (between arms)
    cell.add(gdstk.rectangle(
        (arm_start, el_y_mid_top - MZI_EL_W),
        (arm_end, el_y_mid_bot + MZI_EL_W),
        layer=LY_METAL_EL[0], datatype=LY_METAL_EL[1]
    ))
    # Ground electrode (top)
    cell.add(gdstk.rectangle(
        (arm_start, el_y_top),
        (arm_end, el_y_top + MZI_EL_W),
        layer=LY_METAL_EL[0], datatype=LY_METAL_EL[1]
    ))
    # Ground electrode (bottom)
    cell.add(gdstk.rectangle(
        (arm_start, el_y_bot - MZI_EL_W),
        (arm_end, el_y_bot),
        layer=LY_METAL_EL[0], datatype=LY_METAL_EL[1]
    ))

    # Output Y-combiner
    out_start = arm_end
    out_end = arm_end + MZI_SPLIT_L
    waveguide_sbend(cell, out_start, half_sep, out_end - MZI_SPLIT_L * 0.3, 0)
    waveguide_sbend(cell, out_start, -half_sep, out_end - MZI_SPLIT_L * 0.3, 0)
    waveguide_straight(cell, out_end - MZI_SPLIT_L * 0.3, 0, out_end, 0)

    cell.add(gdstk.Label("MZI", (MZI_TOTAL_L / 2, half_sep + 15),
                          layer=LY_LABEL[0], texttype=LY_LABEL[1]))
    return cell


def add_sfg_element(lib, pair_name, poling_period, name=None):
    """
    Create a single PPLN SFG element cell.
    Waveguide input on left (0,0), output on right (SFG_L, 0).
    Poling pattern overlaid on the waveguide.
    """
    if name is None:
        name = f"SFG_{pair_name}"
    cell = lib.new_cell(name)

    # Waveguide through the PPLN section
    waveguide_straight(cell, 0, 0, SFG_L, 0)

    # Poling pattern — alternating domains
    n_periods = int(SFG_L / poling_period)
    for p in range(n_periods):
        x_start = p * poling_period
        x_end = x_start + poling_period / 2  # half-period is poled
        if x_end > SFG_L:
            x_end = SFG_L
        cell.add(gdstk.rectangle(
            (x_start, -SFG_PPLN_W / 2),
            (x_end, SFG_PPLN_W / 2),
            layer=LY_PPLN[0], datatype=LY_PPLN[1]
        ))

    cell.add(gdstk.Label(
        f"{pair_name} (Λ={poling_period:.1f}μm)",
        (SFG_L / 2, SFG_PPLN_W / 2 + 3),
        layer=LY_LABEL[0], texttype=LY_LABEL[1]
    ))
    return cell


def add_detector(lib, name="DETECTOR"):
    """Create a photodetector cell (Ge-on-LN or bonded)."""
    cell = lib.new_cell(name)

    # Waveguide input
    waveguide_straight(cell, 0, 0, 10, 0)

    # Detector active area
    cell.add(gdstk.rectangle(
        (10, -DET_SIZE / 2), (10 + DET_SIZE, DET_SIZE / 2),
        layer=LY_DETECTOR[0], datatype=LY_DETECTOR[1]
    ))

    # Contact opening
    inset = (DET_SIZE - DET_CONTACT) / 2
    cell.add(gdstk.rectangle(
        (10 + inset, -DET_CONTACT / 2),
        (10 + DET_SIZE - inset, DET_CONTACT / 2),
        layer=LY_DET_CONTACT[0], datatype=LY_DET_CONTACT[1]
    ))

    # Cladding opening over detector
    cell.add(gdstk.rectangle(
        (8, -DET_SIZE / 2 - 2), (10 + DET_SIZE + 2, DET_SIZE / 2 + 2),
        layer=LY_CLAD_OPEN[0], datatype=LY_CLAD_OPEN[1]
    ))

    cell.add(gdstk.Label("DET", (10 + DET_SIZE / 2, DET_SIZE / 2 + 5),
                          layer=LY_LABEL[0], texttype=LY_LABEL[1]))
    return cell


def add_wdm_combiner(lib, name="WDM_3TO1"):
    """
    3-input WDM combiner using cascaded Y-junctions.
    Inputs at y = -spacing, 0, +spacing on the left.
    Output at (0) on the right.
    """
    cell = lib.new_cell(name)
    spacing = 15.0
    stage1_l = 60.0
    stage2_l = 60.0

    # First stage: combine inputs 0+1
    waveguide_straight(cell, 0, -spacing, stage1_l * 0.3, -spacing)
    waveguide_straight(cell, 0, 0, stage1_l * 0.3, 0)
    waveguide_sbend(cell, stage1_l * 0.3, -spacing, stage1_l, -spacing / 2)
    waveguide_sbend(cell, stage1_l * 0.3, 0, stage1_l, -spacing / 2)

    # Third input passes through
    waveguide_straight(cell, 0, spacing, stage1_l, spacing)

    # Second stage: combine result + input 2
    mid_x = stage1_l
    waveguide_straight(cell, mid_x, -spacing / 2, mid_x + stage2_l * 0.3, -spacing / 2)
    waveguide_sbend(cell, mid_x, spacing, mid_x + stage2_l * 0.3, spacing / 4)
    waveguide_sbend(cell, mid_x + stage2_l * 0.3, -spacing / 2, mid_x + stage2_l, 0)
    waveguide_sbend(cell, mid_x + stage2_l * 0.3, spacing / 4, mid_x + stage2_l, 0)

    # Output
    total_l = stage1_l + stage2_l
    waveguide_straight(cell, total_l, 0, total_l + 10, 0)

    cell.add(gdstk.Label("WDM 3→1", (total_l / 2, spacing + 8),
                          layer=LY_LABEL[0], texttype=LY_LABEL[1]))
    return cell


def add_bond_pad(cell, x, y, label=""):
    """Add a bond pad at (x, y)."""
    cell.add(gdstk.rectangle(
        (x - PAD_SIZE / 2, y - PAD_SIZE / 2),
        (x + PAD_SIZE / 2, y + PAD_SIZE / 2),
        layer=LY_METAL_PAD[0], datatype=LY_METAL_PAD[1]
    ))
    cell.add(gdstk.rectangle(
        (x - PAD_SIZE / 2 + 5, y - PAD_SIZE / 2 + 5),
        (x + PAD_SIZE / 2 - 5, y + PAD_SIZE / 2 - 5),
        layer=LY_CLAD_OPEN[0], datatype=LY_CLAD_OPEN[1]
    ))
    if label:
        cell.add(gdstk.Label(label, (x, y + PAD_SIZE / 2 + 5),
                              layer=LY_LABEL[0], texttype=LY_LABEL[1]))


# =====================================================================
# Main layout
# =====================================================================
def main():
    lib = gdstk.Library("WTernary_Fab")
    top = lib.new_cell("HYBRID_SFG_FAB")

    # Create component cells
    coupler_cell = add_edge_coupler(lib)
    mzi_cell = add_mzi_gate(lib)
    det_cell = add_detector(lib)
    combiner_cell = add_wdm_combiner(lib)

    # Create SFG cells (one per frequency pair)
    sfg_cells = {}
    for pair, period in POLING_PERIODS.items():
        sfg_cells[pair] = add_sfg_element(lib, pair, period)

    # =========================================================
    # CHIP FLOORPLAN
    # =========================================================
    # Left edge: laser inputs (edge couplers)
    # Then: vertical distribution + per-row MZI gates + WDM combiners
    # Center: 3×3 SFG chamber grid (each chamber = 6 PPLN sections)
    # Right: detectors + output routing
    # Top/Bottom edges: bond pads for electrodes

    input_edge_x = 50.0          # Left chip edge
    gate_region_x = 500.0        # Where MZI gates sit
    combiner_x = gate_region_x + MZI_TOTAL_L + 80
    chamber_x = combiner_x + 150  # Start of SFG chamber region

    row_ys = [600.0 + r * CHAMBER_PITCH_Y for r in range(N_ROWS)]

    # =========================================================
    # INPUT EDGE COUPLERS (5 total: 3 RGB + 2 weights)
    # =========================================================
    input_labels = ["R (1560nm)", "G (1540nm)", "B (1520nm)",
                    "+1 (1070nm)", "-1 (1040nm)"]
    input_ys = [row_ys[1] - 80, row_ys[1], row_ys[1] + 80,
                row_ys[2] + CHAMBER_PITCH_Y / 2 + 50,
                row_ys[2] + CHAMBER_PITCH_Y / 2 + 130]

    coupler_out_x = input_edge_x + TAPER_L

    for idx, (label, iy) in enumerate(zip(input_labels, input_ys)):
        ref = gdstk.Reference(coupler_cell, (input_edge_x, iy))
        top.add(ref)
        top.add(gdstk.Label(label, (input_edge_x + TAPER_L / 2, iy - 8),
                             layer=LY_LABEL[0], texttype=LY_LABEL[1]))

    # =========================================================
    # RGB VERTICAL DISTRIBUTION BUSES
    # =========================================================
    rgb_bus_x = coupler_out_x + 50
    rgb_ys = input_ys[:3]

    for i in range(3):
        bus_x = rgb_bus_x + i * 15
        # Horizontal from coupler output to bus
        waveguide_straight(top, coupler_out_x, rgb_ys[i], bus_x, rgb_ys[i])
        # Vertical bus spanning all rows
        bus_y_min = min(row_ys) - 40
        bus_y_max = max(row_ys) + 40
        waveguide_straight(top, bus_x, bus_y_min, bus_x, bus_y_max)

    # =========================================================
    # PER-ROW: MZI GATES → WDM COMBINER → ROW CHANNEL
    # =========================================================
    for r in range(N_ROWS):
        row_y = row_ys[r]
        combiner_spacing = 15.0  # must match WDM combiner input spacing

        for i in range(3):
            bus_x = rgb_bus_x + i * 15
            gate_y = row_y + (i - 1) * combiner_spacing
            mzi_x = gate_region_x + i * (MZI_TOTAL_L + 20)

            # S-bend from vertical bus to MZI input
            waveguide_sbend(top, bus_x, row_y, mzi_x, gate_y)

            # MZI gate
            ref = gdstk.Reference(mzi_cell, (mzi_x, gate_y))
            top.add(ref)

            # Waveguide from MZI output to combiner input
            mzi_out_x = mzi_x + MZI_TOTAL_L
            comb_in_x = combiner_x
            comb_in_y = row_y + (i - 1) * combiner_spacing
            waveguide_straight(top, mzi_out_x, gate_y, comb_in_x, comb_in_y)

        # WDM combiner
        ref = gdstk.Reference(combiner_cell, (combiner_x, row_y))
        top.add(ref)

        # Row input channel from combiner to first chamber
        comb_out_x = combiner_x + 130  # combiner total length
        first_chamber_x = chamber_x
        waveguide_straight(top, comb_out_x, row_y, first_chamber_x, row_y)

    # =========================================================
    # WEIGHT BUS DISTRIBUTION
    # =========================================================
    weight_coupler_out_x = coupler_out_x
    weight_bus_x_plus = chamber_x - 80
    weight_bus_x_minus = chamber_x - 50

    for w_idx, (w_iy, w_bus_x) in enumerate([
        (input_ys[3], weight_bus_x_plus),
        (input_ys[4], weight_bus_x_minus)
    ]):
        # Route from coupler to vertical weight bus
        waveguide_sbend(top, weight_coupler_out_x, w_iy, w_bus_x, w_iy)
        # Vertical bus
        waveguide_straight(top, w_bus_x, min(row_ys) - 60,
                           w_bus_x, max(row_ys) + 60)

    # =========================================================
    # SFG CHAMBERS (3×3 grid)
    # =========================================================
    sfg_pairs = ["R+1", "R-1", "G+1", "G-1", "B+1", "B-1"]
    sfg_y_spacing = 50.0  # vertical spacing between SFG elements in a chamber

    for row in range(N_ROWS):
        for col in range(N_COLS):
            ch_x = chamber_x + col * CHAMBER_PITCH_X
            ch_y = row_ys[row]

            # Chamber outline (floorplan layer, non-fab)
            ch_w = SFG_L + 80
            ch_h = (len(sfg_pairs) - 1) * sfg_y_spacing + 40
            top.add(gdstk.rectangle(
                (ch_x - 20, ch_y - ch_h / 2 - 20),
                (ch_x + SFG_L + 60, ch_y + ch_h / 2 + 20),
                layer=LY_FLOORPLAN[0], datatype=LY_FLOORPLAN[1]
            ))
            top.add(gdstk.Label(
                f"Chamber[{row},{col}]",
                (ch_x + SFG_L / 2, ch_y + ch_h / 2 + 30),
                layer=LY_LABEL[0], texttype=LY_LABEL[1]
            ))

            # Weight gate MZIs (2 per chamber, at entry from weight buses)
            # +1 gate feeds SFG pairs R+1, G+1, B+1 (indices 0, 2, 4)
            # -1 gate feeds SFG pairs R-1, G-1, B-1 (indices 1, 3, 5)
            weight_mzi_out_x = []
            weight_mzi_out_y = []
            for w_idx in range(2):
                gate_y = ch_y + (w_idx - 0.5) * 30
                gate_x = ch_x - 40 - MZI_TOTAL_L
                w_bus_x = weight_bus_x_plus if w_idx == 0 else weight_bus_x_minus

                # Tap from weight bus
                waveguide_sbend(top, w_bus_x, ch_y, gate_x, gate_y)

                # MZI gate for weight
                ref = gdstk.Reference(
                    mzi_cell, (gate_x, gate_y),
                )
                top.add(ref)

                # Track MZI output position
                mzi_out_x = gate_x + MZI_TOTAL_L
                weight_mzi_out_x.append(mzi_out_x)
                weight_mzi_out_y.append(gate_y)

                # Vertical distribution from MZI output to its 3 SFG elements
                # +1 feeds indices 0,2,4 ; -1 feeds indices 1,3,5
                dist_x = mzi_out_x + 15 + w_idx * 15
                waveguide_straight(top, mzi_out_x, gate_y, dist_x, gate_y)

                target_indices = [0, 2, 4] if w_idx == 0 else [1, 3, 5]
                target_sfg_ys = [ch_y + (si - (len(sfg_pairs) - 1) / 2) * sfg_y_spacing
                                 for si in target_indices]

                # Vertical bus for this weight
                ys_all = [gate_y] + target_sfg_ys
                waveguide_straight(top, dist_x, min(ys_all) - 5,
                                   dist_x, max(ys_all) + 5)

                # Horizontal taps from vertical bus to each SFG input
                for sfg_target_y in target_sfg_ys:
                    waveguide_straight(top, dist_x, sfg_target_y,
                                       ch_x - 8, sfg_target_y)

            # 6 SFG elements stacked vertically
            for s_idx, pair in enumerate(sfg_pairs):
                sfg_y = ch_y + (s_idx - (len(sfg_pairs) - 1) / 2) * sfg_y_spacing

                # Route from row input to SFG input (S-bend)
                # Input arrives from left, weight arrives from above/below
                # Both meet at the SFG entry — in reality a WDM coupler
                # combines them, but at this scale we show them converging
                waveguide_sbend(top, ch_x - 20, ch_y, ch_x - 8, sfg_y)

                # Short combining section into SFG
                waveguide_straight(top, ch_x - 8, sfg_y, ch_x, sfg_y)

                # SFG element
                ref = gdstk.Reference(sfg_cells[pair], (ch_x, sfg_y))
                top.add(ref)

                # Detector at SFG output
                det_x = ch_x + SFG_L + 5
                ref = gdstk.Reference(det_cell, (det_x, sfg_y))
                top.add(ref)

    # =========================================================
    # BOND PADS (along top and bottom edges)
    # =========================================================
    pad_y_top = max(row_ys) + CHAMBER_PITCH_Y / 2 + 200
    pad_y_bot = min(row_ys) - CHAMBER_PITCH_Y / 2 - 100

    # Gate control pads (27 gates)
    pad_x_start = gate_region_x
    for g in range(27):
        px = pad_x_start + g * PAD_PITCH
        add_bond_pad(top, px, pad_y_bot, f"G{g}")

    # Detector readout pads (54 detectors = 9 chambers × 6)
    for d in range(27):
        px = pad_x_start + d * PAD_PITCH
        add_bond_pad(top, px, pad_y_top, f"D{d}")

    # =========================================================
    # CHIP BORDER (deep etch for dicing)
    # =========================================================
    chip_x_min = 0
    chip_y_min = pad_y_bot - PAD_SIZE - 50
    chip_x_max = chamber_x + (N_COLS - 1) * CHAMBER_PITCH_X + SFG_L + 200
    chip_y_max = pad_y_top + PAD_SIZE + 50

    top.add(gdstk.rectangle(
        (chip_x_min, chip_y_min), (chip_x_max, chip_y_max),
        layer=LY_DEEP_ETCH[0], datatype=LY_DEEP_ETCH[1]
    ))

    top.add(gdstk.Label(
        "WAVELENGTH-TERNARY HYBRID SFG CHIP — FAB LEVEL",
        ((chip_x_min + chip_x_max) / 2, chip_y_max - 30),
        layer=LY_LABEL[0], texttype=LY_LABEL[1]
    ))

    # --- Write ---
    outpath = "hybrid_chip_fab.gds"
    lib.write_gds(outpath)
    chip_w_mm = (chip_x_max - chip_x_min) / 1000
    chip_h_mm = (chip_y_max - chip_y_min) / 1000
    print(f"Fab GDS written: {outpath}")
    print(f"  Chip size: {chip_x_max - chip_x_min:.0f} × {chip_y_max - chip_y_min:.0f} μm")
    print(f"           = {chip_w_mm:.1f} × {chip_h_mm:.1f} mm")
    print(f"  Edge couplers: 5 (3 RGB + 2 weight)")
    print(f"  MZI gates: 27 (9 input + 18 weight)")
    print(f"  SFG elements: 54 (6 per chamber × 9)")
    print(f"  Detectors: 54")
    print(f"  Bond pads: 54 (27 gate + 27 detector)")


if __name__ == "__main__":
    main()
