#ifndef ARCANIS_IRQ_H
#define ARCANIS_IRQ_H

#include <arcanis/types.h>

typedef void (*irq_handler_t)(registers_t*);

void irq_install(void);
void irq_register_handler(int irq, irq_handler_t handler);
void irq_unregister_handler(int irq);
void irq_acknowledge(int irq);

#endif
