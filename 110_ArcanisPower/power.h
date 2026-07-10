#ifndef ARCANIS_POWER_H
#define ARCANIS_POWER_H

typedef enum {
    POWER_STATE_ON,
    POWER_STATE_SLEEP,
    POWER_STATE_HIBERNATE,
    POWER_STATE_OFF
} PowerState;

typedef enum {
    PERF_POWERSAVE,
    PERF_BALANCED,
    PERF_PERFORMANCE,
    PERF_TURBO
} PerfProfile;

typedef struct {
    char name[64];
    double temp_c;
    double power_w;
    double fan_rpm;
    int throttling;
} ThermalZone;

typedef struct {
    char name[64];
    double capacity_wh;
    double charge_pct;
    double voltage;
    double current_a;
    int cycles;
    int plugged;
} Battery;

typedef struct {
    char name[64];
    int core_id;
    int freq_mhz;
    int min_freq;
    int max_freq;
    double voltage_mv;
    double utilization;
} CpuCore;

typedef struct {
    PowerState state;
    PerfProfile profile;
    ThermalZone zones[8];
    int zone_count;
    Battery battery;
    int has_battery;
    CpuCore cores[16];
    int core_count;
    double total_power_w;
    double temp_avg;
} PowerManager;

void power_init(void);
void power_set_state(PowerState state);
void power_set_profile(PerfProfile profile);
void power_set_core_freq(int core_id, int freq_mhz);
void power_list_zones(void);
void power_list_cores(void);
void power_show_battery(void);
void power_show_summary(void);
double power_estimate_savings(void);

#endif
