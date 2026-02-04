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

## Cloud Simulations (Large Jobs)

For heavy simulations (like 81x81 PE arrays), use the cloud runner to spin up an AWS EC2 instance:

```bash
# One-time setup
pip install boto3 paramiko scp
aws configure  # Enter your AWS credentials
export AWS_KEY_PATH="~/.ssh/your-key.pem"
export AWS_KEY_NAME="your-key-name"

# Run simulation on 64-core cloud instance (512GB RAM)
python cloud_runner.py --sim kerr_resonator_sim.py --cores 64 --ram 512

# Use spot instances for 60-70% savings
python cloud_runner.py --sim kerr_resonator_sim.py --cores 64 --spot

# List available instance sizes
python cloud_runner.py --list-servers
```

Results download to `Research/data/cloud_results/`.

| Instance | vCPUs | RAM | On-Demand | Spot |
|----------|-------|-----|-----------|------|
| r7i.16xlarge | 64 | 512GB | $4.03/hr | $1.40/hr |
| r7i.24xlarge | 96 | 768GB | $6.05/hr | $2.10/hr |
| r7i.48xlarge | 192 | 1.5TB | $12.10/hr | $4.20/hr |

Instance auto-terminates when done.

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
