# CPU Phases (Legacy Project)

This directory contains the original optical CPU development phases - an experimental project exploring optical computing from benchtop prototype to chip fabrication.

## Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | RGB Laser Prototype (24"×24" demonstrator) | Complete |
| Phase 2 | Fiber-Optic Benchtop (10 GHz telecom) | Design |
| Phase 3 | Chip Simulation (LiNbO3 photonics) | Simulation |
| Phase 4 | DIY Fab (garage semiconductor) | Research |

## Directory Structure

```
CPU_Phases/
├── Phase1_Prototype/      # ESP32 + visible lasers
├── Phase2_Fiber_Benchtop/ # ITU C-Band telecom
├── Phase3_Chip_Simulation/# Foundry-ready chip design
├── Phase4_DIY_Fab/        # Alternative fabrication
└── cpu_architecture/      # ISA simulator, memory designs
```

## Note

The active project is now **N-Radix Accelerator** (see `../NRadix_Accelerator/`), which focuses on AI workloads rather than general-purpose CPU computing. These phases are preserved for reference and potential future exploration.
