# Optical CPU as N-Radix IOC Controller

## Overview

The optical ternary CPU, originally designed as a general-purpose processor, has a natural role as the **brain of the NR-IOC** (N-Radix I/O Controller). Rather than competing with the N-Radix accelerator on raw compute, the CPU orchestrates it.

This document describes how the CPU architecture integrates with the N-Radix ecosystem.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  HOST SYSTEM                                                │
│  ├── x86/ARM CPU                                            │
│  ├── Linux kernel + nradix driver                          │
│  └── User applications (PyTorch, TensorFlow, etc.)         │
└─────────────────────┬───────────────────────────────────────┘
                      │ PCIe Gen4 x16 (64 GB/s)
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  ELECTRONIC INTERFACE (minimal)                             │
│  ├── PCIe PHY + DMA engine                                  │
│  ├── Boot ROM (loads CPU firmware)                          │
│  └── Clock bridge (electronic → 617 MHz Kerr)              │
└─────────────────────┬───────────────────────────────────────┘
                      │ Optical (1550/1310/1064 nm)
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  OPTICAL CPU (IOC Controller)                               │
│  ├── 81-trit word size (~128-bit equivalent)               │
│  ├── 27-instruction ISA                                     │
│  ├── 3-way branch predictor                                 │
│  ├── 3-tier optical register file                          │
│  ├── DMA controller                                         │
│  ├── Interrupt controller                                   │
│  └── Accelerator interface                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ Optical bus
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  N-RADIX ACCELERATOR                                        │
│  ├── Systolic array (scalable: 27×27 to 960×960)           │
│  ├── WDM channels (1-6 triplets)                           │
│  ├── SFG mixers for ternary arithmetic                     │
│  └── Ring resonator selectors                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  MEMORY HIERARCHY                                           │
│  ├── Tier 1 (Hot): 4 optical registers, ~1ns               │
│  ├── Tier 2 (Working): 16 optical registers, ~10ns         │
│  ├── Tier 3 (Parking): 32 optical registers, ~100ns        │
│  ├── HBM: High-bandwidth DRAM, ~μs                         │
│  ├── DDR: System memory, ~100ns                            │
│  └── NVMe: Bulk storage, ~ms                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Why This Makes Sense

### 1. Native Ternary Throughout
The CPU speaks the same language as the accelerator:
- Same wavelength encoding (1550/1310/1064 nm = -1/0/+1)
- Same 81-trit word size
- No ternary↔binary conversion between controller and compute

### 2. Control Plane vs Data Plane
| Component | Role | Optimized For |
|-----------|------|---------------|
| Optical CPU | Control plane | Branching, scheduling, I/O |
| N-Radix Accelerator | Data plane | Matrix math, throughput |

This mirrors modern GPU architectures (CPU + CUDA cores) but in a unified optical domain.

### 3. ISA Already Designed for This

The 27-instruction ISA includes everything needed for IOC duties:

**Memory Management:**
- `LD1/ST1` - Tier 1 (hot) access
- `LD2/ST2` - Tier 2 (working) access
- `LD3/ST3` - Tier 3 (parking) access
- `DMA` - Bulk data movement

**Control Flow:**
- `BR3` - 3-way branch (negative/zero/positive paths)
- `BRN/BRZ/BRP` - Conditional branches
- `CALL/RET` - Subroutine support

**System:**
- `INT` - Software interrupt
- `HALT` - Stop processor

### 4. Existing Work Repurposed

| Existing Component | New Role |
|--------------------|----------|
| OPU Controller (GDS) | IOC controller core |
| ISA Simulator | Firmware development/testing |
| Memory tier design | Optical register file |
| Interrupt controller | IOA event handling |
| DMA controller | Host↔Accelerator transfers |

---

## CPU Responsibilities

The optical CPU handles:

1. **Command Parsing**
   - Receive work descriptors from host via PCIe
   - Decode operation type, dimensions, data pointers
   - Queue work for accelerator

2. **Work Scheduling**
   - Manage accelerator utilization
   - Handle dependencies between operations
   - Overlap compute with data movement

3. **DMA Coordination**
   - Move data between memory tiers
   - Prefetch inputs for next operation
   - Write back results to host

4. **Error Handling**
   - Monitor accelerator status
   - Handle overflow, underflow, invalid operations
   - Report errors to host driver

5. **Power Management**
   - Gate unused accelerator sections
   - Manage optical amplifier power
   - Thermal monitoring

---

## Firmware Model

The CPU runs a simple firmware loop:

```
; IOC Main Loop (pseudocode in ternary assembly)

init:
    LDI ACC, 0          ; Clear accumulator

main_loop:
    ; Check for host commands
    LD1 ACC, CMD_QUEUE
    TST ACC
    BRZ main_loop       ; No commands, keep polling

    ; Decode command
    CALL decode_cmd

    ; Dispatch based on command type
    BR3 handle_neg, handle_zero, handle_pos

handle_neg:             ; Error/reset commands
    CALL process_error
    JMP main_loop

handle_zero:            ; Status/query commands
    CALL process_status
    JMP main_loop

handle_pos:             ; Compute commands
    CALL dispatch_work
    JMP main_loop

dispatch_work:
    ; Setup DMA for input data
    DMA
    ; Configure accelerator
    ST1 ACC, ACCEL_CONFIG
    ; Wait for completion
    ...
    RET
```

---

## Integration Points

### With N-Radix Accelerator
- Direct optical bus connection
- Shared wavelength encoding
- CPU sends configuration, receives status
- No serialization/deserialization overhead

### With Host Driver (nradix-driver)
- PCIe BAR for command queues
- MSI-X interrupts for completion notification
- DMA descriptors for data transfer
- Memory-mapped status registers

### With Memory Hierarchy
- Optical tiers for hot data (inputs/outputs in flight)
- HBM for working set (model weights, activations)
- DDR/NVMe for cold storage (model checkpoints, datasets)

---

## Scaling Considerations

The CPU doesn't need to scale with the accelerator. A single optical CPU core can manage:
- Multiple accelerator chips (if using multi-chip module)
- Multiple WDM channel groups
- The full memory hierarchy

For redundancy or higher command throughput, 2-4 CPU cores could be used, but this is optional.

---

## Development Path

1. **Now:** Use ISA simulator for firmware development
2. **Phase 1:** Validate CPU design in FPGA emulation
3. **Phase 2:** Fabricate CPU as part of IOC chip
4. **Phase 3:** Integrate with accelerator for full system

---

## Relationship to N-Radix Accelerator

**The accelerator is the star.** It's what delivers the PFLOPS, what competes with H100/B200, what the world needs for AI compute.

The CPU is the **roadie** - it sets up the stage, manages the equipment, handles the logistics. Essential, but not the headline act.

### Critical Discovery: Optical RAM as Weight Storage (Feb 5, 2026)

The CPU's 3-tier optical RAM system solves the accelerator's weight storage problem:

**The Problem:** Original accelerator design assumed per-PE "bistable Kerr resonator" storage for weights. Tristable optical storage is unproven at scale.

**The Solution:** Stream weights from the CPU's optical RAM tiers directly to the systolic array.

```
[Optical RAM Tiers]  ←  Weights stored here (optical)
        ↓
   [Waveguides]      ←  Stream to array (optical)
        ↓
  [Systolic Array]   ←  Simple mixers, no per-PE storage
        ↓
    [NR-IOC]         ←  Convert results to host (only conversion point)
```

**Benefits:**
- PEs become simple (just mixer + routing)
- No exotic per-PE tristable storage needed
- Higher fabrication yield
- Unified optical domain from storage through compute
- CPU and Accelerator share the same memory infrastructure

**The CPU isn't just the controller - its memory system IS the accelerator's weight storage.**

This document lives in `CPU_Phases/` because that's where the CPU design work is tracked. The accelerator documentation in `NRadix_Accelerator/` remains the primary focus.

---

*Last updated: 2026-02-05*
