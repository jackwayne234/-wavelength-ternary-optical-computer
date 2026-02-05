# N-Radix Optical Accelerator

An optical AI accelerator achieving ~59× the performance of NVIDIA's B200 for matrix multiply workloads.

## Directory Structure

```
NRadix_Accelerator/
├── driver/          # NR-IOC driver (C + Python bindings)
├── architecture/    # Systolic array designs (27×27, 81×81)
├── components/      # Photonic component simulations
├── simulations/     # WDM validation tests (Meep FDTD)
├── gds/            # Chip layouts and mask files
├── docs/           # Interface specs, DRC rules, packaging
└── papers/         # Academic papers
```

## Quick Start

```bash
# Run WDM validation
cd simulations/
export OMP_NUM_THREADS=12
/home/jackwayne/miniconda/envs/meep_env/bin/python wdm_27x27_array_test.py

# Use the Python driver/simulator
cd driver/python/
python -c "from nradix import NRadixSimulator; sim = NRadixSimulator(27)"
```

## Key Specs

| Metric | Value |
|--------|-------|
| Array Sizes | 27×27 (729 PEs), 81×81 (6,561 PEs) |
| Clock | 617 MHz (Kerr self-pulsing) |
| WDM Channels | 6 triplets (18 wavelengths) |
| Performance | ~59× B200 (matrix multiply) |

## Documentation

- [Chip Interface](docs/CHIP_INTERFACE.md) - How to connect to the chip
- [Driver Spec](docs/DRIVER_SPEC.md) - NR-IOC driver details
- [DRC Rules](docs/DRC_RULES.md) - Design rules for fabrication
- [Packaging](docs/PACKAGING_SPEC.md) - Fiber coupling, bond pads

## Validation Status

- [x] 3×3 WDM array - PASSED
- [x] 9×9 WDM array - PASSED
- [ ] 27×27 WDM array - Running
- [ ] 81×81 WDM array - Queued
