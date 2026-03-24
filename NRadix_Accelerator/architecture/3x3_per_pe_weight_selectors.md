# 3×3 Proof-of-Concept: Per-PE Weight Selectors

## Overview
The 3×3 proof-of-concept uses explicit MZI-based wavelength selectors at each SFG chamber for independent weight programming per processing element. This differs from the scaled architecture's optical RAM hierarchy.

## Input Selectors (at rail start)
- One MZI wavelength selector per input lane (3 total)
- 2-bit electronic control selects which CW laser wavelength passes through
- Wavelength encoding: 1550nm (-1), 1310nm (0), 1064nm (+1)
- Selection stays constant for the computation cycle
- Fan-out via Y-junction to all 3 SFGs in that row

## Weight Selectors (per SFG chamber)
- One MZI wavelength selector per SFG chamber (9 total)
- 2-bit electronic control per selector
- Each selector independently picks: brown wavelength (+1), pink wavelength (-1), or blocks both (0)
- Weight bus runs vertically, one per column
- At each SFG intersection, the local MZI selector gates the weight

## Dataflow
1. Input trit encoded as wavelength at start of input rail
2. Input wavelength travels horizontally, entering each SFG in its row
3. At each SFG, the local weight selector independently picks the weight wavelength
4. SFG performs optical multiplication (input × weight via sum-frequency generation)
5. SFG output drops to electronic SUM accumulator at bottom of column
6. Column accumulator sums all 3 products electronically

## Control Interface
- 3 × 2-bit input selector controls (6 bits total for inputs)
- 9 × 2-bit weight selector controls (18 bits total for weights)
- Total: 24 control bits for full 3×3 matrix operation

## GDS Layer Map
| Layer | Name | Color | Function |
|-------|------|-------|----------|
| 0 | Chip Outline | Black | Die boundary |
| 1 | Red Light | Red | 1064nm input waveguide (+1) |
| 2 | Green Light | Green | 1310nm input waveguide (0) |
| 3 | Blue Light | Blue | 1550nm input waveguide (-1) |
| 4 | Brown | Brown | Weight waveguide (+1) |
| 5 | Pink | Pink | Weight waveguide (-1) |
| 6 | Purple | Purple | SFG chambers |
| 7 | Black | Black | Electronic SUM accumulators |

## Advantage over Column Broadcast
The per-PE weight selector approach allows any weight value at any position in the 3×3 matrix, enabling arbitrary 3×3 matrix-vector multiplication. The scaled architecture's column broadcast constrains all PEs in a column to the same weight per cycle.
