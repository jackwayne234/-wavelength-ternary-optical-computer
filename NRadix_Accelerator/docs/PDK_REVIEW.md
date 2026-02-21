# PDK Review — TFLN Foundry Landscape
## N-Radix 9x9 Monolithic Chip

**Date:** February 18, 2026
**Target Material:** X-cut LiNbO3 (Thin-Film Lithium Niobate / TFLN)
**Design Tool:** GDSFactory (Python)

---

## Executive Summary

No TFLN foundry currently publishes a downloadable PDK. This is an industry-wide reality — TFLN is still emerging from research into production. All foundries require direct engagement (and typically an NDA) before providing design rules. This is not a blocker; it means the next step is sending emails, not downloading files.

**Key finding:** QCi (Quantum Computing Inc., Tempe AZ) has emerged as a strong second option alongside HyperLight. Their PDK is built on **GDSFactory** — the exact same tool our GDS is generated with. Zero migration cost.

---

## 1. Foundry Landscape (February 2026)

| Foundry | Location | Status | PPLN Support | PDK Platform | Est. Cost |
|---------|----------|--------|-------------|-------------|-----------|
| **HyperLight** | Cambridge, MA | Volume production (6" line, 8" pilot) | Yes (native) | NDA-gated | $15-30k MPW |
| **QCi** | Tempe, AZ | Operational since March 2025 | Yes (explicitly listed) | **GDSFactory** | TBD |
| **CCRAFT** | Neuchatel, Switzerland | First wafer run Sep 2025 | Unknown | Customer-gated | TBD |
| **Lightium** | Switzerland | Closed beta | Likely (chi-2 stated) | Closed beta | TBD |

### 1.1 HyperLight (Primary Target)

**Why they're first choice:**
- Native TFLN platform — d33 ~ 30 pm/V chi2 nonlinearity
- Volume production on 6-inch wafers, 8-inch pilot line
- Demonstrated waveguide losses below 2 dB/m (Nature Photonics, Oct 2025 with Xanadu)
- Supports wavelength range 0.5-2.0 um
- Periodic poling services available

**PDK status:**
- Not publicly downloadable
- Requires NDA + design engagement
- Pre-written inquiry email exists in `FOUNDRY_SUBMISSION_PACKAGE.md` Section 4.1

**Recent developments:**
- Launched TFLN Chiplet platform (March 2025)
- Partnership with Xanadu for quantum photonic chips
- Hiring MPW engineers (active job listings)

### 1.2 QCi (Strong Alternative — NEW)

**Why they deserve attention:**
- PDK built on **GDSFactory** — our GDS generator uses the exact same framework
- Explicitly list PPLN waveguides and microrings as standard capabilities
- Achieved 0.3 nm sidewall roughness (exceptional)
- NIST contract for TFLN photonic chip fabrication (government validation)
- US domestic (Tempe, AZ)

**PDK status:**
- GDSFactory-based PDK previewed January 2025
- Likely requires engagement to access full rules
- 5th purchase order received as of Jan 2025

**Key advantage:** If we use QCi, our existing GDSFactory-based generation pipeline maps directly. No format conversion, no layer translation headaches.

### 1.3 CCRAFT (European Option)

- Spun off from CSEM (Swiss research center) in 2025
- First pure-play TFLN foundry in Europe
- First wafer run completed September 2025
- PPLN support unknown — needs inquiry

### 1.4 Lightium (Watch List)

- Swiss TFLN foundry in closed beta
- States chi-2 capability
- 780/830 nm PDK bands — closest spectral match to our SFG outputs (532-775 nm)
- Worth a speculative inquiry

---

## 2. Layer Mapping Readiness

### 2.1 Our Layers vs. Expected Foundry Support

| Our Layer | Name | Foundry Support | Status |
|-----------|------|----------------|--------|
| (1, 0) | WAVEGUIDE | Standard at all TFLN foundries | Ready |
| (2, 0) | CHI2_SFG (PPLN) | HyperLight: native. QCi: explicit. Others: TBD | Ready |
| (3, 0) | PHOTODET | Hybrid integration required (Ge/InGaAs) | **Gap** |
| (4, 0) | CHI2_DFG (PPLN) | Same as SFG — different poling period | Ready |
| (5, 0) | KERR_CLK | Uses chi3 in LiNbO3 — standard waveguide | Ready |
| (6/15, 0) | AWG_BODY | Standard waveguide etch | Ready |
| (10, 0) | METAL1_HEATER | TiN heaters — standard at all foundries | Ready |
| (12, 0) | METAL2_PAD | Ti/Au bond pads — standard | Ready |
| (13, 0) | DOPING_SA | Er/Yb implant — non-standard | Optional for MVP |
| (14, 0) | DOPING_GAIN | Er/Yb implant — non-standard | Optional for MVP |
| (99, 0) | ALIGNMENT | Cr/Au marks — standard | Ready |

### 2.2 Existing Mapping Tables

The `LAYER_MAPPING.md` already contains detailed mapping tables for:
- HyperLight (primary)
- AIM Photonics
- IMEC
- Ligentec
- Applied Nanotools

These will need updating once the actual foundry PDK is received, but they provide a solid starting framework.

---

## 3. Gap Analysis

### Gap 1 (Critical): Photodetector Integration at 532-775 nm

Our SFG outputs are in the visible range (532-775 nm), but telecom TFLN foundries optimize detectors for 1300-1600 nm. Germanium photodetectors (standard in telecom) have poor response below 900 nm.

**Options:**
- InGaAs hybrid bonding (works for our wavelength range)
- External detection via fiber coupling (MVP approach — simplest)
- Si photodiodes for visible range (if foundry supports hybrid Si integration)

**Recommendation:** For MVP, use external detection. Discuss hybrid integration for Phase 2.

### Gap 2 (Important): PPLN Poling Period Confirmation

Our design requires 6.5-7.0 um poling period for non-telecom SFG wavelengths (1550+1064 -> 631 nm). Standard PPLN foundry offerings target telecom bands with different periods.

**Action:** Must confirm with foundry that custom poling periods in our range are achievable.

### Gap 3 (Minor): Layer Number Remapping

Our generic layer numbers (1, 2, 10, 12, etc.) will need to be remapped to the foundry's specific scheme. This is a trivial GDS edit — the `LAYER_MAPPING.md` already documents the expected mappings.

---

## 4. Recommended Next Steps

### Immediate (This Week)

1. **Send HyperLight inquiry** — pre-written email in `FOUNDRY_SUBMISSION_PACKAGE.md` Section 4.1
2. **Send QCi inquiry** — see draft email in Section 6 below
3. **Send Lightium inquiry** — speculative, but 780/830 nm bands are the closest spectral match

### After PDK Received

4. Compare design rules against our DRC_RULES.md
5. Remap layers using LAYER_MAPPING.md
6. Regenerate foundry-ready GDS with correct layers
7. Submit for foundry DRC

---

## 5. Industry Context

The TFLN foundry ecosystem is in rapid expansion (2024-2026):

- HyperLight + Xanadu: record-low waveguide losses (Nature Photonics, Oct 2025)
- QCi: NIST government contract for TFLN fabrication
- CCRAFT: first pure-play European TFLN foundry
- ELENA EU project: Europe's first commercial LNOI wafer supply chain

Good timing for N-Radix. The ecosystem is mature enough to fabricate but young enough that foundries seek novel design partners.

---

## 6. QCi Draft Inquiry Email

```
Subject: TFLN MPW Inquiry — Novel Ternary Optical Processor (GDSFactory PDK)

Dear QCi Foundry Services Team,

I am developing a wavelength-division ternary optical processor on TFLN
and am interested in your foundry services for an MVP fabrication run.

Key design parameters:
- Chip size: ~1.1 x 0.7 mm
- Material: X-cut TFLN
- Waveguide width: 500 nm (single-mode)
- Critical feature: PPLN periodic poling (6.5-7.0 um period) for
  sum-frequency generation at non-telecom wavelengths
- Operating wavelengths: 1550/1310/1064 nm inputs, 532-775 nm SFG outputs
- Components: 81 SFG mixers, MZI modulators, AWG demux, ring resonators
- Design tool: GDSFactory (compatible with your PDK platform)

Design validated: circuit simulation 8/8 PASS, Monte Carlo 99.82% yield
(10,000 trials), thermal analysis 15-45C passive window.

Questions:
1. Can you accommodate custom PPLN poling periods of 6.5-7.0 um?
2. What detection options exist for visible-range (532-775 nm) outputs?
3. What is your current MPW schedule and pricing?
4. Can I access your GDSFactory PDK for design rule verification?

Complete design package ready (GDS, DRC report, test plan).

Thank you,
Christopher Riner
```

---

## References

- [HyperLight Corporation](https://hyperlightcorp.com)
- [QCi TFLN Foundry Services](https://quantumcomputinginc.com/foundry)
- [QCi GDSFactory PDK Preview (Jan 2025)](https://www.prnewswire.com/news-releases/quantum-computing-inc-secures-fifth-purchase-order/)
- [QCi NIST Contract](https://quantumcomputinginc.com/news/press-releases/qci-nist-contract)
- [CCRAFT Foundry Launch (2025)](https://optics.org/news/16/5/19)
- [Lightium TFLN Foundry](https://lightium.com/)

---

*N-Radix Wavelength-Division Ternary Optical Computer Project — February 2026*
