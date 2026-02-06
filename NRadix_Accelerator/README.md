# N-Radix Optical Accelerator

An optical AI accelerator achieving ~59× the performance of NVIDIA's B200 for matrix multiply workloads.

## Architecture Breakthrough: Streamed Weight Design

**Key insight:** Weights are stored in the CPU's optical RAM and streamed to processing elements (PEs) - no per-PE weight storage required.

### Design Principles

1. **Simplified PEs**: Each processing element contains only:
   - SFG mixer (sum-frequency generation for multiply)
   - Waveguide routing (input/output paths)
   - That's it. No local memory, no complex control logic.

2. **Unified Optical Memory**: The CPU's 3-tier optical RAM serves dual purpose:
   - Standard CPU operations (when running CPU workloads)
   - Accelerator weight storage (streamed to PEs during inference/training)

3. **All-Optical Data Path**: Weights flow from optical RAM → waveguide network → PEs without domain conversion. No electrical bottlenecks, no DAC/ADC overhead.

### Why This Matters

| Aspect | Traditional (per-PE storage) | Streamed Design |
|--------|------------------------------|-----------------|
| PE Complexity | Memory + compute + control | SFG mixer + routing only |
| Fabrication Yield | Lower (more components) | Higher (simpler PEs) |
| Power | Per-PE memory leakage | Centralized, amortized |
| Flexibility | Fixed weight capacity | Limited only by optical RAM |
| Domain Crossings | Multiple E/O conversions | Purely optical |

This architectural simplification makes the design significantly more practical to manufacture while maintaining the performance advantages of optical compute.

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
