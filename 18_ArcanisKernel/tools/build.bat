@echo off
REM ArcanisKernel Build Script for Windows (WSL)

echo ========================================
echo   ArcanisKernel Build System
echo ========================================

if "%1"=="help" goto help
if "%1"=="clean" goto clean
if "%1"=="" goto build

echo Unknown option: %1
goto help

:build
echo Building ArcanisKernel...
wsl make all
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful!
    echo Output: build/arcanis.img
) else (
    echo.
    echo Build failed!
)
goto end

:clean
echo Cleaning build artifacts...
wsl make clean
goto end

:help
echo ArcanisKernel Build Script
echo ==========================
echo   build.bat          - Build kernel
echo   build.bat clean    - Clean build
echo   build.bat help     - Show this help
echo.
echo Requirements:
echo   - WSL2 with Ubuntu
echo   - NASM, i686-elf-gcc, GNU ld
echo.
echo See docs/BUILDING.md for details
goto end

:end
pause
