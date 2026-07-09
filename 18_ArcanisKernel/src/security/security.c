#include <arcanis/security.h>
#include <arcanis/types.h>
#include <arcanis/string.h>
#include <arcanis/io.h>

static security_context_t security_ctx;

static uint32_t lcg_state = 12345;

void security_initialize(void) {
    security_ctx.enabled = true;
    security_ctx.aslr_entropy = 16;
    security_ctx.num_ranges = 0;

    uint32_t seed;
    asm volatile("rdtsc" : "=a"(seed));
    lcg_state = seed;

    security_protect_range(0x00000000, 0x00100000, 0x01);
    security_protect_range(0xB8000000, 0x00100000, 0x02);
}

uint32_t security_get_random(void) {
    lcg_state = lcg_state * 1103515245 + 12345;
    return (lcg_state >> 16) & 0x7FFF;
}

uint32_t security_aslr_randomize(uint32_t base, uint32_t range) {
    if (!security_ctx.enabled) return base;

    uint32_t offset = security_get_random() % range;
    offset = offset & ~(PAGE_SIZE - 1);
    return base + offset;
}

bool security_check_access(uint32_t addr, uint32_t size, uint32_t ring) {
    if (ring > 3) return false;

    for (uint32_t i = 0; i < security_ctx.num_ranges; i++) {
        security_range_t* range = &security_ctx.protected_ranges[i];
        if (addr >= range->base && addr + size <= range->base + range->length) {
            if (ring != 0) return false;
        }
    }

    return true;
}

void security_protect_range(uint32_t base, uint32_t length, uint32_t flags) {
    if (security_ctx.num_ranges < SEC_MAX_RANGES) {
        security_range_t* range = &security_ctx.protected_ranges[security_ctx.num_ranges++];
        range->base = base;
        range->length = length;
        range->flags = flags;
    }
}
