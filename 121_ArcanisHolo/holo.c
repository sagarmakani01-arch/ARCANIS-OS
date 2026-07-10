#include "holo.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static HoloFabric hf;

void holo_init(void) {
    memset(&hf, 0, sizeof(hf));
    hf.fabric_coherence = 1.0;
    hf.entanglement_enabled = 0;
    hf.auto_optimize = 1;
    srand((unsigned)time(NULL));

    holo_create_field("primary", HOLO_CUBE, 0.1);
    holo_create_field("secondary", HOLO_SPHERE, 0.05);
    printf("[HOLO] Fabric initialized with %d fields\n", hf.field_count);
}

HoloField* holo_create_field(const char* name, HoloUnitType type, double resolution) {
    if (hf.field_count >= 16) return NULL;
    HoloField* f = &hf.fields[hf.field_count++];
    snprintf(f->id, sizeof(f->id), "FLD-%d", hf.field_count);
    snprintf(f->name, sizeof(f->name), "%s", name);
    f->type = type;
    f->pixel_count = 0;
    f->volume[0] = resolution * 100;
    f->volume[1] = resolution * 100;
    f->volume[2] = resolution * 100;
    f->resolution = resolution;
    f->coherence = 1.0;
    f->computed = 0;
    printf("[HOLO] Field '%s' created (type=%d, res=%.3f)\n", name, type, resolution);
    return f;
}

HoloPixel* holo_set_pixel(HoloField* f, double x, double y, double z, double amp) {
    if (!f || f->pixel_count >= 512) return NULL;
    for (int i = 0; i < f->pixel_count; i++) {
        if (f->pixels[i].x == x && f->pixels[i].y == y && f->pixels[i].z == z) {
            f->pixels[i].amplitude = amp;
            f->pixels[i].phase = (rand() % 628) / 100.0;
            f->pixels[i].frequency = (rand() % 1000) / 100.0;
            f->pixels[i].active = 1;
            return &f->pixels[i];
        }
    }
    HoloPixel* p = &f->pixels[f->pixel_count++];
    p->x = x;
    p->y = y;
    p->z = z;
    p->amplitude = amp;
    p->phase = (rand() % 628) / 100.0;
    p->frequency = (rand() % 1000) / 100.0;
    p->active = 1;
    hf.total_pixels++;
    printf("[HOLO] Pixel set at (%.1f,%.1f,%.1f) amp=%.2f in '%s'\n", x, y, z, amp, f->name);
    return p;
}

HoloStorage* holo_encode_data(const char* name, double* data, int size) {
    if (hf.storage_count >= 16) return NULL;
    HoloStorage* s = &hf.storage_units[hf.storage_count++];
    snprintf(s->id, sizeof(s->id), "STO-%d", hf.storage_count);
    snprintf(s->name, sizeof(s->name), "%s", name);
    int copy_size = size < 4096 ? size : 4096;
    memcpy(s->data, data, copy_size * sizeof(double));
    s->data_size = copy_size;
    memset(&s->encoding, 0, sizeof(s->encoding));
    s->encoded = 1;
    s->density = (rand() % 1000) / 1000.0;
    s->read_speed = (rand() % 1000) / 10.0;
    printf("[HOLO] Data encoded in '%s' (%d doubles, density=%.2f)\n", name, copy_size, s->density);
    return s;
}

int holo_decode_data(HoloStorage* s, double* output) {
    if (!s || !output || !s->encoded) return 0;
    memcpy(output, s->data, s->data_size * sizeof(double));
    printf("[HOLO] Data decoded from '%s' (%d doubles)\n", s->name, s->data_size);
    return s->data_size;
}

HoloCompute* holo_create_compute(const char* name, HoloField* input, const char* operation) {
    if (hf.compute_count >= 8) return NULL;
    HoloCompute* c = &hf.compute_units[hf.compute_count++];
    snprintf(c->id, sizeof(c->id), "CMP-%d", hf.compute_count);
    snprintf(c->name, sizeof(c->name), "%s", name);
    if (input) c->input_field = *input;
    memset(&c->output_field, 0, sizeof(c->output_field));
    memset(c->transform_matrix, 0, sizeof(c->transform_matrix));
    for (int i = 0; i < 16; i++) c->transform_matrix[i] = (rand() % 2000 - 1000) / 100.0;
    snprintf(c->operation, sizeof(c->operation), "%s", operation);
    c->completed = 0;
    printf("[HOLO] Compute '%s' created (op=%s)\n", name, operation);
    return c;
}

int holo_execute_compute(HoloCompute* c) {
    if (!c) return 0;
    c->output_field = c->input_field;
    for (int i = 0; i < c->output_field.pixel_count && i < 512; i++) {
        c->output_field.pixels[i].amplitude *= c->transform_matrix[i % 16];
        c->output_field.pixels[i].phase += 0.1;
    }
    c->completed = 1;
    c->output_field.computed = 1;
    printf("[HOLO] Compute '%s' executed (%d pixels transformed)\n", c->name, c->output_field.pixel_count);
    return 1;
}

void holo_entangle(HoloField* a, HoloField* b) {
    hf.entanglement_enabled = 1;
    printf("[HOLO] Fields '%s' and '%s' entangled\n", a ? a->name : "?", b ? b->name : "?");
}

void holo_show_fields(void) {
    printf("=== Holo Fields ===\n");
    printf("%-6s %-16s %-6s %-8s %-8s %-10s %s\n", "ID", "Name", "Type", "Pixels", "Res", "Coherence", "Computed");
    for (int i = 0; i < hf.field_count; i++) {
        HoloField* f = &hf.fields[i];
        printf("%-6s %-16s %-6d %-8d %-8.3f %-10.2f %s\n",
               f->id, f->name, f->type, f->pixel_count,
               f->resolution, f->coherence, f->computed ? "YES" : "NO");
    }
}

void holo_show_storage(void) {
    printf("=== Holo Storage ===\n");
    printf("%-6s %-16s %-8s %-8s %-8s %s\n", "ID", "Name", "Size", "Density", "Speed", "Encoded");
    for (int i = 0; i < hf.storage_count; i++) {
        HoloStorage* s = &hf.storage_units[i];
        printf("%-6s %-16s %-8d %-8.2f %-8.1f %s\n",
               s->id, s->name, s->data_size, s->density, s->read_speed,
               s->encoded ? "YES" : "NO");
    }
}

void holo_show_fabric(void) {
    printf("=== Holo Fabric ===\n");
    printf("  Fields: %d\n", hf.field_count);
    printf("  Storage Units: %d\n", hf.storage_count);
    printf("  Compute Units: %d\n", hf.compute_count);
    printf("  Total Pixels: %d\n", hf.total_pixels);
    printf("  Fabric Coherence: %.4f\n", hf.fabric_coherence);
    printf("  Entanglement: %s\n", hf.entanglement_enabled ? "ENABLED" : "DISABLED");
    printf("  Auto-Optimize: %s\n", hf.auto_optimize ? "ON" : "OFF");
}

void holo_optimize(void) {
    hf.fabric_coherence += 0.1;
    if (hf.fabric_coherence > 1.0) hf.fabric_coherence = 1.0;
    for (int i = 0; i < hf.field_count; i++) {
        hf.fields[i].coherence = hf.fabric_coherence;
    }
    int defragged = 0;
    for (int i = 0; i < hf.storage_count; i++) {
        if (!hf.storage_units[i].encoded) {
            hf.storage_units[i].density *= 0.5;
            defragged++;
        }
    }
    printf("[HOLO] Optimized: coherence=%.2f, defragmented=%d units\n", hf.fabric_coherence, defragged);
}
