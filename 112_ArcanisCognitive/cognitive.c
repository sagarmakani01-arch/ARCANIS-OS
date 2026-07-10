#include "cognitive.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static CognitiveKernel ck;

void cognitive_init(void) {
    memset(&ck, 0, sizeof(ck));
    ck.current_emotion = EMOTION_NEUTRAL;
    ck.emotion_confidence = 0.5;
    ck.prediction = PREDICT_STEADY;
    ck.weights.cpu_weight = 1.0;
    ck.weights.mem_weight = 1.0;
    ck.weights.io_weight = 1.0;
    ck.weights.priority_bias = 0.0;
    ck.weights.timeslice_ms = 100;
    ck.energy_awareness = 0.5;
    ck.thermal_awareness = 0.3;
    printf("Cognitive Kernel initialized (emotion: neutral, prediction: steady)\n");
}

UserEmotion cognitive_detect_emotion(double latency, double speed, int error_rate) {
    if (error_rate > 10 && latency < 0.05) ck.current_emotion = EMOTION_FRUSTRATED;
    else if (speed > 1000 && error_rate < 2) ck.current_emotion = EMOTION_FOCUSED;
    else if (latency > 0.5) ck.current_emotion = EMOTION_RELAXED;
    else if (latency < 0.02 && speed > 500) ck.current_emotion = EMOTION_URGENT;
    else if (error_rate < 1 && latency > 0.1) ck.current_emotion = EMOTION_CREATIVE;
    else ck.current_emotion = EMOTION_NEUTRAL;
    ck.emotion_confidence = 0.7 + (rand() % 25) / 100.0;
    return ck.current_emotion;
}

void cognitive_learn_pattern(const char* app, int cpu, int mem, int io) {
    printf("Learning pattern: %s (cpu:%d mem:%d io:%d)\n", app, cpu, mem, io);
    ck.user_profile.app_affinity[rand() % 32] += 0.1;
}

void cognitive_predict_next(int* predicted_cpu, int* predicted_mem, int* predicted_io) {
    *predicted_cpu = 45 + rand() % 40;
    *predicted_mem = 30 + rand() % 50;
    *predicted_io = 20 + rand() % 60;
    if (*predicted_cpu > 70) ck.prediction = PREDICT_SPIKE;
    else if (*predicted_cpu > 50) ck.prediction = PREDICT_LOAD;
    else ck.prediction = PREDICT_STEADY;
}

void cognitive_adjust_scheduler(double cpu_load, double mem_load, double io_load) {
    ck.weights.cpu_weight = 1.0 + (cpu_load / 100.0);
    ck.weights.mem_weight = 1.0 + (mem_load / 100.0);
    ck.weights.io_weight = 1.0 + (io_load / 100.0);
    if (ck.current_emotion == EMOTION_URGENT || ck.current_emotion == EMOTION_FOCUSED)
        ck.weights.timeslice_ms = 150;
    else if (ck.current_emotion == EMOTION_RELAXED)
        ck.weights.timeslice_ms = 75;
    else
        ck.weights.timeslice_ms = 100;
    printf("Scheduler adjusted: cpu=%.2f mem=%.2f io=%.2f timeslice=%dms\n",
           ck.weights.cpu_weight, ck.weights.mem_weight,
           ck.weights.io_weight, ck.weights.timeslice_ms);
}

void cognitive_show_state(void) {
    const char* emotions[] = {"neutral", "focused", "frustrated", "relaxed", "urgent", "creative"};
    const char* preds[] = {"idle", "load", "spike", "steady"};
    printf("\n=== Cognitive Kernel ===\n");
    printf("Emotion: %s (%.0f%% confidence)\n", emotions[ck.current_emotion], ck.emotion_confidence * 100);
    printf("Prediction: %s\n", preds[ck.prediction]);
    printf("Scheduler: cpu=%.2f mem=%.2f io=%.2f | timeslice=%dms\n",
           ck.weights.cpu_weight, ck.weights.mem_weight,
           ck.weights.io_weight, ck.weights.timeslice_ms);
    printf("Energy awareness: %.0f%% | Thermal awareness: %.0f%%\n",
           ck.energy_awareness * 100, ck.thermal_awareness * 100);
}
