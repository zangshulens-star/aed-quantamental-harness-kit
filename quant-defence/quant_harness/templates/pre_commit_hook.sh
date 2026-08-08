#!/bin/bash
# Quant Harness — Pre-commit verification hook
# Runs qh-verify on ALL critical claims before allowing commit.
# Install: cp this to .githooks/pre-commit && git config core.hooksPath .githooks

set -e

CLAIMS_FILE="validation/claims.yaml"

if [ ! -f "$CLAIMS_FILE" ]; then
    echo "[qh] No claims file at $CLAIMS_FILE — skipping verification."
    exit 0
fi

echo "[qh] Running qh-verify on critical claims..."
qh-verify --claims "$CLAIMS_FILE" --severity critical --output terminal

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "[qh] CRITICAL CLAIM VERIFICATION FAILED (exit $EXIT_CODE)."
    echo "[qh] Fix the failing claims or update expected values before committing."
    echo "[qh] To bypass (NOT RECOMMENDED): git commit --no-verify"
    exit 1
fi

echo "[qh] All critical claims PASS."
exit 0
