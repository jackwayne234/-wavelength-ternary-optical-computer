#!/bin/bash
#
# N-Radix MPI Meep Setup Script
# ==============================
# One-command setup for running Meep simulations with full parallelism.
#
# IMPORTANT: The default 'conda install pymeep' installs a SINGLE-THREADED build!
# This script installs the MPI version which uses ALL your CPU cores.
#
# Usage:
#   chmod +x setup_mpi_meep.sh
#   ./setup_mpi_meep.sh
#
# After setup, run simulations with:
#   mpirun -np $(nproc) python your_simulation.py
#

set -e

echo "=============================================="
echo "N-Radix MPI Meep Setup"
echo "=============================================="
echo "This script installs Meep with MPI support for"
echo "full multi-core parallelism."
echo ""

# Detect number of cores
NUM_CORES=$(nproc)
echo "Detected $NUM_CORES CPU cores"
echo ""

# Step 1: Install Miniconda if not present
if [ ! -d "$HOME/miniconda" ]; then
    echo "[1/4] Installing Miniconda..."
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p $HOME/miniconda
    rm /tmp/miniconda.sh
    $HOME/miniconda/bin/conda init bash
    source $HOME/miniconda/bin/activate
else
    echo "[1/4] Miniconda already installed"
    source $HOME/miniconda/bin/activate
fi

# Accept conda ToS if needed
echo "[2/4] Accepting Conda terms of service..."
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true

# Step 2: Create/update meep environment with MPI
echo "[3/4] Installing MPI Meep (this may take a few minutes)..."
if conda env list | grep -q "meep_env"; then
    echo "  Updating existing meep_env..."
    conda activate meep_env
    conda install -y -c conda-forge pymeep=1.31.0=mpi_mpich_py312h639cf41_0 mpi4py mpich numpy matplotlib h5py
else
    echo "  Creating new meep_env..."
    conda create -n meep_env python=3.12 -y
    conda activate meep_env
    conda install -y -c conda-forge pymeep=1.31.0=mpi_mpich_py312h639cf41_0 mpi4py mpich numpy matplotlib h5py
fi

# Step 3: Verify installation
echo "[4/4] Verifying installation..."
python -c "
import meep as mp
print(f'  Meep version: {mp.__version__}')
print(f'  MPI enabled: {mp.with_mpi()}')
if not mp.with_mpi():
    print('  ERROR: MPI not enabled! Something went wrong.')
    exit(1)
"

# Check mpirun
MPIRUN=$(which mpirun)
echo "  mpirun: $MPIRUN"

echo ""
echo "=============================================="
echo "SUCCESS! MPI Meep is ready."
echo "=============================================="
echo ""
echo "To run simulations with all $NUM_CORES cores:"
echo ""
echo "  source ~/miniconda/bin/activate meep_env"
echo "  mpirun -np $NUM_CORES python your_simulation.py"
echo ""
echo "Example:"
echo "  mpirun -np $NUM_CORES python wdm_81x81_array_test.py"
echo ""
echo "=============================================="
