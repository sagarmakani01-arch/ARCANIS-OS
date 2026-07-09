#ifndef ARCANIS_SANDBOX_H
#define ARCANIS_SANDBOX_H

#include "vm.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct {
    uint32_t opcode;
    bool allowed;
} OpRule;

typedef struct Sandbox {
    bool enabled;
    uint64_t maxMemory;
    uint64_t maxInstructions;
    uint64_t maxCallDepth;
    double maxExecutionTime;
    uint64_t instructionLimit;
    uint64_t instructionCount;
    bool restrictIO;
    bool restrictNetwork;
    bool restrictFilesystem;
    bool restrictProcess;
    bool restrictReflection;
    bool restrictDebugger;
    OpRule* opOverrides;
    uint32_t opOverrideCount;
    bool (*customCheck)(struct Sandbox* sandbox, VM* vm, uint32_t opcode);
    void* userData;
} Sandbox;

void initSandbox(Sandbox* sandbox);
void freeSandbox(Sandbox* sandbox);
void sandboxEnable(Sandbox* sandbox);
void sandboxDisable(Sandbox* sandbox);
bool sandboxCheck(Sandbox* sandbox, VM* vm, uint32_t opcode);
void sandboxSetMemoryLimit(Sandbox* sandbox, uint64_t maxBytes);
void sandboxSetInstructionLimit(Sandbox* sandbox, uint64_t maxInstructions);
void sandboxSetTimeLimit(Sandbox* sandbox, double maxSeconds);
void sandboxRestrictIO(Sandbox* sandbox, bool restrict);
void sandboxRestrictNetwork(Sandbox* sandbox, bool restrict);
void sandboxRestrictFilesystem(Sandbox* sandbox, bool restrict);
void sandboxRestrictProcess(Sandbox* sandbox, bool restrict);
void sandboxAddOpOverride(Sandbox* sandbox, uint32_t opcode, bool allowed);

#endif
