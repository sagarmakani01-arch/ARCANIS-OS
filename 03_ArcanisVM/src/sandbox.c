#include "sandbox.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <sys/time.h>
#endif

static double getSandboxTime(void) {
#ifdef _WIN32
    FILETIME ft;
    GetSystemTimeAsFileTime(&ft);
    return (double)(((ULONGLONG)ft.dwHighDateTime << 32) | ft.dwLowDateTime) / 10000000.0;
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (double)tv.tv_sec + (double)tv.tv_usec / 1000000.0;
#endif
}

void initSandbox(Sandbox* sandbox) {
    memset(sandbox, 0, sizeof(Sandbox));
    sandbox->enabled = false;
    sandbox->maxMemory = 64 * 1024 * 1024;
    sandbox->maxInstructions = 10000000;
    sandbox->maxCallDepth = 256;
    sandbox->maxExecutionTime = 5.0;
    sandbox->instructionLimit = sandbox->maxInstructions;
    sandbox->instructionCount = 0;
    sandbox->restrictIO = false;
    sandbox->restrictNetwork = true;
    sandbox->restrictFilesystem = true;
    sandbox->restrictProcess = true;
    sandbox->restrictReflection = false;
    sandbox->restrictDebugger = false;
    sandbox->opOverrides = NULL;
    sandbox->opOverrideCount = 0;
    sandbox->customCheck = NULL;
    sandbox->userData = NULL;
}

void freeSandbox(Sandbox* sandbox) {
    free(sandbox->opOverrides);
    sandbox->opOverrides = NULL;
    sandbox->opOverrideCount = 0;
}

void sandboxEnable(Sandbox* sandbox) {
    sandbox->enabled = true;
    sandbox->instructionCount = 0;
}

void sandboxDisable(Sandbox* sandbox) {
    sandbox->enabled = false;
}

bool sandboxCheck(Sandbox* sandbox, VM* vm, uint32_t opcode) {
    if (!sandbox->enabled) return true;
    sandbox->instructionCount++;
    if (sandbox->instructionCount > sandbox->maxInstructions) {
        vmRuntimeError(vm, "Sandbox: instruction limit exceeded (%llu)", (unsigned long long)sandbox->maxInstructions);
        return false;
    }
    if (vm->frameCount > sandbox->maxCallDepth) {
        vmRuntimeError(vm, "Sandbox: call depth limit exceeded");
        return false;
    }
    if (opcode == OP_CALL || opcode == OP_CALL_TAIL) {
        if (vm->frameCount > sandbox->maxCallDepth) return false;
    }
    if (opcode == OP_NEW_ARRAY || opcode == OP_NEW_MAP || opcode == OP_NEW_OBJECT) {
        if (vm->memory.bytesAllocated > sandbox->maxMemory) {
            vmRuntimeError(vm, "Sandbox: memory limit exceeded");
            return false;
        }
    }
    for (uint32_t i = 0; i < sandbox->opOverrideCount; i++) {
        if (sandbox->opOverrides[i].opcode == opcode)
            return sandbox->opOverrides[i].allowed;
    }
    if (sandbox->customCheck && !sandbox->customCheck(sandbox, vm, opcode))
        return false;
    return true;
}

void sandboxSetMemoryLimit(Sandbox* sandbox, uint64_t maxBytes) {
    sandbox->maxMemory = maxBytes;
}

void sandboxSetInstructionLimit(Sandbox* sandbox, uint64_t maxInstructions) {
    sandbox->maxInstructions = maxInstructions;
}

void sandboxSetTimeLimit(Sandbox* sandbox, double maxSeconds) {
    sandbox->maxExecutionTime = maxSeconds;
}

void sandboxRestrictIO(Sandbox* sandbox, bool restrict) {
    sandbox->restrictIO = restrict;
}

void sandboxRestrictNetwork(Sandbox* sandbox, bool restrict) {
    sandbox->restrictNetwork = restrict;
}

void sandboxRestrictFilesystem(Sandbox* sandbox, bool restrict) {
    sandbox->restrictFilesystem = restrict;
}

void sandboxRestrictProcess(Sandbox* sandbox, bool restrict) {
    sandbox->restrictProcess = restrict;
}

void sandboxAddOpOverride(Sandbox* sandbox, uint32_t opcode, bool allowed) {
    sandbox->opOverrides = realloc(sandbox->opOverrides,
        (sandbox->opOverrideCount + 1) * sizeof(OpRule));
    sandbox->opOverrides[sandbox->opOverrideCount].opcode = opcode;
    sandbox->opOverrides[sandbox->opOverrideCount].allowed = allowed;
    sandbox->opOverrideCount++;
}
