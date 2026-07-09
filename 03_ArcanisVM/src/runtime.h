#ifndef ARCANIS_RUNTIME_H
#define ARCANIS_RUNTIME_H

#include "vm.h"

void initRuntime(VM* vm);
Value nativePrint(int argCount, Value* args, void* context);
Value nativeInput(int argCount, Value* args, void* context);
Value nativeLen(int argCount, Value* args, void* context);
Value nativeType(int argCount, Value* args, void* context);
Value nativeToInt(int argCount, Value* args, void* context);
Value nativeToFloat(int argCount, Value* args, void* context);
Value nativeToString(int argCount, Value* args, void* context);
Value nativeArrayPush(int argCount, Value* args, void* context);
Value nativeArrayPop(int argCount, Value* args, void* context);
Value nativeArrayInsert(int argCount, Value* args, void* context);
Value nativeArrayRemove(int argCount, Value* args, void* context);
Value nativeArraySort(int argCount, Value* args, void* context);
Value nativeArraySlice(int argCount, Value* args, void* context);
Value nativeMapKeys(int argCount, Value* args, void* context);
Value nativeMapValues(int argCount, Value* args, void* context);
Value nativeMapHas(int argCount, Value* args, void* context);
Value nativeClock(int argCount, Value* args, void* context);
Value nativeExit(int argCount, Value* args, void* context);
Value nativeAssert(int argCount, Value* args, void* context);
Value nativeError(int argCount, Value* args, void* context);
Value nativeGC(int argCount, Value* args, void* context);

#endif
