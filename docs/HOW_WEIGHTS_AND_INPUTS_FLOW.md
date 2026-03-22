# How Weights and Inputs Flow Through the Systolic Array

**Date:** 2026-03-22
**Status:** Architecture analysis — documents the physical data flow through the PE array

---

## Weight Distribution (One Per Column)

Weights live in electronic SRAM. Each column of the systolic array gets one weight value per clock cycle.

```
  SRAM holds weight matrix W as electronic values
  
  Column 0 weight: w₀ = +1    Column 1 weight: w₁ = -1    ...
         │                            │
         ▼                            ▼
  ┌─────────────┐              ┌─────────────┐
  │ Laser Select│              │ Laser Select│
  │ +1 → Blue   │              │ -1 → Red    │
  └──────┬──────┘              └──────┬──────┘
         │ Blue (1000nm)              │ Red (1550nm)
         ▼                            ▼
  ┌─────────────┐              ┌─────────────┐
  │  Splitter   │              │  Splitter   │
  │  Tree (1→81)│              │  Tree (1→81)│
  └─┬───┬───┬──┘              └─┬───┬───┬──┘
    │   │   │                    │   │   │
    ▼   ▼   ▼                    ▼   ▼   ▼
   PE  PE  PE  ...all 81        PE  PE  PE  ...all 81
   0,0 1,0 2,0  PEs in          0,1 1,1 2,1  PEs in
                 col 0                        col 1
```

One laser selector per column. One splitter tree fans the weight wavelength to all 81 PEs in that column. Every PE in column j sees the same weight wavelength.

## Input Distribution (One Per Row)

Input data also starts in SRAM. Each row gets one input value per clock cycle.

```
  SRAM holds input x₀ = -1 (Red)
         │
         ▼
  ┌─────────────┐
  │ Laser Select│
  │ -1 → Red    │
  └──────┬──────┘
         │ Red (1550nm)
         ▼
  ┌─────────────┐
  │  Splitter   │
  │  Tree (1→81)│
  └─┬───┬───┬──┘
    │   │   │
    ▼   ▼   ▼
   PE  PE  PE  ... all 81 PEs in row 0
   0,0 0,1 0,2
```

Each PE in a row sees the same input wavelength. The staggered timing of the systolic flow is handled by the controller — it feeds x₀ at cycle 0, x₁ at cycle 1, etc., with diagonal wavefront propagation.

## Inside One PE: The Multiply

For single-trit × single-trit multiplication, each PE uses a **Kerr mixer** (χ³ nonlinearity):

```
  input wavelength ──┐
                     ├──▶ [ Kerr Mixer (χ³) ] ──▶ photodetector(s) ──▶ product
  weight wavelength ─┘         30 μm LiNbO₃
```

The Kerr effect uses intensity-dependent phase modulation:
- **Same sign inputs** (R+R or B+B) → cross-phase modulation → output is Blue (+1)
- **Opposite sign inputs** (R+B) → destructive interference → output is Red (-1)
- **Zero input** (Green) → no intensity, no phase shift → output stays Green (0)

This implements the single-trit multiplication truth table:

| Input | Weight | Product | Physics |
|-------|--------|---------|---------|
| -1 (R) | -1 (R) | +1 (B) | Same sign → cross-phase mod |
| -1 (R) | 0 (G) | 0 (G) | Zero → no interaction |
| -1 (R) | +1 (B) | -1 (R) | Opposite sign → destructive |
| 0 (G) | any | 0 (G) | Zero → no interaction |
| +1 (B) | -1 (R) | -1 (R) | Opposite sign → destructive |
| +1 (B) | 0 (G) | 0 (G) | Zero → no interaction |
| +1 (B) | +1 (B) | +1 (B) | Same sign → cross-phase mod |

**Key:** No frequency conversion happens (unlike SFG for addition). The Kerr effect modulates phase, and interference at the output selects the correct wavelength.

## Accumulation (Electronic, Top → Bottom)

Each PE's product is detected by photodetector(s) and becomes an electronic value {-1, 0, +1}. A transistor adder accumulates:

```
                partial_sum_in (electronic, from PE above)
                       │
                       ▼
              ┌─────────────────┐
              │  ELECTRONIC     │
              │  ADDER          │
              │                 │
              │  product (from  │
              │  photodetectors)│
              │  + partial_sum  │
              │  = new_sum      │
              └────────┬────────┘
                       │
                       ▼
                partial_sum_out (electronic, to PE below)
```

**Important:** The partial sum widens as it descends. After accumulating 81 single-trit products (each ±1), the sum ranges from -81 to +81, which requires ~5 trits to represent. The electronic accumulator must be wider than 1 trit.

## Full Column View: 3 Rows Example

```
  SRAM: w₀=+1 → Blue laser → splitter
                    │ Blue to all PEs in col 0
                    │
  ┌─────────────────┼──────────────────────────────┐
  │                 │              partial_sum = 0  │
  │                 ▼                    │          │
  │ x₀(Red)───▶[Kerr: R×B]──▶[det]──▶[ADD]────────┤ psum = 0 + product₀
  │                 │                    │          │
  │                 ▼                    ▼          │
  │ x₁(Grn)───▶[Kerr: G×B]──▶[det]──▶[ADD]────────┤ psum = psum + product₁
  │                 │                    │          │
  │                 ▼                    ▼          │
  │ x₂(Blu)───▶[Kerr: B×B]──▶[det]──▶[ADD]────────┤ psum = psum + product₂
  │                                      │          │
  │                                      ▼          │
  │                                   RESULT y₀     │
  └─────────────────────────────────────────────────┘
```

## Domain Summary

| What | Domain | How |
|------|--------|-----|
| Weights loaded | SRAM → laser selector → optical waveguide | One laser per column, splitter tree to all PEs |
| Data loaded | SRAM → laser selector → optical waveguide | One laser per row, splitter tree to all PEs |
| Multiply | Optical (Kerr χ³) | Two wavelengths in, product wavelength out |
| Product readout | Optical → Electronic | Photodetector(s) per PE |
| Accumulate | Electronic | Transistor adder, partial sum flows top to bottom |
| Result | Electronic | Bottom of each column |

---

## What Has NOT Been Validated

The Kerr mixer (`mul_mixer`) has a GDS layout but **no FDTD simulation** confirming the multiplication truth table. Only the SFG mixer (for addition) has been FDTD validated with Meep. Validating the Kerr multiplication physics is an open task.
