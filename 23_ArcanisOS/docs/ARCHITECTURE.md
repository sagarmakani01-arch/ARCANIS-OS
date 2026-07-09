# ArcanisOS Architecture

## Overview

ArcanisOS is an AI-native operating system that places artificial intelligence at the core of every subsystem. Unlike traditional OS designs where AI is bolted on as an application layer, ArcanisOS weaves intelligence into the kernel, interface, and development toolchain.

## System Layers

```
┌─────────────────────────────────────────────┐
│              Application Layer               │
│  [Apps] [Services] [Extensions] [Themes]    │
├─────────────────────────────────────────────┤
│           Development Layer                  │
│  ArcanisLang | ArcanisIDE | ArcanisBuild    │
│              ArcanisPackageManager           │
├─────────────────────────────────────────────┤
│           Interface Layer                    │
│  ArcanisDesktop | ArcanisUI | ArcanisShell  │
├─────────────────────────────────────────────┤
│            AI Layer                          │
│  ArcanisBrain | ArcanisAgents | ArcanisMem  │
├─────────────────────────────────────────────┤
│           Kernel Layer                       │
│  Process Mgmt | Scheduler | Module System   │
├─────────────────────────────────────────────┤
│           Integration Layer                  │
│  EventBus | ApiGateway | Security Manager   │
└─────────────────────────────────────────────┘
```

## Component Architecture

### ArcanisKernel
The foundation of the OS. Manages processes, scheduling, and system resources. Features a priority-based round-robin scheduler, process isolation, and a modular extension system.

### ArcanisBrain
Central AI engine that provides natural language understanding, reasoning, and learning capabilities. Works with ArcanisMemory to build persistent knowledge.

### ArcanisAgents
Multi-agent system that creates, manages, and coordinates AI agents. Each agent has a specific role, capabilities, and task queue.

### ArcanisMemory
Hierarchical memory system supporting episodic, semantic, procedural, and working memory types. Includes TTL-based eviction and keyword indexing.

### ArcanisDesktop
Desktop environment with theming, widget system, dock shortcuts, and notification management. Supports dark/light modes and glassmorphism.

### ArcanisShell
AI-first command shell. Supports traditional commands and natural language input. Features command history, aliases, and AI mode toggle.

### ArcanisLang
Multi-language support with built-in definitions for TypeScript, Python, and ArcanisScript (a native AI-oriented language).

### ArcanisIDE
Built-in development environment with project management, file buffers, and language detection.

### ArcanisBuild
Build system supporting transpilation, optimization, and artifact management.

### ArcanisPackageManager
Package management with install, uninstall, update, and dependency resolution.

### Integration Layer
EventBus for decoupled communication, ApiGateway for RESTful interfaces, and SecurityManager for encryption and access control.

## Data Flow

1. User input enters via ArcanisShell or ArcanisUI
2. Input is interpreted by ArcanisBrain (NLU)
3. Intent is routed to appropriate subsystem
4. Kernel manages process execution
5. Agents handle specialized tasks
6. Memory stores and retrieves context
7. Events propagate changes across the system
8. Response is returned through the interface layer
