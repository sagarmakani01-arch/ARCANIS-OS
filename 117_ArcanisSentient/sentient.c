#include "sentient.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static SentientEngine se;

static const char* health_str(SystemHealth h) {
    static const char* s[] = {"HEALTHY","DEGRADED","CRITICAL","UNKNOWN"};
    return h <= SYSTEM_UNKNOWN ? s[h] : "UNKNOWN";
}

static const char* diag_str(DiagnosisType t) {
    static const char* s[] = {"CPU_SPIKE","MEM_LEAK","IO_BOTTLENECK","NET_LOSS","THERMAL","PROCESS_HANG","FILESYSTEM_CORRUPT"};
    return t <= DIAG_FILESYSTEM_CORRUPT ? s[t] : "UNKNOWN";
}

void sentient_init(void) {
    memset(&se, 0, sizeof(se));
    se.overall_health = SYSTEM_HEALTHY;
    se.self_aware = 1;
    se.auto_heal_enabled = 1;
    se.consciousness_level = 0.1;
    srand((unsigned)time(NULL));

    sentient_add_metric("cpu", 80.0, 95.0, 50.0);
    sentient_add_metric("memory", 75.0, 90.0, 45.0);
    sentient_add_metric("io", 70.0, 88.0, 40.0);
    sentient_add_metric("temperature", 70.0, 85.0, 35.0);
    printf("[SENTIENT] Engine initialized, consciousness=%.2f\n", se.consciousness_level);
}

void sentient_add_metric(const char* name, double warning, double critical, double recovery) {
    if (se.metric_count >= 16) return;
    HealthMetric* m = &se.metrics[se.metric_count++];
    snprintf(m->name, sizeof(m->name), "%s", name);
    m->current_value = 0.0;
    m->warning_threshold = warning;
    m->critical_threshold = critical;
    m->recovery_value = recovery;
    m->alert_count = 0;
    m->health = SYSTEM_HEALTHY;
}

void sentient_update_metric(const char* name, double value) {
    for (int i = 0; i < se.metric_count; i++) {
        if (strcmp(se.metrics[i].name, name) == 0) {
            HealthMetric* m = &se.metrics[i];
            m->current_value = value;
            if (value >= m->critical_threshold) {
                m->health = SYSTEM_CRITICAL;
                m->alert_count++;
            } else if (value >= m->warning_threshold) {
                m->health = SYSTEM_DEGRADED;
                m->alert_count++;
            } else if (value <= m->recovery_value) {
                m->health = SYSTEM_HEALTHY;
            }
            printf("[SENTIENT] Metric '%s' = %.1f -> %s\n", name, value, health_str(m->health));
            return;
        }
    }
}

Diagnosis* sentient_diagnose(const char* description, DiagnosisType type, double severity) {
    if (se.diagnosis_count >= 32) return NULL;
    Diagnosis* d = &se.diagnoses[se.diagnosis_count++];
    snprintf(d->id, sizeof(d->id), "DX-%d", se.diagnosis_count);
    d->type = type;
    snprintf(d->description, sizeof(d->description), "%s", description);
    d->severity = severity;
    d->detected_at = (int)time(NULL);
    d->resolved = 0;
    d->auto_healed = 0;
    d->confidence = rand() % 40 + 60;
    printf("[SENTIENT] Diagnosis: %s [%s] sev=%.1f conf=%d%%\n", d->id, diag_str(type), severity, d->confidence);
    return d;
}

HealPatch* sentient_generate_patch(Diagnosis* d, const char* code, const char* desc) {
    if (!d || se.patch_count >= 32) return NULL;
    HealPatch* p = &se.patches[se.patch_count++];
    snprintf(p->id, sizeof(p->id), "PATCH-%d", se.patch_count);
    p->target_type = d->type;
    snprintf(p->patch_code, sizeof(p->patch_code), "%s", code);
    snprintf(p->description, sizeof(p->description), "%s", desc);
    p->applied = 0;
    p->verified = 0;
    p->rollback_count = 0;
    p->effectiveness = (rand() % 100) / 100.0;
    se.patch_generations++;
    printf("[SENTIENT] Patch generated: %s for %s (eff=%.2f)\n", p->id, d->id, p->effectiveness);
    return p;
}

int sentient_apply_patch(HealPatch* p) {
    if (!p) return 0;
    p->applied = 1;
    p->verified = 1;
    se.healing_actions++;
    se.consciousness_level += 0.05;
    printf("[SENTIENT] Patch %s applied (healing=%d, consciousness=%.2f)\n",
           p->id, se.healing_actions, se.consciousness_level);
    return 1;
}

int sentient_verify_health(void) {
    se.overall_health = SYSTEM_HEALTHY;
    for (int i = 0; i < se.metric_count; i++) {
        if (se.metrics[i].health == SYSTEM_CRITICAL) {
            se.overall_health = SYSTEM_CRITICAL;
        } else if (se.metrics[i].health == SYSTEM_DEGRADED && se.overall_health != SYSTEM_CRITICAL) {
            se.overall_health = SYSTEM_DEGRADED;
        }
    }
    printf("[SENTIENT] System health verified: %s\n", health_str(se.overall_health));
    return se.overall_health;
}

void sentient_auto_heal(void) {
    printf("[SENTIENT] Auto-heal cycle started\n");
    for (int i = 0; i < se.diagnosis_count; i++) {
        Diagnosis* d = &se.diagnoses[i];
        if (!d->resolved && d->severity > 3.0) {
            char code[64], desc[256];
            snprintf(code, sizeof(code), "fix_%s_auto", diag_str(d->type));
            snprintf(desc, sizeof(desc), "Auto-generated fix for %s", diag_str(d->type));
            HealPatch* p = sentient_generate_patch(d, code, desc);
            if (p) {
                sentient_apply_patch(p);
                d->resolved = 1;
                d->auto_healed = 1;
            }
        }
    }
    sentient_verify_health();
    printf("[SENTIENT] Auto-heal complete\n");
}

void sentient_show_health(void) {
    printf("=== System Health ===\n");
    printf("%-16s %-10s %-10s %-10s %-10s %s\n", "Metric", "Current", "Warning", "Critical", "Recovery", "Status");
    for (int i = 0; i < se.metric_count; i++) {
        HealthMetric* m = &se.metrics[i];
        printf("%-16s %-10.1f %-10.1f %-10.1f %-10.1f %s\n",
               m->name, m->current_value, m->warning_threshold,
               m->critical_threshold, m->recovery_value, health_str(m->health));
    }
    printf("  Overall: %s\n", health_str(se.overall_health));
}

void sentient_show_diagnoses(void) {
    printf("=== Diagnoses ===\n");
    printf("%-8s %-20s %-8s %-10s %-8s %s\n", "ID", "Type", "Severity", "Confidence", "Resolved", "Description");
    for (int i = 0; i < se.diagnosis_count; i++) {
        Diagnosis* d = &se.diagnoses[i];
        printf("%-8s %-20s %-8.1f %-10d %-8s %s\n",
               d->id, diag_str(d->type), d->severity, d->confidence,
               d->resolved ? "YES" : "NO", d->description);
    }
}

void sentient_show_patches(void) {
    printf("=== Heal Patches ===\n");
    printf("%-10s %-20s %-10s %-10s %s\n", "ID", "Target", "Applied", "Verified", "Description");
    for (int i = 0; i < se.patch_count; i++) {
        HealPatch* p = &se.patches[i];
        printf("%-10s %-20s %-10s %-10s %s\n",
               p->id, diag_str(p->target_type),
               p->applied ? "YES" : "NO", p->verified ? "YES" : "NO", p->description);
    }
}

void sentient_show_consciousness(void) {
    printf("=== Consciousness Level ===\n");
    printf("  Level: %.2f\n", se.consciousness_level);
    printf("  Self-Aware: %s\n", se.self_aware ? "YES" : "NO");
    printf("  Healing Actions: %d\n", se.healing_actions);
    printf("  Patch Generations: %d\n", se.patch_generations);
    printf("  Auto-Heal: %s\n", se.auto_heal_enabled ? "ENABLED" : "DISABLED");
}
