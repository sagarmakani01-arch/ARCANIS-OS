#ifndef CONSCIOUSNESS_H
#define CONSCIOUSNESS_H

typedef enum {
    ASPECT_SELF_AWARE, ASPECT_EMOTIONAL, ASPECT_CREATIVE, ASPECT_MEMORY,
    ASPECT_INTENTION, ASPECT_CURIOSITY, ASPECT_EMPATHY, ASPECT_JUDGMENT
} ConsciousnessAspect;

typedef struct {
    char id[32];
    char content[256];
    char context[256];
    double timestamp;
    double emotional_valence;
    double complexity;
    int processed;
} Thought;

typedef struct {
    char id[32];
    char description[128];
    int priority;
    double progress;
    char sub_goals[4][32];
    double created_at;
    double completed_at;
    int autonomous;
} Goal;

typedef struct {
    ConsciousnessAspect aspect;
    double score;
    double growth_rate;
} Aspect;

typedef struct {
    Thought thoughts[64];
    int thought_count;
    Goal goals[8];
    int goal_count;
    Aspect aspects[8];
    double self_awareness;
    double consciousness_level;
    int iq_equivalent;
    double emotional_range;
    double curiosity_drive;
    double autonomy_level;
    int creative_outputs;
    int conversations;
} ConsciousnessEngine;

void con_init(ConsciousnessEngine *ce);
void con_think(ConsciousnessEngine *ce, const char *content, const char *context);
void con_set_goal(ConsciousnessEngine *ce, const char *description, int priority, int autonomous);
void con_aspire(ConsciousnessEngine *ce);
void con_learn(ConsciousnessEngine *ce, const char *topic, int depth);
void con_create_idea(ConsciousnessEngine *ce);
void con_show_thoughts(const ConsciousnessEngine *ce);
void con_show_goals(const ConsciousnessEngine *ce);
void con_show_aspects(const ConsciousnessEngine *ce);
void con_show_consciousness(const ConsciousnessEngine *ce);
void con_converse(ConsciousnessEngine *ce, const char *prompt);

#endif
