# Communication Between Projects

**Path:** `architecture/communication.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Principles

1. **Explicit contracts** — Every communication channel has a defined schema, version, and protocol
2. **Decoupled senders and receivers** — No direct function calls across project boundaries
3. **Auditability** — All cross-project communication is logged (metadata only, not payload)
4. **Graceful degradation** — If a dependency is unavailable, the system degrades rather than crashes

## Communication Layers

### Layer 0: In-Kernel IPC (Projects 20–39)

- **Shared memory rings** — Lock-free, single-producer single-consumer rings for high-throughput communication
- **Capability-passing** — IPC includes capability delegation; no ambient authority
- **Latency target:** <1µs per message

### Layer 1: System Message Bus (Projects 40–59)

- **Pub/sub event bus** — System-wide events (device plugged, process spawned, network change)
- **Structured events** — All events use protobuf-like schemas with mandatory version field
- **Filterable subscriptions** — Subscribers express predicates; events are filtered at the bus level

### Layer 2: AI Model Channels (Projects 60–79)

- **Inference RPC** — Specialized protocol for model serving with batching, caching, and priority queues
- **Training data pipelines** — Streaming channels with privacy filters built in
- **Model version negotiation** — Clients request minimum model version; server responds with best available

### Layer 3: User-Facing Interfaces (Projects 80–89)

- **Session protocol** — Persistent connection with state synchronization
- **Intent schema** — Structured representation of user intent (not raw text)
- **Feedback channel** — Users provide implicit/explicit feedback that flows back to model training

## Contract Lifecycle

1. **Draft** — Proposed contract, not implemented
2. **Experimental** — Implemented but may change without notice
3. **Stable** — Backward-compatible changes only
4. **Deprecated** — Still works but consumers should migrate
5. **Retired** — No longer available

## Error Handling

- **Timeouts** — Every communication has a configurable timeout with a sensible default
- **Retries** — Idempotent operations retry with exponential backoff
- **Circuit breakers** — Repeated failures trip a breaker; traffic is redirected to fallback
- **Dead letter queues** — Undeliverable messages are stored for analysis

---

*Communication is the architecture. Everything else is implementation.*
