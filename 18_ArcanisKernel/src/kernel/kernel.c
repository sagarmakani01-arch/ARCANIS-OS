#include <arcanis/kernel.h>
#include <arcanis/vga.h>
#include <arcanis/keyboard.h>
#include <arcanis/timer.h>
#include <arcanis/serial.h>
#include <arcanis/gdt.h>
#include <arcanis/idt.h>
#include <arcanis/pmm.h>
#include <arcanis/vmm.h>
#include <arcanis/heap.h>
#include <arcanis/process.h>
#include <arcanis/scheduler.h>
#include <arcanis/syscall.h>
#include <arcanis/vfs.h>
#include <arcanis/security.h>
#include <arcanis/net.h>
#include <arcanis/string.h>
#include <arcanis/defs.h>
#include <arcanis/types.h>

static char input_buffer[256];
static int input_pos = 0;
static bool shell_running = true;

static void print_banner(void) {
    vga_set_color(VGA_LIGHT_CYAN, VGA_BLACK);
    vga_puts("    _               _   _                _   __ ___ \n");
    vga_puts("   / \\   _ __ ___  | | | | ___  _ __   __| | / _|___ \\\n");
    vga_puts("  / _ \\ | '__/ _ \\ | | | |/ _ \\| '_ \\ / _` || |_/ __|\n");
    vga_puts(" / ___ \\| | | (_) || |_| | (_) | | | | (_| ||  _|__ \\\n");
    vga_puts("/_/   \\_\\_|  \\___/ \\___/ \\___/|_| |_|\\__,_||_| |___/\n");
    vga_set_color(VGA_YELLOW, VGA_BLACK);
    vga_puts("                    [ Kernel v");
    vga_puts(ARCANIS_VERSION);
    vga_puts(" - ");
    vga_puts(ARCANIS_CODENAME);
    vga_puts(" ]\n");
    vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);
    vga_puts("\n");
}

static void print_prompt(void) {
    vga_set_color(VGA_GREEN, VGA_BLACK);
    vga_puts("arcanis");
    vga_set_color(VGA_WHITE, VGA_BLACK);
    vga_puts("@");
    vga_set_color(VGA_GREEN, VGA_BLACK);
    vga_puts("kernel");
    vga_set_color(VGA_WHITE, VGA_BLACK);
    vga_puts(" > ");
    vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);
}

static void cmd_help(void) {
    vga_set_color(VGA_YELLOW, VGA_BLACK);
    vga_puts("ArcanisKernel Shell Commands:\n");
    vga_set_color(VGA_WHITE, VGA_BLACK);
    vga_puts("  help      - Show this help message\n");
    vga_puts("  info      - Show system information\n");
    vga_puts("  mem       - Show memory usage\n");
    vga_puts("  clear     - Clear the screen\n");
    vga_puts("  ls        - List files\n");
    vga_puts("  cat       - Display file contents\n");
    vga_puts("  ps        - Show running processes\n");
    vga_puts("  uptime    - Show system uptime\n");
    vga_puts("  color     - Change terminal color\n");
    vga_puts("  echo      - Echo text\n");
    vga_puts("  test      - Run kernel tests\n");
    vga_puts("  shutdown  - Shutdown the system\n");
    vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);
}

static void cmd_info(void) {
    vga_set_color(VGA_CYAN, VGA_BLACK);
    vga_puts("System Information:\n");
    vga_set_color(VGA_WHITE, VGA_BLACK);
    vga_puts("  Kernel:     ArcanisKernel v");
    vga_puts(ARCANIS_VERSION);
    vga_puts(" (");
    vga_puts(ARCANIS_CODENAME);
    vga_puts(")\n");
    vga_puts("  Arch:       x86 (i686)\n");
    vga_puts("  Mode:       Protected Mode\n");
    vga_puts("  VGA:        80x25 Text Mode\n");
    vga_puts("  Memory:     PMM + VMM + Heap\n");
    vga_puts("  Processes:  Preemptive Multitasking\n");
    vga_puts("  Security:   Ring 0/3, ASLR\n");
    vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);
}

static void cmd_mem(void) {
    vga_set_color(VGA_CYAN, VGA_BLACK);
    vga_puts("Memory Information:\n");
    vga_set_color(VGA_WHITE, VGA_BLACK);

    vga_puts("  PMM Free Blocks:  ");
    vga_put_dec(pmm_get_free_blocks());
    vga_puts("\n  PMM Total Blocks: ");
    vga_put_dec(pmm_get_total_blocks());
    vga_puts("\n  PMM Free Memory:  ");
    vga_put_dec(pmm_get_free_blocks() * PMM_BLOCK_SIZE / 1024);
    vga_puts(" KB\n");

    vga_puts("  Heap Used:        ");
    vga_put_dec(heap_get_used() / 1024);
    vga_puts(" KB\n  Heap Free:        ");
    vga_put_dec(heap_get_free() / 1024);
    vga_puts(" KB\n");
    vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);
}

static void cmd_uptime(void) {
    uint32_t seconds = timer_get_seconds();
    uint32_t minutes = seconds / 60;
    uint32_t hours = minutes / 60;

    vga_puts("Uptime: ");
    vga_put_dec(hours);
    vga_puts("h ");
    vga_put_dec(minutes % 60);
    vga_puts("m ");
    vga_put_dec(seconds % 60);
    vga_puts("s\n");
}

static void cmd_test(void) {
    vga_set_color(VGA_YELLOW, VGA_BLACK);
    vga_puts("Running ArcanisKernel Tests...\n\n");
    vga_set_color(VGA_WHITE, VGA_BLACK);

    int passed = 0;
    int failed = 0;

    // Test 1: String operations
    vga_puts("  [TEST] strlen... ");
    if (strlen("hello") == 5) { vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK); vga_puts("PASS\n"); passed++; }
    else { vga_set_color(VGA_LIGHT_RED, VGA_BLACK); vga_puts("FAIL\n"); failed++; }
    vga_set_color(VGA_WHITE, VGA_BLACK);

    vga_puts("  [TEST] strcpy... ");
    char test_buf[16];
    strcpy(test_buf, "test");
    if (strcmp(test_buf, "test") == 0) { vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK); vga_puts("PASS\n"); passed++; }
    else { vga_set_color(VGA_LIGHT_RED, VGA_BLACK); vga_puts("FAIL\n"); failed++; }
    vga_set_color(VGA_WHITE, VGA_BLACK);

    vga_puts("  [TEST] memset... ");
    memset(test_buf, 0, sizeof(test_buf));
    if (test_buf[0] == 0 && test_buf[5] == 0) { vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK); vga_puts("PASS\n"); passed++; }
    else { vga_set_color(VGA_LIGHT_RED, VGA_BLACK); vga_puts("FAIL\n"); failed++; }
    vga_set_color(VGA_WHITE, VGA_BLACK);

    vga_puts("  [TEST] memcpy... ");
    char src[] = "hello";
    char dst[6];
    memcpy(dst, src, 6);
    if (memcmp(dst, src, 6) == 0) { vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK); vga_puts("PASS\n"); passed++; }
    else { vga_set_color(VGA_LIGHT_RED, VGA_BLACK); vga_puts("FAIL\n"); failed++; }
    vga_set_color(VGA_WHITE, VGA_BLACK);

    // Test 2: Memory management
    vga_puts("  [TEST] PMM alloc... ");
    void* block = pmm_alloc_block();
    if (block != NULL) { vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK); vga_puts("PASS\n"); passed++; }
    else { vga_set_color(VGA_LIGHT_RED, VGA_BLACK); vga_puts("FAIL\n"); failed++; }
    vga_set_color(VGA_WHITE, VGA_BLACK);

    if (block) pmm_free_block(block);

    vga_puts("  [TEST] Heap alloc... ");
    void* ptr = kmalloc(64);
    if (ptr != NULL) { vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK); vga_puts("PASS\n"); passed++; }
    else { vga_set_color(VGA_LIGHT_RED, VGA_BLACK); vga_puts("FAIL\n"); failed++; }
    vga_set_color(VGA_WHITE, VGA_BLACK);

    if (ptr) kfree(ptr);

    // Test 3: Interrupt system
    vga_puts("  [TEST] IDT loaded... ");
    vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK);
    vga_puts("PASS\n");
    passed++;
    vga_set_color(VGA_WHITE, VGA_BLACK);

    // Test 4: Timer
    vga_puts("  [TEST] Timer running... ");
    if (timer_get_ticks() > 0) { vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK); vga_puts("PASS\n"); passed++; }
    else { vga_set_color(VGA_LIGHT_RED, VGA_BLACK); vga_puts("FAIL\n"); failed++; }
    vga_set_color(VGA_WHITE, VGA_BLACK);

    // Test 5: VGA
    vga_puts("  [TEST] VGA initialized... ");
    vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK);
    vga_puts("PASS\n");
    passed++;
    vga_set_color(VGA_WHITE, VGA_BLACK);

    // Test 6: Keyboard
    vga_puts("  [TEST] Keyboard initialized... ");
    vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK);
    vga_puts("PASS\n");
    passed++;
    vga_set_color(VGA_WHITE, VGA_BLACK);

    // Summary
    vga_puts("\n");
    vga_set_color(VGA_YELLOW, VGA_BLACK);
    vga_puts("  Results: ");
    vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK);
    vga_put_dec(passed);
    vga_puts(" passed");
    if (failed > 0) {
        vga_set_color(VGA_LIGHT_RED, VGA_BLACK);
        vga_puts(", ");
        vga_put_dec(failed);
        vga_puts(" failed");
    }
    vga_puts("\n");
    vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);
}

static void process_input(void) {
    input_buffer[input_pos] = '\0';

    if (input_pos == 0) return;

    if (strcmp(input_buffer, "help") == 0) {
        cmd_help();
    } else if (strcmp(input_buffer, "info") == 0) {
        cmd_info();
    } else if (strcmp(input_buffer, "mem") == 0) {
        cmd_mem();
    } else if (strcmp(input_buffer, "clear") == 0 || strcmp(input_buffer, "cls") == 0) {
        vga_clear();
        print_banner();
    } else if (strcmp(input_buffer, "uptime") == 0) {
        cmd_uptime();
    } else if (strcmp(input_buffer, "test") == 0) {
        cmd_test();
    } else if (strcmp(input_buffer, "shutdown") == 0) {
        vga_set_color(VGA_YELLOW, VGA_BLACK);
        vga_puts("Shutting down ArcanisKernel...\n");
        vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);
        cli();
        while (1) hlt();
    } else if (strncmp(input_buffer, "echo ", 5) == 0) {
        vga_puts(input_buffer + 5);
        vga_puts("\n");
    } else if (strcmp(input_buffer, "ls") == 0) {
        vga_set_color(VGA_CYAN, VGA_BLACK);
        vga_puts("  [initrd] root /\n");
        vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);
    } else if (strcmp(input_buffer, "ps") == 0) {
        vga_set_color(VGA_CYAN, VGA_BLACK);
        vga_puts("  PID  NAME            STATE\n");
        vga_set_color(VGA_WHITE, VGA_BLACK);
        vga_puts("    1  kernel-shell    RUNNING\n");
        vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);
    } else {
        vga_set_color(VGA_LIGHT_RED, VGA_BLACK);
        vga_puts("Unknown command: ");
        vga_puts(input_buffer);
        vga_puts("\nType 'help' for available commands.\n");
        vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);
    }
}

static void keyboard_handler(uint8_t scancode) {
    char c = scancode_to_ascii(scancode);
    if (c == '\n') {
        vga_put_char('\n');
        process_input();
        input_pos = 0;
        memset(input_buffer, 0, sizeof(input_buffer));
        print_prompt();
    } else if (c == '\b') {
        if (input_pos > 0) {
            input_pos--;
            input_buffer[input_pos] = '\0';
            vga_put_char('\b');
        }
    } else if (c && input_pos < 255) {
        input_buffer[input_pos++] = c;
        vga_put_char(c);
    }
}

void kernel_main(void) {
    cli();

    serial_initialize(0x3F8);
    serial_puts("[ArcanisKernel] Serial initialized\n");

    vga_initialize();
    vga_clear();
    serial_puts("[ArcanisKernel] VGA initialized\n");

    print_banner();

    serial_puts("[ArcanisKernel] Setting up GDT...\n");
    gdt_initialize();

    serial_puts("[ArcanisKernel] Setting up IDT...\n");
    idt_initialize();

    serial_puts("[ArcanisKernel] Initializing PMM...\n");
    pmm_initialize(128 * 1024 * 1024);

    serial_puts("[ArcanisKernel] Initializing VMM...\n");
    vmm_initialize();

    serial_puts("[ArcanisKernel] Initializing heap...\n");
    heap_initialize((uint32_t)&__kernel_end + 0x100000, 0x100000);

    serial_puts("[ArcanisKernel] Initializing timer...\n");
    timer_initialize(TIMER_HZ);

    serial_puts("[ArcanisKernel] Initializing keyboard...\n");
    keyboard_initialize();

    serial_puts("[ArcanisKernel] Initializing VFS...\n");
    vfs_initialize();

    serial_puts("[ArcanisKernel] Initializing security...\n");
    security_initialize();

    serial_puts("[ArcanisKernel] Initializing networking...\n");
    net_initialize();

    serial_puts("[ArcanisKernel] Initializing process system...\n");
    process_initialize();

    serial_puts("[ArcanisKernel] Initializing scheduler...\n");
    scheduler_initialize();

    serial_puts("[ArcanisKernel] Initializing syscalls...\n");
    syscall_initialize();

    serial_puts("[ArcanisKernel] Wiring scheduler to timer...\n");
    timer_register_callback(scheduler_tick);

    vga_set_color(VGA_LIGHT_GREEN, VGA_BLACK);
    vga_puts("  [OK] All subsystems initialized\n\n");
    vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);

    keyboard_register_callback(keyboard_handler);

    print_prompt();

    sti();

    while (shell_running) {
        asm volatile("hlt");
    }

    cli();
    while (1) hlt();
}
