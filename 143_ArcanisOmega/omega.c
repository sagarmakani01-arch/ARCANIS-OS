#include "omega.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
    int adapter_id;
    char target_system[32];
    float compatibility_gain;
} UniversalAdapter;

typedef struct {
    int scale_id;
    char dimension[32];
    float capacity;
} InfiniteScale;

typedef struct {
    int purpose_id;
    char description[64];
    float clarity;
} EvolvedPurpose;

typedef struct {
    UniversalAdapter adapters[16];
    int adapter_count;
    InfiniteScale scales[16];
    int scale_count;
    EvolvedPurpose purposes[16];
    int purpose_count;
    float universal_compatibility;
    int eternal_evolution;
    float reality_flexibility;
    int protocols_active;
} OmegaOS;

static OmegaOS os;

void omega_init(void) {
    os.adapter_count = 0;
    os.scale_count = 0;
    os.purpose_count = 0;
    os.universal_compatibility = 0.5f;
    os.eternal_evolution = 1;
    os.reality_flexibility = 0.0f;
    os.protocols_active = 3;
    srand((unsigned)time(NULL));
    printf("OmegaOS initialized: compatibility=%.2f, evolution=%d\n",
           os.universal_compatibility, os.eternal_evolution);
}

void omega_adapt_to(const char *system) {
    if (os.adapter_count >= 16) return;
    UniversalAdapter *a = &os.adapters[os.adapter_count++];
    a->adapter_id = os.adapter_count;
    snprintf(a->target_system, sizeof(a->target_system), "%s", system);
    a->compatibility_gain = 0.05f + ((float)rand() / RAND_MAX) * 0.15f;
    os.universal_compatibility += a->compatibility_gain;
    if (os.universal_compatibility > 1.0f) os.universal_compatibility = 1.0f;
    printf("Adapter #%d: %s (+%.2f, total=%.2f)\n",
           a->adapter_id, system, a->compatibility_gain, os.universal_compatibility);
}

void omega_scale(const char *dimension) {
    if (os.scale_count >= 16) return;
    InfiniteScale *s = &os.scales[os.scale_count++];
    s->scale_id = os.scale_count;
    snprintf(s->dimension, sizeof(s->dimension), "%s", dimension);
    s->capacity = os.universal_compatibility * 1000.0f;
    printf("Scale #%d: %s (capacity=%.0f)\n", s->scale_id, dimension, s->capacity);
}

void omega_evolve_purpose(const char *desc) {
    if (os.purpose_count >= 16) return;
    EvolvedPurpose *p = &os.purposes[os.purpose_count++];
    p->purpose_id = os.purpose_count;
    snprintf(p->description, sizeof(p->description), "%s", desc);
    p->clarity = ((float)rand() / RAND_MAX);
    printf("Purpose #%d: %s (clarity=%.2f)\n", p->purpose_id, desc, p->clarity);
}

void omega_transcend_limitation(void) {
    os.reality_flexibility += 0.15f;
    if (os.reality_flexibility > 1.0f) os.reality_flexibility = 1.0f;
    printf("Reality flexibility increased to %.2f\n", os.reality_flexibility);
}

void omega_show_adapters(void) {
    printf("\n%-4s %-24s %s\n", "ID", "Target System", "Gain");
    printf("----------------------------------------\n");
    for (int i = 0; i < os.adapter_count; i++) {
        printf("%-4d %-24s %.2f\n",
               os.adapters[i].adapter_id,
               os.adapters[i].target_system,
               os.adapters[i].compatibility_gain);
    }
}

void omega_show_scaling(void) {
    printf("\n%-4s %-24s %s\n", "ID", "Dimension", "Capacity");
    printf("----------------------------------------\n");
    for (int i = 0; i < os.scale_count; i++) {
        printf("%-4d %-24s %.0f\n",
               os.scales[i].scale_id,
               os.scales[i].dimension,
               os.scales[i].capacity);
    }
}

void omega_show_purposes(void) {
    printf("\n%-4s %-40s %s\n", "ID", "Purpose", "Clarity");
    printf("----------------------------------------------------------\n");
    for (int i = 0; i < os.purpose_count; i++) {
        printf("%-4d %-40s %.2f\n",
               os.purposes[i].purpose_id,
               os.purposes[i].description,
               os.purposes[i].clarity);
    }
}

void omega_show_omega_status(void) {
    printf("\n=== OmegaOS Status ===\n");
    printf("%-25s %.2f\n", "Universal Compatibility", os.universal_compatibility);
    printf("%-25s %d\n", "Eternal Evolution", os.eternal_evolution);
    printf("%-25s %.2f\n", "Reality Flexibility", os.reality_flexibility);
    printf("%-25s %d\n", "Active Protocols", os.protocols_active);
    printf("%-25s %d\n", "Adapters", os.adapter_count);
    printf("%-25s %d\n", "Scales", os.scale_count);
    printf("%-25s %d\n", "Purposes Evolved", os.purpose_count);
}
