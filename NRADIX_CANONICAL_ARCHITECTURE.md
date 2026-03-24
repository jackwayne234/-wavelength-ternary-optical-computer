# NRadix Canonical Architecture
**Document type:** Canonical Reference — supersedes all prior conflicting notes  
**Author:** Christopher J. Riner  
**Date:** 2026-03-11  
**Status:** Authoritative  

---

## 1. Purpose

This document resolves the encoding conflict between SESSION_NOTES.md (unbalanced ternary {1,2,3}) and ARCHITECTURE_BREAKTHROUGH.md (signed ternary {−1,0,+1}) and establishes the single canonical architecture for the NRadix optical AI accelerator.

---

## 2. The Conflict — Resolved

Two documents describe the encoding differently. **Both are correct — they describe different layers.**

| Layer | Encoding | Reason |
|---|---|---|
| **Optical multiplier primitive** | {1, 2, 3} (unbalanced ternary) | SFG physics requires two non-zero input photons. Trit value 0 collapses the product — no signal, no distinguishable output. Validated: all 9×9 input combinations produce unique product frequencies. |
| **Weight encoding in MAC layer** | {−1, 0, +1} (signed ternary) | The signed framing in ARCHITECTURE_BREAKTHROUGH.md describes how weights are conceptually represented at the system level for the 81-output MAC. At this layer, trit 0 means "no contribution" — implemented physically as the absence of a routed input, not as a zero-frequency photon. |

**Rule:** No trit-0 photon ever enters an SFG junction. The zero weight is realized by routing — an unused input port simply carries no signal.

---

## 3. Canonical Architecture

### 3.1 Physics Substrate

- **Platform:** SiN/SiO₂ photonic chip, telecom C-band
- **Multiply primitive:** Sum Frequency Generation (SFG) in PPLN waveguides  
  - Multiplication is performed by physics, not logic gates  
  - Catalog fabrication — no exotic poling required  
- **Accumulate primitive:** Waveguide superposition  
  - Multiple SFG output signals co-propagate in a shared waveguide bus  
  - Optical interference IS the accumulator — no electronics in the MAC path  

### 3.2 Validated Frequency Map (Input Trits)

| Trit Value | Frequency |
|---|---|
| 1 | 191.0 THz |
| 2 | 194.0 THz |
| 3 | 201.0 THz |

Minimum separation between input frequencies: **3.0 THz** — sufficient to prevent crosstalk.

### 3.3 Validated SFG Output Metrics

| Metric | Value |
|---|---|
| Unique product frequencies | 6 |
| Extinction ratios | 11.5 – 14.8 dB |
| Power fractions | 80.5 – 90.9% |
| All 9 trit×trit combinations | Pass |
| Simulation platform | JAX BPM, RunPod NVIDIA L4 24GB |

### 3.4 MAC Array Architecture

The MAC (Multiply-Accumulate) array produces **81 unique output identifiers** from a 9×9 input matrix using a two-dimensional encoding scheme:

- **Coarse (port dimension):** Which output waveguide port the signal exits — encodes one axis of the matrix  
- **Fine (frequency dimension):** Which sub-frequency arrives at that port — encodes the other axis  
- **(port, frequency) pair** uniquely identifies the exact computation result  

Programming the matrix = swapping frequency sources at the input routing layer only. No weights are stored in waveguides. The waveguide network topology is static; the matrix is defined by which frequency is injected at each input port.

### 3.5 What the Old Code Does NOT Reflect

`systolic_array_2d.py` (electronic accumulator, systolic grid) is a legacy prototype. It does **not** represent the final architecture. It should be archived, not extended.

The final architecture has **no electronic accumulation**. The accumulator is optical superposition in a shared waveguide bus.

---

## 4. Architecture Summary (One Paragraph)

NRadix is a ternary optical MAC accelerator implemented on SiN/SiO₂. Multiplication is performed physically by SFG in PPLN waveguides using unbalanced ternary inputs encoded as {1,2,3} at frequencies {191.0, 194.0, 201.0} THz. Zero-weighted inputs are implemented by routing absence — no zero-frequency photons enter SFG junctions. Accumulation is performed by optical superposition in a shared waveguide bus, eliminating all electronic accumulators in the MAC path. The 9-port × 9-frequency output space yields 81 unique (port, frequency) output pairs. The matrix is programmed by swapping input frequency sources; no reconfigurable waveguide structures are required. Fabrication targets standard PPLN catalog processes in the telecom C-band.

---

## 5. Open Work Items

| Item | Priority | Notes |
|---|---|---|
| Archive systolic_array_2d.py | High | Move to /legacy/, do not extend |
| Build optical accumulator simulation | High | Model waveguide superposition of SFG outputs |
| Extend BPM pipeline to 2D MAC (9×9) | High | Confirm all 81 output pairs distinct |
| Delete SESSION_NOTES.md.merged_local from Drive | Low | Duplicate from git merge conflict |
| Upload Paper 5 (Prime Numbers / Causal Set Theory) to Zenodo | Medium | Draft complete, needs upload |
| Draft Paper 6 (Entropy rate in GR) | Medium | — |

---

## 6. Source Documents

- SESSION_NOTES.md — Google Drive ID: 1R6CymHrKdnfdzaP5nAzSsyobR1q8Vl2F  
  *Primary source for validated multiplier encoding and BPM simulation results*
- ARCHITECTURE_BREAKTHROUGH.md — Google Drive ID: 1AVQuAQiQ-6jOXQNxQcdWU_9JqQ0iYlmT  
  *Source for 81-output MAC concept and signed weight framing*
- ternary-optical-memory-2026-03-02.md — Google Drive ID: 1aHEfaFAdWfs5XY1WXQFPb6ttxFoqKdTN  
  *Supplementary memory architecture notes*
- NRadix_Project_Status_Report_2026-03-12.pdf — Local workspace  
  *Current project status and validation summary*

---

*This document is authoritative. In any conflict with prior notes, this document governs.*
