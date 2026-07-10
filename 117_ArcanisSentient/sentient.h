#ifndef ARCANIS_SENTIENT_H
#define ARCANIS_SENTIENT_H

typedef enum {
    SYSTEM_HEALTHY,
    SYSTEM_DEGRADED,
    SYSTEM_CRITICAL,
    SYSTEM_UNKNOWN
} SystemHealth;

typedef enum {
    DIAG_CPU_SPIKE,
    DIAG_MEM_LEAK,
    DIAG_IO_BOTTLENECK,
    DIAG_NET_LOSS,
    DIAG_THERMAL,
    DIAG_PROCESS_HANG,
    DIAG_FILESYSTEM_CORRUPT
} DiagnosisType;

typedef struct {
    char id[32];
    DiagnosisType type;
    char description[256];
    double severity;
    int detected_at;
    int resolved;
    int auto_healed;
    int confidence;
} Diagnosis;

typedef struct {
    char id[32];
    DiagnosisType target_type;
    char patch_code[4096];
    char description[256];
    int applied;
    int verified;
    int rollback_count;
    double effectiveness;
} HealPatch;

typedef struct {
    char name[64];
    double current_value;
    double warning_threshold;
    double critical_threshold;
    double recovery_value;
    int alert_count;
    SystemHealth health;
} HealthMetric;

typedef struct {
    HealthMetric metrics[16];
    int metric_count;
    Diagnosis diagnoses[32];
    int diagnosis_count;
    HealPatch patches[32];
    int patch_count;
    SystemHealth overall_health;
    int self_aware;
    int auto_heal_enabled;
    int healing_actions;
    int patch_generations;
    double recovery_time_avg;
    double consciousness_level;
} SentientEngine;

void sentient_init(void);
void sentient_add_metric(const char* name, double warning, double critical, double recovery);
void sentient_update_metric(const char* name, double value);
Diagnosis* sentient_diagnose(const char* description, DiagnosisType type, double severity);
HealPatch* sentient_generate_patch(Diagnosis* d, const char* code, const char* desc);
int sentient_apply_patch(HealPatch* p);
int sentient_verify_health(void);
void sentient_auto_heal(void);
void sentient_show_health(void);
void sentient_show_diagnoses(void);
void sentient_show_patches(void);
void sentient_show_consciousness(void);

#endif
