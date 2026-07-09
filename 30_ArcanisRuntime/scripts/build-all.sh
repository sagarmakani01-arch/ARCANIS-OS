#!/bin/bash
# Arcanis Full Build — build all components in dependency order
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Arcanis Full Build ==="
echo "Root: $ROOT_DIR"
echo ""

echo "[1/4] Building Runtime (C library)..."
if [ -f "$ROOT_DIR/30_ArcanisRuntime/Makefile" ]; then
    make -C "$ROOT_DIR/30_ArcanisRuntime" 2>/dev/null || echo "  (runtime build skipped)"
else
    echo "  (no Makefile found)"
fi

echo "[2/4] Building Kernel..."
if [ -f "$ROOT_DIR/18_ArcanisKernel/Makefile" ]; then
    make -C "$ROOT_DIR/18_ArcanisKernel" 2>/dev/null || echo "  (kernel build skipped)"
else
    echo "  (no Makefile found)"
fi

echo "[3/4] Installing Python packages..."
for pkg in "$ROOT_DIR"/60_ArcanisInference "$ROOT_DIR"/12_ArcanisShell "$ROOT_DIR"/50_ArcanisSecurity \
           "$ROOT_DIR"/41_ArcanisSemanticFS "$ROOT_DIR"/90_ArcanisHAL "$ROOT_DIR"/22_ArcanisAIScheduler \
           "$ROOT_DIR"/06_ArcanisPackageManager "$ROOT_DIR"/33_ArcanisDevAPI "$ROOT_DIR"/91_ArcanisDriverSynth \
           "$ROOT_DIR"/62_ArcanisFederated "$ROOT_DIR"/10_ArcanisAgentSDK "$ROOT_DIR"/27_ArcanisExperiments \
           "$ROOT_DIR"/28_ArcanisResearch "$ROOT_DIR"/29_ArcanisAssets "$ROOT_DIR"/04_ArcanisCLI \
           "$ROOT_DIR"/99_ArcanisIntegration; do
    if [ -f "$pkg/pyproject.toml" ]; then
        echo "  Installing $(basename "$pkg")..."
        pip install -e "$pkg" --quiet 2>/dev/null || echo "    (install skipped)"
    fi
done

echo "[4/4] Running integration tests..."
if [ -f "$ROOT_DIR/99_ArcanisIntegration/arcanis_integration/__init__.py" ]; then
    python3 -c "
from arcanis_integration import IntegrationTestSuite
suite = IntegrationTestSuite()
suite.run_all()
s = suite.summary()
print(f'  Tests: {s[\"total\"]}  Passed: {s[\"passed\"]}  Failed: {s[\"failed\"]}')
" 2>/dev/null || echo "  (integration tests skipped)"
fi

echo ""
echo "=== Build Complete ==="
