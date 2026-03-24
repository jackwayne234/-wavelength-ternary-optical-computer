# Architecture Brainstorm — Binary Optical Computer (2026-03-21)

**Session between CJ and Claude (Barron)**

## The Problem

The original ternary 9x9 architecture requires cascaded SFG accumulation to compute dot products. Each SFG stage adds frequencies, pushing the signal from C-band (~400 THz) into UV and eventually vacuum UV (~3600 THz after 9 stages). Materials become opaque. Detection becomes impossible.

This is true regardless of cascade topology — sequential, binary tree, or ternary tree all reach the same final frequency. The math is associative.

## The Solution: Binary-First, Modular Architecture

### Start Binary

Binary inputs {-1, +1} and binary weights {-1, +1}. Even binary optical compute gives ~4,600x power improvement over an NVIDIA H100 (150 mW vs 700 W). Prove physics first, upgrade to ternary later.

### Two Separate Components

**Weighting Cube** — flat 2D chip
- 4 independent SFG/DFG lanes
- Weight = +1: SFG (frequency up)
- Weight = -1: DFG (frequency down)
- Output: 4 product frequencies

**Accumulation Cube** — 3D layered structure (2D layers bonded together)
- Binary tree: 4 inputs → 2 pairs → 1 output
- 3 SFGs (combine signals) + 2 DFGs (reset frequency between stages)
- SFG makes the routing decision (combined frequency determines path)
- DFG brings frequency back to working range before next SFG
- 5 output ports: {-4, -2, 0, +2, +4}

### SFG/DFG Interleaving

```
Level 1, Node 1:
  product_A + product_B → SFG → high freq → ROUTES → DFG → freq reset ✅

Level 1, Node 2:
  product_C + product_D → SFG → high freq → ROUTES → DFG → freq reset ✅

Level 2:
  group1 + group2 → SFG → routes to FINAL OUTPUT PORT (no DFG needed)
```

No frequency runaway. Every intermediate stays in working range.

### Spatial Output Detection

The output port determines the answer. No frequency measurement, no intensity detection. Just: "did light arrive at this port? Yes or no." The port number IS the answer.

### Chiplet Strategy

One building block: the accumulation-4 cube. Chain hierarchically:

```
[W]→[A4]  [W]→[A4]  [W]→[A4]  [W]→[A4]
    │          │          │          │
    └─────[A4]─┘          └─────[A4]─┘
              │                    │
              └───────[A4]─────────┘
                        │
                  final output
```

- 4 inputs: 1 cube
- 16 inputs: 5 cubes
- 64 inputs: 21 cubes
- 256 inputs: 85 cubes

Same fab process. Yield-based SKUs. More working cubes = higher compute tier.

## Key Insights from Session

1. **Frequency runaway is topology-independent** — tree vs sequential doesn't matter, final frequency is the same
2. **SFG/DFG interleaving** — the only solution that keeps frequencies bounded
3. **Ternary tree for future ternary version** — 9 = 3^2, perfectly balanced 2-level tree with no leftovers
4. **Spatial routing, not frequency accumulation** — the signal's PATH through the cube encodes the running sum
5. **Hardware is fixed, programming is laser frequencies** — change weights by tuning weight lasers, routing network is permanent
6. **The cube is 2D layers bonded together** — not monolithic 3D, which simplifies fabrication

## Open Questions

1. Frequency assignments for binary {-1, +1} encoding
2. DFG pump frequency selection
3. Physical routing mechanism at each SFG node
4. Signal loss through 5 nonlinear stages
5. Phase matching (PPLN periods) per stage
6. Inter-cube optical interface
7. Layer-to-layer alignment precision

## Late Session Breakthrough — Skip Optical Accumulation Entirely

### The 2×2 Simplification

CJ asked: for a 2×2 binary, do you even need the accumulation cube? With 2 lanes, each outputting to f₊ (product=+1) or f₋ (product=-1), there are only 4 possible port patterns:

| Lane 1 | Lane 2 | Pattern | Answer |
|--------|--------|---------|--------|
| f₊ (top) | f₊ (top) | both top | +2 |
| f₋ (bot) | f₋ (bot) | both bottom | -2 |
| f₊ (top) | f₋ (bot) | mixed | 0 |
| f₋ (bot) | f₊ (top) | mixed | 0 |

No accumulation cube needed. Just detect which ports lit up. The PATTERN is the answer.

### The Big Realization

CJ: "we were just counting the ports the whole time."

Every architecture we drew — the 81-port demux, the 3D routing cube, the ternary tree — they ALL ended with "which port lit up = the answer." The optical accumulation was a more complicated way of arriving at the same set of output ports. The lookup table is the same size no matter what.

For binary {-1, +1}:
- You don't need a lookup table at all
- Just count how many f₊ ports lit up, how many f₋ lit up, subtract
- That's a popcount — one of the simplest operations in electronics
- A handful of transistors

For ternary (future):
- Each lane has 6 possible product ports
- Count products in each category, weighted sum: 1×count₁ + 2×count₂ + 3×count₃ + 4×count₄ + 6×count₆ + 9×count₉
- Still trivially simple electronics

### Final Architecture (Simplest Version)

```
OPTICAL (the hard, valuable part):
  N lanes of SFG/DFG → each lane outputs to one of 2 ports → multiplication done

ELECTRONIC (the trivial part):
  Count which ports lit up → subtract → answer
```

The optical chip does massively parallel multiplication at the speed of light at milliwatts. The electronic readout does grade school subtraction. Each domain does what it's best at.

The accumulation cube is GONE. The 3D layered structure, the SFG/DFG interleaving for accumulation, the routing — all unnecessary for the proof of concept. The weighting chip + photodetectors + trivial counting = complete system.

### Why This Is Valid

- The multiplication is the hard, parallelizable, power-hungry part → optics handles it
- The accumulation is trivially simple addition → a few transistors handle it
- No intensity measurement — each port is binary (light/no light)
- No frequency measurement at the output — just presence detection
- Scales to any size: N lanes → 2N ports → popcount

### CJ's Parting Words

"We were just counting the ports the whole time. The lookup table was the same size no matter what."

The optical accumulation was solving a problem that didn't need solving optically.

## Next Steps (Updated)

1. Start with 2×2 binary proof of concept — weighting chip only + 4 detectors
2. Pick frequency assignments for binary {-1, +1} encoding
3. Run full signal chain math for the simplest case
4. Consider whether optical accumulation adds value at larger scales, or if electronic counting always wins

## Drawings

- `drawings/IMG_0205_9x9_chip_layout.jpg` — CJ's hand drawing of the 9x9 chip layout
- `drawings/IMG_0206_weighted_cube_solved.jpg` — CJ's hand drawing of weighting cube, accumulation cube (3 SFGs binary tree), and output cube
