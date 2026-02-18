# Monte Carlo Process Variation Analysis — Monolithic 9x9 N-Radix Chip

**Date:** February 17, 2026
**Last updated:** February 18, 2026
**Script:** `NRadix_Accelerator/simulations/monte_carlo_9x9.py`
**Trials:** 10,000
**Seed:** 42 (reproducible)
**Status:** COMPLETE — results from 10,000-trial run (seed=42)
**Circuit simulation:** 8/8 tests passing

---

## 1. Purpose

This analysis answers the question: **Given realistic TFLN foundry process variations, what percentage of fabricated 9x9 N-Radix chips will actually work?**

Every fab has tolerances. Waveguides come out slightly wider or narrower. Etch depths vary. Poling periods drift. A chip design that works perfectly at nominal values might fail when these variations stack up unfavorably.

Monte Carlo simulation quantifies this risk by:
1. Defining realistic probability distributions for each fab parameter
2. Randomly sampling 10,000 "virtual chips" from those distributions
3. Re-running all validation checks on each virtual chip
4. Computing the fraction that pass — the **predicted yield**

---

## 2. Methodology

### 2.1 Approach

Each trial represents one chip fabricated with random process variations. All 6 geometric/material parameters and 5 component loss parameters are varied simultaneously using Gaussian distributions, clipped at +/- 3 sigma to prevent physically impossible values.

For each virtual chip, 5 validation checks (derived from `monolithic_chip_9x9.py`'s `run_integrated_validation()`) are re-evaluated. A chip passes only if **all 5 checks** pass.

### 2.2 Validation Checks

| # | Check | Pass Criterion | Physical Meaning |
|---|-------|---------------|------------------|
| 1 | **Loss Budget** | Power margin > 0 dB | Signal reaches detectors above sensitivity |
| 2 | **Wavelength Collision** | Min SFG spacing > 20 nm | AWG can separate all SFG products |
| 3 | **Ring Resonator Tuning** | Shift < 5 nm (thermal range) | Heaters can compensate ring detuning |
| 4 | **Path Timing Skew** | Skew < 5% of clock period | Weights arrive synchronously at PEs |
| 5 | **SFG Phase Matching** | Efficiency > 50% of nominal | PPLN still quasi-phase-matched |

---

## 3. Process Variation Parameters

### 3.1 Geometric & Material Parameters

| Parameter | Nominal | 1-sigma | 3-sigma | Unit | Source |
|-----------|---------|---------|---------|------|--------|
| Waveguide width | 500 | 6.67 | 20.0 | nm | DRC WG.W.1 |
| Ring coupling gap | 150 | 5.0 | 15.0 | nm | DRC RING.G.1 |
| PPLN poling period | 6.750 | 0.033 | 0.100 | um | DRC Section 10.1 |
| Etch depth | 400 | 3.33 | 10.0 | nm | DRC Section 10.1 |
| Propagation loss | 2.0 | 0.167 | 0.50 | dB/cm | DRC Section 10.1 |
| Refractive index | 2.200 | 0.00167 | 0.005 | - | Material spec |

### 3.2 Component Loss Parameters

| Component | Nominal Loss | 1-sigma | Unit |
|-----------|-------------|---------|------|
| MZI modulator | 3.0 | 0.5 | dB |
| Wavelength combiner | 3.0 | 0.3 | dB |
| SFG conversion | 10.0 | 1.5 | dB |
| AWG demux | 3.0 | 0.5 | dB |
| Edge coupling | 2.0 | 0.5 | dB |

### 3.3 Parameter Selection Rationale

**Waveguide width (500 nm +/- 20 nm):** The DRC specifies 480-520 nm for single-mode operation. Modern TFLN foundries (HyperLight, LIGENTEC) achieve ~10 nm within-die uniformity, but wafer-to-wafer and lot-to-lot variation pushes this to ~20 nm at 3-sigma. This is the parameter most likely to affect ring resonators and mode confinement.

**Ring coupling gap (150 nm +/- 15 nm):** The gap between ring resonator and bus waveguide controls the Q-factor and extinction ratio. Since it's defined by two separate edges, the gap tolerance compounds. The DRC specifies 130-170 nm range.

**PPLN poling period (6.75 um +/- 0.1 um):** Controls quasi-phase-matching for SFG. The DRC lists +/- 50 nm tolerance, but we use a more conservative 100 nm at 3-sigma to account for poling electrode misalignment and crystal domain irregularity.

**Etch depth (400 nm +/- 10 nm):** RIE etch uniformity across a wafer is typically 2-5%. A 10 nm variation on 400 nm depth (2.5%) is achievable with modern processes.

**Propagation loss (2.0 +/- 0.5 dB/cm):** Depends on sidewall roughness, material absorption, and waveguide geometry. The DRC targets < 3 dB/cm. State-of-art TFLN achieves < 1 dB/cm; we use 2.0 as a conservative nominal for a first-generation design.

**Refractive index (2.2 +/- 0.005):** Varies with crystal orientation, stoichiometry, thin-film thickness, and temperature. The variation is small but matters for resonant structures.

---

## 4. Physical Models

### 4.1 Loss Budget Model

Total optical loss from laser input to photodetector:

```
Total Loss = Propagation Loss + Component Losses

Propagation Loss = (total path length) x (loss per unit length)

Total Path = encoder (180 um) + routing (60 um) + 9 PEs (495 um)
           + output routing (555 um) + decoder (200 um) = 1490 um

Component Losses = MZI + Combiner + SFG + AWG + Edge Coupling

Power at Detector = Laser Power (10 dBm) - Total Loss
Margin = Power at Detector - Detector Sensitivity (-30 dBm)
```

### 4.2 Wavelength Collision Model

SFG output wavelengths are set by energy conservation (not by the fab process):

```
1/lambda_out = 1/lambda_a + 1/lambda_b
```

The 6 products from {1550, 1310, 1064} nm are fixed at {532.0, 587.1, 630.9, 655.0, 710.0, 775.0} nm. The minimum spacing (24.1 nm between 630.9 and 655.0) must exceed the AWG's minimum resolvable spacing (~20 nm). Refractive index variation affects the AWG's channel alignment, reducing the effective margin.

### 4.3 Ring Resonator Detuning Model

Ring resonance wavelength shift depends on effective index change:

```
delta_lambda / lambda = delta_n_eff / n_eff

delta_n_eff = 0.0002 * delta_width(nm)
            + 0.0001 * delta_etch(nm)
            + 0.8 * delta_n_material
```

Thermal tuning via TiN heaters can compensate up to ~5 nm of shift.

### 4.4 Path Timing Model

Timing skew comes from within-die refractive index non-uniformity:

```
Skew = (path length) * (delta_n_within_chip) / c

Within-chip n variation ~ 10% of chip-to-chip variation
```

Maximum acceptable skew: 5% of clock period (81 ps at 617 MHz).

### 4.5 SFG Phase Matching Model

SFG efficiency follows the sinc-squared function:

```
eta = sinc^2(delta_k * L / 2)

delta_k = k_a + k_b - k_out - 2*pi/Lambda_poling
```

where L = 20 um mixer length. PPLN period error and index change shift delta_k away from zero. Pass criterion: efficiency penalty < 3 dB.

---

## 5. Results

**Run date:** 2026-02-17 | **Seed:** 42 | **Trials:** 10,000

### 5.1 Overall Yield

| Metric | Value |
|--------|-------|
| Overall yield (all checks pass) | **99.82%** |
| Total trials | 10,000 |
| Verdict | EXCELLENT -- production-ready process margins |

### 5.2 Per-Check Yields

| Check | Yield | Worst Margin | Mean Margin |
|-------|-------|-------------|-------------|
| Loss Budget | 100.00% | +12.18 dB | +18.73 dB |
| Wavelength Collision | 100.00% | +4.00 nm | +4.06 nm |
| Ring Resonator Tuning | 99.82% | -1.10 nm | +3.64 nm |
| Path Timing Skew | 100.00% | +80.94 ps | +81.01 ps |
| SFG Phase Matching | 100.00% | +3.00 dB | +3.00 dB |

**Yield-limiting check:** Ring Resonator Tuning (only check with any failures -- 18 out of 10,000 trials). The ring resonance shifts beyond the 5 nm thermal tuning range when waveguide width and refractive index variations stack unfavorably.

### 5.3 Sensitivity Ranking

_Which parameter has the most impact on yield?_

| Rank | Parameter | |r| with yield | Impact |
|------|-----------|---------------|--------|
| 1 | Refractive Index | 0.0212 | LOW |
| 2 | Waveguide Width | 0.0166 | LOW |
| 3 | Coupling Gap | 0.0081 | LOW |
| 4 | Etch Depth | 0.0073 | LOW |
| 5 | Prop Loss | 0.0050 | LOW |
| 6 | PPLN Period | 0.0004 | LOW |

All correlations are low because yield is so high (99.82%). When nearly every chip passes, there is little variance in the outcome for the correlation to latch onto. The refractive index and waveguide width are the top two because they most strongly affect ring resonator detuning -- the only check with any failures.

### 5.4 Worst-Case Margins

| Check | Worst Margin | Status |
|-------|-------------|--------|
| Loss Budget | +12.18 dB | Large margin -- very robust |
| Wavelength Collision | +4.00 nm | Fixed by physics (energy conservation) |
| Ring Tuning | -1.10 nm | Yield-limiter (some chips exceed 5nm thermal range) |
| Path Timing | +80.94 ps | Enormous margin (81ps vs 81ps limit) |
| SFG Phase Matching | +3.00 dB | Adequate (mixer length provides broad bandwidth) |

### 5.5 Key Observations

1. **Loss budget has 18+ dB of margin.** The chip path is only 1490 um (~0.15 cm), so propagation loss is negligible. Component losses dominate but stay well within the 40 dB power budget.

2. **Wavelength collision is physically guaranteed.** SFG output wavelengths are set by energy conservation, not fab process. The 24.1 nm minimum spacing cannot be changed by process variation. The only risk is AWG misalignment from index variation, which reduces the effective margin by less than 0.1 nm.

3. **Ring resonator tuning is the yield limiter.** At 99.82%, this is still excellent, but it identifies what to watch. Increasing thermal tuning range (larger heaters) or reducing sensitivity (wider waveguides) would push yield toward 100%.

4. **Timing skew is negligible.** The 9x9 array's short paths (~440 um max) combined with lithographic precision make timing essentially perfect. This will become more important at 243x243 scale.

5. **SFG phase matching is robust.** The 20 um mixer length provides broad enough bandwidth that poling period variations within spec have essentially no impact on conversion efficiency.

---

## 6. Plots

> **Generated by the script into `docs/monte_carlo_plots/`**

| Plot | File | Description |
|------|------|-------------|
| Yield Summary | `yield_summary.png` | Bar chart of per-check and overall yield |
| Margin Histograms | `margin_histograms.png` | Distribution of margins for each check |
| Sensitivity Scatter | `sensitivity_scatter.png` | Each parameter vs. loss margin (pass/fail colored) |
| Loss Distribution | `loss_distribution.png` | Total optical loss across all trials |
| Ring Shift | `ring_shift_distribution.png` | Ring resonator detuning distribution |
| SFG Efficiency | `sfg_efficiency_distribution.png` | SFG phase matching penalty |
| Yield vs. Tolerance | `yield_vs_tolerance.png` | How yield changes if we tighten each parameter |

---

## 7. Interpretation Guide

### Reading the Yield Number

- **> 99%**: Excellent. The design has robust margins against process variation. Production-ready.
- **95-99%**: Good. Acceptable for prototyping and low-volume runs. Some chips may need binning.
- **90-95%**: Marginal. Consider tightening the most sensitive parameter tolerance.
- **< 90%**: Redesign recommended. Check which parameter dominates and address it.

### Reading the Sensitivity Analysis

The sensitivity ranking tells you which fab parameter to focus on:
- **High |r| (> 0.1)**: This parameter strongly affects yield. Tightening its tolerance or redesigning for more margin will help most.
- **Moderate |r| (0.03-0.1)**: Contributes but not dominant. Worth monitoring.
- **Low |r| (< 0.03)**: Yield is insensitive to this parameter. Current tolerance is adequate.

### Reading the Margin Histograms

Each histogram shows the distribution of "how much room to spare" for that check. The red dashed line at 0 is the pass/fail boundary. Designs should have the bulk of the distribution well to the right of 0, with the left tail not extending past it.

---

## 8. Assumptions & Limitations

1. **Gaussian distributions**: Real fab variations may have asymmetric or multimodal distributions (e.g., systematic etch loading effects). Gaussian is a reasonable first approximation.

2. **Parameter independence**: We assume fab parameters are statistically independent. In reality, waveguide width and etch depth may be correlated (same etch step). This means our variance might be slightly overestimated.

3. **Linearized physics**: The ring resonator detuning and effective index models use linear sensitivities. At extreme variations (> 3 sigma), nonlinear effects may appear.

4. **Single operating point**: We evaluate at one temperature and one set of input wavelengths. Thermal drift and wavelength drift are not included.

5. **No systematic errors**: We model only random variation, not systematic offsets (e.g., all waveguides 10nm too wide due to mask bias). Systematic errors would shift the entire distribution and could be corrected with design compensation.

6. **Component loss independence**: MZI, combiner, SFG, AWG, and coupling losses are varied independently. Some may be correlated through shared process steps.

---

## 9. Recommendations for Future Work

1. **Correlated parameter model**: Implement a covariance matrix for parameters that share process steps (width & etch depth, for example).

2. **Temperature sweep**: Run Monte Carlo at multiple temperatures (20-80 C) to understand thermal robustness.

3. **Design centering**: If yield is limited by one parameter, explore biasing the nominal design away from center to maximize the passing fraction (e.g., if wider waveguides always fail, bias the design to slightly narrower).

4. **Foundry data calibration**: Once test structures are fabricated, calibrate the variation model with real measured data from the foundry.

5. **243x243 extension**: Scale this analysis to the full 243x243 array, where longer paths and more PEs will tighten the loss budget.

---

## 10. How to Run

```bash
cd /home/jackwayne/Desktop/Projects/Optical_computing/NRadix_Accelerator/simulations
python3 monte_carlo_9x9.py
```

Output:
- Terminal: Full summary with yield, margins, and sensitivity ranking
- Plots: `../docs/monte_carlo_plots/*.png`
- Text summary: `../docs/monte_carlo_plots/results_summary.txt`

Section 5 has been populated with the actual results from the 10,000-trial run.

---

*Generated for the N-Radix Wavelength-Division Ternary Optical Computer Project*
