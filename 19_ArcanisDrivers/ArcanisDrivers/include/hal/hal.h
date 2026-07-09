#ifndef ARCANIS_HAL_H
#define ARCANIS_HAL_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#include "drivers/driver.h"

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint64_t memory_base;
    size_t memory_size;
    uint32_t cpu_count;
    uint32_t timer_freq;
} HALInfo;

typedef struct {
    DriverStatus (*port_read)(uint16_t port, uint8_t* value);
    DriverStatus (*port_write)(uint16_t port, uint8_t value);
    DriverStatus (*port_readw)(uint16_t port, uint16_t* value);
    DriverStatus (*port_writew)(uint16_t port, uint16_t value);
    DriverStatus (*port_readl)(uint16_t port, uint32_t* value);
    DriverStatus (*port_writel)(uint16_t port, uint32_t value);
} HALIOOps;

typedef struct {
    DriverStatus (*map)(uint64_t phys_addr, size_t size, void** virt_addr);
    DriverStatus (*unmap)(void* virt_addr, size_t size);
    DriverStatus (*read_phys)(uint64_t phys_addr, void* buf, size_t len);
    DriverStatus (*write_phys)(uint64_t phys_addr, const void* buf, size_t len);
} HALMemoryOps;

typedef struct {
    DriverStatus (*enable_irq)(uint32_t irq);
    DriverStatus (*disable_irq)(uint32_t irq);
    DriverStatus (*register_handler)(uint32_t irq, void (*handler)(void*), void* data);
    DriverStatus (*unregister_handler)(uint32_t irq);
    DriverStatus (*send_eoi)(uint32_t irq);
} HALIRQOps;

typedef struct {
    DriverStatus (*get_time)(uint64_t* ticks);
    DriverStatus (*sleep)(uint32_t ms);
    uint32_t (*get_freq)(void);
} HALTimerOps;

typedef struct {
    HALInfo info;
    HALIOOps io;
    HALMemoryOps memory;
    HALIRQOps irq;
    HALTimerOps timer;
    bool initialized;
} HALContext;

DriverStatus hal_init(HALContext* ctx);
DriverStatus hal_shutdown(HALContext* ctx);
DriverStatus hal_get_info(HALContext* ctx, HALInfo* info);

DriverStatus hal_io_read(HALContext* ctx, uint16_t port, uint8_t* value);
DriverStatus hal_io_write(HALContext* ctx, uint16_t port, uint8_t value);
DriverStatus hal_io_readw(HALContext* ctx, uint16_t port, uint16_t* value);
DriverStatus hal_io_writew(HALContext* ctx, uint16_t port, uint16_t value);
DriverStatus hal_io_readl(HALContext* ctx, uint16_t port, uint32_t* value);
DriverStatus hal_io_writel(HALContext* ctx, uint16_t port, uint32_t value);

DriverStatus hal_memory_map(HALContext* ctx, uint64_t phys_addr, size_t size, void** virt_addr);
DriverStatus hal_memory_unmap(HALContext* ctx, void* virt_addr, size_t size);

DriverStatus hal_irq_enable(HALContext* ctx, uint32_t irq);
DriverStatus hal_irq_disable(HALContext* ctx, uint32_t irq);
DriverStatus hal_irq_register(HALContext* ctx, uint32_t irq, void (*handler)(void*), void* data);

DriverStatus hal_timer_sleep(HALContext* ctx, uint32_t ms);
uint32_t hal_timer_get_freq(HALContext* ctx);

#endif