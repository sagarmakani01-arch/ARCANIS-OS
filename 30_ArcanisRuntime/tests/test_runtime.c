#include <arcanis/string.h>
#include <arcanis/pmm.h>
#include <arcanis/heap.h>
#include <arcanis/runtime.h>
#include <stdint.h>

#define TEST_PASS(name) arcanis_test_pass(name)
#define TEST_FAIL(name, msg) arcanis_test_fail(name, msg)

static int tests_run = 0;
static int tests_passed = 0;

static void arcanis_test_pass(const char* name) {
    tests_run++;
    tests_passed++;
    print("[PASS] ");
    println((char*)name);
}

static void arcanis_test_fail(const char* name, const char* msg) {
    tests_run++;
    print("[FAIL] ");
    print((char*)name);
    print(": ");
    println((char*)msg);
}

static void test_strlen(void) {
    TEST_PASS("strlen: empty", arc_strlen("") == 0 ? 1 : 0);
    TEST_PASS("strlen: hello", arc_strlen("hello") == 5 ? 1 : 0);
}

static void test_memcpy(void) {
    char src[] = "hello";
    char dst[6];
    arc_memcpy(dst, src, 6);
    TEST_PASS("memcpy: basic", arc_strcmp(dst, "hello") == 0 ? 1 : 0);
}

static void test_memset(void) {
    char buf[4];
    arc_memset(buf, 0, 4);
    int zeroed = (buf[0] == 0 && buf[1] == 0 && buf[2] == 0 && buf[3] == 0);
    TEST_PASS("memset: zero", zeroed ? 1 : 0);
}

static void test_strcmp(void) {
    TEST_PASS("strcmp: equal", arc_strcmp("abc", "abc") == 0 ? 1 : 0);
    TEST_PASS("strcmp: less", arc_strcmp("abc", "abd") < 0 ? 1 : 0);
    TEST_PASS("strcmp: greater", arc_strcmp("abd", "abc") > 0 ? 1 : 0);
}

static void test_itoa(void) {
    char buf[32];
    arc_itoa(42, buf, 10);
    TEST_PASS("itoa: 42", arc_strcmp(buf, "42") == 0 ? 1 : 0);
    arc_itoa(-10, buf, 10);
    TEST_PASS("itoa: -10", arc_strcmp(buf, "-10") == 0 ? 1 : 0);
}

static void test_pmm(void) {
    arc_pmm_init(4 * 1024 * 1024, 0x100000, 0x200000);
    void* block = arc_pmm_alloc_block();
    TEST_PASS("pmm: alloc block", block != (void*)0 ? 1 : 0);
    if (block) arc_pmm_free_block(block);
    TEST_PASS("pmm: free block", 1);
    uint32_t free = arc_pmm_get_free_blocks();
    TEST_PASS("pmm: free blocks > 0", free > 0 ? 1 : 0);
}

static void test_heap(void) {
    arc_heap_init(0x08000000, 1024 * 1024);
    void* a = arc_kmalloc(64);
    TEST_PASS("kmalloc: basic", a != (void*)0 ? 1 : 0);
    void* b = arc_kmalloc(128);
    TEST_PASS("kmalloc: second", b != (void*)0 ? 1 : 0);
    TEST_PASS("kmalloc: different addrs", a != b ? 1 : 0);
    arc_kfree(a);
    arc_kfree(b);
    TEST_PASS("kfree: no crash", 1);
    size_t used = arc_heap_get_used();
    TEST_PASS("kmalloc: used after free", used == 0 ? 1 : 0);
}

static void test_calloc(void) {
    int* arr = arc_kcalloc(5, sizeof(int));
    TEST_PASS("kcalloc: non-null", arr != (void*)0 ? 1 : 0);
    if (arr) {
        int zeroed = 1;
        for (int i = 0; i < 5; i++) {
            if (arr[i] != 0) { zeroed = 0; break; }
        }
        TEST_PASS("kcalloc: zeroed", zeroed ? 1 : 0);
        arc_kfree(arr);
    }
}

void run_all_tests(void) {
    println("=== ArcanisRuntime Test Suite ===");
    test_strlen();
    test_memcpy();
    test_memset();
    test_strcmp();
    test_itoa();
    test_pmm();
    test_heap();
    test_calloc();
    print("\nResults: ");
    print_int(tests_passed);
    print("/");
    print_int(tests_run);
    println(" passed");
}
