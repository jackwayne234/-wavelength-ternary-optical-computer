#!/bin/bash
# Wait for NEW 27x27 results, then run 81x81

LOG_DIR="/home/jackwayne/Desktop/Optical_computing/Research/data/wdm_validation"
SIM_DIR="/home/jackwayne/Desktop/Optical_computing/NRadix_Accelerator/simulations"
RESULTS_FILE="$LOG_DIR/wdm_27x27_array_results.txt"
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')

# Record current time to compare against
START_TIME=$(date +%s)

echo "=========================================="
echo "81x81 AUTO-LAUNCHER"
echo "=========================================="
echo "Started: $(date)"
echo "Waiting for NEW 27x27 results (newer than now)..."
echo ""

# Wait for results file to be modified AFTER we started
while true; do
    if [ -f "$RESULTS_FILE" ]; then
        FILE_TIME=$(stat -c %Y "$RESULTS_FILE")
        if [ "$FILE_TIME" -gt "$START_TIME" ]; then
            echo "New 27x27 results detected!"
            break
        fi
    fi
    sleep 10
    echo -n "."
done

echo ""
echo "=========================================="
echo "27x27 COMPLETE! Starting 81x81..."
echo "=========================================="
echo "Started: $(date)"
echo ""

cd "$SIM_DIR"
export OMP_NUM_THREADS=12

/home/jackwayne/miniconda/envs/meep_env/bin/python wdm_81x81_array_test.py 2>&1 | tee "$LOG_DIR/wdm_81x81_run_${TIMESTAMP}.log"

echo ""
echo "=========================================="
echo "81x81 COMPLETE!"
echo "Finished: $(date)"
echo "=========================================="
