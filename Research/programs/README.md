# Optical Computer Programs

## Directory Structure (Organized by Computer Type)

```
Research/programs/
├── standard_computer/     # Tier 1: General Purpose (~4 TFLOPS)
│   ├── README.md
│   └── standard_generator.py
│
├── home_ai/               # Tier 2: Prosumer AI (~291 TFLOPS)
│   ├── README.md
│   └── home_ai_generator.py
│
├── supercomputer/         # Tier 3: Datacenter (~2.33 PFLOPS)
│   ├── README.md
│   └── supercomputer_generator.py
│
├── shared_components/     # Modules used by all tiers
│   └── README.md
│
├── simulations/           # Meep FDTD physics validation
│   └── README.md
│
└── [shared .py files]     # Core module implementations
```

## Quick Start

```bash
cd /home/jackwayne/Desktop/Optical_computing

# Generate Standard Computer (dev kit, ~4 TFLOPS)
.mamba_env/bin/python3 Research/programs/standard_computer/standard_generator.py

# Generate Home AI (prosumer, ~291 TFLOPS)
.mamba_env/bin/python3 Research/programs/home_ai/home_ai_generator.py

# Generate Supercomputer (datacenter, ~2.33 PFLOPS)
.mamba_env/bin/python3 Research/programs/supercomputer/supercomputer_generator.py
```

## Three Computer Types

| Tier | Name | Array | TFLOPS | vs GPU | Config |
|------|------|-------|--------|--------|--------|
| 1 | Standard | 81×81 | 4 | 0.05x 4090 | 1 SC |
| 2 | Home AI | 243×243 + 8 WDM | 291 | **3.5x 4090** | 1-4 SC |
| 3 | Supercomputer | 243×243 × 8 × 8 WDM | 2,330 | **1.2x H100** | 8 SC |

## Round Table Architecture

**ALL tiers use the Round Table backplane architecture:**

```
        Ring 0 (CENTER):  Kerr Clock (617 MHz)
        Ring 1:           Supercomputers (1-8)
        Ring 2:           Super IOCs (1-8)
        Ring 3 (OUTER):   IOAs (modular peripherals)
```

**CRITICAL**: All components equidistant from central Kerr clock to minimize clock skew.

## Core Module Files

| File | Purpose |
|------|---------|
| `optical_backplane.py` | Round Table + legacy backplanes |
| `optical_systolic_array.py` | 81×81 systolic array |
| `c_band_wdm_systolic.py` | WDM systolic arrays (243×243) |
| `super_ioc_module.py` | Streaming interface |
| `ioc_module.py` | Input/Output Converter |
| `ioa_module.py` | Peripheral adapters |
| `opu_controller.py` | Controller (the "brain") |
| `storage_ioa.py` | NVMe/DDR5/HBM interfaces |

## Simulation Files

| File | Component |
|------|-----------|
| `kerr_resonator_sim.py` | 617 MHz clock generation |
| `awg_demux_sim.py` | Wavelength demultiplexer |
| `mzi_switch_sim.py` | Optical switches |
| `soa_gate_sim.py` | SOA amplifiers |

## Output Locations

- GDS files: `Research/data/gds/[tier]/`
- CSV data: `Research/data/csv/`
- Session notes: `docs/session_notes/`
