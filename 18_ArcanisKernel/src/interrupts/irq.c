#include <arcanis/irq.h>
#include <arcanis/idt.h>
#include <arcanis/io.h>
#include <arcanis/defs.h>
#include <arcanis/types.h>
#include <arcanis/vga.h>

static irq_handler_t irq_handlers[ARCANIS_MAX_IRQ] = { NULL };

void irq_acknowledge(int irq) {
    if (irq >= 8) {
        outb(0xA0, 0x20);
    }
    outb(0x20, 0x20);
}

void irq_register_handler(int irq, irq_handler_t handler) {
    if (irq < ARCANIS_MAX_IRQ) {
        irq_handlers[irq] = handler;
    }
}

void irq_unregister_handler(int irq) {
    if (irq < ARCANIS_MAX_IRQ) {
        irq_handlers[irq] = NULL;
    }
}

void irq_handler(registers_t* regs) {
    int irq = regs->int_no - 32;

    if (irq >= 0 && irq < ARCANIS_MAX_IRQ) {
        if (irq_handlers[irq]) {
            irq_handlers[irq](regs);
        }
    }

    irq_acknowledge(irq);
}
