#!/usr/bin/env bash
set -e

echo "============================================"
echo "  RDI Framework — Demo"
echo "============================================"
echo ""

PYTHON="${PYTHON:-python3}"

echo ">>> Running pipeline on sample data..."
$PYTHON -m rdi.cli run --input samples/ --output output/
echo ""

echo ">>> Validating provenance ledger..."
$PYTHON -m rdi.cli validate-ledger --ledger output/provenance_ledger.jsonl
echo ""

echo ">>> Risk Report:"
echo "--------------------------------------------"
cat output/risk_report.json
echo ""
echo "--------------------------------------------"
echo ""
echo "Demo complete."
