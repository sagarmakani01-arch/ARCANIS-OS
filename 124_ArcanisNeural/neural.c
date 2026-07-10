#include "neural.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#define MAX_REGIONS 10
#define MAX_WAVES 5
#define MAX_PATTERNS 50
#define MAX_COMMANDS 50

typedef struct {
    char name[32];
    double frequency;
    double amplitude;
    double phase;
} BrainWave;

typedef struct {
    char name[32];
    BrainWave waves[MAX_WAVES];
    int wave_count;
    double focus_level;
} BrainRegion;

typedef struct {
    char id[32];
    char pattern_data[128];
    double confidence;
    int activated;
} ThoughtPattern;

typedef struct {
    char id[32];
    char command[128];
    double priority;
    int executed;
} NeuralCommand;

typedef struct {
    BrainRegion regions[MAX_REGIONS];
    int region_count;
    ThoughtPattern patterns[MAX_PATTERNS];
    int pattern_count;
    NeuralCommand commands[MAX_COMMANDS];
    int command_count;
    int focus_level;
    int sessions_completed;
    char last_scan[64];
} NeuralInterface;

static NeuralInterface ni;

void neural_init(void) {
    srand(time(NULL));
    memset(&ni, 0, sizeof(ni));
    ni.region_count = 4;
    const char *names[] = {"prefrontal", "motor", "visual", "temporal"};
    for (int i = 0; i < ni.region_count; i++) {
        strncpy(ni.regions[i].name, names[i], sizeof(ni.regions[i].name) - 1);
        ni.regions[i].wave_count = 3;
        ni.regions[i].focus_level = 0.75;
        for (int j = 0; j < 3; j++) {
            snprintf(ni.regions[i].waves[j].name, sizeof(ni.regions[i].waves[j].name), "wave%d", j + 1);
            ni.regions[i].waves[j].frequency = (rand() % 4000 + 100) / 100.0;
            ni.regions[i].waves[j].amplitude = (rand() % 100) / 100.0;
            ni.regions[i].waves[j].phase = (rand() % 360);
        }
    }
    ni.focus_level = 75;
    ni.sessions_completed = 0;
    printf("[NEURAL] Interface initialized with %d regions\n", ni.region_count);
}

void neural_scan_brain(void) {
    time_t t = time(NULL);
    strncpy(ni.last_scan, ctime(&t), sizeof(ni.last_scan) - 1);
    ni.last_scan[strcspn(ni.last_scan, "\n")] = 0;
    printf("\n=== BRAIN SCAN [%s] ===\n", ni.last_scan);
    printf("%-20s %-8s %-12s %-12s %-10s\n", "Region", "Waves", "Freq(Hz)", "Amplitude", "Phase(deg)");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < ni.region_count; i++) {
        for (int j = 0; j < ni.regions[i].wave_count; j++) {
            printf("%-20s %-8s %-12.2f %-12.4f %-10.1f\n",
                   ni.regions[i].name, ni.regions[i].waves[j].name,
                   ni.regions[i].waves[j].frequency, ni.regions[i].waves[j].amplitude,
                   ni.regions[i].waves[j].phase);
        }
    }
    printf("------------------------------------------------------------\n");
}

void neural_learn_pattern(const char *pattern_data) {
    if (ni.pattern_count >= MAX_PATTERNS) { printf("[NEURAL] Pattern storage full\n"); return; }
    ThoughtPattern *tp = &ni.patterns[ni.pattern_count++];
    snprintf(tp->id, sizeof(tp->id), "PAT-%03d", ni.pattern_count);
    strncpy(tp->pattern_data, pattern_data, sizeof(tp->pattern_data) - 1);
    tp->confidence = (rand() % 1000) / 1000.0;
    tp->activated = 0;
    printf("[NEURAL] Learned pattern %s: %s (conf: %.2f)\n", tp->id, tp->pattern_data, tp->confidence);
}

void neural_interpret_thought(const char *thought) {
    if (ni.pattern_count == 0) { printf("[NEURAL] No patterns to match\n"); return; }
    int idx = rand() % ni.pattern_count;
    NeuralCommand *cmd = &ni.commands[ni.command_count++];
    snprintf(cmd->id, sizeof(cmd->id), "CMD-%03d", ni.command_count);
    snprintf(cmd->command, sizeof(cmd->command), "exec_%s", thought);
    cmd->priority = ni.patterns[idx].confidence;
    cmd->executed = 0;
    printf("[NEURAL] Interpreted thought '%s' -> command %s (priority %.2f)\n", thought, cmd->id, cmd->priority);
}

void neural_execute_thought(const char *cmd_id) {
    for (int i = 0; i < ni.command_count; i++) {
        if (strcmp(ni.commands[i].id, cmd_id) == 0 && !ni.commands[i].executed) {
            ni.commands[i].executed = 1;
            printf("[NEURAL] Executing command %s: %s\n", ni.commands[i].id, ni.commands[i].command);
            return;
        }
    }
    printf("[NEURAL] Command %s not found or already executed\n", cmd_id);
}

void neural_train_focus(void) {
    ni.focus_level += 5;
    ni.sessions_completed++;
    printf("[NEURAL] Focus training session %d complete. Focus level: %d\n", ni.sessions_completed, ni.focus_level);
}

void neural_show_status(void) {
    printf("\n=== NEURAL STATUS ===\n");
    printf("Regions: %d\n", ni.region_count);
    printf("Patterns stored: %d\n", ni.pattern_count);
    printf("Commands pending: %d\n", ni.command_count);
    printf("Focus level: %d\n", ni.focus_level);
    printf("Sessions completed: %d\n", ni.sessions_completed);
    printf("Last scan: %s\n", ni.last_scan);
}

void neural_show_brainwaves(void) {
    printf("\n=== BRAINWAVES ===\n");
    printf("%-20s %-10s %-10s %-10s\n", "Region", "Wave", "Freq", "Amp");
    printf("----------------------------------------\n");
    for (int i = 0; i < ni.region_count; i++)
        for (int j = 0; j < ni.regions[i].wave_count; j++)
            printf("%-20s %-10s %-10.2f %-10.4f\n",
                   ni.regions[i].name, ni.regions[i].waves[j].name,
                   ni.regions[i].waves[j].frequency, ni.regions[i].waves[j].amplitude);
}

void neural_show_patterns(void) {
    printf("\n=== PATTERNS ===\n");
    printf("%-10s %-30s %-10s %-10s\n", "ID", "Data", "Confidence", "Activated");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < ni.pattern_count; i++)
        printf("%-10s %-30s %-10.2f %-10d\n",
               ni.patterns[i].id, ni.patterns[i].pattern_data,
               ni.patterns[i].confidence, ni.patterns[i].activated);
}

void neural_show_commands(void) {
    printf("\n=== COMMANDS ===\n");
    printf("%-10s %-30s %-10s %-10s\n", "ID", "Command", "Priority", "Executed");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < ni.command_count; i++)
        printf("%-10s %-30s %-10.2f %-10d\n",
               ni.commands[i].id, ni.commands[i].command,
               ni.commands[i].priority, ni.commands[i].executed);
}
