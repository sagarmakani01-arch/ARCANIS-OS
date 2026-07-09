#ifndef ARCANIS_DEBUGGER_H
#define ARCANIS_DEBUGGER_H

#include "vm.h"
#include <stdint.h>
#include <stdbool.h>

typedef enum {
    CHECK_OK,
    CHECK_BREAK,
    CHECK_ERROR,
} CheckResult;

typedef enum {
    DBG_RUN,
    DBG_STEP_INTO,
    DBG_STEP_OVER,
    DBG_STEP_OUT,
    DBG_PAUSED,
} DebugState;

typedef struct Breakpoint {
    uint32_t id;
    ObjString* sourceFile;
    uint32_t line;
    bool enabled;
    uint32_t hitCount;
    struct Breakpoint* next;
} Breakpoint;

typedef struct Debugger {
    bool enabled;
    DebugState state;
    Breakpoint* breakpoints;
    uint32_t nextBreakpointId;
    uint32_t currentLine;
    uint32_t stackDepth;
    char* sourceFile;
    bool pauseOnError;
    bool pauseOnEntry;
    uint32_t lastLine;
    ObjFunction* currentFunction;
    void (*onBreak)(struct Debugger* dbg, VM* vm);
    void (*onStep)(struct Debugger* dbg, VM* vm);
    void (*onError)(struct Debugger* dbg, VM* vm, const char* msg);
} Debugger;

void initDebugger(Debugger* dbg);
void freeDebugger(Debugger* dbg);
uint32_t debuggerSetBreakpoint(Debugger* dbg, const char* sourceFile, uint32_t line);
bool debuggerRemoveBreakpoint(Debugger* dbg, uint32_t id);
void debuggerEnable(Debugger* dbg);
void debuggerDisable(Debugger* dbg);
CheckResult debuggerCheck(Debugger* dbg, VM* vm);
ExecResult debuggerBreak(Debugger* dbg, VM* vm);
ExecResult debuggerCheckBreak(Debugger* dbg, VM* vm);
void debuggerStepInto(Debugger* dbg);
void debuggerStepOver(Debugger* dbg);
void debuggerStepOut(Debugger* dbg);
void debuggerContinue(Debugger* dbg);
void debuggerPrintStack(Debugger* dbg, VM* vm);
void debuggerPrintLocals(Debugger* dbg, VM* vm);
void debuggerPrintBreakpoints(Debugger* dbg);

#endif
