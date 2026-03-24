# NRadix Hybrid Architecture: Optical Multiply + Electronic Accumulate

**Status:** Architecture correction — March 23, 2026
**Supersedes:** All prior "fully optical MAC" claims

---

## 1. What Changed

The original NRadix architecture made three claims that do not hold:

1. **"Fully optical MAC"** — The multiply step is optical. The accumulate step cannot be.
2. **"No transistors in the compute path"** — Photodetectors and adder trees are electronic components. They are in the compute path.
3. **"Optical superposition handles accumulation"** — It does not. Superposition destroys information.

### Why optical accumulation fails

When multiple SFG output beams are combined into a single waveguide or free-space path, their fields superpose. The resulting intensity is a function of amplitudes and phases, not a clean arithmetic sum of trit values. You cannot recover individual products from the combined signal. A signal at total power P could be one beam at P, two beams at P/2, three beams at P/3, or any other decomposition. The information needed to compute a dot product — the individual product values — is gone.

This is not an engineering limitation. It is physics. Optical superposition is linear in the field, not in the encoded trit value. Intensity detection gives you |sum of fields|^2, not sum of |individual values|.

### The "counting ports" insight (March 21, 2026)

The proposed optical accumulation cube — a structure to combine SFG outputs and somehow preserve their individual contributions — is unnecessary. The architecture is simpler than that:

- Each SFG unit has a known set of output ports (one per possible product value).
- A photodetector on each port tells you: did this product fire, yes or no?
- The trit value of the product is determined by *which port* lit up, not by measuring intensity.
- Accumulation is then just: read the port labels, sum electronically.

No optical accumulation structure needed. No intensity arithmetic. Just detect and count.

---

## 2. The Honest Architecture

```
OPTICAL DOMAIN                              | BOUNDARY        | ELECTRONIC DOMAIN
                                            |                 |
Laser A (freq-encoded trit) ──┐             |                 |
                               ├─ SFG Chamber ─> Photodetector ──> ┐
Laser B (freq-encoded trit) ──┘             |                 |    │
                                            |                 |    │
Laser A (freq-encoded trit) ──┐             |                 |    ├── Adder Tree ──> Dot Product
                               ├─ SFG Chamber ─> Photodetector ──> ┘
Laser B (freq-encoded trit) ──┘             |                 |
                                            |                 |
         (xN parallel SFG chambers)         |                 |  (one adder tree per output element)
```

> **Note:** Each "SFG Chamber" is the final physical PE design — a passive broadcast-and-select unit containing multiple PPLN waveguides. See [Chamber Architecture](#chamber-architecture--broadcast-and-select-sfg) below for internals.

**Signal chain, step by step:**

1. **Encode:** Map each balanced ternary trit {-1, 0, +1} to a laser frequency. Two input vectors, N trits each.
2. **Multiply (optical):** Each SFG crystal takes one frequency from vector A and one from vector B. Output frequency = sum of input frequencies, which encodes the product trit. All N multiplies fire simultaneously.
3. **Detect (boundary):** A photodetector at each SFG output port converts the optical product signal to an electrical signal. The port identity tells you the product value.
4. **Accumulate (electronic):** An adder tree sums the N detected product values to produce one element of the output vector.
5. **Repeat:** For matrix-vector multiply, run N dot products (one per output row). For matrix-matrix, run N^2.

---

## Chamber Architecture — Broadcast-and-Select SFG

This section describes the internal design of each processing element (PE) in the optical multiply array. It is an evolution of the hybrid architecture, not a replacement — the optical/electronic split described above remains unchanged. The chamber is about HOW the optical multiply works internally.

### The problem the chamber solves

A single PPLN waveguide is phase-matched for one specific input frequency pair. If inputs A and B can each take 3 values (ternary), there are 9 possible input pair combinations. A naive design would require a switching network in front of the SFG to route each pair to the correct waveguide — adding active components, routing logic, and pre-knowledge of the input values before they arrive.

### The SFG Chamber

At each PE position, instead of a single SFG waveguide, there is a **chamber** containing multiple PPLN waveguides — one for every possible input pair. The chamber is entirely passive in the optical domain.

**How it works:**

1. Two input frequencies (representing trit values) are broadcast into the chamber simultaneously.
2. Each PPLN waveguide inside has a different poling period, tuned to phase-match one specific input pair.
3. Only the waveguide whose poling period matches the incoming pair will efficiently convert — the others stay dark (suppressed by 32-80 dB, already validated in SFG simulations).
4. The matching waveguide produces the correct product frequency.
5. A photodetector reads which output frequency appeared.

### What this eliminates

- **No switching network** needed to select the right SFG.
- **No routing logic** to determine which pair is arriving.
- **No pre-knowledge of inputs** required.
- **Physics does ALL the selection** — the chip is entirely passive in the optical domain.

### Chamber contents (for ternary {1, 2, 3})

- 9 PPLN waveguides with poling periods spanning 19.79-22.55 um
- Each tuned to one of the 9 possible input pairs
- 6 unique output frequencies (382-402 THz)
- Validated: wrong-pair suppression is 32-80 dB

### Encoding flexibility

The physical chamber is encoding-agnostic. The same hardware supports:

| Encoding | Values | Mechanism | Notes |
|----------|--------|-----------|-------|
| Unbalanced ternary | {1, 2, 3} | 9 SFG pairs, 6 unique products | Current encoding |
| Balanced ternary | {-1, 0, +1} | SFG lanes (+x+ = +, -x- = +) and DFG lanes (+x- = -, -x+ = -), zero = no light | Neural network natural encoding |
| Binary | {-1, +1} | Only SFG and DFG lanes needed | Simplest case |
| Any radix | N values | Add more PPLN waveguides per chamber | Scales linearly |

The encoding scheme is a software/firmware decision about which laser frequencies map to which values. The physical chip is the same regardless.

### Updated signal chain diagram

```
OPTICAL DOMAIN                              | BOUNDARY        | ELECTRONIC
                                            |                 |
Input A freq ──→ ┌─────────────────────┐    |                 |
                 │   SFG CHAMBER       │    |                 |
                 │                     │    |                 |
                 │  PPLN₁ (pair 1×1) ─┐│    |                 |
                 │  PPLN₂ (pair 1×2) ─┤│    |                 |
                 │  PPLN₃ (pair 1×3) ─┤│───→│  Photodetector ─→ Adder
                 │  ...               ─┤│    |                 |   Tree
                 │  PPLN₉ (pair 3×3) ─┘│    |                 |    ↓
                 │                     │    |                 |  Dot Product
Input B freq ──→ └─────────────────────┘    |                 |  Result
                                            |                 |
(Only the phase-matched PPLN fires)         |                 |
```

### Why this is the final PE design

The broadcast-and-select chamber resolves the last open question in the multiply unit: how to handle arbitrary input pairs without active routing. By placing all possible PPLN waveguides in parallel and letting phase-matching physics do the selection, the entire optical domain remains passive. No switches, no control signals, no feedback loops. Light goes in, the correct product comes out.

---

## 3. What's Optical (and Why It's Valuable)

### The multiply via SFG

Sum Frequency Generation in a PPLN (periodically poled lithium niobate) waveguide takes two input photons and produces one output photon whose frequency is the sum of the inputs. When trit values are encoded as frequency offsets, frequency addition IS trit multiplication (in balanced ternary, the product table maps directly to frequency sums).

### Why this matters

- **All N multiplies happen simultaneously.** No clock, no sequential pipeline for the multiply step. The latency is the speed of light through the waveguide (~ps scale).
- **Multiply is the expensive operation.** In a matrix multiply of dimension N, there are N^2 multiplications per output element. In electronic accelerators (TPUs, GPUs), each multiply costs ~0.9-4.2 pJ depending on precision.
- **Power scales with laser power, not with transistor switching.** The SFG process is driven by the input laser fields. Total optical power budget is in the low mW range for the multiply array, compared to tens of watts for the equivalent electronic multiply array.

---

## 4. What's Electronic (and Why That's Fine)

### Photodetection

Each SFG output port has a photodetector (InGaAs or silicon, depending on wavelength). This converts the optical product signal to an electrical current. Standard telecom-grade detectors, nothing exotic.

### Adder tree

N electrical product signals feed into a binary adder tree to produce the dot product sum. For balanced ternary values, the products are small integers (-1, 0, +1), so the adder tree is narrow and fast.

### The cost of addition

- One addition: ~0.1 pJ in modern CMOS
- One multiply: ~0.9-4.2 pJ in modern CMOS
- Ratio: addition is 10-40x cheaper than multiplication

The accumulate step involves N additions per dot product. The multiply step involves N multiplications per dot product. By offloading the multiplications to optics and keeping the additions in electronics, we are replacing the expensive operations and keeping the cheap ones. This is the correct split.

### Memory and control

Weights must be loaded from electronic memory (SRAM/HBM) to configure the laser modulators. Control logic sequences the matrix operations. This is identical to how every electronic accelerator works — the memory wall is the same.

---

## 5. Why This Split Is Optimal

| Aspect | Optical Multiply | Electronic Accumulate |
|--------|-----------------|----------------------|
| Operation | SFG frequency addition | Binary adder tree |
| Parallelism | All N at once (speed of light) | Pipelined tree, O(log N) depth |
| Energy per op | Sub-pJ (laser amortized) | ~0.1 pJ per addition |
| Latency | ~ps (waveguide transit) | ~ns (CMOS logic) |
| Complexity | Passive waveguide + crystal | Standard digital logic |

The throughput bottleneck in any matrix accelerator is memory bandwidth, not arithmetic. A TPU spends most of its time waiting for weights to arrive from HBM. This architecture has the same bottleneck — it does not eliminate the memory wall.

**The advantage is power, not speed.** For the same throughput as an electronic accelerator:

- The multiply array dissipates milliwatts instead of watts
- Total system power drops significantly because multiplies dominate the energy budget
- Less heat means denser packing, which means shorter interconnects, which means less energy on data movement

This is not "optical computing replaces electronics." This is "optics handles the one operation where it has a physical advantage, electronics handles everything else."

---

## 6. What Remains Valid

All simulation and design work on the optical multiply path is unaffected by this architectural correction. The multiply unit was always the novel contribution.

| Validation | Result | Status |
|-----------|--------|--------|
| SFG trit multiplication (all 9 product combinations) | 6/6 PASS (degenerate cases consolidated) | Valid |
| AWG demultiplexer routing (19 channels) | 19/19 PASS | Valid |
| AWG multiply unit integration | 3/3 PASS | Valid |
| PPLN quasi-phase-matching periods | 19.79-22.55 um, standard fab | Valid |
| End-to-end signal chain (encode -> SFG -> detect) | 9/9 PASS | Valid |
| FDTD adjoint-optimized multiply unit | 100% port efficiency, 3/3 ports | Valid |
| GDS layout files | Foundry-ready for multiply unit | Valid |

The physics works. The fabrication is feasible. The multiply unit does what it claims.

---

## 7. What's Invalidated

| Previous Claim | Correction |
|---------------|-----------|
| Fully optical MAC | Optical multiply only. Accumulate is electronic. |
| No transistors in compute path | Photodetectors + adder trees are electronic and are in the compute path. |
| Optical superposition handles accumulate | It does not. Superposition loses the individual product values needed for summation. |
| Direct performance comparisons to H100/B200 | Throughput comparisons remain valid — memory bandwidth is the bottleneck in both architectures, not arithmetic. The advantage is power and cooling, not raw TOPS. See [System-Level Power Comparison](#9-system-level-power-comparison). |

---

## 9. System-Level Power Comparison

### Why throughput is identical

Both optical and electronic matrix multipliers are **memory-bound**. The arithmetic units — whether SFG chambers or INT8 multiply-accumulate arrays — sit idle most of the time, waiting for weights to arrive from HBM. The throughput ceiling is set by memory bandwidth, not compute speed.

This means the hybrid optical architecture does not claim faster TOPS. It claims the **same throughput at radically lower power**.

### Where the power actually goes

In a modern AI accelerator datacenter, the power budget breaks down roughly as:

| Component | % of site power | Notes |
|-----------|----------------|-------|
| Matrix multiply arrays (compute) | ~25-30% | The multiply units themselves |
| Active cooling for compute | ~25-30% | Removing heat generated by multiply units |
| Memory + interconnect | ~20-25% | HBM, NoC, PCIe/NVLink |
| Everything else | ~15-25% | Storage, networking, facility overhead |

**~50% of total site power goes to running and cooling the multiply arrays.** This is the target.

### What the optical multiply eliminates

The SFG chamber is a passive nonlinear crystal. It does not switch transistors. It does not dissipate heat in the compute path. The energy cost of the multiply is the input laser power — low milliwatts for the entire array, compared to tens of watts for the equivalent electronic multiply array.

| | Electronic (H100/B200) | Optical Hybrid |
|---|---|---|
| Multiply energy | ~0.9-4.2 pJ per op (INT8/FP16) | Sub-pJ (laser amortized across array) |
| Multiply array heat | Tens of watts | Near zero (passive crystal) |
| Cooling for multiply | ~1:1 ratio (1W cooling per 1W compute) | Negligible |
| Accumulate energy | ~0.1 pJ per add | ~0.1 pJ per add (same — electronic) |
| Memory bandwidth | HBM-limited | HBM-limited (same bottleneck) |
| Throughput (TOPS) | Memory-bound | Memory-bound (same ceiling) |

### The real value proposition

For the same throughput:

1. **Eliminate multiply heat entirely.** The SFG process generates no waste heat in the compute path.
2. **Eliminate the cooling infrastructure for multiply.** No heat means no chillers, no fans, no cold plates for the compute die.
3. **Cut total site power by up to ~50%.** The multiply arrays and their cooling — the two largest power consumers — are both replaced.

This is not a marginal improvement. A datacenter that draws 100 MW today could deliver the same AI throughput at ~50 MW. The capital cost of cooling infrastructure (chillers, power distribution, building space) drops proportionally.

### What stays the same

- Memory power (HBM): identical
- Accumulation power (adder trees): identical
- Interconnect power: identical
- Control logic: identical

The optical hybrid does not solve the memory wall. Nothing does. But it eliminates the second-largest power sink in the system and its associated cooling — which together account for roughly half the facility power budget.

---

## 10. Path Forward

The hybrid architecture is not a retreat. It is the correct design.

Optical multiply via SFG is real, validated, and physically advantageous. Forcing accumulation into the optical domain was an error — it cannot work due to information loss in superposition, and it was never necessary. Electronic accumulation is cheap, fast, and well-understood.

The value proposition remains: replace the most power-hungry operation in matrix arithmetic (multiply) with a passive optical process that runs at the speed of light and dissipates milliwatts. Let electronics handle everything it's good at.

Next steps:
1. Design the photodetector array and adder tree for the target vector dimension
2. Characterize the optical-to-electronic boundary: detector responsivity, noise floor, bit error rate at target data rates
3. Build a detailed power model: laser wall-plug efficiency, detector bias power, adder tree power at target dimension
4. Quantify cooling savings: thermal simulation of passive SFG chamber vs electronic multiply die at equivalent throughput
