# Monolithic 9x9 N-Radix Chip — Validation Report

**Date:** 2026-02-08
**Topology:** Split-edge (IOC left, array center, IOC right)
**Material:** X-cut LiNbO3 (TFLN)
**Array:** 9×9 = 81 PEs

## Chip Dimensions

- Width: 1095 μm
- Height: 695 μm
- Material: X-cut LiNbO3 (TFLN), n = 2.2

## Validation Results

| Check | Result | Value |
|-------|--------|-------|
| Activation path matching | PASS | Spread: 0.000 ps |
| Weight path equalization | PASS | Spread: 0.000 ps |
| Loss budget | PASS | Margin: 18.70 dB |
| Timing skew | PASS | 0.0000% of clock |
| Wavelength collision-free | PASS | Min spacing: 24.1 nm |

## Overall: **ALL PASSED**

## Loss Budget Detail

- Total optical path: 1490 μm
- Total loss: 21.30 dB
- Laser power: +10 dBm
- Detector sensitivity: -30 dBm
- **Power margin: 18.70 dB**

## SFG Output Wavelengths

| Combination | Output λ (nm) |
|-------------|---------------|
| BLUE+BLUE | 532.0 |
| GREEN+BLUE | 587.1 |
| RED+BLUE | 630.9 |
| GREEN+GREEN | 655.0 |
| RED+GREEN | 710.0 |
| RED+RED | 775.0 |

Minimum spacing: 24.1 nm
