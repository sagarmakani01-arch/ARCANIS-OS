#ifndef EMOTIVE_H
#define EMOTIVE_H

#include <stddef.h>

typedef enum {
    EMOTE_JOY,
    EMOTE_SADNESS,
    EMOTE_ANGER,
    EMOTE_FEAR,
    EMOTE_SURPRISE,
    EMOTE_DISGUST,
    EMOTE_TRUST,
    EMOTE_ANTICIPATION
} EmotionType;

typedef struct {
    EmotionType emotion;
    double intensity;
    double valence;
    double arousal;
    int duration_ms;
} EmotionalState;

typedef struct {
    char id[32];
    char name[64];
    char current_color[8];
    int current_size;
    int current_opacity;
    int animation_speed;
    int layout_priority;
    double emotional_sensitivity;
} AdaptiveUIElement;

typedef struct {
    char trigger[128];
    EmotionType response;
    double probability;
    double intensity_curve[8];
} EmotionalResponse;

typedef struct {
    EmotionalState current;
    EmotionalState history[64];
    int history_count;
    AdaptiveUIElement ui_elements[32];
    EmotionalResponse responses[32];
    double adaptation_speed;
    double empathy_level;
    double mood_trend[3];
} EmotiveEngine;

void emotive_init(EmotiveEngine *engine);
void emotive_detect_emotion(EmotiveEngine *engine, const double *input_signals);
void emotive_adapt_ui(EmotiveEngine *engine);
void emotive_set_mood(EmotiveEngine *engine, EmotionType emotion, double intensity);
void emotive_show_state(EmotiveEngine *engine);
void emotive_show_ui(EmotiveEngine *engine);
void emotive_show_history(EmotiveEngine *engine);

#endif /* EMOTIVE_H */
