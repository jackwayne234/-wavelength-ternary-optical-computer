# N-Radix Chip Interface Specification

**Version:** 1.1
**Date:** February 18, 2026
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
    │   Activations   ┌─────────────────┐                  │
    │   Waveguides ──►│  Systolic Array │──► Photodetectors│
    │                 │   (9×9 MVP,     │                  │
    │   Weight        │    scales to    │   Electrical     │
    │   Stream ──────►│    27×27/81×81) │   Outputs        │
    │   (from         │                 │                  │
    │   optical RAM)  │   PEs = mixer   │                  │
    │                 │   + routing     │                  │
    │   Kerr Clock    │   (no per-PE    │                  │
    │   (IOC-internal)│   weight store) │                  │
    │        ───►     └─────────────────┘                  │
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

**Status (Feb 2026):** FDTD simulation (Meep) confirmed all 18 wavelengths propagate independently through waveguides. However, circuit-level simulation revealed **cross-triplet PPLN coupling at 60nm spacing** -- adjacent triplet SFG efficiency is ~98%, meaning the PPLN crystal does not isolate triplets sufficiently at this spacing. Each triplet works perfectly in isolation.

**Conclusion: Single-triplet MVP is validated and fab-ready. Multi-triplet WDM is Phase 2** (requires per-triplet PPLN sections, separate waveguide lanes, or wider spacing).

**Source options for 6 triplets (Phase 2):**
- Frequency comb + AWG filtering
- 18-channel DFB laser array
- Supercontinuum source + filter bank

---

## Optical Output Specification

The chip has on-chip photodetectors. You read electrical signals, not optical.

### Photodetector Outputs

For the MVP triplet (1550/1310/1064 nm), the 6 SFG products are:

| Signal | SFG Wavelength | Input Combination | Meaning |
|--------|----------------|-------------------|---------|
| DET_-2 | 775.0 nm | RED+RED | Overflow: borrow |
| DET_-1 | 710.0 nm | RED+GREEN | Result: -1 |
| DET_0a | 655.0 nm | GREEN+GREEN | Result: 0 |
| DET_0b | 630.9 nm | RED+BLUE | Result: 0 |
| DET_+1 | 587.1 nm | GREEN+BLUE | Result: +1 |
| DET_+2 | 532.0 nm | BLUE+BLUE | Overflow: carry |

**Note:** Two distinct wavelengths encode "0" (655.0 and 630.9 nm). The AWG demux separates all 6 SFG outputs. Minimum spacing between adjacent outputs: 24.1 nm.

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
| Channels | 6 per PE output | DET_-2 through DET_+2 (two channels for 0) |

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

### Kerr Clock (IOC-Internal)

The chip has an internal optical clock based on Kerr self-pulsing. The clock is **IOC-internal only** -- it does not distribute to the passive accelerator PEs. Photon arrival synchronization at PEs is achieved through matched waveguide path lengths (timing is geometry, not clock distribution).

| Parameter | Value |
|-----------|-------|
| Frequency | 617 MHz |
| Location | IOC region (chip edge) |
| Distribution | IOC-internal only (no H-tree to PEs) |
| PE synchronization | Matched waveguide path lengths (validated: 0.000 ps spread) |

### NR-IOC Timing Requirements

| Parameter | Requirement |
|-----------|-------------|
| Input modulation rate | Synchronize to 617 MHz (or submultiple) |
| Path length matching | Activation and weight paths equalized on-chip (0.000 ps spread validated) |
| Latency (9×9) | ~9 clock cycles for full systolic pass |
| Latency (27×27) | ~27 clock cycles for full systolic pass |
| Latency (81×81) | ~81 clock cycles for full systolic pass |

**Note:** The NR-IOC may need a clock recovery circuit to synchronize with the chip's Kerr clock, or the chip can provide a clock output signal.

---

## Array Size Independence

**The same NR-IOC design works for all chip sizes.**

| Chip | PEs | Latency | NR-IOC Changes | Status |
|------|-----|---------|----------------|--------|
| **9×9 (MVP)** | 81 | 9 clocks | Baseline | Circuit sim 8/8 PASS, fab-ready |
| 27×27 | 729 | 27 clocks | None | Architecture validated |
| 81×81 | 6,561 | 81 clocks | None | FDTD validated |

The NR-IOC interface (wavelengths, photodetector readout) is identical across all sizes. Only the computation latency and data volume differ. The 9x9 monolithic chip (1095 x 695 um on X-cut LiNbO3) is the current fabrication target.

---

## Upgrade Path

| Stage | Lasers | Triplets | Cost | Performance | Status |
|-------|--------|----------|------|-------------|--------|
| **MVP** | 3 | 1 | ~$1k | 1× baseline | Fab-ready (8/8 tests PASS) |
| **Expanded** | 6 | 2 | ~$2k | 2× parallel | Phase 2 (cross-coupling issue at 60nm spacing) |
| **Full** | 18 | 6 | ~$10-30k | 6× parallel | Phase 2 (requires per-triplet PPLN sections) |

Start with MVP. Prove the chip works. Multi-triplet parallelism requires solving the cross-triplet PPLN coupling issue (Phase 2).

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
- ❌ Per-PE weight storage (weights streamed from optical RAM)
- ❌ Software/firmware updates (logic is geometry)
- ❌ Active cooling (photons don't generate heat like electrons)
- ❌ High voltage supplies (optical, not electronic logic)

---

## Architecture Insight: Streamed Weights

**BREAKTHROUGH (Feb 2026):** Weights are NOT stored per-PE.

**Old approach:** Each Processing Element had its own bistable Kerr resonator for weight storage. Complex per-PE storage with tight tolerances.

**New approach:** Weights are stored in optical RAM (the CPU's 3-tier memory system) and STREAMED to PEs via waveguides.

**Benefits:**
1. **Simpler PEs** - Each PE is just a mixer + optical routing. No exotic per-PE storage.
2. **Higher yield** - Passive optics are easier to fabricate reliably than per-PE memory elements.
3. **Unified memory** - The CPU's optical RAM serves both CPU operations AND accelerator weight streaming.
4. **All-optical path** - Weights flow from optical RAM → waveguides → PEs → computation without O/E/O conversion.

---

## PE Types: ADD/SUB and MUL/DIV

**All PEs physically just add.** The IOC (controller) determines the meaning.

| PE Mode | What the IOC Sends | What the PE Does | What the IOC Reads Back |
|---------|--------------------|--------------------|------------------------|
| **ADD/SUB** | Straight ternary values a, b | Ternary addition (SFG) | a + b (or a - b via complement) |
| **MUL/DIV** | log(a), log(b) | Ternary addition (SFG) | log(a) + log(b) = log(a * b), IOC computes antilog |

**Key insight:** The glass never multiplies or divides. It just adds. Complexity lives in the IOC firmware, not the hardware.

- **ADD/SUB PEs** perform straight ternary addition and subtraction (subtraction via ternary complement encoding)
- **MUL/DIV PEs** perform log-domain addition, which the IOC interprets as multiplication. The IOC encodes log(a) and log(b) before sending, then takes the antilog of the result

The physical signals through the chip are identical in both modes -- the same SFG mixing happens regardless. Only the IOC's pre-encoding and post-decoding differs. This means PE mode is a software/firmware concept, not a hardware distinction.

**Validated:** Circuit simulation test 7/8 ("IOC Domain Modes") confirms physical signal identity between ADD and MUL modes.

---

## Validation Status

### Circuit-Level Simulation: 8/8 Tests PASS (Single Triplet)

Full-chip SAX-based circuit simulation of the monolithic 9x9 chip:

| Test | Description | Result |
|------|-------------|--------|
| 1. Single PE multiplication table | All 9 trit*trit combinations | PASS |
| 2. Identity matrix | 9x9 identity input | PASS |
| 3. All-ones | Uniform input stress test | PASS |
| 4. Single nonzero | Isolation / crosstalk check | PASS |
| 5. Mixed 3x3 | Realistic mixed values | PASS |
| 6. Tridiagonal Laplacian | Sparse matrix pattern | PASS |
| 7. IOC domain modes | ADD vs MUL mode equivalence | PASS |
| 8. Loss budget | Worst-case power margin | PASS (17.6 dB at PE[0,8]) |

### Monolithic 9x9 Architecture: 5/5 Checks PASS

| Check | Result | Value |
|-------|--------|-------|
| Activation path matching | PASS | 0.000 ps spread |
| Weight path equalization | PASS | 0.000 ps spread |
| Loss budget | PASS | 18.70 dB margin |
| Timing skew | PASS | 0.0000% of clock |
| Wavelength collision-free | PASS | Min spacing: 24.1 nm |

### Additional Analyses Complete

| Analysis | Result |
|----------|--------|
| Monte Carlo (10,000 trials) | 99.82% yield |
| Thermal sensitivity | 30 C passive window (15-45 C) |
| 6-triplet WDM | Cross-coupling at 60nm spacing -- single triplet fab-ready, multi-triplet Phase 2 |

---

## Files Reference

| File | Description |
|------|-------------|
| `NRadix_Accelerator/architecture/monolithic_chip_9x9.py` | 9x9 monolithic chip generator + validation |
| `NRadix_Accelerator/circuit_sim/simulate_9x9.py` | Full-chip circuit simulation (8/8 tests) |
| `NRadix_Accelerator/circuit_sim/simulate_6triplet.py` | 6-triplet WDM simulation |
| `NRadix_Accelerator/circuit_sim/demo.py` | Interactive Tkinter GUI demo |
| `NRadix_Accelerator/driver/` | Driver software (C source + Python bindings) |
| `docs/DRIVER_SPEC.md` | Full NR-IOC driver specification |
| `docs/DRIVER_CHEATSHEET.md` | Quick reference |
| `docs/MONOLITHIC_9x9_VALIDATION.md` | 9x9 architecture validation report |
| `docs/TAPEOUT_READINESS.md` | Tape-out readiness checklist (all 5 gaps resolved) |

---

## Contact

**Designer:** Christopher Riner
**Email:** chrisriner45@gmail.com
**Repository:** https://github.com/jackwayne234/-wavelength-ternary-optical-computer

---

*This is open source hardware. Build your own NR-IOC. Hit the wavelengths, read the detectors, go.*
