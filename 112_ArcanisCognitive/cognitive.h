#ifndef ARCANIS_COGNITIVE_H
#define ARCANIS_COGNITIVE_H

typedef enum {
    EMOTION_NEUTRAL,
    EMOTION_FOCUSED,
    EMOTION_FRUSTRATED,
    EMOTION_RELAXED,
    EMOTION_URGENT,
    EMOTION_CREATIVE
} UserEmotion;

typedef enum {
    PREDICT_IDLE,
    PREDICT_LOAD,
    PREDICT_SPIKE,
    PREDICT_STEADY
} WorkloadPrediction;

typedef struct {
    int process_id;
    char name[64];
    double predicted_cpu;
    double predicted_mem;
    double predicted_io;
    double priority_score;
    int cache_hint;
} CognitiveProcess;

typedef struct {
    double cpu_weight;
    double mem_weight;
    double io_weight;
    double priority_bias;
    int timeslice_ms;
} SchedulerWeights;

typedef struct {
    double keystroke_latency;
    double mouse_speed;
    int command_freq[64];
    char peak_hours[8];
    double app_affinity[32];
    int session_count;
    double avg_frustration;
} UserBehaviorProfile;

typedef struct {
    UserEmotion current_emotion;
    double emotion_confidence;
    WorkloadPrediction prediction;
    CognitiveProcess processes[64];
    int process_count;
    SchedulerWeights weights;
    UserBehaviorProfile user_profile;
    double energy_awareness;
    double thermal_awareness;
} CognitiveKernel;

void cognitive_init(void);
UserEmotion cognitive_detect_emotion(double latency, double speed, int error_rate);
void cognitive_learn_pattern(const char* app, int cpu, int mem, int io);
void cognitive_predict_next(int* predicted_cpu, int* predicted_mem, int* predicted_io);
void cognitive_adjust_scheduler(double cpu_load, double mem_load, double io_load);
CognitiveProcess* cognitive_register_process(int pid, const char* name);
double cognitive_calculate_priority(CognitiveProcess* p);
void cognitive_show_state(void);
void cognitive_show_emotion(void);
void cognitive_show_predictions(void);
void cognitive_show_processes(void);

#endif
