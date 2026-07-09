# ArcanisOS API Reference

## Core Classes

### ArcanisOS
Main system class that integrates all components.

```typescript
const os = new ArcanisOS();
await os.boot();
await os.executeCommand("natural language input");
await os.shutdown();
```

### ArcanisKernel
```typescript
kernel.createProcess(name, executable?, priority?, parentPid?)
kernel.killProcess(pid)
kernel.getProcess(pid)
kernel.listProcesses()
kernel.getStats()
```

### ArcanisBrain
```typescript
brain.think(input: string): Promise<Thought>
brain.understand(input: string): Promise<Intent>
brain.learn(input: string, output: string, feedback?: number): Promise<void>
brain.reason(premises: string[]): Promise<string>
```

### ArcanisMemory
```typescript
memory.store(key, value, type?, ttl?, metadata?): MemoryEntry
memory.recall(key: string): MemoryEntry[]
memory.forget(id: string): boolean
memory.clear(type?: MemoryType): void
memory.stats(): { total: number; byType: Record<string, number> }
```

### EventBus
```typescript
bus.emit(type: string, source: string, data: unknown): void
bus.on(type: string, handler: (event: BusEvent) => void): void
bus.off(type: string, handler): void
bus.once(type: string, handler): void
bus.getHistory(type?: string): BusEvent[]
```

### ApiGateway
```typescript
api.register(endpoint: ApiEndpoint): void
api.unregister(method: string, path: string): void
api.call(method, path, params?, body?): Promise<ApiResponse>
```

### SecurityManager
```typescript
security.checkPermission(policyId: string, permission: Permission): boolean
security.encrypt(data: string): { iv: string; encrypted: string }
security.decrypt(iv: string, encrypted: string): string
```

## Configuration

Default config at `config/default.json` supports:
- System settings (name, version, language, timezone)
- Kernel settings (maxProcesses, schedulerTickMs, securityLevel)
- AI settings (model, temperature, maxTokens, memoryLimit)
- Interface settings (theme, shell behavior)
- Security settings (encryption, policy, auditLog)
- Development settings (defaultLanguage, buildOptimization)
