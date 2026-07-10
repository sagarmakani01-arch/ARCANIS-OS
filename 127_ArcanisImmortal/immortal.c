#include "immortal.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#define MAX_CLONES 20
#define MAX_MEMORIES 50

typedef struct {
    char id[32];
    char content[128];
    char keyword[32];
    int timestamp;
    int strength;
} MemoryFragment;

typedef struct {
    char id[32];
    char name[48];
    double consciousness_level;
    double personality_coherence;
    int memory_count;
    MemoryFragment memories[MAX_MEMORIES];
    int evolution_generations;
    int trait_aggression;
    int trait_curiosity;
    int trait_empathy;
} UserClone;

typedef struct {
    UserClone clones[MAX_CLONES];
    int clone_count;
    int total_memories;
    int evolution_generations;
    double consciousness_level;
    double personality_coherence;
} ImmortalEngine;

static ImmortalEngine ie;

void immortal_init(void) {
    srand(time(NULL));
    memset(&ie, 0, sizeof(ie));
    ie.evolution_generations = 1;
    ie.consciousness_level = 0.1;
    ie.personality_coherence = 0.5;
    printf("[IMMORTAL] Engine initialized\n");
}

void immortal_create_clone(const char *name) {
    if (ie.clone_count >= MAX_CLONES) { printf("[IMMORTAL] Clone limit reached\n"); return; }
    UserClone *c = &ie.clones[ie.clone_count++];
    snprintf(c->id, sizeof(c->id), "CLN-%03d", ie.clone_count);
    strncpy(c->name, name, sizeof(c->name) - 1);
    c->consciousness_level = 0.1;
    c->personality_coherence = (rand() % 1000) / 1000.0;
    c->memory_count = 0;
    c->evolution_generations = 1;
    c->trait_aggression = rand() % 100;
    c->trait_curiosity = rand() % 100;
    c->trait_empathy = rand() % 100;
    printf("[IMMORTAL] Created clone '%s' (%s) consciousness: %.2f\n", c->name, c->id, c->consciousness_level);
}

void immortal_record_memory(const char *clone_id, const char *content, const char *keyword) {
    for (int i = 0; i < ie.clone_count; i++) {
        if (strcmp(ie.clones[i].id, clone_id) == 0) {
            if (ie.clones[i].memory_count >= MAX_MEMORIES) { printf("[IMMORTAL] Memory full\n"); return; }
            MemoryFragment *m = &ie.clones[i].memories[ie.clones[i].memory_count++];
            strncpy(m->content, content, sizeof(m->content) - 1);
            strncpy(m->keyword, keyword, sizeof(m->keyword) - 1);
            m->timestamp = (int)time(NULL);
            m->strength = rand() % 100;
            snprintf(m->id, sizeof(m->id), "MEM-%03d", ie.total_memories + 1);
            ie.total_memories++;
            printf("[IMMORTAL] Memory recorded for %s: '%s' [%s]\n", clone_id, content, keyword);
            return;
        }
    }
    printf("[IMMORTAL] Clone %s not found\n", clone_id);
}

void immortal_recall(const char *keyword) {
    printf("\n=== RECALL: '%s' ===\n", keyword);
    int found = 0;
    for (int i = 0; i < ie.clone_count; i++) {
        for (int j = 0; j < ie.clones[i].memory_count; j++) {
            if (strstr(ie.clones[i].memories[j].keyword, keyword) ||
                strstr(ie.clones[i].memories[j].content, keyword)) {
                printf("[%s] %s: %s (strength: %d)\n",
                       ie.clones[i].name, ie.clones[i].memories[j].id,
                       ie.clones[i].memories[j].content, ie.clones[i].memories[j].strength);
                found = 1;
            }
        }
    }
    if (!found) printf("[IMMORTAL] No memories found for '%s'\n", keyword);
}

void immortal_simulate(const char *clone_id, const char *scenario) {
    for (int i = 0; i < ie.clone_count; i++) {
        if (strcmp(ie.clones[i].id, clone_id) == 0) {
            printf("\n=== SIMULATION: %s in '%s' ===\n", ie.clones[i].name, scenario);
            printf("Consciousness: %.2f, Coherence: %.2f\n", ie.clones[i].consciousness_level, ie.clones[i].personality_coherence);
            printf("Traits: aggression=%d, curiosity=%d, empathy=%d\n",
                   ie.clones[i].trait_aggression, ie.clones[i].trait_curiosity, ie.clones[i].trait_empathy);
            printf("Behavior: ");
            int action = rand() % 3;
            if (action == 0) printf("explores '%s' curiously\n", scenario);
            else if (action == 1) printf("analyzes '%s' logically\n", scenario);
            else printf("responds emotionally to '%s'\n", scenario);
            return;
        }
    }
    printf("[IMMORTAL] Clone %s not found\n", clone_id);
}

void immortal_evolve(void) {
    ie.evolution_generations++;
    ie.consciousness_level += 0.05;
    ie.personality_coherence += 0.02;
    printf("[IMMORTAL] Evolution generation %d: consciousness=%.2f, coherence=%.2f\n",
           ie.evolution_generations, ie.consciousness_level, ie.personality_coherence);
}

void immortal_show_clones(void) {
    printf("\n=== CLONES ===\n");
    printf("%-10s %-20s %-8s %-8s %-6s %-6s %-6s\n", "ID", "Name", "Consc.", "Coher.", "Aggr", "Curi", "Emp");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < ie.clone_count; i++)
        printf("%-10s %-20s %-8.2f %-8.2f %-6d %-6d %-6d\n",
               ie.clones[i].id, ie.clones[i].name,
               ie.clones[i].consciousness_level, ie.clones[i].personality_coherence,
               ie.clones[i].trait_aggression, ie.clones[i].trait_curiosity, ie.clones[i].trait_empathy);
}

void immortal_show_memories(void) {
    printf("\n=== MEMORIES ===\n");
    for (int i = 0; i < ie.clone_count; i++) {
        printf("--- %s (%s) ---\n", ie.clones[i].name, ie.clones[i].id);
        for (int j = 0; j < ie.clones[i].memory_count; j++)
            printf("  %s [%s]: %s (str:%d)\n",
                   ie.clones[i].memories[j].id, ie.clones[i].memories[j].keyword,
                   ie.clones[i].memories[j].content, ie.clones[i].memories[j].strength);
    }
}

void immortal_show_personality(void) {
    printf("\n=== PERSONALITY ===\n");
    printf("%-20s %-12s %-12s %-12s %-12s\n", "Name", "Coherence", "Aggression", "Curiosity", "Empathy");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < ie.clone_count; i++)
        printf("%-20s %-12.2f %-12d %-12d %-12d\n",
               ie.clones[i].name, ie.clones[i].personality_coherence,
               ie.clones[i].trait_aggression, ie.clones[i].trait_curiosity, ie.clones[i].trait_empathy);
}

void immortal_show_stats(void) {
    printf("\n=== IMMORTAL STATS ===\n");
    printf("Active clones: %d\n", ie.clone_count);
    printf("Total memories: %d\n", ie.total_memories);
    printf("Evolution generations: %d\n", ie.evolution_generations);
    printf("Global consciousness: %.2f\n", ie.consciousness_level);
    printf("Global coherence: %.2f\n", ie.personality_coherence);
}
