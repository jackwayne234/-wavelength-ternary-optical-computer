# SHARED COMPONENTS

## Modules Used Across All Computer Tiers

These components are the building blocks shared by Standard, Home AI, and Supercomputer configurations.

## Core Modules

| Module | File | Purpose |
|--------|------|---------|
| **IOC** | `../ioc_module.py` | Input/Output Converter (Electronic ↔ Optical) |
| **Super IOC** | `../super_ioc_module.py` | Streaming interface (weights, activations, results) |
| **IOA** | `../ioa_module.py` | Input/Output Adapters (PCIe, Ethernet, etc.) |
| **Storage IOA** | `../storage_ioa.py` | NVMe, DDR5, HBM interfaces |
| **OPU Controller** | `../opu_controller.py` | The "brain" - command sequencing |
| **Backplane** | `../optical_backplane.py` | Round Table and legacy backplanes |

## RAM Tier Generators

| Tier | File | Access Time | Registers |
|------|------|-------------|-----------|
| Tier 1 (Hot) | `../ternary_tier1_ram_generator.py` | ~1 ns | ACC, TMP, A, B |
| Tier 2 (Working) | `../ternary_tier2_ram_generator.py` | ~10 ns | R0-R15 |
| Tier 3 (Parking) | `../ternary_tier3_ram_generator.py` | ~100 ns | P0-P31 |

## Systolic Array Generators

| File | Array Size | PEs |
|------|------------|-----|
| `../optical_systolic_array.py` | 81×81 | 6,561 |
| `../c_band_wdm_systolic.py` | 243×243 + WDM | 59,049+ |

## Key Design Principle

```
████████████████████████████████████████████████████████████████████
█                                                                  █
█   ALL COMPONENTS MUST BE COMPATIBLE WITH ROUND TABLE LAYOUT      █
█   - Central Kerr clock (617 MHz)                                 █
█   - Equidistant placement from clock                             █
█   - Minimal clock skew across all modules                        █
█                                                                  █
████████████████████████████████████████████████████████████████████
```

## Usage

These modules are imported by tier-specific generators:

```python
# Example: In supercomputer_generator.py
import sys
sys.path.insert(0, '..')
from optical_backplane import round_table_backplane
from super_ioc_module import super_ioc_module
from c_band_wdm_systolic import wdm_systolic_array
```
