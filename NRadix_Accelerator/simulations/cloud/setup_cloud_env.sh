#!/bin/bash
# =============================================================================
# N-Radix Cloud Environment Setup Script
# =============================================================================
# Sets up a fresh Ubuntu instance for running Meep FDTD simulations
# Tested on: Ubuntu 22.04 LTS, Ubuntu 24.04 LTS
#
# Usage:
#   chmod +x setup_cloud_env.sh
#   ./setup_cloud_env.sh
#
# This script:
#   1. Updates system packages
#   2. Installs Miniconda
#   3. Creates meep_env with Python 3.12 and pymeep
#   4. Configures OpenMP threading
# =============================================================================

set -e  # Exit on any error

echo "=============================================="
echo "N-Radix Cloud Environment Setup"
echo "=============================================="
echo "Started: $(date)"
echo ""

# -----------------------------------------------------------------------------
# System Updates
# -----------------------------------------------------------------------------
echo "[1/5] Updating system packages..."
sudo apt-get update -y
sudo apt-get install -y wget curl htop tmux git

# -----------------------------------------------------------------------------
# Install Miniconda
# -----------------------------------------------------------------------------
MINICONDA_DIR="$HOME/miniconda"

if [ -d "$MINICONDA_DIR" ]; then
    echo "[2/5] Miniconda already installed at $MINICONDA_DIR"
else
    echo "[2/5] Installing Miniconda..."
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p $MINICONDA_DIR
    rm /tmp/miniconda.sh
fi

# Initialize conda for this session
eval "$($MINICONDA_DIR/bin/conda shell.bash hook)"
conda init bash

# -----------------------------------------------------------------------------
# Create Meep Environment
# -----------------------------------------------------------------------------
echo "[3/5] Creating meep_env with Python 3.12..."

# Check if environment exists
if conda env list | grep -q "meep_env"; then
    echo "       Environment meep_env already exists, updating..."
    conda activate meep_env
    conda install -y -c conda-forge pymeep matplotlib numpy scipy h5py
else
    echo "       Creating new environment..."
    conda create -y -n meep_env python=3.12
    conda activate meep_env

    # Install pymeep from conda-forge
    echo "[4/5] Installing pymeep and dependencies..."
    conda install -y -c conda-forge pymeep matplotlib numpy scipy h5py
fi

# Verify installation
echo ""
echo "[5/5] Verifying installation..."
python -c "import meep; print(f'Meep version: {meep.__version__}')"
python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"
python -c "import matplotlib; print(f'Matplotlib version: {matplotlib.__version__}')"

# -----------------------------------------------------------------------------
# Configure OpenMP
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "Configuring OpenMP Threading"
echo "=============================================="

# Detect CPU cores
NUM_CORES=$(nproc)
echo "Detected $NUM_CORES CPU cores"

# Add OpenMP settings to bashrc
if ! grep -q "OMP_NUM_THREADS" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# N-Radix Meep OpenMP Configuration" >> ~/.bashrc
    echo "export OMP_NUM_THREADS=$NUM_CORES" >> ~/.bashrc
    echo "export OMP_PROC_BIND=spread" >> ~/.bashrc
    echo "export OMP_PLACES=threads" >> ~/.bashrc
fi

# Set for current session
export OMP_NUM_THREADS=$NUM_CORES
export OMP_PROC_BIND=spread
export OMP_PLACES=threads

# -----------------------------------------------------------------------------
# Create simulation directory
# -----------------------------------------------------------------------------
SIMDIR="$HOME/nradix_simulations"
mkdir -p $SIMDIR
mkdir -p $SIMDIR/results
mkdir -p $SIMDIR/logs

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "Environment Details:"
echo "  - Conda environment: meep_env"
echo "  - Python version: 3.12"
echo "  - OpenMP threads: $NUM_CORES"
echo "  - Simulation dir: $SIMDIR"
echo ""
echo "To activate the environment:"
echo "  source ~/miniconda/bin/activate meep_env"
echo ""
echo "To run simulations:"
echo "  cd $SIMDIR"
echo "  ./run_81x81_cloud.sh"
echo ""
echo "Completed: $(date)"
