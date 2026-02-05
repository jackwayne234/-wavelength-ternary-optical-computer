#!/bin/bash
# =============================================================================
# N-Radix Cloud Upload Script
# =============================================================================
# Packages simulation files and uploads to a cloud instance.
#
# Usage:
#   ./upload_to_cloud.sh <user@hostname> [ssh_key_path]
#
# Examples:
#   ./upload_to_cloud.sh ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com
#   ./upload_to_cloud.sh ubuntu@35.123.45.67 ~/.ssh/my-key.pem
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Parse Arguments
# -----------------------------------------------------------------------------
if [ -z "$1" ]; then
    echo "Usage: $0 <user@hostname> [ssh_key_path]"
    echo ""
    echo "Examples:"
    echo "  $0 ubuntu@ec2-xx-xx-xx-xx.compute.amazonaws.com"
    echo "  $0 ubuntu@35.123.45.67 ~/.ssh/my-key.pem"
    exit 1
fi

REMOTE_HOST="$1"
SSH_KEY="${2:-}"

# SSH options
if [ -n "$SSH_KEY" ]; then
    SSH_OPTS="-i $SSH_KEY"
    SCP_OPTS="-i $SSH_KEY"
else
    SSH_OPTS=""
    SCP_OPTS=""
fi

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NRADIX_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PACKAGE_NAME="nradix_cloud_sim"
TEMP_DIR="/tmp/${PACKAGE_NAME}_$$"
ARCHIVE="${PACKAGE_NAME}.tar.gz"
REMOTE_DIR="~/nradix_simulations"

echo "=============================================="
echo "N-Radix Cloud Upload"
echo "=============================================="
echo "Local root: $NRADIX_ROOT"
echo "Remote host: $REMOTE_HOST"
echo "Remote dir: $REMOTE_DIR"
echo ""

# -----------------------------------------------------------------------------
# Create Package
# -----------------------------------------------------------------------------
echo "Creating package..."
mkdir -p "$TEMP_DIR"

# Copy cloud scripts
cp "$SCRIPT_DIR/setup_cloud_env.sh" "$TEMP_DIR/"
cp "$SCRIPT_DIR/run_81x81_cloud.sh" "$TEMP_DIR/"
cp "$SCRIPT_DIR/CLOUD_README.md" "$TEMP_DIR/"

# Copy simulation files
SIM_DIR="$NRADIX_ROOT/NRadix_Accelerator/simulations"
if [ -d "$SIM_DIR" ]; then
    # Copy the 81x81 simulation
    cp "$SIM_DIR/wdm_81x81_array_test.py" "$TEMP_DIR/"

    # Copy other WDM tests if user wants to run the full sequence
    cp "$SIM_DIR/wdm_waveguide_test.py" "$TEMP_DIR/" 2>/dev/null || true
    cp "$SIM_DIR/wdm_3x3_array_test.py" "$TEMP_DIR/" 2>/dev/null || true
    cp "$SIM_DIR/wdm_9x9_array_test.py" "$TEMP_DIR/" 2>/dev/null || true
    cp "$SIM_DIR/wdm_27x27_array_test.py" "$TEMP_DIR/" 2>/dev/null || true
fi

# Create archive
cd /tmp
tar -czvf "$ARCHIVE" "${PACKAGE_NAME}_$$"
ARCHIVE_PATH="/tmp/$ARCHIVE"
ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)

echo "Package created: $ARCHIVE_PATH ($ARCHIVE_SIZE)"
echo ""

# -----------------------------------------------------------------------------
# Upload to Cloud
# -----------------------------------------------------------------------------
echo "Uploading to $REMOTE_HOST..."

# Create remote directory
ssh $SSH_OPTS "$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

# Upload archive
scp $SCP_OPTS "$ARCHIVE_PATH" "$REMOTE_HOST:$REMOTE_DIR/"

# Extract on remote
ssh $SSH_OPTS "$REMOTE_HOST" "cd $REMOTE_DIR && tar -xzf $ARCHIVE && mv ${PACKAGE_NAME}_$$/* . && rm -rf ${PACKAGE_NAME}_$$ $ARCHIVE"

# Make scripts executable
ssh $SSH_OPTS "$REMOTE_HOST" "chmod +x $REMOTE_DIR/*.sh"

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------
rm -rf "$TEMP_DIR"
rm -f "$ARCHIVE_PATH"

echo ""
echo "=============================================="
echo "Upload Complete!"
echo "=============================================="
echo ""
echo "Files uploaded to: $REMOTE_HOST:$REMOTE_DIR"
echo ""
echo "Next steps on the remote instance:"
echo "  1. SSH into instance:"
echo "     ssh $SSH_OPTS $REMOTE_HOST"
echo ""
echo "  2. Set up environment (first time only):"
echo "     cd $REMOTE_DIR"
echo "     ./setup_cloud_env.sh"
echo ""
echo "  3. Run simulation (in tmux for long runs):"
echo "     tmux new -s meep"
echo "     cd $REMOTE_DIR"
echo "     ./run_81x81_cloud.sh"
echo ""
echo "  4. Download results when done:"
echo "     scp $SCP_OPTS -r $REMOTE_HOST:$REMOTE_DIR/results ./cloud_results/"
echo ""
