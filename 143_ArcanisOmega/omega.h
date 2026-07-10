#ifndef OMEGA_H
#define OMEGA_H

typedef enum {
    OMEGA_ADAPT_HARDWARE, OMEGA_ADAPT_REALITY, OMEGA_SELF_EVOLVE, OMEGA_INFINITE_SCALE, OMEGA_UNIVERSAL
} OmegaProtocol;

typedef struct {
    char id[32];
    char target_environment[64];
    char adaptation_strategy[256];
    double compatibility;
    double transformation_time_ms;
    double success_rate;
} UniversalAdapter;

typedef struct {
    char id[32];
    char scaling_dimension[32];
    double current_capacity;
    double max_capacity;
    double elasticity;
    int auto_balance;
} InfiniteScale;

typedef struct {
    OmegaProtocol protocol;
    int active;
    double proficiency;
} Protocol;

typedef struct {
    Protocol protocols[5];
    UniversalAdapter adapters[8];
    InfiniteScale scaling;
    double universal_compatibility;
    double reality_flexibility;
    char purpose_evolved[8][128];
    int total_forms;
    int eternal_evolution;
    char last_form[64];
} OmegaOS;

void omega_init(OmegaOS *os);
void omega_adapt_to(OmegaOS *os, const char *environment);
void omega_scale(OmegaOS *os, const char *dimension, double capacity);
void omega_evolve_purpose(OmegaOS *os, const char *purpose);
void omega_transcend_limitation(OmegaOS *os);
void omega_show_adapters(const OmegaOS *os);
void omega_show_scaling(const OmegaOS *os);
void omega_show_purposes(const OmegaOS *os);
void omega_show_omega_status(const OmegaOS *os);

#endif
