/**
 * security_adv.h — Advanced Security & Zero Trust
 *
 * Zero trust architecture, SIEM, IAM, compliance scanning.
 */
#ifndef ARCANIS_SECURITY_ADV_H
#define ARCANIS_SECURITY_ADV_H

#include <arcanis/types.h>

#define SEC_MAX_POLICIES     256
#define SEC_MAX_EVENTS       4096
#define SEC_MAX_USERS        512
#define SEC_MAX_THREATS      128
#define SEC_MAX_NAME         64
#define SEC_MAX_HOST         128

typedef struct {
    char user_id[32];
    char username[64];
    char role[32];
    int authenticated;
    int authorized;
    uint64_t last_access;
    uint32_t access_count;
    uint32_t violations;
    char device_id[64];
    double trust_score;
} sec_identity_t;

typedef enum {
    SEC_POLICY_ALLOW,
    SEC_POLICY_DENY,
    SEC_POLICY_MFA,
    SEC_POLICY_LOG
} sec_policy_action_t;

typedef struct {
    char name[SEC_MAX_NAME];
    char resource[128];
    char action[16];
    sec_policy_action_t policy_action;
    char conditions[256];
    int enabled;
    uint64_t hit_count;
} sec_policy_t;

typedef enum {
    SEC_EVENT_LOGIN,
    SEC_EVENT_ACCESS,
    SEC_EVENT_MFA,
    SEC_EVENT_THREAT,
    SEC_EVENT_COMPLIANCE
} sec_event_type_t;

typedef struct {
    sec_event_type_t type;
    uint64_t timestamp;
    char user[64];
    char resource[128];
    char details[256];
    int blocked;
    double severity;
} sec_event_t;

typedef struct {
    char name[32];
    char cve_id[16];
    char description[256];
    double cvss_score;
    int patched;
    char mitigation[256];
} sec_threat_t;

typedef struct {
    char framework[32];
    char control_id[16];
    char description[256];
    int passed;
    char recommendation[256];
} sec_compliance_t;

typedef struct {
    sec_identity_t identities[SEC_MAX_USERS];
    uint32_t num_identities;

    sec_policy_t policies[SEC_MAX_POLICIES];
    uint32_t num_policies;

    sec_event_t events[SEC_MAX_EVENTS];
    uint32_t event_count;
    uint32_t event_capacity;

    sec_threat_t threats[SEC_MAX_THREATS];
    uint32_t num_threats;

    uint64_t total_events;
    uint64_t blocked_events;
    uint64_t mfa_events;
    double overall_trust_score;
    int zero_trust_enabled;
} sec_adv_system_t;

void sec_adv_init(sec_adv_system_t* sys);

int  sec_adv_add_identity(sec_adv_system_t* sys, const char* username, const char* role);
int  sec_adv_authenticate(sec_adv_system_t* sys, const char* username, int mfa);
int  sec_adv_list_identities(sec_adv_system_t* sys, char* buf, uint32_t buf_len);

int  sec_adv_add_policy(sec_adv_system_t* sys, const char* name, const char* resource,
                        const char* action, sec_policy_action_t policy_action);
int  sec_adv_evaluate(sec_adv_system_t* sys, const char* user, const char* resource,
                      const char* action);
int  sec_adv_list_policies(sec_adv_system_t* sys, char* buf, uint32_t buf_len);

int  sec_adv_log_event(sec_adv_system_t* sys, sec_event_type_t type, const char* user,
                       const char* resource, const char* details, int blocked);
int  sec_adv_get_events(sec_adv_system_t* sys, char* buf, uint32_t buf_len);

int  sec_adv_add_threat(sec_adv_system_t* sys, const char* name, const char* cve,
                        double cvss);
int  sec_adv_list_threats(sec_adv_system_t* sys, char* buf, uint32_t buf_len);

int  sec_adv_set_zero_trust(sec_adv_system_t* sys, int enabled);
int  sec_adv_get_status(sec_adv_system_t* sys, char* buf, uint32_t buf_len);

#endif
