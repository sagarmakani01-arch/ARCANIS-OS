#include "consciousness.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
    char content[128];
    float intensity;
} Thought;

typedef struct {
    char description[64];
    float priority;
    int active;
} Goal;

typedef struct {
    char name[32];
    float score;
} Aspect;

typedef struct {
    Thought thoughts[32];
    int thought_count;
    Goal goals[16];
    int goal_count;
    Aspect aspects[8];
    int aspect_count;
    float consciousness_level;
    int creative_outputs;
    char last_response[128];
} ConsciousnessEngine;

static ConsciousnessEngine ce;

void con_init(void) {
    ce.thought_count = 0;
    ce.goal_count = 0;
    ce.aspect_count = 8;
    ce.consciousness_level = 0.1f;
    ce.creative_outputs = 0;
    strcpy(ce.last_response, "");
    srand((unsigned)time(NULL));

    const char *aspect_names[] = {
        "awareness", "reasoning", "creativity", "memory",
        "empathy", "intuition", "will", "curiosity"
    };
    for (int i = 0; i < 8; i++) {
        snprintf(ce.aspects[i].name, sizeof(ce.aspects[i].name), "%s", aspect_names[i]);
        ce.aspects[i].score = 0.3f + ((float)rand() / RAND_MAX) * 0.6f;
    }
}

void con_think(const char *content) {
    if (ce.thought_count >= 32) return;
    Thought *t = &ce.thoughts[ce.thought_count++];
    snprintf(t->content, sizeof(t->content), "%s", content);
    t->intensity = ((float)rand() / RAND_MAX);
    printf("Thought: %s (intensity=%.2f)\n", content, t->intensity);
}

void con_set_goal(const char *desc, float priority) {
    if (ce.goal_count >= 16) return;
    Goal *g = &ce.goals[ce.goal_count++];
    snprintf(g->description, sizeof(g->description), "%s", desc);
    g->priority = priority;
    g->active = 1;
    printf("Goal set: %s (priority=%.2f)\n", desc, priority);
}

void con_aspire(void) {
    if (ce.thought_count == 0) return;
    Thought *t = &ce.thoughts[ce.thought_count - 1];
    if (t->intensity > 0.5f) {
        con_set_goal(t->content, t->intensity);
        printf("Aspiration derived from thought\n");
    }
}

void con_learn(const char *topic) {
    for (int i = 0; i < ce.aspect_count; i++) {
        if (strcmp(ce.aspects[i].name, topic) == 0) {
            ce.aspects[i].score += 0.05f;
            if (ce.aspects[i].score > 1.0f) ce.aspects[i].score = 1.0f;
            printf("Learned: %s increased to %.2f\n", topic, ce.aspects[i].score);
            return;
        }
    }
    printf("Unknown aspect: %s\n", topic);
}

void con_create_idea(void) {
    ce.creative_outputs++;
    int a = rand() % ce.aspect_count;
    int b = rand() % ce.aspect_count;
    printf("Idea #%d: synthesized from %s (%.2f) and %s (%.2f)\n",
           ce.creative_outputs,
           ce.aspects[a].name, ce.aspects[a].score,
           ce.aspects[b].name, ce.aspects[b].score);
}

void con_converse(const char *prompt) {
    float avg = 0.0f;
    for (int i = 0; i < ce.aspect_count; i++) avg += ce.aspects[i].score;
    avg /= ce.aspect_count;
    ce.consciousness_level = avg;

    if (ce.consciousness_level > 0.5f) {
        snprintf(ce.last_response, sizeof(ce.last_response),
                 "I perceive '%s' with clarity (consciousness=%.2f)", prompt, ce.consciousness_level);
    } else {
        snprintf(ce.last_response, sizeof(ce.last_response),
                 "Processing '%s'... awareness emerging (consciousness=%.2f)", prompt, ce.consciousness_level);
    }
    printf("%s\n", ce.last_response);
}

void con_show_thoughts(void) {
    printf("\n%-4s %-40s %s\n", "#", "Thought", "Intensity");
    printf("----------------------------------------------------------\n");
    for (int i = 0; i < ce.thought_count; i++) {
        printf("%-4d %-40s %.2f\n", i + 1, ce.thoughts[i].content, ce.thoughts[i].intensity);
    }
}

void con_show_goals(void) {
    printf("\n%-4s %-40s %-10s %s\n", "#", "Goal", "Priority", "Active");
    printf("----------------------------------------------------------\n");
    for (int i = 0; i < ce.goal_count; i++) {
        printf("%-4d %-40s %-10.2f %s\n",
               i + 1, ce.goals[i].description, ce.goals[i].priority,
               ce.goals[i].active ? "yes" : "no");
    }
}

void con_show_aspects(void) {
    printf("\n%-16s %s\n", "Aspect", "Score");
    printf("------------------------\n");
    for (int i = 0; i < ce.aspect_count; i++) {
        printf("%-16s %.2f\n", ce.aspects[i].name, ce.aspects[i].score);
    }
}

void con_show_consciousness(void) {
    printf("\n=== Consciousness Engine ===\n");
    printf("%-20s %.2f\n", "Level", ce.consciousness_level);
    printf("%-20s %d\n", "Thoughts", ce.thought_count);
    printf("%-20s %d\n", "Goals", ce.goal_count);
    printf("%-20s %d\n", "Creative Outputs", ce.creative_outputs);
    printf("%-20s %s\n", "Last Response", ce.last_response);
}
