# End-to-End Functional Test Plan — Monolithic 9x9 N-Radix Chip

**Document ID:** TEST-FUNC-001
**Version:** 1.1
**Date:** 2026-02-18
**Status:** COMPLETE
**Author:** Christopher Riner / N-Radix Project
**Chip:** Monolithic 9x9 N-Radix Ternary Optical Processor
**Branch:** fab/9x9-monolithic-tape-out
**Circuit Simulation:** 8/8 tests PASS

---

## Purpose

This document provides a complete, step-by-step functional test procedure for the monolithic 9x9 N-Radix chip. It is written so that a lab technician unfamiliar with the project can independently verify chip functionality using standard photonic test equipment. All tests are ordered from simplest (single PE) to most complex (full 9x9 matrix multiply), with explicit pass/fail criteria at each stage.

---

## Table of Contents

1. [Reference Information](#1-reference-information)
2. [Equipment Required](#2-equipment-required)
3. [Calibration Procedure](#3-calibration-procedure)
4. [Test Level 1: Single PE Verification](#4-test-level-1-single-pe-verification)
5. [Test Level 2: Single Row Dot Product](#5-test-level-2-single-row-dot-product)
6. [Test Level 3: Full 9x9 Matrix Multiply](#6-test-level-3-full-9x9-matrix-multiply)
7. [Failure Diagnosis Flowchart](#7-failure-diagnosis-flowchart)
8. [Data Recording Templates](#8-data-recording-templates)
9. [Sign-Off Checklist](#9-sign-off-checklist)

---

## 1. Reference Information

### 1.1 Chip Specifications

| Parameter | Value |
|-----------|-------|
| Die size | 1095 x 695 um |
| Array | 9x9 = 81 Processing Elements |
| Material | X-cut LiNbO3 (TFLN), n = 2.2 |
| Topology | Split-edge (IOC input left, PE array center, IOC output right) |
| Clock | 617 MHz Kerr self-pulsing (IOC-internal only) |
| PE pitch | 55 um center-to-center |
| Waveguide width | 0.5 um (single-mode at all wavelengths) |
| Power margin | 18.70 dB (validated) |
| Total optical path loss | 21.30 dB |
| Laser power per channel | +10 dBm |
| Detector sensitivity | -30 dBm |

### 1.2 PE Types

The architecture has two logical PE types. Both physically perform the same operation (ternary addition via SFG). The IOC determines the semantic meaning of each PE's output:

| PE Type | Physical Operation | Logical Meaning | Notes |
|---------|-------------------|-----------------|-------|
| **ADD/SUB** | Ternary SFG addition | Straight ternary add/subtract | Direct balanced-ternary arithmetic |
| **MUL/DIV** | Ternary SFG addition | Log-domain addition = multiplication | Inputs pre-encoded in log domain by IOC; addition in log domain is multiplication in linear domain |

All PEs are physically identical. The IOC is responsible for encoding inputs in the appropriate domain (linear for ADD/SUB, logarithmic for MUL/DIV) and decoding outputs accordingly.

### 1.3 Ternary Wavelength Encoding

| Trit Value | Wavelength | Band | Tolerance |
|------------|------------|------|-----------|
| **-1** (RED) | 1550 nm | C-band | +/- 1 nm |
| **0** (GREEN) | 1310 nm | O-band | +/- 1 nm |
| **+1** (BLUE) | 1064 nm | Near-IR | +/- 1 nm |

### 1.4 SFG Output Products

Sum-Frequency Generation produces the following wavelengths from input pairs. The output wavelength is computed as: 1/lambda_out = 1/lambda_a + 1/lambda_b.

| Input A | Input B | SFG Combination | Output Wavelength (nm) | Ternary Product (A x B) |
|---------|---------|-----------------|------------------------|-------------------------|
| +1 (1064) | +1 (1064) | BLUE+BLUE | 532.0 | +1 |
| 0 (1310) | +1 (1064) | GREEN+BLUE | 587.1 | 0 |
| -1 (1550) | +1 (1064) | RED+BLUE | 630.9 | -1 |
| 0 (1310) | 0 (1310) | GREEN+GREEN | 655.0 | 0 |
| -1 (1550) | 0 (1310) | RED+GREEN | 710.0 | 0 |
| -1 (1550) | -1 (1550) | RED+RED | 775.0 | +1 |

Minimum output spacing: 24.1 nm (collision-free for AWG demux with >20 nm channel separation).

### 1.5 Detector Mapping

Each PE output column terminates at an AWG demux feeding 5 photodetectors. The detector-to-result mapping is:

| Detector | SFG Wavelength Range | Ternary Result | Meaning |
|----------|---------------------|----------------|---------|
| DET_+2 | ~532 nm (BLUE+BLUE) | +2 (carry) | Overflow carry |
| DET_+1 | ~587 nm (GREEN+BLUE) | +1 | Result: positive one |
| DET_0 | ~631-710 nm (multiple) | 0 | Result: zero |
| DET_-1 | ~631 nm (RED+BLUE) | -1 | Result: negative one |
| DET_-2 | ~775 nm (RED+RED) | -2 (borrow) | Overflow borrow |

**Detector interpretation rules:**
- Only ONE detector should fire per PE per clock cycle in single-PE mode.
- In accumulation (row/array) mode, multiple partial sum products may arrive, and the decoder sums them.
- Detectors DET_+2 and DET_-2 indicate carry/borrow, which propagates to the next trit position.

### 1.6 Electrical Output Specifications

| Parameter | Value |
|-----------|-------|
| Detector type | Ge-on-Si or InGaAs (broadband 500-775 nm) |
| Responsivity | 0.5-1.0 A/W |
| Dark current | < 10 nA at -2V bias |
| Photocurrent range | 1-100 uA (typical) |
| Detector bias | -1 to -3 V (reverse bias) |
| TIA transimpedance | 10-100 kOhm |
| TIA bandwidth | > 1 GHz |

---

## 2. Equipment Required

### 2.1 Optical Sources

| Item | Specification | Purpose | Approx. Cost |
|------|---------------|---------|--------------|
| 1550 nm DFB laser | > 10 mW, linewidth < 1 nm, FC/APC | Trit = -1 (RED) | $300-400 |
| 1310 nm DFB laser | > 10 mW, linewidth < 1 nm, FC/APC | Trit = 0 (GREEN) | $300-400 |
| 1064 nm DPSS laser | > 10 mW, linewidth < 1 nm, FC/APC | Trit = +1 (BLUE) | $200-400 |
| Variable optical attenuator (VOA) | 0-30 dB, 1000-1600 nm | Power calibration | $200-500 |
| Optical power meter | -60 to +10 dBm, 400-1700 nm | Power measurement | $300-600 |

### 2.2 Fiber and Coupling

| Item | Specification | Purpose |
|------|---------------|---------|
| SMF-28 fiber patch cables (x6) | FC/APC, 1 meter | Input/output coupling |
| Fiber V-groove array | 127 or 250 um pitch, 2-6 channels | Edge coupling to chip |
| 3-axis alignment stage | 0.1 um resolution, piezo fine adjust | Fiber-to-chip alignment |
| Microscope | 10x-50x, long working distance | Alignment visualization |
| UV-cure adhesive + UV lamp | Norland NOA 61 or equivalent | Fiber bonding (if permanent) |

### 2.3 Electrical Readout

| Item | Specification | Purpose |
|------|---------------|---------|
| TIA board | 5-channel, > 1 GHz BW, 10-100 kOhm | Photocurrent amplification |
| Oscilloscope | >= 1 GHz, >= 4 channels | Waveform capture |
| Source measure unit (SMU) | 4-channel, uA resolution | Detector bias + DC readout |
| DC power supply | 0-5 V, 1 A | Heater power |
| FPGA development board | Xilinx Zynq-7020 or equivalent | Encoding/decoding/timing |
| Multimeter | 6.5-digit, uA range | Precision current measurement |

### 2.4 Environmental

| Item | Specification | Purpose |
|------|---------------|---------|
| TEC controller | +/- 0.1 deg C stability | Chip temperature control |
| Thermistor/RTD | Package-mounted | Temperature monitoring |
| Optical table | Vibration-isolated, M6 threaded | Stability |

---

## 3. Calibration Procedure

Perform all calibration steps before any functional testing. Record all values in the Data Recording Template (Section 8.1).

### 3.1 Step 1: Baseline Detector Dark Readings (No Input Light)

**Purpose:** Establish noise floor for all 5 detector channels per output column.

**Procedure:**

1. Power off all lasers. Verify no ambient light reaches chip (cover fiber inputs or work in darkened enclosure).
2. Apply detector bias voltage of -2.0 V to all photodetectors.
3. Wait 5 minutes for thermal equilibrium.
4. Using the SMU, measure DC photocurrent on each of the 5 detectors (DET_-2 through DET_+2) on at least 3 output columns (columns 0, 4, and 8 recommended).
5. Record 10 consecutive readings per detector at 1-second intervals.
6. Compute mean and standard deviation for each detector.

**Pass criteria:**
- Mean dark current: < 10 nA per detector
- Standard deviation: < 1 nA
- No detector reads > 20 nA

**If FAIL:** Check detector bias connections. Verify no stray light. Inspect wire bonds to detector pads.

### 3.2 Step 2: Single-Wavelength Reference Measurements

**Purpose:** Verify that each input laser couples into the chip and produces measurable output.

**Procedure (repeat for each of the 3 wavelengths):**

1. Set laser to nominal power: +10 dBm (10 mW).
2. Measure laser output power with power meter at fiber tip. Record actual power.
3. Connect fiber to chip input port (row 0, activation input).
4. Inject ONLY the 1550 nm laser (all others OFF).
5. Monitor all 5 detectors on output column 0.
6. Record photocurrent on each detector.
7. Repeat with ONLY the 1310 nm laser.
8. Repeat with ONLY the 1064 nm laser.

**Expected results (single wavelength, no SFG partner):**

When only one wavelength is injected, there is no SFG mixing partner. You should see:
- Residual scatter/leakage at the input wavelength, but NO SFG product.
- All 5 detector currents should be near dark current levels (< 50 nA).
- If any detector reads > 1 uA with a single input wavelength, there may be self-SHG (second harmonic generation) or stray light coupling.

**Pass criteria:**
- All detectors read < 50 nA above dark current baseline with single-wavelength input.
- This confirms the AWG demux is not routing stray input-band light to the SFG-band detectors.

### 3.3 Step 3: Fiber Coupling Verification

**Purpose:** Confirm adequate optical power reaches the PE array through the edge coupler.

**Procedure:**

1. Inject 1550 nm laser at +10 dBm into the chip input port for row 0.
2. If a through-waveguide test port exists (consult chip layout), measure transmitted power at the output facet using the power meter.
3. If no through port exists, perform this step using the SFG test in Level 1 (Section 4) as a proxy: successful SFG confirms adequate coupling.

**Expected coupling loss:** 1-2 dB per facet (total round-trip: 2-4 dB).

**Alternative method (active alignment):**
1. Set laser to +10 dBm.
2. While monitoring the power meter at the output, slowly adjust the 3-axis stage (X, Y, Z).
3. Maximize output power. Lock stage position.
4. Record maximum coupled power. Compute coupling loss = (input power dBm) - (output power dBm).

**Pass criteria:**
- Coupling loss per facet: < 3 dB
- If coupling loss > 5 dB: re-cleave fiber, clean facets, re-align.

### 3.4 Step 4: Power Level Calibration

**Purpose:** Set each laser to the correct input power, accounting for coupling loss, so that the SFG products produce detector currents within the measurable range.

**Procedure:**

1. Based on measured coupling loss from Step 3, calculate the required laser launch power:
   - Target power at PE input: -5 dBm to 0 dBm (100 uW to 1 mW in the waveguide)
   - Required launch power = Target + Coupling loss
   - Example: if coupling loss = 2 dB, launch at +2 dBm for 0 dBm at PE
2. Use the VOA to set each laser to the calculated launch power.
3. Verify with power meter.
4. Record calibrated power levels for all 3 lasers.

**Pass criteria:**
- Each laser is within +/- 0.5 dB of its target launch power.
- All 3 lasers are within 1 dB of each other (power-balanced).

### 3.5 Step 5: Thermal Stabilization

**Purpose:** Ensure the chip is at a stable operating temperature before functional tests.

**Procedure:**

1. Set TEC controller to 25.0 deg C.
2. Monitor thermistor reading.
3. Wait until temperature is stable within +/- 0.1 deg C for at least 5 minutes.
4. Record stabilized temperature.

**Pass criteria:**
- Temperature: 25.0 +/- 0.1 deg C
- Temperature drift over 5 minutes: < 0.05 deg C

---

## 4. Test Level 1: Single PE Verification

### 4.1 Overview

Test a single Processing Element by injecting two wavelengths (one activation, one weight) and verifying the correct SFG product appears at the expected detector.

**Target PE:** PE[0,0] (top-left corner, row 0, column 0). This is the first PE reached by the activation input on row 0 and the weight input on column 0.

### 4.2 Test Setup

1. Connect the 1550 nm, 1310 nm, and 1064 nm lasers to the FPGA-controlled laser driver board.
2. Configure the FPGA to drive row 0 activation input and column 0 weight input.
3. Connect TIA board to the 5 detectors on output column 0.
4. Connect TIA outputs to oscilloscope (or ADC for automated readout).

### 4.3 All 9 Ternary Multiplication Test Cases

For each test case below:
1. Set the activation laser to the specified wavelength for operand A.
2. Set the weight laser to the specified wavelength for operand B.
3. Turn ON both lasers simultaneously at calibrated power.
4. Wait 100 ns (62 clock cycles at 617 MHz) for signal to stabilize.
5. Read all 5 detector currents.
6. Verify that ONLY the expected detector fires above threshold.

**Detection threshold:** A detector is considered "firing" if its photocurrent exceeds 3x the dark current baseline + 100 nA. All other detectors must remain below this threshold.

---

#### Test 1.1: (+1) x (+1) = +1

| Parameter | Value |
|-----------|-------|
| Operand A (activation) | +1 |
| Operand B (weight) | +1 |
| Input wavelength A | 1064 nm (BLUE) |
| Input wavelength B | 1064 nm (BLUE) |
| SFG combination | BLUE + BLUE |
| Expected output wavelength | 532.0 nm |
| Expected detector | **DET_+2** (carry) |
| Expected ternary product | +1 (but encoded as DET_+2 at single-PE level, since B+B = +1x+1 = +1 mapped to 532 nm) |

**Note on detector mapping for single PE:** At the single-PE level, the ternary product of the SFG interaction is identified by which output wavelength is produced. The mapping from SFG wavelength to ternary result is:

| SFG Wavelength | Physical Meaning | Ternary Product |
|----------------|------------------|-----------------|
| 532.0 nm | BLUE+BLUE | (+1)(+1) = +1 |
| 587.1 nm | GREEN+BLUE | (0)(+1) = 0 |
| 630.9 nm | RED+BLUE | (-1)(+1) = -1 |
| 655.0 nm | GREEN+GREEN | (0)(0) = 0 |
| 710.0 nm | RED+GREEN | (-1)(0) = 0 |
| 775.0 nm | RED+RED | (-1)(-1) = +1 |

The AWG demux routes each SFG wavelength to a specific detector. The detector that fires tells you the result.

**Expected detector currents (approximate):**

| Detector | Expected Current | Status |
|----------|-----------------|--------|
| DET_-2 (775 nm) | < threshold (dark) | No signal |
| DET_-1 (631 nm) | < threshold (dark) | No signal |
| DET_0 (655/710 nm) | < threshold (dark) | No signal |
| DET_+1 (587 nm) | < threshold (dark) | No signal |
| DET_+2 (532 nm) | **1-50 uA** | **SIGNAL** |

**Pass:** DET_+2 fires, all others below threshold.
**Fail:** Wrong detector fires, or no detector fires, or multiple detectors fire.

---

#### Test 1.2: (+1) x (0) = 0

| Parameter | Value |
|-----------|-------|
| Operand A (activation) | +1 |
| Operand B (weight) | 0 |
| Input wavelength A | 1064 nm (BLUE) |
| Input wavelength B | 1310 nm (GREEN) |
| SFG combination | GREEN + BLUE |
| Expected output wavelength | 587.1 nm |
| Expected detector | **DET_+1** |

| Detector | Expected Current | Status |
|----------|-----------------|--------|
| DET_-2 (775 nm) | < threshold | No signal |
| DET_-1 (631 nm) | < threshold | No signal |
| DET_0 (655/710 nm) | < threshold | No signal |
| DET_+1 (587 nm) | **1-50 uA** | **SIGNAL** |
| DET_+2 (532 nm) | < threshold | No signal |

**Pass:** DET_+1 fires only.

---

#### Test 1.3: (+1) x (-1) = -1

| Parameter | Value |
|-----------|-------|
| Operand A (activation) | +1 |
| Operand B (weight) | -1 |
| Input wavelength A | 1064 nm (BLUE) |
| Input wavelength B | 1550 nm (RED) |
| SFG combination | RED + BLUE |
| Expected output wavelength | 630.9 nm |
| Expected detector | **DET_-1** |

| Detector | Expected Current | Status |
|----------|-----------------|--------|
| DET_-2 (775 nm) | < threshold | No signal |
| DET_-1 (631 nm) | **1-50 uA** | **SIGNAL** |
| DET_0 (655/710 nm) | < threshold | No signal |
| DET_+1 (587 nm) | < threshold | No signal |
| DET_+2 (532 nm) | < threshold | No signal |

**Pass:** DET_-1 fires only.

---

#### Test 1.4: (0) x (+1) = 0

| Parameter | Value |
|-----------|-------|
| Operand A (activation) | 0 |
| Operand B (weight) | +1 |
| Input wavelength A | 1310 nm (GREEN) |
| Input wavelength B | 1064 nm (BLUE) |
| SFG combination | GREEN + BLUE |
| Expected output wavelength | 587.1 nm |
| Expected detector | **DET_+1** |

| Detector | Expected Current | Status |
|----------|-----------------|--------|
| DET_-2 (775 nm) | < threshold | No signal |
| DET_-1 (631 nm) | < threshold | No signal |
| DET_0 (655/710 nm) | < threshold | No signal |
| DET_+1 (587 nm) | **1-50 uA** | **SIGNAL** |
| DET_+2 (532 nm) | < threshold | No signal |

**Pass:** DET_+1 fires only. (Note: same SFG product as Test 1.2 — SFG is commutative.)

---

#### Test 1.5: (0) x (0) = 0

| Parameter | Value |
|-----------|-------|
| Operand A (activation) | 0 |
| Operand B (weight) | 0 |
| Input wavelength A | 1310 nm (GREEN) |
| Input wavelength B | 1310 nm (GREEN) |
| SFG combination | GREEN + GREEN |
| Expected output wavelength | 655.0 nm |
| Expected detector | **DET_0** |

| Detector | Expected Current | Status |
|----------|-----------------|--------|
| DET_-2 (775 nm) | < threshold | No signal |
| DET_-1 (631 nm) | < threshold | No signal |
| DET_0 (655 nm) | **1-50 uA** | **SIGNAL** |
| DET_+1 (587 nm) | < threshold | No signal |
| DET_+2 (532 nm) | < threshold | No signal |

**Pass:** DET_0 fires only.

---

#### Test 1.6: (0) x (-1) = 0

| Parameter | Value |
|-----------|-------|
| Operand A (activation) | 0 |
| Operand B (weight) | -1 |
| Input wavelength A | 1310 nm (GREEN) |
| Input wavelength B | 1550 nm (RED) |
| SFG combination | RED + GREEN |
| Expected output wavelength | 710.0 nm |
| Expected detector | **DET_0** |

| Detector | Expected Current | Status |
|----------|-----------------|--------|
| DET_-2 (775 nm) | < threshold | No signal |
| DET_-1 (631 nm) | < threshold | No signal |
| DET_0 (710 nm) | **1-50 uA** | **SIGNAL** |
| DET_+1 (587 nm) | < threshold | No signal |
| DET_+2 (532 nm) | < threshold | No signal |

**Pass:** DET_0 fires only. (Note: DET_0 receives both 655 nm and 710 nm — both map to result 0.)

---

#### Test 1.7: (-1) x (+1) = -1

| Parameter | Value |
|-----------|-------|
| Operand A (activation) | -1 |
| Operand B (weight) | +1 |
| Input wavelength A | 1550 nm (RED) |
| Input wavelength B | 1064 nm (BLUE) |
| SFG combination | RED + BLUE |
| Expected output wavelength | 630.9 nm |
| Expected detector | **DET_-1** |

| Detector | Expected Current | Status |
|----------|-----------------|--------|
| DET_-2 (775 nm) | < threshold | No signal |
| DET_-1 (631 nm) | **1-50 uA** | **SIGNAL** |
| DET_0 (655/710 nm) | < threshold | No signal |
| DET_+1 (587 nm) | < threshold | No signal |
| DET_+2 (532 nm) | < threshold | No signal |

**Pass:** DET_-1 fires only. (Same SFG product as Test 1.3.)

---

#### Test 1.8: (-1) x (0) = 0

| Parameter | Value |
|-----------|-------|
| Operand A (activation) | -1 |
| Operand B (weight) | 0 |
| Input wavelength A | 1550 nm (RED) |
| Input wavelength B | 1310 nm (GREEN) |
| SFG combination | RED + GREEN |
| Expected output wavelength | 710.0 nm |
| Expected detector | **DET_0** |

| Detector | Expected Current | Status |
|----------|-----------------|--------|
| DET_-2 (775 nm) | < threshold | No signal |
| DET_-1 (631 nm) | < threshold | No signal |
| DET_0 (710 nm) | **1-50 uA** | **SIGNAL** |
| DET_+1 (587 nm) | < threshold | No signal |
| DET_+2 (532 nm) | < threshold | No signal |

**Pass:** DET_0 fires only.

---

#### Test 1.9: (-1) x (-1) = +1

| Parameter | Value |
|-----------|-------|
| Operand A (activation) | -1 |
| Operand B (weight) | -1 |
| Input wavelength A | 1550 nm (RED) |
| Input wavelength B | 1550 nm (RED) |
| SFG combination | RED + RED |
| Expected output wavelength | 775.0 nm |
| Expected detector | **DET_-2** (borrow) |

| Detector | Expected Current | Status |
|----------|-----------------|--------|
| DET_-2 (775 nm) | **1-50 uA** | **SIGNAL** |
| DET_-1 (631 nm) | < threshold | No signal |
| DET_0 (655/710 nm) | < threshold | No signal |
| DET_+1 (587 nm) | < threshold | No signal |
| DET_+2 (532 nm) | < threshold | No signal |

**Pass:** DET_-2 fires only.

---

### 4.4 Single PE Summary Table

| Test | A | B | A x B | Input Wavelengths | SFG Output (nm) | Active Detector |
|------|---|---|-------|-------------------|------------------|-----------------|
| 1.1 | +1 | +1 | +1 | 1064 + 1064 | 532.0 | DET_+2 |
| 1.2 | +1 | 0 | 0 | 1064 + 1310 | 587.1 | DET_+1 |
| 1.3 | +1 | -1 | -1 | 1064 + 1550 | 630.9 | DET_-1 |
| 1.4 | 0 | +1 | 0 | 1310 + 1064 | 587.1 | DET_+1 |
| 1.5 | 0 | 0 | 0 | 1310 + 1310 | 655.0 | DET_0 |
| 1.6 | 0 | -1 | 0 | 1310 + 1550 | 710.0 | DET_0 |
| 1.7 | -1 | +1 | -1 | 1550 + 1064 | 630.9 | DET_-1 |
| 1.8 | -1 | 0 | 0 | 1550 + 1310 | 710.0 | DET_0 |
| 1.9 | -1 | -1 | +1 | 1550 + 1550 | 775.0 | DET_-2 |

**Level 1 Pass Criteria:** All 9 tests pass. Each test must show the correct single detector firing with all others below threshold.

**Minimum passing:** At least 8 of 9 tests pass. If exactly 1 test fails, proceed to failure diagnosis (Section 7) before continuing.

---

## 5. Test Level 2: Single Row Dot Product

### 5.1 Overview

A single row of 9 PEs computes a dot product: the element-wise multiplication of a 9-element activation vector **a** with a 9-element weight vector **w**, followed by accumulation along the column:

result_col_j = a[j] x w[j]   (at each PE, before accumulation)

The partial sums flow vertically (top to bottom) through the systolic array. For a single-row test, we read the 9 output columns directly, each showing the product of one activation-weight pair. The accumulation is tested by examining the same column across multiple rows (covered in Level 3).

**For Level 2, we verify that all 9 PEs in a row produce the correct individual products simultaneously.**

### 5.2 Test Setup

1. Configure the FPGA to encode a 9-element activation vector on row 0 input.
   - Each element is time-multiplexed onto the same fiber at the 617 MHz clock rate, OR
   - All 9 elements are injected simultaneously if the IOC encoder supports parallel activation (one wavelength per PE column via the weight bus).
2. Configure the FPGA to load a 9-element weight vector onto the weight streaming bus.
3. Connect TIA boards to all 9 output columns (5 detectors each, 45 total channels).

### 5.3 Test Case 2.1: All-Ones Dot Product

**Purpose:** Verify that all 9 PEs produce the same result when given identical inputs.

**Activation vector a:** [+1, +1, +1, +1, +1, +1, +1, +1, +1]
**Weight vector w:**      [+1, +1, +1, +1, +1, +1, +1, +1, +1]

**Input wavelengths per PE:**
- Activation: 1064 nm on all 9 row inputs
- Weight: 1064 nm on all 9 column weight drops

**Expected per-PE SFG:** BLUE+BLUE = 532.0 nm at every PE.

**Expected detector output per column:**

| Column | PE Product | Active Detector | Expected Current |
|--------|-----------|-----------------|-----------------|
| 0 | (+1)(+1) = +1 | DET_+2 (532 nm) | 1-50 uA |
| 1 | (+1)(+1) = +1 | DET_+2 (532 nm) | 1-50 uA |
| 2 | (+1)(+1) = +1 | DET_+2 (532 nm) | 1-50 uA |
| 3 | (+1)(+1) = +1 | DET_+2 (532 nm) | 1-50 uA |
| 4 | (+1)(+1) = +1 | DET_+2 (532 nm) | 1-50 uA |
| 5 | (+1)(+1) = +1 | DET_+2 (532 nm) | 1-50 uA |
| 6 | (+1)(+1) = +1 | DET_+2 (532 nm) | 1-50 uA |
| 7 | (+1)(+1) = +1 | DET_+2 (532 nm) | 1-50 uA |
| 8 | (+1)(+1) = +1 | DET_+2 (532 nm) | 1-50 uA |

**Hand-calculated dot product:** sum = 9 x (+1) = +9. In balanced ternary: +9 = +1 x 3^2 + 0 x 3^1 + 0 x 3^0 = (+1, 0, 0)_3.
Note: The per-column detector reading shows the individual PE product. The full accumulation for the dot product requires reading the column bottom detector (after all 9 partial sums flow through) — this tests the systolic accumulation and is covered in Level 3.

**Pass criteria:**
- All 9 columns show DET_+2 firing.
- No other detectors above threshold on any column.
- DET_+2 currents across all 9 columns are within 2x of each other (uniformity check).

---

### 5.4 Test Case 2.2: Mixed Vector Dot Product

**Purpose:** Verify correct per-element multiplication with different trit values.

**Activation vector a:** [+1, -1,  0, +1, -1,  0, +1, -1,  0]
**Weight vector w:**      [+1, +1, +1, -1, -1, -1,  0,  0,  0]

**Expected per-PE products:**

| Col | a[j] | w[j] | Product | Input A (nm) | Input B (nm) | SFG (nm) | Detector |
|-----|------|------|---------|-------------|-------------|----------|----------|
| 0 | +1 | +1 | +1 | 1064 | 1064 | 532.0 | DET_+2 |
| 1 | -1 | +1 | -1 | 1550 | 1064 | 630.9 | DET_-1 |
| 2 | 0 | +1 | 0 | 1310 | 1064 | 587.1 | DET_+1 |
| 3 | +1 | -1 | -1 | 1064 | 1550 | 630.9 | DET_-1 |
| 4 | -1 | -1 | +1 | 1550 | 1550 | 775.0 | DET_-2 |
| 5 | 0 | -1 | 0 | 1310 | 1550 | 710.0 | DET_0 |
| 6 | +1 | 0 | 0 | 1064 | 1310 | 587.1 | DET_+1 |
| 7 | -1 | 0 | 0 | 1550 | 1310 | 710.0 | DET_0 |
| 8 | 0 | 0 | 0 | 1310 | 1310 | 655.0 | DET_0 |

**Hand-calculated dot product:** (+1) + (-1) + (0) + (-1) + (+1) + (0) + (0) + (0) + (0) = **0**

**Pass criteria:**
- Each column shows ONLY the expected detector firing (per table above).
- No spurious detectors active.
- This test exercises all 6 unique SFG wavelengths simultaneously across the row.

---

### 5.5 Test Case 2.3: Alternating Sign Vector

**Purpose:** Stress test with rapid sign alternation.

**Activation vector a:** [+1, -1, +1, -1, +1, -1, +1, -1, +1]
**Weight vector w:**      [-1, +1, -1, +1, -1, +1, -1, +1, -1]

**Expected per-PE products:**

| Col | a[j] | w[j] | Product | Input A (nm) | Input B (nm) | SFG (nm) | Detector |
|-----|------|------|---------|-------------|-------------|----------|----------|
| 0 | +1 | -1 | -1 | 1064 | 1550 | 630.9 | DET_-1 |
| 1 | -1 | +1 | -1 | 1550 | 1064 | 630.9 | DET_-1 |
| 2 | +1 | -1 | -1 | 1064 | 1550 | 630.9 | DET_-1 |
| 3 | -1 | +1 | -1 | 1550 | 1064 | 630.9 | DET_-1 |
| 4 | +1 | -1 | -1 | 1064 | 1550 | 630.9 | DET_-1 |
| 5 | -1 | +1 | -1 | 1550 | 1064 | 630.9 | DET_-1 |
| 6 | +1 | -1 | -1 | 1064 | 1550 | 630.9 | DET_-1 |
| 7 | -1 | +1 | -1 | 1550 | 1064 | 630.9 | DET_-1 |
| 8 | +1 | -1 | -1 | 1064 | 1550 | 630.9 | DET_-1 |

**Hand-calculated dot product:** 9 x (-1) = **-9**. In balanced ternary: -9 = (-1, 0, 0)_3.

**Pass criteria:**
- All 9 columns show DET_-1 firing.
- This is a strong uniformity test: all PEs should produce the same SFG wavelength (630.9 nm) with consistent detector current levels.
- Column-to-column current variation: < 3x between strongest and weakest.

---

### 5.6 Level 2 Pass Criteria Summary

| Test Case | Description | Pass Condition |
|-----------|-------------|----------------|
| 2.1 | All-ones | 9/9 columns correct |
| 2.2 | Mixed vector | 9/9 columns correct, all 6 SFG wavelengths present |
| 2.3 | Alternating sign | 9/9 columns correct, uniformity < 3x variation |

**Minimum passing:** All 3 test cases pass. If any single column consistently fails across all 3 tests, that column's PE or decoder may be defective — note the column number and proceed to failure diagnosis (Section 7).

---

## 6. Test Level 3: Full 9x9 Matrix Multiply

### 6.1 Overview

The 9x9 systolic array computes a matrix-vector multiplication:

**C = A x B**

Where:
- **A** is a 9x9 ternary weight matrix (stored in optical RAM, streamed via weight bus)
- **B** is a 9-element ternary activation vector (injected via left-edge encoders)
- **C** is the 9-element ternary result vector (read from bottom-edge decoders)

In the systolic array:
- Activation vector **B** is injected simultaneously across all 9 rows.
- Weight matrix **A** is streamed column by column, one column per clock cycle.
- Partial sums accumulate vertically (top to bottom) through each column.
- After 9 clock cycles, the complete result vector **C** appears at the column outputs.

### 6.2 Timing

| Parameter | Value |
|-----------|-------|
| Clock frequency | 617 MHz |
| Clock period | 1.621 ns |
| Systolic latency | 9 clock cycles (for 9x9 array) |
| Total computation time | 9 x 1.621 ns = **14.59 ns** |
| Output read window | Clock cycles 10-18 (results available at column bottoms) |
| Pipeline fill time | 9 clock cycles |
| Steady-state throughput | 1 result vector per clock cycle (after pipeline fill) |

**Procedure:**
1. Load weight matrix **A** into optical RAM.
2. On clock cycle 0: inject activation vector **B** on all 9 row inputs. Begin streaming weight column 0.
3. On clock cycle 1: stream weight column 1 (partial sums from cycle 0 flow down one row).
4. Continue through clock cycle 8: stream weight column 8.
5. On clock cycle 9: first complete result appears at column 0 output.
6. On clock cycles 10-17: remaining results appear at columns 1-8.
7. Read all 9 column outputs using the 5-detector decoders.

### 6.3 Test Case 3.1: Identity Matrix Test

**Purpose:** Multiply by the ternary identity matrix. Output should equal the input activation vector.

**Weight matrix A (identity):**

```
A = [+1,  0,  0,  0,  0,  0,  0,  0,  0]
    [ 0, +1,  0,  0,  0,  0,  0,  0,  0]
    [ 0,  0, +1,  0,  0,  0,  0,  0,  0]
    [ 0,  0,  0, +1,  0,  0,  0,  0,  0]
    [ 0,  0,  0,  0, +1,  0,  0,  0,  0]
    [ 0,  0,  0,  0,  0, +1,  0,  0,  0]
    [ 0,  0,  0,  0,  0,  0, +1,  0,  0]
    [ 0,  0,  0,  0,  0,  0,  0, +1,  0]
    [ 0,  0,  0,  0,  0,  0,  0,  0, +1]
```

**Activation vector B:**

```
B = [+1, -1, 0, +1, 0, -1, +1, -1, 0]
```

**Expected output C = A x B:**

```
C = [+1, -1, 0, +1, 0, -1, +1, -1, 0]
```

**Detailed expected per-column results:**

For the identity matrix, each column j has weight +1 at row j and 0 everywhere else. The dot product for column j is simply B[j].

| Output Column | Dot Product | Expected Ternary Result | Dominant Detector |
|---------------|-------------|-------------------------|-------------------|
| 0 | (+1)(+1) + 0+0+0+0+0+0+0+0 = +1 | +1 | DET_+2 (532 nm) |
| 1 | 0+(+1)(-1)+0+0+0+0+0+0+0 = -1 | -1 | DET_-1 (631 nm) |
| 2 | 0+0+(+1)(0)+0+0+0+0+0+0 = 0 | 0 | DET_0 (655/710 nm) |
| 3 | 0+0+0+(+1)(+1)+0+0+0+0+0 = +1 | +1 | DET_+2 (532 nm) |
| 4 | 0+0+0+0+(+1)(0)+0+0+0+0 = 0 | 0 | DET_0 (655/710 nm) |
| 5 | 0+0+0+0+0+(+1)(-1)+0+0+0 = -1 | -1 | DET_-1 (631 nm) |
| 6 | 0+0+0+0+0+0+(+1)(+1)+0+0 = +1 | +1 | DET_+2 (532 nm) |
| 7 | 0+0+0+0+0+0+0+(+1)(-1)+0 = -1 | -1 | DET_-1 (631 nm) |
| 8 | 0+0+0+0+0+0+0+0+(+1)(0) = 0 | 0 | DET_0 (655/710 nm) |

**Pass criteria:**
- Output vector C matches input vector B exactly: [+1, -1, 0, +1, 0, -1, +1, -1, 0].
- Each column output decoder reports the correct ternary trit.
- Results appear at the correct clock cycles (beginning at cycle 9).

---

### 6.4 Test Case 3.2: Known Computation Test

**Purpose:** Verify a non-trivial matrix multiplication with a hand-calculated expected result.

**Weight matrix A:**

```
A = [+1, -1,  0,  0,  0,  0,  0,  0,  0]
    [-1, +1, -1,  0,  0,  0,  0,  0,  0]
    [ 0, -1, +1, -1,  0,  0,  0,  0,  0]
    [ 0,  0, -1, +1, -1,  0,  0,  0,  0]
    [ 0,  0,  0, -1, +1, -1,  0,  0,  0]
    [ 0,  0,  0,  0, -1, +1, -1,  0,  0]
    [ 0,  0,  0,  0,  0, -1, +1, -1,  0]
    [ 0,  0,  0,  0,  0,  0, -1, +1, -1]
    [ 0,  0,  0,  0,  0,  0,  0, -1, +1]
```

This is a tridiagonal matrix with +1 on the diagonal and -1 on the super/sub-diagonals. It computes a discrete second difference (Laplacian-like operation).

**Activation vector B:**

```
B = [+1, +1, +1, +1, +1, +1, +1, +1, +1]
```

**Hand calculation C = A x B:**

| Row | Computation | Result |
|-----|-------------|--------|
| C[0] | (+1)(+1) + (-1)(+1) + 0 + ... | +1 - 1 = 0 |
| C[1] | (-1)(+1) + (+1)(+1) + (-1)(+1) + 0 + ... | -1 + 1 - 1 = -1 |
| C[2] | 0 + (-1)(+1) + (+1)(+1) + (-1)(+1) + 0 + ... | -1 + 1 - 1 = -1 |
| C[3] | 0 + 0 + (-1)(+1) + (+1)(+1) + (-1)(+1) + 0 + ... | -1 + 1 - 1 = -1 |
| C[4] | ... same pattern ... | -1 |
| C[5] | ... same pattern ... | -1 |
| C[6] | ... same pattern ... | -1 |
| C[7] | ... same pattern ... | -1 |
| C[8] | 0 + ... + (-1)(+1) + (+1)(+1) | -1 + 1 = 0 |

**Expected output C:**

```
C = [0, -1, -1, -1, -1, -1, -1, -1, 0]
```

**Expected decoder outputs:**

| Output Column | Result | Dominant Detector |
|---------------|--------|-------------------|
| 0 | 0 | DET_0 |
| 1 | -1 | DET_-1 |
| 2 | -1 | DET_-1 |
| 3 | -1 | DET_-1 |
| 4 | -1 | DET_-1 |
| 5 | -1 | DET_-1 |
| 6 | -1 | DET_-1 |
| 7 | -1 | DET_-1 |
| 8 | 0 | DET_0 |

**Pass criteria:**
- Output vector C = [0, -1, -1, -1, -1, -1, -1, -1, 0].
- All 9 columns report correct results.
- Interior columns (1-7) all show DET_-1, providing a uniformity check on accumulated results.

---

### 6.5 Test Case 3.3: Full-Range Accumulation Test (Optional, Advanced)

**Purpose:** Test that the systolic accumulation handles the maximum possible dot product magnitude.

**Weight matrix A (all +1):**

```
A = [+1, +1, +1, +1, +1, +1, +1, +1, +1]
    [+1, +1, +1, +1, +1, +1, +1, +1, +1]
    [+1, +1, +1, +1, +1, +1, +1, +1, +1]
    [+1, +1, +1, +1, +1, +1, +1, +1, +1]
    [+1, +1, +1, +1, +1, +1, +1, +1, +1]
    [+1, +1, +1, +1, +1, +1, +1, +1, +1]
    [+1, +1, +1, +1, +1, +1, +1, +1, +1]
    [+1, +1, +1, +1, +1, +1, +1, +1, +1]
    [+1, +1, +1, +1, +1, +1, +1, +1, +1]
```

**Activation vector B:**

```
B = [+1, +1, +1, +1, +1, +1, +1, +1, +1]
```

**Expected output C:**
Each column computes the dot product of all-ones: sum = 9 x (+1) = +9.

In balanced ternary: +9 = 1 x 3^2 + 0 x 3^1 + 0 x 3^0, represented as (+1, 0, 0)_bal3.

```
C = [+9, +9, +9, +9, +9, +9, +9, +9, +9]
  = [(+1,0,0), (+1,0,0), (+1,0,0), (+1,0,0), (+1,0,0), (+1,0,0), (+1,0,0), (+1,0,0), (+1,0,0)]
```

**Note:** This test exercises the carry chain. The accumulated partial sum of 9 products (each +1) will generate carries as it exceeds the single-trit range [-1, +1]. The decoder must correctly interpret the multi-trit result.

**Pass criteria:**
- All 9 column decoders report value +9 (balanced ternary: +1, 0, 0).
- Carry chain operates correctly through all 9 accumulation stages.

---

### 6.6 Level 3 Pass Criteria Summary

| Test Case | Description | Pass Condition |
|-----------|-------------|----------------|
| 3.1 | Identity matrix | C = B for all 9 elements |
| 3.2 | Tridiagonal Laplacian | C = [0,-1,-1,-1,-1,-1,-1,-1,0] |
| 3.3 (optional) | Full accumulation | All columns report +9 with correct carries |

**Minimum passing:** Test 3.1 and Test 3.2 both pass. Test 3.3 is optional but recommended for carry chain validation.

---

## 7. Failure Diagnosis Flowchart

### 7.1 No Detector Signal

```
START: Detector reads near dark current when signal expected
  |
  +--> Is the laser ON and at correct wavelength?
  |      |
  |      NO --> Turn on laser. Verify wavelength with OSA or wavemeter.
  |      |
  |      YES
  |      |
  +--> Is the laser power at calibrated level?
  |      |
  |      NO --> Re-calibrate laser power (Section 3.4). Check VOA setting.
  |      |
  |      YES
  |      |
  +--> Is the fiber connected to the correct chip input port?
  |      |
  |      NO --> Re-connect to correct port. Input A = row input, Input B = weight bus.
  |      |
  |      YES
  |      |
  +--> Measure coupling power:
  |    Disconnect output fiber, place power meter at chip output facet.
  |    Any light emerging?
  |      |
  |      NO --> Fiber-chip alignment lost.
  |      |      Re-do active alignment (Section 3.3).
  |      |      If still no signal: fiber may be broken or chip facet damaged.
  |      |      Inspect fiber cleave and chip edge under microscope.
  |      |
  |      YES (but weak, <-30 dBm)
  |      |      Coupling loss too high.
  |      |      Re-align and optimize. Target: <3 dB loss per facet.
  |      |      If unable to achieve: try different V-groove position
  |      |      or re-cleave fiber.
  |      |
  |      YES (adequate power)
  |      |
  +--> Are BOTH wavelengths reaching the PE simultaneously?
  |      |
  |      NO --> SFG requires two photons. Verify both lasers are ON
  |      |      and routed to the same PE. Check timing synchronization.
  |      |
  |      YES
  |      |
  +--> Check waveguide integrity:
  |    Inject 1550 nm (strongest signal). Monitor with IR camera
  |    or scattered light. Is light propagating through the waveguide?
  |      |
  |      NO --> Waveguide defect (break, excessive loss, fabrication error).
  |      |      Try a different PE row/column to isolate the defect.
  |      |      Record the defective waveguide location.
  |      |
  |      YES
  |      |
  +--> SFG mixer may be non-functional:
         Check PPLN poling quality. The QPM period may be incorrect
         or the poling may have failed during fabrication.
         Try injecting both wavelengths at higher power (+15 dBm)
         to look for any SFG signal, even weak.
         If still nothing: PE is likely defective.
```

### 7.2 Wrong Detector Fires

```
START: A detector other than the expected one shows signal
  |
  +--> Is the unexpected detector adjacent to the expected one?
  |      |
  |      YES --> Possible AWG tuning error.
  |      |       The AWG demux center wavelengths may be shifted due
  |      |       to fabrication variation or temperature drift.
  |      |       ACTION: Adjust chip temperature by +/- 1 deg C
  |      |       and re-test. If the correct detector activates at
  |      |       a different temperature, the AWG needs thermal tuning.
  |      |       Record the optimal temperature.
  |      |
  |      NO --> Possible wavelength error or stray light.
  |      |
  +--> Verify input laser wavelengths:
  |    Use OSA (optical spectrum analyzer) or wavemeter to confirm
  |    each laser is within +/- 1 nm of nominal.
  |      |
  |      OUT OF SPEC --> Adjust laser temperature/current to correct wavelength.
  |      |
  |      IN SPEC
  |      |
  +--> Are multiple detectors firing simultaneously?
  |      |
  |      YES --> Possible crosstalk between adjacent waveguides or
  |      |       AWG channels. Measure the power ratio between
  |      |       strongest and second-strongest detector.
  |      |       If ratio > 10:1 (10 dB): acceptable crosstalk,
  |      |       threshold discriminator should resolve it.
  |      |       If ratio < 10:1: AWG channel isolation insufficient.
  |      |       Record values and escalate.
  |      |
  |      NO (single wrong detector)
  |      |
  +--> Check ring resonator tuning:
         If the chip uses ring resonators for wavelength routing,
         the resonance may have shifted. Sweep the corresponding
         heater voltage from 0 to 5V while monitoring the detector.
         Look for the voltage at which the correct detector activates.
         Record the required heater voltage.
```

### 7.3 Signal Too Weak

```
START: Expected detector fires but current is <1 uA (below useful range)
  |
  +--> Check loss budget:
  |    Measure optical power at each stage of the path:
  |    1. Laser output (should be ~+10 dBm)
  |    2. After fiber coupling (should be ~+7 to +9 dBm)
  |    3. At chip output facet (if accessible)
  |      |
  |      Loss > 5 dB at coupling --> Re-align fiber.
  |      Loss within budget but signal still weak -->
  |      |
  +--> Check SFG conversion efficiency:
  |    SFG is inherently inefficient (~10%, i.e., 10 dB loss).
  |    If input power is too low, SFG output may be below
  |    detector threshold.
  |    ACTION: Increase laser power by 3-6 dB and re-test.
  |      |
  |      Still weak -->
  |      |
  +--> Check detector responsivity:
  |    Inject a known-power visible source (e.g., 635 nm HeNe)
  |    directly into the detector fiber (bypassing the chip).
  |    Measure photocurrent.
  |    Expected: I = Responsivity x Power
  |              = 0.7 A/W x 100 uW = 70 uA
  |      |
  |      Detector responsivity < 0.3 A/W --> Detector may be
  |      damaged or wire bond broken. Test other detectors.
  |      |
  |      Detector OK -->
  |      |
  +--> Check TIA gain:
         Verify TIA transimpedance setting. At 100 kOhm gain:
         1 uA photocurrent --> 100 mV output.
         If oscilloscope shows <10 mV, TIA may be misconfigured
         or faulty. Replace/reconfigure TIA.
```

### 7.4 Wrong Computation Result (Row or Array Level)

```
START: Individual PEs work (Level 1 passes) but row/array result is incorrect
  |
  +--> Is the error in a specific column consistently?
  |      |
  |      YES --> That column has a defective PE or routing issue.
  |      |       Test each PE in that column individually (Level 1).
  |      |       Identify which row's PE is failing.
  |      |
  |      NO (errors vary across columns)
  |      |
  +--> Check weight streaming order:
  |    The FPGA may be sending weight matrix columns in the
  |    wrong order. Verify FPGA firmware matches the chip's
  |    column-to-weight-drop mapping.
  |      |
  |      Mapping error --> Fix FPGA firmware. Re-test.
  |      |
  |      Mapping correct
  |      |
  +--> Check systolic timing:
  |    The activation vector and weight columns must be
  |    synchronized to the 617 MHz clock.
  |    - Weight column 0 must arrive during clock cycle 0
  |    - Weight column 1 during clock cycle 1
  |    - etc.
  |    Use oscilloscope to verify timing alignment between
  |    the clock output and weight/activation signals.
  |      |
  |      Timing misaligned --> Adjust FPGA clock phase. Re-test.
  |      |
  |      Timing correct
  |      |
  +--> Check carry chain:
  |    If partial sums exceed +1 or -1, carry must propagate
  |    correctly between trit positions.
  |    Test with simple carry case: two consecutive (+1)(+1) = +1
  |    products in same column. Sum should be +2, which requires
  |    carry to the next trit position.
  |    If carry does not propagate: carry waveguide may be broken
  |    or misrouted. Inspect GDS layout vs. fabricated chip.
  |      |
  |      Carry failure --> Record defective carry location.
  |      |
  +--> Check accumulation loop:
         Each PE has an accumulator loop (recirculating delay).
         If the loop introduces excess loss or incorrect phase,
         partial sums will be wrong. Test by injecting a known
         sequence of products and monitoring the accumulated
         output over multiple clock cycles.
```

---

## 8. Data Recording Templates

### 8.1 Calibration Data Sheet

```
================================================================
CALIBRATION DATA SHEET — N-Radix 9x9 Chip
================================================================
Date: _______________     Operator: _______________
Chip ID: _______________  Serial #: _______________
Temperature: _________ deg C  (TEC setpoint: 25.0 deg C)

--- DARK CURRENT BASELINE (All lasers OFF) ---

| Detector | Col 0 (nA) | Col 4 (nA) | Col 8 (nA) | PASS? |
|----------|-----------|-----------|-----------|-------|
| DET_-2   |           |           |           | <10nA |
| DET_-1   |           |           |           | <10nA |
| DET_0    |           |           |           | <10nA |
| DET_+1   |           |           |           | <10nA |
| DET_+2   |           |           |           | <10nA |

--- SINGLE-WAVELENGTH REFERENCE (one laser at a time) ---

Test: 1550 nm only, +10 dBm, Row 0 input
| Detector | Col 0 (nA) | Above Dark? | PASS (<50nA above dark)? |
|----------|-----------|-------------|--------------------------|
| DET_-2   |           |             |                          |
| DET_-1   |           |             |                          |
| DET_0    |           |             |                          |
| DET_+1   |           |             |                          |
| DET_+2   |           |             |                          |

Test: 1310 nm only, +10 dBm, Row 0 input
| Detector | Col 0 (nA) | Above Dark? | PASS (<50nA above dark)? |
|----------|-----------|-------------|--------------------------|
| DET_-2   |           |             |                          |
| DET_-1   |           |             |                          |
| DET_0    |           |             |                          |
| DET_+1   |           |             |                          |
| DET_+2   |           |             |                          |

Test: 1064 nm only, +10 dBm, Row 0 input
| Detector | Col 0 (nA) | Above Dark? | PASS (<50nA above dark)? |
|----------|-----------|-------------|--------------------------|
| DET_-2   |           |             |                          |
| DET_-1   |           |             |                          |
| DET_0    |           |             |                          |
| DET_+1   |           |             |                          |
| DET_+2   |           |             |                          |

--- FIBER COUPLING ---

| Port      | Input Power (dBm) | Output Power (dBm) | Coupling Loss (dB) | PASS (<3dB)? |
|-----------|-------------------|--------------------|--------------------|--------------|
| Row 0 in  |                   |                    |                    |              |
| Weight bus|                   |                    |                    |              |

--- LASER POWER CALIBRATION ---

| Laser     | Nominal (dBm) | Measured (dBm) | Within +/-0.5dB? |
|-----------|---------------|----------------|------------------|
| 1550 nm   | +10.0         |                |                  |
| 1310 nm   | +10.0         |                |                  |
| 1064 nm   | +10.0         |                |                  |

--- THERMAL STABILITY ---

| Time (min) | Temperature (deg C) | Within +/-0.1 deg C? |
|------------|--------------------|-----------------------|
| 0          |                    |                       |
| 1          |                    |                       |
| 2          |                    |                       |
| 3          |                    |                       |
| 4          |                    |                       |
| 5          |                    |                       |

Calibration PASS: [ ]  FAIL: [ ]
Signed: _______________ Date: _______________
================================================================
```

### 8.2 Level 1 — Single PE Test Data Sheet

```
================================================================
LEVEL 1 DATA SHEET — Single PE Verification
================================================================
Date: _______________     Operator: _______________
Chip ID: _______________  PE Under Test: PE[___,___]

Detection threshold = 3 x (max dark current) + 100 nA = _______ nA

| Test | A | B | A*B | DET_-2 (uA) | DET_-1 (uA) | DET_0 (uA) | DET_+1 (uA) | DET_+2 (uA) | Expected Det | Correct? |
|------|---|---|-----|-------------|-------------|------------|-------------|-------------|--------------|----------|
| 1.1  |+1 |+1 | +1  |             |             |            |             |             | DET_+2       |          |
| 1.2  |+1 | 0 |  0  |             |             |            |             |             | DET_+1       |          |
| 1.3  |+1 |-1 | -1  |             |             |            |             |             | DET_-1       |          |
| 1.4  | 0 |+1 |  0  |             |             |            |             |             | DET_+1       |          |
| 1.5  | 0 | 0 |  0  |             |             |            |             |             | DET_0        |          |
| 1.6  | 0 |-1 |  0  |             |             |            |             |             | DET_0        |          |
| 1.7  |-1 |+1 | -1  |             |             |            |             |             | DET_-1       |          |
| 1.8  |-1 | 0 |  0  |             |             |            |             |             | DET_0        |          |
| 1.9  |-1 |-1 | +1  |             |             |            |             |             | DET_-2       |          |

Tests passed: ___/9
Level 1 PASS: [ ]  FAIL: [ ]
Notes: _______________________________________________________________
Signed: _______________ Date: _______________
================================================================
```

### 8.3 Level 2 — Row Dot Product Data Sheet

```
================================================================
LEVEL 2 DATA SHEET — Single Row Dot Product
================================================================
Date: _______________     Operator: _______________
Chip ID: _______________  Row Under Test: ___

--- Test 2.1: All-Ones ---
a = [+1,+1,+1,+1,+1,+1,+1,+1,+1]
w = [+1,+1,+1,+1,+1,+1,+1,+1,+1]
Expected: all DET_+2

| Col | DET_-2 | DET_-1 | DET_0 | DET_+1 | DET_+2 | Expected | Match? |
|-----|--------|--------|-------|--------|--------|----------|--------|
| 0   |        |        |       |        |        | DET_+2   |        |
| 1   |        |        |       |        |        | DET_+2   |        |
| 2   |        |        |       |        |        | DET_+2   |        |
| 3   |        |        |       |        |        | DET_+2   |        |
| 4   |        |        |       |        |        | DET_+2   |        |
| 5   |        |        |       |        |        | DET_+2   |        |
| 6   |        |        |       |        |        | DET_+2   |        |
| 7   |        |        |       |        |        | DET_+2   |        |
| 8   |        |        |       |        |        | DET_+2   |        |

Max/Min current ratio: ___ (target: <2x)
Test 2.1 PASS: [ ]  FAIL: [ ]

--- Test 2.2: Mixed Vector ---
a = [+1,-1, 0,+1,-1, 0,+1,-1, 0]
w = [+1,+1,+1,-1,-1,-1, 0, 0, 0]

| Col | a[j] | w[j] | Prod | Expected Det | Measured Det | Match? |
|-----|------|------|------|-------------|-------------|--------|
| 0   | +1   | +1   | +1   | DET_+2      |             |        |
| 1   | -1   | +1   | -1   | DET_-1      |             |        |
| 2   |  0   | +1   |  0   | DET_+1      |             |        |
| 3   | +1   | -1   | -1   | DET_-1      |             |        |
| 4   | -1   | -1   | +1   | DET_-2      |             |        |
| 5   |  0   | -1   |  0   | DET_0       |             |        |
| 6   | +1   |  0   |  0   | DET_+1      |             |        |
| 7   | -1   |  0   |  0   | DET_0       |             |        |
| 8   |  0   |  0   |  0   | DET_0       |             |        |

Test 2.2 PASS: [ ]  FAIL: [ ]

--- Test 2.3: Alternating Sign ---
a = [+1,-1,+1,-1,+1,-1,+1,-1,+1]
w = [-1,+1,-1,+1,-1,+1,-1,+1,-1]
Expected: all DET_-1

| Col | DET_-2 | DET_-1 | DET_0 | DET_+1 | DET_+2 | Expected | Match? |
|-----|--------|--------|-------|--------|--------|----------|--------|
| 0   |        |        |       |        |        | DET_-1   |        |
| 1   |        |        |       |        |        | DET_-1   |        |
| 2   |        |        |       |        |        | DET_-1   |        |
| 3   |        |        |       |        |        | DET_-1   |        |
| 4   |        |        |       |        |        | DET_-1   |        |
| 5   |        |        |       |        |        | DET_-1   |        |
| 6   |        |        |       |        |        | DET_-1   |        |
| 7   |        |        |       |        |        | DET_-1   |        |
| 8   |        |        |       |        |        | DET_-1   |        |

Max/Min current ratio: ___ (target: <3x)
Test 2.3 PASS: [ ]  FAIL: [ ]

Level 2 PASS: [ ]  FAIL: [ ]
Signed: _______________ Date: _______________
================================================================
```

### 8.4 Level 3 — Matrix Multiply Data Sheet

```
================================================================
LEVEL 3 DATA SHEET — Full 9x9 Matrix Multiply
================================================================
Date: _______________     Operator: _______________
Chip ID: _______________

--- Test 3.1: Identity Matrix ---
A = I (9x9 identity)
B = [+1,-1, 0,+1, 0,-1,+1,-1, 0]
Expected C = B

| Col | Expected | Measured | Match? | Latency (clk cycles) |
|-----|----------|----------|--------|----------------------|
| 0   | +1       |          |        |                      |
| 1   | -1       |          |        |                      |
| 2   |  0       |          |        |                      |
| 3   | +1       |          |        |                      |
| 4   |  0       |          |        |                      |
| 5   | -1       |          |        |                      |
| 6   | +1       |          |        |                      |
| 7   | -1       |          |        |                      |
| 8   |  0       |          |        |                      |

First result at clock cycle: ___ (expected: 9)
Test 3.1 PASS: [ ]  FAIL: [ ]

--- Test 3.2: Tridiagonal Laplacian ---
A = tridiagonal(+1, -1)
B = [+1,+1,+1,+1,+1,+1,+1,+1,+1]
Expected C = [0,-1,-1,-1,-1,-1,-1,-1,0]

| Col | Expected | Measured | Match? |
|-----|----------|----------|--------|
| 0   |  0       |          |        |
| 1   | -1       |          |        |
| 2   | -1       |          |        |
| 3   | -1       |          |        |
| 4   | -1       |          |        |
| 5   | -1       |          |        |
| 6   | -1       |          |        |
| 7   | -1       |          |        |
| 8   |  0       |          |        |

Test 3.2 PASS: [ ]  FAIL: [ ]

--- Test 3.3: Full Accumulation (Optional) ---
A = all +1
B = all +1
Expected C = [+9,+9,+9,+9,+9,+9,+9,+9,+9]

| Col | Expected (decimal) | Expected (bal3) | Measured | Match? |
|-----|--------------------|--------------------|----------|--------|
| 0   | +9                 | (+1, 0, 0)         |          |        |
| 1   | +9                 | (+1, 0, 0)         |          |        |
| 2   | +9                 | (+1, 0, 0)         |          |        |
| 3   | +9                 | (+1, 0, 0)         |          |        |
| 4   | +9                 | (+1, 0, 0)         |          |        |
| 5   | +9                 | (+1, 0, 0)         |          |        |
| 6   | +9                 | (+1, 0, 0)         |          |        |
| 7   | +9                 | (+1, 0, 0)         |          |        |
| 8   | +9                 | (+1, 0, 0)         |          |        |

Carry chain functional: [ ] Yes  [ ] No
Test 3.3 PASS: [ ]  FAIL: [ ]

Level 3 PASS: [ ]  FAIL: [ ]
Signed: _______________ Date: _______________
================================================================
```

---

## 9. Sign-Off Checklist

```
================================================================
FUNCTIONAL TEST SIGN-OFF — N-Radix 9x9 Chip
================================================================
Chip ID: _______________
Test Date: _______________
Operator: _______________
Witness: _______________

CALIBRATION
  [ ] Dark current baseline: all detectors < 10 nA
  [ ] Single-wavelength reference: no spurious SFG signals
  [ ] Fiber coupling loss: < 3 dB per facet
  [ ] Laser power calibrated: all 3 lasers within +/- 0.5 dB
  [ ] Thermal stability: +/- 0.1 deg C for 5 minutes

LEVEL 1: SINGLE PE
  [ ] Test 1.1: (+1)(+1) = +1     DET_+2 fires
  [ ] Test 1.2: (+1)( 0) =  0     DET_+1 fires
  [ ] Test 1.3: (+1)(-1) = -1     DET_-1 fires
  [ ] Test 1.4: ( 0)(+1) =  0     DET_+1 fires
  [ ] Test 1.5: ( 0)( 0) =  0     DET_0  fires
  [ ] Test 1.6: ( 0)(-1) =  0     DET_0  fires
  [ ] Test 1.7: (-1)(+1) = -1     DET_-1 fires
  [ ] Test 1.8: (-1)( 0) =  0     DET_0  fires
  [ ] Test 1.9: (-1)(-1) = +1     DET_-2 fires
  Tests passed: ___/9   Minimum: 8/9

LEVEL 2: SINGLE ROW
  [ ] Test 2.1: All-ones vector         9/9 columns correct
  [ ] Test 2.2: Mixed vector (6 SFG)    9/9 columns correct
  [ ] Test 2.3: Alternating sign         9/9 columns correct
  Tests passed: ___/3   Minimum: 3/3

LEVEL 3: FULL 9x9 MATRIX
  [ ] Test 3.1: Identity matrix          C = B
  [ ] Test 3.2: Tridiagonal Laplacian    C = [0,-1,-1,-1,-1,-1,-1,-1,0]
  [ ] Test 3.3: Full accumulation (opt)  All columns = +9
  Tests passed: ___/2 (or ___/3)   Minimum: 2/2

OVERALL RESULT
  [ ] PASS — Chip is functionally verified
  [ ] CONDITIONAL PASS — Minor defects noted: _______________
  [ ] FAIL — Critical defects: _______________

Notes:
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

Operator signature: _______________  Date: _______________
Witness signature:  _______________  Date: _______________
================================================================
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-17 | Initial release |
| 1.1 | 2026-02-18 | Added PE types (ADD/SUB, MUL/DIV); marked COMPLETE; circuit sim 8/8 PASS; renumbered subsections |

---

## References

- CHIP_INTERFACE.md — Optical and electrical interface specification
- PACKAGING_SPEC.md — Packaging, fiber coupling, and bond pad specification
- MONOLITHIC_9x9_VALIDATION.md — Chip validation report (simulation)
- monolithic_chip_9x9.py — Architecture and GDS generation source
- IOC_Driver_Spec.md — IOC driver software specification
- DRC_RULES.md — Design rule check specification
- Paper v1: DOI 10.5281/zenodo.18437600 — Wavelength-Division Ternary Logic
- Paper v2: DOI 10.5281/zenodo.18501296 — N-Radix Optical AI Accelerator

---

*This document is designed so that a lab technician unfamiliar with the N-Radix project can follow it step-by-step and independently verify chip functionality. All wavelengths, power levels, and expected values are drawn directly from validated simulation results (circuit simulation: 8/8 tests PASS) and the chip interface specification.*
