# File Organization Plan: TPU vs CPU Separation

**Date:** February 5, 2026
**Status:** PROPOSED - Awaiting Review

---

## Overview

This document proposes reorganizing the repository to clearly separate:
- **N-Radix Accelerator (TPU)** - The optical AI accelerator project
- **CPU Phases** - The legacy experimental optical CPU project (Phases 1-4)

---

## Proposed New Structure

```
/home/jackwayne/Desktop/Optical_computing/
│
├── NRadix_Accelerator/              ← NEW: All TPU/accelerator work
│   ├── driver/                      ← from nradix-driver/
│   │   ├── python/nradix.py
│   │   ├── src/nrioc.c, encoding.c
│   │   ├── include/nrioc.h
│   │   └── tests/
│   │
│   ├── architecture/                ← from Research/programs/nradix_architecture/
│   │   ├── README.md
│   │   ├── optical_systolic_array.py
│   │   ├── c_band_wdm_systolic.py
│   │   ├── home_ai/
│   │   └── supercomputer/
│   │
│   ├── components/                  ← from Research/programs/shared/
│   │   ├── photonics/              (optical_selector.py, sfg_mixer.py, etc.)
│   │   ├── nrioc_module.py
│   │   └── optical_backplane.py
│   │
│   ├── simulations/                 ← from Research/programs/simulations/
│   │   ├── wdm_3x3_array_test.py
│   │   ├── wdm_9x9_array_test.py
│   │   ├── wdm_27x27_array_test.py
│   │   ├── wdm_81x81_array_test.py
│   │   └── wdm_waveguide_test.py
│   │
│   ├── gds/                         ← from Research/data/gds/
│   │   ├── optical_systolic_27x27.gds
│   │   ├── optical_systolic_81x81.gds
│   │   └── masks/
│   │
│   ├── docs/                        ← N-Radix specific docs
│   │   ├── CHIP_INTERFACE.md
│   │   ├── DRIVER_SPEC.md
│   │   ├── DRC_RULES.md
│   │   ├── LAYER_MAPPING.md
│   │   ├── PACKAGING_SPEC.md
│   │   └── MPW_RETICLE_PLAN.md
│   │
│   └── papers/
│       └── NRADIX_PAPER_V2.md
│
├── CPU_Phases/                      ← NEW: Legacy Phase project
│   ├── Phase1_Prototype/            ← as-is
│   │   ├── firmware/
│   │   ├── hardware/
│   │   └── admin_logistics/
│   │
│   ├── Phase2_Fiber_Benchtop/       ← as-is
│   │   ├── firmware/
│   │   ├── hardware/
│   │   └── docs/
│   │
│   ├── Phase3_Chip_Simulation/      ← as-is
│   │   ├── admin_logistics/
│   │   └── analysis/
│   │
│   ├── Phase4_DIY_Fab/              ← as-is
│   │   ├── documentation/
│   │   └── equipment/
│   │
│   └── cpu_architecture/            ← from Research/programs/cpu_architecture/
│       ├── ternary_isa_simulator.py
│       ├── opu_controller.py
│       └── memory/
│
├── Research/                        ← Shared research data
│   └── data/
│       ├── wdm_validation/         (simulation results)
│       ├── csv/
│       └── h5/
│
├── docs/                            ← Shared documentation
│   ├── session_notes/
│   ├── decisions/
│   └── FILE_ORGANIZATION.md        (this file)
│
├── tools/                           ← Shared utilities
│   └── research_search/
│
└── [Root files remain]
    ├── CLAUDE.md
    ├── README.md (updated)
    ├── requirements.txt
    └── LICENSE
```

---

## Current → Proposed Mapping

### TPU (N-Radix) Files

| Current Location | New Location |
|------------------|--------------|
| `nradix-driver/` | `NRadix_Accelerator/driver/` |
| `Research/programs/nradix_architecture/` | `NRadix_Accelerator/architecture/` |
| `Research/programs/shared/photonics/` | `NRadix_Accelerator/components/photonics/` |
| `Research/programs/shared/nrioc_module.py` | `NRadix_Accelerator/components/` |
| `Research/programs/simulations/wdm_*.py` | `NRadix_Accelerator/simulations/` |
| `Research/data/gds/` | `NRadix_Accelerator/gds/` |
| `docs/CHIP_INTERFACE.md` | `NRadix_Accelerator/docs/` |
| `docs/DRIVER_SPEC.md` | `NRadix_Accelerator/docs/` |
| `docs/DRC_RULES.md` | `NRadix_Accelerator/docs/` |
| `docs/LAYER_MAPPING.md` | `NRadix_Accelerator/docs/` |
| `docs/PACKAGING_SPEC.md` | `NRadix_Accelerator/docs/` |
| `docs/MPW_RETICLE_PLAN.md` | `NRadix_Accelerator/docs/` |
| `docs/papers/NRADIX_PAPER_V2.md` | `NRadix_Accelerator/papers/` |

### CPU (Phases) Files

| Current Location | New Location |
|------------------|--------------|
| `Phase1_Prototype/` | `CPU_Phases/Phase1_Prototype/` |
| `Phase2_Fiber_Benchtop/` | `CPU_Phases/Phase2_Fiber_Benchtop/` |
| `Phase3_Chip_Simulation/` | `CPU_Phases/Phase3_Chip_Simulation/` |
| `Phase4_DIY_Fab/` | `CPU_Phases/Phase4_DIY_Fab/` |
| `Research/programs/cpu_architecture/` | `CPU_Phases/cpu_architecture/` |

---

## Migration Steps

### Step 1: Create Directory Structure
```bash
mkdir -p NRadix_Accelerator/{driver,architecture,components,simulations,gds,docs,papers}
mkdir -p CPU_Phases
```

### Step 2: Move N-Radix Files
```bash
git mv nradix-driver/* NRadix_Accelerator/driver/
git mv Research/programs/nradix_architecture/* NRadix_Accelerator/architecture/
git mv Research/programs/simulations/wdm_*.py NRadix_Accelerator/simulations/
git mv Research/data/gds NRadix_Accelerator/gds
# ... etc
```

### Step 3: Move CPU Phase Files
```bash
git mv Phase1_Prototype CPU_Phases/
git mv Phase2_Fiber_Benchtop CPU_Phases/
git mv Phase3_Chip_Simulation CPU_Phases/
git mv Phase4_DIY_Fab CPU_Phases/
git mv Research/programs/cpu_architecture CPU_Phases/
```

### Step 4: Update Imports
- Update Python import paths in all moved files
- Update any hardcoded paths

### Step 5: Update README
- Update root README.md to reflect new structure
- Add README.md to each new top-level directory

---

## Benefits

1. **Clarity** - Immediately obvious which code is accelerator vs experimental CPU
2. **Focus** - N-Radix is the active project; CPU phases are preserved but separate
3. **Foundry Ready** - N-Radix directory can be packaged for foundry submission
4. **Contribution** - Contributors can focus on one path without confusion

---

## Questions for Review

1. Should `Research/data/` stay shared or split between projects?
2. Should `tools/research_search/` stay at root or move?
3. Any files unclear about which project they belong to?

---

## Approval

- [ ] Christopher reviewed and approved
- [ ] Migration executed
- [ ] Imports updated
- [ ] Tests pass
