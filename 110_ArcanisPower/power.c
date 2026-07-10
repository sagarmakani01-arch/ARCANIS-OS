#include "power.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static PowerManager pm;

void power_init(void) {
    memset(&pm, 0, sizeof(pm));
    pm.state = POWER_STATE_ON;
    pm.profile = PERF_BALANCED;
    pm.total_power_w = 65.0;

    pm.zone_count = 3;
    snprintf(pm.zones[0].name, 64, "CPU Package");
    pm.zones[0].temp_c = 52.3; pm.zones[0].power_w = 45.0; pm.zones[0].fan_rpm = 2100;
    snprintf(pm.zones[1].name, 64, "GPU");
    pm.zones[1].temp_c = 48.7; pm.zones[1].power_w = 120.0; pm.zones[1].fan_rpm = 1800;
    snprintf(pm.zones[2].name, 64, "Chipset");
    pm.zones[2].temp_c = 38.2; pm.zones[2].power_w = 8.5; pm.zones[2].fan_rpm = 1200;

    pm.has_battery = 1;
    snprintf(pm.battery.name, 64, "Li-Ion Polymer");
    pm.battery.capacity_wh = 56.0;
    pm.battery.charge_pct = 78.5;
    pm.battery.voltage = 12.3;
    pm.battery.current_a = 2.1;
    pm.battery.cycles = 342;
    pm.battery.plugged = 1;

    pm.core_count = 4;
    for (int i = 0; i < pm.core_count; i++) {
        snprintf(pm.cores[i].name, 64, "Core %d", i);
        pm.cores[i].core_id = i;
        pm.cores[i].freq_mhz = 2400;
        pm.cores[i].min_freq = 800;
        pm.cores[i].max_freq = 4200;
        pm.cores[i].voltage_mv = 1.15;
        pm.cores[i].utilization = (double)(rand() % 100);
    }

    pm.temp_avg = 46.4;
    printf("Power manager initialized (%s profile)\n",
           pm.profile == PERF_POWERSAVE ? "powersave" :
           pm.profile == PERF_BALANCED ? "balanced" :
           pm.profile == PERF_PERFORMANCE ? "performance" : "turbo");
}

void power_set_state(PowerState state) {
    pm.state = state;
    const char* states[] = {"on", "sleep", "hibernate", "off"};
    printf("Power state: %s\n", states[state]);
}

void power_set_profile(PerfProfile profile) {
    pm.profile = profile;
    const char* names[] = {"powersave", "balanced", "performance", "turbo"};
    printf("Performance profile: %s\n", names[profile]);
}

void power_set_core_freq(int core_id, int freq_mhz) {
    for (int i = 0; i < pm.core_count; i++) {
        if (pm.cores[i].core_id == core_id) {
            if (freq_mhz < pm.cores[i].min_freq) freq_mhz = pm.cores[i].min_freq;
            if (freq_mhz > pm.cores[i].max_freq) freq_mhz = pm.cores[i].max_freq;
            pm.cores[i].freq_mhz = freq_mhz;
            printf("Core %d frequency set to %d MHz\n", core_id, freq_mhz);
            return;
        }
    }
    printf("Core %d not found\n", core_id);
}

void power_list_zones(void) {
    printf("\nThermal Zones:\n");
    printf("  %-15s %8s %10s %10s %s\n", "ZONE", "TEMP", "POWER", "FAN", "THROTTLE");
    printf("  --------------- -------- ---------- ---------- ---------\n");
    for (int i = 0; i < pm.zone_count; i++) {
        printf("  %-15s %7.1fC %9.1fW %8.0fRPM %s\n",
               pm.zones[i].name, pm.zones[i].temp_c, pm.zones[i].power_w,
               pm.zones[i].fan_rpm, pm.zones[i].throttling ? "YES" : "no");
    }
}

void power_list_cores(void) {
    printf("\nCPU Cores:\n");
    printf("  %-10s %8s %8s %8s %8s %s\n", "CORE", "FREQ", "MIN", "MAX", "VOLT", "UTIL");
    printf("  ---------- -------- -------- -------- -------- --------\n");
    for (int i = 0; i < pm.core_count; i++) {
        printf("  %-10s %5dMHz %5dMHz %5dMHz %6.2fV %5.1f%%\n",
               pm.cores[i].name, pm.cores[i].freq_mhz,
               pm.cores[i].min_freq, pm.cores[i].max_freq,
               pm.cores[i].voltage_mv, pm.cores[i].utilization);
    }
}

void power_show_battery(void) {
    if (!pm.has_battery) { printf("No battery detected\n"); return; }
    Battery* b = &pm.battery;
    printf("\nBattery:\n");
    printf("  Type:       %s\n", b->name);
    printf("  Capacity:   %.1f Wh\n", b->capacity_wh);
    printf("  Charge:     %.1f%%\n", b->charge_pct);
    printf("  Voltage:    %.1f V\n", b->voltage);
    printf("  Current:    %.1f A\n", b->current_a);
    printf("  Cycles:     %d\n", b->cycles);
    printf("  Plugged:    %s\n", b->plugged ? "yes" : "no");
}

void power_show_summary(void) {
    printf("\n=== Power Summary ===\n");
    const char* states[] = {"on", "sleep", "hibernate", "off"};
    const char* profiles[] = {"powersave", "balanced", "performance", "turbo"};
    printf("  State:          %s\n", states[pm.state]);
    printf("  Profile:        %s\n", profiles[pm.profile]);
    printf("  Total Power:    %.1f W\n", pm.total_power_w);
    printf("  Avg Temp:       %.1f C\n", pm.temp_avg);
    if (pm.has_battery)
        printf("  Battery:        %.1f%%\n", pm.battery.charge_pct);
    double savings = power_estimate_savings();
    if (savings > 0)
        printf("  Potential Savings: %.1f W (switch to powersave)\n", savings);
}

double power_estimate_savings(void) {
    if (pm.profile == PERF_POWERSAVE) return 0;
    return pm.total_power_w * 0.35;
}
