#ifndef ARCANIS_TIMER_H
#define ARCANIS_TIMER_H

#include <arcanis/types.h>

typedef void (*timer_callback_t)(void);

void timer_initialize(uint32_t freq);
void timer_register_callback(timer_callback_t cb);
uint32_t timer_get_ticks(void);
uint32_t timer_get_seconds(void);
void timer_sleep(uint32_t ms);

#endif
