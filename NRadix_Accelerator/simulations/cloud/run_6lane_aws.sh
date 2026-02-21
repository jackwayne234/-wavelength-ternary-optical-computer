#!/bin/bash
# ============================================================================
# AWS Cloud Runner: 6-Lane IOC Integration Test
# ============================================================================
#
# Designed for AWS EC2 compute-optimized instances:
#   - c7i.4xlarge  (16 vCPUs, 32GB)  — good balance, ~$0.68/hr
#   - c7i.8xlarge  (32 vCPUs, 64GB)  — fast, ~$1.36/hr
#   - c7i.16xlarge (64 vCPUs, 128GB) — blazing, ~$2.72/hr
#   - hpc7a.96xlarge (192 vCPUs)     — overkill but ~15 min total
#
# Estimated run times (all 36 simulations):
#   16 cores:  ~30-40 min (6 triplets × ~5 min each, running 6 at once)
#   32 cores:  ~15-20 min
#   64 cores:  ~10-15 min
#
# SETUP (run once on fresh EC2 instance):
#   1. Launch Amazon Linux 2023 or Ubuntu 22.04 instance
#   2. Run this script with --setup flag first
#   3. Then run without --setup to execute the test
#
# Usage:
#   chmod +x run_6lane_aws.sh
#   ./run_6lane_aws.sh --setup    # First time: install dependencies
#   ./run_6lane_aws.sh            # Run the test
#   ./run_6lane_aws.sh --download # Download results to local machine
#
# ============================================================================

set -e

WORK_DIR="$HOME/nradix_test"
CONDA_ENV="meep_env"
RESULTS_DIR="$WORK_DIR/results"
REPO_URL="http://gitea:3000/chris/optical-computing-workspace.git"
# For AWS, clone from GitHub if available, or upload the test script directly
SCRIPT_PATH="NRadix_Accelerator/simulations/ioc_6lane_integration_test.py"

# Auto-detect cores
TOTAL_CORES=$(nproc)
echo "Detected $TOTAL_CORES CPU cores"

setup_environment() {
    echo "============================================"
    echo "  SETTING UP MEEP ENVIRONMENT ON AWS"
    echo "============================================"

    # Install system dependencies
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y build-essential wget git libopenmpi-dev openmpi-bin
    elif command -v yum &>/dev/null; then
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y wget git openmpi openmpi-devel
        echo 'export PATH=/usr/lib64/openmpi/bin:$PATH' >> ~/.bashrc
        export PATH=/usr/lib64/openmpi/bin:$PATH
    fi

    # Install Miniconda if not present
    if [ ! -d "$HOME/miniconda" ]; then
        echo "Installing Miniconda..."
        wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
        bash /tmp/miniconda.sh -b -p $HOME/miniconda
        rm /tmp/miniconda.sh
    fi

    export PATH="$HOME/miniconda/bin:$PATH"
    eval "$(conda shell.bash hook)"

    # Create meep environment
    if ! conda env list | grep -q $CONDA_ENV; then
        echo "Creating Meep environment..."
        conda create -n $CONDA_ENV -y python=3.11
    fi

    conda activate $CONDA_ENV

    # Install Meep and dependencies
    echo "Installing Meep..."
    conda install -y -c conda-forge pymeep pymeep-extras
    pip install matplotlib numpy mpi4py

    echo ""
    echo "  ✓ Environment ready!"
    echo "  Python: $(which python)"
    echo "  Meep: $(python -c 'import meep; print(meep.__version__)' 2>/dev/null || echo 'checking...')"
    echo ""
}

run_test() {
    echo "============================================"
    echo "  RUNNING 6-LANE IOC INTEGRATION TEST"
    echo "  Cores: $TOTAL_CORES"
    echo "============================================"

    export PATH="$HOME/miniconda/bin:$PATH"
    eval "$(conda shell.bash hook)"
    conda activate $CONDA_ENV

    mkdir -p $WORK_DIR $RESULTS_DIR

    # Check if test script exists
    if [ ! -f "$WORK_DIR/$SCRIPT_PATH" ]; then
        echo "Test script not found. Please copy the repo or upload the script:"
        echo "  scp -r NRadix_Accelerator/ ec2-user@<ip>:$WORK_DIR/"
        echo ""
        echo "Or clone from git:"
        echo "  cd $WORK_DIR && git clone <repo-url>"
        exit 1
    fi

    cd $WORK_DIR

    PYTHON_BIN="$HOME/miniconda/envs/$CONDA_ENV/bin/python"

    echo ""
    echo "Starting parallel execution at $(date)"
    echo "Running 6 triplets concurrently across $TOTAL_CORES cores..."
    echo ""

    # Use the parallel mode — runs all 6 triplets as concurrent subprocesses
    $PYTHON_BIN $SCRIPT_PATH \
        --parallel \
        --cores $TOTAL_CORES \
        --python $PYTHON_BIN \
        --output $RESULTS_DIR

    echo ""
    echo "Completed at $(date)"
    echo "Results in: $RESULTS_DIR"
    echo ""

    # List all output files
    echo "Output files:"
    find $RESULTS_DIR -type f | sort
}

download_hint() {
    echo "============================================"
    echo "  DOWNLOAD RESULTS"
    echo "============================================"
    echo ""
    echo "From your local machine, run:"
    echo ""
    echo "  scp -r ec2-user@<instance-ip>:$RESULTS_DIR/ ~/Desktop/ioc_6lane_results/"
    echo ""
    echo "Or use rsync:"
    echo "  rsync -avz ec2-user@<instance-ip>:$RESULTS_DIR/ ~/Desktop/ioc_6lane_results/"
    echo ""
    echo "Files to look for:"
    echo "  - ioc_6lane_results.txt    (machine-readable summary)"
    echo "  - ioc_6lane_summary.png    (heatmap of all 36 tests)"
    echo "  - T1/ through T6/          (per-triplet plots and logs)"
    echo ""
}

# Parse arguments
case "${1:-}" in
    --setup)
        setup_environment
        ;;
    --download)
        download_hint
        ;;
    *)
        run_test
        ;;
esac
