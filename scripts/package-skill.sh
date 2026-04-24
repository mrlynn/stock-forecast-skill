#!/usr/bin/env bash
# Build a .skill zip that Claude can import. Run from the repository root.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${ROOT}/dist"
OUT_FILE="${OUT_DIR}/stock-forecast.skill"
mkdir -p "${OUT_DIR}"
rm -f "${OUT_FILE}"
(
  cd "${ROOT}"
  zip -r "${OUT_FILE}" stock-forecast -x "*.pyc" -x "*__pycache__*"
)
echo "Wrote ${OUT_FILE}"
unzip -l "${OUT_FILE}"
