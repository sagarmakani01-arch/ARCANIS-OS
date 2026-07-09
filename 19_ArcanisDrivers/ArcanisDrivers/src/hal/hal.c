#include "hal/hal.h"
#include <string.h>

#define HAL_MAGIC 0x41524348
#define HAL_VERSION 1

#define MAX_IRQ_HANDLERS 256

typedef struct {
    void (*handler)(void*);
    void* data;
    bool active;
} IRQHandler;

static IRQHandler g_irq_handlers[MAX_IRQ_HANDLERS];

DriverStatus hal_init(HALContext* ctx) {
    if (!ctx) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    memset(ctx, 0, sizeof(HALContext));
    memset(g_irq_handlers, 0, sizeof(g_irq_handlers));

    ctx->info.magic = HAL_MAGIC;
    ctx->info.version = HAL_VERSION;
    ctx->info.memory_base = 0x100000;
    ctx->info.memory_size = 256 * 1024 * 1024;
    ctx->info.cpu_count = 1;
    ctx->info.timer_freq = 1000;

    ctx->io.port_read = NULL;
    ctx->io.port_write = NULL;
    ctx->io.port_readw = NULL;
    ctx->io.port_writew = NULL;
    ctx->io.port_readl = NULL;
    ctx->io.port_writel = NULL;

    ctx->memory.map = NULL;
    ctx->memory.unmap = NULL;
    ctx->memory.read_phys = NULL;
    ctx->memory.write_phys = NULL;

    ctx->irq.enable_irq = NULL;
    ctx->irq.disable_irq = NULL;
    ctx->irq.register_handler = NULL;
    ctx->irq.unregister_handler = NULL;
    ctx->irq.send_eoi = NULL;

    ctx->timer.get_time = NULL;
    ctx->timer.sleep = NULL;
    ctx->timer.get_freq = NULL;

    ctx->initialized = true;

    return DRIVER_STATUS_OK;
}

DriverStatus hal_shutdown(HALContext* ctx) {
    if (!ctx || !ctx->initialized) {
        return DRIVER_STATUS_NOT_READY;
    }

    for (uint32_t i = 0; i < MAX_IRQ_HANDLERS; i++) {
        g_irq_handlers[i].active = false;
        g_irq_handlers[i].handler = NULL;
        g_irq_handlers[i].data = NULL;
    }

    ctx->initialized = false;
    return DRIVER_STATUS_OK;
}

DriverStatus hal_get_info(HALContext* ctx, HALInfo* info) {
    if (!ctx || !info || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    *info = ctx->info;
    return DRIVER_STATUS_OK;
}

DriverStatus hal_io_read(HALContext* ctx, uint16_t port, uint8_t* value) {
    if (!ctx || !value || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->io.port_read) {
        return ctx->io.port_read(port, value);
    }

    *value = 0;
    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus hal_io_write(HALContext* ctx, uint16_t port, uint8_t value) {
    if (!ctx || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->io.port_write) {
        return ctx->io.port_write(port, value);
    }

    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus hal_io_readw(HALContext* ctx, uint16_t port, uint16_t* value) {
    if (!ctx || !value || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->io.port_readw) {
        return ctx->io.port_readw(port, value);
    }

    *value = 0;
    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus hal_io_writew(HALContext* ctx, uint16_t port, uint16_t value) {
    if (!ctx || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->io.port_writew) {
        return ctx->io.port_writew(port, value);
    }

    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus hal_io_readl(HALContext* ctx, uint16_t port, uint32_t* value) {
    if (!ctx || !value || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->io.port_readl) {
        return ctx->io.port_readl(port, value);
    }

    *value = 0;
    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus hal_io_writel(HALContext* ctx, uint16_t port, uint32_t value) {
    if (!ctx || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->io.port_writel) {
        return ctx->io.port_writel(port, value);
    }

    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus hal_memory_map(HALContext* ctx, uint64_t phys_addr, size_t size, void** virt_addr) {
    if (!ctx || !virt_addr || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->memory.map) {
        return ctx->memory.map(phys_addr, size, virt_addr);
    }

    *virt_addr = (void*)(uintptr_t)phys_addr;
    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus hal_memory_unmap(HALContext* ctx, void* virt_addr, size_t size) {
    if (!ctx || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->memory.unmap) {
        return ctx->memory.unmap(virt_addr, size);
    }

    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus hal_irq_enable(HALContext* ctx, uint32_t irq) {
    if (!ctx || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (irq >= MAX_IRQ_HANDLERS) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->irq.enable_irq) {
        return ctx->irq.enable_irq(irq);
    }

    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus hal_irq_disable(HALContext* ctx, uint32_t irq) {
    if (!ctx || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (irq >= MAX_IRQ_HANDLERS) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->irq.disable_irq) {
        return ctx->irq.disable_irq(irq);
    }

    return DRIVER_STATUS_NOT_SUPPORTED;
}

DriverStatus hal_irq_register(HALContext* ctx, uint32_t irq, void (*handler)(void*), void* data) {
    if (!ctx || !handler || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (irq >= MAX_IRQ_HANDLERS) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (g_irq_handlers[irq].active) {
        return DRIVER_STATUS_BUSY;
    }

    g_irq_handlers[irq].handler = handler;
    g_irq_handlers[irq].data = data;
    g_irq_handlers[irq].active = true;

    if (ctx->irq.register_handler) {
        return ctx->irq.register_handler(irq, handler, data);
    }

    return DRIVER_STATUS_OK;
}

DriverStatus hal_timer_sleep(HALContext* ctx, uint32_t ms) {
    if (!ctx || !ctx->initialized) {
        return DRIVER_STATUS_INVALID_PARAM;
    }

    if (ctx->timer.sleep) {
        return ctx->timer.sleep(ms);
    }

    return DRIVER_STATUS_NOT_SUPPORTED;
}

uint32_t hal_timer_get_freq(HALContext* ctx) {
    if (!ctx || !ctx->initialized) {
        return 0;
    }

    if (ctx->timer.get_freq) {
        return ctx->timer.get_freq();
    }

    return ctx->info.timer_freq;
}
