#include <arcanis/idt.h>
#include <arcanis/vga.h>
#include <arcanis/serial.h>
#include <arcanis/string.h>

static const char* exception_messages[] = {
    "Division By Zero", "Debug", "NMI", "Breakpoint",
    "Overflow", "Bound Range Exceeded", "Invalid Opcode", "Device Not Available",
    "Double Fault", "Coprocessor Segment Overrun", "Invalid TSS", "Segment Not Present",
    "Stack-Segment Fault", "General Protection Fault", "Page Fault", "Reserved",
    "x87 FPU Error", "Alignment Check", "Machine Check", "SIMD Exception",
    "Virtualization Exception", "Control Protection", "Reserved", "Reserved",
    "Reserved", "Reserved", "Reserved", "Reserved",
    "Hypervisor Injection", "VMM Communication", "Security Exception", "Reserved"
};

void isr_handler(registers_t* regs) {
    if (regs->int_no < 32) {
        vga_set_color(VGA_WHITE, VGA_RED);
        vga_puts("\n!!! EXCEPTION !!!\n");
        vga_puts("Exception: ");
        vga_puts(exception_messages[regs->int_no]);
        vga_puts("\nError Code: ");
        vga_put_hex(regs->err_code);
        vga_puts("\nEIP: ");
        vga_put_hex(regs->eip);
        vga_puts("\nCS:  ");
        vga_put_hex(regs->cs);
        vga_puts("\nEFLAGS: ");
        vga_put_hex(regs->eflags);
        vga_puts("\n");
        vga_set_color(VGA_LIGHT_GREY, VGA_BLACK);

        serial_puts("[PANIC] Exception: ");
        serial_puts(exception_messages[regs->int_no]);
        serial_puts("\n");

        asm volatile("cli; hlt");
    }
}
