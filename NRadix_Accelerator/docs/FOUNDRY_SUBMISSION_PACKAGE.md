# Turnkey Foundry Submission Package
# Monolithic 9x9 N-Radix Ternary Optical Processor

**Version:** 1.2
**Date:** February 21, 2026
**Author:** Christopher Riner
**Branch:** fab/9x9-monolithic-tape-out
**Status:** READY TO SEND when funding clears

---

> **What this document is:** Everything needed to go from "yes, we have funding" to
> "GDS is at the foundry" in 24 hours. Pre-written emails, file lists, cost breakdowns,
> timelines, and contingency plans. Print it, check boxes, execute.

> **Update 2026-02-21:** Isolated-lane architecture validated. Each SFG pair now gets a
> dedicated PPLN waveguide, eliminating cross-talk and SHG suppression requirements.
> Full 6-lane FDTD integration test: **36/36 PASS** across all 6 wavelength triplets
> (1000–1340 nm inputs, 500–670 nm SFG outputs). Material model fixed: Sellmeier equation
> corrected (Zelmon et al. coefficients), FDTD-stable single-pole Lorentzian fit with
> f₀=3.5 below stability boundary. QPM periods range 5.01–13.30 μm across triplets.
>
> **Update 2026-02-18:** Circuit simulation is COMPLETE (8/8 tests PASS). Single-triplet
> MVP is fab-ready. 6-triplet WDM cross-coupling was found during simulation -- multi-triplet
> operation is deferred to Phase 2. The 3^3 encoding scheme (tower levels, 27-state cubing)
> has been DROPPED because cubing does not distribute over addition. All PEs physically
> perform addition; the IOC determines whether the result represents ADD/SUB (straight
> ternary) or MUL/DIV (log-domain).

---

## Table of Contents

1. [Pre-Submission Checklist](#1-pre-submission-checklist)
2. [Submission Package Contents](#2-submission-package-contents)
3. [Foundry-Specific Submission Instructions](#3-foundry-specific-submission-instructions)
4. [Draft Inquiry Emails](#4-draft-inquiry-emails)
5. [Financial Planning](#5-financial-planning)
6. [Parallel Actions Timeline](#6-parallel-actions-timeline)
7. [Risk Register](#7-risk-register)

---

## 1. Pre-Submission Checklist

Every box must be checked before the GDS leaves the building.

### 1.1 Technical Readiness

- [x] Monolithic 9x9 architecture validated (all 5 checks PASS)
- [x] GDS generator script functional (`architecture/monolithic_chip_9x9.py`)
- [x] DRC rules documented (`DRC_RULES.md`)
- [x] Layer mapping for target foundries (`LAYER_MAPPING.md`)
- [x] SFG wavelength collision analysis PASS (24.1 nm min spacing)
- [x] Loss budget analysis PASS (18.70 dB margin)
- [x] Monte Carlo yield analysis: 99.82% predicted yield (10,000 trials)
- [x] Thermal sensitivity: 30 C passive window (15-45 C), TEC optional
- [x] PCM test structures designed (waveguide loss, ring Q, SFG efficiency)
- [x] Functional test plan complete (3 test levels, 9 PE tests)
- [x] Test bench BOM complete (4 budget tiers, $1.8k-$16.5k)
- [x] Circuit-level simulation (SAX) -- COMPLETE, 8/8 tests PASS
- [x] 6-lane IOC FDTD integration test -- COMPLETE, 36/36 PASS (isolated-lane architecture)
- [x] Sellmeier material model corrected (Zelmon et al. coefficients, FDTD-stable Lorentzian)
- [ ] Final GDS regenerated from latest parameters
- [ ] GDS passes KLayout DRC with zero violations
- [ ] GDS layer mapping remapped to target foundry PDK
- [ ] Foundry-specific PDK downloaded and reviewed

### 1.2 Financial Readiness

- [ ] Funding source confirmed (grant, self-fund, investor, crowdfunding)
- [ ] Payment method set up (credit card, wire transfer, purchase order)
- [ ] MPW deposit amount confirmed with foundry
- [ ] Test bench budget allocated ($4k-$16.5k depending on tier)
- [ ] Packaging budget allocated ($300-$1,500)
- [ ] Contingency reserve set aside (20% of total budget)

### 1.3 Logistical Readiness

- [ ] Foundry contacted and design reviewed (or inquiry email sent)
- [ ] MPW run date identified and slot reserved (or waitlisted)
- [ ] NDA signed with foundry (if required)
- [ ] Shipping address confirmed for die return
- [ ] Wire bonding service identified and scheduled
- [ ] Lab space available for test bench assembly
- [ ] Long-lead items ordered (V-groove fiber array: 4-6 week lead time)

### 1.4 Documentation Readiness

- [x] Paper v1 (theory) published: DOI 10.5281/zenodo.18437600
- [x] Paper v2 (architecture) published: DOI 10.5281/zenodo.18501296
- [x] Chip interface specification (`CHIP_INTERFACE.md`)
- [x] Packaging specification (`PACKAGING_SPEC.md`)
- [x] Foundry questions prepared (`FOUNDRY_QUESTIONS.md`)
- [x] MPW reticle plan (`MPW_RETICLE_PLAN.md`)

---

## 2. Submission Package Contents

### 2.1 Packing List -- What Goes to the Foundry

Every file listed below must be included in the submission. The foundry receives a single ZIP archive.

| # | File | Format | How to Generate / Where to Find | Purpose |
|---|------|--------|--------------------------------|---------|
| 1 | `nradix_9x9_monolithic.gds` | GDSII | `python architecture/monolithic_chip_9x9.py` | Chip layout -- the design itself |
| 2 | `layer_mapping_[FOUNDRY].csv` | CSV | Derived from `LAYER_MAPPING.md`, Section: Foundry Mapping Guide | Maps our generic layers to foundry PDK layers |
| 3 | `DESIGN_SUMMARY.pdf` | PDF | Export from this document + `CHIP_INTERFACE.md` | 2-page overview: what the chip does, key specs |
| 4 | `DRC_REPORT.txt` | Text | KLayout DRC run output using `DRC_RULES.md` script | Proof the design is clean |
| 5 | `test_plan_summary.pdf` | PDF | Export from `FUNCTIONAL_TEST_PLAN.md` | What we measure when dies come back |
| 6 | `pcm_structures.pdf` | PDF | Extract from `MPW_RETICLE_PLAN.md` Section 5 | Process control monitor descriptions |
| 7 | `contact_info.txt` | Text | See below | Designer contact details |

### 2.2 GDS Regeneration Procedure

Before submission, regenerate the GDS from source to ensure it reflects the latest parameters:

```bash
cd /home/jackwayne/Desktop/Projects/Optical_computing/NRadix_Accelerator/architecture
python monolithic_chip_9x9.py
```

The script outputs a GDS file via gdsfactory. Verify by opening in KLayout:
1. Open in KLayout
2. Verify all layers are present (WAVEGUIDE, CHI2_SFG, PHOTODET, AWG_BODY, METAL1_HEATER, METAL2_PAD, ALIGNMENT)
3. Run DRC script from `DRC_RULES.md` Section 11
4. Confirm zero violations
5. Export layer-specific mask files if foundry requires separate masks

### 2.3 Layer Remapping for Target Foundry

The GDS uses generic layer numbers. Before submission, remap to the target foundry's PDK:

**For HyperLight (primary):**

| Our Layer | Our # | HyperLight Layer | Action |
|-----------|-------|-----------------|--------|
| WAVEGUIDE | (1, 0) | WG | Remap layer number |
| CHI2_SFG | (2, 0) | PPLN or EO | Remap + confirm poling support |
| PHOTODET | (3, 0) | Custom | Discuss hybrid Ge/InGaAs integration |
| AWG_BODY | (6, 0) | WG | Same as waveguide layer |
| METAL1_HEATER | (10, 0) | HEATER | Remap |
| METAL2_PAD | (12, 0) | METAL | Remap |
| ALIGNMENT | (99, 0) | Per foundry spec | Use their alignment mark standard |
| LABEL | (100, 0) | -- | Remove before submission |

Remapping tool: Use KLayout's layer mapping or a gdsfactory post-processing script.

### 2.4 Contact Info File

```
PROJECT: N-Radix Ternary Optical Processor (Monolithic 9x9)
DESIGNER: Christopher Riner
EMAIL: chrisriner45@gmail.com
LOCATION: Chesapeake, VA, USA
PAPER 1: DOI 10.5281/zenodo.18437600 (Theory)
PAPER 2: DOI 10.5281/zenodo.18501296 (Architecture)
REPO: https://github.com/jackwayne234/-wavelength-ternary-optical-computer
```

---

## 3. Foundry-Specific Submission Instructions

### 3.1 HyperLight Corporation -- PRIMARY RECOMMENDATION

**Why HyperLight:** Native thin-film lithium niobate (TFLN) platform. This is the ONLY foundry that natively supports chi-2 nonlinear optics (PPLN periodic poling) -- the core of our SFG computation. No hybrid bonding or exotic post-processing needed.

| Item | Detail |
|------|--------|
| **Location** | Cambridge, MA, USA (domestic) |
| **Website** | https://www.hyperlightcorp.com |
| **Contact** | Foundry services inquiries via website contact form; also try info@hyperlightcorp.com |
| **Platform** | Thin-film LiNbO3 on insulator (LNOI / TFLN) |
| **Format** | GDSII (confirm OASIS acceptance) |
| **MPW schedule** | Custom -- contact for next available run |
| **Slot sizes** | Custom die sizes negotiated per project |
| **Expected lead time** | 3-6 months from tape-out to die return |
| **Cost range** | $10,000-$30,000 for MPW slot (estimate based on similar TFLN foundries) |
| **Key capabilities** | Periodic poling (PPLN), EO modulators, low-loss waveguides (<1 dB/cm), heater metallization |
| **What to confirm** | Photodetector integration (for 500-670 nm visible), minimum poling period (need 5.0 um), maximum poling period (need 13.3 um), die size limits (need 3.6 x 5.4 mm) |
| **Special requirements** | May require NDA before sharing PDK; ask about design review service |

**HyperLight submission checklist:**
- [ ] Contact via website/email with inquiry (use email template from Section 4.1)
- [ ] Request PDK and design rules
- [ ] Confirm PPLN poling capability at 5.0-13.3 um periods
- [ ] Confirm photodetector option for visible range (500-670 nm)
- [ ] Remap GDS layers to their PDK
- [ ] Submit design package
- [ ] Pay deposit
- [ ] Schedule design review call

### 3.2 AIM Photonics -- BACKUP (Domestic US)

**Why AIM:** US government-supported photonic foundry. Mature process, good for prototyping. Lower barrier for academic/independent researchers.

| Item | Detail |
|------|--------|
| **Location** | Albany, NY, USA |
| **Website** | https://www.aimphotonics.com |
| **Contact** | inquiry@aimphotonics.com or via SUNY Polytechnic |
| **Platform** | Silicon photonics + SiN options |
| **Format** | GDSII |
| **MPW schedule** | Regular quarterly runs (check website for calendar) |
| **Slot sizes** | 2.5x2.5 mm (small), 5x5 mm (medium), 10x10 mm (large) |
| **Expected lead time** | 4-6 months |
| **Cost range** | $3,000-$8,000 (small slot), $8,000-$20,000 (medium/large) |
| **Key capabilities** | Ge photodetectors (native), heaters, low-loss SiN waveguides |
| **Limitation** | NO native chi-2 nonlinearity. Would need hybrid LiNbO3 bonding or a fundamentally different approach to SFG. This is a major architectural concern. |
| **Best for** | Testing passive routing, waveguide loss, ring resonators, photodetectors -- all the components EXCEPT the SFG mixer. Could do a "passive routing validation" run. |

**AIM submission note:** AIM cannot do PPLN natively. Use AIM only for passive component characterization or as a fallback if HyperLight is unavailable. A partial submission (waveguide + ring + detector test structures only, no SFG) is still valuable.

### 3.3 Applied Nanotools -- BACKUP (Quick Turn)

**Why ANT:** High-resolution e-beam lithography. Fast turnaround for prototyping. Can work with customer-supplied wafers (including LNOI wafers).

| Item | Detail |
|------|--------|
| **Location** | Edmonton, Alberta, Canada |
| **Website** | https://www.appliednt.com |
| **Contact** | Via website contact form |
| **Platform** | E-beam patterning on customer wafers, or their own SiN/SiO2 platform |
| **Format** | GDSII |
| **MPW schedule** | Rolling -- submit anytime, batched monthly |
| **Slot sizes** | Flexible (e-beam, not mask-based) |
| **Expected lead time** | 2-4 weeks (fast!) |
| **Cost range** | $2,000-$10,000 depending on area and complexity |
| **Key capabilities** | Sub-100 nm features, high resolution, fast turnaround |
| **Limitation** | E-beam only (no PPLN poling). Would need to supply pre-poled LNOI wafer or skip SFG. |
| **Best for** | Quick passive waveguide/ring validation. Testing coupling structures. Prototyping before a full TFLN run. |

**ANT submission note:** If Christopher can source a blank LNOI wafer (~$200-500 from NANOLN or Partow Technologies), ANT can pattern the waveguides on it. The PPLN poling would still need a separate step (lab poling setup or a poling service).

### 3.4 Foundry Decision Matrix

| Criterion | HyperLight | AIM Photonics | Applied Nanotools |
|-----------|-----------|---------------|-------------------|
| Native PPLN / chi-2 | YES | NO | NO |
| Photodetectors | Hybrid (confirm) | Native Ge | NO (external) |
| Cost (MPW) | $10k-$30k | $3k-$20k | $2k-$10k |
| Lead time | 3-6 months | 4-6 months | 2-4 weeks |
| US domestic | YES | YES | Canada |
| Design review service | Ask | YES | Limited |
| Full chip validation possible | YES | Partial only | Partial only |

**Recommendation:** HyperLight is the only foundry that can fabricate the complete chip (SFG + passive routing + detectors) in one run. Start there. Use AIM or ANT for parallel passive-component test structures if budget allows.

---

## 4. Draft Inquiry Emails

### 4.1 Initial Inquiry Email -- HyperLight (PRIMARY)

```
Subject: MPW Inquiry — Monolithic Ternary Optical Processor on TFLN

Dear HyperLight Foundry Team,

I am an independent researcher developing a wavelength-division ternary
optical computing architecture. I am writing to inquire about fabricating
a proof-of-concept chip through your foundry services.

PROJECT SUMMARY:

The design is a monolithic 9x9 ternary systolic array processor on
thin-film lithium niobate (TFLN). It uses 6 collision-free wavelength
triplets (1000-1340 nm, 20 nm intra-triplet / 60 nm inter-triplet
spacing) to encode ternary logic states (-1, 0, +1) and performs
arithmetic via sum-frequency generation in periodically poled LiNbO3
(PPLN) waveguides. Each SFG pair uses an isolated (dedicated) PPLN
waveguide for clean operation. The architecture has been validated
through Meep FDTD simulation (36/36 SFG combinations PASS), SAX
circuit simulation (8/8 tests PASS), and analytical modeling, with
two publications on Zenodo.

KEY SPECIFICATIONS:

- Die size: 3.6 x 5.4 mm (monolithic, single substrate)
- Active area: 3.2 x 4.8 mm
- Array: 9x9 = 81 Processing Elements, 6 parallel WDM lanes each
- Waveguide: 0.5 um wide x 0.4 um etch, single-mode
- Critical feature: PPLN periodic poling (5.0-13.3 um periods, 20 um length)
- Architecture: Isolated lanes (dedicated PPLN waveguide per SFG pair)
- SFG output wavelengths: 500-670 nm (visible)
- Heater metallization: TiN for ring resonator tuning
- Bond pads: ~1100 pads (100x100 um, Ti/Au)
- Monte Carlo predicted yield: 99.82% (10,000 trials)
- Power margin: 18.70 dB

WAVELENGTH PLAN (6 triplets):

  T1: 1000/1020/1040 nm -> SFG 500-520 nm, QPM 5.0-5.7 um
  T2: 1060/1080/1100 nm -> SFG 530-550 nm, QPM 6.1-6.9 um
  T3: 1120/1140/1160 nm -> SFG 560-580 nm, QPM 7.4-8.3 um
  T4: 1180/1200/1220 nm -> SFG 590-610 nm, QPM 8.8-9.8 um
  T5: 1240/1260/1280 nm -> SFG 620-640 nm, QPM 10.3-11.5 um
  T6: 1300/1320/1340 nm -> SFG 650-670 nm, QPM 12.1-13.3 um

WHAT I NEED:

1. MPW slot for one die (~3.6 x 5.4 mm) plus PCM test structures
2. PPLN periodic poling at periods ranging 5.0-13.3 um
3. Photodetector integration (for 500-670 nm visible SFG outputs)
4. Heater metallization (TiN)
5. Bond pad metallization (Ti/Au)

QUESTIONS:

1. Does your platform support PPLN poling at 5.0-13.3 um periods for
   SFG at the wavelengths listed above?
2. What photodetector options are available for the visible range
   (500-670 nm)?
3. What is your current MPW schedule and pricing?
4. Do you offer design review before tape-out?
5. What PDK and design rules should I target?

PUBLICATIONS:

- Paper 1 (Theory): "Wavelength-Division Ternary Logic: Bypassing the
  Radix Economy Penalty in Optical Computing"
  DOI: 10.5281/zenodo.18437600

- Paper 2 (Architecture): "Wavelength-Division Ternary Computing II:
  The N-Radix Optical AI Accelerator"
  DOI: 10.5281/zenodo.18501296

I have a complete design package ready to share: GDS layout (gdsfactory),
layer mapping, DRC rules, simulation data, and test plan. The full
project repository is public:
https://github.com/jackwayne234/-wavelength-ternary-optical-computer

I am flexible on schedule and happy to adapt the design to your process.
Thank you for your time, and I look forward to discussing this further.

Best regards,

Christopher Riner
chrisriner45@gmail.com
Chesapeake, VA, USA
```

### 4.2 Initial Inquiry Email -- AIM Photonics (BACKUP)

```
Subject: MPW Inquiry — Photonic Test Structures for Ternary Optical Computing

Dear AIM Photonics Team,

I am an independent researcher investigating wavelength-division ternary
optical computing. I would like to fabricate passive photonic test
structures through your MPW program.

PROJECT:

The design is a ternary optical processor that uses 6 wavelength triplets
(1000-1340 nm range, 18 wavelengths total) to encode data and relies on
passive photonic components (waveguides, ring resonators, AWG
demultiplexers, photodetectors) for signal routing and readout.

I understand that your silicon/SiN platform does not support native
chi-2 nonlinear optics. However, I would like to validate the PASSIVE
portion of my design using your process:

COMPONENTS TO TEST:

1. Waveguide propagation loss at 1000-1340 nm (cutback structures)
2. Ring resonator Q-factor and extinction ratio (sweep of radii and gaps)
3. AWG demultiplexer (5-channel, visible range)
4. MMI couplers (1x2, 2x2 splitters)
5. Ge photodetector responsivity at 500-670 nm
6. Spot-size converters for edge coupling

SLOT SIZE NEEDED: 5x5 mm (small MPW slot) for test structures only

PUBLICATIONS:

- DOI: 10.5281/zenodo.18437600 (Theory)
- DOI: 10.5281/zenodo.18501296 (Architecture)

Would you be able to accommodate these test structures in your next
MPW run? What is the current schedule and pricing for a 5x5 mm slot?

Best regards,

Christopher Riner
chrisriner45@gmail.com
Chesapeake, VA, USA
```

### 4.3 Initial Inquiry Email -- Applied Nanotools (BACKUP)

```
Subject: E-Beam Patterning Inquiry — LNOI Waveguide Prototyping

Dear Applied Nanotools Team,

I am an independent researcher working on wavelength-division ternary
optical computing. I am interested in using your e-beam lithography
services to pattern waveguides on a customer-supplied LNOI wafer.

DESIGN:

- Waveguide width: 500 nm, etch depth: 400 nm
- Ring resonators: 5-25 um radius, 150 nm coupling gap
- Total pattern area: approximately 1.1 x 0.7 mm (one die)
- Additional PCM test structures: ~3 mm^2

I would supply a pre-made LNOI wafer (e.g., from NANOLN or Partow
Technologies). The pattern consists of ridge waveguides, ring resonators,
and grating/taper structures — standard photonic components.

QUESTIONS:

1. Can you pattern on customer-supplied LNOI wafers?
2. What is your minimum feature size and overlay accuracy?
3. What is the typical turnaround time and cost for this type of job?
4. Do you handle etching after patterning, or just the e-beam exposure?

PUBLICATIONS:

- DOI: 10.5281/zenodo.18437600

Thank you for your time.

Best regards,

Christopher Riner
chrisriner45@gmail.com
Chesapeake, VA, USA
```

### 4.4 Follow-Up Email -- "Ready to Submit" (For Any Foundry)

Send this once the foundry has responded to the initial inquiry, confirmed compatibility, and provided a PDK.

```
Subject: Re: MPW Inquiry — N-Radix Chip — Design Package Ready for Submission

Dear [Foundry Contact Name],

Thank you for the information about your process and MPW schedule.
I have completed the design package and am ready to submit.

ATTACHED FILES:

1. nradix_9x9_monolithic.gds — Chip layout (GDSII), generated with
   gdsfactory, layers remapped to your PDK per our discussion
2. layer_mapping_[FOUNDRY].csv — Layer correspondence table
3. DESIGN_SUMMARY.pdf — 2-page chip overview
4. DRC_REPORT.txt — Clean DRC run (zero violations)
5. test_plan_summary.pdf — Post-fab measurement plan
6. pcm_structures.pdf — Process control monitor descriptions

DESIGN HIGHLIGHTS:

- Die size: 3.6 x 5.4 mm
- 81 PEs (9x9 systolic array), 6 parallel WDM lanes each
- Isolated-lane architecture (dedicated PPLN per SFG pair)
- 6 wavelength triplets (1000-1340 nm), SFG outputs 500-670 nm
- PPLN QPM periods: 5.0-13.3 um
- 7 active layers + alignment marks
- Monte Carlo yield: 99.82% at 10,000 trials
- 6-lane IOC FDTD validation: 36/36 PASS
- Power margin: 18.70 dB
- All validation checks PASS

I am ready to:
- Pay the MPW deposit upon invoice
- Sign any required NDA or service agreement
- Schedule a design review call at your convenience

Please let me know the next steps and any modifications needed to
the design package.

Best regards,

Christopher Riner
chrisriner45@gmail.com
Chesapeake, VA, USA
```

---

## 5. Financial Planning

### 5.1 Phase 1 Budget: MVP Tape-Out + Basic Test

This is the minimum spend to get a chip fabricated and functionally tested.

| Category | Low Estimate | High Estimate | Notes |
|----------|-------------|---------------|-------|
| **MPW slot (HyperLight)** | $10,000 | $30,000 | Depends on die size, run timing, foundry pricing |
| **MPW slot (AIM, if parallel)** | $3,000 | $8,000 | Optional: passive test structures only |
| **Packaging (wire bonding + submount)** | $300 | $1,500 | University service = low; contract service = high |
| **Test bench (MVP tier)** | $1,955 | $4,016 | Bare-bones DIY = low; comfortable = high |
| **Fiber V-groove array** | $300 | $500 | Included in test bench, called out for lead time |
| **Shipping and handling** | $100 | $300 | Die return, consumables |
| **Contingency (20%)** | $2,531 | $6,863 | Murphy's law reserve |
| **PHASE 1 TOTAL** | **$15,186** | **$44,179** | |

**Realistic middle-ground estimate: ~$25,000**

This covers: one HyperLight MPW slot (~$15k), MVP test bench (~$4k), packaging (~$500), and contingency (~$5k).

### 5.2 Phase 2 Budget: Full Characterization

After first silicon proves the concept, expand testing.

| Category | Cost | Notes |
|----------|------|-------|
| Upgraded electronics (full ADC, DACs) | $2,260 | Multi-channel ADC/DAC for all 81 PEs |
| Upgraded optical (EOMs, OSA) | $5,550 | 617 MHz modulation, spectrum analysis |
| Upgraded thermal (precision TEC) | $1,230 | Laboratory-grade temp control |
| Full wire bonding (all 1100 pads) | $1,500 | Contract wire bonding service |
| Probe station (used) | $1,500 | Die-level testing before bonding |
| **PHASE 2 TOTAL** | **~$12,040** | |

### 5.3 Phase 3 Budget: Scale-Up

If 9x9 works, scale to 27x27 or 81x81.

| Category | Low Estimate | High Estimate | Notes |
|----------|-------------|---------------|-------|
| Larger MPW slot (10x10 mm) | $8,000 | $20,000 | 27x27 array + redundant test structures |
| Dedicated TFLN run (full reticle) | $50,000 | $200,000 | 81x81 array, full processor, everything |
| Professional packaging | $5,000 | $50,000 | Hermetic, fiber pigtailed, production quality |
| **PHASE 3 TOTAL** | **$63,000** | **$270,000** | |

### 5.4 Funding Sources to Pursue

Listed in order of accessibility for an independent researcher:

| Source | Amount Range | Timeline | Effort | Notes |
|--------|-------------|----------|--------|-------|
| **Self-fund (savings/credit)** | $1k-$25k | Immediate | Low | Fastest path. Phase 1 MVP is within reach. |
| **Crowdfunding (Experiment.com)** | $5k-$50k | 2-3 months | Medium | Science-specific crowdfunding. Published papers add credibility. |
| **AIM Photonics programs** | $5k-$25k | 3-6 months | Medium | AIM has programs specifically for small businesses and researchers. Check their "photonics incubator" offerings. |
| **NSF SBIR Phase I** | $275k | 6-12 months | High | Requires forming a small business entity (LLC). Covers Phase 1 + Phase 2 + salary. Highly competitive but published papers and validated design are strong. Topic: Photonic Computing. |
| **DOD SBIR (DARPA, Navy)** | $275k | 6-12 months | High | DARPA has had BAAs on optical computing. Navy (NSWC Dahlgren) is local to Chesapeake. |
| **Indie angel investor** | $25k-$100k | 1-6 months | Medium | Pitch deck: two published papers, validated design, clear roadmap. The "geometry is the program" security angle is investor-attractive. |
| **University collaboration** | Access | 1-3 months | Medium | Partner with a university photonics lab. They provide equipment/fab access; Christopher provides the design. Co-author on resulting paper. |
| **GoFundMe / general crowdfunding** | $1k-$10k | 1 month | Low | Less rigorous than Experiment.com but faster. Good for test bench funding. |
| **Patent licensing (future)** | Variable | 12+ months | High | File provisional patent first ($150). License to photonics companies once chips prove out. |

**Recommended first move:** Self-fund the inquiry emails (free) and Phase 1 test bench components that have long lead times (fiber array: $300). Simultaneously apply for AIM Photonics programs and start an Experiment.com campaign.

### 5.5 Payment Timeline

| Milestone | When | Amount | Payment Method |
|-----------|------|--------|----------------|
| Foundry inquiry | Day 0 | $0 | Free |
| PDK access / NDA | Week 1-2 | $0-$500 | NDA may require nominal fee |
| MPW deposit | Upon slot reservation | 50% of MPW cost (~$5k-$15k) | Wire transfer or credit card |
| MPW balance | Upon tape-out | Remaining 50% (~$5k-$15k) | Wire transfer |
| Long-lead test components | Day 0 | ~$500 | Credit card |
| Remaining test bench | Weeks 1-4 | ~$1,500-$3,500 | Credit card |
| Wire bonding service | When dies arrive | ~$300-$1,500 | University PO or credit card |
| Phase 2 upgrades | After first-light | ~$12k | As budget allows |

---

## 6. Parallel Actions Timeline

The moment someone says "yes" and money is available:

### Day 0 -- Launch Day

| Action | Who | Cost | Lead Time |
|--------|-----|------|-----------|
| Send "Ready to Submit" email to HyperLight (Section 4.4) | Christopher | $0 | Immediate |
| Pay MPW deposit (if invoiced) | Christopher | $5k-$15k | Same day |
| Order V-groove fiber array (OZ Optics, 2-ch, 127 um pitch, SMF-28, angle-polished) | Christopher | $300-$500 | **4-6 weeks** (long lead!) |
| Order custom PCB carrier boards (JLCPCB, 4-layer, design in KiCad) | Christopher | $50 | 1-2 weeks |
| Book wire bonding service (local university or SPT Roth) | Christopher | $0 (booking) | Schedule 3-4 months out |
| Regenerate final GDS from `monolithic_chip_9x9.py` | Christopher | $0 | 1 hour |
| Run KLayout DRC, confirm zero violations | Christopher | $0 | 1 hour |
| Remap GDS layers to foundry PDK | Christopher | $0 | 2-4 hours |

### Week 1-2 -- Test Bench Phase 1

| Action | Cost | Notes |
|--------|------|-------|
| Order laser sources (tunable or fixed DFB covering 1000-1340 nm range, 18 wavelengths across 6 triplets) | $1,150-$3,000 | Ships 1-3 days from Thorlabs; may need tunable source for full coverage |
| Order laser driver components (WLD3343 x3, butterfly sockets) | $300 | DIY path; or $4,500 for CLD1015 x3 |
| Order Red Pitaya STEMlab 125-14 (FPGA + ADC) | $300 | Ships ~1 week |
| Order MicroBlock 3-axis stage (Thorlabs MBT616D) | $350 | Ships 1-3 days |
| Order steel breadboard 12"x12" (Thorlabs MB1212) + posts | $250 | Ships 1-3 days |
| Order WDM combiner + fiber patch cables | $290 | Ships 1-3 days |
| Order TIA components (OPA857 eval + ICs for DIY channels) | $209 | Ships 1-2 weeks |

### Week 2-4 -- Test Bench Assembly

| Action | Notes |
|--------|-------|
| Design and order PCB carrier board in KiCad | If not done Day 0 |
| Assemble laser driver boards (if DIY path) | Requires soldering station |
| Assemble TIA board (5 channels for 1 PE) | OPA857 on custom PCB |
| Install Red Pitaya, configure SCPI interface | Follow test bench doc Section 6.7 |
| Write Phase 1 FPGA firmware (DC test: GPIO laser on/off, ADC read) | ~1 week development |
| Write PC test software (Python, test vectors, UART/SCPI interface) | ~1 week, can parallelize with firmware |
| Set up optical breadboard, mount stages | 2-4 hours |
| Verify all three lasers output correct wavelengths and power | 2-4 hours |

### Month 1-2 -- Software Development (While Waiting for Chips)

| Action | Notes |
|--------|-------|
| ~~Implement SAX circuit simulation (from CIRCUIT_SIMULATION_PLAN.md)~~ | COMPLETE -- 8/8 tests PASS |
| ~~Run all 8 circuit simulation test cases~~ | COMPLETE -- validates design computationally |
| Refine FPGA firmware: add automated test sweep, threshold calibration | Phase 2 firmware |
| Build PC test reporting (HTML reports, detector heatmaps) | Per TEST_BENCH_DESIGN.md Section 5.5 |
| Order thermal management components (TEC, thermistor, heatsink) | $224 |

### Month 3-6 -- Chip Fabrication (Foundry Working)

During this time, Christopher cannot affect foundry schedule but can:

| Action | Notes |
|--------|-------|
| Complete test bench assembly and dry-run with mock signals | Test the test bench before chips arrive |
| Write fiber alignment procedure (practice with spare fiber) | Most time-consuming step; practice helps |
| Engage packaging house (if professional wire bonding chosen) | Send die dimensions, pad map, bond count |
| Prepare lab space: stable table, anti-vibration, temperature control | Vibration kills fiber alignment |
| Build carry-chain FPGA firmware (Phase 3) if time allows | For testing addition, not just multiplication |
| Write up interim results for publication (simulation paper) | Keep momentum; circuit sim results ready to publish |

### Month 6+ -- Chips Arrive: Execute Test Plan

| Day | Action | Reference |
|-----|--------|-----------|
| Day 0 | Visual inspection under microscope | TAPEOUT_READINESS.md, Post-Fab Sequence step 1 |
| Day 0 | Die attach to AlN submount with thermal epoxy | PACKAGING_SPEC.md Section 9.1 |
| Day 1 | Wire bonding (MVP: 8 bonds for 1 PE + power/ground) | TEST_BENCH_DESIGN.md Section 6.4 |
| Day 1-2 | Fiber alignment to chip edge (most critical step) | TEST_BENCH_DESIGN.md Section 6.5 |
| Day 2 | Connect TIA, verify photodetector dark current | TEST_BENCH_DESIGN.md Section 6.6 |
| Day 2 | First light: inject 1550 nm, look for any detector response | |
| Day 2-3 | Run single-PE SFG verification (B+B -> 532 nm on DET_+2) | FUNCTIONAL_TEST_PLAN.md, Test Level 1 |
| Day 3 | Run full 9-case multiplication truth table on 1 PE | TEST_BENCH_DESIGN.md Section 4.4.3 |
| Day 3-4 | PCM characterization: waveguide loss, ring Q, SFG efficiency | MPW_RETICLE_PLAN.md Section 5 |
| Day 4-7 | Test Level 2: single row dot product (9 PEs) | FUNCTIONAL_TEST_PLAN.md |
| Week 2 | Test Level 3: full 9x9 matrix multiply | FUNCTIONAL_TEST_PLAN.md |
| Week 2-3 | Measure thermal sensitivity, compare to simulation | THERMAL_SENSITIVITY.md |
| Week 3-4 | Write up results, update validation docs | |
| Week 4 | **Announce results with real measured data** | |

---

## 7. Risk Register

### 7.1 Technical Risks

| # | Risk | Probability | Impact | Mitigation | Contingency |
|---|------|-------------|--------|------------|-------------|
| T1 | Foundry rejects design (DRC violations, unsupported features) | Medium | High | Run foundry-specific DRC before submission; request design review call; ask foundry to flag issues before tape-out | Fix violations and resubmit on next MPW run. Budget for 1 re-spin ($10k-$30k extra). |
| T2 | PPLN poling period not achievable at foundry | Low | Critical | HyperLight has native PPLN capability; confirm specific periods (5.0-13.3 um range across 6 triplets) in initial inquiry | If HyperLight cannot do it: (a) adjust wavelength triplets to match their available periods, (b) try a different foundry, or (c) use external poling on a blank LNOI wafer patterned by ANT. |
| T3 | Photodetectors not available at 500-670 nm | Medium | High | These are visible-range wavelengths; standard Ge detectors are optimized for 1300-1600 nm. Need Si photodiodes for visible. | If on-chip detectors are unavailable: (a) use external fiber-coupled Si photodiodes off-chip (adds packaging complexity but works), (b) redesign output for grating couplers to off-chip detectors. |
| T4 | First chips do not compute correctly | Medium | Medium | Monte Carlo shows 99.82% yield. Test PCM structures first to isolate component-level issues. | Follow FUNCTIONAL_TEST_PLAN.md diagnosis flowchart: (1) Check fiber coupling, (2) Verify waveguide transmission, (3) Test ring resonators individually, (4) Isolate single PE, (5) Check SFG output wavelength. Data from failed chips is still valuable for the next spin. |
| T5 | SFG conversion efficiency too low to detect | Low | High | Loss budget shows 18.70 dB margin. Monte Carlo includes SFG efficiency variation. | Increase laser input power (up to 100 mW). Use lock-in amplifier for weak-signal detection. Lengthen PPLN section in next spin. |
| T6 | Waveguide loss much higher than expected | Low | Medium | PCM cutback structures will measure actual loss. Design has 18.70 dB margin absorbing up to ~15 dB extra loss. | If loss is extreme (>10 dB/cm): indicates process issue. Work with foundry to diagnose. May need wider waveguides or different etch recipe. |
| T7 | Ring resonators off-resonance | Medium | Low | Heater tuning pads are included for thermal tuning. Monte Carlo shows ring tuning is the limiting factor (still 99.82% yield). | Apply voltage to heater pads via FPGA DACs. Sweep voltage to find resonance. If heater range insufficient: (a) increase heater length in next spin, (b) pre-heat chip to shift resonances globally. |
| T8 | Fiber alignment too difficult to achieve | Low | Medium | Test bench includes 3-axis stage with 0.5 um resolution. Edge couplers have inverse tapers for mode expansion. | (a) Switch to grating couplers (higher loss but easier alignment), (b) Hire a packaging house for professional alignment, (c) Use lensed fiber tips for larger mode field. |

### 7.2 Financial Risks

| # | Risk | Probability | Impact | Mitigation | Contingency |
|---|------|-------------|--------|------------|-------------|
| F1 | Funding falls through before tape-out | Medium | Critical | Pursue multiple funding sources simultaneously. Self-fund inquiry emails and long-lead components ($500-$1000) to maintain momentum. | Fall back to cheaper alternatives: (a) ANT e-beam run ($2k-$5k) for passive-only validation, (b) Partner with university that has LNOI fab capability (free/low cost), (c) Phase the project: fund test bench first, then MPW later. |
| F2 | MPW costs more than expected | Medium | Medium | Get firm quotes from foundry before committing. Our estimates ($10k-$30k) are based on comparable TFLN foundry pricing. | (a) Choose smaller die (single ALU: 0.35x0.25 mm costs much less), (b) Share MPW slot with another researcher, (c) Use AIM for passive structures at lower cost. |
| F3 | Test bench costs exceed budget | Low | Low | Four budget tiers documented ($1.8k to $16.5k). Start at bare-bones, upgrade as needed. | Bare-bones MVP ($1,955) proves the chip works. Everything else is optimization. An Arduino + salvaged SFP laser + op-amp TIA costs under $100 if absolutely desperate. |
| F4 | Second spin needed (first chips partially work) | Medium | High | Maximize learning from first spin: comprehensive PCM structures, multiple die variants. | Budget $10k-$30k for a second spin. Data from first spin informs design changes, so second spin has much higher confidence. This is normal in chip development -- most designs need 2-3 spins. |

### 7.3 Logistical Risks

| # | Risk | Probability | Impact | Mitigation | Contingency |
|---|------|-------------|--------|------------|-------------|
| L1 | HyperLight MPW schedule does not align | Medium | Medium | Contact them early. Long lead time is expected. Be ready to submit immediately when a slot opens. | (a) Wait for next run (3-6 month cycles), (b) Negotiate a dedicated run (more expensive), (c) Use ANT for quick passive validation while waiting. |
| L2 | V-groove fiber array delayed | Medium | Medium | Order Day 0. These are custom components with 4-6 week lead times. | (a) Use bare fiber cleaved flat (lower coupling efficiency but works for initial tests), (b) Order from multiple vendors, (c) Buy a stock 2-channel array if custom is delayed. |
| L3 | Wire bonding service unavailable locally | Low | Medium | Identify 2-3 options: local university, contract house (SPT Roth, Palomar). Book early. | (a) Use probe station for pad-level contact without bonding, (b) Ship die to a remote wire bonding service, (c) Use conductive epoxy micro-dots under microscope (crude but functional for MVP). |
| L4 | Dies damaged in shipping or handling | Low | High | Request that foundry ship in gel-pak trays. Handle only with vacuum tweezers. Store in clean, dry environment. | (a) Order more than one die (most MPW runs yield multiple copies), (b) Request foundry to hold backup dies, (c) Inspect under microscope immediately upon receipt. |
| L5 | Timeline slips past 6 months | Medium | Low | The critical path is: funding -> foundry submission -> fab time -> die return -> test. Fab time is fixed (~3-6 months). Everything else can be parallelized. | Accept the timeline. Chip development is inherently slow. Use the waiting time productively (software, simulation, test bench, publications, grant applications). |

### 7.4 Critical Path Analysis

The critical path determines the minimum time from "go" to "first measured data":

```
                CRITICAL PATH (minimum elapsed time)
                ======================================

Day 0           Fund secured
  |
  v
Day 1-3         GDS finalized, DRC clean, layers remapped, package submitted
  |
  v
Week 1-2        Foundry acknowledges, design review, slot confirmed
  |
  v
Month 1         Tape-out (foundry begins fabrication)
  |
  |  <<< PARALLEL: build test bench, write firmware/software >>>
  |
  v
Month 3-6       Dies returned
  |
  v
Month 3-6 +1w   Wire bonding, die attach, fiber alignment
  |
  v
Month 3-6 +2w   FIRST LIGHT: SFG verification on one PE
  |
  v
Month 3-6 +4w   Full 9x9 validation complete

TOTAL: 4-7 months from funding to measured results
```

**What is NOT on the critical path (can be done in parallel):**
- Test bench assembly (weeks 1-4)
- FPGA firmware development (weeks 2-6)
- PC software development (weeks 2-6)
- Circuit simulation (SAX) -- DONE
- Publication of simulation results
- Grant applications for Phase 2

**What IS on the critical path:**
1. Funding (blocks everything)
2. Foundry submission and acceptance (blocks fabrication)
3. Fabrication (3-6 months, cannot be shortened)
4. Wire bonding (blocks testing, but only takes 1-2 days)
5. Fiber alignment (blocks testing, takes 2-8 hours first time)

---

## Appendix A: Quick Reference Card

Print this card. Tape it to the wall.

```
================================================================
        N-RADIX 9x9 MONOLITHIC CHIP -- QUICK REFERENCE
================================================================

CHIP: 3.6 x 5.4 mm, 81 PEs, X-cut LiNbO3 (TFLN)
GDS:  python architecture/monolithic_chip_9x9.py

ARCHITECTURE: Isolated-lane (dedicated PPLN per SFG pair)

WAVELENGTHS (6 collision-free triplets, 20nm intra / 60nm inter):
  T1: 1000/1020/1040 nm -> SFG 500-520 nm, QPM 5.0-5.7 um
  T2: 1060/1080/1100 nm -> SFG 530-550 nm, QPM 6.1-6.9 um
  T3: 1120/1140/1160 nm -> SFG 560-580 nm, QPM 7.4-8.3 um
  T4: 1180/1200/1220 nm -> SFG 590-610 nm, QPM 8.8-9.8 um
  T5: 1240/1260/1280 nm -> SFG 620-640 nm, QPM 10.3-11.5 um
  T6: 1300/1320/1340 nm -> SFG 650-670 nm, QPM 12.1-13.3 um

PE TYPES (all physically add; IOC determines meaning):
  ADD/SUB: straight ternary addition/subtraction
  MUL/DIV: log-domain addition = multiplication

VALIDATION:
  Path match:     PASS (0.000 ps spread)
  Loss budget:    PASS (18.70 dB margin)
  Timing skew:    PASS (0.0000% of clock)
  Collision-free: PASS (24.1 nm min spacing)
  Monte Carlo:    PASS (99.82% yield, 10,000 trials)
  Thermal:        PASS (30 C passive window)
  Circuit sim:    PASS (8/8 tests, SAX)
  6-lane IOC:     PASS (36/36 SFG pairs, isolated-lane FDTD)

MATERIAL MODEL: Sellmeier (Zelmon et al. 1997)
  n^2 = 1 + B1*L^2/(L^2-C1^2) + B2*L^2/(L^2-C2^2)
  FDTD: single-pole Lorentzian, f0=3.5 (below stability boundary)

PAPERS:
  Theory:   DOI 10.5281/zenodo.18437600
  Arch:     DOI 10.5281/zenodo.18501296

CONTACT:
  Christopher Riner
  chrisriner45@gmail.com
  Chesapeake, VA

FOUNDRY TARGET: HyperLight (TFLN, native PPLN)
ESTIMATED COST: ~$25,000 (Phase 1 MVP total)
ESTIMATED TIME: 4-7 months to measured results
================================================================
```

---

## Appendix B: Document Cross-Reference

Every document in the tape-out package and where to find it:

| Document | Path | Status |
|----------|------|--------|
| This submission package | `docs/FOUNDRY_SUBMISSION_PACKAGE.md` | Current document |
| Tape-out readiness checklist | `docs/TAPEOUT_READINESS.md` | Master tracking |
| MPW reticle plan | `docs/MPW_RETICLE_PLAN.md` | Complete |
| Foundry questions | `docs/FOUNDRY_QUESTIONS.md` | Complete |
| Layer mapping | `docs/LAYER_MAPPING.md` | Complete |
| DRC rules | `docs/DRC_RULES.md` | Complete |
| Packaging specification | `docs/PACKAGING_SPEC.md` | Complete |
| Chip interface specification | `docs/CHIP_INTERFACE.md` | Complete |
| Test bench design + BOM | `docs/TEST_BENCH_DESIGN.md` | Complete |
| Functional test plan | `docs/FUNCTIONAL_TEST_PLAN.md` | Complete |
| Monte Carlo analysis | `docs/MONTE_CARLO_ANALYSIS.md` | Complete |
| Thermal sensitivity analysis | `docs/THERMAL_SENSITIVITY.md` | Complete |
| Circuit simulation plan | `docs/CIRCUIT_SIMULATION_PLAN.md` | COMPLETE -- 8/8 tests PASS |
| 9x9 validation report | `docs/MONOLITHIC_9x9_VALIDATION.md` | Complete |
| GDS generator script | `architecture/monolithic_chip_9x9.py` | Functional |
| Existing foundry email template | `CPU_Phases/Phase3_Chip_Simulation/foundry_inquiry_email.txt` | Superseded by Section 4 of this doc |

---

## Appendix C: Checklist Summary (Print and Check)

```
PRE-SUBMISSION (before contacting foundry):
[ ] Read this entire document
[ ] Regenerate GDS: python architecture/monolithic_chip_9x9.py
[ ] Run KLayout DRC: zero violations
[ ] Review layer mapping for target foundry
[ ] Confirm payment method is ready

INQUIRY PHASE:
[ ] Send inquiry email to HyperLight (Section 4.1)
[ ] Send inquiry email to AIM Photonics (Section 4.2, if parallel)
[ ] Send inquiry email to Applied Nanotools (Section 4.3, if parallel)
[ ] Receive foundry response; download PDK
[ ] Remap GDS layers to foundry PDK
[ ] Re-run DRC with foundry rules

SUBMISSION PHASE:
[ ] Assemble ZIP package (Section 2.1, 7 files)
[ ] Send "Ready to Submit" email (Section 4.4)
[ ] Pay MPW deposit

PARALLEL -- ORDER IMMEDIATELY:
[ ] V-groove fiber array (4-6 week lead time!)
[ ] Custom PCB carrier boards (1-2 week lead time)
[ ] Book wire bonding service (schedule 3-4 months out)

PARALLEL -- ORDER WITHIN 2 WEEKS:
[ ] Laser sources (3x DFB/FP)
[ ] Laser driver components (or CLD1015 units)
[ ] Red Pitaya STEMlab 125-14
[ ] Alignment stage + breadboard
[ ] WDM combiner + fiber patch cables
[ ] TIA components

WAITING FOR CHIPS -- BUILD AND PREPARE:
[ ] Assemble test bench on optical breadboard
[ ] Verify all lasers output correctly
[ ] Write FPGA firmware (DC test, Phase 1)
[ ] Write PC test software (Python)
[x] Implement SAX circuit simulation
[x] Run circuit simulation test cases (8/8 PASS)
[ ] Practice fiber alignment with spare fiber
[ ] Prepare lab space (stable, low vibration)

CHIPS ARRIVE:
[ ] Visual inspection under microscope
[ ] Die attach to AlN submount
[ ] Wire bonding (MVP: 8 bonds)
[ ] Fiber alignment (2-8 hours)
[ ] TIA connection and dark current check
[ ] First light: any detector response?
[ ] Single PE SFG verification
[ ] Full 9-case truth table on 1 PE
[ ] PCM characterization
[ ] Row dot product test (9 PEs)
[ ] Full 9x9 matrix multiply test
[ ] Thermal sweep test
[ ] Document results
[ ] Announce with real measured data
```

---

*This document is the turnkey foundry submission package for the N-Radix 9x9 Monolithic Ternary Optical Processor. It is designed to be complete, actionable, and ready to execute the moment funding is secured. Every email is pre-written. Every cost is estimated. Every timeline is mapped. Print it. Check the boxes. Ship the chip.*

---

**Document prepared:** February 17, 2026 (updated February 18, 2026)
**Author:** Christopher Riner (with Claude)
**Project:** N-Radix Wavelength-Division Ternary Optical Computer
**Repository:** https://github.com/jackwayne234/-wavelength-ternary-optical-computer
