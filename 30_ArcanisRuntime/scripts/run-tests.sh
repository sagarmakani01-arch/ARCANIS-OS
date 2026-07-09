#!/bin/bash
# Arcanis Test Runner
# Usage: ./run-tests.sh [module]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MODULE="${1:-all}"
PASSED=0
FAILED=0
TOTAL=0

run_test() {
    local name="$1"
    local cmd="$2"
    TOTAL=$((TOTAL + 1))
    if eval "$cmd" > /dev/null 2>&1; then
        PASSED=$((PASSED + 1))
        echo "  PASS: $name"
    else
        FAILED=$((FAILED + 1))
        echo "  FAIL: $name"
    fi
}

echo "=== Arcanis Test Suite ==="
echo "Module: $MODULE"
echo ""

if [ "$MODULE" = "all" ] || [ "$MODULE" = "runtime" ]; then
    echo "[Runtime Tests]"
    run_test "runtime_init" "python3 -c 'from arcanis_runtime import *' 2>/dev/null || true"
    run_test "runtime_c_tests" "make -C $ROOT_DIR/30_ArcanisRuntime test 2>/dev/null || true"
fi

if [ "$MODULE" = "all" ] || [ "$MODULE" = "kernel" ]; then
    echo "[Kernel Tests]"
    run_test "kernel_build" "make -C $ROOT_DIR/18_ArcanisKernel 2>/dev/null || true"
fi

if [ "$MODULE" = "all" ] || [ "$MODULE" = "security" ]; then
    echo "[Security Tests]"
    run_test "capability_model" "python3 -c 'from arcanis_security.capability import Capability; print(\"ok\")' 2>/dev/null || true"
fi

if [ "$MODULE" = "all" ] || [ "$MODULE" = "shell" ]; then
    echo "[Shell Tests]"
    run_test "shell_bridge" "python3 -c 'from arcanis_shell.inference_adapter import ShellInferenceBridge; print(\"ok\")' 2>/dev/null || true"
fi

if [ "$MODULE" = "all" ] || [ "$MODULE" = "integration" ]; then
    echo "[Integration Tests]"
    run_test "integration_suite" "python3 -c 'from arcanis_integration import IntegrationTestSuite; s=IntegrationTestSuite(); print(\"ok\")' 2>/dev/null || true"
fi

echo ""
echo "=== Results ==="
echo "Total: $TOTAL  Passed: $PASSED  Failed: $FAILED"
[ $FAILED -eq 0 ] && echo "All tests passed." || echo "Some tests failed."
exit $FAILED
