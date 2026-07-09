/*
 * ArcanisKernel Test Suite
 * Comprehensive tests for kernel subsystems
 */

#include <arcanis/test.h>
#include <arcanis/string.h>
#include <arcanis/pmm.h>
#include <arcanis/heap.h>
#include <arcanis/types.h>
#include <arcanis/vga.h>

static int test_counter = 0;
static int pass_counter = 0;
static int fail_counter = 0;

static void test_assert(bool condition, const char* test_name) {
    test_counter++;
    if (condition) {
        pass_counter++;
        vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK);
        vga_puts("  [PASS] ");
    } else {
        fail_counter++;
        vga_set_color(VGA_LIGHT_RED, VGA_BLACK);
        vga_puts("  [FAIL] ");
    }
    vga_puts(test_name);
    vga_puts("\n");
    vga_set_color(VGA_WHITE, VGA_BLACK);
}

int test_string_ops(void) {
    vga_puts("\n--- String Operations Tests ---\n");

    test_assert(strlen("hello") == 5, "strlen basic");
    test_assert(strlen("") == 0, "strlen empty");

    char buf[16];
    strcpy(buf, "test");
    test_assert(strcmp(buf, "test") == 0, "strcpy/strcmp");

    memset(buf, 'A', 5);
    buf[5] = '\0';
    test_assert(buf[0] == 'A' && buf[4] == 'A', "memset");

    char src[] = "hello";
    char dst[6];
    memcpy(dst, src, 6);
    test_assert(memcmp(dst, src, 6) == 0, "memcpy/memcmp");

    char num[12];
    itoa(12345, num, 10);
    test_assert(strcmp(num, "12345") == 0, "itoa decimal");

    itoa(0xFF, num, 16);
    test_assert(strcmp(num, "ff") == 0, "itoa hex");

    return TEST_PASS;
}

int test_memory_ops(void) {
    vga_puts("\n--- Memory Operations Tests ---\n");

    void* block1 = pmm_alloc_block();
    test_assert(block1 != NULL, "PMM alloc block");

    void* block2 = pmm_alloc_block();
    test_assert(block2 != NULL, "PMM alloc second block");
    test_assert(block1 != block2, "PMM blocks differ");

    if (block1) pmm_free_block(block1);
    if (block2) pmm_free_block(block2);

    void* ptr1 = kmalloc(32);
    test_assert(ptr1 != NULL, "Heap alloc 32 bytes");

    void* ptr2 = kmalloc(64);
    test_assert(ptr2 != NULL, "Heap alloc 64 bytes");
    test_assert(ptr1 != ptr2, "Heap allocs differ");

    if (ptr1) kfree(ptr1);
    if (ptr2) kfree(ptr2);

    return TEST_PASS;
}

int test_run_all(void) {
    test_counter = 0;
    pass_counter = 0;
    fail_counter = 0;

    vga_set_color(VGA_YELLOW, VGA_BLACK);
    vga_puts("\n========================================\n");
    vga_puts("    ArcanisKernel Test Suite\n");
    vga_puts("========================================\n");
    vga_set_color(VGA_WHITE, VGA_BLACK);

    test_string_ops();
    test_memory_ops();

    vga_set_color(VGA_YELLOW, VGA_BLACK);
    vga_puts("\n========================================\n");
    vga_puts("    Results\n");
    vga_puts("========================================\n");

    vga_set_color(VGA_WHITE, VGA_BLACK);
    vga_puts("  Total:   ");
    vga_put_dec(test_counter);
    vga_puts("\n");

    vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK);
    vga_puts("  Passed:  ");
    vga_put_dec(pass_counter);
    vga_puts("\n");

    if (fail_counter > 0) {
        vga_set_color(VGA_LIGHT_RED, VGA_BLACK);
        vga_puts("  Failed:  ");
        vga_put_dec(fail_counter);
        vga_puts("\n");
    }

    vga_set_color(VGA_YELLOW, VGA_BLACK);
    vga_puts("========================================\n");
    vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);

    return fail_counter == 0 ? TEST_PASS : TEST_FAIL;
}
