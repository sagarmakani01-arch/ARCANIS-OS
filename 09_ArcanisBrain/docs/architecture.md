# Architecture

## Overview

ArcanisBrain follows a modular layered architecture. Each module is independent, communicating through the central `EventBus` and `Context` objects.

```
┌──────────────────────────────────────────────────────────┐
│                      API Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐       │
│  │   REST   │  │  GraphQL │  │   WebSocket      │       │
│  └──────────┘  └──────────┘  └──────────────────┘       │
├──────────────────────────────────────────────────────────┤
│                     ArcanisBrain Engine                    │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐│
│  │Reasoning │  Memory  │  Agents  │Personality│ Security ││
│  └──────────┴──────────┴──────────┴──────────┴──────────┘│
│                     EventBus / Context                     │
├──────────────────────────────────────────────────────────┤
│                     Storage Layer                          │
│              (JSON files, configurable)                    │
└──────────────────────────────────────────────────────────┘
```

## Engine Flow

1. **Input** → User message enters via API or direct `process()` call
2. **Security** → Input is scanned for blocked patterns
3. **Personality** → User profile loaded, input adapted
4. **Memory** → Relevant context retrieved from all memory stores
5. **Reasoning** → Task created, plan generated
6. **Agents** → Agents selected, tasks delegated, tools executed
7. **Response** → Final response composed, styled, stored in memory

## Key Design Decisions

- **Singleton EventBus** for decoupled module communication
- **Dataclass-based types** for type safety and serialization
- **Async-first** for non-blocking agent execution
- **Pluggable storage** with JSON persistence by default
