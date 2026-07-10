# Arcanis OS — Architecture Guide

## Overview

Arcanis OS is an AI-native operating system built from first principles. It combines a traditional microkernel architecture with modern AI capabilities, containerization, and virtualization.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Space Applications                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Shell    │ │   GUI    │ │   Apps   │ │   AI     │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│       │            │            │            │              │
├───────┼────────────┼────────────┼────────────┼──────────────┤
│       │         System Libraries              │              │
│  ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐ ┌────┴─────┐      │
│  │   libc   │ │  libgui  │ │  libnet  │ │  libai   │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
├───────┼────────────┼────────────┼────────────┼──────────────┤
│                    System Calls (46)                         │
├─────────────────────────────────────────────────────────────┤
│                       Kernel Space                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    Microkernel                        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │   │
│  │  │ Process │ │ Memory  │ │   IPC   │ │   VFS   │  │   │
│  │  │ Manager │ │ Manager │ │         │ │         │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Network  │ │ Security │ │   FS     │ │  Driver  │      │
│  │  Stack   │ │ Module   │ │ Drivers  │ │  Model   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    Hardware Abstraction Layer                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │   PCI    │ │   USB    │ │   ATA    │ │   VGA    │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Microkernel (`18_ArcanisKernel`)

The microkernel provides minimal core functionality:
- **Process Management**: Fork, exec, wait, kill, signals
- **Memory Management**: Physical (PMM) and virtual (VMM) memory managers
- **IPC**: Message queues, shared memory, semaphores
- **Scheduling**: 8-level MLFQ with priority aging
- **System Calls**: 46 syscalls for all OS operations

### 2. Filesystem

- **VFS Layer**: Virtual filesystem abstraction
- **ext2 Driver**: Full ext2 filesystem implementation
- **Memory-mapped Files**: mmap/munmap with page table management
- **Device Files**: /dev, /proc, /sys virtual filesystems

### 3. Networking

- **TCP/IP Stack**: Full network stack implementation
- **DNS Resolver**: Domain name resolution
- **HTTP Client**: HTTP/HTTPS request handling
- **DHCP Client**: Automatic IP configuration
- **Firewall**: Packet filtering with iptables-like interface
- **VPN**: Encrypted tunnel support

### 4. Security

- **User Authentication**: Multi-user support with PAM
- **Capability Model**: Fine-grained permission control
- **Encryption**: AES-128/192/256, RSA
- **Password Manager**: Encrypted credential storage
- **Audit Logging**: Security event tracking

### 5. Virtualization

- **Hypervisor**: Type-2 hypervisor for VM management
- **Container Runtime**: Docker-compatible containerization
- **Namespaces**: PID, mount, network, UTS, IPC, user
- **Cgroups**: Resource limiting and accounting

### 6. AI Integration

- **Inference Engine**: On-device AI inference
- **Intent Classifier**: Natural language understanding
- **NL Shell**: Natural language command processing
- **Knowledge Base**: Local knowledge storage

### 7. GUI/Desktop

- **Window Manager**: Tiling and floating windows
- **GUI Toolkit**: 15 widget types
- **File Manager**: Graphical file browser
- **Terminal Emulator**: ANSI escape sequence support

## Memory Layout

```
0x00000000 - 0x000FFFFF    BIOS/Reserved (1MB)
0x00100000 - 0x002FFFFF    Kernel Space (2MB)
0x00300000 - 0x00FFFFFF    Free Memory
0x01000000 - 0x0FFFFFFF    User Space (240MB)
0x10000000 - 0xFFFFFFFF    Kernel Modules (2GB)
```

## Process States

```
Created → Running → Waiting → Terminated
    ↓         ↓
  Paused    Stopped
```

## System Call Interface

| Category | Syscalls |
|----------|----------|
| Process  | fork, exec, exit, wait, kill, getpid, signal |
| Memory   | mmap, munmap, brk, mprotect |
| File     | open, close, read, write, lseek, stat, unlink |
| Network  | socket, bind, listen, accept, connect, send, recv |
| IPC      | msgget, msgsnd, msgrcv, shmget, semget, semop |
| User     | login, setuid, getuid |
| Package  | pkg install, pkg remove |
| System   | svc, sync, reboot, shutdown |

## Driver Model

- **Universal Driver Model**: Auto-detection and binding
- **PCI Bus Manager**: Device enumeration and configuration
- **USB Support**: Hot-plug detection
- **GPU Abstraction**: Software and hardware rendering

## Build System

The OS uses a custom build system with:
- Cross-compiler for x86 (i686-elf-gcc)
- NASM assembler for boot/kernel code
- Custom linker scripts
- QEMU integration for testing

## Testing

- Unit tests for all components
- Integration tests for system workflows
- Performance benchmarks
- Security audit tests

## Version History

- v1.0.0: Foundation (kernel, shell, filesystem)
- v1.1.0: Networking and multi-user
- v1.2.0: Persistent storage and dev tools
- v1.3.0: GUI and desktop environment
- v1.4.0: Network applications
- v1.5.0: Shell scripting and apps
- v1.6.0: Network tools and security
- v1.7.0: Virtualization and containers
- v2.0.0: Production release with testing and documentation
