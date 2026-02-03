# SIMULATIONS

## Meep FDTD Electromagnetic Simulations

These files use Meep (MIT Electromagnetic Equation Propagation) for physics validation of optical components.

## Simulation Files

| File | Component | Status |
|------|-----------|--------|
| `./kerr_resonator_sim.py` | Kerr clock (617 MHz) | In Progress |
| `./clock_distribution_sim.py` | Clock skew validation | **NEW** |
| `./awg_demux_sim.py` | AWG demultiplexer | Complete |
| `./mzi_switch_sim.py` | MZI optical switch | Complete |
| `./soa_gate_sim.py` | SOA amplifier | Complete |
| `./directional_coupler_sim.py` | Directional coupler | Complete |
| `./waveguide_bend_sim.py` | Waveguide bends | Complete |

## Running Simulations

```bash
cd /home/jackwayne/Desktop/Optical_computing

# Activate Meep environment
source .mamba_env/bin/activate

# Run specific simulation
.mamba_env/bin/python3 Research/programs/simulations/kerr_resonator_sim.py --time-domain

# Run Kerr power sweep
.mamba_env/bin/python3 Research/programs/simulations/kerr_resonator_sim.py --sweep-power
```

## Output Locations

- CSV data: `Research/data/csv/`
- PNG plots: `Research/data/csv/*.png`
- HDF5 fields: `Research/data/` (large files, gitignored)

## Key Simulations for Validation

### 1. Kerr Resonator (Clock Generation)
- Target: 617 MHz self-pulsing via χ³ nonlinearity
- Status: Sweeping χ³ values to find bistability threshold

### 1b. Clock Distribution (NEW)
- Target: Validate clock reaches all PEs from central Kerr with <5% skew
- Tests: 9×9 array (integrated supercomputer validation design)
- Command: `.mamba_env/bin/python3 Research/programs/simulations/clock_distribution_sim.py --analyze-skew`

### 2. AWG Demultiplexer
- Target: Separate 5 output wavelengths from SFG mixer
- Verified: Crosstalk < -20 dB

### 3. SOA Amplifiers
- Target: 30 dB gain for signal regeneration
- Verified: Gain saturation behavior characterized

## Completed Simulation Results

See `Research/RESULTS_SUMMARY.md` for verified component parameters.
