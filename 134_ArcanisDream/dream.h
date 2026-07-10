#ifndef DREAM_H
#define DREAM_H

typedef enum {
    PHASE_NREM_1, PHASE_NREM_2, PHASE_NREM_3, PHASE_REM, PHASE_LUCID
} DreamPhase;

typedef struct {
    char id[32];
    char content[1024];
    char symbols[8][64];
    char emotional_tone[32];
    double coherence;
    double novelty;
    double timestamp;
} DreamFragment;

typedef struct {
    char id[32];
    char date[16];
    DreamFragment fragments[16];
    int fragment_count;
    double total_duration;
    int insights_generated;
    int optimization_applied;
} DreamCycle;

typedef struct {
    DreamCycle cycles[16];
    int cycle_count;
    int total_dreams;
    int total_insights;
    int optimizations_derived;
    int subconscious_active;
    double dream_recall;
    int lucid_dreams;
} DreamEngine;

void dream_init(DreamEngine *engine);
void dream_simulate_cycle(DreamEngine *engine);
void dream_extract_insight(DreamEngine *engine);
void dream_apply_optimization(DreamEngine *engine, const char *insight);
void dream_show_cycles(const DreamEngine *engine);
void dream_show_last_dream(const DreamEngine *engine);
void dream_show_stats(const DreamEngine *engine);

#endif
