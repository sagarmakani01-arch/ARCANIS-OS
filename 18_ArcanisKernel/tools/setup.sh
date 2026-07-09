#!/bin/bash
# ArcanisKernel Setup Script

set -e

echo "========================================"
echo "  ArcanisKernel Development Setup"
echo "========================================"

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux"
    if command -v apt &> /dev/null; then
        sudo apt update
        sudo apt install -y nasm build-essential qemu-system-x86 wget
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y nasm gcc make qemu-system-x86 wget
    elif command -v pacman &> /dev/null; then
        sudo pacman -S nasm base-devel qemu-desktop wget
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS"
    if command -v brew &> /dev/null; then
        brew install nasm qemu
    else
        echo "Please install Homebrew first"
        exit 1
    fi
else
    echo "Unsupported OS. Install manually: NASM, i686-elf-gcc, QEMU"
    exit 1
fi

if ! command -v i686-elf-gcc &> /dev/null; then
    echo "Cross-compiler not found. Install i686-elf-gcc or see docs/BUILDING.md"
fi

echo ""
echo "Setup complete! Run 'make all' to build, 'make run' to test."
