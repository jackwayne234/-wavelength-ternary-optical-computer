# Multi-Project Wafer (MPW) Reticle Integration Plan

**Document Version:** 1.0
**Date:** February 5, 2026
**Project:** Wavelength-Division Ternary Optical Computer
**Author:** Christopher Riner

---

## 1. Overview

This document outlines the reticle integration strategy for submitting ternary optical processor designs to Multi-Project Wafer (MPW) runs. MPW shuttles allow multiple designs to share a single reticle, dramatically reducing per-design fabrication costs for prototyping.

### Target Foundries
| Foundry | Platform | Key Capability |
|---------|----------|----------------|
| HyperLight | LiNbO3 | Native chi-2 nonlinearity (ideal for SFG) |
| Ligentec | Low-loss SiN | Best waveguide loss (<0.1 dB/cm) |
| AIM Photonics | Si + SiN | Domestic US option, mature PDK |
| Applied Nanotools | E-beam | High resolution for tight gaps |

---

## 2. Die Sizes for Design Variants

### Summary Table

| Design | Dimensions | Area | Purpose |
|--------|------------|------|---------|
| Single ALU (1-trit) | 350 x 250 um | 0.088 mm^2 | Fundamental verification |
| 9-trit Nonad | 1200 x 600 um | 0.72 mm^2 | Carry chain testing |
| 27x27 Systolic Array | 1.65 x 1.65 mm | 2.72 mm^2 | AI acceleration prototype |
| 81-trit Full Processor | 3.6 x 5.4 mm | 19.4 mm^2 | Full architecture demo |
| 81x81 Systolic Array | 4.7 x 4.7 mm | 22.1 mm^2 | Maximum compute density |

### Detailed Specifications

#### 2.1 Single ALU Test Structure (1-trit)
```
Dimensions: 350 x 250 um (0.35 x 0.25 mm)
Area: 0.088 mm^2

Components:
- 2x AWG demux (3-channel input)
- 6x Ring resonators (input selectors)
- 2x Wavelength combiners
- 1x MMI 2x2 coupler
- 1x SFG mixer (chi-2)
- 1x AWG demux (5-channel output)
- 5x Photodetectors

Purpose: Verify fundamental ternary arithmetic, SFG mixing, wavelength encoding
```

#### 2.2 9-trit Nonad
```
Dimensions: 1200 x 600 um (1.2 x 0.6 mm)
Area: 0.72 mm^2

Components:
- 9x Single ALU units
- Carry chain interconnects
- Shared clock distribution

Purpose: Validate multi-trit carry propagation, timing
```

#### 2.3 27x27 Systolic Array
```
Dimensions: 1650 x 1650 um (1.65 x 1.65 mm)
Area: 2.72 mm^2

Based on:
- PE size: 50 x 50 um
- PE spacing: 5 um
- PE pitch: 55 um
- Array: 27 x 27 = 729 PEs
- Dimensions: (27 * 55) + margins = ~1650 um

Components:
- 729 Processing Elements (multi-domain support)
- Weight loading bus
- Activation I/O buffers
- Clock distribution (center-out radial)

Purpose: AI acceleration prototype, matrix multiply verification
```

#### 2.4 81-trit Full Processor
```
Dimensions: 3600 x 5400 um (3.6 x 5.4 mm)
Area: 19.4 mm^2

Components:
- 81x Single ALU units
- 486 ring resonators
- 243 AWG demultiplexers
- 81 SFG mixers
- 405 photodetectors
- ~500 MMI couplers
- Centered frontend (Kerr clock, Y-junction)

Purpose: Full 81-trit word processing, 128-bit binary equivalent
```

#### 2.5 81x81 Systolic Array
```
Dimensions: 4700 x 4700 um (4.7 x 4.7 mm)
Area: 22.1 mm^2

Based on:
- PE pitch: 55 um
- Array: 81 x 81 = 6,561 PEs
- Array core: 81 * 55 = 4455 um
- With I/O buffers and margins: ~4700 um

Components:
- 6,561 Processing Elements
- LINEAR/LOG/LOG-LOG mode support
- Weight-stationary architecture
- 617 MHz clock distribution

Purpose: Maximum AI acceleration, 4.05 TMAC/s target
```

---

## 3. Scribe Lane Requirements

### Standard Scribe Lane Dimensions
```
Minimum width: 80 um (high-precision dicing)
Typical width: 100-150 um (standard blade dicing)
Maximum width: 200 um (laser dicing, thick wafers)

Recommendation: 120 um scribe lanes
- Compatible with most foundry processes
- Allows for dicing tolerance (+/- 10 um)
- Room for test pads within scribe lanes
```

### Scribe Lane Layout
```
         ┌────────────────────────────────────────────────┐
         │                  Die N                         │
         │                                                │
         ├──────────────────┬─────────────────────────────┤
         │                  │                             │
         │     Die A        │ ◄── 120 um ──►  Die B       │
         │                  │    Scribe Lane              │
         │                  │                             │
         ├──────────────────┴─────────────────────────────┤
         │                  Die M                         │
         └────────────────────────────────────────────────┘
```

### Scribe Lane Contents
- Vernier alignment markers for dicing
- Metal routing for PCM interconnects
- Test pad access points
- Corner fiducials

---

## 4. Alignment Mark Placement

### Corner Alignment Marks
```
Reticle Layout with Alignment Marks:

    [ALN]                                         [ALN]
      ┌─────────────────────────────────────────────┐
      │  ┌────┐  ┌────┐  ┌────┐  ┌────┐  ┌────┐   │
      │  │Die1│  │Die2│  │Die3│  │Die4│  │Die5│   │
      │  └────┘  └────┘  └────┘  └────┘  └────┘   │
      │                                           │
      │  ┌────┐  ┌────┐ [CTR] ┌────┐  ┌────┐     │
      │  │Die6│  │Die7│  ALN  │Die8│  │Die9│     │
      │  └────┘  └────┘       └────┘  └────┘     │
      │                                           │
      │  ┌────────────────┐  ┌──────────────┐    │
      │  │   Large Die    │  │   PCM Block  │    │
      │  │   (81-trit)    │  │              │    │
      │  └────────────────┘  └──────────────┘    │
      │                                           │
      └─────────────────────────────────────────────┘
    [ALN]                                         [ALN]

Legend:
  [ALN] = Alignment marks (200 x 200 um)
  [CTR] = Center alignment mark
```

### Alignment Mark Specifications
```
Corner Marks (4x required):
- Position: 500 um from reticle edge
- Size: 200 x 200 um
- Type: Cross-in-box or Vernier
- Layers: All lithography layers

Center Mark (1x optional but recommended):
- Position: Reticle center
- Size: 200 x 200 um
- Purpose: Rotation error detection

Interlayer Marks:
- Vernier scale: 0.1 um resolution
- Located adjacent to each die
```

---

## 5. Process Control Monitors (PCMs)

### 5.1 Waveguide Loss Test Structures

```
Purpose: Measure propagation loss (dB/cm) at operating wavelengths

Structure Type: Cutback Method
  ┌──────────────────────────────────────────────────────┐
  │                                                      │
  │  [IN]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[OUT]  │  L = 5 mm
  │                                                      │
  │  [IN]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[OUT]            │  L = 3 mm
  │                                                      │
  │  [IN]━━━━━━━━━━━━━━━━━━[OUT]                        │  L = 1 mm
  │                                                      │
  │  [IN]━━━━━━[OUT]                                    │  L = 0.3 mm
  │                                                      │
  └──────────────────────────────────────────────────────┘

Dimensions per structure: 6000 x 100 um (serpentine for longer paths)
Total PCM area: 6000 x 500 um = 3 mm^2

Test wavelengths:
- 1.550 um (C-band, "Red" input)
- 1.310 um (O-band)
- 1.216 um ("Green" input)
- 1.064 um (near-IR)
- 1.000 um ("Blue" input)

Pass criteria: Loss < 3 dB/cm at all wavelengths
```

### 5.2 Ring Resonator Test Structures

```
Purpose: Characterize resonance, Q-factor, extinction ratio, FSR

Structure Layout:
  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │  ┌─┐    ┌──┐    ┌───┐    ┌────┐    ┌─────┐    │
  │  │ │    │  │    │   │    │    │    │     │    │
  │  └─┘    └──┘    └───┘    └────┘    └─────┘    │
  │  R=5um  R=10um  R=15um   R=20um    R=25um     │
  │                                                 │
  │  Coupling gaps: 0.10, 0.15, 0.20, 0.25 um     │
  │                                                 │
  └─────────────────────────────────────────────────┘

Array configuration:
- 5 radii x 4 gap values = 20 ring variants
- Each ring: 80 x 80 um footprint
- Total: 20 x 80 x 80 um = 0.128 mm^2 per row
- Include 3 rows (different waveguide widths): 0.384 mm^2

Measurements:
- Resonance wavelength vs. temperature
- Q-factor (target > 10,000)
- Extinction ratio (target > 10 dB)
- Free spectral range (FSR)

Target specifications:
- Ring radius: 5 um (PDK minimum) or 0.8 um (simulated optimal)
- Coupling gap: 0.15 um (simulation verified)
- Extinction: > 10 dB
```

### 5.3 SFG Efficiency Monitors

```
Purpose: Verify chi-2 nonlinear mixing efficiency

Structure:
  ┌────────────────────────────────────────────────────────┐
  │                                                        │
  │  [1550nm]━┓                                           │
  │           ┣━━[SFG MIXER 20um]━━━[5ch AWG]━┳━[DET -2] │
  │  [1000nm]━┛        │                      ┣━[DET -1] │
  │                    │                      ┣━[DET  0] │
  │                  PPLN                     ┣━[DET +1] │
  │              (chi-2 region)               ┗━[DET +2] │
  │                                                        │
  │  Mixer lengths: 10, 15, 20, 25, 30 um                 │
  │                                                        │
  └────────────────────────────────────────────────────────┘

Test combinations:
- R+R (1.550+1.550) -> 0.775 um (DET_-2)
- R+G (1.550+1.216) -> 0.681 um (DET_-1)
- R+B (1.550+1.000) -> 0.608 um (DET_0)
- G+G (1.216+1.216) -> 0.608 um (DET_0)  ** CRITICAL: must match R+B **
- G+B (1.216+1.000) -> 0.549 um (DET_+1)
- B+B (1.000+1.000) -> 0.500 um (DET_+2)

Array configuration:
- 5 mixer lengths x 6 input combinations = 30 test structures
- Each structure: 400 x 300 um
- Total: 30 x 0.12 mm^2 = 3.6 mm^2

Pass criteria:
- Detectable SFG signal at all combinations
- R+B and G+G outputs within +/- 1 nm (confirms harmonic mean design)
- Conversion efficiency measurable (target: -20 dB or better)
```

### 5.4 Additional PCM Structures

```
AWG Characterization:
- 3-channel input demux (for ternary inputs)
- 5-channel output demux (for SFG results)
- Center wavelength accuracy: +/- 1 nm
- Channel isolation: > 20 dB
- Area: 1.5 mm^2

MMI Coupler Test:
- 1x2 splitters (50/50 target)
- 2x2 couplers (3dB)
- Splitting ratio tolerance: +/- 5%
- Area: 0.5 mm^2

Photodetector Response:
- Responsivity at 0.500-0.775 um
- Dark current measurement
- Bandwidth characterization
- Area: 0.5 mm^2

Bend Loss:
- Spiral waveguides at R = 5, 10, 15 um
- Loss per 90-degree bend
- Area: 0.3 mm^2

Total PCM Area: ~9 mm^2
```

---

## 6. Suggested Reticle Layout

### Option A: Small MPW Slot (5 x 5 mm)

```
┌─────────────────────────────────────────────────────────────┐
│ [ALN]                                                 [ALN] │
│   ┌───────────┬───────────┬───────────┬───────────┐        │
│   │  1-trit   │  1-trit   │  1-trit   │  1-trit   │        │
│   │  ALU #1   │  ALU #2   │  ALU #3   │  ALU #4   │        │
│   │ 350x250   │ 350x250   │ 350x250   │ 350x250   │        │
│   ├───────────┼───────────┴───────────┼───────────┤        │
│   │  1-trit   │                       │  1-trit   │        │
│   │  ALU #5   │    PCM: Waveguide     │  ALU #6   │        │
│   │ 350x250   │       Loss Test       │ 350x250   │        │
│   ├───────────┤      1500x800         ├───────────┤        │
│   │  9-trit   │                       │ Ring Res  │        │
│   │  Nonad    ├───────────────────────┤   Test    │        │
│   │ 1200x600  │   PCM: SFG Monitors   │  800x800  │        │
│   │           │      1500x800         │           │        │
│   └───────────┴───────────────────────┴───────────┘        │
│ [ALN]                                                 [ALN] │
└─────────────────────────────────────────────────────────────┘

Slot size: 5 x 5 mm = 25 mm^2
Die content:
  - 6x Single ALU (0.53 mm^2 total)
  - 1x 9-trit Nonad (0.72 mm^2)
  - Waveguide PCM (1.2 mm^2)
  - SFG PCM (1.2 mm^2)
  - Ring PCM (0.64 mm^2)

Scribe lanes: 120 um
Fill factor: ~20%
```

### Option B: Medium MPW Slot (10 x 10 mm)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ [ALN]                                                             [ALN] │
│   ┌─────────────────────────┬─────────────────────────────────────┐    │
│   │                         │  ┌─────┐┌─────┐┌─────┐┌─────┐      │    │
│   │     27x27 Systolic      │  │ ALU ││ ALU ││ ALU ││ ALU │      │    │
│   │        Array            │  │ #1  ││ #2  ││ #3  ││ #4  │      │    │
│   │      1650 x 1650        │  └─────┘└─────┘└─────┘└─────┘      │    │
│   │       729 PEs           │  ┌─────┐┌─────┐┌─────┐┌─────┐      │    │
│   │                         │  │ ALU ││ ALU ││ ALU ││ ALU │      │    │
│   │                         │  │ #5  ││ #6  ││ #7  ││ #8  │      │    │
│   │                         │  └─────┘└─────┘└─────┘└─────┘      │    │
│   ├─────────────────────────┼─────────────────────────────────────┤    │
│   │   9-trit Nonad #1       │   9-trit Nonad #2    │    9-trit   │    │
│   │     1200 x 600          │     1200 x 600       │   Nonad #3  │    │
│   ├─────────────────────────┼──────────────────────┼─────────────┤    │
│   │                         │                      │             │    │
│   │   PCM: Waveguide Loss   │   PCM: Ring Res.    │  PCM: SFG   │    │
│   │      2000 x 800         │     1500 x 1000     │  Monitors   │    │
│   │                         │                      │  1500x1200  │    │
│   ├─────────────────────────┴──────────────────────┼─────────────┤    │
│   │                                                │             │    │
│   │           PCM: AWG + MMI + Detectors          │   Spares    │    │
│   │                  3000 x 1500                   │             │    │
│   │                                                │             │    │
│   └────────────────────────────────────────────────┴─────────────┘    │
│ [ALN]                          [CTR]                            [ALN] │
└─────────────────────────────────────────────────────────────────────────┘

Slot size: 10 x 10 mm = 100 mm^2
Die content:
  - 1x 27x27 Systolic Array (2.72 mm^2)
  - 8x Single ALU (0.70 mm^2 total)
  - 3x 9-trit Nonad (2.16 mm^2)
  - Comprehensive PCM suite (~12 mm^2)

Fill factor: ~18%
Recommended for: First tape-out, comprehensive characterization
```

### Option C: Large MPW Slot (Full Reticle, 25 x 32 mm)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ [ALN]                                                                      [ALN] │
│   ┌────────────────────────────────┬──────────────────────────────────────┐     │
│   │                                │                                      │     │
│   │                                │        81x81 Systolic Array          │     │
│   │    81-trit Full Processor      │           4700 x 4700                │     │
│   │        3600 x 5400             │           6,561 PEs                  │     │
│   │                                │                                      │     │
│   │      (Full ALU word)           │      (AI Acceleration Target)       │     │
│   │                                │                                      │     │
│   │                                │                                      │     │
│   ├────────────────────────────────┼──────────────────────────────────────┤     │
│   │                                │                                      │     │
│   │   27x27 Systolic Array #1      │   27x27 Systolic Array #2           │     │
│   │       1650 x 1650              │       1650 x 1650                    │     │
│   │                                │                                      │     │
│   ├────────────┬───────────────────┼─────────────┬────────────────────────┤     │
│   │            │                   │             │                        │     │
│   │  9-trit x6 │  Single ALU x16   │  9-trit x6  │  Single ALU x16       │     │
│   │            │   (4x4 array)     │             │   (4x4 array)          │     │
│   │            │                   │             │                        │     │
│   ├────────────┴───────────────────┴─────────────┴────────────────────────┤     │
│   │                                                                        │     │
│   │                    PROCESS CONTROL MONITOR BLOCK                      │     │
│   │                           (Full Suite)                                 │     │
│   │   ┌──────────┬──────────┬──────────┬──────────┬──────────┬─────────┐ │     │
│   │   │ WG Loss  │ Ring Res │ SFG Mix  │ AWG Test │ MMI Test │ Detect  │ │     │
│   │   │  3 mm^2  │  2 mm^2  │  4 mm^2  │  2 mm^2  │  1 mm^2  │  1 mm^2 │ │     │
│   │   └──────────┴──────────┴──────────┴──────────┴──────────┴─────────┘ │     │
│   │                                                                        │     │
│   └────────────────────────────────────────────────────────────────────────┘     │
│ [ALN]                             [CTR]                                   [ALN] │
└──────────────────────────────────────────────────────────────────────────────────┘

Slot size: 25 x 32 mm = 800 mm^2 (full reticle, dedicated run)
Die content:
  - 1x 81-trit Full Processor (19.4 mm^2)
  - 1x 81x81 Systolic Array (22.1 mm^2)
  - 2x 27x27 Systolic Array (5.44 mm^2)
  - 12x 9-trit Nonad (8.64 mm^2)
  - 32x Single ALU (2.82 mm^2)
  - Full PCM suite (13 mm^2)

Total active: ~71 mm^2
Fill factor: ~9% (typical for photonics, routing dominates)
```

---

## 7. Die Separation and Dicing Notes

### Dicing Strategy

```
Recommended Method: Stealth Dicing (laser)
- Non-contact, no chipping
- Clean edges for fiber coupling
- Works well with SiN and LiNbO3

Alternative: Blade Dicing
- Lower cost
- Requires wider scribe lanes (150+ um)
- More edge chipping risk

Post-Dicing:
1. Edge polish if using blade dicing
2. Anti-reflection coating on facets
3. Visual inspection under microscope
```

### Edge Coupling Considerations

```
For fiber coupling at die edges:
- Spot-size converters near die edges
- Inverse tapers: 0.5 um -> 0.15 um (tip)
- Taper length: 200-500 um
- Include coupling test structures on each die

Placement:
  ┌─────────────────────────────────────────┐
  │                                         │
  │  [SSC]━━━━━━━ Die Content ━━━━━━━[SSC] │
  │                                         │
  │  SSC = Spot Size Converter              │
  │  Located within 50 um of die edge       │
  │                                         │
  └─────────────────────────────────────────┘
```

### Dicing Map Example

```
For 10x10 mm MPW slot:

    0mm    2mm    4mm    6mm    8mm   10mm
    ├──────┼──────┼──────┼──────┼──────┤
    │      │      │      │      │      │
2mm ├──────┼──────┼──────┼──────┼──────┤
    │      │  27x27 Array │      │      │
4mm ├──────┤             ├──────┼──────┤
    │ ALUs │             │ ALUs │ Ring │
6mm ├──────┼──────┬──────┼──────┼──────┤
    │Nonad │Nonad │Nonad │ SFG  │ AWG  │
8mm ├──────┼──────┼──────┼──────┼──────┤
    │ WG Loss Test       │ MMI  │ Det  │
10mm└──────┴──────┴──────┴──────┴──────┘

Dicing cuts: Horizontal at 2, 4, 6, 8 mm
             Vertical at 2, 4, 6, 8 mm
             (adjusted to actual die boundaries)
```

---

## 8. Typical MPW Slot Sizes and Fit

### Common MPW Offerings

| Foundry | Small Slot | Medium Slot | Large Slot |
|---------|-----------|-------------|------------|
| AIM Photonics | 2.5 x 2.5 mm | 5 x 5 mm | 10 x 10 mm |
| Ligentec | 3 x 3 mm | 6 x 6 mm | 12 x 12 mm |
| HyperLight | Custom | Custom | Custom |
| IMEC | 2 x 2 mm | 5 x 5 mm | 10 x 10 mm |

### Design Fit Matrix

| Design | 2.5 x 2.5 mm | 5 x 5 mm | 10 x 10 mm |
|--------|-------------|----------|------------|
| Single ALU (0.35 x 0.25) | 36x possible | 144x possible | 576x possible |
| 9-trit Nonad (1.2 x 0.6) | 2x possible | 16x possible | 64x possible |
| 27x27 Array (1.65 x 1.65) | No | 4x possible | 25x possible |
| 81-trit Proc (3.6 x 5.4) | No | No | 1x (tight fit) |
| 81x81 Array (4.7 x 4.7) | No | No | 2x possible |

### Recommended Strategy

**Phase 1: Initial Characterization (5 x 5 mm slot)**
- Focus on PCMs and single ALU verification
- 6-8 single ALUs with variations
- Full waveguide loss, ring, and SFG test suite
- Estimated cost: $3,000-8,000

**Phase 2: Array Validation (10 x 10 mm slot)**
- 27x27 systolic array
- Multiple 9-trit nonads
- Additional single ALUs for redundancy
- Expanded PCM coverage
- Estimated cost: $8,000-20,000

**Phase 3: Full System (dedicated run or large MPW)**
- 81-trit full processor
- 81x81 systolic array
- Complete characterization suite
- Estimated cost: $50,000-200,000+

---

## 9. Submission Checklist

### Before Tape-Out

- [ ] GDS files pass foundry DRC (Design Rule Check)
- [ ] Layer mapping confirmed with foundry PDK
- [ ] All ports accessible at die edges
- [ ] Alignment marks present at all corners
- [ ] PCM structures included
- [ ] Scribe lanes properly sized
- [ ] Text labels on correct layer (toggle-able)
- [ ] Dicing plan documented

### Files to Submit

1. `*.gds` - Layout files (one per design variant)
2. `DESIGN_SUMMARY.md` - Architecture documentation
3. `layer_map.csv` - PDK layer mapping
4. `test_plan.md` - Measurement procedures
5. `dicing_map.pdf` - Die separation guide

---

## 10. References

1. Design Summary: `/home/jackwayne/Desktop/Optical_computing/Phase3_Chip_Simulation/DESIGN_SUMMARY.md`
2. GDS Files: `/home/jackwayne/Desktop/Optical_computing/Research/data/gds/`
3. Foundry Inquiry: `/home/jackwayne/Desktop/Optical_computing/Phase3_Chip_Simulation/foundry_inquiry_email.txt`
4. Systolic Array Generator: `/home/jackwayne/Desktop/Optical_computing/Research/programs/nradix_architecture/optical_systolic_array.py`

---

*Document prepared for Multi-Project Wafer submission planning.*
*Wavelength-Division Ternary Optical Computer Project*
