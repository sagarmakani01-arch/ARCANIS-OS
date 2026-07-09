#include <arcanis/syscall.h>
#include <arcanis/idt.h>
#include <arcanis/process.h>
#include <arcanis/vga.h>
#include <arcanis/keyboard.h>
#include <arcanis/timer.h>
#include <arcanis/string.h>
#include <arcanis/types.h>
#include <arcanis/defs.h>
#include <arcanis/vfs.h>

static syscall_handler_t syscall_handlers[SYSCALL_COUNT] = { NULL };

extern void syscall_stub(void);

static int32_t sys_exit(registers_t* regs) {
    process_t* proc = process_get_current();
    if (proc) {
        process_destroy(proc);
        scheduler_schedule();
    }
    return 0;
}

static int32_t sys_getpid(registers_t* regs) {
    process_t* proc = process_get_current();
    return proc ? proc->pid : -1;
}

static int32_t sys_putchar(registers_t* regs) {
    char c = (char)regs->ebx;
    vga_put_char(c);
    return 0;
}

static int32_t sys_getchar(registers_t* regs) {
    while (!keyboard_has_data()) {
        asm volatile("hlt");
    }
    uint8_t sc = keyboard_get_scancode();
    return (int32_t)scancode_to_ascii(sc);
}

static int32_t sys_cls(registers_t* regs) {
    vga_clear();
    return 0;
}

static int32_t sys_sleep(registers_t* regs) {
    uint32_t ms = regs->ebx;
    timer_sleep(ms);
    return 0;
}

static int32_t sys_info(registers_t* regs) {
    return 0;
}

void syscall_initialize(void) {
    syscall_handlers[SYS_EXIT]    = sys_exit;
    syscall_handlers[SYS_GETPID]  = sys_getpid;
    syscall_handlers[SYS_PUTCHAR] = sys_putchar;
    syscall_handlers[SYS_GETCHAR] = sys_getchar;
    syscall_handlers[SYS_CLS]     = sys_cls;
    syscall_handlers[SYS_SLEEP]   = sys_sleep;
    syscall_handlers[SYS_INFO]    = sys_info;
}

void syscall_handler(registers_t* regs) {
    uint32_t syscall_num = regs->eax;

    if (syscall_num >= SYSCALL_COUNT || !syscall_handlers[syscall_num]) {
        regs->eax = -1;
        return;
    }

    regs->eax = syscall_handlers[syscall_num](regs);
}
