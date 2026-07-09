#ifndef ARCANIS_SECURITY_H
#define ARCANIS_SECURITY_H

#include <arcanis/types.h>

#define SEC_MAX_RANGES 64

typedef struct {
    uint32_t base;
    uint32_t length;
    uint32_t flags;
} security_range_t;

typedef struct {
    uint32_t aslr_entropy;
    security_range_t protected_ranges[SEC_MAX_RANGES];
    uint32_t num_ranges;
    bool     enabled;
} security_context_t;

void security_initialize(void);
uint32_t security_aslr_randomize(uint32_t base, uint32_t range);
bool security_check_access(uint32_t addr, uint32_t size, uint32_t ring);
void security_protect_range(uint32_t base, uint32_t length, uint32_t flags);
uint32_t security_get_random(void);

#endif
