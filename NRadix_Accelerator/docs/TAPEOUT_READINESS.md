# Tape-Out Readiness Checklist — Monolithic 9x9 N-Radix Chip

**Created:** 2026-02-17
**Branch:** fab/9x9-monolithic-tape-out
**Goal:** Achieve highest confidence before foundry submission and public announcement

---

## Status Summary

| # | Gap | Status | Document | Priority |
|---|-----|--------|----------|----------|
| 1 | Circuit-level simulation (full chip) | **COMPLETE (single triplet)** — 8/8 tests PASS (incl. IOC domain modes). 6-triplet found cross-coupling issue → MVP single-triplet is solid, multi-triplet needs per-triplet PPLN sections | [CIRCUIT_SIMULATION_PLAN.md](CIRCUIT_SIMULATION_PLAN.md) | CRITICAL |
| 2 | Monte Carlo process variation analysis | **COMPLETE** — 10,000 trials, 99.82% yield, ring tuning is limiting factor | [MONTE_CARLO_ANALYSIS.md](MONTE_CARLO_ANALYSIS.md) | CRITICAL |
| 3 | Thermal sensitivity analysis | **COMPLETE** — 30°C passive window (15-45°C), SFG >99.9% across range, TEC optional | [THERMAL_SENSITIVITY.md](THERMAL_SENSITIVITY.md) | HIGH |
| 4 | End-to-end functional test plan | **COMPLETE** — 3 test levels, 9 PE tests, failure diagnosis flowcharts, data sheets | [FUNCTIONAL_TEST_PLAN.md](FUNCTIONAL_TEST_PLAN.md) | HIGH |
| 5 | Post-fab test bench design & BOM | **COMPLETE** — 4 budget tiers ($1.8k-$16.5k), FPGA firmware spec, setup procedure | [TEST_BENCH_DESIGN.md](TEST_BENCH_DESIGN.md) | MEDIUM |

---

## Gap 1: Circuit-Level Simulation (CRITICAL)

**Problem:** Individual components validated via Meep FDTD, but no simulation of the full 9x9 chip as an integrated photonic circuit — light in one side, computed result out the other.

**What's needed:**
- Select photonic circuit simulator (Lumerical INTERCONNECT, Simphony, SAX, or similar)
- Build S-parameter models for each component (waveguide, ring resonator, SFG mixer, AWG, photodetector)
- Connect into full 9x9 systolic array circuit
- Run end-to-end: inject ternary-encoded wavelengths, verify correct computed outputs
- Document tool selection rationale, setup, and results

**Success criteria:** Simulate a known ternary multiplication (e.g., [1, -1, 0] × [1, 1, -1]) through the 9x9 array and get correct output at photodetectors.

**Output:** `CIRCUIT_SIMULATION_PLAN.md` + simulation script

---

## Gap 2: Monte Carlo Process Variation Analysis (CRITICAL)

**Problem:** Current validation assumes perfect fabrication. Real foundries have ±10-20nm variation on critical dimensions. Need to prove the design survives realistic fab tolerances.

**What's needed:**
- Identify critical parameters: waveguide width, coupling gap, PPLN poling period, etch depth, waveguide loss rate
- Define realistic variation ranges (from foundry PDK specs or literature)
- Run 1000+ Monte Carlo trials varying all parameters simultaneously
- Re-run all 5 validation checks per trial
- Report: yield estimate, sensitivity ranking, worst-case margins

**Success criteria:** >95% yield across all validation checks with realistic fab tolerances.

**Output:** `MONTE_CARLO_ANALYSIS.md` + `monte_carlo_9x9.py` script

---

## Gap 3: Thermal Sensitivity Analysis (HIGH)

**Problem:** Ring resonators shift ~10 pm/°C. SFG phase-matching is temperature-dependent. No analysis showing how much temperature drift the design tolerates.

**What's needed:**
- Model temperature-dependent refractive index of LiNbO3 (thermo-optic coefficient)
- Sweep operating temperature from 15°C to 45°C
- Track: ring resonator wavelength shift, SFG efficiency change, AWG channel drift
- Determine: safe operating window, whether TEC is required or optional
- Quantify heater tuning range needed to compensate

**Success criteria:** Define the temperature tolerance window (e.g., "design works within ±2°C without active tuning, ±10°C with heater compensation").

**Output:** `THERMAL_SENSITIVITY.md` + `thermal_sweep_9x9.py` script

---

## Gap 4: End-to-End Functional Test Plan (HIGH)

**Problem:** PCM characterization exists (waveguide loss, ring Q, etc.) but no step-by-step procedure to prove the chip actually computes correctly.

**What's needed:**
- Define specific ternary test vectors (start simple, build up):
  - **Test 1:** Single PE — inject two trits, verify correct SFG product at detector
  - **Test 2:** Single row — 9 PEs, verify correct dot product
  - **Test 3:** Full 9x9 — inject two 9-element ternary vectors, verify matrix multiply
- For each test: exact input wavelengths, power levels, expected detector readings, pass/fail thresholds
- Include calibration procedure (baseline detector readings with no input, single-wavelength reference)
- Include failure diagnosis flowchart (if test fails, here's how to isolate the problem)

**Success criteria:** A technician with the test bench could follow this document and independently verify chip functionality.

**Output:** `FUNCTIONAL_TEST_PLAN.md`

---

## Gap 5: Post-Fab Test Bench Design (MEDIUM)

**Problem:** No detailed design for the physical test setup — what equipment, what FPGA code, what software reads detectors and confirms correct answers.

**What's needed:**
- Complete bill of materials with part numbers and costs
- Test bench block diagram (laser sources → fiber array → chip → detectors → TIA → ADC → FPGA → PC)
- FPGA firmware spec (encode ternary inputs, synchronize with clock, read detector outputs)
- PC software spec (send test vectors, collect results, compare to expected, report pass/fail)
- Setup procedure (step-by-step from unboxing to first measurement)
- Estimated total cost for MVP test bench

**Success criteria:** Could hand this document to a lab technician and they could build the test bench from scratch.

**Output:** `TEST_BENCH_DESIGN.md`

---

## Session 2026-02-17 Deliverables

### Circuit Simulation (Gap 1 — RESOLVED for single triplet)
- [x] SAX-based circuit simulator implemented (`circuit_sim/simulate_9x9.py`)
- [x] 8 component models: waveguide, bend, SFG mixer, MZI encoder, combiner, AWG, photodetector, meander
- [x] 8/8 single-triplet tests PASS (multiplication table, identity, all-ones, isolation, mixed 3x3, tridiagonal, IOC domain modes, loss budget)
- [x] Worst-case power margin: 17.6 dB at PE[0,8]
- [x] 6-triplet WDM simulation (`circuit_sim/simulate_6triplet.py`) — **found cross-triplet PPLN coupling at 60nm spacing**
- [x] Each triplet individually: all 6 PASS
- [x] Cross-triplet isolation: FAIL at 60nm spacing (adjacent triplet SFG efficiency ~98%)
- [x] Solutions identified: per-triplet PPLN sections, separate waveguide lanes, or wider spacing
- [x] **Conclusion: Single-triplet MVP is validated and fab-ready. Multi-triplet is Phase 2.**

### Turnkey Foundry Submission Package (NEW)
- [x] `FOUNDRY_SUBMISSION_PACKAGE.md` — 842-line complete submission guide
- [x] 4 pre-written foundry inquiry emails (HyperLight, AIM, Applied Nanotools, follow-up)
- [x] Day-by-day execution timeline (funding → fab → test → results in 4-7 months)
- [x] Budget: ~$25k realistic middle for Phase 1 MVP
- [x] 30+ item pre-submission checklist
- [x] Risk register: 17 risks with mitigations
- [x] Parallel actions plan (order test equipment while chip is being fabricated)

### Session 2026-02-18 Updates

#### IOC Domain Modes (ADD/SUB vs MUL/DIV)
- [x] IOCInterpreter class added to circuit simulation
- [x] IOC domain modes test: PASS (8/8 total tests)
- [x] ADD/SUB PEs: straight ternary addition/subtraction (direct)
- [x] MUL/DIV PEs: log-domain addition → multiplication (IOC handles encoding)
- [x] All PEs physically just add — IOC determines meaning
- [x] Verified: physical signals identical between modes (glass doesn't change)

#### 3^3 Tower Encoding — DROPPED
- [x] 3^3 encoding for ADD/SUB PEs investigated and **dropped**
- [x] Reason: cubing doesn't distribute over addition — (a+b)^3 != a^3 + b^3
- [x] Minimum representable value would be 27, creating gaps for values 1-26
- [x] Removed from: simulate_9x9.py, DRIVER_SPEC.md, DRIVER_CHEATSHEET.md
- [x] MUL/DIV log-domain encoding remains (mathematically sound)

#### Interactive Demo
- [x] `circuit_sim/demo.py` — Tkinter GUI with 5 example buttons
- [x] Visual 9x9 grid, animated light propagation, wavelength-colored cells
- [x] All 5 examples verified against physics simulation

#### Documentation Package
- [x] All 12 docs converted to styled HTML with navigation
- [x] Desktop folder: `NRadix_Chip_Package/START_HERE.html`

---

## Previously Completed (No Gaps)

These items are already done and documented:

- [x] Monolithic 9x9 architecture design (`monolithic_chip_9x9.py`)
- [x] All 5 validation checks PASS
- [x] DRC rules (`DRC_RULES.md`)
- [x] Layer mapping for 5 foundries (`LAYER_MAPPING.md`)
- [x] MPW reticle plan — 3 phases (`MPW_RETICLE_PLAN.md`)
- [x] Chip interface specification (`CHIP_INTERFACE.md`)
- [x] Packaging specification (`PACKAGING_SPEC.md`)
- [x] Foundry questions prepared (`FOUNDRY_QUESTIONS.md`)
- [x] PCM test structure designs
- [x] GDS generator (gdsfactory, reproducible)
- [x] SFG wavelength collision analysis (24.1 nm min spacing)
- [x] Loss budget analysis (18.70 dB margin)
- [x] 81x81 FDTD validation PASSED
- [x] Paper v1 (theory) published — Zenodo DOI: 10.5281/zenodo.18437600
- [x] Paper v2 (architecture) published — Zenodo DOI: 10.5281/zenodo.18501296

---

## Foundry Submission Checklist

When all 5 gaps are closed, these are the final steps:

- [ ] All 5 gaps above resolved and documented
- [ ] Final GDS generated from `monolithic_chip_9x9.py` with latest parameters
- [ ] GDS passes KLayout DRC with zero violations
- [ ] Circuit simulation confirms end-to-end functionality
- [ ] Monte Carlo shows >95% yield
- [ ] Thermal analysis defines operating window
- [ ] Test bench BOM ordered / on hand
- [ ] Functional test plan reviewed
- [ ] Foundry (HyperLight) contacted with design package
- [ ] Foundry DRC review passed
- [ ] MPW slot reserved and paid
- [ ] Ship it

---

## Post-Fab Sequence

When the chip comes back from foundry:

1. **Visual inspection** — microscope check for obvious defects
2. **Die attach** — mount on AlN submount per PACKAGING_SPEC.md §9.1
3. **Wire bonding** — per PACKAGING_SPEC.md §9.2 sequence
4. **Fiber alignment** — per PACKAGING_SPEC.md §9.3 procedure
5. **PCM characterization** — waveguide loss, ring Q, SFG efficiency (per PCM structures)
6. **Functional testing** — per FUNCTIONAL_TEST_PLAN.md
7. **Performance measurement** — throughput, power, latency
8. **Document results** — update this file with measured vs. simulated comparison
9. **Tweet** — with real data backing every claim

---

*This document is the single source of truth for tape-out readiness. Read it at the start of every session.*
