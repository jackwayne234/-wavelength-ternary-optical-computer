#!/bin/bash
#
# WDM Validation Overnight Runner
# ================================
# Runs WDM simulations using OpenMP for parallelism.
# Designed to run overnight while you sleep.
#
# Note: MPI is unavailable with Python 3.13, so we use OpenMP threading instead.
# The OMP_NUM_THREADS environment variable controls the number of threads.
#
# Usage: ./run_wdm_validation_overnight.sh
#
# Estimated runtime:
#   - Waveguide test: ~30-60 minutes
#   - 3×3 array test: ~2-4 hours
#   - Total: ~3-5 hours
#

set -e  # Exit on error

# Configuration
NUM_CORES=12
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="/home/jackwayne/Desktop/Optical_computing/Research/data/wdm_validation"

# Create log directory
mkdir -p "$LOG_DIR"

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
LOG_FILE="$LOG_DIR/wdm_overnight_${TIMESTAMP}.log"

echo "=================================================" | tee "$LOG_FILE"
echo "N-RADIX WDM VALIDATION - OVERNIGHT RUN" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "CPU cores: $NUM_CORES" | tee -a "$LOG_FILE"
echo "Log file: $LOG_FILE" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"

# Check for Meep
echo "" | tee -a "$LOG_FILE"
echo "Checking for Meep installation..." | tee -a "$LOG_FILE"
if ! python3 -c "import meep" 2>/dev/null; then
    echo "ERROR: Meep not found. Please activate your Meep conda environment:" | tee -a "$LOG_FILE"
    echo "  conda activate meep" | tee -a "$LOG_FILE"
    exit 1
fi
echo "Meep found!" | tee -a "$LOG_FILE"

# Set up OpenMP for parallelism (MPI unavailable with Python 3.13)
export OMP_NUM_THREADS=$NUM_CORES
echo "OpenMP threads: $OMP_NUM_THREADS" | tee -a "$LOG_FILE"

# Python interpreter path
PYTHON="/home/jackwayne/miniconda/envs/meep_env/bin/python"
echo "Python: $PYTHON" | tee -a "$LOG_FILE"

# =============================================================================
# TEST 1: WDM WAVEGUIDE
# =============================================================================
echo "" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"
echo "TEST 1: WDM WAVEGUIDE VALIDATION" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"

cd "$SCRIPT_DIR"

echo "Running with OpenMP ($OMP_NUM_THREADS threads)..." | tee -a "$LOG_FILE"
$PYTHON wdm_waveguide_test.py 2>&1 | tee -a "$LOG_FILE"

WG_EXIT=$?
echo "" | tee -a "$LOG_FILE"
echo "Waveguide test completed: $(date)" | tee -a "$LOG_FILE"
if [ $WG_EXIT -eq 0 ]; then
    echo "Waveguide test: PASSED" | tee -a "$LOG_FILE"
else
    echo "Waveguide test: FAILED (exit code $WG_EXIT)" | tee -a "$LOG_FILE"
    echo "Continuing to array test anyway..." | tee -a "$LOG_FILE"
fi

# =============================================================================
# TEST 2: WDM 3×3 ARRAY
# =============================================================================
echo "" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"
echo "TEST 2: WDM 3×3 ARRAY VALIDATION" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"

echo "Running with OpenMP ($OMP_NUM_THREADS threads)..." | tee -a "$LOG_FILE"
$PYTHON wdm_3x3_array_test.py 2>&1 | tee -a "$LOG_FILE"

ARRAY_EXIT=$?
echo "" | tee -a "$LOG_FILE"
echo "3×3 array test completed: $(date)" | tee -a "$LOG_FILE"
if [ $ARRAY_EXIT -eq 0 ]; then
    echo "3×3 array test: PASSED" | tee -a "$LOG_FILE"
else
    echo "3×3 array test: FAILED (exit code $ARRAY_EXIT)" | tee -a "$LOG_FILE"
fi

# =============================================================================
# SUMMARY
# =============================================================================
echo "" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"
echo "OVERNIGHT RUN COMPLETE" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"
echo "Finished: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Results:" | tee -a "$LOG_FILE"
echo "  Waveguide test: $([ $WG_EXIT -eq 0 ] && echo 'PASSED' || echo 'FAILED')" | tee -a "$LOG_FILE"
echo "  3×3 Array test: $([ $ARRAY_EXIT -eq 0 ] && echo 'PASSED' || echo 'FAILED')" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Output files:" | tee -a "$LOG_FILE"
echo "  $LOG_DIR/wdm_waveguide_results.png" | tee -a "$LOG_FILE"
echo "  $LOG_DIR/wdm_waveguide_results.txt" | tee -a "$LOG_FILE"
echo "  $LOG_DIR/wdm_3x3_array_results.png" | tee -a "$LOG_FILE"
echo "  $LOG_DIR/wdm_3x3_array_results.txt" | tee -a "$LOG_FILE"
echo "  $LOG_FILE" | tee -a "$LOG_FILE"
echo "=================================================" | tee -a "$LOG_FILE"

# Play a sound when done (optional, comment out if annoying)
# paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || true

echo ""
echo "Sweet dreams! Check results in the morning."
echo ""
