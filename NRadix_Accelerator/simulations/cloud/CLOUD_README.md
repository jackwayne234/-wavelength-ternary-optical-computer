# N-Radix 81x81 WDM Validation - Cloud Simulation Guide

This package contains everything needed to run the full-chip 81x81 WDM validation simulation on a cloud instance.

## Overview

The 81x81 array simulation validates that all 18 wavelengths (6 WDM triplets) can propagate through a full-scale systolic array without interference. This is the final validation step before physical prototyping.

**Estimated runtime:** 30-45 minutes on recommended instance
**Memory requirement:** 64GB RAM (simulation uses ~30GB)

## Recommended Cloud Instance

### Primary Recommendation: AWS c6i.8xlarge

| Spec | Value |
|------|-------|
| **vCPUs** | 32 |
| **RAM** | 64GB |
| **Cost** | ~$1.36/hr |
| **Est. Runtime** | 30-45 min |
| **Est. Total Cost** | ~$1.00 |

This gives you 32 cores (more than your local 12-core machine) with enough RAM for the simulation.

**AMI:** Ubuntu 22.04 LTS or Ubuntu 24.04 LTS

### Alternative Options

#### AWS EC2

| Instance | vCPUs | RAM | Cost/hr | Notes |
|----------|-------|-----|---------|-------|
| **c6i.8xlarge** | 32 | 64GB | ~$1.36 | **RECOMMENDED** - fast, enough RAM |
| c7i.8xlarge | 32 | 64GB | ~$1.43 | Newer gen, slightly faster |
| c6i.4xlarge | 16 | 32GB | ~$0.68 | Budget option (may be tight on RAM) |
| r6i.4xlarge | 16 | 128GB | ~$1.00 | More RAM if needed |

#### Google Cloud Platform (GCP)

| Instance | vCPUs | RAM | Cost/hr | Notes |
|----------|-------|-----|---------|-------|
| **c2-standard-30** | 30 | 120GB | ~$1.27 | Best GCP option |
| n2-highcpu-32 | 32 | 32GB | ~$1.13 | May be tight on RAM |
| n2-standard-32 | 32 | 128GB | ~$1.52 | Safe on RAM |

**Image:** Ubuntu 22.04 LTS

#### Azure

| Instance | vCPUs | RAM | Cost/hr | Notes |
|----------|-------|-----|---------|-------|
| **Standard_F32s_v2** | 32 | 64GB | ~$1.35 | Best Azure option |
| Standard_D32s_v5 | 32 | 128GB | ~$1.52 | More RAM |

**Image:** Ubuntu Server 22.04 LTS

## Quick Start

### 1. Launch Instance

Launch an **AWS c6i.8xlarge** (or equivalent) with:
- Ubuntu 22.04 or 24.04 LTS
- 32 vCPUs, 64GB RAM
- 50GB+ storage
- SSH key configured

### 2. Upload Simulation Files

From your local machine:

```bash
# Using the upload script (recommended)
./upload_to_cloud.sh ubuntu@<your-instance-ip> ~/.ssh/your-key.pem

# Or manually with scp
scp -i ~/.ssh/your-key.pem -r ./* ubuntu@<your-instance-ip>:~/nradix_simulations/
```

### 3. Set Up Environment (First Time Only)

SSH into your instance and run the setup script:

```bash
ssh -i ~/.ssh/your-key.pem ubuntu@<your-instance-ip>

cd ~/nradix_simulations
chmod +x *.sh
./setup_cloud_env.sh
```

This will:
- Install Miniconda
- Create a Python 3.12 environment with MPI-enabled Meep
- Install mpi4py and mpich for parallel execution

### 4. Run the Simulation

Use `tmux` or `screen` to keep the simulation running if you disconnect:

```bash
# Start a tmux session
tmux new -s meep

# Run the simulation
cd ~/nradix_simulations
./run_81x81_cloud.sh

# Detach from tmux: Ctrl+B, then D
# Reattach later: tmux attach -t meep
```

### 5. Monitor Progress

In another terminal:
```bash
# Watch the log file
tail -f ~/nradix_simulations/logs/wdm_81x81_*.log

# Check system resources
htop
```

### 6. Download Results

When the simulation completes:

```bash
# From your local machine
scp -i ~/.ssh/your-key.pem -r ubuntu@<your-instance-ip>:~/nradix_simulations/results ./cloud_results/
```

## Files Included

| File | Description |
|------|-------------|
| `setup_cloud_env.sh` | Environment setup (run once) |
| `run_81x81_cloud.sh` | Simulation runner with logging |
| `upload_to_cloud.sh` | Upload helper script |
| `wdm_81x81_array_test.py` | The main simulation |
| `wdm_*_array_test.py` | Smaller validation tests |
| `CLOUD_README.md` | This file |

## Output Files

After successful completion, you'll find in `~/nradix_simulations/results/run_<timestamp>/`:

| File | Description |
|------|-------------|
| `wdm_81x81_power_heatmap.png` | Power distribution across 81 output ports |
| `wdm_81x81_spectral_summary.png` | Wavelength response analysis |
| `wdm_81x81_array_results.txt` | Detailed numerical results |
| `wdm_81x81_*.log` | Simulation log with timing info |

## IMPORTANT: MPI vs OpenMP (Parallelism)

**The default `conda install pymeep` installs the `nompi` build which is SINGLE-THREADED.**

Setting `OMP_NUM_THREADS` does NOTHING with the nompi build. You MUST install the MPI version for multi-core parallelism.

### Quick Check: Is My Meep Parallel?

```bash
# Check which build you have
conda list pymeep
# Look for "mpi_mpich" in the build string - if you see "nompi", it's single-threaded!

# Correct output example:
# pymeep    1.31.0    mpi_mpich_py312h639cf41_0    conda-forge
```

### Installing MPI-Enabled Meep

```bash
conda install -c conda-forge pymeep=*=mpi_mpich* mpi4py mpich
```

### Running with MPI

```bash
# Use mpirun, not just python
mpirun -np 32 python simulation.py

# Or specify number of cores dynamically
mpirun -np $(nproc) python simulation.py
```

## Troubleshooting

### Out of Memory

If the simulation crashes with memory errors:
- Use a larger instance (64GB+ RAM)
- Reduce `RESOLUTION` in the simulation script (e.g., from 20 to 15)
- Close any other processes consuming memory

### Conda Not Found

If conda commands fail after setup:
```bash
source ~/miniconda/bin/activate meep_env
```

### Meep Import Error

If `import meep` fails:
```bash
conda activate meep_env
conda install -c conda-forge pymeep --force-reinstall
```

### Slow Performance (Only Using 1 Core)

Check that you have the MPI build installed:
```bash
conda list pymeep
# Should show "mpi_mpich" in the build string, NOT "nompi"

# If it shows nompi, reinstall with MPI:
conda install -c conda-forge pymeep=*=mpi_mpich* mpi4py mpich --force-reinstall
```

Make sure you're running with `mpirun`:
```bash
# WRONG - runs single-threaded even with MPI build
python simulation.py

# CORRECT - uses all cores
mpirun -np $(nproc) python simulation.py
```

### SSH Connection Timeout

For long simulations, add to your SSH config (`~/.ssh/config`):
```
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 10
```

## Cost Optimization Tips

1. **Use Spot/Preemptible instances** - 60-80% cheaper, but can be terminated
   - AWS Spot: ~$0.15/hr for r6i.2xlarge
   - GCP Preemptible: ~$0.10/hr for n2-highmem-8

2. **Run smaller tests first** - Validate with 27x27 before 81x81

3. **Stop instance when done** - Don't leave instances running after simulation completes

4. **Use the right region** - Prices vary; us-east-1 (AWS) and us-central1 (GCP) are often cheapest

## Technical Notes

### Why Python 3.12 (not 3.13)?

Python 3.13 has compatibility issues with some Meep dependencies. Python 3.12 is the sweet spot for stability.

### Why MPI (not OpenMP)?

- **The default pymeep is single-threaded!** The `nompi` conda build ignores `OMP_NUM_THREADS` entirely.
- MPI is required for any multi-core parallelism in Meep.
- Setup is straightforward: just install the MPI build and use `mpirun`.
- The setup script handles this automatically.

### Memory Estimation

Approximate memory usage:
- 27x27 array: ~8GB
- 81x81 array: ~24-32GB
- Resolution 20: baseline
- Resolution 30: ~2.25x more memory

### MPI Scaling Notes

- With MPI, use all available cores: `mpirun -np 64 python simulation.py`
- Scaling is NOT perfectly linear due to MPI communication overhead
- 64 cores gives roughly 1.5-1.7x speedup over 32 cores (not 2x)
- Sweet spot for 81x81 simulation: 32-64 cores
- Beyond 128 cores, diminishing returns - communication overhead dominates
- Larger simulations (960x960) would benefit from more cores

**64-core AWS options:**

| Instance | vCPUs | RAM | Cost/hr |
|----------|-------|-----|---------|
| c6i.16xlarge | 64 | 128GB | ~$2.72 |
| c7i.16xlarge | 64 | 128GB | ~$2.86 |

## Support

If you encounter issues, check the simulation log file for error messages. The log includes:
- System specifications
- Meep version
- Progress timestamps
- Any error messages

For architecture questions, refer to the main N-Radix documentation.
