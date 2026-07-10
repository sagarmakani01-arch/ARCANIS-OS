#ifndef ARCANIS_NEURAL_H
#define ARCANIS_NEURAL_H

typedef enum {
    SIGNAL_EEG_ALPHA,
    SIGNAL_EEG_BETA,
    SIGNAL_EEG_THETA,
    SIGNAL_EEG_DELTA,
    SIGNAL_EEG_GAMMA
} BrainSignalType;

typedef struct {
    BrainSignalType type;
    double frequency;
    double amplitude;
    double coherence;
    double attention;
    double meditation;
} BrainWave;

typedef struct {
    int id;
    char pattern[256];
    char interpreted_command[128];
    double confidence;
    int repeat_count;
} ThoughtPattern;

typedef struct {
    int id;
    char region[32];
    BrainWave waves[8];
    int wave_count;
    double activation;
    double connectivity;
} BrainRegion;

typedef struct {
    char id[32];
    char command[128];
    double probability;
    int executed;
} NeuralCommand;

typedef struct {
    char id[32];
    char user_name[64];
    BrainRegion regions[8];
    int region_count;
    ThoughtPattern patterns[64];
    int pattern_count;
    double focus_level;
    double cognitive_load;
    int neurofeedback_active;
    NeuralCommand pending_commands[16];
    int command_count;
    double learning_curve;
    int sessions_completed;
} NeuralInterface;

void neural_init(void);
void neural_scan_brain(void);
ThoughtPattern* neural_learn_pattern(const char* pattern, const char* command);
NeuralCommand* neural_interpret_thought(double* raw_signal, int len);
int neural_execute_thought(NeuralCommand* cmd);
void neural_train_focus(int minutes);
void neural_show_status(void);
void neural_show_brainwaves(void);
void neural_show_patterns(void);
void neural_show_commands(void);

#endif
