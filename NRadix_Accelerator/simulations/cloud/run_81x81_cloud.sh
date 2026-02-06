#!/bin/bash
# =============================================================================
# N-Radix 81x81 WDM Array Simulation Runner
# =============================================================================
# Runs the full-chip WDM validation simulation with logging and monitoring.
#
# Usage:
#   chmod +x run_81x81_cloud.sh
#   ./run_81x81_cloud.sh
#
# Requirements:
#   - Meep environment set up via setup_cloud_env.sh
#   - wdm_81x81_array_test.py in current directory
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIMDIR="${SIMDIR:-$HOME/nradix_simulations}"
RESULTS_DIR="$SIMDIR/results"
LOGS_DIR="$SIMDIR/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOGS_DIR/wdm_81x81_${TIMESTAMP}.log"

# Ensure directories exist
mkdir -p "$RESULTS_DIR"
mkdir -p "$LOGS_DIR"

# -----------------------------------------------------------------------------
# Detect CPU cores for MPI
# -----------------------------------------------------------------------------
NUM_CORES=$(nproc)

# NOTE: OpenMP/OMP_NUM_THREADS does NOT work with the default pymeep build!
# The conda-forge 'nompi' pymeep is SINGLE-THREADED.
# For parallelism, you MUST use MPI. See setup_mpi_meep.sh

echo "=============================================="
echo "N-Radix 81x81 WDM Array Simulation (MPI)"
echo "=============================================="
echo "Started: $(date)"
echo "Host: $(hostname)"
echo "CPU cores: $NUM_CORES"
echo "MPI processes: $NUM_CORES"
echo "Log file: $LOG_FILE"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# System Info
# -----------------------------------------------------------------------------
echo "System Information:" | tee -a "$LOG_FILE"
echo "  - OS: $(uname -a)" | tee -a "$LOG_FILE"
echo "  - CPU: $(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2)" | tee -a "$LOG_FILE"
echo "  - RAM: $(free -h | grep Mem | awk '{print $2}')" | tee -a "$LOG_FILE"
echo "  - Available RAM: $(free -h | grep Mem | awk '{print $7}')" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# -----------------------------------------------------------------------------
# Activate Conda Environment
# -----------------------------------------------------------------------------
echo "Activating meep_env..." | tee -a "$LOG_FILE"

# Find and source conda
if [ -f "$HOME/miniconda/bin/activate" ]; then
    source "$HOME/miniconda/bin/activate" meep_env
elif [ -f "/opt/conda/bin/activate" ]; then
    source "/opt/conda/bin/activate" meep_env
else
    echo "ERROR: Cannot find conda installation" | tee -a "$LOG_FILE"
    exit 1
fi

# Verify Python, Meep, and MPI
echo "Python: $(which python)" | tee -a "$LOG_FILE"
echo "Meep version: $(python -c 'import meep; print(meep.__version__)')" | tee -a "$LOG_FILE"
echo "MPI enabled: $(python -c 'import meep; print(meep.with_mpi())')" | tee -a "$LOG_FILE"
echo "mpirun: $(which mpirun)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check MPI is available
if ! python -c 'import meep; assert meep.with_mpi(), "MPI not enabled"' 2>/dev/null; then
    echo "ERROR: MPI Meep not installed!" | tee -a "$LOG_FILE"
    echo "Run ./setup_mpi_meep.sh first to install MPI-enabled Meep." | tee -a "$LOG_FILE"
    exit 1
fi

# -----------------------------------------------------------------------------
# Check for simulation script
# -----------------------------------------------------------------------------
SIM_SCRIPT="$SIMDIR/wdm_81x81_array_test.py"

if [ ! -f "$SIM_SCRIPT" ]; then
    # Try current directory
    if [ -f "./wdm_81x81_array_test.py" ]; then
        SIM_SCRIPT="./wdm_81x81_array_test.py"
    else
        echo "ERROR: Cannot find wdm_81x81_array_test.py" | tee -a "$LOG_FILE"
        echo "Please ensure the simulation file is in $SIMDIR or current directory" | tee -a "$LOG_FILE"
        exit 1
    fi
fi

echo "Simulation script: $SIM_SCRIPT" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# -----------------------------------------------------------------------------
# Pre-flight RAM check
# -----------------------------------------------------------------------------
AVAILABLE_GB=$(free -g | grep Mem | awk '{print $7}')
echo "Available RAM: ${AVAILABLE_GB}GB" | tee -a "$LOG_FILE"

if [ "$AVAILABLE_GB" -lt 24 ]; then
    echo "WARNING: Less than 24GB RAM available. 81x81 simulation may fail." | tee -a "$LOG_FILE"
    echo "Recommended: 32GB+ RAM for 81x81 array simulation." | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
fi

# -----------------------------------------------------------------------------
# Run Simulation
# -----------------------------------------------------------------------------
echo "=============================================="
echo "Starting Simulation"
echo "=============================================="
echo "" | tee -a "$LOG_FILE"

START_TIME=$(date +%s)

# Run with MPI using all available cores
echo "Running with MPI ($NUM_CORES processes)..." | tee -a "$LOG_FILE"
mpirun -np $NUM_CORES python "$SIM_SCRIPT" 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "" | tee -a "$LOG_FILE"
echo "=============================================="
echo "Simulation Complete"
echo "=============================================="
echo "Exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
echo "Duration: ${DURATION} seconds ($(($DURATION / 60)) minutes)" | tee -a "$LOG_FILE"
echo "Ended: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# -----------------------------------------------------------------------------
# Collect Results
# -----------------------------------------------------------------------------
echo "Collecting results..." | tee -a "$LOG_FILE"

# Copy output files to results directory with timestamp
OUTPUT_DIR="/home/jackwayne/Desktop/Optical_computing/Research/data/wdm_validation"
if [ -d "$OUTPUT_DIR" ]; then
    DEST_DIR="$RESULTS_DIR/run_${TIMESTAMP}"
    mkdir -p "$DEST_DIR"
    cp -r "$OUTPUT_DIR"/* "$DEST_DIR"/ 2>/dev/null || true
    echo "Results copied to: $DEST_DIR" | tee -a "$LOG_FILE"
else
    # Results may be in current directory
    if ls *.png *.txt 2>/dev/null; then
        DEST_DIR="$RESULTS_DIR/run_${TIMESTAMP}"
        mkdir -p "$DEST_DIR"
        mv *.png *.txt "$DEST_DIR"/ 2>/dev/null || true
        echo "Results moved to: $DEST_DIR" | tee -a "$LOG_FILE"
    fi
fi

# Copy log to results
cp "$LOG_FILE" "$DEST_DIR"/ 2>/dev/null || true

echo ""
echo "=============================================="
echo "Summary"
echo "=============================================="
echo "Log: $LOG_FILE"
echo "Results: $DEST_DIR"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "SUCCESS: Simulation completed successfully!"
else
    echo "FAILED: Simulation exited with code $EXIT_CODE"
fi
