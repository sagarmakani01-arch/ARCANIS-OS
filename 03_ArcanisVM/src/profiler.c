#include "profiler.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#ifdef _WIN32
#include <windows.h>
#else
#include <sys/time.h>
#endif

static double getProfilerTime(void) {
#ifdef _WIN32
    LARGE_INTEGER freq, count;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&count);
    return (double)count.QuadPart / (double)freq.QuadPart;
#else
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (double)tv.tv_sec + (double)tv.tv_usec / 1000000.0;
#endif
}

static const char* opcodeName(uint32_t op) {
    static const char* names[] = {
        "HALT","NOP","LOAD_CONST","LOAD_NIL","LOAD_TRUE","LOAD_FALSE","LOAD_INT_0","LOAD_INT_1",
        "LOAD_LOCAL","STORE_LOCAL","LOAD_GLOBAL","STORE_GLOBAL","LOAD_UPVALUE","STORE_UPVALUE",
        "LOAD_MODULE","STORE_MODULE","ADD","SUB","MUL","DIV","MOD","NEG","EQ","NE","LT","GT","LE","GE",
        "AND","OR","NOT","JMP","JMP_IF_FALSE","JMP_IF_TRUE","JMP_IF_FALSE_POP","LOOP","CALL",
        "CALL_TAIL","RETURN","RETURN_VALUE","CLOSURE","CLOSE_UPVALUE","NEW_ARRAY","NEW_MAP",
        "INDEX_GET","INDEX_SET","NEW_OBJECT","PROP_GET","PROP_SET","METHOD","INVOKE","INHERIT",
        "GET_SUPER","SCOPE_ENTER","SCOPE_EXIT","DEFINE_GLOBAL","POP","DUP","SWAP","BUILD_STRING",
        "IMPORT","EXPORT","DEBUG_BREAK","PROFILE_START","PROFILE_END","SANDBOX_ENTER","SANDBOX_EXIT"
    };
    if (op < sizeof(names)/sizeof(names[0])) return names[op];
    return "UNKNOWN";
}

void initProfiler(Profiler* profiler) {
    memset(profiler, 0, sizeof(Profiler));
    profiler->enabled = false;
    profiler->entryCount = 0;
    profiler->startTime = 0;
    profiler->elapsedTime = 0;
    profiler->totalInstructions = 0;
    profiler->totalCalls = 0;
    profiler->totalGarbageCollections = 0;
    profiler->profileMemory = false;
    profiler->profileIO = false;
    profiler->onProfileResult = NULL;
}

void profilerStart(Profiler* profiler, VM* vm, uint32_t opcode) {
    (void)opcode;
    if (!profiler->enabled) return;
    profiler->startTime = getProfilerTime();
    profiler->totalInstructions = 0;
    profiler->totalCalls = 0;
    profiler->elapsedTime = 0;
    memset(profiler->entries, 0, sizeof(ProfileEntry) * PROFILER_MAX_OPS);
    profiler->entryCount = PROFILER_MAX_OPS;
    for (int i = 0; i < PROFILER_MAX_OPS; i++) {
        profiler->entries[i].opcode = i;
        profiler->entries[i].name = opcodeName(i);
        profiler->entries[i].minTime = 1e30;
        profiler->entries[i].maxTime = 0;
    }
    (void)vm;
}

void profilerStop(Profiler* profiler, VM* vm) {
    if (!profiler->enabled) return;
    profiler->elapsedTime = getProfilerTime() - profiler->startTime;
    (void)vm;
    if (profiler->onProfileResult) profiler->onProfileResult(profiler);
}

void profilerTick(Profiler* profiler, VM* vm, uint32_t opcode) {
    (void)vm;
    if (!profiler->enabled) return;
    if (opcode < PROFILER_MAX_OPS) {
        profiler->entries[opcode].hitCount++;
        if (opcode == OP_CALL || opcode == OP_CALL_TAIL || opcode == OP_INVOKE)
            profiler->totalCalls++;
    }
    profiler->totalInstructions++;
}

void profilerEnable(Profiler* profiler) { profiler->enabled = true; }
void profilerDisable(Profiler* profiler) { profiler->enabled = false; }

void profilerReset(Profiler* profiler) {
    initProfiler(profiler);
}

void profilerPrintReport(Profiler* profiler) {
    printf("\n=== Profiler Report ===\n");
    printf("Total time: %.6f seconds\n", profiler->elapsedTime);
    printf("Total instructions: %llu\n", (unsigned long long)profiler->totalInstructions);
    printf("Total calls: %llu\n", (unsigned long long)profiler->totalCalls);
    if (profiler->totalInstructions > 0) {
        printf("Throughput: %.0f instructions/sec\n",
            (double)profiler->totalInstructions / profiler->elapsedTime);
    }
    printf("\nOpcode Statistics:\n");
    printf("%-20s %12s %10s\n", "Opcode", "Count", "Percentage");
    printf("%-20s %12s %10s\n", "--------------------", "------------", "----------");
    for (int i = 0; i < PROFILER_MAX_OPS; i++) {
        if (profiler->entries[i].hitCount > 0) {
            double pct = (double)profiler->entries[i].hitCount * 100.0 / profiler->totalInstructions;
            printf("%-20s %12llu %9.2f%%\n", profiler->entries[i].name,
                (unsigned long long)profiler->entries[i].hitCount, pct);
        }
    }
    printf("\n");
}

void profilerPrintJson(Profiler* profiler) {
    printf("{\n");
    printf("  \"elapsed\": %.6f,\n", profiler->elapsedTime);
    printf("  \"totalInstructions\": %llu,\n", (unsigned long long)profiler->totalInstructions);
    printf("  \"totalCalls\": %llu,\n", (unsigned long long)profiler->totalCalls);
    printf("  \"opcodes\": [\n");
    bool first = true;
    for (int i = 0; i < PROFILER_MAX_OPS; i++) {
        if (profiler->entries[i].hitCount > 0) {
            if (!first) printf(",\n");
            first = false;
            printf("    { \"op\": \"%s\", \"count\": %llu, \"pct\": %.4f }",
                profiler->entries[i].name,
                (unsigned long long)profiler->entries[i].hitCount,
                (double)profiler->entries[i].hitCount * 100.0 / profiler->totalInstructions);
        }
    }
    printf("\n  ]\n}\n");
}
