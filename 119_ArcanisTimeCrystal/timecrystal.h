#ifndef ARCANIS_TIMECRYSTAL_H
#define ARCANIS_TIMECRYSTAL_H

typedef struct {
    double timestamp;
    char state_hash[64];
    char data[2048];
    int version;
    double entropy;
} TimeCrystalMoment;

typedef struct {
    char id[32];
    char name[64];
    TimeCrystalMoment moments[128];
    int moment_count;
    int current_version;
    double temporal_stability;
    int branched;
    char branch_parent[32];
} Timeline;

typedef struct {
    char id[32];
    char name[64];
    double divergence_point;
    char alternate_data[2048];
    double probability;
} ParallelReality;

typedef struct {
    Timeline timelines[16];
    int timeline_count;
    ParallelReality parallel_realities[32];
    int reality_count;
    int total_moments;
    double temporal_coherence;
    int chrono_locked;
    int auto_version;
} TimeCrystalDB;

void tcrystal_init(void);
Timeline* tcrystal_create_timeline(const char* name);
TimeCrystalMoment* tcrystal_snapshot(Timeline* tl, const char* data);
int tcrystal_rollback(Timeline* tl, int version);
Timeline* tcrystal_branch(Timeline* tl, const char* new_name, int from_version);
ParallelReality* tcrystal_create_reality(const char* name, double divergence, const char* data);
void tcrystal_merge(Timeline* a, Timeline* b);
void tcrystal_diff(Timeline* tl, int v1, int v2);
void tcrystal_stabilize(Timeline* tl);
void tcrystal_show_timelines(void);
void tcrystal_show_timeline(Timeline* tl);
void tcrystal_show_realities(void);
void tcrystal_show_coherence(void);

#endif
