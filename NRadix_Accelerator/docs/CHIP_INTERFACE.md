# N-Radix Chip Interface Specification

**Version:** 1.0
**Date:** February 5, 2026
**Author:** Christopher Riner

---

## Overview

This document specifies the physical interface to the N-Radix optical chip. The chip is a passive optical device - it expects modulated light at specific wavelengths and outputs electrical signals from on-chip photodetectors.

**Key principle:** Bring your own lasers. The chip doesn't generate light - it processes it.

---

## Interface Diagram

```
                        YOUR RESPONSIBILITY
    ┌──────────────────────────────────────────────────────┐
    │                      NR-IOC                          │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
    │  │    FPGA     │  │   Laser     │  │    TIA      │  │
    │  │  Encoding/  │  │   Drivers   │  │  Amplifiers │  │
    │  │  Decoding   │  │             │  │             │  │
    │  └─────────────┘  └──────┬──────┘  └──────▲──────┘  │
    └───────────────────────────┼────────────────┼─────────┘
                                │                │
                          Fiber Array      Fiber Array
                           (input)          (output)
                                │                │
    ════════════════════════════╪════════════════╪═════════
                        CHIP BOUNDARY
    ════════════════════════════╪════════════════╪═════════
                                │                │
    ┌───────────────────────────▼────────────────┴─────────┐
    │                   N-RADIX OPTICAL CHIP               │
    │                                                       │
    │   Input         ┌─────────────────┐                  │
    │   Waveguides ──►│  Systolic Array │──► Photodetectors│
    │                 │   (27×27 or     │                  │
    │   Kerr Clock    │    81×81 PEs)   │   Electrical     │
    │   (on-chip) ───►│                 │   Outputs        │
    │                 └─────────────────┘                  │
    │                                                       │
    └──────────────────────────────────────────────────────┘
```

---

## Optical Input Specification

### Single Triplet Configuration (MVP)

For initial prototyping, use one wavelength triplet:

| Trit Value | Wavelength | Tolerance | Notes |
|------------|------------|-----------|-------|
| **-1** | 1550 nm | ±1 nm | Telecom C-band, easiest to source |
| **0** | 1310 nm | ±1 nm | Telecom O-band |
| **+1** | 1064 nm | ±1 nm | Nd:YAG, DPSS lasers common |

**Laser requirements:**
- Modulation bandwidth: >100 MHz (617 MHz ideal)
- Output power: 1-10 mW per channel
- Linewidth: <1 nm (DFB lasers recommended)

### Full 6-Triplet Configuration (Maximum Parallelism)

For 6× parallel computation through the same chip:

| Triplet | λ₋₁ (nm) | λ₀ (nm) | λ₊₁ (nm) | SFG Products (nm) |
|---------|----------|---------|----------|-------------------|
| 1 | 1040 | 1020 | 1000 | 515, 510, 505 |
| 2 | 1100 | 1080 | 1060 | 545, 540, 535 |
| 3 | 1160 | 1140 | 1120 | 575, 570, 565 |
| 4 | 1220 | 1200 | 1180 | 605, 600, 595 |
| 5 | 1280 | 1260 | 1240 | 635, 630, 625 |
| 6 | 1340 | 1320 | 1300 | 665, 660, 655 |

**Key properties:**
- 18 total wavelengths (6 triplets × 3 wavelengths)
- 60 nm spacing between triplets
- 20 nm spacing within each triplet
- All inputs: 1000-1340 nm (NIR)
- All SFG outputs: 505-665 nm (visible)
- Collision-free: no wavelength overlaps

**Validated:** FDTD simulation (Meep) confirmed all 18 wavelengths propagate independently through waveguides and a 3×3 PE array with no crosstalk (Feb 2026).

**Source options for 6 triplets:**
- Frequency comb + AWG filtering
- 18-channel DFB laser array
- Supercontinuum source + filter bank

---

## Optical Output Specification

The chip has on-chip photodetectors. You read electrical signals, not optical.

### Photodetector Outputs

| Signal | SFG Wavelength | Meaning |
|--------|----------------|---------|
| DET_-2 | ~775 nm (varies by triplet) | Overflow: borrow |
| DET_-1 | ~681 nm | Result: -1 |
| DET_0 | ~608 nm | Result: 0 |
| DET_+1 | ~549 nm | Result: +1 |
| DET_+2 | ~500 nm | Overflow: carry |

**Electrical interface:**
- Photocurrent output (requires TIA)
- Typical current: 1-100 µA
- Bandwidth: match clock frequency (617 MHz)

### Recommended TIA Specifications

| Parameter | Value | Notes |
|-----------|-------|-------|
| Bandwidth | >1 GHz | Headroom for 617 MHz clock |
| Transimpedance | 10-100 kΩ | Balance gain vs bandwidth |
| Input noise | <10 pA/√Hz | Low noise for weak signals |
| Channels | 5 per PE output | DET_-2 through DET_+2 |

---

## Fiber Coupling

### Edge Coupling (Recommended for v1)

| Parameter | Value |
|-----------|-------|
| Fiber type | SMF-28 or equivalent |
| V-groove pitch | 127 µm or 250 µm |
| Alignment tolerance | ±1 µm |
| Coupling loss | ~1-2 dB per facet |

### Grating Couplers (Alternative)

| Parameter | Value |
|-----------|-------|
| Coupling angle | 8-12° from vertical |
| Coupling loss | ~3 dB per coupler |
| Wavelength sensitivity | ±20 nm bandwidth |

---

## Timing

### Kerr Clock (On-Chip)

The chip has an internal optical clock based on Kerr self-pulsing:

| Parameter | Value |
|-----------|-------|
| Frequency | 617 MHz |
| Location | Chip center |
| Distribution | H-tree to all PEs |
| Skew | <5% of period (validated at 27×27) |

### NR-IOC Timing Requirements

| Parameter | Requirement |
|-----------|-------------|
| Input modulation rate | Synchronize to 617 MHz (or submultiple) |
| Setup time | TBD (depends on waveguide length) |
| Hold time | TBD |
| Latency (27×27) | ~27 clock cycles for full systolic pass |
| Latency (81×81) | ~81 clock cycles for full systolic pass |

**Note:** The NR-IOC may need a clock recovery circuit to synchronize with the chip's Kerr clock, or the chip can provide a clock output signal.

---

## Array Size Independence

**The same NR-IOC design works for both 27×27 and 81×81 chips.**

| Chip | PEs | Latency | NR-IOC Changes |
|------|-----|---------|----------------|
| 27×27 | 729 | 27 clocks | None |
| 81×81 | 6,561 | 81 clocks | None |

The NR-IOC interface (wavelengths, photodetector readout) is identical. Only the computation latency and data volume differ.

---

## Upgrade Path

| Stage | Lasers | Triplets | Cost | Performance |
|-------|--------|----------|------|-------------|
| **MVP** | 3 | 1 | ~$1k | 1× baseline |
| **Expanded** | 6 | 2 | ~$2k | 2× parallel |
| **Full** | 18 | 6 | ~$10-30k | 6× parallel |

Start with MVP. Prove the chip works. Add triplets for more parallelism without changing the chip.

---

## Bill of Materials (MVP Configuration)

### Lasers

| Wavelength | Suggested Part | Approx Cost |
|------------|----------------|-------------|
| 1550 nm | Thorlabs DFB1550 or similar | $300-400 |
| 1310 nm | Thorlabs DFB1310 or similar | $300-400 |
| 1064 nm | CNI MGL-III-1064 or DPSS | $200-400 |

### Electronics

| Component | Suggested Part | Approx Cost |
|-----------|----------------|-------------|
| FPGA dev board | Xilinx Zynq-7020 or similar | $150-300 |
| TIA eval board | Analog Devices or TI eval | $100-200 |
| Laser drivers | Wavelength Electronics or similar | $100-200 |

### Optical

| Component | Suggested Part | Approx Cost |
|-----------|----------------|-------------|
| Fiber V-groove array | OZ Optics or similar | $200-500 |
| Fiber patch cables | Standard FC/APC | $50-100 |
| Alignment stages (benchtop) | Thorlabs stages | $200-500 |

**Total MVP NR-IOC: ~$1,500-2,500**

---

## What the Chip Does NOT Need

The chip is passive. It does NOT require:

- ❌ On-chip light generation (you provide lasers)
- ❌ On-chip memory refresh (Kerr bistable is static)
- ❌ Software/firmware updates (logic is geometry)
- ❌ Active cooling (photons don't generate heat like electrons)
- ❌ High voltage supplies (optical, not electronic logic)

---

## Files Reference

| File | Description |
|------|-------------|
| `nradix-driver/` | Driver software and simulator |
| `docs/DRIVER_SPEC.md` | Full NR-IOC driver specification |
| `docs/DRIVER_CHEATSHEET.md` | Quick reference |
| `Research/programs/nradix_architecture/` | Architecture documentation |
| `Research/data/gds/optical_systolic_27x27.gds` | 27×27 chip layout |
| `Research/data/gds/optical_systolic_81x81.gds` | 81×81 chip layout |

---

## Contact

**Designer:** Christopher Riner
**Email:** chrisriner45@gmail.com
**Repository:** https://github.com/jackwayne234/-wavelength-ternary-optical-computer

---

*This is open source hardware. Build your own NR-IOC. Hit the wavelengths, read the detectors, go.*
