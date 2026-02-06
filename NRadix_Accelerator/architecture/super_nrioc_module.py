#!/usr/bin/env python3
"""
Super NR-IOC Module for Optical Systolic Array

Enhanced Input/Output Converter serving as the HOST INTERFACE for the optical system.

=============================================================================
NEW ARCHITECTURE: OPTICAL RAM WEIGHT STREAMING
=============================================================================

Key insight: Weights are stored in the CPU's 3-tier optical RAM system and
STREAMED to the PE array through this NR-IOC module. This eliminates the need
for per-PE weight storage and keeps data in the optical domain throughout.

Data Flow:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   HOST (Electronic)                                                         │
│      │                                                                       │
│      │ PCIe/USB (binary data)                                               │
│      ▼                                                                       │
│   ┌──────────────────┐                                                      │
│   │     NR-IOC       │  ◄── THIS MODULE                                    │
│   │  (Host Interface)│      - Electronic-to-optical conversion             │
│   │                  │      - Format conversion (binary → ternary)         │
│   │                  │      - Timing/clock synchronization                  │
│   └────────┬─────────┘                                                      │
│            │                                                                 │
│            │ OPTICAL (stays optical from here)                              │
│            ▼                                                                 │
│   ┌──────────────────┐                                                      │
│   │   CPU OPTICAL    │  ◄── Weight storage lives HERE                      │
│   │   RAM (3-tier)   │      - L1: Ring resonator cache                     │
│   │                  │      - L2: Delay line buffer                         │
│   │                  │      - L3: Large optical storage                     │
│   └────────┬─────────┘                                                      │
│            │                                                                 │
│            │ OPTICAL (weights stream out)                                   │
│            ▼                                                                 │
│   ┌──────────────────┐                                                      │
│   │  PE ARRAY        │  ◄── Weights arrive optically, compute optically   │
│   │  (81×81)         │      No E/O conversion for weights!                 │
│   └──────────────────┘                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

Why this matters:
1. Weights stay OPTICAL from RAM through compute - no E/O/E conversion penalty
2. NR-IOC only converts at HOST BOUNDARY (once, not per-PE)
3. CPU's existing 3-tier RAM becomes weight storage (no new memory needed)
4. Streaming enables arbitrary model sizes (not limited by PE storage)

Module components:
- Weight Serializer: Reads from optical RAM, serializes for distribution tree
- Weight Distribution Tree: Broadcasts optical weights to PE columns
- Activation Streamer: 81-channel parallel input @ 617 MHz (from host)
- Result Collector: 81-channel parallel output with accumulation (to host)
- Clock Interface: Kerr resonator 617 MHz distribution

Throughput: 50 Gtrits/s input, 50 Gtrits/s output
Latency: ~160 ns (array propagation) + ~10 ns (IOC overhead)

Author: Wavelength-Division Ternary Optical Computer Project
"""

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.typings import LayerSpec
import numpy as np
from typing import Optional, Literal, Tuple, List
import os

# Activate PDK
gf.gpdk.PDK.activate()

# =============================================================================
# Layer Definitions
# =============================================================================

LAYER_WAVEGUIDE: LayerSpec = (1, 0)
LAYER_HEATER: LayerSpec = (10, 0)
LAYER_CARRY: LayerSpec = (11, 0)
LAYER_METAL_PAD: LayerSpec = (12, 0)
LAYER_LOG: LayerSpec = (13, 0)
LAYER_EXP: LayerSpec = (14, 0)
LAYER_AWG: LayerSpec = (15, 0)
LAYER_DETECTOR: LayerSpec = (16, 0)
LAYER_LASER: LayerSpec = (17, 0)
LAYER_BUFFER: LayerSpec = (18, 0)
LAYER_MUX: LayerSpec = (19, 0)
LAYER_BUS: LayerSpec = (20, 0)
LAYER_SERIAL: LayerSpec = (21, 0)
LAYER_CLOCK: LayerSpec = (22, 0)
LAYER_DMA: LayerSpec = (23, 0)
LAYER_TEXT: LayerSpec = (100, 0)

# =============================================================================
# Constants
# =============================================================================

WAVEGUIDE_WIDTH = 0.5
BEND_RADIUS = 5.0
CLOCK_FREQ_MHZ = 617
ARRAY_SIZE = 81
TOTAL_PES = ARRAY_SIZE * ARRAY_SIZE  # 6,561
TRITS_PER_VALUE = 9

# Unique ID generator
_uid_counter = 0
def _uid() -> str:
    global _uid_counter
    _uid_counter += 1
    return f"{_uid_counter:05d}"


# =============================================================================
# Weight Loader Unit
# =============================================================================

@gf.cell
def weight_serializer() -> Component:
    """
    Optical Weight Serializer - Reads from CPU's Optical RAM

    NEW ARCHITECTURE: This component interfaces with the CPU's 3-tier optical
    RAM system to read weights and serialize them for distribution to PEs.

    Key design principle: Weights stay OPTICAL throughout.
    - Input: Optical signal from CPU's RAM (not electronic!)
    - Output: Serialized optical stream @ 617 MHz

    The serializer:
    1. Receives optical weight data from CPU's L1/L2/L3 optical RAM
    2. Buffers in optical delay lines (ring resonators)
    3. Serializes via time-division multiplexing
    4. Outputs timed pulses synchronized to Kerr clock

    This is NOT an E/O converter - it's an optical-to-optical formatter.
    E/O conversion only happens at the host boundary (in the NR-IOC host interface).
    """
    c = gf.Component()

    width = 200
    height = 120

    # Main block
    c.add_polygon([(0, 0), (width, 0), (width, height), (0, height)], layer=LAYER_SERIAL)

    # ==========================================================================
    # OPTICAL INPUT from CPU RAM (NOT electronic!)
    # ==========================================================================

    # Optical input bus from CPU's optical RAM
    c.add_polygon([(-30, height/2-10), (0, height/2-10),
                   (0, height/2+10), (-30, height/2+10)], layer=LAYER_WAVEGUIDE)
    c.add_label("FROM CPU", position=(-45, height/2+15), layer=LAYER_TEXT)
    c.add_label("OPT RAM", position=(-45, height/2-5), layer=LAYER_TEXT)

    # ==========================================================================
    # Internal optical buffer (ring resonators for timing)
    # ==========================================================================

    # Ring resonator buffer array (holds optical data for serialization)
    for i in range(4):
        x = 30 + i * 35
        y = height/2
        # Small ring resonator
        c.add_polygon([(x, y-12), (x+25, y-12), (x+25, y+12), (x, y+12)], layer=LAYER_CARRY)
        c.add_label(f"R{i}", position=(x+12, y), layer=LAYER_TEXT)

    c.add_label("OPTICAL BUFFER", position=(width/2, height - 20), layer=LAYER_TEXT)
    c.add_label("(Ring Resonators)", position=(width/2, height - 35), layer=LAYER_TEXT)

    # ==========================================================================
    # Serialized optical output
    # ==========================================================================

    # Serial output (optical waveguide)
    c.add_polygon([(width, height/2-2), (width+30, height/2-2),
                   (width+30, height/2+2), (width, height/2+2)], layer=LAYER_WAVEGUIDE)
    c.add_label("SER OUT", position=(width+45, height/2), layer=LAYER_TEXT)

    # Clock input (for timing synchronization)
    c.add_polygon([(width/2-10, -15), (width/2+10, -15),
                   (width/2+10, 0), (width/2-10, 0)], layer=LAYER_CLOCK)
    c.add_label("CLK", position=(width/2, -25), layer=LAYER_TEXT)

    # Read address (from controller - which RAM address to read)
    c.add_polygon([(width-40, height), (width-10, height),
                   (width-10, height+15), (width-40, height+15)], layer=LAYER_METAL_PAD)
    c.add_label("ADDR", position=(width-25, height+25), layer=LAYER_TEXT)

    # Labels
    c.add_label("WEIGHT", position=(width/2, 30), layer=LAYER_TEXT)
    c.add_label("SERIALIZER", position=(width/2, 15), layer=LAYER_TEXT)
    c.add_label("(Optical Domain)", position=(width/2, 0), layer=LAYER_TEXT)

    # ==========================================================================
    # Ports
    # ==========================================================================

    # Optical input from CPU RAM (this is the key change!)
    c.add_port("opt_ram_in", center=(-30, height/2), width=20, orientation=180, layer=LAYER_WAVEGUIDE)
    # Serialized optical output
    c.add_port("ser_out", center=(width+30, height/2), width=WAVEGUIDE_WIDTH, orientation=0, layer=LAYER_WAVEGUIDE)
    # Clock
    c.add_port("clk", center=(width/2, -7.5), width=20, orientation=270, layer=LAYER_CLOCK)
    # Address control (electronic - tells which weight to read)
    c.add_port("addr", center=(width-25, height+7.5), width=30, orientation=90, layer=LAYER_METAL_PAD)

    return c


@gf.cell
def weight_distribution_tree(n_outputs: int = 81) -> Component:
    """
    Optical Weight Distribution Tree - Broadcasts from CPU RAM to PE Array

    NEW ARCHITECTURE: This tree distributes OPTICAL weights from the CPU's
    optical RAM to the PE array columns. The weights never leave the optical
    domain between RAM and compute.

    Data flow:
    ┌─────────────────────────────────────────────────────────────────┐
    │  CPU Optical RAM                                                 │
    │       │                                                          │
    │       │ (optical waveguide)                                     │
    │       ▼                                                          │
    │  Weight Serializer                                              │
    │       │                                                          │
    │       │ (serialized optical stream)                             │
    │       ▼                                                          │
    │  ┌─────────────────────────────────────┐                        │
    │  │   WEIGHT DISTRIBUTION TREE          │ ◄── THIS COMPONENT    │
    │  │   (1-to-81 optical splitter)        │                        │
    │  │                                     │                        │
    │  │   Input: Single optical stream      │                        │
    │  │   Output: 81 synchronized copies    │                        │
    │  │                                     │                        │
    │  │   Uses cascaded Y-junctions with    │                        │
    │  │   SOAs for loss compensation        │                        │
    │  └──────────────┬──────────────────────┘                        │
    │                 │                                                │
    │     ┌───────────┼───────────┐                                   │
    │     ▼           ▼           ▼                                   │
    │   Col 0       Col 1  ...  Col 80                                │
    │     │           │           │                                    │
    │     ▼           ▼           ▼                                    │
    │   PE Array (weights arrive optically!)                          │
    └─────────────────────────────────────────────────────────────────┘

    Key insight: By keeping weights optical from RAM through distribution,
    we eliminate 81 E/O conversions per weight. The only E/O conversion
    happens once at the host boundary when weights first enter the system.

    Uses cascaded Y-junctions for equal power splitting, with SOAs
    at each stage to compensate for splitting losses.
    """
    c = gf.Component()

    # Calculate tree depth (log2 for binary splitting)
    depth = int(np.ceil(np.log2(n_outputs)))

    stage_width = 50
    total_width = depth * stage_width + 80  # Extra space for labels
    total_height = n_outputs * 5

    # ==========================================================================
    # Tree structure visualization
    # ==========================================================================

    # Main tree body
    c.add_polygon([(0, total_height/2 - 25), (total_width - 30, total_height/2 - 25),
                   (total_width - 30, total_height/2 + 25), (0, total_height/2 + 25)], layer=LAYER_BUS)

    # ==========================================================================
    # OPTICAL INPUT (from CPU RAM via serializer)
    # ==========================================================================

    # Input waveguide (optical - from weight serializer which reads CPU RAM)
    c.add_polygon([(-30, total_height/2 - WAVEGUIDE_WIDTH/2), (0, total_height/2 - WAVEGUIDE_WIDTH/2),
                   (0, total_height/2 + WAVEGUIDE_WIDTH/2), (-30, total_height/2 + WAVEGUIDE_WIDTH/2)],
                  layer=LAYER_WAVEGUIDE)
    c.add_label("FROM", position=(-45, total_height/2 + 12), layer=LAYER_TEXT)
    c.add_label("OPT RAM", position=(-45, total_height/2 - 8), layer=LAYER_TEXT)

    # ==========================================================================
    # Output waveguides to PE columns (all optical!)
    # ==========================================================================

    output_spacing = total_height / n_outputs
    for i in range(n_outputs):
        y = output_spacing * (i + 0.5)
        c.add_polygon([(total_width - 30, y - WAVEGUIDE_WIDTH/2), (total_width + 15, y - WAVEGUIDE_WIDTH/2),
                       (total_width + 15, y + WAVEGUIDE_WIDTH/2), (total_width - 30, y + WAVEGUIDE_WIDTH/2)],
                      layer=LAYER_WAVEGUIDE)
        c.add_port(f"out_{i}", center=(total_width + 15, y), width=WAVEGUIDE_WIDTH,
                   orientation=0, layer=LAYER_WAVEGUIDE)

    # Label outputs
    c.add_label("TO PE", position=(total_width + 30, total_height/2 + 20), layer=LAYER_TEXT)
    c.add_label("COLS", position=(total_width + 30, total_height/2), layer=LAYER_TEXT)
    c.add_label("[0:80]", position=(total_width + 30, total_height/2 - 20), layer=LAYER_TEXT)

    # ==========================================================================
    # SOAs for loss compensation (critical for maintaining signal integrity)
    # ==========================================================================

    for stage in range(depth):
        x = stage * stage_width + 25
        c.add_polygon([(x, total_height/2 - 15), (x + 20, total_height/2 - 15),
                       (x + 20, total_height/2 + 15), (x, total_height/2 + 15)], layer=LAYER_EXP)
        c.add_label("SOA", position=(x + 10, total_height/2), layer=LAYER_TEXT)

    # ==========================================================================
    # Labels
    # ==========================================================================

    c.add_label(f"OPTICAL 1:{n_outputs} DISTRIBUTION TREE", position=(total_width/2 - 15, total_height/2 + 40), layer=LAYER_TEXT)
    c.add_label("(Weights from CPU RAM → PE Array)", position=(total_width/2 - 15, total_height/2 - 40), layer=LAYER_TEXT)

    # ==========================================================================
    # Ports
    # ==========================================================================

    # Optical input from weight serializer (which reads CPU optical RAM)
    c.add_port("opt_in", center=(-30, total_height/2), width=WAVEGUIDE_WIDTH, orientation=180, layer=LAYER_WAVEGUIDE)

    return c


@gf.cell
def weight_loader_unit() -> Component:
    """
    Weight Streaming Unit - Streams from CPU Optical RAM to PE Array

    NEW ARCHITECTURE: This unit streams weights FROM the CPU's optical RAM
    TO the PE array. Weights stay optical throughout - no per-PE storage needed.

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                     WEIGHT STREAMING UNIT                                │
    │                                                                          │
    │   ┌────────────────┐                                                    │
    │   │  CPU OPTICAL   │  ◄── Weights stored here (3-tier optical RAM)     │
    │   │  RAM INTERFACE │      - Already optical, no conversion needed       │
    │   │                │      - L1/L2/L3 hierarchy for speed/capacity       │
    │   └───────┬────────┘                                                    │
    │           │ optical                                                      │
    │           ▼                                                              │
    │   ┌────────────────┐                                                    │
    │   │ WEIGHT         │  ◄── Reads optical weights, serializes timing     │
    │   │ SERIALIZER     │                                                    │
    │   └───────┬────────┘                                                    │
    │           │ optical                                                      │
    │           ▼                                                              │
    │   ┌────────────────┐      ┌──────┐                                      │
    │   │ DISTRIBUTION   │──────│ Col 0│──► PE[0,*]                           │
    │   │ TREE           │──────│ Col 1│──► PE[1,*]                           │
    │   │ (1:81 optical) │ ...  │ ...  │                                      │
    │   │                │──────│Col 80│──► PE[80,*]                          │
    │   └────────────────┘      └──────┘                                      │
    │                                                                          │
    │   Key: All arrows are OPTICAL waveguides, not electrical!               │
    └─────────────────────────────────────────────────────────────────────────┘

    Streaming model:
    - Weights stream continuously from optical RAM
    - Each PE receives its weight at the right time (pipelined)
    - No need to "load" weights - they're always flowing
    - Arbitrary model size supported (not limited by PE registers)

    Streaming time @ 617 MHz for 6,561 weights × 9 trits = ~96 μs per full refresh
    """
    c = gf.Component()

    width = 900
    height = 700

    # Background
    c.add_polygon([(0, 0), (width, 0), (width, height), (0, height)], layer=LAYER_BUS)

    # ==========================================================================
    # Title
    # ==========================================================================

    c.add_label("WEIGHT STREAMING UNIT", position=(width/2, height - 20), layer=LAYER_TEXT)
    c.add_label("Optical RAM → PE Array (all optical)", position=(width/2, height - 45), layer=LAYER_TEXT)

    # ==========================================================================
    # CPU Optical RAM Interface (left side) - THIS IS THE KEY CHANGE
    # ==========================================================================

    c.add_polygon([(20, height/2 - 120), (150, height/2 - 120),
                   (150, height/2 + 120), (20, height/2 + 120)], layer=LAYER_CARRY)
    c.add_label("CPU", position=(85, height/2 + 80), layer=LAYER_TEXT)
    c.add_label("OPTICAL", position=(85, height/2 + 50), layer=LAYER_TEXT)
    c.add_label("RAM", position=(85, height/2 + 20), layer=LAYER_TEXT)
    c.add_label("INTERFACE", position=(85, height/2 - 10), layer=LAYER_TEXT)

    # Show the 3-tier hierarchy
    c.add_polygon([(30, height/2 - 100), (140, height/2 - 100),
                   (140, height/2 - 60), (30, height/2 - 60)], layer=LAYER_BUFFER)
    c.add_label("L1: Ring", position=(85, height/2 - 80), layer=LAYER_TEXT)

    c.add_polygon([(30, height/2 - 55), (140, height/2 - 55),
                   (140, height/2 - 15), (30, height/2 - 15)], layer=LAYER_BUFFER)
    c.add_label("L2: Delay", position=(85, height/2 - 35), layer=LAYER_TEXT)

    # Optical waveguide from RAM (NOT electronic!)
    c.add_polygon([(150, height/2 - 5), (180, height/2 - 5),
                   (180, height/2 + 5), (150, height/2 + 5)], layer=LAYER_WAVEGUIDE)
    c.add_label("OPT", position=(165, height/2 + 20), layer=LAYER_TEXT)

    # ==========================================================================
    # Weight serializer (now reads optical, not electronic)
    # ==========================================================================

    serializer = c << weight_serializer()
    serializer.dmove((200, height/2 - 60))

    # ==========================================================================
    # Distribution tree (optical broadcast to all columns)
    # ==========================================================================

    tree = c << weight_distribution_tree(n_outputs=81)
    tree.dmove((480, height/2 - 200))

    # ==========================================================================
    # Address/control logic (electronic - just coordinates, not data)
    # ==========================================================================

    c.add_polygon([(200, 80), (350, 80), (350, 180), (200, 180)], layer=LAYER_METAL_PAD)
    c.add_label("ADDRESS", position=(275, 150), layer=LAYER_TEXT)
    c.add_label("GENERATOR", position=(275, 120), layer=LAYER_TEXT)
    c.add_label("(Electronic)", position=(275, 95), layer=LAYER_TEXT)

    # Row sequencer
    c.add_polygon([(380, 80), (480, 80), (480, 160), (380, 160)], layer=LAYER_MUX)
    c.add_label("ROW", position=(430, 135), layer=LAYER_TEXT)
    c.add_label("SEQ", position=(430, 105), layer=LAYER_TEXT)

    # Status indicators
    c.add_polygon([(750, 80), (870, 80), (870, 140), (750, 140)], layer=LAYER_METAL_PAD)
    c.add_label("STREAM", position=(810, 120), layer=LAYER_TEXT)
    c.add_label("STATUS", position=(810, 95), layer=LAYER_TEXT)

    # ==========================================================================
    # Documentation box explaining the architecture
    # ==========================================================================

    c.add_polygon([(20, 20), (350, 20), (350, 70), (20, 70)], layer=LAYER_METAL_PAD)
    c.add_label("Note: Data path is ALL OPTICAL", position=(185, 55), layer=LAYER_TEXT)
    c.add_label("Only control signals are electronic", position=(185, 35), layer=LAYER_TEXT)

    # ==========================================================================
    # Ports
    # ==========================================================================

    # Optical input from CPU RAM (this replaces the old electronic host_data)
    c.add_port("cpu_ram_optical", center=(0, height/2), width=20, orientation=180, layer=LAYER_WAVEGUIDE)

    # Electronic control (addresses, not data)
    c.add_port("ctrl", center=(0, height/2 - 180), width=50, orientation=180, layer=LAYER_METAL_PAD)

    # Weight outputs to array (right side) - all optical
    for i in range(81):
        y = 120 + i * 5
        c.add_port(f"weight_col_{i}", center=(width, y), width=WAVEGUIDE_WIDTH,
                   orientation=0, layer=LAYER_WAVEGUIDE)

    c.add_port("clk_in", center=(width/2, 0), width=20, orientation=270, layer=LAYER_CLOCK)
    c.add_port("status", center=(810, 0), width=50, orientation=270, layer=LAYER_METAL_PAD)

    return c


# =============================================================================
# Activation Streamer
# =============================================================================

@gf.cell
def activation_channel() -> Component:
    """
    Single activation input channel with timing alignment.

    Includes:
    - Photodetector (if from electronic source)
    - Laser modulator (if generating optical)
    - Delay line for timing alignment
    - SOA for signal conditioning
    """
    c = gf.Component()

    width = 120
    height = 25

    # Channel body
    c.add_polygon([(0, 0), (width, 0), (width, height), (0, height)], layer=LAYER_BUFFER)

    # E/O converter (laser + modulator)
    c.add_polygon([(5, 5), (35, 5), (35, 20), (5, 20)], layer=LAYER_LASER)
    c.add_label("E/O", position=(20, 12), layer=LAYER_TEXT)

    # Delay line (tunable)
    c.add_polygon([(40, 8), (80, 8), (80, 17), (40, 17)], layer=LAYER_WAVEGUIDE)
    c.add_label("DLY", position=(60, 12), layer=LAYER_TEXT)

    # SOA
    c.add_polygon([(85, 5), (110, 5), (110, 20), (85, 20)], layer=LAYER_EXP)
    c.add_label("SOA", position=(97, 12), layer=LAYER_TEXT)

    # Input (electronic)
    c.add_polygon([(-15, height/2 - 5), (0, height/2 - 5),
                   (0, height/2 + 5), (-15, height/2 + 5)], layer=LAYER_METAL_PAD)

    # Output (optical)
    c.add_polygon([(width, height/2 - WAVEGUIDE_WIDTH/2), (width + 15, height/2 - WAVEGUIDE_WIDTH/2),
                   (width + 15, height/2 + WAVEGUIDE_WIDTH/2), (width, height/2 + WAVEGUIDE_WIDTH/2)],
                  layer=LAYER_WAVEGUIDE)

    # Ports
    c.add_port("elec_in", center=(-7.5, height/2), width=10, orientation=180, layer=LAYER_METAL_PAD)
    c.add_port("opt_out", center=(width + 15, height/2), width=WAVEGUIDE_WIDTH, orientation=0, layer=LAYER_WAVEGUIDE)
    c.add_port("delay_ctrl", center=(60, 0), width=10, orientation=270, layer=LAYER_HEATER)

    return c


@gf.cell
def double_buffer_81ch() -> Component:
    """
    81-channel double buffer for ping-pong operation.

    Buffer A: Currently being read (sent to array)
    Buffer B: Currently being written (from host)

    Eliminates stalls - seamless continuous streaming.
    """
    c = gf.Component()

    width = 300
    height = 500

    # Main body
    c.add_polygon([(0, 0), (width, 0), (width, height), (0, height)], layer=LAYER_BUFFER)

    # Buffer A (top half)
    c.add_polygon([(20, height/2 + 20), (width - 20, height/2 + 20),
                   (width - 20, height - 20), (20, height - 20)], layer=LAYER_CARRY)
    c.add_label("BUFFER A", position=(width/2, height * 3/4), layer=LAYER_TEXT)
    c.add_label("(READ)", position=(width/2, height * 3/4 - 20), layer=LAYER_TEXT)

    # Buffer B (bottom half)
    c.add_polygon([(20, 20), (width - 20, 20),
                   (width - 20, height/2 - 20), (20, height/2 - 20)], layer=LAYER_CARRY)
    c.add_label("BUFFER B", position=(width/2, height/4), layer=LAYER_TEXT)
    c.add_label("(WRITE)", position=(width/2, height/4 - 20), layer=LAYER_TEXT)

    # Crossbar switch in middle
    c.add_polygon([(width/2 - 40, height/2 - 15), (width/2 + 40, height/2 - 15),
                   (width/2 + 40, height/2 + 15), (width/2 - 40, height/2 + 15)], layer=LAYER_MUX)
    c.add_label("SWAP", position=(width/2, height/2), layer=LAYER_TEXT)

    # Title
    c.add_label("DOUBLE BUFFER", position=(width/2, height - 5), layer=LAYER_TEXT)
    c.add_label("81 channels × 9 trits × 2", position=(width/2, 10), layer=LAYER_TEXT)

    # Input ports (left - from host)
    for i in range(0, 81, 10):  # Show every 10th
        y = 30 + i * 5
        c.add_polygon([(-10, y), (0, y), (0, y + 3), (-10, y + 3)], layer=LAYER_METAL_PAD)
    c.add_label("FROM", position=(-25, height/4), layer=LAYER_TEXT)
    c.add_label("HOST", position=(-25, height/4 - 15), layer=LAYER_TEXT)

    # Output ports (right - to array)
    for i in range(0, 81, 10):
        y = 30 + i * 5
        c.add_polygon([(width, y), (width + 10, y), (width + 10, y + 3), (width, y + 3)], layer=LAYER_WAVEGUIDE)
    c.add_label("TO", position=(width + 25, height/4), layer=LAYER_TEXT)
    c.add_label("ARRAY", position=(width + 25, height/4 - 15), layer=LAYER_TEXT)

    # Control
    c.add_polygon([(width/2 - 25, height + 10), (width/2 + 25, height + 10),
                   (width/2 + 25, height + 30), (width/2 - 25, height + 30)], layer=LAYER_METAL_PAD)
    c.add_label("SWAP_SEL", position=(width/2, height + 40), layer=LAYER_TEXT)

    # Ports
    c.add_port("data_in", center=(0, height/4), width=50, orientation=180, layer=LAYER_METAL_PAD)
    c.add_port("data_out", center=(width, height/4), width=50, orientation=0, layer=LAYER_WAVEGUIDE)
    c.add_port("swap_ctrl", center=(width/2, height + 20), width=50, orientation=90, layer=LAYER_METAL_PAD)

    return c


@gf.cell
def activation_streamer_unit() -> Component:
    """
    Complete activation streaming unit with 81 parallel channels.

    Features:
    - 81 parallel E/O converters
    - Programmable delay lines for systolic timing
    - Double-buffered input (no stalls)
    - SOA conditioning per channel

    Throughput: 81 × 617 MHz × 9 trits = 450 Gtrits/s
    """
    c = gf.Component()

    width = 700
    height = 550

    # Background
    c.add_polygon([(0, 0), (width, 0), (width, height), (0, height)], layer=LAYER_BUS)

    # Title
    c.add_label("ACTIVATION STREAMER UNIT", position=(width/2, height - 20), layer=LAYER_TEXT)
    c.add_label("81 channels @ 617 MHz = 50 Gtrits/s", position=(width/2, height - 40), layer=LAYER_TEXT)

    # Double buffer
    dbuf = c << double_buffer_81ch()
    dbuf.dmove((50, 30))

    # 81 activation channels (show subset for clarity)
    channel_y_start = 50
    channel_spacing = 6

    for i in range(81):
        y = channel_y_start + i * channel_spacing

        # Simplified channel representation
        c.add_polygon([(380, y), (580, y), (580, y + 4), (380, y + 4)], layer=LAYER_BUFFER)

        # Timing delay indicator
        if i % 9 == 0:  # Label every 9th
            c.add_label(f"CH{i}", position=(600, y + 2), layer=LAYER_TEXT)

    # Staggered delay pattern visualization
    c.add_polygon([(420, 50), (450, 50), (450, 530), (420, 530)], layer=LAYER_HEATER)
    c.add_label("TIMING", position=(435, 540), layer=LAYER_TEXT)
    c.add_label("SKEW", position=(435, 35), layer=LAYER_TEXT)

    # SOA bank
    c.add_polygon([(500, 50), (560, 50), (560, 530), (500, 530)], layer=LAYER_EXP)
    c.add_label("SOA", position=(530, height/2 + 10), layer=LAYER_TEXT)
    c.add_label("BANK", position=(530, height/2 - 10), layer=LAYER_TEXT)

    # Timing controller
    c.add_polygon([(420, height - 80), (560, height - 80), (560, height - 50), (420, height - 50)],
                  layer=LAYER_METAL_PAD)
    c.add_label("TIMING CTRL", position=(490, height - 65), layer=LAYER_TEXT)

    # Ports
    c.add_port("host_data", center=(0, height/4), width=100, orientation=180, layer=LAYER_METAL_PAD)
    c.add_port("clk_in", center=(width/2, 0), width=20, orientation=270, layer=LAYER_CLOCK)

    # Output ports to array
    for i in range(81):
        y = channel_y_start + i * channel_spacing + 2
        c.add_port(f"act_out_{i}", center=(width, y), width=WAVEGUIDE_WIDTH,
                   orientation=0, layer=LAYER_WAVEGUIDE)

    c.add_port("timing_cfg", center=(490, height), width=80, orientation=90, layer=LAYER_METAL_PAD)

    return c


# =============================================================================
# Result Collector
# =============================================================================

@gf.cell
def result_channel() -> Component:
    """
    Single result output channel.

    Includes:
    - Photodetector array (5-level for ternary)
    - TIA (transimpedance amplifier)
    - ADC interface
    """
    c = gf.Component()

    width = 100
    height = 25

    # Channel body
    c.add_polygon([(0, 0), (width, 0), (width, height), (0, height)], layer=LAYER_BUFFER)

    # Optical input
    c.add_polygon([(-15, height/2 - WAVEGUIDE_WIDTH/2), (0, height/2 - WAVEGUIDE_WIDTH/2),
                   (0, height/2 + WAVEGUIDE_WIDTH/2), (-15, height/2 + WAVEGUIDE_WIDTH/2)],
                  layer=LAYER_WAVEGUIDE)

    # Photodetector
    c.add_polygon([(5, 5), (30, 5), (30, 20), (5, 20)], layer=LAYER_DETECTOR)
    c.add_label("PD", position=(17, 12), layer=LAYER_TEXT)

    # TIA
    c.add_polygon([(35, 5), (60, 5), (60, 20), (35, 20)], layer=LAYER_METAL_PAD)
    c.add_label("TIA", position=(47, 12), layer=LAYER_TEXT)

    # Output buffer
    c.add_polygon([(65, 5), (95, 5), (95, 20), (65, 20)], layer=LAYER_METAL_PAD)
    c.add_label("BUF", position=(80, 12), layer=LAYER_TEXT)

    # Electronic output
    c.add_polygon([(width, height/2 - 5), (width + 15, height/2 - 5),
                   (width + 15, height/2 + 5), (width, height/2 + 5)], layer=LAYER_METAL_PAD)

    # Ports
    c.add_port("opt_in", center=(-15, height/2), width=WAVEGUIDE_WIDTH, orientation=180, layer=LAYER_WAVEGUIDE)
    c.add_port("elec_out", center=(width + 7.5, height/2), width=10, orientation=0, layer=LAYER_METAL_PAD)

    return c


@gf.cell
def accumulator_bank_81ch() -> Component:
    """
    81-channel accumulator bank for batch accumulation.

    Accumulates results across multiple compute cycles
    for operations like batch matrix multiply.
    """
    c = gf.Component()

    width = 200
    height = 500

    # Main body
    c.add_polygon([(0, 0), (width, 0), (width, height), (0, height)], layer=LAYER_BUFFER)

    # 81 accumulator cells
    cell_height = height / 81
    for i in range(81):
        y = i * cell_height
        c.add_polygon([(10, y + 1), (width - 10, y + 1),
                       (width - 10, y + cell_height - 1), (10, y + cell_height - 1)],
                      layer=LAYER_CARRY)

    c.add_label("ACCUMULATOR", position=(width/2, height + 15), layer=LAYER_TEXT)
    c.add_label("BANK [80:0]", position=(width/2, height + 5), layer=LAYER_TEXT)

    # Clear control
    c.add_polygon([(width/2 - 30, -25), (width/2 + 30, -25),
                   (width/2 + 30, -5), (width/2 - 30, -5)], layer=LAYER_METAL_PAD)
    c.add_label("ACC_CLR", position=(width/2, -35), layer=LAYER_TEXT)

    # Ports
    c.add_port("data_in", center=(0, height/2), width=50, orientation=180, layer=LAYER_WAVEGUIDE)
    c.add_port("data_out", center=(width, height/2), width=50, orientation=0, layer=LAYER_METAL_PAD)
    c.add_port("clear", center=(width/2, -15), width=60, orientation=270, layer=LAYER_METAL_PAD)

    return c


@gf.cell
def result_collector_unit() -> Component:
    """
    Complete result collection unit with 81 parallel channels.

    Features:
    - 81 parallel O/E converters (photodetectors + TIAs)
    - Optional accumulation across batches
    - Format conversion (ternary to binary)
    - DMA interface to host

    Throughput: 81 × 617 MHz × 9 trits = 450 Gtrits/s
    """
    c = gf.Component()

    width = 700
    height = 550

    # Background
    c.add_polygon([(0, 0), (width, 0), (width, height), (0, height)], layer=LAYER_BUS)

    # Title
    c.add_label("RESULT COLLECTOR UNIT", position=(width/2, height - 20), layer=LAYER_TEXT)
    c.add_label("81 channels @ 617 MHz = 50 Gtrits/s", position=(width/2, height - 40), layer=LAYER_TEXT)

    # Input channels (from array)
    channel_y_start = 50
    channel_spacing = 6

    for i in range(81):
        y = channel_y_start + i * channel_spacing

        # Simplified channel
        c.add_polygon([(50, y), (200, y), (200, y + 4), (50, y + 4)], layer=LAYER_BUFFER)

        if i % 9 == 0:
            c.add_label(f"CH{i}", position=(30, y + 2), layer=LAYER_TEXT)

    # Photodetector bank
    c.add_polygon([(70, 50), (120, 50), (120, 530), (70, 530)], layer=LAYER_DETECTOR)
    c.add_label("PD", position=(95, height/2 + 10), layer=LAYER_TEXT)
    c.add_label("ARRAY", position=(95, height/2 - 10), layer=LAYER_TEXT)

    # TIA bank
    c.add_polygon([(130, 50), (180, 50), (180, 530), (130, 530)], layer=LAYER_METAL_PAD)
    c.add_label("TIA", position=(155, height/2 + 10), layer=LAYER_TEXT)
    c.add_label("BANK", position=(155, height/2 - 10), layer=LAYER_TEXT)

    # Accumulator bank
    acc_bank = c << accumulator_bank_81ch()
    acc_bank.dmove((220, 30))

    # Format converter (ternary to binary)
    c.add_polygon([(450, 100), (550, 100), (550, 450), (450, 450)], layer=LAYER_MUX)
    c.add_label("TRIT→BIN", position=(500, height/2 + 20), layer=LAYER_TEXT)
    c.add_label("CONVERT", position=(500, height/2 - 20), layer=LAYER_TEXT)

    # DMA interface
    c.add_polygon([(580, 150), (680, 150), (680, 400), (580, 400)], layer=LAYER_DMA)
    c.add_label("DMA", position=(630, height/2 + 20), layer=LAYER_TEXT)
    c.add_label("ENGINE", position=(630, height/2 - 20), layer=LAYER_TEXT)

    # Ports - inputs from array
    for i in range(81):
        y = channel_y_start + i * channel_spacing + 2
        c.add_port(f"result_in_{i}", center=(0, y), width=WAVEGUIDE_WIDTH,
                   orientation=180, layer=LAYER_WAVEGUIDE)

    c.add_port("host_data", center=(width, height/2), width=100, orientation=0, layer=LAYER_DMA)
    c.add_port("clk_in", center=(width/2, 0), width=20, orientation=270, layer=LAYER_CLOCK)
    c.add_port("acc_clear", center=(320, 0), width=40, orientation=270, layer=LAYER_METAL_PAD)

    return c


# =============================================================================
# Clock Distribution
# =============================================================================

@gf.cell
def kerr_clock_source() -> Component:
    """
    Kerr resonator clock source at 617 MHz.

    Self-pulsing Kerr ring generates optical clock
    that synchronizes entire system.
    """
    c = gf.Component()

    radius = 80

    # Kerr ring
    n_points = 64
    angles = np.linspace(0, 2*np.pi, n_points)

    outer_points = [(radius * np.cos(a), radius * np.sin(a)) for a in angles]
    c.add_polygon(outer_points, layer=LAYER_CLOCK)

    inner_points = [((radius - 15) * np.cos(a), (radius - 15) * np.sin(a)) for a in angles]
    # Inner void would be air - represented by not filling

    # Coupling waveguide
    c.add_polygon([(-radius - 30, -5), (-radius + 10, -5),
                   (-radius + 10, 5), (-radius - 30, 5)], layer=LAYER_WAVEGUIDE)

    # Pump input
    c.add_polygon([(-radius - 30, -50), (-radius - 10, -50),
                   (-radius - 10, -20), (-radius - 30, -20)], layer=LAYER_LASER)
    c.add_label("PUMP", position=(-radius - 20, -60), layer=LAYER_TEXT)

    # Clock output
    c.add_polygon([(radius - 10, -5), (radius + 50, -5),
                   (radius + 50, 5), (radius - 10, 5)], layer=LAYER_WAVEGUIDE)

    c.add_label("KERR", position=(0, 20), layer=LAYER_TEXT)
    c.add_label("617 MHz", position=(0, 0), layer=LAYER_TEXT)
    c.add_label("CLOCK", position=(0, -20), layer=LAYER_TEXT)

    # Ports
    c.add_port("pump_in", center=(-radius - 30, -35), width=20, orientation=180, layer=LAYER_LASER)
    c.add_port("clk_out", center=(radius + 50, 0), width=WAVEGUIDE_WIDTH, orientation=0, layer=LAYER_WAVEGUIDE)

    return c


@gf.cell
def clock_distribution_hub() -> Component:
    """
    Central clock distribution hub.

    Takes 617 MHz from Kerr source and distributes to all units
    with matched path lengths for zero skew.
    """
    c = gf.Component()

    width = 400
    height = 400

    # Central hub
    hub_radius = 50
    center = (width/2, height/2)

    n_points = 64
    angles = np.linspace(0, 2*np.pi, n_points)
    hub_points = [(center[0] + hub_radius * np.cos(a),
                   center[1] + hub_radius * np.sin(a)) for a in angles]
    c.add_polygon(hub_points, layer=LAYER_CLOCK)

    # SOA in center
    c.add_polygon([(center[0] - 20, center[1] - 10), (center[0] + 20, center[1] - 10),
                   (center[0] + 20, center[1] + 10), (center[0] - 20, center[1] + 10)], layer=LAYER_EXP)

    c.add_label("CLOCK", position=center, layer=LAYER_TEXT)
    c.add_label("HUB", position=(center[0], center[1] - 25), layer=LAYER_TEXT)

    # 8 radial outputs (matched length)
    output_names = ["WEIGHT_LD", "ACT_STREAM", "RESULT_COL", "ARRAY_N",
                    "ARRAY_E", "ARRAY_S", "ARRAY_W", "CTRL"]

    for i, name in enumerate(output_names):
        angle = i * np.pi / 4
        x1 = center[0] + hub_radius * np.cos(angle)
        y1 = center[1] + hub_radius * np.sin(angle)
        x2 = center[0] + (width/2 - 20) * np.cos(angle)
        y2 = center[1] + (height/2 - 20) * np.sin(angle)

        # Radial waveguide
        dx = 3 * np.cos(angle + np.pi/2)
        dy = 3 * np.sin(angle + np.pi/2)
        c.add_polygon([
            (x1 - dx, y1 - dy), (x2 - dx, y2 - dy),
            (x2 + dx, y2 + dy), (x1 + dx, y1 + dy)
        ], layer=LAYER_CLOCK)

        # Output port
        c.add_port(f"clk_{name.lower()}", center=(x2, y2), width=6,
                   orientation=np.degrees(angle), layer=LAYER_CLOCK)

        # Label
        label_x = center[0] + (width/2 - 40) * np.cos(angle)
        label_y = center[1] + (height/2 - 40) * np.sin(angle)
        c.add_label(name, position=(label_x, label_y), layer=LAYER_TEXT)

    # Clock input
    c.add_port("clk_in", center=(0, height/2), width=WAVEGUIDE_WIDTH,
               orientation=180, layer=LAYER_WAVEGUIDE)
    c.add_polygon([(-20, height/2 - WAVEGUIDE_WIDTH/2), (center[0] - hub_radius, height/2 - WAVEGUIDE_WIDTH/2),
                   (center[0] - hub_radius, height/2 + WAVEGUIDE_WIDTH/2), (-20, height/2 + WAVEGUIDE_WIDTH/2)],
                  layer=LAYER_WAVEGUIDE)

    return c


# =============================================================================
# Complete Super IOC Module
# =============================================================================

@gf.cell
def super_ioc_module() -> Component:
    """
    Complete Super NR-IOC Module for 81×81 Optical Systolic Array.

    This module serves as the HOST INTERFACE - the boundary between the
    electronic host system and the all-optical compute fabric.

    ==========================================================================
    NEW ARCHITECTURE: Optical RAM Weight Streaming
    ==========================================================================

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                        SUPER NR-IOC                                      │
    │                    (Host Interface Module)                               │
    ├─────────────────────────────────────────────────────────────────────────┤
    │                                                                          │
    │  HOST (Electronic) ──────► E/O CONVERSION ──────► OPTICAL DOMAIN        │
    │                              (happens ONCE)                              │
    │                                                                          │
    │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
    │  │ WEIGHT         │  │  ACTIVATION    │  │   RESULT       │            │
    │  │ STREAMING      │  │  STREAMER      │  │   COLLECTOR    │            │
    │  │                │  │                │  │                │            │
    │  │ FROM: CPU      │  │  81-ch @617M   │  │  81-ch @617M   │            │
    │  │ OPTICAL RAM    │  │  double-buf    │  │  accumulate    │            │
    │  │                │  │                │  │                │            │
    │  │ Weights stay   │  │  Activations   │  │  Results →     │            │
    │  │ OPTICAL!       │  │  from host     │  │  back to host  │            │
    │  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘            │
    │          │                   │                   │                      │
    │          │    OPTICAL        │    OPTICAL        │    OPTICAL          │
    │          │                   │                   │                      │
    │          └───────────────────┴───────────────────┘                      │
    │                              │                                          │
    │                      ┌───────┴───────┐                                  │
    │                      │  CLOCK HUB    │                                  │
    │                      │   617 MHz     │                                  │
    │                      │  (from Kerr)  │                                  │
    │                      └───────────────┘                                  │
    │                              │                                          │
    │                      TO/FROM 81×81 PE ARRAY                            │
    │                      (all optical data paths)                          │
    └─────────────────────────────────────────────────────────────────────────┘

    Key Architecture Points:
    1. WEIGHTS: Stored in CPU's 3-tier optical RAM, streamed optically to PEs
       - No per-PE weight storage needed
       - Weights stay optical from RAM through compute
       - Arbitrary model sizes (not limited by PE registers)

    2. NR-IOC handles HOST BOUNDARY conversions only:
       - Activations: Host (binary electronic) → NR-IOC (E/O) → Optical
       - Results: Optical → NR-IOC (O/E) → Host (binary electronic)
       - Weights: Already optical in CPU RAM, just routed through

    3. Inside the optical domain, data NEVER converts back to electronic

    Specifications:
    - Weight streaming: 59,049 trits in ~96 μs (from optical RAM)
    - Activation throughput: 50 Gtrits/s (81 × 617 MHz × 9 trits)
    - Result throughput: 50 Gtrits/s
    - Zero-stall double buffering for activations
    - Integrated 617 MHz Kerr clock distribution
    """
    c = gf.Component("super_ioc_module")

    # Overall dimensions
    total_width = 2400
    total_height = 1800

    # Background
    c.add_polygon([(0, 0), (total_width, 0), (total_width, total_height), (0, total_height)],
                  layer=LAYER_BUS)

    # ==========================================================================
    # Title Block
    # ==========================================================================

    c.add_label("SUPER NR-IOC MODULE", position=(total_width/2, total_height - 30), layer=LAYER_TEXT)
    c.add_label("Host Interface for 81×81 Optical Systolic Array", position=(total_width/2, total_height - 55), layer=LAYER_TEXT)
    c.add_label("Weights Stream from CPU Optical RAM (All-Optical Path)", position=(total_width/2, total_height - 80), layer=LAYER_TEXT)

    # ==========================================================================
    # Kerr Clock Source (top left)
    # ==========================================================================

    kerr = c << kerr_clock_source()
    kerr.dmove((150, total_height - 250))
    c.add_label("CLOCK SOURCE", position=(150, total_height - 100), layer=LAYER_TEXT)

    # ==========================================================================
    # Clock Distribution Hub (center top)
    # ==========================================================================

    clock_hub = c << clock_distribution_hub()
    clock_hub.dmove((total_width/2 - 200, total_height - 550))

    # Connect Kerr to hub
    c.add_polygon([(300, total_height - 250), (total_width/2 - 200, total_height - 250),
                   (total_width/2 - 200, total_height - 350), (total_width/2 - 200 + 10, total_height - 350),
                   (total_width/2 - 200 + 10, total_height - 245), (300, total_height - 245)],
                  layer=LAYER_CLOCK)

    # ==========================================================================
    # Weight Streaming Unit (left side) - reads from CPU optical RAM
    # ==========================================================================

    weight_loader = c << weight_loader_unit()
    weight_loader.dmove((50, total_height/2 - 350))

    # ==========================================================================
    # Activation Streamer Unit (center)
    # ==========================================================================

    act_streamer = c << activation_streamer_unit()
    act_streamer.dmove((total_width/2 - 350, 100))

    # ==========================================================================
    # Result Collector Unit (right side)
    # ==========================================================================

    result_collector = c << result_collector_unit()
    result_collector.dmove((total_width - 750, total_height/2 - 275))

    # ==========================================================================
    # Host Interface Block (bottom)
    # ==========================================================================

    host_width = 600
    host_height = 150
    host_x = total_width/2 - host_width/2
    host_y = 30

    c.add_polygon([(host_x, host_y), (host_x + host_width, host_y),
                   (host_x + host_width, host_y + host_height), (host_x, host_y + host_height)],
                  layer=LAYER_DMA)

    c.add_label("HOST INTERFACE", position=(total_width/2, host_y + host_height/2 + 20), layer=LAYER_TEXT)
    c.add_label("PCIe / USB / Ethernet", position=(total_width/2, host_y + host_height/2 - 20), layer=LAYER_TEXT)

    # DMA channels
    c.add_polygon([(host_x + 50, host_y + 30), (host_x + 150, host_y + 30),
                   (host_x + 150, host_y + 70), (host_x + 50, host_y + 70)], layer=LAYER_METAL_PAD)
    c.add_label("DMA0", position=(host_x + 100, host_y + 50), layer=LAYER_TEXT)

    c.add_polygon([(host_x + 200, host_y + 30), (host_x + 300, host_y + 30),
                   (host_x + 300, host_y + 70), (host_x + 200, host_y + 70)], layer=LAYER_METAL_PAD)
    c.add_label("DMA1", position=(host_x + 250, host_y + 50), layer=LAYER_TEXT)

    c.add_polygon([(host_x + 350, host_y + 30), (host_x + 450, host_y + 30),
                   (host_x + 450, host_y + 70), (host_x + 350, host_y + 70)], layer=LAYER_METAL_PAD)
    c.add_label("DMA2", position=(host_x + 400, host_y + 50), layer=LAYER_TEXT)

    # Control registers
    c.add_polygon([(host_x + 480, host_y + 30), (host_x + 580, host_y + 30),
                   (host_x + 580, host_y + 120), (host_x + 480, host_y + 120)], layer=LAYER_METAL_PAD)
    c.add_label("CTRL", position=(host_x + 530, host_y + 90), layer=LAYER_TEXT)
    c.add_label("REGS", position=(host_x + 530, host_y + 60), layer=LAYER_TEXT)

    # ==========================================================================
    # Array Interface (outputs to systolic array)
    # ==========================================================================

    array_interface_y = total_height/2

    # Weight outputs (81 lines going right) - optical from CPU RAM
    c.add_label("TO ARRAY: WEIGHTS (OPTICAL)", position=(total_width - 100, total_height - 150), layer=LAYER_TEXT)
    for i in range(0, 81, 5):
        y = total_height - 200 - i * 4
        c.add_polygon([(total_width - 50, y), (total_width, y),
                       (total_width, y + 2), (total_width - 50, y + 2)], layer=LAYER_WAVEGUIDE)

    # Activation outputs (81 lines going right)
    c.add_label("TO ARRAY: ACTIVATIONS", position=(total_width - 100, 700), layer=LAYER_TEXT)
    for i in range(0, 81, 5):
        y = 650 - i * 4
        c.add_polygon([(total_width - 50, y), (total_width, y),
                       (total_width, y + 2), (total_width - 50, y + 2)], layer=LAYER_WAVEGUIDE)

    # Result inputs (81 lines coming from right)
    c.add_label("FROM ARRAY: RESULTS", position=(total_width - 100, 350), layer=LAYER_TEXT)
    for i in range(0, 81, 5):
        y = 300 - i * 4
        c.add_polygon([(total_width - 50, y), (total_width, y),
                       (total_width, y + 2), (total_width - 50, y + 2)], layer=LAYER_WAVEGUIDE)

    # ==========================================================================
    # Specifications Block
    # ==========================================================================

    spec_x = 50
    spec_y = 50

    c.add_polygon([(spec_x, spec_y), (spec_x + 350, spec_y),
                   (spec_x + 350, spec_y + 200), (spec_x, spec_y + 200)], layer=LAYER_METAL_PAD)

    c.add_label("SPECIFICATIONS", position=(spec_x + 175, spec_y + 180), layer=LAYER_TEXT)
    c.add_label("─────────────────", position=(spec_x + 175, spec_y + 165), layer=LAYER_TEXT)
    c.add_label("Weights: FROM CPU OPTICAL RAM", position=(spec_x + 175, spec_y + 145), layer=LAYER_TEXT)
    c.add_label("Weight stream: ~96 μs refresh", position=(spec_x + 175, spec_y + 125), layer=LAYER_TEXT)
    c.add_label("Act throughput: 50 Gt/s", position=(spec_x + 175, spec_y + 105), layer=LAYER_TEXT)
    c.add_label("Result throughput: 50 Gt/s", position=(spec_x + 175, spec_y + 85), layer=LAYER_TEXT)
    c.add_label("Clock: 617 MHz (Kerr)", position=(spec_x + 175, spec_y + 65), layer=LAYER_TEXT)
    c.add_label("Host: PCIe Gen4 x8", position=(spec_x + 175, spec_y + 45), layer=LAYER_TEXT)
    c.add_label("All-optical data path!", position=(spec_x + 175, spec_y + 25), layer=LAYER_TEXT)

    # ==========================================================================
    # External Ports
    # ==========================================================================

    # Host interface
    c.add_port("host_pcie", center=(total_width/2, 0), width=100, orientation=270, layer=LAYER_DMA)

    # Pump laser input
    c.add_port("pump_laser", center=(0, total_height - 200), width=20, orientation=180, layer=LAYER_LASER)

    # Array interfaces (right side)
    c.add_port("weight_bus", center=(total_width, total_height - 300), width=50, orientation=0, layer=LAYER_WAVEGUIDE)
    c.add_port("activation_bus", center=(total_width, 550), width=50, orientation=0, layer=LAYER_WAVEGUIDE)
    c.add_port("result_bus", center=(total_width, 200), width=50, orientation=0, layer=LAYER_WAVEGUIDE)

    # Clock output to array
    c.add_port("clk_to_array", center=(total_width, total_height/2), width=20, orientation=0, layer=LAYER_CLOCK)

    print("Super NR-IOC Module generated!")
    print(f"  Dimensions: {total_width} × {total_height} μm")
    print(f"  Weight streaming: {TOTAL_PES * TRITS_PER_VALUE} trits from CPU optical RAM")
    print(f"  Throughput: {ARRAY_SIZE * CLOCK_FREQ_MHZ * TRITS_PER_VALUE / 1000:.1f} Gtrits/s")
    print(f"  Architecture: All-optical data path (E/O at host boundary only)")

    return c


# =============================================================================
# Complete System: Super IOC + Systolic Array
# =============================================================================

@gf.cell
def complete_ai_accelerator() -> Component:
    """
    Complete AI Accelerator: Super IOC + 81×81 Systolic Array

    This is the full system with no external RAM required.
    """
    c = gf.Component("complete_ai_accelerator")

    # Import systolic array
    try:
        from optical_systolic_array import optical_systolic_array_81x81
        has_array = True
    except ImportError:
        has_array = False
        print("Note: optical_systolic_array.py not found, generating IOC only")

    # Super IOC
    ioc = c << super_ioc_module()
    ioc.dmove((0, 0))

    if has_array:
        # Systolic array (to the right of IOC)
        array = c << optical_systolic_array_81x81()
        array.dmove((2500, 200))

        # Connection bus between IOC and array
        c.add_polygon([(2400, 500), (2500, 500), (2500, 1500), (2400, 1500)], layer=LAYER_BUS)
        c.add_label("IOC ↔ ARRAY BUS", position=(2450, 1000), layer=LAYER_TEXT)

    c.add_label("COMPLETE OPTICAL AI ACCELERATOR", position=(2000, 2000), layer=LAYER_TEXT)
    c.add_label("Super IOC + 81×81 Systolic Array", position=(2000, 1970), layer=LAYER_TEXT)
    c.add_label("4.05 TMAC/s | No External RAM", position=(2000, 1940), layer=LAYER_TEXT)

    return c


# =============================================================================
# Interactive CLI
# =============================================================================

def main():
    print("=" * 70)
    print("  SUPER NR-IOC MODULE GENERATOR")
    print("  Host Interface for Optical Systolic Array")
    print("=" * 70)
    print()
    print("NEW ARCHITECTURE: Optical RAM Weight Streaming")
    print("  - Weights stored in CPU's 3-tier optical RAM")
    print("  - Streamed optically to PE array (no E/O conversion)")
    print("  - NR-IOC handles host boundary only")
    print()
    print("Features:")
    print("  - Weight Streaming: From CPU optical RAM @ 617 MHz")
    print("  - Activation Streamer: 81-ch double-buffered (host E/O)")
    print("  - Result Collector: 81-ch with accumulation (O/E to host)")
    print("  - Integrated 617 MHz Kerr clock")
    print("  - ALL-OPTICAL DATA PATH for weights!")
    print()
    print("Options:")
    print("  1. Generate complete Super NR-IOC module")
    print("  2. Generate Weight Streaming unit only")
    print("  3. Generate Activation Streamer unit only")
    print("  4. Generate Result Collector unit only")
    print("  5. Generate Clock Distribution hub only")
    print("  6. Generate complete AI Accelerator (NR-IOC + Array)")
    print()

    choice = input("Select option (1-6): ").strip()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    gds_dir = os.path.join(base_dir, 'data', 'gds')
    os.makedirs(gds_dir, exist_ok=True)

    if choice == "1":
        print("\nGenerating Super NR-IOC module...")
        comp = super_ioc_module()
        output_path = os.path.join(gds_dir, "super_nrioc_module.gds")

    elif choice == "2":
        print("\nGenerating Weight Streaming unit...")
        comp = weight_loader_unit()
        output_path = os.path.join(gds_dir, "weight_streaming_unit.gds")

    elif choice == "3":
        print("\nGenerating Activation Streamer unit...")
        comp = activation_streamer_unit()
        output_path = os.path.join(gds_dir, "activation_streamer_unit.gds")

    elif choice == "4":
        print("\nGenerating Result Collector unit...")
        comp = result_collector_unit()
        output_path = os.path.join(gds_dir, "result_collector_unit.gds")

    elif choice == "5":
        print("\nGenerating Clock Distribution hub...")
        comp = clock_distribution_hub()
        output_path = os.path.join(gds_dir, "clock_distribution_hub.gds")

    elif choice == "6":
        print("\nGenerating complete AI Accelerator...")
        print("(This may take a while for the 81×81 array)")
        comp = complete_ai_accelerator()
        output_path = os.path.join(gds_dir, "complete_ai_accelerator.gds")

    else:
        print("Invalid selection.")
        return

    comp.write_gds(output_path)
    print(f"\nSaved to: {output_path}")

    # Get dimensions
    bbox = comp.dbbox()
    print(f"Dimensions: {bbox.width():.0f} × {bbox.height():.0f} μm")

    # Offer to open in KLayout
    show = input("\nOpen in KLayout? (y/n): ").strip().lower()
    if show == "y":
        import subprocess
        try:
            subprocess.Popen(["klayout", output_path])
            print("KLayout launched!")
        except FileNotFoundError:
            print("KLayout not found in PATH")


if __name__ == "__main__":
    main()
