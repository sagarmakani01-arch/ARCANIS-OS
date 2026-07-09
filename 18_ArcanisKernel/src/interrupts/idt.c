#include <arcanis/idt.h>
#include <arcanis/io.h>
#include <arcanis/string.h>
#include <arcanis/defs.h>
#include <arcanis/vga.h>

static struct idt_entry idt[ARCANIS_MAX_IDT];
static struct idt_ptr   idt_ptr;
static isr_handler_t    isr_handlers[ARCANIS_MAX_IDT];

extern void idt_flush(uint32_t);
extern void isr0(void);
extern void isr1(void);
extern void isr2(void);
extern void isr3(void);
extern void isr4(void);
extern void isr5(void);
extern void isr6(void);
extern void isr7(void);
extern void isr8(void);
extern void isr9(void);
extern void isr10(void);
extern void isr11(void);
extern void isr12(void);
extern void isr13(void);
extern void isr14(void);
extern void isr15(void);
extern void isr16(void);
extern void isr17(void);
extern void isr18(void);
extern void isr19(void);
extern void isr20(void);
extern void isr21(void);
extern void isr22(void);
extern void isr23(void);
extern void isr24(void);
extern void isr25(void);
extern void isr26(void);
extern void isr27(void);
extern void isr28(void);
extern void isr29(void);
extern void isr30(void);
extern void isr31(void);

extern void irq0(void);
extern void irq1(void);
extern void irq2(void);
extern void irq3(void);
extern void irq4(void);
extern void irq5(void);
extern void irq6(void);
extern void irq7(void);
extern void irq8(void);
extern void irq9(void);
extern void irq10(void);
extern void irq11(void);
extern void irq12(void);
extern void irq13(void);
extern void irq14(void);
extern void irq15(void);

extern void syscall_stub(void);

void idt_set_gate(uint8_t num, uint32_t base, uint16_t sel, uint8_t flags) {
    idt[num].base_low  = base & 0xFFFF;
    idt[num].base_high = (base >> 16) & 0xFFFF;
    idt[num].sel       = sel;
    idt[num].always0   = 0;
    idt[num].flags     = flags;
}

void idt_initialize(void) {
    idt_ptr.limit = sizeof(struct idt_entry) * ARCANIS_MAX_IDT - 1;
    idt_ptr.base  = (uint32_t)&idt;

    memset(&idt, 0, sizeof(struct idt_entry) * ARCANIS_MAX_IDT);
    memset(&isr_handlers, 0, sizeof(isr_handlers));

    remap_pic();

    uint32_t isr_bases[] = {
        (uint32_t)isr0, (uint32_t)isr1, (uint32_t)isr2, (uint32_t)isr3,
        (uint32_t)isr4, (uint32_t)isr5, (uint32_t)isr6, (uint32_t)isr7,
        (uint32_t)isr8, (uint32_t)isr9, (uint32_t)isr10, (uint32_t)isr11,
        (uint32_t)isr12, (uint32_t)isr13, (uint32_t)isr14, (uint32_t)isr15,
        (uint32_t)isr16, (uint32_t)isr17, (uint32_t)isr18, (uint32_t)isr19,
        (uint32_t)isr20, (uint32_t)isr21, (uint32_t)isr22, (uint32_t)isr23,
        (uint32_t)isr24, (uint32_t)isr25, (uint32_t)isr26, (uint32_t)isr27,
        (uint32_t)isr28, (uint32_t)isr29, (uint32_t)isr30, (uint32_t)isr31,
    };

    for (int i = 0; i < 32; i++) {
        idt_set_gate(i, isr_bases[i], GDT_KERNEL_CODE * 8,
            IDT_GATE_INT | SEG_PRESENT | SEG_DPL_KERNEL);
    }

    uint32_t irq_bases[] = {
        (uint32_t)irq0, (uint32_t)irq1, (uint32_t)irq2, (uint32_t)irq3,
        (uint32_t)irq4, (uint32_t)irq5, (uint32_t)irq6, (uint32_t)irq7,
        (uint32_t)irq8, (uint32_t)irq9, (uint32_t)irq10, (uint32_t)irq11,
        (uint32_t)irq12, (uint32_t)irq13, (uint32_t)irq14, (uint32_t)irq15,
    };

    for (int i = 0; i < 16; i++) {
        idt_set_gate(i + 32, irq_bases[i], GDT_KERNEL_CODE * 8,
            IDT_GATE_INT | SEG_PRESENT | SEG_DPL_KERNEL);
    }

    idt_set_gate(SYSCALL_INT, (uint32_t)syscall_stub, GDT_KERNEL_CODE * 8,
        IDT_GATE_INT | SEG_PRESENT | SEG_DPL_USER);

    asm volatile("lidt %0" : : "m"(idt_ptr));
    asm volatile("sti");
}

void idt_register_handler(uint8_t num, isr_handler_t handler) {
    isr_handlers[num] = handler;
}

static void remap_pic(void) {
    outb(0x20, 0x11);
    outb(0xA0, 0x11);
    io_wait();
    outb(0x21, 0x20);
    outb(0xA1, 0x28);
    io_wait();
    outb(0x21, 0x04);
    outb(0xA1, 0x02);
    io_wait();
    outb(0x21, 0x01);
    outb(0xA1, 0x01);
    io_wait();
    outb(0x21, 0x0);
    outb(0xA1, 0x0);
}
