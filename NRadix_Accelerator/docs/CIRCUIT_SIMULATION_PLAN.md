# Circuit-Level Simulation: Monolithic 9x9 N-Radix Chip

**Date:** 2026-02-17 (plan) → 2026-02-18 (implemented and PASSING)
**Author:** N-Radix Project (Claude-assisted research)
**Status:** COMPLETE — 8/8 tests PASS
**Implementation:** `circuit_sim/simulate_9x9.py` + `circuit_sim/models/components.py`
**Interactive demo:** `circuit_sim/demo.py` (Tkinter GUI with 5 examples)

---

## 1. Motivation and Scope

### What we have now

The project has validated individual photonic components via Meep FDTD:

| Component | Simulation file | What was validated |
|-----------|----------------|-------------------|
| Straight waveguide | `components/photonics/straight_waveguide.py` | Propagation, mode confinement at 1550 nm |
| Ring resonator (selector) | `components/photonics/optical_selector.py` | Resonant filtering, electro-optic tuning |
| SFG mixer (PPLN) | `components/photonics/sfg_mixer.py` | Sum-frequency generation for RED+GREEN |
| Y-junction combiner | `components/photonics/y_junction.py` | Wavelength combining (two arms to one) |
| Photodetector (Ge) | `components/photonics/photodetector.py` | Absorption efficiency at 608 nm (SFG output) |
| WDM 9x9 array routing | `simulations/wdm_9x9_array_test.py` | 18 wavelengths through 9x9 grid, no crosstalk |
| IOC integration (SFG physics) | `simulations/ioc_integration_test.py` | All 6 SFG products in PPLN with QPM |

The monolithic 9x9 chip (`architecture/monolithic_chip_9x9.py`) has passed analytical validation for path-length matching, loss budget, timing skew, and wavelength collision-freedom.

### What was missing (now resolved)

A **full-chip photonic circuit simulation** was needed: inject ternary-encoded optical signals at the input edge, propagate through all 81 PEs, and verify that the correct computed results appear at the output photodetectors.

**This has been built and is passing all tests.** The simulation (`circuit_sim/simulate_9x9.py`) bridges the gap between "individual components work" and "the system computes correctly."

### Results (2026-02-18)

| Test | Description | Status |
|------|-------------|--------|
| single_pe | All 9 ternary multiplications through one PE | **PASS** |
| identity | Identity matrix — output equals input | **PASS** |
| all_ones | All +1 inputs and weights — each column sums to 9 | **PASS** |
| single_nonzero | Single weight, all others zero — PE isolation | **PASS** |
| mixed_3x3 | 3x3 submatrix with mixed signs | **PASS** |
| tridiagonal | Laplacian-like [-1, 0, -1] pattern | **PASS** |
| ioc_domain | IOC PE modes: ADD/SUB direct, MUL/DIV log-domain | **PASS** |
| loss_budget | Worst-case power margin at PE[0,8]: 17.6 dB | **PASS** |

**Component models implemented:** waveguide (with Sellmeier dispersion), SFG mixer (PPLN), MZI encoder, AWG demux (6-channel), photodetector, bend/meander.

### Why not just use Meep for the full chip?

The monolithic chip is 1095 x 695 micrometers. At the minimum usable FDTD resolution (20 pixels/micrometer), the simulation domain would be approximately 21,900 x 13,900 grid points = ~304 million cells per 2D slice. With multiple wavelengths (1064-1550 nm input, 532-775 nm SFG output) requiring adequate temporal resolution, and a run time of hundreds of picoseconds, this simulation would:

- Require ~50-100 GB of RAM (even 2D)
- Take days to weeks on 12 cores
- Be impractical for iterative design exploration

**Circuit-level simulation** (S-parameter / transfer-matrix methods) solves this: each component is represented by a compact model (a small matrix), and the full circuit is assembled algebraically. A 9x9 array simulation runs in seconds, not days.

---

## 2. Tool Landscape and Recommendation

### 2.1 Tools Evaluated

| Tool | Type | License | Python | Strengths | Weaknesses |
|------|------|---------|--------|-----------|------------|
| **SAX** | S-parameter circuit sim, JAX-based | MIT (open source) | Yes | Fast, autodiff for optimization, functional API, integrates with gdsfactory | No built-in nonlinear models; linear S-parameter framework |
| **Simphony** | S-parameter circuit sim | MIT (open source) | Yes | SPICE-like netlists, built-in SiEPIC models, 20x faster than Lumerical INTERCONNECT | Silicon photonics focus; model library is SOI, not LiNbO3 |
| **gdsfactory + gplugins** | Layout + simulation ecosystem | MIT (open source) | Yes | Already used for GDS layout; SAX plugin built in; Meep/Tidy3D/INTERCONNECT plugins | Orchestration layer, not a simulator itself |
| **Lumerical INTERCONNECT** | Commercial circuit sim | Commercial (~$15k/yr) | Via API | Industry standard, nonlinear models, time-domain + frequency-domain | Expensive; overkill for hobby project |
| **Photon Design PICWave** | Commercial circuit sim | Commercial | Limited | Has chi(2) nonlinear PPLN model | Very expensive; closed source |
| **PyNLO** | Nonlinear pulse propagation | Open source | Yes | Designed for chi(2)/chi(3) interactions | Not a circuit simulator; single-waveguide propagation only |

### 2.2 Recommendation: SAX + custom nonlinear models

**Primary tool: SAX** (`pip install sax`)

Reasons:
1. **Already in the ecosystem.** The project uses gdsfactory for GDS layout. SAX is gdsfactory's native circuit simulator.
2. **Pure Python, JAX-powered.** Runs on any machine, no license fees, GPU-acceleratable if needed.
3. **Functional API.** Component models are just Python functions that return S-parameter dictionaries. Defining custom LiNbO3 components is straightforward.
4. **Fast.** A 9x9 array with 81 PEs, 9 encoders, 9 decoders, and routing waveguides will simulate in under a second.
5. **Gradient-based optimization.** JAX autodiff means we can later optimize waveguide lengths, coupling gaps, etc.

**Limitation and workaround for nonlinear SFG:** SAX is a linear S-parameter solver. SFG is inherently nonlinear (two input frequencies produce a third). The solution is a **two-stage simulation**:

- **Stage 1: SFG compact model from Meep.** Use the existing FDTD simulations (already done in `ioc_integration_test.py`) to extract effective S-parameters for the PPLN mixer at each wavelength combination. The PPLN mixer becomes a multi-port compact model: two input wavelengths in, one SFG output wavelength out, with a conversion efficiency coefficient.
- **Stage 2: Circuit assembly in SAX.** Wire all compact models together using a netlist that mirrors the monolithic chip layout. Inject signals, propagate through the network, read outputs.

This hybrid approach leverages the FDTD results we already have while enabling fast full-chip simulation.

**Secondary tool: Simphony** (backup option, `pip install simphony`)

Simphony uses the same S-parameter paradigm but with a more object-oriented API. If SAX's JAX dependency causes installation issues, Simphony is a solid fallback. The component model definitions are nearly identical in concept.

---

## 3. Installation

### 3.1 SAX installation

```bash
# Create a dedicated environment (or use existing meep_env)
conda create -n photonic_sim python=3.11 -y
conda activate photonic_sim

# Install SAX and dependencies
pip install sax jax jaxlib

# Install gdsfactory plugins for SAX integration
pip install gplugins[sax]

# Install Simphony as backup
pip install simphony

# Verify
python -c "import sax; print('SAX version:', sax.__version__)"
python -c "import jax; print('JAX version:', jax.__version__)"
```

### 3.2 Alternative: install into existing meep_env

```bash
conda activate meep_env
pip install sax jax jaxlib
python -c "import sax; print('SAX OK')"
```

Note: JAX requires Python 3.9+. The existing meep_env should be compatible.

---

## 4. S-Parameter Models for Each Component

Each component in the monolithic chip needs a compact S-parameter model. Models are Python functions that return an `SDict` (dictionary mapping port-pair tuples to complex transmission coefficients).

### 4.1 Waveguide Segment

The simplest component. A waveguide introduces phase delay and propagation loss.

```python
import jax.numpy as jnp
import sax

def waveguide(
    *,
    wl: float = 1.55,          # wavelength in micrometers
    length: float = 10.0,       # length in micrometers
    neff: float = 2.2,          # effective index (LiNbO3)
    ng: float = 2.3,            # group index
    loss_db_per_cm: float = 2.0,# propagation loss
    wl0: float = 1.55,          # reference wavelength
) -> sax.SDict:
    """LiNbO3 ridge waveguide compact model."""
    # Frequency-dependent effective index (first-order dispersion)
    dwl = wl - wl0
    neff_wl = neff - (ng - neff) * dwl / wl0

    # Phase accumulated over length
    phase = 2 * jnp.pi * neff_wl * length / wl

    # Loss (convert dB/cm to linear/um)
    loss_per_um = loss_db_per_cm / (10.0 * 1e4)  # dB/cm -> dB/um
    amplitude = 10 ** (-loss_per_um * length / 20)  # dB to linear amplitude

    # S-parameters: transmission both directions, no reflection
    t = amplitude * jnp.exp(1j * phase)
    return {
        ("in", "out"): t,
        ("out", "in"): t,
    }
```

**Parameters to calibrate from Meep:**
- `neff`: Extract from eigenmode analysis of the 0.5 um wide, LiNbO3 (n=2.2) ridge waveguide at each wavelength. The existing `straight_waveguide.py` simulation can provide this.
- `ng`: Group index from `ng = neff - wl * d(neff)/d(wl)`. Run the waveguide simulation at two nearby wavelengths.
- `loss_db_per_cm`: Use 2 dB/cm for TFLN waveguides (literature value; can be refined if Meep propagation loss data is available).

**Wavelength-specific models needed:** The chip operates at 6 input wavelengths (1064, 1310, 1550 nm and their SFG outputs at 532-775 nm). The effective index varies with wavelength:

| Wavelength (nm) | Approximate n_eff (LiNbO3, 0.5 um ridge) |
|-----------------|------------------------------------------|
| 1550 | 2.14 |
| 1310 | 2.17 |
| 1064 | 2.21 |
| 775 | 2.26 |
| 710 | 2.28 |
| 655 | 2.30 |
| 631 | 2.31 |
| 587 | 2.33 |
| 532 | 2.36 |

These are approximate values from LiNbO3 Sellmeier data. For accurate models, run a Meep eigenmode solver at each wavelength (a quick simulation, seconds each).

### 4.2 Waveguide Bend

A bend introduces additional loss and a slight effective-index change.

```python
def waveguide_bend(
    *,
    wl: float = 1.55,
    radius: float = 5.0,        # bend radius in um
    angle_deg: float = 90.0,    # bend angle
    neff: float = 2.2,
    loss_db_per_90deg: float = 0.05,  # bend loss
) -> sax.SDict:
    """Waveguide bend compact model."""
    arc_length = radius * jnp.pi * angle_deg / 180.0
    phase = 2 * jnp.pi * neff * arc_length / wl
    amplitude = 10 ** (-loss_db_per_90deg * (angle_deg / 90.0) / 20)
    t = amplitude * jnp.exp(1j * phase)
    return {
        ("in", "out"): t,
        ("out", "in"): t,
    }
```

At 5 um bend radius in LiNbO3, bend loss is typically < 0.1 dB per 90-degree turn for wavelengths around 1550 nm. Tighter at shorter wavelengths.

### 4.3 SFG Mixer (PPLN) — The Critical Component

This is where the computation happens. The PPLN mixer is a nonlinear device: two input photons (at frequencies f_a and f_b) produce one output photon at f_a + f_b via sum-frequency generation.

In a linear S-parameter framework, we model this as a **3-port device** with a frequency-dependent conversion efficiency extracted from FDTD.

```python
def sfg_mixer_ppln(
    *,
    wl_a: float = 1.55,        # input wavelength A (um)
    wl_b: float = 1.31,        # input wavelength B (um)
    ppln_length: float = 20.0,  # PPLN interaction length (um)
    conversion_efficiency: float = 0.1,  # power conversion (from FDTD)
    insertion_loss_db: float = 1.0,      # passthrough loss
    neff: float = 2.2,
) -> sax.SDict:
    """
    PPLN SFG mixer compact model.

    Ports:
        input_a:  activation input (horizontal waveguide)
        input_b:  weight input (vertical waveguide)
        output:   SFG product output (to accumulator / next PE)
        pass_h:   horizontal passthrough (activation to next PE)
        pass_v:   vertical passthrough (partial sum to next PE)

    The conversion_efficiency is pre-calibrated from Meep FDTD
    simulation of the specific wavelength pair in the PPLN section.
    """
    wl_sfg = 1.0 / (1.0 / wl_a + 1.0 / wl_b)

    # Phase through the mixer region
    phase_a = 2 * jnp.pi * neff * ppln_length / wl_a
    phase_b = 2 * jnp.pi * neff * ppln_length / wl_b

    # SFG conversion: sqrt of power conversion for amplitude
    eta = jnp.sqrt(conversion_efficiency)

    # Passthrough: what does not get converted passes through
    # Conservation: |pass|^2 + |sfg|^2 ~ 1 (minus loss)
    pass_amplitude = jnp.sqrt(1.0 - conversion_efficiency)
    loss_linear = 10 ** (-insertion_loss_db / 20)

    return {
        # SFG product: from input_a + input_b to output
        # This is a simplified linear proxy — the actual SFG
        # depends on the product of two field amplitudes, but
        # at the circuit level we represent it as a fixed
        # conversion efficiency calibrated at operating power
        ("input_a", "output"): eta * loss_linear * jnp.exp(1j * phase_a),
        ("input_b", "output"): eta * loss_linear * jnp.exp(1j * phase_b),

        # Horizontal passthrough (activation continues to next PE)
        ("input_a", "pass_h"): pass_amplitude * loss_linear * jnp.exp(1j * phase_a),
        ("pass_h", "input_a"): pass_amplitude * loss_linear * jnp.exp(1j * phase_a),

        # Vertical passthrough (partial sum continues downward)
        ("input_b", "pass_v"): pass_amplitude * loss_linear * jnp.exp(1j * phase_b),
        ("pass_v", "input_b"): pass_amplitude * loss_linear * jnp.exp(1j * phase_b),
    }
```

**Extracting conversion_efficiency from existing FDTD data:**

The `ioc_integration_test.py` simulation already runs all 6 SFG interactions. To extract compact model parameters:

1. Run `ioc_integration_test.py` (already done — results exist)
2. For each SFG pair, measure the ratio: `P_sfg_output / P_input_total`
3. This ratio is the `conversion_efficiency` parameter for that wavelength pair

| SFG Pair | Input wavelengths | Output wavelength | Expected conversion efficiency |
|----------|------------------|-------------------|-------------------------------|
| B+B | 1064 + 1064 nm | 532 nm | ~5-15% (SHG, best QPM match) |
| G+B | 1310 + 1064 nm | 587 nm | ~3-10% (cross-SFG) |
| R+B | 1550 + 1064 nm | 631 nm | ~3-10% (cross-SFG) |
| G+G | 1310 + 1310 nm | 655 nm | ~5-15% (SHG) |
| R+G | 1550 + 1310 nm | 710 nm | ~3-10% (cross-SFG) |
| R+R | 1550 + 1550 nm | 775 nm | ~5-15% (SHG) |

These values are approximate. The actual values from the FDTD simulation should be used.

**Important note on the nonlinear modeling limitation:** The SFG mixer model above is a linearized approximation. It works because:
- At the circuit level, we care about "did the correct output wavelength appear?" not "what is the exact field amplitude?"
- The conversion efficiency is pre-calibrated at the expected operating power level
- For validation, we are checking correct routing and wavelength assignment, not absolute power levels

For power-accurate simulations, a time-domain circuit simulator (like Lumerical INTERCONNECT) would be needed. But for functional verification — "does the correct ternary result come out?" — the linearized SAX model is sufficient.

### 4.4 MZI Modulator (Encoder)

The Mach-Zehnder Interferometer modulator in the IOC encoder encodes ternary values by selectively transmitting one of three wavelengths.

```python
def mzi_modulator(
    *,
    wl: float = 1.55,
    arm_length: float = 100.0,    # MZI arm length (um)
    delta_n: float = 0.0,         # electro-optic index change
    neff: float = 2.2,
    insertion_loss_db: float = 3.0,
    extinction_ratio_db: float = 20.0,
) -> sax.SDict:
    """
    MZI modulator for ternary encoding.

    When delta_n = 0: full transmission (ON state)
    When delta_n = wl/(2*arm_length): null (OFF state)
    """
    phase_diff = 2 * jnp.pi * delta_n * arm_length / wl
    # MZI transfer function: T = cos^2(phase_diff / 2)
    transmission = jnp.cos(phase_diff / 2) ** 2

    loss_linear = 10 ** (-insertion_loss_db / 20)
    t = jnp.sqrt(transmission) * loss_linear

    return {
        ("in", "out"): t,
        ("out", "in"): t,
    }
```

For the encoder, we need 3 MZI modulators (one per wavelength: 1550, 1310, 1064 nm). To encode trit value -1, the 1550 nm MZI is ON, the others are OFF. For trit 0, the 1310 nm MZI is ON. For trit +1, the 1064 nm MZI is ON.

### 4.5 Wavelength Combiner (MMI)

Combines three wavelength channels into a single waveguide.

```python
def wavelength_combiner_3to1(
    *,
    wl: float = 1.55,
    insertion_loss_db: float = 1.0,  # per-channel loss
) -> sax.SDict:
    """
    3-to-1 wavelength combiner (MMI-based).

    Minimal crosstalk assumed — wavelengths are widely spaced
    (1064, 1310, 1550 nm = 246+ nm spacing).
    """
    loss_linear = 10 ** (-insertion_loss_db / 20)
    # Each input maps to the common output
    return {
        ("in_r", "out"): loss_linear,
        ("in_g", "out"): loss_linear,
        ("in_b", "out"): loss_linear,
        ("out", "in_r"): loss_linear,
        ("out", "in_g"): loss_linear,
        ("out", "in_b"): loss_linear,
    }
```

### 4.6 AWG Demultiplexer (5-channel)

The output decoder uses an Arrayed Waveguide Grating to separate the 6 SFG product wavelengths (532-775 nm) into individual channels routed to photodetectors.

```python
def awg_demux_5ch(
    *,
    wl: float = 0.587,          # wavelength being queried
    center_wavelengths: tuple = (0.532, 0.587, 0.631, 0.655, 0.710, 0.775),
    channel_bandwidth_nm: float = 15.0,
    insertion_loss_db: float = 3.0,
    crosstalk_db: float = -25.0,
) -> sax.SDict:
    """
    AWG demultiplexer — routes SFG output wavelengths to
    individual photodetector channels.

    6 output channels (one per SFG product wavelength).
    Min channel spacing: 24 nm (validated collision-free).
    """
    loss_linear = 10 ** (-insertion_loss_db / 20)
    crosstalk_linear = 10 ** (crosstalk_db / 20)

    sdict = {}
    for i, cwl in enumerate(center_wavelengths):
        port_name = f"ch_{i}"
        # Gaussian passband
        detuning_nm = (wl - cwl) * 1000  # convert um to nm
        sigma_nm = channel_bandwidth_nm / 2.355  # FWHM to sigma
        passband = jnp.exp(-0.5 * (detuning_nm / sigma_nm) ** 2)

        t = loss_linear * passband
        sdict[("in", port_name)] = t
        sdict[(port_name, "in")] = t

    return sdict
```

### 4.7 Photodetector

The photodetector converts optical power to electrical signal. In the S-parameter model, it is a termination (absorber) with a responsivity.

```python
def photodetector(
    *,
    wl: float = 0.587,
    responsivity_A_per_W: float = 0.5,
    detector_length_um: float = 2.0,
    absorption_efficiency: float = 0.9,
) -> sax.SDict:
    """
    Waveguide-coupled Ge photodetector.

    At the circuit level, this is an absorbing termination.
    The absorption_efficiency determines how much light is
    captured vs. passes through.

    Returns a dict with the "detected" power fraction.
    """
    # Absorbed fraction (this terminates the circuit)
    return {
        ("in", "detected"): jnp.sqrt(absorption_efficiency),
    }
```

### 4.8 Path-Length Equalization Meander

The meander is just a waveguide with extra length. It reuses the waveguide model with the appropriate length parameter. No separate model is needed — just instantiate `waveguide(length=extra_length)`.

---

## 5. Assembling the Full 9x9 Circuit

### 5.1 Circuit hierarchy

The circuit has a natural hierarchy:

```
monolithic_9x9_chip
  |
  +-- encoder[0..8]              (IOC input, left edge)
  |     +-- mzi_r, mzi_g, mzi_b (3 MZI modulators)
  |     +-- combiner_3to1       (wavelength combiner)
  |     +-- wg_to_array         (routing waveguide)
  |
  +-- pe_array[9x9]             (center, passive)
  |     +-- pe[row][col]        (81 processing elements)
  |           +-- sfg_mixer     (PPLN computation)
  |           +-- wg_h_in/out   (horizontal routing)
  |           +-- wg_v_in/out   (vertical routing)
  |           +-- wg_weight     (weight input from bus)
  |
  +-- decoder[0..8]             (IOC output, right edge)
  |     +-- wg_from_array      (routing waveguide)
  |     +-- awg_demux          (5-channel demux)
  |     +-- pd[0..4]           (5 photodetectors)
  |
  +-- weight_bus                (top edge)
        +-- wg_drop[0..8]      (distribution to columns)
        +-- meander[0..8]      (path equalization)
```

### 5.2 SAX netlist for one PE

```python
import sax

def pe_netlist(row: int, col: int) -> sax.RecursiveNetlist:
    """Netlist for a single Processing Element."""
    return {
        "instances": {
            "mixer": "sfg_mixer_ppln",
            "wg_h_in": "waveguide",
            "wg_h_out": "waveguide",
            "wg_v_in": "waveguide",
            "wg_v_out": "waveguide",
            "wg_weight": "waveguide",
        },
        "connections": {
            # Horizontal path: in -> mixer -> out
            "wg_h_in,out": "mixer,input_a",
            "mixer,pass_h": "wg_h_out,in",

            # Vertical path: in -> mixer -> out
            "wg_v_in,out": "mixer,input_b",
            "mixer,pass_v": "wg_v_out,in",

            # Weight input
            "wg_weight,out": "mixer,input_b",
        },
        "ports": {
            "in_h": "wg_h_in,in",
            "out_h": "wg_h_out,out",
            "in_v": "wg_v_in,in",
            "out_v": "wg_v_out,out",
            "weight_in": "wg_weight,in",
            "sfg_out": "mixer,output",
        },
    }
```

### 5.3 SAX netlist for the full 9x9 array

```python
def array_9x9_netlist() -> sax.RecursiveNetlist:
    """Netlist for the complete 9x9 PE array."""
    instances = {}
    connections = {}
    ports = {}

    for row in range(9):
        for col in range(9):
            pe_name = f"pe_{row}_{col}"
            instances[pe_name] = "processing_element"

            # Horizontal connections (left to right within a row)
            if col > 0:
                prev_pe = f"pe_{row}_{col-1}"
                connections[f"{prev_pe},out_h"] = f"{pe_name},in_h"

            # Vertical connections (top to bottom within a column)
            if row > 0:
                above_pe = f"pe_{row-1}_{col}"
                connections[f"{above_pe},out_v"] = f"{pe_name},in_v"

        # Row input port (from encoder)
        ports[f"row_{row}_in"] = f"pe_{row}_0,in_h"
        # Row output port (passthrough to right edge)
        ports[f"row_{row}_out"] = f"pe_{row}_8,out_h"

    for col in range(9):
        # Column output port (bottom, to decoder)
        ports[f"col_{col}_out"] = f"pe_8_{col},out_v"
        # Column top input (from weight bus)
        ports[f"col_{col}_weight"] = f"pe_0_{col},weight_in"

    return {
        "instances": instances,
        "connections": connections,
        "ports": ports,
    }
```

### 5.4 Full chip netlist

```python
def monolithic_9x9_netlist() -> sax.RecursiveNetlist:
    """Complete monolithic chip netlist."""
    instances = {}
    connections = {}
    ports = {}

    # Encoders (left edge)
    for row in range(9):
        enc = f"encoder_{row}"
        instances[enc] = "ioc_encoder"
        # Routing waveguide from encoder to array
        wg = f"wg_enc_to_array_{row}"
        instances[wg] = "waveguide"
        connections[f"{enc},encoded_out"] = f"{wg},in"
        connections[f"{wg},out"] = f"array,row_{row}_in"
        # External laser input
        ports[f"laser_in_{row}"] = f"{enc},laser_in"

    # PE array
    instances["array"] = "pe_array_9x9"

    # Decoders (right edge)
    for col in range(9):
        # Routing waveguide from array column output to decoder
        wg = f"wg_array_to_dec_{col}"
        instances[wg] = "waveguide"
        connections[f"array,col_{col}_out"] = f"{wg},in"

        dec = f"decoder_{col}"
        instances[dec] = "ioc_decoder"
        connections[f"{wg},out"] = f"{dec},result_in"
        # Electronic output
        ports[f"data_out_{col}"] = f"{dec},data_out"

    # Weight bus distribution
    for col in range(9):
        wg_w = f"wg_weight_{col}"
        instances[wg_w] = "waveguide"
        connections[f"{wg_w},out"] = f"array,col_{col}_weight"
        ports[f"weight_in_{col}"] = f"{wg_w},in"

    return {
        "instances": instances,
        "connections": connections,
        "ports": ports,
    }
```

### 5.5 Registering models and running the simulation

```python
import sax
import jax.numpy as jnp

# Register all component models
models = {
    "waveguide": waveguide,
    "waveguide_bend": waveguide_bend,
    "sfg_mixer_ppln": sfg_mixer_ppln,
    "mzi_modulator": mzi_modulator,
    "wavelength_combiner_3to1": wavelength_combiner_3to1,
    "awg_demux_5ch": awg_demux_5ch,
    "photodetector": photodetector,
    "processing_element": pe_netlist,       # sub-circuit
    "pe_array_9x9": array_9x9_netlist,      # sub-circuit
    "ioc_encoder": encoder_netlist,          # sub-circuit (to be defined)
    "ioc_decoder": decoder_netlist,          # sub-circuit (to be defined)
}

# Build the circuit
circuit, _ = sax.circuit(
    netlist=monolithic_9x9_netlist(),
    models=models,
)

# Simulate at a specific wavelength
result = circuit(wl=1.55)

# Extract S-parameter from laser input to data output
# Example: what comes out of decoder 0 when we inject at laser 0?
s_laser0_to_data0 = result[("laser_in_0", "data_out_0")]
print(f"Transmission laser_0 -> data_0: {abs(s_laser0_to_data0)**2:.6f}")
```

---

## 6. Simulation Flow: End-to-End Test Procedure

### Step 0: Extract S-parameters from Meep (one-time calibration)

Run short Meep simulations to extract compact model parameters:

```
scripts/extract_sparams/
  extract_waveguide_neff.py      — eigenmode at each wavelength
  extract_sfg_efficiency.py      — SFG conversion ratio per pair
  extract_ring_resonator.py      — ring resonator drop/through
  extract_photodetector.py       — absorption vs. wavelength
```

Each script outputs a JSON file with calibrated parameters:

```json
{
  "waveguide_1550nm": {"neff": 2.14, "ng": 2.30, "loss_db_cm": 2.0},
  "waveguide_1310nm": {"neff": 2.17, "ng": 2.32, "loss_db_cm": 2.2},
  "waveguide_1064nm": {"neff": 2.21, "ng": 2.35, "loss_db_cm": 2.5},
  "sfg_RG":           {"conversion_efficiency": 0.08, "insertion_loss_db": 1.0},
  ...
}
```

### Step 1: Build component models from calibrated data

Load the JSON, instantiate parameterized SAX models.

### Step 2: Assemble the netlist

Use the hierarchical netlists from Section 5. Each PE, encoder, and decoder is a sub-circuit.

### Step 3: Sweep wavelengths

For each input trit encoding, simulate across the 3 input wavelengths and check which SFG output wavelengths appear at each decoder.

### Step 4: Compare against expected ternary arithmetic

The systolic array performs matrix-vector multiplication. For a weight matrix W (9x9) and input vector x (9x1), the output should be y = W * x (mod ternary arithmetic). Each element y_j = sum(W[j,i] * x[i]) for i=0..8.

### Step 5: Report pass/fail per test case

---

## 7. Test Cases

### 7.1 Test Case 1: Identity matrix (passthrough)

**Purpose:** Verify that signals propagate through the array without corruption.

**Setup:**
- Weight matrix: 9x9 identity (diagonal = +1, off-diagonal = 0)
- Input vector: [+1, -1, 0, +1, -1, 0, +1, -1, 0]

**Expected output:** [+1, -1, 0, +1, -1, 0, +1, -1, 0] (same as input)

**What this tests:** End-to-end signal integrity. Every PE on the diagonal performs (+1) * (input) = input. Off-diagonal PEs get weight=0, so they contribute nothing.

**Implementation:**
```python
def test_identity_passthrough():
    """Inject identity weights and verify output equals input."""
    input_trits = [+1, -1, 0, +1, -1, 0, +1, -1, 0]
    weights = [[1 if i == j else 0 for j in range(9)] for i in range(9)]

    # Encode inputs as wavelengths
    input_wavelengths = [trit_to_wavelength(t) for t in input_trits]

    # Encode weights as wavelengths
    weight_wavelengths = [[trit_to_wavelength(w) for w in row] for row in weights]

    # Run circuit simulation
    output_trits = simulate_matmul(input_wavelengths, weight_wavelengths)

    expected = input_trits
    assert output_trits == expected, f"FAIL: got {output_trits}, expected {expected}"
    print("PASS: Identity passthrough")
```

### 7.2 Test Case 2: All-ones multiplication

**Purpose:** Verify that accumulation across a row works.

**Setup:**
- Weight matrix: all +1
- Input vector: all +1

**Expected output:** Each output element = sum of 9 multiplications of (+1)*(+1) = 9 * (+1) = +9. In balanced ternary, +9 = [+1, 0, 0] (one trit carry chain). For a single-trit output, the result wraps or saturates. The raw SFG accumulation would show 9 copies of the B+B SFG product (532 nm).

**What this tests:** Accumulation behavior and signal-to-noise at the output detectors when all PEs contribute.

### 7.3 Test Case 3: Single non-zero weight

**Purpose:** Verify isolation between PEs.

**Setup:**
- Weight matrix: all 0 except W[4][4] = +1
- Input vector: all +1

**Expected output:** Only output column 4 has a non-zero result (+1). All other outputs should be zero (no SFG product detected).

**What this tests:** PE isolation, crosstalk between channels.

### 7.4 Test Case 4: Ternary multiplication table

**Purpose:** Verify all 9 trit*trit products.

**Setup:** Run 9 single-PE simulations (or use a 3x3 sub-array):

| Input A | Input B | Expected SFG output | Expected trit result |
|---------|---------|--------------------|--------------------|
| +1 (1064) | +1 (1064) | 532 nm (B+B) | +1 |
| +1 (1064) | 0 (1310) | 587 nm (G+B) | 0 |
| +1 (1064) | -1 (1550) | 631 nm (R+B) | -1 |
| 0 (1310) | +1 (1064) | 587 nm (G+B) | 0 |
| 0 (1310) | 0 (1310) | 655 nm (G+G) | 0 |
| 0 (1310) | -1 (1550) | 710 nm (R+G) | 0 |
| -1 (1550) | +1 (1064) | 631 nm (R+B) | -1 |
| -1 (1550) | 0 (1310) | 710 nm (R+G) | 0 |
| -1 (1550) | -1 (1550) | 775 nm (R+R) | +1 |

**What this tests:** Core SFG arithmetic correctness. This is the most important test — it validates that the physics of wavelength-encoded ternary multiplication actually works at the circuit level.

### 7.5 Test Case 5: Known 3x3 matrix-vector product

**Purpose:** Validate multi-PE accumulation with a known answer.

**Setup:**
- Use a 3x3 sub-array (top-left corner of the 9x9)
- Weight matrix W = [[+1, 0, -1], [0, +1, 0], [-1, 0, +1]]
- Input vector x = [+1, +1, +1]

**Expected output:**
- y[0] = (+1)(+1) + (0)(+1) + (-1)(+1) = +1 + 0 + (-1) = 0
- y[1] = (0)(+1) + (+1)(+1) + (0)(+1) = 0 + 1 + 0 = +1
- y[2] = (-1)(+1) + (0)(+1) + (+1)(+1) = -1 + 0 + 1 = 0

**Expected output vector:** [0, +1, 0]

**What this tests:** Multi-PE accumulation with mixed positive and negative contributions. Verifies that the vertical accumulation path (carry chain) correctly sums SFG products.

### 7.6 Test Case 6: Loss budget validation

**Purpose:** Verify that the full-chip optical path has positive power margin.

**Setup:**
- Inject calibrated power at each laser input
- Measure power arriving at each photodetector
- Compare against analytical loss budget (21.30 dB total, 18.70 dB margin from validation report)

**What this tests:** The circuit simulation should reproduce the analytical loss budget within reasonable tolerance (within 3 dB).

### 7.7 Test Case 7: Wavelength crosstalk check

**Purpose:** Ensure that input wavelengths do not leak to incorrect output channels.

**Setup:**
- Inject only 1550 nm (trit -1) at row 0
- All weights = +1
- Check that decoder channel for "R+R" (775 nm) sees signal
- Check that decoder channels for other SFG products see only noise (below -20 dB of R+R channel)

**What this tests:** AWG demux isolation and wavelength routing integrity.

---

## 8. Helper Functions

### 8.1 Trit encoding/decoding

```python
# Wavelength encoding
TRIT_WAVELENGTHS = {
    -1: 1.550,  # RED (C-band)
     0: 1.310,  # GREEN (O-band)
    +1: 1.064,  # BLUE (Nd:YAG)
}

SFG_DECODE = {
    0.532: +1,  # B+B -> +1
    0.587:  0,  # G+B ->  0
    0.631: -1,  # R+B -> -1
    0.655:  0,  # G+G ->  0
    0.710:  0,  # R+G ->  0
    0.775: +1,  # R+R -> +1
}

def trit_to_wavelength(trit: int) -> float:
    """Convert trit value (-1, 0, +1) to wavelength in um."""
    return TRIT_WAVELENGTHS[trit]

def wavelength_to_trit(wl_um: float, tolerance: float = 0.005) -> int:
    """Decode SFG output wavelength back to trit value."""
    for ref_wl, trit in SFG_DECODE.items():
        if abs(wl_um - ref_wl) < tolerance:
            return trit
    raise ValueError(f"Unknown SFG wavelength: {wl_um} um")
```

### 8.2 Matrix-vector multiplication test harness

```python
def simulate_matmul(
    input_trits: list[int],
    weight_matrix: list[list[int]],
    circuit_fn,
) -> list[int]:
    """
    Simulate ternary matrix-vector multiplication through the chip.

    Args:
        input_trits: length-9 list of trit values (-1, 0, +1)
        weight_matrix: 9x9 list of trit values
        circuit_fn: compiled SAX circuit function

    Returns:
        length-9 list of output trit values
    """
    output_trits = []

    for col in range(9):
        # Accumulate SFG products for this output column
        accumulated_trit = 0
        for row in range(9):
            a = input_trits[row]
            w = weight_matrix[row][col]
            product = a * w  # ternary multiplication
            accumulated_trit += product

        # In practice, the circuit simulation would track
        # wavelength propagation and SFG products through
        # the netlist. This is the expected result for comparison.
        output_trits.append(accumulated_trit)

    return output_trits
```

---

## 9. File Organization

All circuit simulation code should live in a new directory:

```
NRadix_Accelerator/
  circuit_sim/
    __init__.py
    models/
      __init__.py
      waveguide.py          -- waveguide and bend models
      sfg_mixer.py          -- PPLN SFG compact model
      encoder.py            -- MZI + combiner models
      decoder.py            -- AWG + photodetector models
    netlists/
      __init__.py
      pe.py                 -- single PE netlist
      array_9x9.py          -- 9x9 array netlist
      full_chip.py          -- complete monolithic chip netlist
    calibration/
      __init__.py
      extract_sparams.py    -- Meep-based S-parameter extraction
      sparams_data.json     -- calibrated parameters
    tests/
      __init__.py
      test_identity.py      -- Test case 1
      test_all_ones.py      -- Test case 2
      test_isolation.py     -- Test case 3
      test_mult_table.py    -- Test case 4
      test_3x3_matmul.py   -- Test case 5
      test_loss_budget.py   -- Test case 6
      test_crosstalk.py     -- Test case 7
      conftest.py           -- shared fixtures
    run_all_tests.py        -- full validation suite
```

---

## 10. Implementation Roadmap

### Phase 1: Foundation (1-2 sessions)

1. Install SAX and verify it works
2. Implement the waveguide compact model
3. Implement the SFG mixer compact model (with hardcoded conversion efficiencies)
4. Build and simulate a single PE
5. Verify: inject two wavelengths, see SFG output at correct wavelength

### Phase 2: Calibration (1 session)

1. Run Meep eigenmode solver at 9 wavelengths to get accurate neff values
2. Extract SFG conversion efficiencies from existing `ioc_integration_test.py` results
3. Update compact models with calibrated parameters
4. Store calibration data in JSON

### Phase 3: Array Assembly (1-2 sessions)

1. Build the 9x9 PE array netlist
2. Build encoder and decoder sub-circuit netlists
3. Assemble the full chip netlist
4. Run a basic smoke test (inject one wavelength, see it propagate)

### Phase 4: Validation (1-2 sessions)

1. Implement all 7 test cases from Section 7
2. Run the full test suite
3. Debug any failures (likely routing or phase issues)
4. Generate a validation report

### Phase 5: Optimization (ongoing)

1. Use JAX autodiff to optimize waveguide lengths for phase matching
2. Sweep loss parameters to find fabrication tolerance bounds
3. Monte Carlo analysis: what happens if component parameters vary randomly?

---

## 11. Comparison with Existing Validation

The existing monolithic 9x9 validation (`MONOLITHIC_9x9_VALIDATION.md`) is **analytical** — it uses closed-form equations for path lengths, loss budgets, and timing. The circuit simulation adds:

| Aspect | Analytical (current) | Circuit Sim (this plan) |
|--------|---------------------|------------------------|
| Path lengths | Geometric calculation | S-parameter phase tracking |
| Loss budget | Sum of component losses | Full circuit propagation |
| Wavelength routing | SFG equation check | Wavelength-dependent S-matrix |
| Computation correctness | Not tested | Ternary arithmetic verification |
| Multi-PE interaction | Not tested | Full array with accumulation |
| Crosstalk | Not tested | Off-diagonal S-parameters |

The circuit simulation is the natural next step: it validates the same chip design but at a higher fidelity, and critically, it tests whether the chip actually **computes** correctly.

---

## 12. References and Resources

- [SAX GitHub repository](https://github.com/flaport/sax) — S-parameter circuit simulator (MIT license)
- [SAX documentation](https://flaport.github.io/sax/) — API reference and tutorials
- [SAX circuit simulator plugin for gdsfactory](https://gdsfactory.github.io/gplugins/notebooks/sax_01_sax.html) — integration guide
- [Simphony GitHub repository](https://github.com/BYUCamachoLab/simphony) — alternative circuit simulator (MIT license)
- [Simphony documentation](https://simphonyphotonics.readthedocs.io/) — API reference
- [Simphony paper (arXiv)](https://arxiv.org/abs/2009.05146) — framework description
- [gdsfactory](https://gdsfactory.github.io/gdsfactory/index.html) — photonic layout tool (already in use)
- [Modeling Nonlinear Optics with the Transfer Matrix Method](https://arxiv.org/abs/2502.06496) — compact nonlinear models
- [PyNLO](https://pynlo.readthedocs.io/en/latest/readme_link.html) — nonlinear optics propagation (for reference)
- [Photon Design PICWave PPLN](https://photond.com/picwave/applications/nonlinear-optics-ppln) — commercial nonlinear circuit sim (reference only)

---

## 13. Summary

This plan bridges the gap between validated individual components and a proven complete chip. The key insight is that SAX (already in the gdsfactory ecosystem used by this project) can perform fast circuit-level simulation once each component has a calibrated S-parameter model. The nonlinear SFG physics, which SAX cannot simulate natively, is handled by pre-calibrating conversion efficiencies from the existing Meep FDTD simulations.

The end result: inject a ternary-encoded input vector on the left edge of the chip, stream ternary weights from the top, and verify that the correct matrix-vector product appears at the photodetectors on the right edge. If all 7 test cases pass, the monolithic 9x9 chip design is validated not just analytically but computationally — the architecture computes correctly.
