#!/usr/bin/env bash
set -euo pipefail

# This script installs the full requirements, assuming you have already installed
# a CUDA-enabled PyTorch build compatible with your system.
#
# Recommended flow:
#   1) Follow https://pytorch.org/get-started/locally/ and install torch+cuda
#   2) Run this script

VENV_DIR="${VENV_DIR:-$HOME/.venvs/PortalRecruit}"
FORCE_RECREATE="${FORCE_RECREATE:-0}"

echo "[PortalRecruit] Using venv: $VENV_DIR"

if [[ -d "$VENV_DIR" && "$FORCE_RECREATE" != "1" ]]; then
  echo "[PortalRecruit] Venv already exists. Set FORCE_RECREATE=1 to recreate it."
else
  rm -rf "$VENV_DIR"
  python3.13 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install -U pip

echo "[PortalRecruit] NOTE: This GPU bootstrap does NOT choose CUDA wheels for you."
echo "[PortalRecruit] Install GPU torch first (per PyTorch docs), then run requirements:" 

echo "[PortalRecruit] Installing project requirements"
"$VENV_DIR/bin/pip" install -r requirements.txt

echo ""
echo "Done. Activate with:"
echo "  source \"$VENV_DIR/bin/activate\""
