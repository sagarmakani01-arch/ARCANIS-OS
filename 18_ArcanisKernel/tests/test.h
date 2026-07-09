/*
 * ArcanisKernel Test Framework
 * Runs tests inside the kernel shell environment
 */

#ifndef ARCANIS_TEST_H
#define ARCANIS_TEST_H

#include <arcanis/types.h>

#define TEST_PASS  0
#define TEST_FAIL  1

typedef int (*test_func_t)(void);

typedef struct {
    const char* name;
    test_func_t func;
} test_case_t;

int test_run_all(void);
int test_string_ops(void);
int test_memory_ops(void);
int test_list_ops(void);

#endif
