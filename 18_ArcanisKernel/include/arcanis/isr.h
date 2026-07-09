#ifndef ARCANIS_ISR_H
#define ARCANIS_ISR_H

#include <arcanis/types.h>

void isr_install(void);
void isr_handler(registers_t* regs);

#endif
