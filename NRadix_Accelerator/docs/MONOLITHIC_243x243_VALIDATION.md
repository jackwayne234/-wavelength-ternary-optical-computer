# Monolithic 243x243 N-Radix Chip — Validation Report

**Date:** 2026-02-08
**Topology:** Split-edge (IOC left, array center, IOC right)
**Material:** X-cut LiNbO3 (TFLN)
**Array:** 243x243 = 59,049 PEs
**Amplification:** EDWA (Er/Yb co-doped LiNbO3)

## Chip Dimensions

- Width: 13965 um (1.40 cm)
- Height: 13565 um (1.36 cm)
- Array area: 13365 x 13365 um (1.34 x 1.34 cm)

## Phase 1: Unamplified Loss Profile

### Horizontal Path (activation)

- Entry power: 2.95 dBm
- Exit power: -72.62 dBm
- Total loss: 75.57 dB
- **Signal dies at column 105** (43.2% of array)

### Vertical Path (partial sums)

- SFG output power: 0.00 dBm
- Power at detector: -79.62 dBm
- Total loss: 79.62 dB
- **Signal dies at row 96** (39.5% of array)

## Phase 2: EDWA Amplifier Design

| Parameter | Value |
|-----------|-------|
| Gain per stage | 12.0 dB |
| Stage length | 500.0 um |
| Noise figure | 5.0 dB |
| Pump wavelength | 980 nm |
| Pump power/stage | 50.0 mW |

### Horizontal Amplifiers

- Stages per row: 6
- Spacing: ~39 PEs (2123 um)
- Total horizontal amps: 1458

| Stage | After Column | Power Before | Power After |
|-------|-------------|-------------|------------|
| 1 | 32 | -7.3 dBm | 4.7 dBm |
| 2 | 70 | -7.1 dBm | 4.9 dBm |
| 3 | 109 | -7.3 dBm | 4.7 dBm |
| 4 | 147 | -7.1 dBm | 4.9 dBm |
| 5 | 186 | -7.2 dBm | 4.8 dBm |
| 6 | 225 | -7.3 dBm | 4.7 dBm |

### Vertical Amplifiers

- Stages per column: 6
- Spacing: ~39 PEs (2123 um)
- Total vertical amps: 1458

| Stage | After Row | Power Before | Power After |
|-------|----------|-------------|------------|
| 1 | 32 | -10.3 dBm | 1.7 dBm |
| 2 | 70 | -10.1 dBm | 1.9 dBm |
| 3 | 109 | -10.2 dBm | 1.8 dBm |
| 4 | 147 | -10.0 dBm | 2.0 dBm |
| 5 | 186 | -10.2 dBm | 1.8 dBm |
| 6 | 225 | -10.3 dBm | 1.7 dBm |

## Phase 3: Amplified Chip Summary

| Metric | Value |
|--------|-------|
| Total EDWA stages | 2916 |
| Total pump power | 145.80 W |
| Area overhead | 3.8% |
| Throughput | 36.43 TFLOPS |

## Validation Results

**Overall: SOME FAILED**

| Check | Result |
|-------|--------|
| Horizontal signal (amplified) | PASS |
| Vertical signal (amplified) | PASS |
| Vertical at detector | PASS |
| Pump power < 10W | FAIL |
| Area overhead < 20% | PASS |
