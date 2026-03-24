"""
Wavelength-Ternary Hybrid SFG Chip — GDS Generator
====================================================
Architecture (from CJ's hand-drawn design):

LEFT SIDE:
  3 RGB lasers (always on) → vertical distribution buses → 3 rows
  Each row has 3 color gates (selectors) before the merge junction
  Selected colors merge into the row's input channel

TOP:
  2 weight buses (+1 brown, -1 grey) always on
  Vertical taps down to each SFG chamber column

CENTER:
  3×3 grid of SFG chambers (9 total)
  Each chamber contains 6 SFG elements (3 colors × 2 weights)
  Each chamber has 2 weight gates (black circles) controlling +1/-1 entry

BOTTOM:
  9 detectors (one per chamber)
  3 column summers → dot products

Total controllable gates: 27 (9 input + 18 weight)
Total SFG elements: 54 (6 per chamber × 9 chambers)
"""

import gdstk
import math

# --- Layer definitions ---
LY_WAVEGUIDE   = (1, 0)   # Input waveguides
LY_SFG         = (2, 0)   # SFG elements inside chambers
LY_CHAMBER     = (3, 0)   # SFG chamber outlines
LY_DETECTOR    = (4, 0)   # Photodetector pads
LY_METAL       = (5, 0)   # Electronic traces (column summers)
LY_LABEL       = (6, 0)   # Text labels
LY_CHIP_BORDER = (7, 0)   # Chip outline
LY_WEIGHT_BUS  = (8, 0)   # Weight bus waveguides (+1, -1)
LY_GATE        = (9, 0)   # Controllable gates (black circles)
LY_LASER       = (10, 0)  # RGB laser sources

# --- Dimensions (microns) ---
CHAMBER_W = 100
CHAMBER_H = 90
SFG_W = 12
SFG_H = 3
SFG_ROWS = 3        # 3 color pairs
SFG_COLS = 2        # 2 weight pairs
SFG_SPACING_X = 18
SFG_SPACING_Y = 16

COL_PITCH = 180      # Horizontal spacing between columns
ROW_PITCH = 160      # Vertical spacing between rows
MARGIN = 100

WG_WIDTH = 3
GATE_RADIUS = 6      # Black circle gates
LASER_W = 20
LASER_H = 12
DET_W = 15
DET_H = 12

WEIGHT_BUS_SPACING = 30  # Spacing between +1 and -1 buses

N_ROWS = 3
N_COLS = 3


def add_circle(cell, cx, cy, r, layer):
    """Add a filled circle as a polygon."""
    pts = [(cx + r * math.cos(a), cy + r * math.sin(a))
           for a in [2 * math.pi * i / 32 for i in range(32)]]
    cell.add(gdstk.Polygon(pts, layer=layer[0], datatype=layer[1]))


def main():
    lib = gdstk.Library("WavelengthTernary_Hybrid")
    top = lib.new_cell("HYBRID_SFG_CHIP")

    # Origin for the chamber grid
    grid_ox = MARGIN + 180  # space for lasers + distribution + gates on left
    grid_oy = MARGIN + 80   # space for column summers at bottom

    # =========================================================
    # RGB LASERS (3 total, always on, far left)
    # =========================================================
    laser_x = MARGIN
    colors = ["R", "G", "B"]
    color_bus_spacing = 20    # x-spacing between R/G/B vertical buses
    color_tap_spacing = 18    # y-spacing between R/G/B taps at each row

    row_ys = [grid_oy + r * ROW_PITCH + CHAMBER_H / 2 for r in range(N_ROWS)]
    laser_center_y = (row_ys[0] + row_ys[-1]) / 2

    # X positions for each stage
    bus_x_positions = [laser_x + LASER_W + 15 + i * color_bus_spacing for i in range(3)]
    gate_region_x = bus_x_positions[-1] + 30   # gates start after rightmost bus
    merge_x = gate_region_x + 3 * color_bus_spacing + GATE_RADIUS + 15

    for i, color in enumerate(colors):
        laser_y = laser_center_y + (i - 1) * 30
        bus_x = bus_x_positions[i]

        # Laser source
        top.add(gdstk.rectangle(
            (laser_x, laser_y - LASER_H / 2),
            (laser_x + LASER_W, laser_y + LASER_H / 2),
            layer=LY_LASER[0], datatype=LY_LASER[1]
        ))
        top.add(gdstk.Label(
            f"{color} (always on)", (laser_x + LASER_W / 2, laser_y + LASER_H),
            layer=LY_LABEL[0], texttype=LY_LABEL[1]
        ))

        # Horizontal waveguide from laser to its vertical bus
        top.add(gdstk.rectangle(
            (laser_x + LASER_W, laser_y - WG_WIDTH / 2),
            (bus_x, laser_y + WG_WIDTH / 2),
            layer=LY_WAVEGUIDE[0], datatype=LY_WAVEGUIDE[1]
        ))

        # Vertical distribution bus (spans all rows)
        top.add(gdstk.rectangle(
            (bus_x - WG_WIDTH / 2, row_ys[0] - color_tap_spacing - 5),
            (bus_x + WG_WIDTH / 2, row_ys[-1] + color_tap_spacing + 5),
            layer=LY_WAVEGUIDE[0], datatype=LY_WAVEGUIDE[1]
        ))

        # Per-row: horizontal tap from bus → gate → merge
        this_gate_x = gate_region_x + i * color_bus_spacing

        for r in range(N_ROWS):
            row_cy = row_ys[r]
            tap_y = row_cy + (i - 1) * color_tap_spacing

            # Horizontal waveguide: bus → gate
            top.add(gdstk.rectangle(
                (bus_x + WG_WIDTH / 2, tap_y - WG_WIDTH / 2),
                (this_gate_x - GATE_RADIUS, tap_y + WG_WIDTH / 2),
                layer=LY_WAVEGUIDE[0], datatype=LY_WAVEGUIDE[1]
            ))

            # Input gate (selector)
            add_circle(top, this_gate_x, tap_y, GATE_RADIUS, LY_GATE)
            top.add(gdstk.Label(
                f"G{color}{r}",
                (this_gate_x, tap_y - GATE_RADIUS - 5),
                layer=LY_LABEL[0], texttype=LY_LABEL[1]
            ))

            # Horizontal waveguide: gate → merge junction
            top.add(gdstk.rectangle(
                (this_gate_x + GATE_RADIUS, tap_y - WG_WIDTH / 2),
                (merge_x, tap_y + WG_WIDTH / 2),
                layer=LY_WAVEGUIDE[0], datatype=LY_WAVEGUIDE[1]
            ))

    # =========================================================
    # MERGE JUNCTIONS + ROW INPUT CHANNELS
    # =========================================================
    for r in range(N_ROWS):
        row_cy = row_ys[r]

        # Merge bar — 3 color taps converge into 1 row channel
        merge_y_top = row_cy + color_tap_spacing + WG_WIDTH / 2
        merge_y_bot = row_cy - color_tap_spacing - WG_WIDTH / 2
        top.add(gdstk.rectangle(
            (merge_x, merge_y_bot),
            (merge_x + 4, merge_y_top),
            layer=LY_WAVEGUIDE[0], datatype=LY_WAVEGUIDE[1]
        ))

        # Horizontal input waveguide from merge into row of chambers
        row_end_x = grid_ox + (N_COLS - 1) * COL_PITCH + CHAMBER_W + 10
        top.add(gdstk.rectangle(
            (merge_x + 4, row_cy - WG_WIDTH / 2),
            (row_end_x, row_cy + WG_WIDTH / 2),
            layer=LY_WAVEGUIDE[0], datatype=LY_WAVEGUIDE[1]
        ))
        top.add(gdstk.Label(
            f"Row {r}", (merge_x + 15, row_cy + 8),
            layer=LY_LABEL[0], texttype=LY_LABEL[1]
        ))

    # =========================================================
    # WEIGHT BUSES (+1 and -1) — horizontal at top, tap down
    # =========================================================
    weight_bus_y_plus = grid_oy + (N_ROWS - 1) * ROW_PITCH + CHAMBER_H + 50
    weight_bus_y_minus = weight_bus_y_plus + WEIGHT_BUS_SPACING

    bus_x_start = grid_ox - 20
    bus_x_end = grid_ox + (N_COLS - 1) * COL_PITCH + CHAMBER_W + 20

    # +1 weight bus
    top.add(gdstk.rectangle(
        (bus_x_start, weight_bus_y_plus - WG_WIDTH / 2),
        (bus_x_end, weight_bus_y_plus + WG_WIDTH / 2),
        layer=LY_WEIGHT_BUS[0], datatype=LY_WEIGHT_BUS[1]
    ))
    top.add(gdstk.Label(
        "+1 WEIGHT BUS", (bus_x_start - 5, weight_bus_y_plus),
        layer=LY_LABEL[0], texttype=LY_LABEL[1]
    ))

    # -1 weight bus
    top.add(gdstk.rectangle(
        (bus_x_start, weight_bus_y_minus - WG_WIDTH / 2),
        (bus_x_end, weight_bus_y_minus + WG_WIDTH / 2),
        layer=LY_WEIGHT_BUS[0], datatype=LY_WEIGHT_BUS[1]
    ))
    top.add(gdstk.Label(
        "-1 WEIGHT BUS", (bus_x_start - 5, weight_bus_y_minus),
        layer=LY_LABEL[0], texttype=LY_LABEL[1]
    ))

    # Vertical taps from weight buses down to each column of chambers
    for col in range(N_COLS):
        col_cx = grid_ox + col * COL_PITCH + CHAMBER_W / 2
        tap_plus_x = col_cx - 12
        tap_minus_x = col_cx + 12

        # +1 tap (from bus down to top of topmost chamber)
        top_chamber_y = grid_oy + (N_ROWS - 1) * ROW_PITCH + CHAMBER_H
        top.add(gdstk.rectangle(
            (tap_plus_x - WG_WIDTH / 2, top_chamber_y),
            (tap_plus_x + WG_WIDTH / 2, weight_bus_y_plus),
            layer=LY_WEIGHT_BUS[0], datatype=LY_WEIGHT_BUS[1]
        ))

        # -1 tap
        top.add(gdstk.rectangle(
            (tap_minus_x - WG_WIDTH / 2, top_chamber_y),
            (tap_minus_x + WG_WIDTH / 2, weight_bus_y_minus),
            layer=LY_WEIGHT_BUS[0], datatype=LY_WEIGHT_BUS[1]
        ))

        # Continue weight taps vertically through all chambers in column
        bottom_chamber_y = grid_oy
        top.add(gdstk.rectangle(
            (tap_plus_x - WG_WIDTH / 2, bottom_chamber_y),
            (tap_plus_x + WG_WIDTH / 2, top_chamber_y),
            layer=LY_WEIGHT_BUS[0], datatype=LY_WEIGHT_BUS[1]
        ))
        top.add(gdstk.rectangle(
            (tap_minus_x - WG_WIDTH / 2, bottom_chamber_y),
            (tap_minus_x + WG_WIDTH / 2, top_chamber_y),
            layer=LY_WEIGHT_BUS[0], datatype=LY_WEIGHT_BUS[1]
        ))

    # =========================================================
    # SFG CHAMBERS (3×3 grid)
    # =========================================================
    for row in range(N_ROWS):
        for col in range(N_COLS):
            cx = grid_ox + col * COL_PITCH
            cy = grid_oy + row * ROW_PITCH

            # Chamber outline
            top.add(gdstk.rectangle(
                (cx, cy), (cx + CHAMBER_W, cy + CHAMBER_H),
                layer=LY_CHAMBER[0], datatype=LY_CHAMBER[1]
            ))

            # 6 SFG elements inside (3 rows × 2 cols)
            # Rows = R, G, B frequency tuning
            # Cols = +1 weight pair, -1 weight pair
            sfg_block_w = (SFG_COLS - 1) * SFG_SPACING_X + SFG_W
            sfg_block_h = (SFG_ROWS - 1) * SFG_SPACING_Y + SFG_H
            sfg_ox = cx + (CHAMBER_W - sfg_block_w) / 2
            sfg_oy = cy + (CHAMBER_H - sfg_block_h) / 2

            sfg_labels = [
                ["R+1", "R-1"],
                ["G+1", "G-1"],
                ["B+1", "B-1"],
            ]

            for sr in range(SFG_ROWS):
                for sc in range(SFG_COLS):
                    sx = sfg_ox + sc * SFG_SPACING_X
                    sy = sfg_oy + sr * SFG_SPACING_Y
                    top.add(gdstk.rectangle(
                        (sx, sy), (sx + SFG_W, sy + SFG_H),
                        layer=LY_SFG[0], datatype=LY_SFG[1]
                    ))
                    top.add(gdstk.Label(
                        sfg_labels[sr][sc],
                        (sx + SFG_W / 2, sy + SFG_H / 2),
                        layer=LY_LABEL[0], texttype=LY_LABEL[1]
                    ))

            # Weight gates — 2 black circles on top edge of chamber
            col_cx = cx + CHAMBER_W / 2
            gate_plus_x = col_cx - 12
            gate_minus_x = col_cx + 12
            gate_y = cy + CHAMBER_H  # top edge

            add_circle(top, gate_plus_x, gate_y, GATE_RADIUS, LY_GATE)
            add_circle(top, gate_minus_x, gate_y, GATE_RADIUS, LY_GATE)

            # Chamber label
            top.add(gdstk.Label(
                f"SFG[{row},{col}]",
                (cx + CHAMBER_W / 2, cy - 8),
                layer=LY_LABEL[0], texttype=LY_LABEL[1]
            ))

            # --- Detector output (bottom of chamber) ---
            det_x = cx + CHAMBER_W / 2 - DET_W / 2
            det_y = cy - 25

            # Waveguide from chamber bottom to detector
            top.add(gdstk.rectangle(
                (cx + CHAMBER_W / 2 - WG_WIDTH / 2, det_y + DET_H),
                (cx + CHAMBER_W / 2 + WG_WIDTH / 2, cy),
                layer=LY_WAVEGUIDE[0], datatype=LY_WAVEGUIDE[1]
            ))

            # Detector pad
            top.add(gdstk.rectangle(
                (det_x, det_y), (det_x + DET_W, det_y + DET_H),
                layer=LY_DETECTOR[0], datatype=LY_DETECTOR[1]
            ))

    # =========================================================
    # COLUMN SUMMERS — sum detectors in each column → dot product
    # =========================================================
    summer_y = grid_oy - 70

    for col in range(N_COLS):
        col_cx = grid_ox + col * COL_PITCH + CHAMBER_W / 2

        # Metal traces from each detector down to summer
        for row in range(N_ROWS):
            det_bottom_y = grid_oy + row * ROW_PITCH - 25
            top.add(gdstk.rectangle(
                (col_cx - 1.5, summer_y + 25),
                (col_cx + 1.5, det_bottom_y),
                layer=LY_METAL[0], datatype=LY_METAL[1]
            ))

        # Sum node — triangle pointing down
        top.add(gdstk.Polygon(
            [
                (col_cx - 18, summer_y + 25),
                (col_cx + 18, summer_y + 25),
                (col_cx, summer_y),
            ],
            layer=LY_METAL[0], datatype=LY_METAL[1]
        ))

        # Dot product label
        top.add(gdstk.Label(
            f"DOT[{col}]",
            (col_cx, summer_y - 10),
            layer=LY_LABEL[0], texttype=LY_LABEL[1]
        ))

    # =========================================================
    # CHIP BORDER
    # =========================================================
    chip_x_min = MARGIN - 20
    chip_y_min = summer_y - 30
    chip_x_max = grid_ox + (N_COLS - 1) * COL_PITCH + CHAMBER_W + 40
    chip_y_max = weight_bus_y_minus + 40
    top.add(gdstk.rectangle(
        (chip_x_min, chip_y_min), (chip_x_max, chip_y_max),
        layer=LY_CHIP_BORDER[0], datatype=LY_CHIP_BORDER[1]
    ))

    # Title
    top.add(gdstk.Label(
        "WAVELENGTH-TERNARY HYBRID SFG CHIP",
        ((chip_x_min + chip_x_max) / 2, chip_y_max - 15),
        layer=LY_LABEL[0], texttype=LY_LABEL[1]
    ))

    # --- Write ---
    outpath = "hybrid_chip_3x3.gds"
    lib.write_gds(outpath)
    print(f"GDS written: {outpath}")
    print(f"  Chip size: {chip_x_max - chip_x_min:.0f} x {chip_y_max - chip_y_min:.0f} um")
    print(f"  SFG chambers: {N_ROWS * N_COLS}")
    print(f"  SFG elements per chamber: {SFG_ROWS * SFG_COLS}")
    print(f"  Total SFG elements: {N_ROWS * N_COLS * SFG_ROWS * SFG_COLS}")
    n_input_gates = N_ROWS * 3  # 3 RGB gates per row
    n_weight_gates = N_ROWS * N_COLS * 2
    print(f"  Total gates: {n_input_gates} input + {n_weight_gates} weight = {n_input_gates + n_weight_gates}")


if __name__ == "__main__":
    main()
