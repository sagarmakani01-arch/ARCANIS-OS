#include "dream.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
    char description[64];
    float coherence;
    float novelty;
} Fragment;

typedef struct {
    int cycle_id;
    Fragment fragments[4];
    int fragment_count;
    float resonance;
} DreamCycle;

typedef struct {
    DreamCycle cycles[10];
    int cycle_count;
    int total_dreams;
    int total_insights;
    int optimizations_derived;
    char last_dream_content[128];
} DreamEngine;

static DreamEngine de;

void dream_init(void) {
    de.cycle_count = 2;
    de.total_dreams = 0;
    de.total_insights = 0;
    de.optimizations_derived = 0;
    strcpy(de.last_dream_content, "none");
    for (int i = 0; i < de.cycle_count; i++) {
        de.cycles[i].cycle_id = i + 1;
        de.cycles[i].fragment_count = 0;
        de.cycles[i].resonance = 0.5f;
    }
    srand((unsigned)time(NULL));
}

static const char *fragment_topics[] = {
    "flying through data streams",
    "talking to AI entities",
    "exploring code forests",
    "building quantum bridges",
    "dancing with algorithms",
    "dreaming in binary"
};

void dream_simulate_cycle(void) {
    if (de.cycle_count >= 10) return;
    DreamCycle *dc = &de.cycles[de.cycle_count++];
    dc->cycle_id = de.cycle_count;
    dc->fragment_count = 4;
    dc->resonance = 0.5f + ((float)rand() / RAND_MAX) * 0.5f;
    for (int i = 0; i < 4; i++) {
        int idx = rand() % 6;
        snprintf(dc->fragments[i].description, sizeof(dc->fragments[i].description),
                 "%s", fragment_topics[idx]);
        dc->fragments[i].coherence = 0.3f + ((float)rand() / RAND_MAX) * 0.6f;
        dc->fragments[i].novelty = (float)rand() / RAND_MAX;
    }
    de.total_dreams++;
    snprintf(de.last_dream_content, sizeof(de.last_dream_content),
             "Cycle %d: %s", dc->cycle_id, dc->fragments[0].description);
}

void dream_extract_insight(void) {
    if (de.cycle_count == 0) return;
    DreamCycle *dc = &de.cycles[de.cycle_count - 1];
    int best = 0;
    for (int i = 1; i < dc->fragment_count; i++) {
        if (dc->fragments[i].novelty > dc->fragments[best].novelty)
            best = i;
    }
    printf("Insight from fragment '%s' (novelty=%.2f)\n",
           dc->fragments[best].description, dc->fragments[best].novelty);
    de.total_insights++;
}

void dream_apply_optimization(void) {
    printf("Applying dream-derived optimization #%d\n", de.optimizations_derived + 1);
    de.optimizations_derived++;
}

void dream_show_cycles(void) {
    printf("\n%-8s %-10s %-10s %s\n", "CycleID", "Fragments", "Resonance", "Sample Fragment");
    printf("----------------------------------------------------------\n");
    for (int i = 0; i < de.cycle_count; i++) {
        printf("%-8d %-10d %-10.2f %s\n",
               de.cycles[i].cycle_id,
               de.cycles[i].fragment_count,
               de.cycles[i].resonance,
               de.cycles[i].fragments[0].description);
    }
}

void dream_show_last_dream(void) {
    printf("Last Dream: %s\n", de.last_dream_content);
}

void dream_show_stats(void) {
    printf("\n%-20s %d\n", "Total Dreams", de.total_dreams);
    printf("%-20s %d\n", "Total Insights", de.total_insights);
    printf("%-20s %d\n", "Optimizations", de.optimizations_derived);
    printf("%-20s %d\n", "Active Cycles", de.cycle_count);
}
