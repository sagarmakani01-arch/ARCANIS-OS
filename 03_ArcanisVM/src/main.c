#include "vm.h"
#include "bytecode.h"
#include "compiler.h"
#include "debugger.h"
#include "profiler.h"
#include "sandbox.h"
#include "plugin.h"
#include "runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>

static VM vm;
static Debugger dbg;
static Profiler prof;

static void printUsage(void) {
    printf("Usage: arcanisvm [options] <file.arc>\n");
    printf("Options:\n");
    printf("  --help         Show this help\n");
    printf("  --version      Show version\n");
    printf("  --debug        Enable debugger\n");
    printf("  --profile      Enable profiler\n");
    printf("  --sandbox      Enable sandbox\n");
    printf("  --disassemble  Disassemble bytecode\n");
    printf("  --eval <code>  Evaluate code from command line\n");
    printf("  --plugin <so>  Load a plugin\n");
}

static void printVersion(void) {
    printf("ArcanisVM v1.0.0\n");
    printf("Arcanis Runtime Environment\n");
}

#ifdef _WIN32
static void platformInit(void) {
    SetConsoleOutputCP(CP_UTF8);
}
#else
static void platformInit(void) {}
#endif

static void handleSignal(int sig) {
    (void)sig;
    printf("\nExecution interrupted\n");
    exit(1);
}

int main(int argc, char* argv[]) {
    platformInit();
    signal(SIGINT, handleSignal);

    bool enableDebug = false;
    bool enableProfile = false;
    bool enableSandbox = false;
    bool disassemble = false;
    const char* evalCode = NULL;
    const char* inputFile = NULL;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--help") == 0) { printUsage(); return 0; }
        else if (strcmp(argv[i], "--version") == 0) { printVersion(); return 0; }
        else if (strcmp(argv[i], "--debug") == 0) enableDebug = true;
        else if (strcmp(argv[i], "--profile") == 0) enableProfile = true;
        else if (strcmp(argv[i], "--sandbox") == 0) enableSandbox = true;
        else if (strcmp(argv[i], "--disassemble") == 0) disassemble = true;
        else if (strcmp(argv[i], "--eval") == 0 && i + 1 < argc) evalCode = argv[++i];
        else if (strcmp(argv[i], "--plugin") == 0 && i + 1 < argc) {
            i++;
        }
        else inputFile = argv[i];
    }

    if (!inputFile && !evalCode) {
        printUsage();
        return 1;
    }

    initVM(&vm);

    if (enableDebug) {
        initDebugger(&dbg);
        dbg.enabled = true;
        vm.debugger = &dbg;
    }

    if (enableProfile) {
        initProfiler(&prof);
        prof.enabled = true;
        vm.profiler = &prof;
    }

    if (enableSandbox) {
        vm.sandbox = malloc(sizeof(Sandbox));
        initSandbox(vm.sandbox);
        sandboxEnable(vm.sandbox);
    }

    ObjFunction* fn = NULL;

    if (evalCode) {
        fn = compile(&vm, evalCode, (uint32_t)strlen(evalCode));
    } else if (inputFile) {
        FILE* f = fopen(inputFile, "rb");
        if (!f) { fprintf(stderr, "Cannot open file: %s\n", inputFile); return 1; }
        fseek(f, 0, SEEK_END);
        long size = ftell(f);
        rewind(f);
        char* source = malloc(size + 1);
        fread(source, 1, size, f);
        source[size] = '\0';
        fclose(f);
        fn = compile(&vm, source, (uint32_t)size);
        free(source);
    }

    if (!fn) {
        fprintf(stderr, "Compilation failed\n");
        freeVM(&vm);
        return 1;
    }

    if (disassemble) {
        disassembleChunk((BytecodeChunk*)fn, fn->name ? fn->name->chars : "script");
    }

    if (enableProfile && vm.profiler) profilerStart(vm.profiler, &vm, 0);

    ExecResult result = vmInterpret(&vm, fn);

    if (enableProfile && vm.profiler) {
        profilerStop(vm.profiler, &vm);
        profilerPrintReport(vm.profiler);
    }

    if (result != EXEC_OK && result != EXEC_HALTED) {
        fprintf(stderr, "Execution error: %s\n", vm.errorMessage);
    }

    freeVM(&vm);
    return result == EXEC_OK ? 0 : 1;
}
