#ifndef IMMORTAL_H
#define IMMORTAL_H

#include <stddef.h>

typedef enum {
    TRAIT_ANALYTICAL,
    TRAIT_CREATIVE,
    TRAIT_PATIENT,
    TRAIT_CURIOUS,
    TRAIT_DECISIVE,
    TRAIT_CAUTIOUS
} PersonalityTrait;

typedef struct {
    char id[32];
    double timestamp;
    char content[1024];
    double emotional_weight;
    double importance;
    int access_count;
    double last_recalled;
} MemoryFragment;

typedef struct {
    PersonalityTrait trait;
    double weight;
} TraitWithWeight;

typedef struct {
    char id[32];
    char name[64];
    TraitWithWeight traits[8];
    MemoryFragment memories[128];
    int memory_count;
    double personality_coherence;
    double consciousness_level;
    int interaction_count;
    double last_active;
} UserClone;

typedef struct {
    char id[32];
    char pattern[256];
    double frequency;
    char context[256];
    double predictability;
} BehaviorModel;

typedef struct {
    UserClone clones[8];
    int clone_count;
    BehaviorModel models[16];
    int total_memories;
    int total_interactions;
    int evolution_generations;
    double persistence_level;
} ImmortalEngine;

void immortal_init(ImmortalEngine *engine);
int immortal_create_clone(ImmortalEngine *engine, const char *id, const char *name);
int immortal_record_memory(ImmortalEngine *engine, int clone_idx, MemoryFragment memory);
int immortal_recall(ImmortalEngine *engine, int clone_idx, const char *keyword);
int immortal_simulate(ImmortalEngine *engine, int clone_idx, const char *scenario);
int immortal_evolve(ImmortalEngine *engine, int clone_idx);
void immortal_show_clones(ImmortalEngine *engine);
void immortal_show_memories(ImmortalEngine *engine, int clone_idx);
void immortal_show_personality(ImmortalEngine *engine, int clone_idx);
void immortal_show_stats(ImmortalEngine *engine);

#endif /* IMMORTAL_H */
