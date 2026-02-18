# Design Rule Check (DRC) Specification
## N-Radix Wavelength-Division Ternary Optical Chip

**Version:** 1.1
**Date:** February 18, 2026
**Platform:** X-cut LiNbO3 (Lithium Niobate)
**Chip Size:** 10mm x 10mm
**Feature Size:** 500nm minimum
**Validation:** Circuit simulation 8/8 PASS | Monte Carlo 99.82% yield (10,000 trials) | Thermal 15-45C passive window

---

## 1. Layer Definitions

| GDS Layer | Datatype | Name | Purpose | Process |
|-----------|----------|------|---------|---------|
| 1 | 0 | WG | Waveguide core | RIE etch 400nm |
| 2 | 0 | SFG | SFG mixer region (chi2 addition) | PPLN poling |
| 3 | 0 | PD | Photodetector region | - |
| 4 | 0 | DFG | DFG mixer region (chi2 subtraction) | PPLN poling |
| 5 | 0 | KERR_RES | Kerr resonator region | - |
| 6 | 0 | AWG | AWG body | RIE etch |
| 7 | 0 | MUL | MUL mixer region (chi3 multiplication) | - |
| 10 | 0 | MTL1 | Heater metal (TiN) | Liftoff 100nm TiN |
| 12 | 0 | MTL2 | Bond pad metal (Ti/Au) | Liftoff 20nm Ti / 500nm Au |
| 13 | 0 | DOP_SA | Saturable absorber doping | Er/Yb implant |
| 14 | 0 | DOP_GAIN | Gain medium doping | Er/Yb implant |
| 100 | 0 | LABEL | Text labels | Non-fabricated |

---

## 2. Minimum Feature Sizes

### 2.1 Waveguide Layer (WG - Layer 1)

| Rule ID | Parameter | Min | Max | Unit | Notes |
|---------|-----------|-----|-----|------|-------|
| WG.W.1 | Waveguide width (single-mode) | 0.480 | 0.520 | um | Target: 0.500 um +/- 20nm |
| WG.W.2 | Mixer waveguide width | 0.780 | 0.820 | um | Target: 0.800 um for phase matching |
| WG.L.1 | Minimum waveguide length | 1.0 | - | um | - |
| WG.S.1 | Minimum waveguide spacing | 0.5 | - | um | Prevents evanescent coupling |
| WG.S.2 | Coupling gap (ring-to-bus) | 0.130 | 0.170 | um | Target: 0.150 um |
| WG.R.1 | Minimum bend radius | 5.0 | - | um | PDK minimum for ring resonators |
| WG.R.2 | Recommended bend radius | 10.0 | - | um | For low-loss routing |
| WG.A.1 | Maximum bend angle change | - | 90 | deg | Per single bend |

### 2.2 Heater Metal Layer (MTL1 - Layer 10)

| Rule ID | Parameter | Min | Max | Unit | Notes |
|---------|-----------|-----|-----|------|-------|
| MTL1.W.1 | Minimum heater width | 1.0 | - | um | - |
| MTL1.W.2 | Heater trace width (typical) | 2.0 | 10.0 | um | For MZI phase control |
| MTL1.S.1 | Minimum heater spacing | 2.0 | - | um | Thermal isolation |
| MTL1.L.1 | Minimum heater length | 5.0 | - | um | - |

### 2.3 Bond Pad Metal Layer (MTL2 - Layer 12)

| Rule ID | Parameter | Min | Max | Unit | Notes |
|---------|-----------|-----|-----|------|-------|
| MTL2.W.1 | Minimum pad dimension | 80 | - | um | - |
| MTL2.W.2 | Recommended pad size | 100 | 150 | um | Target: 100x100 um |
| MTL2.S.1 | Minimum pad-to-pad spacing | 50 | - | um | Wire bond clearance |
| MTL2.S.2 | Minimum pad-to-edge spacing | 100 | - | um | Dicing street |

### 2.4 PPLN Poling Regions (Layers 2, 4)

| Rule ID | Parameter | Min | Max | Unit | Notes |
|---------|-----------|-----|-----|------|-------|
| PPLN.P.1 | SFG poling period | 6.5 | 7.0 | um | For 1.55/1.0 um SFG |
| PPLN.P.2 | DFG poling period | 10.0 | 12.0 | um | For difference freq |
| PPLN.W.1 | Poling electrode width | 2.0 | - | um | - |
| PPLN.S.1 | Poling electrode spacing | 1.0 | - | um | - |
| PPLN.L.1 | SFG mixer length | 18.0 | 22.0 | um | Target: 20 um |
| PPLN.L.2 | DFG mixer length | 23.0 | 27.0 | um | Target: 25 um |
| PPLN.L.3 | Kerr mixer length | 28.0 | 32.0 | um | Target: 30 um |

### 2.5 Doping Regions (Layers 13, 14)

| Rule ID | Parameter | Min | Max | Unit | Notes |
|---------|-----------|-----|-----|------|-------|
| DOP.W.1 | Minimum doping region width | 2.0 | - | um | - |
| DOP.S.1 | Doping region spacing | 5.0 | - | um | Prevents diffusion overlap |
| DOP.ENC.1 | Doping enclosure of waveguide | 0.5 | - | um | Each side |

---

## 3. Spacing Rules

### 3.1 Same-Layer Spacing

| Rule ID | Layers | Min Spacing | Unit | Notes |
|---------|--------|-------------|------|-------|
| SP.1 | WG to WG | 0.5 | um | Non-coupled waveguides |
| SP.2 | WG to WG (coupled) | 0.15 | um | Intentional coupling |
| SP.3 | MTL1 to MTL1 | 2.0 | um | Thermal isolation |
| SP.4 | MTL2 to MTL2 | 50.0 | um | Wire bond clearance |
| SP.5 | SFG to SFG | 10.0 | um | Prevent phase mismatch |
| SP.6 | DFG to DFG | 10.0 | um | Prevent phase mismatch |
| SP.7 | AWG to AWG | 20.0 | um | - |

### 3.2 Different-Layer Spacing

| Rule ID | Layer 1 | Layer 2 | Min Spacing | Unit | Notes |
|---------|---------|---------|-------------|------|-------|
| SP.X.1 | WG | MTL1 | 0.5 | um | Heater-to-waveguide gap |
| SP.X.2 | WG | MTL2 | 5.0 | um | Keep pads away from optical |
| SP.X.3 | MTL1 | MTL2 | 5.0 | um | Prevent shorts |
| SP.X.4 | PD | WG | 0.0 | um | PD overlaps waveguide |

---

## 4. Enclosure Rules

### 4.1 Metal Enclosure

| Rule ID | Inner Layer | Outer Layer | Min Enclosure | Unit | Notes |
|---------|-------------|-------------|---------------|------|-------|
| ENC.1 | Via | MTL1 | 0.5 | um | Via must be enclosed by metal |
| ENC.2 | Via | MTL2 | 1.0 | um | Via to pad enclosure |
| ENC.3 | Contact | MTL2 | 2.0 | um | Contact area enclosure |

### 4.2 Doping Enclosure

| Rule ID | Inner Layer | Outer Layer | Min Enclosure | Unit | Notes |
|---------|-------------|-------------|---------------|------|-------|
| ENC.D.1 | WG | DOP_SA | 0.5 | um | SA region surrounds WG |
| ENC.D.2 | WG | DOP_GAIN | 0.5 | um | Gain region surrounds WG |

### 4.3 Mixer Region Enclosure

| Rule ID | Inner Layer | Outer Layer | Min Enclosure | Unit | Notes |
|---------|-------------|-------------|---------------|------|-------|
| ENC.M.1 | WG | SFG | 0.2 | um | SFG region surrounds WG |
| ENC.M.2 | WG | DFG | 0.2 | um | DFG region surrounds WG |
| ENC.M.3 | WG | MUL | 0.2 | um | MUL region surrounds WG |

---

## 5. Alignment Tolerances

### 5.1 Layer-to-Layer Alignment

| Rule ID | Reference Layer | Target Layer | Tolerance | Unit | Notes |
|---------|-----------------|--------------|-----------|------|-------|
| ALIGN.1 | WG | MTL1 | +/- 0.5 | um | Heater alignment |
| ALIGN.2 | WG | MTL2 | +/- 2.0 | um | Pad alignment |
| ALIGN.3 | WG | SFG/DFG | +/- 0.5 | um | Mixer alignment critical |
| ALIGN.4 | WG | DOP_SA | +/- 1.0 | um | Doping alignment |
| ALIGN.5 | WG | DOP_GAIN | +/- 1.0 | um | Doping alignment |
| ALIGN.6 | WG | PD | +/- 0.5 | um | Detector alignment |

### 5.2 Alignment Marks

| Parameter | Value | Unit | Notes |
|-----------|-------|------|-------|
| Mark size | 100 | um | Cross alignment marks |
| Mark location | All four corners | - | Chip corners |
| Inter-layer tolerance | +/- 0.5 | um | Between any two layers |

---

## 6. Component-Specific Rules

### 6.1 Ring Resonator

| Rule ID | Parameter | Min | Nom | Max | Unit |
|---------|-----------|-----|-----|-----|------|
| RING.R.1 | Ring radius | 4.4 | 5.0 | - | um |
| RING.G.1 | Bus-ring gap | 0.13 | 0.15 | 0.17 | um |
| RING.W.1 | Ring waveguide width | 0.48 | 0.50 | 0.52 | um |

### 6.2 MMI Coupler

| Rule ID | Parameter | Min | Nom | Max | Unit |
|---------|-----------|-----|-----|-----|------|
| MMI.W.1 | MMI width | 2.5 | 3.0 | 4.0 | um |
| MMI.L.1 | MMI length | 8.0 | 10.0 | 15.0 | um |
| MMI.G.1 | Output waveguide gap | 0.4 | 0.5 | 0.6 | um |

### 6.3 AWG Demultiplexer

| Rule ID | Parameter | Min | Nom | Max | Unit |
|---------|-----------|-----|-----|-----|------|
| AWG.W.1 | Array waveguide width | 0.48 | 0.50 | 0.52 | um |
| AWG.S.1 | Array waveguide pitch | 1.0 | 1.5 | 2.0 | um |
| AWG.R.1 | Free propagation region radius | 20.0 | - | - | um |

### 6.4 Photodetector

| Rule ID | Parameter | Min | Nom | Max | Unit |
|---------|-----------|-----|-----|-----|------|
| PD.W.1 | Detector width | 5.0 | 10.0 | 20.0 | um |
| PD.L.1 | Detector length | 10.0 | 20.0 | 50.0 | um |

---

## 7. Density Rules

### 7.1 Waveguide Density

| Rule ID | Parameter | Min | Max | Unit | Notes |
|---------|-----------|-----|-----|------|-------|
| DENS.WG.1 | WG density (local 50x50 um) | 5 | 70 | % | Etch uniformity |
| DENS.WG.2 | WG density (global) | 10 | 50 | % | Wafer bow |

### 7.2 Metal Density

| Rule ID | Parameter | Min | Max | Unit | Notes |
|---------|-----------|-----|-----|------|-------|
| DENS.MTL1.1 | MTL1 density (local 100x100 um) | 5 | 50 | % | Thermal management |
| DENS.MTL2.1 | MTL2 density (global) | - | 30 | % | Stress management |

### 7.3 Fill Rules

| Rule ID | Description | Notes |
|---------|-------------|-------|
| FILL.1 | Add dummy WG fills in low-density regions | If WG density < 10% |
| FILL.2 | Add MTL1 dummy fills | If MTL1 density < 5% |

---

## 8. Edge and Boundary Rules

### 8.1 Die Boundary

| Rule ID | Parameter | Value | Unit | Notes |
|---------|-----------|-------|------|-------|
| EDGE.1 | Minimum feature to die edge | 50 | um | All layers |
| EDGE.2 | Waveguide to die edge | 100 | um | For edge coupling |
| EDGE.3 | Bond pad to die edge | 100 | um | Dicing clearance |
| EDGE.4 | Dicing street width | 100 | um | Between dies |

### 8.2 Exclusion Zones

| Rule ID | Zone | Exclusion | Unit | Notes |
|---------|------|-----------|------|-------|
| EXCL.1 | Alignment mark zone | 150 | um | No other features |
| EXCL.2 | Fiber coupling zone | 50 | um | Clear path for fibers |

---

## 9. Electrical Rules

### 9.1 Heater Resistance

| Rule ID | Parameter | Min | Nom | Max | Unit |
|---------|-----------|-----|-----|-----|------|
| ELEC.R.1 | TiN sheet resistance | 50 | 75 | 100 | Ohm/sq |
| ELEC.R.2 | Total heater resistance | 100 | 500 | 2000 | Ohm |

### 9.2 Bond Pad

| Rule ID | Parameter | Value | Unit | Notes |
|---------|-----------|-------|------|-------|
| ELEC.BP.1 | Wire bond pull strength | > 5 | grams | QC requirement |
| ELEC.BP.2 | Pad pitch (minimum) | 150 | um | Standard wire bonder |

---

## 10. Process Quality Control

### 10.1 Acceptance Criteria

| Step | Measurement | Target | Tolerance | Unit |
|------|-------------|--------|-----------|------|
| Post-etch | Waveguide width | 500 | +/- 20 | nm |
| Post-etch | Etch depth | 400 | +/- 10 | nm |
| Post-etch | Sidewall angle | 87.5 | 85-90 | deg |
| Post-poling | Poling period | Target | +/- 50 | nm |
| Post-metal | Sheet resistance | 75 | 50-100 | Ohm/sq |
| Post-implant | SA absorption | > 3 | - | dB |
| Post-implant | Gain | > 10 | - | dB |
| Final | Insertion loss | < 3 | - | dB/cm |

---

## 11. KLayout DRC Script Template

```ruby
# N-Radix Optical Chip DRC Rules
# For use with KLayout DRC engine

# Layer definitions
WG = input(1, 0)
SFG = input(2, 0)
PD = input(3, 0)
DFG = input(4, 0)
KERR_RES = input(5, 0)
AWG = input(6, 0)
MUL = input(7, 0)
MTL1 = input(10, 0)
MTL2 = input(12, 0)
DOP_SA = input(13, 0)
DOP_GAIN = input(14, 0)

# ==== WAVEGUIDE RULES ====

# WG.W.1: Waveguide width check (0.48 - 0.52 um for single-mode)
WG.width(0.48.um).output("WG.W.1", "Waveguide too narrow (< 0.48 um)")
WG.width(0.52.um, nil).output("WG.W.1", "Waveguide too wide (> 0.52 um) - check if mixer")

# WG.S.1: Minimum waveguide spacing (non-coupled)
WG.space(0.5.um).output("WG.S.1", "Waveguide spacing < 0.5 um (unintentional coupling)")

# WG.S.2: Coupling gap check (informational - 0.13 to 0.17 um)
# Note: Gaps < 0.17um are intentional coupling regions

# ==== HEATER METAL RULES ====

# MTL1.W.1: Minimum heater width
MTL1.width(1.0.um).output("MTL1.W.1", "Heater width < 1.0 um")

# MTL1.S.1: Minimum heater spacing (thermal isolation)
MTL1.space(2.0.um).output("MTL1.S.1", "Heater spacing < 2.0 um")

# ==== BOND PAD RULES ====

# MTL2.W.1: Minimum pad dimension
MTL2.width(80.um).output("MTL2.W.1", "Bond pad < 80 um")

# MTL2.S.1: Minimum pad-to-pad spacing
MTL2.space(50.um).output("MTL2.S.1", "Pad spacing < 50 um")

# ==== SPACING RULES ====

# SP.X.1: Waveguide to heater spacing
WG.separation(MTL1, 0.5.um).output("SP.X.1", "WG to heater < 0.5 um")

# SP.X.2: Waveguide to bond pad spacing
WG.separation(MTL2, 5.0.um).output("SP.X.2", "WG to bond pad < 5.0 um")

# SP.X.3: Heater to bond pad spacing
MTL1.separation(MTL2, 5.0.um).output("SP.X.3", "Heater to bond pad < 5.0 um")

# ==== ENCLOSURE RULES ====

# ENC.D.1: SA doping must enclose waveguide by 0.5 um
WG.not_inside(DOP_SA.sized(-0.5.um)).and(DOP_SA).output("ENC.D.1", "SA doping enclosure < 0.5 um")

# ENC.D.2: Gain doping must enclose waveguide by 0.5 um
WG.not_inside(DOP_GAIN.sized(-0.5.um)).and(DOP_GAIN).output("ENC.D.2", "Gain doping enclosure < 0.5 um")

# ENC.M.1: SFG region must enclose waveguide by 0.2 um
WG.not_inside(SFG.sized(-0.2.um)).and(SFG).output("ENC.M.1", "SFG enclosure < 0.2 um")

# ENC.M.2: DFG region must enclose waveguide by 0.2 um
WG.not_inside(DFG.sized(-0.2.um)).and(DFG).output("ENC.M.2", "DFG enclosure < 0.2 um")

# ENC.M.3: MUL region must enclose waveguide by 0.2 um
WG.not_inside(MUL.sized(-0.2.um)).and(MUL).output("ENC.M.3", "MUL enclosure < 0.2 um")

# ==== DENSITY RULES ====

# DENS.WG.1: Waveguide density check (5-70% in 50x50 um window)
# Note: Requires density DRC which may need custom implementation

# ==== EDGE RULES ====

# Define chip boundary (10mm x 10mm)
chip_boundary = polygon_layer
# EDGE.1: Minimum feature to die edge
# Implement based on actual chip boundary definition

# ==== MIXER REGION RULES ====

# SFG/DFG mixer region spacing
SFG.space(10.um).output("SP.5", "SFG region spacing < 10 um")
DFG.space(10.um).output("SP.6", "DFG region spacing < 10 um")

# ==== ANTENNA RULES (for high-frequency signals) ====

# Heater traces should not have sharp corners
# MTL1.with_angle(0, 45).output("ANT.1", "Sharp metal corner")
```

---

## 12. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-05 | C. Riner | Initial release |
| 1.1 | 2026-02-18 | C. Riner | Updated to reflect circuit sim 8/8 PASS, Monte Carlo 99.82% yield, thermal analysis complete. Added references to validation documents. |

---

## 13. References

- Process Traveler: `Research/data/gds/masks/process_traveler.md`
- Design Summary: `CPU_Phases/Phase3_Chip_Simulation/DESIGN_SUMMARY.md`
- Circuit Simulation (8/8 PASS): `NRadix_Accelerator/circuit_sim/simulate_9x9.py`
- Circuit Simulation Plan: `NRadix_Accelerator/docs/CIRCUIT_SIMULATION_PLAN.md`
- Monte Carlo Analysis (99.82% yield): `NRadix_Accelerator/docs/MONTE_CARLO_ANALYSIS.md`
- Thermal Sensitivity (15-45C passive): `NRadix_Accelerator/docs/THERMAL_SENSITIVITY.md`
- Layer Mapping (5 foundries): `NRadix_Accelerator/docs/LAYER_MAPPING.md`
- Monolithic 9x9 Validation: `NRadix_Accelerator/docs/MONOLITHIC_9x9_VALIDATION.md`
- GDSFactory Generic PDK documentation
- LiNbO3 photonic process design rules

---

*N-Radix Wavelength-Division Ternary Optical Computer Project -- updated 2026-02-18*
