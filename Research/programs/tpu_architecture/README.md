# TPU Architecture - AI Accelerator Path

This directory contains the optical tensor processing unit (TPU) implementation - optimized for AI/ML workloads using systolic array architecture.

## Core Concept

**Streaming matrix operations via WDM parallel processing**

Unlike the general-purpose CPU path, this architecture is purpose-built for:
- Matrix multiplication (GEMM operations)
- Convolutions
- Transformer attention patterns
- Any operation that can be expressed as systolic data flow

## Key Files

### Core Systolic Array
- **`optical_systolic_array.py`** - Base systolic array implementation using ternary optical elements
- **`c_band_wdm_systolic.py`** - WDM-enhanced version using C-band wavelength channels for parallel lanes
- **`super_ioc_module.py`** - Super integrated optical compute module (scaled-up IOC)
- **`integrated_supercomputer.py`** - Full system integration with memory hierarchy

### Application-Specific Generators
- **`home_ai/`** - Home AI accelerator designs (edge inference)
- **`supercomputer/`** - Exascale supercomputer configurations

## Architecture Highlights

1. **Systolic Data Flow** - Data streams through a 2D array of processing elements, maximizing reuse
2. **WDM Parallelism** - Multiple wavelength channels operate simultaneously (up to 80 channels in C-band)
3. **Ternary Advantage** - 3-state encoding (1550nm/1310nm/1064nm) provides log3/log2 = 1.58x density improvement
4. **Streaming Architecture** - Continuous data flow, no fetch-decode-execute overhead

## How Weights Are Stored: Bistable Kerr Flip-Flops

Each Processing Element (PE) contains a **9-trit weight register** built from bistable Kerr resonators. Here's how it works:

### The Mechanism

A Kerr resonator exploits the optical Kerr effect (χ³ nonlinearity) where the refractive index changes with light intensity. At the right power levels, the resonator has **two stable states** - it "locks" into one or the other based on input.

For ternary storage, each trit uses **wavelength presence** to encode three states:

| Stored Value | Wavelength Present | Physical State |
|--------------|-------------------|----------------|
| **-1** | 1550nm (Red) | Resonator locked to λ_red |
| **0** | 1310nm (Green) | Resonator locked to λ_green |
| **+1** | 1064nm (Blue) | Resonator locked to λ_blue |

### Writing a Weight (Setting the Flip-Flop)

To write a value to a PE's weight register:

1. **Assert the WRITE_ENABLE line** for that PE (optical pulse on the write bus)
2. **Inject the desired wavelength** at high power (above bistability threshold)
3. **Remove WRITE_ENABLE** - the resonator stays locked to that wavelength

The write operation takes ~10ns (a few clock cycles at 617 MHz).

### Example: Loading a 3×3 Weight Matrix

Say we want to load this weight matrix into a 3×3 section of the systolic array:

```
W = | +1  -1   0 |
    |  0  +1  +1 |
    | -1   0  -1 |
```

**Step 1: Address the PEs**

The weight loading bus addresses PEs row by row:
```
Clock 1: Select Row 0 (PE[0,0], PE[0,1], PE[0,2])
Clock 2: Select Row 1 (PE[1,0], PE[1,1], PE[1,2])
Clock 3: Select Row 2 (PE[2,0], PE[2,1], PE[2,2])
```

**Step 2: Inject wavelengths for each row**

```
Clock 1, Row 0: Inject 1064nm → PE[0,0]  (+1)
                Inject 1550nm → PE[0,1]  (-1)
                Inject 1310nm → PE[0,2]  (0)

Clock 2, Row 1: Inject 1310nm → PE[1,0]  (0)
                Inject 1064nm → PE[1,1]  (+1)
                Inject 1064nm → PE[1,2]  (+1)

Clock 3, Row 2: Inject 1550nm → PE[2,0]  (-1)
                Inject 1310nm → PE[2,1]  (0)
                Inject 1550nm → PE[2,2]  (-1)
```

**Total load time for 3×3:** 3 clock cycles = ~4.9ns

**For an 81×81 array:** 81 clock cycles = ~131ns (~0.13μs)

### Reading the Weight (During Compute)

During matrix operations, each PE continuously outputs its stored wavelength at low power. The mixer combines this with the streaming input:

```
          Input activation (streaming)
                    ↓
    ┌───────────────────────────────┐
    │              PE               │
    │   ┌───────────────────────┐   │
    │   │  Kerr Bistable Cell   │   │
    │   │  (stores weight λ)    │───┼──→ Weight wavelength (continuous)
    │   └───────────────────────┘   │
    │              ↓                │
    │         SFG Mixer             │
    │    (input × weight = output)  │
    │              ↓                │
    └───────────────────────────────┘
                    ↓
           Output (to next PE)
```

The weight doesn't need to be "read" in a traditional sense - it's always present, always mixing with the input stream. This is why systolic arrays are so efficient: **weights are stationary, data flows through**.

### Persistence

Bistable Kerr resonators maintain their state indefinitely as long as:
- Minimum holding power is maintained (~1mW)
- No write pulse is applied

No refresh cycles needed (unlike DRAM). Weights persist until explicitly overwritten.

---

## Performance Targets

| Configuration | Peak Performance | Notes |
|--------------|------------------|-------|
| 27x27 array | 583 TFLOPS | Single chip, base |
| 243x243 array | 47 PFLOPS | Multi-chiplet |
| 960x960 array | 738 PFLOPS | Full scale |

*Performance scales with array size squared and WDM channel count*

## vs General-Purpose Path

The `standard_computer/` directory contains the von Neumann architecture path (fetch-decode-execute, branching, etc.). This TPU path trades flexibility for raw throughput on tensor operations.

**Use TPU path for:** Training, inference, any matrix-heavy workload
**Use CPU path for:** Control flow, I/O handling, general compute
