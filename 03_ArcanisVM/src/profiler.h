#ifndef ARCANIS_PROFILER_H
#define ARCANIS_PROFILER_H

#include "vm.h"
#include <stdint.h>
#include <stdbool.h>

#define PROFILER_MAX_OPS 256

typedef struct {
    uint32_t opcode;
    uint64_t hitCount;
    double totalTime;
    double minTime;
    double maxTime;
    const char* name;
} ProfileEntry;

typedef struct {
    bool enabled;
    ProfileEntry entries[PROFILER_MAX_OPS];
    uint32_t entryCount;
    double startTime;
    double elapsedTime;
    uint64_t totalInstructions;
    uint64_t totalCalls;
    uint64_t totalGarbageCollections;
    bool profileMemory;
    bool profileIO;
    void (*onProfileResult)(struct Profiler* profiler);
} Profiler;

void initProfiler(Profiler* profiler);
void profilerStart(Profiler* profiler, VM* vm, uint32_t opcode);
void profilerStop(Profiler* profiler, VM* vm);
void profilerTick(Profiler* profiler, VM* vm, uint32_t opcode);
void profilerEnable(Profiler* profiler);
void profilerDisable(Profiler* profiler);
void profilerReset(Profiler* profiler);
void profilerPrintReport(Profiler* profiler);
void profilerPrintJson(Profiler* profiler);

#endif
