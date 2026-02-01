# Wavelength-Division Ternary Optical Computer

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18437600.svg)](https://doi.org/10.5281/zenodo.18437600)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Status: Active](https://img.shields.io/badge/Status-Active%20Development-green.svg)]()

> **Bypassing the Radix Economy Penalty in Optical Computing**

This repository contains the research, simulation, and hardware implementation files for a novel **Ternary (Base-3) Optical Computer** that uses wavelength-division multiplexing to bypass the fundamental limitations of electronic ternary logic.

## 🎯 The Big Idea

Ternary (base-3) logic is mathematically optimal for computing (closest to Euler's number *e*), but electronic implementations require 40× more transistors per trit than bits. **We solve this by using light colors instead of voltage levels:**

- **Red** = -1
- **Green** = 0  
- **Blue** = +1

Unlike transistors, where cost scales with the number of states, wavelength differentiation is **independent of radix**. This unlocks the full 1.58× information density advantage of ternary logic while leveraging photonics' speed, parallelism, and low power.

📄 **Read the Paper**: [Zenodo Publication](https://doi.org/10.5281/zenodo.18437600)

## 📂 Repository Structure

### [Phase1_Prototype/](Phase1_Prototype/) - "Macro" Demonstrator
**Status:** Parts Ordered / Construction In Progress

A 24"×24" visible-light prototype using Red/Green/Blue lasers and 3D-printed optics to prove the architecture.

- **Firmware**: ESP32 controller with ternary logic implementation ([`ternary_logic_controller.ino`](Phase1_Prototype/firmware/ternary_logic_controller/ternary_logic_controller.ino))
- **Hardware**: Complete BOM, 3D print files (SCAD), assembly instructions
- **Demo**: Blue + Red = Purple = 0 (1 + -1 = 0)

**[→ Start Building](Phase1_Prototype/NEXT_STEPS.md)**

### [Phase2_Fiber_Benchtop/](Phase2_Fiber_Benchtop/) - "Speed" Demonstrator  
**Status:** Procurement

10GHz fiber-optic benchtop using standard ITU C-Band telecom equipment to prove the architecture scales to real-world speeds.

- **Firmware**: SFP+ laser tuning scripts ([`sfp_tuner.py`](Phase2_Fiber_Benchtop/firmware/sfp_tuner.py))
- **Target**: Demonstrate 1.58 bits/symbol (vs 1 bit for binary)

### [Phase3_Chip_Simulation/](Phase3_Chip_Simulation/) - Silicon Photonics
**Status:** Design & Partnership Development

Miniaturizing the design onto a Lithium Niobate (LiNbO3) photonic integrated circuit.

- **Goal**: GDSII layouts for foundry fabrication
- **Target**: MPW (Multi-Project Wafer) run

### [Phase4_DIY_Fab/](Phase4_DIY_Fab/) - Contingency Plan
**Status:** Planning

If commercial fabrication partnerships fail, we'll build a garage-scale semiconductor fab using DIY photolithography.

- **Resolution**: 5-10μm (sufficient for proof-of-concept)
- **Safety**: Full ORM assessment included
- **Budget**: $800-3000

### [Research/](Research/) - Theory & Simulations

- **[`papers/`](Research/papers/)**: Published paper, LaTeX source, figures, supplementary materials
- **[`programs/`](Research/programs/)**: 12 Python/Meep FDTD simulation scripts
  - Ring resonator selectors
  - SFG mixers  
  - Y-junctions
  - Photodetectors
  - Universal logic gates

## 🚀 Quick Start

### Build the Phase 1 Prototype
```bash
# 1. Review the BOM and order parts
cat Phase1_Prototype/hardware/BOM_24x24_Prototype.md

# 2. 3D print the optical components
# Files: Phase1_Prototype/hardware/scad/*.scad

# 3. Flash the firmware
# Open: Phase1_Prototype/firmware/ternary_logic_controller/ternary_logic_controller.ino
# Upload to ESP32

# 4. Run your first calculation
# Serial command: ADD 1 -1
# Result: Purple light = 0
```

### Run Simulations
```bash
cd Research/programs/
python3 optical_selector.py    # Ring resonator simulation
python3 sfg_mixer.py           # Sum-frequency generation mixer
python3 test_photonic_logic.py # Logic verification
```

### Phase 2 Fiber Benchtop
```bash
python3 Phase2_Fiber_Benchtop/firmware/sfp_tuner.py
```

## 📊 Project Status

| Phase | Component | Status | Timeline |
|-------|-----------|--------|----------|
| 1 | Visible Light Prototype | 🟡 Building | 1 month |
| 2 | Fiber Benchtop (10GHz) | 🔵 Planning | 2 months |
| 3 | Silicon Chip | ⚪ Seeking Funding | TBD |
| 4 | DIY Fab (Backup) | ⚪ Contingency | On Demand |

## 🎥 Demonstrations & Outreach

- **YouTube**: Build videos and logic demonstrations (coming soon)
- **Hackaday.io**: Project log and community updates
- **Zenodo**: Open-access publication and data

## 🤝 Contributing

This is an open research project. Contributions welcome:

- **Hardware**: 3D print improvements, optical alignment tips
- **Software**: Simulation optimizations, firmware features
- **Theory**: Mathematical analysis, alternative architectures
- **Documentation**: Better explanations, translations

## 📜 Citation

If you use this work, please cite:

```bibtex
@misc{riner2026wavelength,
  author = {Riner, Christopher},
  title = {Wavelength-Division Ternary Logic: Bypassing the Radix Economy Penalty in Optical Computing},
  year = {2026},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.18437600},
  url = {https://doi.org/10.5281/zenodo.18437600}
}
```

## 📄 License

- **Paper & Documentation**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Code**: MIT License (see individual files)
- **Hardware Designs**: CERN Open Hardware License

## 🙏 Acknowledgments

- **Inspiration**: The Setun computer (Moscow State University, 1958)
- **Therapist**: Who asked "why don't you start now?"
- **20 years US Navy**: Discipline, ORM, and "make it work" mentality

---

**Author**: Christopher Riner  
**Contact**: chrisriner@gmail.com  
**Location**: Chesapeake, VA, USA  
**Status**: Active duty Navy, retiring soon to build optical computers full-time

> *"The best time to plant a tree was 20 years ago. The second best time is now."*
