#!/bin/bash
# Wait for 27x27 to finish, then run 81x81

LOG_DIR="/home/jackwayne/Desktop/Optical_computing/Research/data/wdm_validation"
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')

echo "Waiting for 27x27 to complete..."
echo "Will auto-launch 81x81 when done."
echo ""

# Wait for the 27x27 results file to appear
while [ ! -f "$LOG_DIR/wdm_27x27_array_results.txt" ]; do
    sleep 10
done

echo "=========================================="
echo "27x27 COMPLETE! Starting 81x81..."
echo "=========================================="
echo "Started: $(date)"
echo ""

cd /home/jackwayne/Desktop/Optical_computing/Research/programs/simulations
export OMP_NUM_THREADS=12

/home/jackwayne/miniconda/envs/meep_env/bin/python wdm_81x81_array_test.py 2>&1 | tee "$LOG_DIR/wdm_81x81_run_${TIMESTAMP}.log"

echo ""
echo "=========================================="
echo "81x81 COMPLETE!"
echo "Finished: $(date)"
echo "=========================================="
