# N-Radix Chip Packaging and Fiber Coupling Specification

**Version:** 1.0
**Date:** February 5, 2026
**Author:** Christopher Riner
**Document Type:** Packaging House / Test Lab Specification

---

## 1. Overview

This document specifies the packaging requirements for the N-Radix ternary optical processor chip. The chip is a photonic integrated circuit (PIC) fabricated on Lithium Niobate (LiNbO3) or Silicon Nitride (SiN) substrate, requiring optical fiber coupling for input and electrical connections for photodetector readout and thermal tuning.

**Chip Function:** 81-trit optical ALU (ternary arithmetic logic unit)
**Technology:** Silicon photonics with χ² nonlinear mixing
**Interface:** Optical input, electrical output

---

## 2. Chip Dimensions and Die Size

### Die Sizes by Configuration

| Configuration | Die Size (mm) | Active Area (mm²) | Notes |
|---------------|---------------|-------------------|-------|
| Single ALU (1 trit) | 0.35 × 0.25 | 0.09 | Minimum test structure |
| 9-trit nonad | 1.2 × 0.6 | 0.72 | Basic functional unit |
| 27×27 systolic array | ~8 × 8 | 64 | Standard AI accelerator |
| **81-trit full processor** | **3.6 × 5.4** | **19.4** | **Primary target** |
| 81×81 systolic array | ~24 × 24 | 576 | Maximum configuration |

### Recommended Die Dimensions (81-trit processor)

```
┌─────────────────────────────────────────┐
│                                         │
│           Die: 3.6 × 5.4 mm             │
│                                         │
│   ┌─────────────────────────────────┐   │
│   │                                 │   │
│   │     Active Area: 3.2 × 4.8 mm   │   │
│   │                                 │   │
│   │        (81 trit ALUs in         │   │
│   │         3×3 nonad grid)         │   │
│   │                                 │   │
│   └─────────────────────────────────┘   │
│                                         │
│   Scribe lane: 100 µm minimum           │
│   Edge exclusion: 200 µm                │
│                                         │
└─────────────────────────────────────────┘
```

---

## 3. Fiber Array Coupling Requirements

### 3.1 Recommended Coupling Method: Edge Coupling

Edge coupling is preferred for v1 prototypes due to broader wavelength acceptance and lower sensitivity to fabrication variations.

| Parameter | Value | Tolerance |
|-----------|-------|-----------|
| Coupling method | Edge coupling (butt coupling) | - |
| Fiber type | SMF-28 or equivalent | - |
| Mode field diameter | 10.4 µm @ 1550 nm | ±0.5 µm |
| Numerical aperture | 0.14 | - |
| V-groove pitch | 127 µm or 250 µm | ±0.5 µm |
| Fiber count (input) | 2 (Operand A, Operand B) | - |
| Fiber count (total) | 2-6 depending on configuration | - |

### 3.2 Edge Coupler Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| Coupler type | Inverse taper | Adiabatic mode converter |
| Taper tip width | 180 nm | Expanded mode matching |
| Taper length | 200-500 µm | Trade-off: length vs coupling |
| Waveguide width at chip | 500 nm | Single-mode at all λ |
| Coupling loss (target) | 1-2 dB per facet | Including mode mismatch |
| Alignment tolerance (1 dB) | ±1.0 µm lateral | X and Y directions |
| Alignment tolerance (1 dB) | ±0.5° angular | Pitch and yaw |

### 3.3 Wavelength Requirements

The fiber array must transmit the following wavelengths with minimal loss:

| Trit Value | Wavelength | Band | Purpose |
|------------|------------|------|---------|
| -1 (NEG) | 1550 nm | C-band | Operand encoding |
| 0 (ZERO) | 1310 nm | O-band | Operand encoding |
| +1 (POS) | 1064 nm | Near-IR | Operand encoding |

**Note:** Standard SMF-28 fiber is single-mode at all three wavelengths.

### 3.4 Alternative: Grating Couplers

For wafer-scale testing or applications requiring surface-normal coupling:

| Parameter | Value | Notes |
|-----------|-------|-------|
| Coupling angle | 8-12° from vertical | Foundry-dependent |
| Coupling loss | 3-5 dB per coupler | Higher than edge coupling |
| Bandwidth (3 dB) | ±20 nm | Wavelength-specific design |
| Polarization | TE preferred | TM requires different grating |
| Alignment tolerance | ±2 µm | More forgiving than edge |

**Recommendation:** Use grating couplers only for die-level testing. Production packaging should use edge coupling for lower loss and broader wavelength acceptance.

---

## 4. Bond Pad Locations and Sizes

### 4.1 Pad Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| Pad size | 100 × 100 µm | Standard wire bond compatible |
| Pad pitch (minimum) | 150 µm | 50 µm gap between pads |
| Pad metal | 20 nm Ti / 500 nm Au | Wire bond compatible |
| Wire bond type | Ball bond (Au) or wedge | 25 µm gold wire |
| Pull strength | >5 g | Qualification requirement |

### 4.2 Pad Categories

| Category | Count (81-trit) | Layer | Function |
|----------|-----------------|-------|----------|
| Photodetector readout | 405 | (12, 0) | 5 outputs per ALU × 81 ALUs |
| Heater control | 486 | (10, 0) | Ring resonator tuning (if MZI) |
| Carry chain I/O | 162 | (12, 0) | Carry in/out per trit |
| Ground | 16+ | (12, 0) | Distributed ground pads |
| Power (VDD) | 8+ | (12, 0) | Heater power supply |
| **Total pads** | **~1100** | - | Approximately |

### 4.3 Pad Ring Layout

```
                    TOP EDGE (5.4 mm)
    ┌────────────────────────────────────────────┐
    │ GND VDD PD PD PD ... (Detector outputs)    │
    │                                            │
  L │                                            │ R
  E │   ┌────────────────────────────────┐       │ I
  F │   │                                │       │ G
  T │   │      ACTIVE PHOTONIC           │       │ H
    │   │         REGION                 │       │ T
  E │   │                                │       │
  D │   │   (81 ALUs in 3×3 grid)        │       │ E
  G │   │                                │       │ D
  E │   │                                │       │ G
    │   └────────────────────────────────┘       │ E
    │                                            │
    │ HTR HTR HTR ... (Heater controls)          │
    └────────────────────────────────────────────┘
                   BOTTOM EDGE

    ▲ Fiber input (left edge, edge coupling)
```

### 4.4 Photodetector Pad Arrangement

Each ALU has 5 photodetector outputs arranged in a row:

```
┌─────┬─────┬─────┬─────┬─────┐
│DET  │DET  │DET  │DET  │DET  │
│ -2  │ -1  │  0  │ +1  │ +2  │
│     │     │     │     │     │
│BORROW│RESULT│RESULT│RESULT│CARRY│
└─────┴─────┴─────┴─────┴─────┘
  │     │     │     │     │
  └─────┴─────┴─────┴─────┴──── To TIA board
```

---

## 5. Electrical Connections

### 5.1 Photodetector Interface

| Parameter | Value | Notes |
|-----------|-------|-------|
| Detector type | Ge-on-Si or InGaAs | Broadband 500-775 nm |
| Output | Photocurrent | Requires external TIA |
| Responsivity | 0.5-1.0 A/W | Wavelength-dependent |
| Bandwidth | >1 GHz | Supports 617 MHz clock |
| Dark current | <10 nA | At -2V bias |
| Bias voltage | -1 to -3 V | Reverse bias |
| Sensitivity | -30 dBm | Minimum detectable power |

### 5.2 Heater Interface (MZI Switch Configuration)

| Parameter | Value | Notes |
|-----------|-------|-------|
| Heater material | 100 nm TiN | Resistive heating |
| Sheet resistance | 50-100 Ω/□ | Foundry-dependent |
| Heater resistance | 200-500 Ω | Typical per element |
| Power per heater | 10-50 mW | For π phase shift |
| Response time | 1-10 µs | Thermal time constant |
| Operating voltage | 1-5 V | Linear with power |

### 5.3 Electrical I/O Summary

| Signal Group | Count | Direction | Voltage | Notes |
|--------------|-------|-----------|---------|-------|
| DET_-2 to DET_+2 | 405 | Output | Photocurrent | Analog, to TIA |
| HEATER | 486 | Input | 0-5 V | Analog, DC tuning |
| CARRY_OUT | 81 | Output | Digital | To firmware |
| CARRY_IN | 81 | Input | Digital | From firmware |
| VDD | 8+ | Input | 3.3 V or 5 V | Heater power |
| GND | 16+ | - | 0 V | Star ground preferred |

---

## 6. Thermal Considerations

### 6.1 Heat Sources

| Component | Power (each) | Count | Total Power |
|-----------|--------------|-------|-------------|
| MZI heaters (active) | 20 mW | ~100 active | 2 W |
| Photodetectors | Negligible | 405 | <50 mW |
| Waveguides | Negligible | - | - |
| **Total chip dissipation** | - | - | **~2-3 W maximum** |

**Note:** The optical logic itself is passive and generates no heat. Heat is only from thermo-optic tuning elements.

### 6.2 Thermal Requirements

| Parameter | Value | Notes |
|-----------|-------|-------|
| Operating temperature | 20-40°C | Stable within ±0.1°C |
| Max junction temperature | 85°C | Standard commercial |
| Thermal resistance (target) | <5°C/W | Package to heatsink |
| Temperature stability | ±0.1°C | For wavelength stability |
| Warm-up time | <5 minutes | To reach thermal equilibrium |

### 6.3 Thermal Management Recommendations

1. **Die attach:** Use high thermal conductivity epoxy (>2 W/m·K) or AuSn solder
2. **Substrate:** Aluminum nitride (AlN) carrier for high thermal conductivity
3. **Heat spreading:** Copper heat spreader under substrate
4. **TEC option:** Thermoelectric cooler for precision temperature control
5. **Temperature sensor:** On-chip or package-mounted RTD/thermistor

```
    ┌─────────────────────────┐
    │      Optical Chip       │  Die attach (AuSn or epoxy)
    ├─────────────────────────┤
    │    AlN Submount (2mm)   │  High thermal conductivity
    ├─────────────────────────┤
    │   Cu Heat Spreader      │  Thermal spreading layer
    ├─────────────────────────┤
    │        TEC (opt)        │  Active temperature control
    ├─────────────────────────┤
    │      Package Base       │  Metal package or PCB
    └─────────────────────────┘
```

---

## 7. Recommended Packaging Approach

### 7.1 Development / Prototype Phase

**Recommendation:** Chip-on-Board (COB) or Bare Die on Submount

| Aspect | Specification |
|--------|---------------|
| Die mounting | Bare die on AlN submount |
| Wire bonding | Au wedge or ball bond |
| Fiber coupling | Active alignment with UV cure |
| Encapsulation | Glob top or lid (optional) |
| Form factor | Custom evaluation board |

**Advantages:**
- Lowest cost for small quantities
- Easy rework and debugging
- Direct access to all pads
- Flexible fiber routing

### 7.2 Production Phase

**Recommendation:** Butterfly Package or Custom Hermetic

| Package Type | Pros | Cons | Use Case |
|--------------|------|------|----------|
| Butterfly (14-pin) | Standard, proven | Limited I/O | Single ALU test |
| Custom hermetic | Full I/O, reliable | Higher cost | Production chip |
| Gold box | Hermetic, robust | Very high cost | Aerospace/mil |
| Open cavity | Cost-effective | Not hermetic | Lab/prototype |

### 7.3 Recommended Package Dimensions

For 81-trit processor (3.6 × 5.4 mm die):

| Parameter | Value |
|-----------|-------|
| Package footprint | 20 × 30 mm minimum |
| Package height | 5-8 mm (with fiber) |
| Cavity size | 10 × 15 mm minimum |
| Fiber exit | Single or dual side |
| Lead count | 100+ (multi-row or LGA) |

### 7.4 Fiber Pigtail Options

| Option | Fiber Type | Connector | Notes |
|--------|------------|-----------|-------|
| **Bare fiber** | SMF-28 | None | Lowest loss, splice to system |
| PM fiber | PANDA PM | FC/APC | If polarization critical |
| **Fiber array** | SMF-28 × 2-6 | V-groove block | Recommended for multi-port |
| Lensed fiber | SMF-28 + lens | FC/APC | Improved alignment tolerance |

---

## 8. Chip Layout with I/O Locations

### 8.1 ASCII Layout Diagram (81-trit Processor)

```
                              5.4 mm
    ◄──────────────────────────────────────────────►

    ┌──────────────────────────────────────────────┐  ▲
    │  PHOTODETECTOR OUTPUT PADS (Top Row)         │  │
    │  ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐   │  │
    │  │D0│D1│D2│D3│D4│..│..│..│..│..│..│D80│D81│  │  │
    │  └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘   │  │
    │                                              │  │
    │  ┌────────────────────────────────────────┐  │  │
    │  │ ZONE 6    │  ZONE 7    │   ZONE 8     │  │  │
    │  │ (9 ALUs)  │  (9 ALUs)  │   (9 ALUs)   │  │  │
    │  ├───────────┼────────────┼──────────────┤  │  │
 ▼  │  │ ZONE 3    │[FRONTEND]  │   ZONE 5     │  │  3.6
 F  │  │ (9 ALUs)  │Kerr Clock  │   (9 ALUs)   │  │  mm
 I  │  │           │ + Y-junc   │              │  │  │
 B  │  ├───────────┼────────────┼──────────────┤  │  │
 E  │  │ ZONE 0    │  ZONE 1    │   ZONE 2     │  │  │
 R  │  │ (9 ALUs)  │  (9 ALUs)  │   (9 ALUs)   │  │  │
    │  └────────────────────────────────────────┘  │  │
 I  │                                              │  │
 N  │  ┌──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┬──┐   │  │
 P  │  │H0│H1│H2│H3│H4│..│..│..│..│..│VDD│GND│  │   │  │
 U  │  └──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┴──┘   │  │
 T  │  HEATER CONTROL PADS (Bottom Row)           │  ▼
    └──────────────────────────────────────────────┘

    ◄── EDGE COUPLING ──►
        Input A (upper)
        Input B (lower)

        Facet polished
        to optical quality
```

### 8.2 Optical Port Locations

| Port | Edge | Position (from corner) | Purpose |
|------|------|------------------------|---------|
| input_a | Left | Y = 2.0 mm | Operand A input |
| input_b | Left | Y = 1.4 mm | Operand B input |
| (future) clock_out | Right | Y = 1.8 mm | Clock distribution (optional) |

### 8.3 Alignment Marks

| Location | Coordinates (mm) | Purpose |
|----------|------------------|---------|
| Top-left | (0.2, 3.4) | Primary alignment |
| Top-right | (5.2, 3.4) | Rotation check |
| Bottom-left | (0.2, 0.2) | Secondary reference |
| Bottom-right | (5.2, 0.2) | Verification |

Mark design: Cross pattern, 100 µm arms, 10 µm width

---

## 9. Assembly and Test Recommendations

### 9.1 Die Attach Process

1. **Substrate preparation:** Clean AlN submount with plasma
2. **Adhesive application:** Dispense thermal epoxy or AuSn preform
3. **Die placement:** ±10 µm accuracy using die bonder
4. **Cure:** Per adhesive datasheet (typically 150°C, 1 hour for epoxy)
5. **Inspection:** Verify void-free attachment via X-ray or acoustic microscopy

### 9.2 Wire Bonding Sequence

1. Bond ground pads first (thermal/electrical stability)
2. Bond power (VDD) pads
3. Bond photodetector outputs
4. Bond heater controls
5. Bond carry chain I/O

### 9.3 Fiber Attachment Process

1. **Fiber preparation:** Cleave fiber array to optical quality
2. **Coarse alignment:** Position fiber ~50 µm from chip facet
3. **Active alignment:** Inject test laser, monitor output power
4. **Fine alignment:** Optimize X, Y, Z, pitch, yaw for maximum coupling
5. **UV cure:** Fix fiber position with UV-curable adhesive
6. **Strain relief:** Apply additional adhesive for mechanical stability

### 9.4 Test Points

| Test | Equipment | Pass Criteria |
|------|-----------|---------------|
| Waveguide transmission | 1.55 µm laser + power meter | Loss < 3 dB/cm |
| Fiber coupling | Tunable laser + OSA | Coupling loss < 3 dB |
| Photodetector response | Calibrated source + SMU | Responsivity > 0.5 A/W |
| Heater function | DC source + thermal camera | Linear response |
| SFG mixing | Dual-λ source + spectrometer | Correct output λ |

---

## 10. Files Reference

| File | Description |
|------|-------------|
| `Research/data/gds/ternary_81trit_simplified.gds` | Primary 81-trit chip layout |
| `Research/data/gds/masks/METAL2_PAD.gds` | Bond pad mask layer |
| `Research/data/gds/masks/WAVEGUIDE.gds` | Waveguide pattern mask |
| `docs/CHIP_INTERFACE.md` | Complete interface specification |
| `Phase3_Chip_Simulation/DESIGN_SUMMARY.md` | Chip design documentation |

---

## 11. Contact

**Designer:** Christopher Riner
**Email:** chrisriner45@gmail.com
**Repository:** https://github.com/jackwayne234/-wavelength-ternary-optical-computer
**Paper:** DOI: 10.5281/zenodo.18437600

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-05 | Initial release |

---

*This document provides specifications for packaging house and test lab personnel. For full chip design details, refer to DESIGN_SUMMARY.md and CHIP_INTERFACE.md.*
