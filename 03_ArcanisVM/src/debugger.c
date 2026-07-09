#include "debugger.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

void initDebugger(Debugger* dbg) {
    memset(dbg, 0, sizeof(Debugger));
    dbg->enabled = false;
    dbg->state = DBG_RUN;
    dbg->breakpoints = NULL;
    dbg->nextBreakpointId = 1;
    dbg->currentLine = 0;
    dbg->stackDepth = 0;
    dbg->sourceFile = NULL;
    dbg->pauseOnError = false;
    dbg->pauseOnEntry = false;
    dbg->lastLine = 0;
    dbg->currentFunction = NULL;
    dbg->onBreak = NULL;
    dbg->onStep = NULL;
    dbg->onError = NULL;
}

void freeDebugger(Debugger* dbg) {
    Breakpoint* bp = dbg->breakpoints;
    while (bp) {
        Breakpoint* next = bp->next;
        free(bp);
        bp = next;
    }
    dbg->breakpoints = NULL;
    free(dbg->sourceFile);
    dbg->sourceFile = NULL;
}

uint32_t debuggerSetBreakpoint(Debugger* dbg, const char* sourceFile, uint32_t line) {
    Breakpoint* bp = calloc(1, sizeof(Breakpoint));
    bp->id = dbg->nextBreakpointId++;
    bp->line = line;
    bp->enabled = true;
    bp->hitCount = 0;
    bp->next = dbg->breakpoints;
    dbg->breakpoints = bp;
    return bp->id;
}

bool debuggerRemoveBreakpoint(Debugger* dbg, uint32_t id) {
    Breakpoint** prev = &dbg->breakpoints;
    Breakpoint* bp = dbg->breakpoints;
    while (bp) {
        if (bp->id == id) {
            *prev = bp->next;
            free(bp);
            return true;
        }
        prev = &bp->next;
        bp = bp->next;
    }
    return false;
}

void debuggerEnable(Debugger* dbg) { dbg->enabled = true; }
void debuggerDisable(Debugger* dbg) { dbg->enabled = false; }

CheckResult debuggerCheck(Debugger* dbg, VM* vm) {
    if (!dbg->enabled) return CHECK_OK;
    if (dbg->state == DBG_STEP_INTO) return CHECK_BREAK;
    if (dbg->frameCount == 0) return CHECK_OK;
    CallFrame* frame = &vm->frames[vm->frameCount - 1];
    if (!frame->closure || !frame->closure->function) return CHECK_OK;
    ObjFunction* fn = frame->closure->function;
    dbg->currentFunction = fn;
    if (fn->lines && frame->ip > 0 && (frame->ip - 1) < fn->lineCount)
        dbg->currentLine = fn->lines[frame->ip - 1];
    uint32_t currentDepth = vm->frameCount;

    if (dbg->state == DBG_STEP_OVER && currentDepth <= dbg->stackDepth) {
        dbg->state = DBG_PAUSED;
        return CHECK_BREAK;
    }
    if (dbg->state == DBG_STEP_OUT && currentDepth < dbg->stackDepth) {
        dbg->state = DBG_PAUSED;
        return CHECK_BREAK;
    }

    Breakpoint* bp = dbg->breakpoints;
    while (bp) {
        if (bp->enabled && bp->line == dbg->currentLine) {
            bp->hitCount++;
            dbg->state = DBG_PAUSED;
            return CHECK_BREAK;
        }
        bp = bp->next;
    }
    return CHECK_OK;
}

ExecResult debuggerBreak(Debugger* dbg, VM* vm) {
    if (!dbg->enabled) return EXEC_OK;
    printf("Debugger break at line %d in ", dbg->currentLine);
    if (dbg->currentFunction && dbg->currentFunction->name)
        printf("%s", dbg->currentFunction->name->chars);
    else
        printf("script");
    printf("\n");
    if (dbg->onBreak) dbg->onBreak(dbg, vm);
    if (dbg->onStep) dbg->onStep(dbg, vm);
    return EXEC_DEBUG_BREAK;
}

ExecResult debuggerCheckBreak(Debugger* dbg, VM* vm) {
    (void)vm;
    if (dbg->onBreak) dbg->onBreak(dbg, vm);
    return EXEC_DEBUG_BREAK;
}

void debuggerStepInto(Debugger* dbg) {
    dbg->state = DBG_STEP_INTO;
    dbg->stackDepth = 0;
}

void debuggerStepOver(Debugger* dbg) {
    dbg->state = DBG_STEP_OVER;
    dbg->stackDepth = 0;
}

void debuggerStepOut(Debugger* dbg) {
    dbg->state = DBG_STEP_OUT;
    dbg->stackDepth = 0;
}

void debuggerContinue(Debugger* dbg) {
    dbg->state = DBG_RUN;
}

void debuggerPrintStack(Debugger* dbg, VM* vm) {
    (void)dbg;
    printf("Call Stack:\n");
    for (uint32_t i = 0; i < vm->frameCount; i++) {
        CallFrame* frame = &vm->frames[i];
        if (frame->closure && frame->closure->function) {
            ObjFunction* fn = frame->closure->function;
            printf("  #%d: ", i);
            if (fn->name) printf("%s", fn->name->chars);
            else printf("script");
            if (fn->lines && frame->ip > 0 && (frame->ip - 1) < fn->lineCount)
                printf(" [line %d]", fn->lines[frame->ip - 1]);
            printf("\n");
        }
    }
}

void debuggerPrintLocals(Debugger* dbg, VM* vm) {
    (void)dbg;
    if (vm->frameCount == 0) return;
    CallFrame* frame = &vm->frames[vm->frameCount - 1];
    ObjFunction* fn = frame->closure->function;
    printf("Locals:\n");
    uint32_t stackIdx = 0;
    for (uint32_t i = 0; i < fn->arity; i++) {
        printf("  arg %d: ", i);
        printValue(stdout, frame->slots[i]);
        printf("\n");
        stackIdx = i + 1;
    }
    uint32_t localCount = stackCount(&vm->stack) - (uint32_t)(frame->slots - vm->stack.slots);
    for (uint32_t i = stackIdx; i < localCount && i < 16; i++) {
        printf("  local %d: ", i);
        printValue(stdout, frame->slots[i]);
        printf("\n");
    }
}

void debuggerPrintBreakpoints(Debugger* dbg) {
    printf("Breakpoints:\n");
    Breakpoint* bp = dbg->breakpoints;
    while (bp) {
        printf("  #%d: line %d %s (hit %d times)\n",
            bp->id, bp->line, bp->enabled ? "" : "(disabled)", bp->hitCount);
        bp = bp->next;
    }
}
