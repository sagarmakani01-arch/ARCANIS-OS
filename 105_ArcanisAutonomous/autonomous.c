/**
 * autonomous.c — Autonomous Systems Implementation
 */
#include <arcanis/autonomous.h>
#include <arcanis/string.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void au_init(au_system_t* sys) {
    if (!sys) return;
    memset(sys, 0, sizeof(au_system_t));
    sys->state = AU_STATE_NORMAL;
    sys->health_score = 100;
    printf("[AUTONOMOUS] Self-healing system initialized\n");
}

int au_add_metric(au_system_t* sys, const char* name, double warning, double critical) {
    if (!sys || !name) return -1;
    if (sys->num_metrics >= AU_MAX_METRICS) return -1;
    au_metric_t* m = &sys->metrics[sys->num_metrics];
    string_copy(m->name, name, 64);
    m->warning_threshold = warning;
    m->critical_threshold = critical;
    m->target_value = 0;
    sys->num_metrics++;
    return 0;
}

int au_update_metric(au_system_t* sys, const char* name, double value) {
    if (!sys || !name) return -1;
    for (uint32_t i = 0; i < sys->num_metrics; i++) {
        if (string_compare(sys->metrics[i].name, name) == 0) {
            sys->metrics[i].current_value = value;
            sys->metrics[i].trending_up = value > sys->metrics[i].current_value;
            /* Update health score */
            if (value >= sys->metrics[i].critical_threshold)
                sys->health_score = (sys->health_score > 30) ? sys->health_score - 10 : 30;
            else if (value >= sys->metrics[i].warning_threshold)
                sys->health_score = (sys->health_score > 60) ? sys->health_score - 5 : 60;
            else
                sys->health_score = (sys->health_score < 100) ? sys->health_score + 2 : 100;
            return 0;
        }
    }
    return -1;
}

int au_list_metrics(au_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "METRICS:\n");
    pos += snprintf(buf + pos, buf_len - pos, "NAME           VALUE    WARNING CRITICAL TARGET\n");
    for (uint32_t i = 0; i < sys->num_metrics && pos < buf_len - 80; i++) {
        au_metric_t* m = &sys->metrics[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-14s %8.2f %7.2f %7.2f %7.2f%s\n",
            m->name, m->current_value, m->warning_threshold, m->critical_threshold, m->target_value,
            m->current_value >= m->critical_threshold ? " CRIT" :
            m->current_value >= m->warning_threshold ? " WARN" : "");
    }
    return (int)pos;
}

int au_add_healing_policy(au_system_t* sys, const char* name, const char* metric,
                          const char* condition, double threshold) {
    if (!sys || !name || !metric || !condition) return -1;
    if (sys->num_healing_policies >= AU_MAX_POLICIES) return -1;
    au_healing_policy_t* p = &sys->healing_policies[sys->num_healing_policies];
    memset(p, 0, sizeof(au_healing_policy_t));
    string_copy(p->name, name, AU_MAX_NAME);
    string_copy(p->metric_name, metric, 64);
    string_copy(p->condition, condition, 16);
    p->threshold = threshold;
    p->cooldown_seconds = 300;
    p->max_actions = 3;
    p->enabled = 1;
    sys->num_healing_policies++;
    printf("[AUTONOMOUS] Healing policy '%s' added\n", name);
    return 0;
}

int au_add_healing_action(au_system_t* sys, const char* policy_name,
                          au_action_type_t type, const char* target) {
    if (!sys || !policy_name || !target) return -1;
    for (uint32_t i = 0; i < sys->num_healing_policies; i++) {
        if (string_compare(sys->healing_policies[i].name, policy_name) == 0) {
            au_healing_policy_t* p = &sys->healing_policies[i];
            if (p->num_actions >= AU_MAX_ACTIONS) return -1;
            au_action_t* a = &p->actions[p->num_actions];
            a->type = type;
            string_copy(a->name, "", AU_MAX_NAME);
            string_copy(a->target, target, AU_MAX_NAME);
            p->num_actions++;
            return 0;
        }
    }
    return -1;
}

int au_run_healing(au_system_t* sys) {
    if (!sys) return -1;
    printf("[AUTONOMOUS] Running healing check...\n");
    for (uint32_t i = 0; i < sys->num_healing_policies; i++) {
        au_healing_policy_t* p = &sys->healing_policies[i];
        if (!p->enabled) continue;
        for (uint32_t j = 0; j < sys->num_metrics; j++) {
            if (string_compare(sys->metrics[j].name, p->metric_name) != 0) continue;
            if (sys->metrics[j].current_value >= p->threshold) {
                printf("[AUTONOMOUS] Policy '%s' triggered (%.2f >= %.2f)\n",
                       p->name, sys->metrics[j].current_value, p->threshold);
                sys->state = AU_STATE_HEALING;
                for (uint32_t k = 0; k < p->num_actions; k++) {
                    p->actions[k].executed = 1;
                    p->actions[k].success = 1;
                    sys->total_healing_actions++;
                    printf("[AUTONOMOUS] Action: %d on %s\n",
                           p->actions[k].type, p->actions[k].target);
                }
                p->action_count++;
                sys->total_incidents++;
            }
        }
    }
    if (sys->state == AU_STATE_HEALING) sys->state = AU_STATE_RECOVERED;
    return 0;
}

int au_list_policies(au_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "HEALING POLICIES: %u\n", sys->num_healing_policies);
    for (uint32_t i = 0; i < sys->num_healing_policies && pos < buf_len - 60; i++) {
        au_healing_policy_t* p = &sys->healing_policies[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "  %-20s [%s] %s >= %.2f (actions: %u, triggered: %u)\n",
            p->name, p->enabled ? "ON" : "OFF", p->metric_name,
            p->threshold, p->num_actions, p->action_count);
    }
    return (int)pos;
}

int au_add_scaling_policy(au_system_t* sys, const char* name, const char* metric,
                          uint32_t min_inst, uint32_t max_inst, double scale_up) {
    if (!sys || !name || !metric) return -1;
    if (sys->num_scaling_policies >= AU_MAX_POLICIES) return -1;
    au_scaling_policy_t* p = &sys->scaling_policies[sys->num_scaling_policies];
    memset(p, 0, sizeof(au_scaling_policy_t));
    string_copy(p->name, name, AU_MAX_NAME);
    string_copy(p->metric_name, metric, 64);
    p->min_instances = min_inst;
    p->max_instances = max_inst;
    p->current_instances = min_inst;
    p->scale_up_threshold = scale_up;
    p->scale_down_threshold = scale_up * 0.3;
    p->scale_up_by = 2;
    p->scale_down_by = 1;
    p->cooldown_seconds = 120;
    p->enabled = 1;
    sys->num_scaling_policies++;
    printf("[AUTONOMOUS] Scaling policy '%s' added\n", name);
    return 0;
}

int au_run_scaling(au_system_t* sys) {
    if (!sys) return -1;
    for (uint32_t i = 0; i < sys->num_scaling_policies; i++) {
        au_scaling_policy_t* p = &sys->scaling_policies[i];
        if (!p->enabled) continue;
        for (uint32_t j = 0; j < sys->num_metrics; j++) {
            if (string_compare(sys->metrics[j].name, p->metric_name) != 0) continue;
            double v = sys->metrics[j].current_value;
            if (v >= p->scale_up_threshold && p->current_instances < p->max_instances) {
                p->current_instances += p->scale_up_by;
                if (p->current_instances > p->max_instances) p->current_instances = p->max_instances;
                sys->total_scale_events++;
                printf("[AUTONOMOUS] Scaling UP '%s': %u -> %u\n",
                       p->name, p->current_instances - p->scale_up_by, p->current_instances);
            } else if (v <= p->scale_down_threshold && p->current_instances > p->min_instances) {
                p->current_instances -= p->scale_down_by;
                if (p->current_instances < p->min_instances) p->current_instances = p->min_instances;
                sys->total_scale_events++;
                printf("[AUTONOMOUS] Scaling DOWN '%s': %u -> %u\n",
                       p->name, p->current_instances + p->scale_down_by, p->current_instances);
            }
        }
    }
    return 0;
}

int au_list_scaling(au_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "SCALING POLICIES: %u\n", sys->num_scaling_policies);
    for (uint32_t i = 0; i < sys->num_scaling_policies && pos < buf_len - 80; i++) {
        au_scaling_policy_t* p = &sys->scaling_policies[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "  %-20s %s inst: %u/%u scale: up@%.0f%% down@%.0f%% [%s]\n",
            p->name, p->metric_name, p->current_instances, p->max_instances,
            p->scale_up_threshold, p->scale_down_threshold,
            p->enabled ? "ON" : "OFF");
    }
    return (int)pos;
}

int au_get_status(au_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    const char* states[] = {"NORMAL", "DEGRADED", "CRITICAL", "HEALING", "RECOVERED"};
    return snprintf(buf, buf_len,
        "Autonomous System Status:\n"
        "  State: %s\n"
        "  Health Score: %u/100\n"
        "  Healing Policies: %u\n"
        "  Scaling Policies: %u\n"
        "  Total Incidents: %llu\n"
        "  Healing Actions: %llu\n"
        "  Scale Events: %llu\n",
        states[sys->state], sys->health_score,
        sys->num_healing_policies, sys->num_scaling_policies,
        (unsigned long long)sys->total_incidents,
        (unsigned long long)sys->total_healing_actions,
        (unsigned long long)sys->total_scale_events);
}
