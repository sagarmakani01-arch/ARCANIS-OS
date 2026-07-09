#include <arcanis/timer.h>
#include <arcanis/io.h>
#include <arcanis/defs.h>
#include <arcanis/types.h>

static volatile uint32_t timer_ticks = 0;
static timer_callback_t timer_callback = NULL;

void timer_interrupt_handler(registers_t* regs) {
    (void)regs;
    timer_ticks++;
    if (timer_callback) {
        timer_callback();
    }
}

void timer_initialize(uint32_t freq) {
    timer_ticks = 0;

    uint32_t divisor = PIT_FREQ / freq;
    outb(0x43, 0x36);
    outb(0x40, (uint8_t)(divisor & 0xFF));
    outb(0x40, (uint8_t)((divisor >> 8) & 0xFF));

    extern void irq_register_handler(int irq, void (*handler)(registers_t*));
    irq_register_handler(0, timer_interrupt_handler);
}

void timer_register_callback(timer_callback_t cb) {
    timer_callback = cb;
}

uint32_t timer_get_ticks(void) {
    return timer_ticks;
}

uint32_t timer_get_seconds(void) {
    return timer_ticks / TIMER_HZ;
}

void timer_sleep(uint32_t ms) {
    uint32_t target = timer_ticks + (ms * TIMER_HZ / 1000);
    while (timer_ticks < target) {
        asm volatile("hlt");
    }
}
