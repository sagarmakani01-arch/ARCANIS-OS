#include "bio_os.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
    char data[64];
    int length;
} BioSequence;

typedef struct {
    int cell_id;
    char type[32];
    float health;
    int sequence_count;
    BioSequence sequences[8];
    int active;
} BioCell;

typedef struct {
    BioCell cells[16];
    int cell_count;
    int total_sequences;
    float avg_health;
} BioSystem;

static BioSystem bs;

void bio_init(void) {
    bs.cell_count = 2;
    bs.total_sequences = 0;
    bs.avg_health = 90.0f;
    srand((unsigned)time(NULL));

    snprintf(bs.cells[0].type, sizeof(bs.cells[0].type), "neuron");
    bs.cells[0].cell_id = 1;
    bs.cells[0].health = 85.0f + ((float)rand() / RAND_MAX) * 15.0f;
    bs.cells[0].sequence_count = 0;
    bs.cells[0].active = 1;

    snprintf(bs.cells[1].type, sizeof(bs.cells[1].type), "hepatocyte");
    bs.cells[1].cell_id = 2;
    bs.cells[1].health = 80.0f + ((float)rand() / RAND_MAX) * 20.0f;
    bs.cells[1].sequence_count = 0;
    bs.cells[1].active = 1;
}

void bio_create_cell(const char *type) {
    if (bs.cell_count >= 16) return;
    BioCell *c = &bs.cells[bs.cell_count++];
    c->cell_id = bs.cell_count;
    snprintf(c->type, sizeof(c->type), "%s", type);
    c->health = 80.0f + ((float)rand() / RAND_MAX) * 20.0f;
    c->sequence_count = 0;
    c->active = 1;
}

void bio_add_sequence(int cell_id, const char *data) {
    for (int i = 0; i < bs.cell_count; i++) {
        if (bs.cells[i].cell_id == cell_id && bs.cells[i].sequence_count < 8) {
            BioSequence *s = &bs.cells[i].sequences[bs.cells[i].sequence_count++];
            snprintf(s->data, sizeof(s->data), "%s", data);
            s->length = (int)strlen(data);
            bs.total_sequences++;
            return;
        }
    }
}

void bio_replicate(int cell_id) {
    if (bs.cell_count >= 16) return;
    for (int i = 0; i < bs.cell_count; i++) {
        if (bs.cells[i].cell_id == cell_id) {
            BioCell *c = &bs.cells[bs.cell_count++];
            c->cell_id = bs.cell_count;
            snprintf(c->type, sizeof(c->type), "%s_clone", bs.cells[i].type);
            c->health = bs.cells[i].health * (0.9f + ((float)rand() / RAND_MAX) * 0.1f);
            c->sequence_count = 0;
            c->active = 1;
            printf("Replicated %s -> %s (health: %.1f)\n", bs.cells[i].type, c->type, c->health);
            return;
        }
    }
}

void bio_compute(void) {
    float result = 0.0f;
    for (int i = 0; i < bs.cell_count; i++) {
        if (bs.cells[i].active)
            result += bs.cells[i].health * bs.cells[i].sequence_count;
    }
    printf("Bio-computation result: %.2f\n", result);
}

void bio_show_cells(void) {
    printf("\n%-6s %-16s %-8s %-6s %s\n", "ID", "Type", "Health", "Seqs", "Active");
    printf("------------------------------------------------\n");
    for (int i = 0; i < bs.cell_count; i++) {
        printf("%-6d %-16s %-8.1f %-6d %s\n",
               bs.cells[i].cell_id, bs.cells[i].type,
               bs.cells[i].health, bs.cells[i].sequence_count,
               bs.cells[i].active ? "yes" : "no");
    }
}

void bio_show_sequences(int cell_id) {
    for (int i = 0; i < bs.cell_count; i++) {
        if (bs.cells[i].cell_id == cell_id) {
            printf("\nSequences for %s (ID=%d):\n", bs.cells[i].type, cell_id);
            for (int j = 0; j < bs.cells[i].sequence_count; j++) {
                printf("  %d. %s (len=%d)\n", j + 1,
                       bs.cells[i].sequences[j].data,
                       bs.cells[i].sequences[j].length);
            }
            return;
        }
    }
}

void bio_show_system(void) {
    printf("\n=== BioOS System ===\n");
    printf("%-20s %d\n", "Total Cells", bs.cell_count);
    printf("%-20s %d\n", "Total Sequences", bs.total_sequences);
    float avg = 0.0f;
    for (int i = 0; i < bs.cell_count; i++) avg += bs.cells[i].health;
    if (bs.cell_count > 0) avg /= bs.cell_count;
    printf("%-20s %.1f\n", "Avg Health", avg);
}
