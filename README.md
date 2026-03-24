# Wavelength-Ternary Hybrid SFG Optical Computer

> **A hybrid optical-electronic matrix multiplier using sum-frequency generation (SFG) and ternary logic on lithium niobate.**

---

## What This Is

A 3×3 optical matrix multiplier chip designed on LNOI (thin-film lithium niobate on insulator). The multiply step is photonic — two light signals mix via SFG in periodically poled waveguides. The accumulate step is electronic — photodetectors convert products to voltages, column adders produce dot products.

### Why It Matters

- **No heat from multiply** — SFG is a passive nonlinear process, milliwatts vs watts
- **~50% less site power** — data centers spend half their power budget on cooling matrix multiplier ASICs. Remove the heat source, remove the cooling
- **Same throughput** — memory bandwidth is the bottleneck for both optical and electronic accelerators. The optical multiply doesn't speed things up, but it eliminates the power and thermal cost of the compute step

---

## Architecture

Hand-designed, no inverse-design optimization needed. The physics dictates the layout.

### Signal Flow

```
3 RGB Lasers (always on)
    │
    ├──► Vertical distribution buses (1 per color)
    │
    ├──► Per-row: 3 color gates (MZI switches) → WDM merge → row input channel
    │
    ▼
3×3 Grid of SFG Chambers ◄── 2 Weight Buses (+1 @ 1070nm, -1 @ 1040nm)
    │                              │
    │                         2 weight gates per chamber (MZI)
    │
    ▼
9 Chambers × 6 SFG elements each = 54 PPLN sections
    │
    ▼
54 Photodetectors → 3 Column Summers → 3 Dot Products
```

### Key Numbers

| Parameter | Value |
|-----------|-------|
| Chip size | 3.2 × 2.7 mm |
| Platform | LNOI (lithium niobate on insulator) |
| Input wavelengths | R=1560nm, G=1540nm, B=1520nm |
| Weight wavelengths | +1=1070nm, -1=1040nm |
| SFG output range | 617-635 nm (visible, Si-detectable) |
| Min spectral separation | 3.22 nm (standard filters work) |
| Poling periods | 12.55-13.55 μm |
| Waveguide width | 800 nm (single-mode) |
| Bend radius | ≥50 μm |
| Total SFG elements | 54 (6 per chamber × 9 chambers) |
| Total gates | 27 (9 input + 18 weight) |
| Gate type | Electro-optic MZI (native LN EO effect) |

### How SFG Selection Works

Each SFG chamber contains 6 individually-tuned PPLN waveguides — one for every possible (color × weight) pair. When an input wavelength and a weight wavelength enter the chamber simultaneously, **only the SFG element tuned to that specific frequency pair** produces output. The others are phase-mismatched and suppressed. No switching logic needed inside the chamber — the physics does the selection.

### Ternary Operation

Each SFG chamber can produce:
- `input × (+1)` — open the +1 weight gate
- `input × (-1)` — open the -1 weight gate
- `input × 0` — both gates closed (no weight enters)

---

## Repository Structure

```
├── drawings/                    # Hand-drawn architecture reference
│   └── IMG_0210_hybrid_chamber_architecture.jpg
│
├── docs/
│   ├── HYBRID_ARCHITECTURE.md   # Architecture design document
│   ├── MEEP_MPI_SETUP.md        # Meep parallel simulation fix
│   └── learn/
│       └── hybrid_matrix_multiply.html  # Interactive learning page
│
├── gds/
│   ├── generate_hybrid_chip.py  # Schematic-level GDS generator
│   ├── generate_fab_chip.py     # Fab-level GDS generator (LNOI)
│   ├── wavelength_design.py     # Wavelength selection + poling period calculator
│   ├── render_gds.py            # Schematic → HTML viewer
│   ├── render_fab.py            # Fab → HTML viewer
│   ├── hybrid_chip_3x3.gds     # Schematic GDS
│   ├── hybrid_chip_fab.gds     # Fab-level GDS (open with KLayout)
│   ├── viewer.html              # Schematic viewer (open in browser)
│   └── viewer_fab.html          # Fab viewer (open in browser)
│
├── LICENSE                      # MIT (code)
├── LICENSES/                    # CC BY 4.0 (docs), CERN OHL (hardware)
└── requirements.txt
```

---

## Current Status (March 2026)

### Done
- [x] Architecture designed by hand from first principles
- [x] Schematic GDS — correct 3×3 layout with per-row RGB gating
- [x] Wavelength selection — all 6 SFG outputs separated by ≥3.2 nm
- [x] Poling period calculations — all within standard PPLN fab range
- [x] Fab-level GDS — real LNOI component geometries (MZIs, PPLN, detectors, edge couplers)
- [x] KLayout installed for proper GDS inspection

### Next Steps
- [ ] Fix weight bus → SFG routing in fab GDS (weight MZI outputs need to connect through to SFG elements)
- [ ] Add WDM couplers at SFG entry (combine input + weight light before PPLN section)
- [ ] Output demux design (AWG or ring filters to separate 6 SFG wavelengths per chamber)
- [ ] Bond pad routing (metal traces from MZI electrodes and detectors to pads)
- [ ] DRC check against target foundry rules
- [ ] Simulation: SFG conversion efficiency vs PPLN length
- [ ] Simulation: MZI extinction ratio requirements
- [ ] Column summer circuit design (electronic)

### Future (when SFG tech matures)
- [ ] Consolidate 6 SFGs per chamber → 1 broadband SFG (6× density improvement)
- [ ] 6-triplet WDM: 6 chips worth of compute on 1 chip

---

## Quick Start

```bash
# Install dependencies
pip install gdstk

# Generate schematic GDS
cd gds/
python3 generate_hybrid_chip.py

# Generate fab-level GDS
python3 generate_fab_chip.py

# View in browser
python3 render_gds.py && open viewer.html
python3 render_fab.py && open viewer_fab.html

# View in KLayout (recommended for fab GDS)
open -a /Applications/KLayout/klayout.app hybrid_chip_fab.gds

# Run wavelength design calculations
python3 wavelength_design.py
```

---

## Citation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18437600.svg)](https://doi.org/10.5281/zenodo.18437600)

```bibtex
@misc{riner2026wavelength,
  author = {Riner, Christopher},
  title = {Wavelength-Division Ternary Logic: Bypassing the Radix Economy Penalty in Optical Computing},
  year = {2026},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.18437600}
}
```

---

## License

| Component | License |
|-----------|---------|
| Software | MIT |
| Documentation | CC BY 4.0 |
| Hardware Designs | CERN OHL |

**Author:** Christopher Riner — Active Duty U.S. Navy
**GitHub:** [jackwayne234](https://github.com/jackwayne234)
