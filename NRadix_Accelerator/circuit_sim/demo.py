#!/usr/bin/env python3
"""
N-RADIX 9x9 Optical Chip — Interactive Demo

Visual demo of the monolithic 9x9 ternary optical chip.
Press a button, watch light propagate through 81 PEs.

Colors match the real wavelengths:
  Blue  = +1 (1064 nm)
  Green =  0 (1310 nm)
  Red   = -1 (1550 nm)

Author: N-Radix Project
Date: 2026-02-18
"""

import tkinter as tk
from tkinter import font as tkfont
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulate_9x9 import simulate_array_9x9

# =============================================================================
# Color scheme — matches real wavelengths
# =============================================================================

COLORS = {
    +1: "#3B82F6",   # Blue  (1064 nm)
    0:  "#22C55E",   # Green (1310 nm)
    -1: "#EF4444",   # Red   (1550 nm)
}
COLORS_LIGHT = {
    +1: "#BFDBFE",
    0:  "#BBF7D0",
    -1: "#FECACA",
}
COLOR_EMPTY = "#E5E7EB"
COLOR_BG = "#1E293B"
COLOR_PANEL = "#334155"
COLOR_TEXT = "#F1F5F9"
COLOR_DIM = "#94A3B8"
COLOR_GOLD = "#F59E0B"
COLOR_PASS = "#22C55E"

TRIT_LABEL = {+1: "+1", 0: " 0", -1: "-1"}
TRIT_SYMBOL = {+1: "+", 0: "0", -1: "-"}


# =============================================================================
# The 5 examples
# =============================================================================

EXAMPLES = [
    {
        "name": "Add Four Ones = 4",
        "desc": "Four +1 inputs, all weights +1 in column 0.\nThe column sums: 1+1+1+1 = 4.",
        "input": [+1, +1, +1, +1, 0, 0, 0, 0, 0],
        "weights": [
            [+1, 0, 0, 0, 0, 0, 0, 0, 0],
            [+1, 0, 0, 0, 0, 0, 0, 0, 0],
            [+1, 0, 0, 0, 0, 0, 0, 0, 0],
            [+1, 0, 0, 0, 0, 0, 0, 0, 0],
            [0,  0, 0, 0, 0, 0, 0, 0, 0],
            [0,  0, 0, 0, 0, 0, 0, 0, 0],
            [0,  0, 0, 0, 0, 0, 0, 0, 0],
            [0,  0, 0, 0, 0, 0, 0, 0, 0],
            [0,  0, 0, 0, 0, 0, 0, 0, 0],
        ],
    },
    {
        "name": "Identity: Output = Input",
        "desc": "Weight matrix = identity.\nWhat goes in, comes out.",
        "input": [+1, -1, 0, +1, -1, +1, 0, -1, +1],
        "weights": [[1 if i == j else 0 for j in range(9)] for i in range(9)],
    },
    {
        "name": "Negate Everything",
        "desc": "Weight = negative identity.\nEvery value flips sign: +1 becomes -1.",
        "input": [+1, +1, -1, 0, +1, -1, -1, +1, 0],
        "weights": [[-1 if i == j else 0 for j in range(9)] for i in range(9)],
    },
    {
        "name": "All Ones: 1+1+...+1 = 9",
        "desc": "Every input +1, every weight +1.\nEach column sums nine +1s = 9.",
        "input": [+1] * 9,
        "weights": [[+1] * 9 for _ in range(9)],
    },
    {
        "name": "Mixed Multiply-Accumulate",
        "desc": "Mixed +1/-1 inputs, interesting weight pattern.\nShows the chip doing real math with negatives.",
        "input": [+1, -1, +1, -1, +1, -1, +1, -1, +1],
        "weights": [
            [+1, -1,  0,  0,  0,  0,  0,  0,  0],
            [-1, +1, -1,  0,  0,  0,  0,  0,  0],
            [ 0, -1, +1, -1,  0,  0,  0,  0,  0],
            [ 0,  0, -1, +1, -1,  0,  0,  0,  0],
            [ 0,  0,  0, -1, +1, -1,  0,  0,  0],
            [ 0,  0,  0,  0, -1, +1, -1,  0,  0],
            [ 0,  0,  0,  0,  0, -1, +1, -1,  0],
            [ 0,  0,  0,  0,  0,  0, -1, +1, -1],
            [ 0,  0,  0,  0,  0,  0,  0, -1, +1],
        ],
    },
]


# =============================================================================
# GUI
# =============================================================================

class ChipDemo(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("N-RADIX 9x9 Optical Chip Demo")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)

        # Fonts
        self.font_title = tkfont.Font(family="Helvetica", size=16, weight="bold")
        self.font_btn = tkfont.Font(family="Helvetica", size=11)
        self.font_cell = tkfont.Font(family="Courier", size=11, weight="bold")
        self.font_label = tkfont.Font(family="Helvetica", size=10)
        self.font_desc = tkfont.Font(family="Helvetica", size=10, slant="italic")
        self.font_result = tkfont.Font(family="Courier", size=13, weight="bold")
        self.font_small = tkfont.Font(family="Helvetica", size=9)

        # State
        self.pe_cells = [[None]*9 for _ in range(9)]
        self.input_cells = [None]*9
        self.output_cells = [None]*9
        self.product_cells = [[None]*9 for _ in range(9)]
        self.weight_labels = [[None]*9 for _ in range(9)]
        self.animation_step = 0
        self.current_example = None
        self.current_result = None

        self._build_ui()

    def _build_ui(self):
        # ── Title ──
        title_frame = tk.Frame(self, bg=COLOR_BG, padx=20, pady=10)
        title_frame.pack(fill="x")

        tk.Label(
            title_frame, text="N-RADIX 9x9 Optical Chip",
            font=self.font_title, fg=COLOR_GOLD, bg=COLOR_BG,
        ).pack(side="left")

        tk.Label(
            title_frame, text="  Monolithic LiNbO3  |  81 PEs  |  Passive Photonic",
            font=self.font_small, fg=COLOR_DIM, bg=COLOR_BG,
        ).pack(side="left", padx=(10, 0))

        # ── Main content: buttons left, grid right ──
        main = tk.Frame(self, bg=COLOR_BG, padx=10, pady=5)
        main.pack(fill="both", expand=True)

        # Left panel — buttons
        left = tk.Frame(main, bg=COLOR_PANEL, padx=12, pady=12, relief="flat",
                        highlightbackground="#475569", highlightthickness=1)
        left.pack(side="left", fill="y", padx=(10, 10), pady=5)

        tk.Label(
            left, text="EXAMPLES", font=self.font_label,
            fg=COLOR_GOLD, bg=COLOR_PANEL,
        ).pack(pady=(0, 8))

        self.buttons = []
        for i, ex in enumerate(EXAMPLES):
            btn = tk.Button(
                left, text=f"  {i+1}. {ex['name']}  ",
                font=self.font_btn, bg="#475569", fg=COLOR_TEXT,
                activebackground=COLOR_GOLD, activeforeground=COLOR_BG,
                relief="flat", cursor="hand2", anchor="w",
                command=lambda idx=i: self.run_example(idx),
            )
            btn.pack(fill="x", pady=3)
            self.buttons.append(btn)

        # Description area
        self.desc_label = tk.Label(
            left, text="Pick an example to run.", wraplength=220,
            font=self.font_desc, fg=COLOR_DIM, bg=COLOR_PANEL,
            justify="left",
        )
        self.desc_label.pack(pady=(15, 5), fill="x")

        # Legend
        legend = tk.Frame(left, bg=COLOR_PANEL)
        legend.pack(pady=(15, 0))
        tk.Label(legend, text="WAVELENGTHS:", font=self.font_small,
                 fg=COLOR_DIM, bg=COLOR_PANEL).pack(anchor="w")
        for val, label, wl in [(+1, "+1  Blue", "1064nm"),
                                (0, " 0  Green", "1310nm"),
                                (-1, "-1  Red", "1550nm")]:
            row = tk.Frame(legend, bg=COLOR_PANEL)
            row.pack(anchor="w", pady=1)
            tk.Canvas(row, width=14, height=14, bg=COLORS[val],
                      highlightthickness=0).pack(side="left", padx=(0, 5))
            tk.Label(row, text=f"{label} ({wl})", font=self.font_small,
                     fg=COLOR_TEXT, bg=COLOR_PANEL).pack(side="left")

        # Right panel — the chip grid
        right = tk.Frame(main, bg=COLOR_BG, padx=10, pady=5)
        right.pack(side="left", fill="both", expand=True)

        self._build_grid(right)

    def _build_grid(self, parent):
        grid_frame = tk.Frame(parent, bg=COLOR_BG)
        grid_frame.pack(pady=5)

        cell_size = 44
        gap = 2

        # Column headers: "w0 w1 w2..."
        header_row = tk.Frame(grid_frame, bg=COLOR_BG)
        header_row.pack()
        tk.Label(header_row, text="", width=6, bg=COLOR_BG).pack(side="left")  # spacer for row labels
        tk.Label(header_row, text="weights (from top)", font=self.font_small,
                 fg=COLOR_DIM, bg=COLOR_BG).pack(side="left")

        # Weight labels row
        wlabel_row = tk.Frame(grid_frame, bg=COLOR_BG)
        wlabel_row.pack()
        tk.Label(wlabel_row, text="", width=6, bg=COLOR_BG).pack(side="left")
        for col in range(9):
            lbl = tk.Label(wlabel_row, text=f"w{col}", width=4,
                           font=self.font_small, fg=COLOR_DIM, bg=COLOR_BG)
            lbl.pack(side="left", padx=gap)

        # Input label
        inp_label = tk.Frame(grid_frame, bg=COLOR_BG)
        inp_label.pack(anchor="w")
        tk.Label(inp_label, text=" input", font=self.font_small,
                 fg=COLOR_DIM, bg=COLOR_BG).pack(side="left")

        # Main grid rows
        for row in range(9):
            row_frame = tk.Frame(grid_frame, bg=COLOR_BG)
            row_frame.pack()

            # Input cell (left edge)
            inp_cell = tk.Label(
                row_frame, text="", width=3, height=1,
                font=self.font_cell, bg=COLOR_EMPTY, fg="white",
                relief="flat", padx=2, pady=2,
            )
            inp_cell.pack(side="left", padx=(0, 6))
            self.input_cells[row] = inp_cell

            # Arrow
            tk.Label(row_frame, text="\u2192", fg=COLOR_DIM, bg=COLOR_BG,
                     font=self.font_small).pack(side="left", padx=(0, 4))

            # PE cells
            for col in range(9):
                cell = tk.Label(
                    row_frame, text="", width=3, height=1,
                    font=self.font_cell, bg=COLOR_EMPTY, fg="white",
                    relief="flat", padx=2, pady=2,
                )
                cell.pack(side="left", padx=gap, pady=gap)
                self.pe_cells[row][col] = cell

        # Arrow row between grid and output
        arrow_row = tk.Frame(grid_frame, bg=COLOR_BG)
        arrow_row.pack()
        tk.Label(arrow_row, text="", width=6, bg=COLOR_BG).pack(side="left")
        for col in range(9):
            tk.Label(arrow_row, text="\u2193", width=4,
                     font=self.font_small, fg=COLOR_DIM, bg=COLOR_BG
                     ).pack(side="left", padx=gap)

        # Output label
        tk.Label(grid_frame, text="  output (column sums)", font=self.font_small,
                 fg=COLOR_DIM, bg=COLOR_BG).pack(anchor="w")

        # Output cells
        out_row = tk.Frame(grid_frame, bg=COLOR_BG)
        out_row.pack()
        tk.Label(out_row, text="", width=6, bg=COLOR_BG).pack(side="left")
        for col in range(9):
            cell = tk.Label(
                out_row, text="", width=3, height=1,
                font=self.font_cell, bg=COLOR_EMPTY, fg="white",
                relief="flat", padx=2, pady=2,
            )
            cell.pack(side="left", padx=gap, pady=gap)
            self.output_cells[col] = cell

        # Result text
        self.result_frame = tk.Frame(parent, bg=COLOR_BG)
        self.result_frame.pack(pady=(10, 5))

        self.result_label = tk.Label(
            self.result_frame, text="", font=self.font_result,
            fg=COLOR_TEXT, bg=COLOR_BG,
        )
        self.result_label.pack()

        self.status_label = tk.Label(
            self.result_frame, text="", font=self.font_label,
            fg=COLOR_DIM, bg=COLOR_BG,
        )
        self.status_label.pack()

    def _color_for_value(self, val):
        """Get color for a trit value."""
        if val in COLORS:
            return COLORS[val]
        # For accumulated values outside {-1,0,+1}, use gold
        return COLOR_GOLD

    def _set_cell(self, cell, val, is_product=False):
        """Set a cell's display value and color."""
        if val is None:
            cell.configure(text="", bg=COLOR_EMPTY, fg="white")
            return

        if isinstance(val, int) and val in COLORS and not is_product:
            cell.configure(
                text=TRIT_LABEL.get(val, str(val)),
                bg=COLORS[val], fg="white",
            )
        else:
            # Accumulated value or product display
            bg = self._color_for_value(val) if isinstance(val, int) and val in COLORS else COLOR_GOLD
            cell.configure(
                text=str(val) if isinstance(val, int) else val,
                bg=bg, fg=COLOR_BG if bg == COLOR_GOLD else "white",
            )

    def clear_grid(self):
        """Reset all cells to empty."""
        for row in range(9):
            self._set_cell(self.input_cells[row], None)
            for col in range(9):
                self._set_cell(self.pe_cells[row][col], None)
        for col in range(9):
            self._set_cell(self.output_cells[col], None)
        self.result_label.configure(text="")
        self.status_label.configure(text="")

    def run_example(self, idx):
        """Run an example with step-by-step animation."""
        ex = EXAMPLES[idx]
        self.current_example = ex

        # Highlight active button
        for i, btn in enumerate(self.buttons):
            if i == idx:
                btn.configure(bg=COLOR_GOLD, fg=COLOR_BG)
            else:
                btn.configure(bg="#475569", fg=COLOR_TEXT)

        self.desc_label.configure(text=ex["desc"])

        # Run the actual physics simulation
        self.current_result = simulate_array_9x9(
            ex["input"], ex["weights"], verbose=False
        )

        # Animate: clear, then fill step by step
        self.clear_grid()
        self.animation_step = 0
        self._animate_step(ex)

    def _animate_step(self, ex):
        """Animate the chip computation step by step."""
        step = self.animation_step

        if step == 0:
            # Step 0: Show inputs lighting up
            self.status_label.configure(text="Encoding inputs...", fg=COLOR_DIM)
            for row in range(9):
                self._set_cell(self.input_cells[row], ex["input"][row])
            self.animation_step = 1
            self.after(400, lambda: self._animate_step(ex))

        elif 1 <= step <= 9:
            # Steps 1-9: Light propagates through each column (left to right)
            col = step - 1
            self.status_label.configure(
                text=f"Light propagating... column {col}", fg=COLOR_DIM
            )
            for row in range(9):
                trit_a = ex["input"][row]
                trit_w = ex["weights"][row][col]
                product = trit_a * trit_w

                # Show the product in the PE cell
                if trit_a == 0 or trit_w == 0:
                    self._set_cell(self.pe_cells[row][col], 0)
                else:
                    self._set_cell(self.pe_cells[row][col], product)

            self.animation_step = step + 1
            self.after(200, lambda: self._animate_step(ex))

        elif step == 10:
            # Step 10: Show column sums (outputs)
            self.status_label.configure(text="Reading detectors...", fg=COLOR_DIM)
            result = self.current_result
            for col in range(9):
                val = result.detected_output[col]
                self._set_cell(self.output_cells[col], val, is_product=True)

            self.animation_step = 11
            self.after(400, lambda: self._animate_step(ex))

        elif step == 11:
            # Step 11: Show final result
            result = self.current_result
            out = result.detected_output
            expected = result.expected_output
            match = result.all_correct

            self.result_label.configure(
                text=f"Output: {out}",
                fg=COLOR_PASS if match else "#EF4444",
            )

            if match:
                self.status_label.configure(
                    text="PASS -- Detected output matches expected",
                    fg=COLOR_PASS,
                )
            else:
                self.status_label.configure(
                    text=f"Expected {expected} -- got {out}",
                    fg="#EF4444",
                )


def main():
    app = ChipDemo()
    # Center on screen
    app.update_idletasks()
    w = 920
    h = 680
    x = (app.winfo_screenwidth() // 2) - (w // 2)
    y = (app.winfo_screenheight() // 2) - (h // 2)
    app.geometry(f"{w}x{h}+{x}+{y}")
    app.mainloop()


if __name__ == "__main__":
    main()
