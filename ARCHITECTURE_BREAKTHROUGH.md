# NRadix Full MAC Architecture — Breakthrough Session 2026-03-03

## The Key Insight

The output is encoded in TWO dimensions — both are purely wavelength-selective, no power/phase/magnitude:

1. **Which port** the signal exits → encodes the coarse value (the "tens")
2. **Which frequency** arrives at that port → encodes the fine value (the "units")

Together: 9 ports × 9 frequencies = **81 unique (port, frequency) pairs** covering the full output space.

---

## Full Architecture

### Inputs
- 9 channels, each carrying one of 3 frequencies:
  - −1 → 191.0 THz
  - 0  → 194.0 THz
  - +1 → 201.0 THz

### Weights
- Binary {−1, +1} per SFG, encoded as frequencies
- 3 fixed CW laser sources feed a wavelength-selective routing network
- Each of the 81 SFG cells receives the appropriate weight frequency via routing
- SFGs are passive and fixed after fabrication — programmability lives entirely in the routing layer

### Compute
- Each SFG: f_input + f_weight → f_product (wavelength encodes product value)
- Cascade of SFG stages accumulates products
- Each stage output frequency encodes the running sum
- Final stage produces one of 81 unique frequencies

### Output Encoding (2D wavelength)
```
Port 1  →  f1..f9   answers  1– 9
Port 2  →  f1..f9   answers 10–18
Port 3  →  f1..f9   answers 19–27
Port 4  →  f1..f9   answers 28–36
Port 5  →  f1..f9   answers 37–45
Port 6  →  f1..f9   answers 46–54
Port 7  →  f1..f9   answers 55–63
Port 8  →  f1..f9   answers 64–72
Port 9  →  f1..f9   answers 73–81
```

81 unique frequencies total, organized as 9 coarse bands × 9 fine sub-frequencies.
Same conceptual f1-f9 at each port, but physically distinct absolute frequencies per band.
Identical to how DWDM organizes channels — mature, manufacturable.

### Constraints
- Wavelength-selective routing ONLY — no power, phase, or magnitude detection
- All SFGs passive and fixed after fabrication
- Platform: SiN/SiO₂, telecom C/L band
- Programmability: routing layer only

### Optimizer Freedom
- Frequency assignments for all 81 output channels
- Number and topology of SFG cascade stages
- Waveguide routing geometry
- Coarse/fine band spacing

---

## Inverse Design Problem Statement

Design a photonic circuit using SFGs and waveguides that:
- Takes 9 ternary inputs {−1, 0, +1} encoded as frequencies {191, 194, 201 THz}
- Applies binary weights {−1, +1} per SFG via wavelength-selective routing
- Cascades as many SFG stages as needed to accumulate all 9 weighted inputs
- Produces a final output frequency that routes to exactly one of 81 (port, sub-frequency) pairs
- All routing is wavelength-selective only

Add as many SFGs and waveguides as needed.

---

## Why This Works

- DWDM-style 2D encoding is a proven photonic technique
- No new physics required — SFG, AWG, and wavelength routing are all validated
- The cascade naturally builds up frequency as it accumulates — frequency IS the running sum
- Output is unambiguous: which port + which sub-frequency = exact answer, no measurement of power needed
