# N-Radix: Wavelength-Division Ternary Optical Accelerator

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18437600.svg)](https://doi.org/10.5281/zenodo.18437600)
[![License: Code - MIT](https://img.shields.io/badge/License-Code%20MIT-blue.svg)](LICENSE)
[![License: Docs - CC BY 4.0](https://img.shields.io/badge/License-Docs%20CC%20BY%204.0-lightgrey.svg)](LICENSES/CC-BY-4.0.txt)
[![License: Hardware - CERN OHL](https://img.shields.io/badge/License-Hardware%20CERN%20OHL-orange.svg)](LICENSES/CERN-OHL.txt)

> **An Optical AI Accelerator achieving ~59x NVIDIA B200 performance**
>
> Using wavelength-division ternary logic for massively parallel matrix operations at a fraction of the power.

---

## What Is This?

**N-Radix** is an optical AI accelerator optimized for parallel matrix operations - the same workloads that dominate AI training and inference. Instead of electrons through transistors, we use photons through waveguides.

### Performance vs NVIDIA

| Mode | Performance | vs B200 (2.5 PFLOPS) | vs H100 (~2 PFLOPS) |
|------|-------------|----------------------|---------------------|
| **Base** | 82 PFLOPS/chip | 33x | 41x |
| **Matrix multiply** | ~148 PFLOPS/chip | **~59x** | ~74x |
| **Pure ADD** | 738 PFLOPS/chip | 295x | 369x |

*Matrix multiply is the realistic AI workload comparison. Pure ADD applies to accumulation-heavy operations.*

---

## Repository Structure

```
Optical_computing/
├── NRadix_Accelerator/     # <-- MAIN PROJECT: Optical AI accelerator
│   ├── driver/             # NR-IOC driver (C + Python bindings)
│   ├── architecture/       # Systolic array designs (27x27, 81x81)
│   ├── components/         # Photonic component simulations
│   ├── simulations/        # WDM validation tests (Meep FDTD)
│   ├── gds/                # Chip layouts and mask files
│   ├── docs/               # Interface specs, DRC rules, packaging
│   └── papers/             # Academic papers
│
├── CPU_Phases/             # Legacy: General-purpose CPU prototypes
│   ├── Phase1_Prototype/   # Visible light RGB demonstrator
│   ├── Phase2_Fiber_Benchtop/  # 10GHz fiber-optic version
│   ├── Phase3_Chip_Simulation/ # Silicon photonics design
│   ├── Phase4_DIY_Fab/     # Contingency DIY fab approach
│   └── cpu_architecture/   # Round Table multi-CPU design
│
├── Research/               # Shared research, data, papers
├── docs/                   # Project documentation, session notes
└── tools/                  # Research search tool, utilities
```

---

## N-Radix Accelerator

**All active development is in [`NRadix_Accelerator/`](NRadix_Accelerator/)**

### Key Specifications

| Spec | Value |
|------|-------|
| **Array Sizes** | 27x27 (729 PEs), 81x81 (6,561 PEs) |
| **Clock** | 617 MHz Kerr self-pulsing |
| **WDM Channels** | 6 triplets (18 wavelengths) |
| **Logic States** | Ternary (-1, 0, +1) via wavelength |

### Architecture Overview

N-Radix uses a **systolic array** design - the same architecture as Google TPUs and NVIDIA tensor cores. Data flows through a grid of Processing Elements (PEs), each performing multiply-accumulate operations.

```
        Weight inputs (stationary in PEs)
                    |
        +---------------------------------+
        |   PE-PE-PE-PE-PE-PE-PE-PE-PE    |
   A -> |   PE-PE-PE-PE-PE-PE-PE-PE-PE -> C
   c    |   PE-PE-PE-PE-PE-PE-PE-PE-PE    |
   t    |   PE-PE-PE-PE-PE-PE-PE-PE-PE    |
   i    |   PE-PE-PE-PE-PE-PE-PE-PE-PE    |
   v    |            |                    |
   a    |    Accumulated outputs          |
   t    +---------------------------------+
   i
   o
   n
   s
```

**The key insight:** Wavelength-division multiplexing runs 6 independent computations through the same physical hardware simultaneously. This is mature telecom technology repurposed for compute.

### Validation Status

| Test | Status |
|------|--------|
| 3x3 WDM array | PASSED |
| 9x9 WDM array | PASSED |
| 27x27 WDM array (2.4% clock skew) | PASSED |
| 81x81 WDM array | Queued |

### Key Documentation

| Doc | Description |
|-----|-------------|
| [Chip Interface](NRadix_Accelerator/docs/CHIP_INTERFACE.md) | How to connect to the chip |
| [Driver Spec](NRadix_Accelerator/docs/DRIVER_SPEC.md) | NR-IOC driver details |
| [DRC Rules](NRadix_Accelerator/docs/DRC_RULES.md) | Design rules for fabrication |
| [Packaging](NRadix_Accelerator/docs/PACKAGING_SPEC.md) | Fiber coupling, bond pads |
| [Layer Mapping](NRadix_Accelerator/docs/LAYER_MAPPING.md) | GDS layer definitions |
| [MPW Plan](NRadix_Accelerator/docs/MPW_RETICLE_PLAN.md) | Multi-project wafer strategy |

### Quick Start

```bash
# Run WDM validation simulation
cd NRadix_Accelerator/simulations/
export OMP_NUM_THREADS=12
python wdm_27x27_array_test.py

# Use the Python driver/simulator
cd NRadix_Accelerator/driver/python/
python -c "from nradix import NRadixSimulator; sim = NRadixSimulator(27)"
```

---

## The Core Insight

Ternary (base-3) logic is mathematically optimal for computing (closest to Euler's number *e*), but electronic implementations require ~40x more transistors per trit. **We solve this by using light wavelengths instead of voltage levels:**

| Trit Value | Wavelength | Band |
|------------|------------|------|
| **-1** | 1550 nm | Telecom C-band |
| **0** | 1310 nm | O-band |
| **+1** | 1064 nm | Near-IR |

Unlike transistors, wavelength differentiation is independent of radix. This unlocks ternary's 1.58x information density advantage while leveraging photonics' speed, parallelism, and low power.

**Read the Paper:** [Zenodo Publication](https://doi.org/10.5281/zenodo.18437600)

---

## CPU Phases (Legacy)

The [`CPU_Phases/`](CPU_Phases/) directory contains earlier prototyping work and an alternative general-purpose CPU architecture. This work is preserved but not the current focus.

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Visible light RGB prototype (24"x24") | Parts ordered |
| Phase 2 | 10GHz fiber benchtop | Planning |
| Phase 3 | Silicon photonics chip | Seeking funding |
| Phase 4 | DIY fab (contingency) | On demand |

The CPU approach uses a **Round Table** topology - multiple CPUs arranged equidistant from a central 617 MHz Kerr clock to eliminate clock skew. This is relevant for general-purpose computing workloads but not the primary focus of N-Radix, which targets AI/matrix operations.

---

## Contributing

This is an open research project. Contributions welcome:

- **Hardware**: Optical alignment, component testing
- **Software**: Driver development, simulation optimization
- **Theory**: Architecture analysis, encoding schemes
- **Documentation**: Technical writing, diagrams

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Citation

### Paper (Theory)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18437600.svg)](https://doi.org/10.5281/zenodo.18437600)

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

### Software (Implementation)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18450479.svg)](https://doi.org/10.5281/zenodo.18450479)

```bibtex
@software{riner2026wavelengthsoftware,
  author = {Riner, Christopher},
  title = {Wavelength-Division Ternary Optical Computer},
  year = {2026},
  publisher = {Zenodo},
  version = {v1.0.1},
  doi = {10.5281/zenodo.18450479},
  url = {https://doi.org/10.5281/zenodo.18450479}
}
```

---

## License

| Component | License |
|-----------|---------|
| Software Code | MIT License |
| Documentation | CC BY 4.0 |
| Hardware Designs | CERN OHL |

---

**Author:** Christopher Riner
**Contact:** chrisriner45@gmail.com
**Location:** Chesapeake, VA, USA
