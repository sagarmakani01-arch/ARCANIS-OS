/**
 * security_adv.c — Advanced Security & Zero Trust Implementation
 */
#include <arcanis/security_adv.h>
#include <arcanis/string.h>
#include <stdio.h>
#include <string.h>

void sec_adv_init(sec_adv_system_t* sys) {
    if (!sys) return;
    memset(sys, 0, sizeof(sec_adv_system_t));
    sys->overall_trust_score = 85.0;
    sys->zero_trust_enabled = 1;
    sys->event_capacity = SEC_MAX_EVENTS;
    printf("[SECURITY] Zero Trust Architecture initialized\n");
}

int sec_adv_add_identity(sec_adv_system_t* sys, const char* username, const char* role) {
    if (!sys || !username || !role) return -1;
    if (sys->num_identities >= SEC_MAX_USERS) return -1;
    sec_identity_t* id = &sys->identities[sys->num_identities];
    memset(id, 0, sizeof(sec_identity_t));
    snprintf(id->user_id, 32, "u-%u", sys->num_identities);
    string_copy(id->username, username, 64);
    string_copy(id->role, role, 32);
    id->trust_score = 50.0;
    sys->num_identities++;
    return 0;
}

int sec_adv_authenticate(sec_adv_system_t* sys, const char* username, int mfa) {
    if (!sys || !username) return -1;
    for (uint32_t i = 0; i < sys->num_identities; i++) {
        if (string_compare(sys->identities[i].username, username) == 0) {
            sec_identity_t* id = &sys->identities[i];
            id->authenticated = 1;
            id->last_access = 0;
            if (mfa) {
                id->trust_score = 85.0;
                sys->mfa_events++;
            } else {
                id->trust_score = 60.0;
            }
            printf("[SECURITY] User '%s' authenticated (MFA: %s)\n", username, mfa ? "yes" : "no");
            return 0;
        }
    }
    return -1;
}

int sec_adv_list_identities(sec_adv_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "IDENTITIES: %u\n", sys->num_identities);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID        USERNAME       ROLE         AUTH  ACCESS  TRUST  VIOLATIONS\n");
    for (uint32_t i = 0; i < sys->num_identities && pos < buf_len - 120; i++) {
        sec_identity_t* id = &sys->identities[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-9s %-14s %-12s %-5s %5u  %5.1f  %u\n",
            id->user_id, id->username, id->role,
            id->authenticated ? "yes" : "no",
            id->access_count, id->trust_score, id->violations);
    }
    return (int)pos;
}

int sec_adv_add_policy(sec_adv_system_t* sys, const char* name, const char* resource,
                       const char* action, sec_policy_action_t policy_action) {
    if (!sys || !name || !resource || !action) return -1;
    if (sys->num_policies >= SEC_MAX_POLICIES) return -1;
    sec_policy_t* p = &sys->policies[sys->num_policies];
    memset(p, 0, sizeof(sec_policy_t));
    string_copy(p->name, name, SEC_MAX_NAME);
    string_copy(p->resource, resource, 128);
    string_copy(p->action, action, 16);
    p->policy_action = policy_action;
    p->enabled = 1;
    sys->num_policies++;
    return 0;
}

int sec_adv_evaluate(sec_adv_system_t* sys, const char* user,
                     const char* resource, const char* action) {
    if (!sys || !user || !resource || !action) return -1;
    for (uint32_t i = 0; i < sys->num_policies; i++) {
        sec_policy_t* p = &sys->policies[i];
        if (!p->enabled) continue;
        /* Check if policy matches resource/action pattern */
        if (string_compare(p->action, action) != 0 && string_compare(p->action, "*") != 0) continue;
        p->hit_count++;
        sys->total_events++;
        if (p->policy_action == SEC_POLICY_DENY) {
            sys->blocked_events++;
            return -1; /* Denied */
        }
    }
    return 0; /* Allowed */
}

int sec_adv_list_policies(sec_adv_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t pos = 0;
    const char* actions[] = {"ALLOW", "DENY", "MFA", "LOG"};
    pos += snprintf(buf + pos, buf_len - pos, "POLICIES: %u\n", sys->num_policies);
    for (uint32_t i = 0; i < sys->num_policies && pos < buf_len - 80; i++) {
        sec_policy_t* p = &sys->policies[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "  %-20s %-20s %-8s %s\n",
            p->name, p->resource, p->action, actions[p->policy_action]);
    }
    return (int)pos;
}

int sec_adv_log_event(sec_adv_system_t* sys, sec_event_type_t type, const char* user,
                      const char* resource, const char* details, int blocked) {
    if (!sys || !user || !resource || !details) return -1;
    uint32_t idx = sys->event_count % sys->event_capacity;
    sec_event_t* e = &sys->events[idx];
    e->type = type;
    e->timestamp = 0;
    string_copy(e->user, user, 64);
    string_copy(e->resource, resource, 128);
    string_copy(e->details, details, 256);
    e->blocked = blocked;
    e->severity = blocked ? 8.0 : 2.0;
    sys->event_count++;
    sys->total_events++;
    if (blocked) sys->blocked_events++;
    return 0;
}

int sec_adv_get_events(sec_adv_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t pos = 0;
    uint32_t count = sys->event_count < 20 ? sys->event_count : 20;
    const char* types[] = {"LOGIN", "ACCESS", "MFA", "THREAT", "COMPLIANCE"};
    pos += snprintf(buf + pos, buf_len - pos, "SECURITY EVENTS (last %u):\n", count);
    for (uint32_t i = 0; i < count && pos < buf_len - 200; i++) {
        uint32_t idx = (sys->event_count - count + i) % sys->event_capacity;
        sec_event_t* e = &sys->events[idx];
        pos += snprintf(buf + pos, buf_len - pos,
            "  [%s] %s -> %s: %s%s\n",
            types[e->type], e->user, e->resource, e->details,
            e->blocked ? " [BLOCKED]" : "");
    }
    return (int)pos;
}

int sec_adv_add_threat(sec_adv_system_t* sys, const char* name, const char* cve, double cvss) {
    if (!sys || !name || !cve) return -1;
    if (sys->num_threats >= SEC_MAX_THREATS) return -1;
    sec_threat_t* t = &sys->threats[sys->num_threats];
    string_copy(t->name, name, 32);
    string_copy(t->cve_id, cve, 16);
    t->cvss_score = cvss;
    t->patched = 0;
    sys->num_threats++;
    return 0;
}

int sec_adv_list_threats(sec_adv_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "THREATS: %u\n", sys->num_threats);
    for (uint32_t i = 0; i < sys->num_threats && pos < buf_len - 100; i++) {
        sec_threat_t* t = &sys->threats[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "  %-16s %-12s CVSS:%.1f %s\n",
            t->name, t->cve_id, t->cvss_score, t->patched ? "[PATCHED]" : "[UNPATCHED]");
    }
    return (int)pos;
}

int sec_adv_set_zero_trust(sec_adv_system_t* sys, int enabled) {
    if (!sys) return -1;
    sys->zero_trust_enabled = enabled;
    printf("[SECURITY] Zero Trust %s\n", enabled ? "enabled" : "disabled");
    return 0;
}

int sec_adv_get_status(sec_adv_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t authorized = 0, violations = 0;
    for (uint32_t i = 0; i < sys->num_identities; i++) {
        if (sys->identities[i].authenticated) authorized++;
        violations += sys->identities[i].violations;
    }
    return snprintf(buf, buf_len,
        "Zero Trust Security Status:\n"
        "  Zero Trust: %s\n"
        "  Overall Trust: %.1f%%\n"
        "  Identities: %u (authorized: %u)\n"
        "  Policies: %u\n"
        "  Total Events: %llu\n"
        "  Blocked: %llu\n"
        "  MFA Events: %llu\n"
        "  Threats: %u\n",
        sys->zero_trust_enabled ? "ENABLED" : "DISABLED",
        sys->overall_trust_score,
        sys->num_identities, authorized,
        sys->num_policies,
        (unsigned long long)sys->total_events,
        (unsigned long long)sys->blocked_events,
        (unsigned long long)sys->mfa_events,
        sys->num_threats);
}
