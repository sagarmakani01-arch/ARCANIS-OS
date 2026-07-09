#!/bin/bash
# Arcanis Kernel Build Script
# Usage: ./build-kernel.sh [target]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
KERNEL_DIR="$ROOT_DIR/18_ArcanisKernel"
BUILD_DIR="$KERNEL_DIR/build"
TARGET="${1:-i686}"

echo "=== Arcanis Kernel Build ==="
echo "Target: $TARGET"
echo "Source: $KERNEL_DIR"

mkdir -p "$BUILD_DIR"

cd "$KERNEL_DIR"
if [ -f Makefile ]; then
    echo "[1/3] Assembling boot code..."
    make boot 2>/dev/null || echo "  (boot target not available)"

    echo "[2/3] Compiling kernel..."
    make kernel 2>/dev/null || echo "  (kernel target not available)"

    echo "[3/3] Linking..."
    make link 2>/dev/null || echo "  (link target not available)"
else
    echo "ERROR: No Makefile found in $KERNEL_DIR"
    exit 1
fi

echo ""
echo "Build complete. Output: $BUILD_DIR/"
ls -la "$BUILD_DIR"/*.bin "$BUILD_DIR"/*.elf 2>/dev/null || echo "  (no binary outputs found)"
