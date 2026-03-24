#!/bin/bash
# =============================================================================
# run_fdtd_optimize.sh — FDTD Adjoint Inverse Design Runner
# Runs fdtd_inverse_design.py (multiply_unit or demux) and pushes results
# to GitHub on exit/crash/disconnect.
#
# ONE-TIME RUNPOD SETUP:
# ----------------------
#   pip install "jax[cuda12]" numpy scipy matplotlib gdstk
#   git clone https://github.com/jackwayne234/New-ternary-optical-computer.git
#   cd New-ternary-optical-computer
#   export GITHUB_TOKEN=ghp_your_token_here
#
#   # Run multiply unit optimization (~3-5 hours on A40):
#   bash NRadix_Accelerator/simulation/run_fdtd_optimize.sh multiply_unit
#
#   # Run demux optimization (~25-75 hours on A40):
#   bash NRadix_Accelerator/simulation/run_fdtd_optimize.sh demux
#
# If SSH drops: tmux attach -t fdtd_opt
# =============================================================================

set -euo pipefail

COMPONENT="${1:-multiply_unit}"
if [[ "$COMPONENT" != "multiply_unit" && "$COMPONENT" != "demux" ]]; then
    echo "Usage: $0 [multiply_unit|demux]"
    echo "Default: multiply_unit"
    exit 1
fi

# ---------------------------------------------------------------------------
# Auto-launch inside tmux
# ---------------------------------------------------------------------------
if [ -z "${TMUX:-}" ]; then
    command -v tmux >/dev/null 2>&1 || { apt-get update -qq && apt-get install -y -qq tmux; }
    echo "[fdtd_opt] Launching in tmux session 'fdtd_opt'..."
    echo "[fdtd_opt] Reconnect: tmux attach -t fdtd_opt"
    exec tmux new-session -s fdtd_opt \
        "GITHUB_TOKEN=${GITHUB_TOKEN:-} bash $(realpath "$0") $COMPONENT"
fi

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GIT_EMAIL="chrisriner45@gmail.com"
GIT_NAME="Christopher Riner"
REPO_OWNER="jackwayne234"
REPO_NAME="New-ternary-optical-computer"
BRANCH="master"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RESULTS_DIR="$SCRIPT_DIR/results"

# ---------------------------------------------------------------------------
# Validate GitHub token
# ---------------------------------------------------------------------------
if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo ""
    echo "  ERROR: GITHUB_TOKEN is not set."
    echo "  Fix: export GITHUB_TOKEN=ghp_your_token_here"
    exit 1
fi

# ---------------------------------------------------------------------------
# Configure git
# ---------------------------------------------------------------------------
cd "$REPO_ROOT"
git config user.email "$GIT_EMAIL"
git config user.name "$GIT_NAME"
git remote set-url origin "https://${GITHUB_TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"

# ---------------------------------------------------------------------------
# Push-on-exit
# ---------------------------------------------------------------------------
_push_results() {
    local exit_code=$?
    echo ""
    echo "============================================================"
    if [ $exit_code -eq 0 ]; then
        echo "  FDTD optimization complete. Pushing results to GitHub..."
    else
        echo "  Run interrupted (exit $exit_code). Pushing checkpoints..."
    fi
    echo "============================================================"

    cd "$REPO_ROOT"

    if git add NRadix_Accelerator/simulation/results/ 2>/dev/null; then
        if git diff --cached --quiet; then
            echo "  Nothing new to push."
        else
            TIMESTAMP=$(date '+%Y-%m-%d %H:%M UTC')
            if [ $exit_code -eq 0 ]; then
                MSG="FDTD inverse design results ($COMPONENT) — ${TIMESTAMP}"
            else
                MSG="FDTD inverse design checkpoints ($COMPONENT, interrupted) — ${TIMESTAMP}"
            fi
            git commit -m "$MSG"
            git push origin "$BRANCH"
            echo "  Pushed to github.com/${REPO_OWNER}/${REPO_NAME}"
        fi
    else
        echo "  WARNING: git add failed."
    fi
}

trap '_push_results' EXIT SIGINT SIGTERM SIGHUP

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  NRadix FDTD Adjoint Inverse Design"
echo "  Component: $COMPONENT"
echo "  Host:      $(hostname)"
echo "  Start:     $(date)"
echo "  GPU:       $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo 'not detected')"
echo "  tmux:      session 'fdtd_opt' (reconnect: tmux attach -t fdtd_opt)"
echo "============================================================"
echo ""

# Check density files exist
if [ ! -f "$RESULTS_DIR/${COMPONENT}_density.npy" ]; then
    echo "  ERROR: ${COMPONENT}_density.npy not found in results/"
    echo "  Run mac_inverse_design.py first."
    exit 1
fi

# XLA flags for GPU performance
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.90
export XLA_FLAGS="--xla_gpu_enable_triton_gemm=false"

mkdir -p "$RESULTS_DIR"
cd "$SCRIPT_DIR"

echo "Starting FDTD adjoint optimization for: $COMPONENT"
echo "Logs below. Checkpoints save every 50 iterations."
echo ""

python3 fdtd_inverse_design.py "$COMPONENT" 2>&1 | tee "results/fdtd_optimize_${COMPONENT}.log"

echo ""
echo "Optimization complete."
echo "Run fdtdx_validation.py to validate the optimized density."
