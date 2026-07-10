/**
 * autonomous.h — Autonomous Systems
 *
 * Self-healing, auto-scaling, auto-remediation, orchestration.
 */
#ifndef ARCANIS_AUTONOMOUS_H
#define ARCANIS_AUTONOMOUS_H

#include <arcanis/types.h>

#define AU_MAX_POLICIES      128
#define AU_MAX_ACTIONS       64
#define AU_MAX_METRICS       32
#define AU_MAX_NAME          64
#define AU_MAX_MSG           256

typedef enum {
    AU_STATE_NORMAL,
    AU_STATE_DEGRADED,
    AU_STATE_CRITICAL,
    AU_STATE_HEALING,
    AU_STATE_RECOVERED
} au_system_state_t;

typedef struct {
    char name[64];
    double current_value;
    double warning_threshold;
    double critical_threshold;
    double target_value;
    int trending_up;
} au_metric_t;

typedef enum {
    AU_ACTION_RESTART,
    AU_ACTION_SCALE_UP,
    AU_ACTION_SCALE_DOWN,
    AU_ACTION_FAILOVER,
    AU_ACTION_ROLLBACK,
    AU_ACTION_NOTIFY,
    AU_ACTION_CUSTOM
} au_action_type_t;

typedef struct {
    au_action_type_t type;
    char name[AU_MAX_NAME];
    char target[AU_MAX_NAME];
    char params[256];
    int executed;
    uint64_t executed_at;
    int success;
} au_action_t;

typedef struct {
    char name[AU_MAX_NAME];
    char metric_name[64];
    char condition[16];
    double threshold;
    uint32_t cooldown_seconds;
    uint32_t max_actions;
    uint32_t action_count;
    au_action_t actions[AU_MAX_ACTIONS];
    uint32_t num_actions;
    int enabled;
    uint64_t last_triggered;
} au_healing_policy_t;

typedef struct {
    char name[AU_MAX_NAME];
    char metric_name[64];
    uint32_t min_instances;
    uint32_t max_instances;
    uint32_t current_instances;
    double scale_up_threshold;
    double scale_down_threshold;
    uint32_t scale_up_by;
    uint32_t scale_down_by;
    uint32_t cooldown_seconds;
    int enabled;
    uint64_t last_scale_up;
    uint64_t last_scale_down;
} au_scaling_policy_t;

typedef struct {
    au_system_state_t state;
    au_metric_t metrics[AU_MAX_METRICS];
    uint32_t num_metrics;

    au_healing_policy_t healing_policies[AU_MAX_POLICIES];
    uint32_t num_healing_policies;

    au_scaling_policy_t scaling_policies[AU_MAX_POLICIES];
    uint32_t num_scaling_policies;

    uint64_t total_incidents;
    uint64_t total_healing_actions;
    uint64_t total_scale_events;
    uint32_t health_score; /* 0-100 */
} au_system_t;

void au_init(au_system_t* sys);

/* Metrics */
int  au_add_metric(au_system_t* sys, const char* name, double warning, double critical);
int  au_update_metric(au_system_t* sys, const char* name, double value);
int  au_list_metrics(au_system_t* sys, char* buf, uint32_t buf_len);

/* Healing policies */
int  au_add_healing_policy(au_system_t* sys, const char* name, const char* metric,
                           const char* condition, double threshold);
int  au_add_healing_action(au_system_t* sys, const char* policy_name,
                           au_action_type_t type, const char* target);
int  au_run_healing(au_system_t* sys);
int  au_list_policies(au_system_t* sys, char* buf, uint32_t buf_len);

/* Auto-scaling */
int  au_add_scaling_policy(au_system_t* sys, const char* name, const char* metric,
                           uint32_t min_inst, uint32_t max_inst, double scale_up);
int  au_run_scaling(au_system_t* sys);
int  au_list_scaling(au_system_t* sys, char* buf, uint32_t buf_len);

/* Dashboard */
int  au_get_status(au_system_t* sys, char* buf, uint32_t buf_len);

#endif
