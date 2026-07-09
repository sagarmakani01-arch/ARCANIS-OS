# ArcanisVM Build Script for Windows
# Usage: .\build.ps1 [Debug|Release]

param(
    [ValidateSet("Debug", "Release")]
    [string]$Config = "Release"
)

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OutDir = "$RootDir\out\$Config"

$Sources = @(
    "src\main.c", "src\vm.c", "src\bytecode.c", "src\value.c",
    "src\stack.c", "src\memory.c", "src\gc.c", "src\runtime.c",
    "src\compiler.c", "src\debugger.c", "src\profiler.c",
    "src\sandbox.c", "src\plugin.c"
)

$IncludeDirs = @("src", "include")

# Try to find a C compiler
$CC = $null
$possibleCCs = @("cl.exe", "gcc.exe", "clang.exe", "cc.exe")

foreach ($c in $possibleCCs) {
    $path = Get-Command $c -ErrorAction SilentlyContinue
    if ($path) { $CC = $c; break }
}

if (-not $CC) {
    # Check for MSVC via vswhere
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path $vswhere) {
        $vsPath = & $vswhere -latest -property installationPath
        $vcVars = "$vsPath\VC\Auxiliary\Build\vcvarsall.bat"
        if (Test-Path $vcVars) {
            Write-Host "Found Visual Studio at $vsPath"
            $env:VCVARS = $vcVars
            $CC = "cl.exe"
        }
    }
}

if (-not $CC) {
    Write-Error "No C compiler found. Install MSVC, GCC, or Clang."
    exit 1
}

Write-Host "=== ArcanisVM Build ==="
Write-Host "Compiler: $CC"
Write-Host "Config:   $Config"

# Create output directory
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

$cflags = @()
if ($CC -eq "cl.exe") {
    # MSVC
    $cflags += "/nologo", "/W3", "/std:c11"
    if ($Config -eq "Release") {
        $cflags += "/O2", "/MD"
    } else {
        $cflags += "/Zi", "/Od", "/MDd"
    }
    $outFlag = "/Fe:"
    $objExt = ".obj"

    # Call vcvars if available
    if ($env:VCVARS) {
        & cmd /c "call `"$env:VCVARS`" x64 2>&1 && set > %temp%\vcvars.txt"
        Get-Content "$env:TEMP\vcvars.txt" | ForEach-Object {
            if ($_ -match '^(\w+)=(.*)$') { Set-Item -Path "env:$($matches[1])" -Value $matches[2] }
        }
    }
} else {
    # GCC/Clang
    $cflags += "-Wall", "-Wextra", "-std=c11"
    if ($Config -eq "Release") {
        $cflags += "-O2", "-g"
    } else {
        $cflags += "-O0", "-g3"
    }
    $outFlag = "-o "
    $objExt = ".o"
}

# Add include paths
foreach ($dir in $IncludeDirs) {
    if ($CC -eq "cl.exe") { $cflags += "/I$RootDir\$dir" }
    else { $cflags += "-I$RootDir\$dir" }
}

# Compile each source file
$objects = @()
foreach ($src in $Sources) {
    $srcPath = "$RootDir\$src"
    $objName = [System.IO.Path]::GetFileNameWithoutExtension($src) + $objExt
    $objPath = "$OutDir\$objName"

    if ($CC -eq "cl.exe") {
        $cmd = "$CC /c $cflags $srcPath /Fo$objPath"
    } else {
        $cmd = "$CC -c $cflags $srcPath $outFlag$objPath"
    }

    Write-Host "Compiling $src..."
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) { Write-Error "Compilation failed: $src"; exit 1 }
    $objects += $objPath
}

# Link
$target = "$OutDir\arcanisvm.exe"
if ($CC -eq "cl.exe") {
    $linkCmd = "$CC $cflags $($objects -join ' ') /Fe$target"
} else {
    $linkCmd = "$CC $cflags $($objects -join ' ') -o $target -lm"
}

Write-Host "Linking..."
Invoke-Expression $linkCmd
if ($LASTEXITCODE -ne 0) { Write-Error "Linking failed"; exit 1 }

Write-Host ""
Write-Host "Build successful: $target"
Write-Host ""
Write-Host "Quick test:"
Write-Host "  $target --eval `"print('Hello from ArcanisVM!')`""
