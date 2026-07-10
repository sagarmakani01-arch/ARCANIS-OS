#include "emotive.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#define MAX_HISTORY 20
#define MAX_UI 10

typedef enum {
    EMOTE_NEUTRAL,
    EMOTE_JOY,
    EMOTE_SADNESS,
    EMOTE_FEAR,
    EMOTE_ANGER,
    EMOTE_TRUST,
    EMOTE_DISGUST,
    EMOTE_SURPRISE,
    EMOTE_ANTICIPATION
} EmotionType;

typedef struct {
    EmotionType emotion;
    double intensity;
    int timestamp;
} EmotionState;

typedef struct {
    char element[32];
    char color[16];
    int size;
} UIElement;

static const char *emotion_names[] = {
    "neutral", "joy", "sadness", "fear", "anger", "trust",
    "disgust", "surprise", "anticipation"
};

typedef struct {
    EmotionType current_emotion;
    double valence;
    double arousal;
    double intensity;
    EmotionState history[MAX_HISTORY];
    int history_count;
    UIElement ui_elements[MAX_UI];
    int ui_count;
} EmotiveEngine;

static EmotiveEngine ee;

void emotive_init(void) {
    srand(time(NULL));
    memset(&ee, 0, sizeof(ee));
    ee.current_emotion = EMOTE_TRUST;
    ee.valence = 0.3;
    ee.arousal = 0.5;
    ee.intensity = 0.5;
    ee.history[ee.history_count++] = (EmotionState){EMOTE_TRUST, 0.5, (int)time(NULL)};
    ee.ui_count = 3;
    strncpy(ee.ui_elements[0].element, "button", 32);
    strncpy(ee.ui_elements[0].color, "blue", 16);
    ee.ui_elements[0].size = 20;
    strncpy(ee.ui_elements[1].element, "panel", 32);
    strncpy(ee.ui_elements[1].color, "gray", 16);
    ee.ui_elements[1].size = 100;
    strncpy(ee.ui_elements[2].element, "text", 32);
    strncpy(ee.ui_elements[2].color, "white", 16);
    ee.ui_elements[2].size = 14;
    printf("[EMOTIVE] Initialized with emotion: %s\n", emotion_names[ee.current_emotion]);
}

void emotive_detect_emotion(const char *input) {
    if (strstr(input, "error")) {
        ee.current_emotion = EMOTE_SADNESS;
        ee.valence = 0.1; ee.arousal = 0.3;
    } else if (strstr(input, "speed") || strstr(input, "fast")) {
        ee.current_emotion = EMOTE_JOY;
        ee.valence = 0.9; ee.arousal = 0.8;
    } else if (strstr(input, "danger") || strstr(input, "threat")) {
        ee.current_emotion = EMOTE_FEAR;
        ee.valence = 0.1; ee.arousal = 0.9;
    } else if (strstr(input, "anger") || strstr(input, "rage")) {
        ee.current_emotion = EMOTE_ANGER;
        ee.valence = 0.2; ee.arousal = 0.9;
    } else if (strstr(input, "surprise") || strstr(input, "unexpected")) {
        ee.current_emotion = EMOTE_SURPRISE;
        ee.valence = 0.5; ee.arousal = 0.8;
    } else if (strstr(input, "trust") || strstr(input, "safe")) {
        ee.current_emotion = EMOTE_TRUST;
        ee.valence = 0.7; ee.arousal = 0.3;
    } else {
        ee.current_emotion = EMOTE_NEUTRAL;
        ee.valence = 0.5; ee.arousal = 0.5;
    }
    ee.intensity = (ee.valence + ee.arousal) / 2.0;
    if (ee.history_count < MAX_HISTORY)
        ee.history[ee.history_count++] = (EmotionState){ee.current_emotion, ee.intensity, (int)time(NULL)};
    printf("[EMOTIVE] Detected emotion: %s (val=%.2f, aro=%.2f)\n",
           emotion_names[ee.current_emotion], ee.valence, ee.arousal);
}

void emotive_adapt_ui(void) {
    for (int i = 0; i < ee.ui_count; i++) {
        switch (ee.current_emotion) {
            case EMOTE_JOY:
                strncpy(ee.ui_elements[i].color, "yellow", 16);
                ee.ui_elements[i].size += 2;
                break;
            case EMOTE_SADNESS:
                strncpy(ee.ui_elements[i].color, "blue", 16);
                ee.ui_elements[i].size -= 1;
                break;
            case EMOTE_FEAR:
                strncpy(ee.ui_elements[i].color, "purple", 16);
                ee.ui_elements[i].size += 1;
                break;
            case EMOTE_ANGER:
                strncpy(ee.ui_elements[i].color, "red", 16);
                ee.ui_elements[i].size += 3;
                break;
            default:
                strncpy(ee.ui_elements[i].color, "gray", 16);
                break;
        }
    }
    printf("[EMOTIVE] UI adapted to %s emotion\n", emotion_names[ee.current_emotion]);
}

void emotive_set_mood(const char *mood, double intensity) {
    for (int i = 0; i < 9; i++) {
        if (strcmp(mood, emotion_names[i]) == 0) {
            ee.current_emotion = (EmotionType)i;
            ee.intensity = intensity;
            ee.valence = (rand() % 1000) / 1000.0;
            ee.arousal = (rand() % 1000) / 1000.0;
            if (ee.history_count < MAX_HISTORY)
                ee.history[ee.history_count++] = (EmotionState){ee.current_emotion, intensity, (int)time(NULL)};
            printf("[EMOTIVE] Mood set to %s (intensity: %.2f)\n", mood, intensity);
            return;
        }
    }
    printf("[EMOTIVE] Unknown emotion '%s'\n", mood);
}

void emotive_show_state(void) {
    printf("\n=== EMOTIVE STATE ===\n");
    printf("Current emotion: %s\n", emotion_names[ee.current_emotion]);
    printf("Valence: %.2f\n", ee.valence);
    printf("Arousal: %.2f\n", ee.arousal);
    printf("Intensity: %.2f\n", ee.intensity);
}

void emotive_show_ui(void) {
    printf("\n=== UI ELEMENTS ===\n");
    printf("%-15s %-12s %-8s\n", "Element", "Color", "Size");
    printf("----------------------------------------\n");
    for (int i = 0; i < ee.ui_count; i++)
        printf("%-15s %-12s %-8d\n", ee.ui_elements[i].element, ee.ui_elements[i].color, ee.ui_elements[i].size);
}

void emotive_show_history(void) {
    printf("\n=== EMOTION HISTORY (last %d) ===\n", ee.history_count);
    printf("%-15s %-10s\n", "Emotion", "Intensity");
    printf("----------------------------------------\n");
    int start = ee.history_count > 6 ? ee.history_count - 6 : 0;
    for (int i = start; i < ee.history_count; i++)
        printf("%-15s %-10.2f\n", emotion_names[ee.history[i].emotion], ee.history[i].intensity);
}
