#include "timecrystal.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static TimeCrystalDB tcdb;

void tcrystal_init(void) {
    memset(&tcdb, 0, sizeof(tcdb));
    tcdb.temporal_coherence = 1.0;
    tcdb.chrono_locked = 0;
    tcdb.auto_version = 1;
    srand((unsigned)time(NULL));

    tcrystal_create_timeline("prime");
    printf("[TCRYSTAL] TimeCrystal initialized with %d timeline(s)\n", tcdb.timeline_count);
}

Timeline* tcrystal_create_timeline(const char* name) {
    if (tcdb.timeline_count >= 16) return NULL;
    Timeline* tl = &tcdb.timelines[tcdb.timeline_count++];
    snprintf(tl->id, sizeof(tl->id), "TL-%d", tcdb.timeline_count);
    snprintf(tl->name, sizeof(tl->name), "%s", name);
    tl->moment_count = 0;
    tl->current_version = 0;
    tl->temporal_stability = 0.9;
    tl->branched = 0;
    memset(tl->branch_parent, 0, sizeof(tl->branch_parent));
    printf("[TCRYSTAL] Timeline '%s' created (id=%s)\n", name, tl->id);
    return tl;
}

TimeCrystalMoment* tcrystal_snapshot(Timeline* tl, const char* data) {
    if (!tl || tl->moment_count >= 128) return NULL;
    TimeCrystalMoment* m = &tl->moments[tl->moment_count++];
    m->timestamp = (double)time(NULL);
    snprintf(m->state_hash, sizeof(m->state_hash), "HASH-%04x", rand() % 0xFFFF);
    snprintf(m->data, sizeof(m->data), "%s", data);
    m->version = tl->moment_count;
    m->entropy = (rand() % 1000) / 1000.0;
    tl->current_version = m->version;
    tcdb.total_moments++;
    printf("[TCRYSTAL] Snapshot v%d on '%s': %s\n", m->version, tl->name, data);
    return m;
}

int tcrystal_rollback(Timeline* tl, int version) {
    if (!tl) return 0;
    for (int i = 0; i < tl->moment_count; i++) {
        if (tl->moments[i].version == version) {
            tl->current_version = version;
            printf("[TCRYSTAL] Rollback '%s' to v%d\n", tl->name, version);
            return 1;
        }
    }
    printf("[TCRYSTAL] Version v%d not found in '%s'\n", version, tl->name);
    return 0;
}

Timeline* tcrystal_branch(Timeline* tl, const char* new_name, int from_version) {
    if (!tl || tcdb.timeline_count >= 16) return NULL;
    Timeline* branch = &tcdb.timelines[tcdb.timeline_count++];
    snprintf(branch->id, sizeof(branch->id), "TL-%d", tcdb.timeline_count);
    snprintf(branch->name, sizeof(branch->name), "%s", new_name);
    branch->moment_count = 0;
    branch->current_version = 0;
    branch->temporal_stability = tl->temporal_stability * 0.9;
    branch->branched = 1;
    snprintf(branch->branch_parent, sizeof(branch->branch_parent), "%s", tl->id);

    for (int i = 0; i < tl->moment_count && tl->moments[i].version <= from_version; i++) {
        if (branch->moment_count < 128) {
            branch->moments[branch->moment_count++] = tl->moments[i];
        }
    }
    branch->current_version = from_version;
    printf("[TCRYSTAL] Branch '%s' from '%s' at v%d\n", new_name, tl->name, from_version);
    return branch;
}

ParallelReality* tcrystal_create_reality(const char* name, double divergence, const char* data) {
    if (tcdb.reality_count >= 32) return NULL;
    ParallelReality* pr = &tcdb.parallel_realities[tcdb.reality_count++];
    snprintf(pr->id, sizeof(pr->id), "PR-%d", tcdb.reality_count);
    snprintf(pr->name, sizeof(pr->name), "%s", name);
    pr->divergence_point = divergence;
    snprintf(pr->alternate_data, sizeof(pr->alternate_data), "%s", data);
    pr->probability = (rand() % 1000) / 1000.0;
    printf("[TCRYSTAL] Parallel reality '%s' (div=%.2f, prob=%.2f)\n", name, divergence, pr->probability);
    return pr;
}

void tcrystal_merge(Timeline* a, Timeline* b) {
    if (!a || !b) return;
    int merge_count = b->moment_count < (128 - a->moment_count) ? b->moment_count : (128 - a->moment_count);
    for (int i = 0; i < merge_count; i++) {
        TimeCrystalMoment* m = &a->moments[a->moment_count++];
        *m = b->moments[i];
        m->entropy = (a->moments[i < a->moment_count - 1 ? i : 0].entropy + b->moments[i].entropy) / 2.0;
    }
    a->current_version = a->moment_count;
    printf("[TCRYSTAL] Merged '%s' <- '%s': %d moments\n", a->name, b->name, merge_count);
}

void tcrystal_diff(Timeline* tl, int v1, int v2) {
    if (!tl) return;
    TimeCrystalMoment *m1 = NULL, *m2 = NULL;
    for (int i = 0; i < tl->moment_count; i++) {
        if (tl->moments[i].version == v1) m1 = &tl->moments[i];
        if (tl->moments[i].version == v2) m2 = &tl->moments[i];
    }
    printf("=== Diff '%s' v%d vs v%d ===\n", tl->name, v1, v2);
    if (m1 && m2) {
        printf("  Data: '%s' -> '%s'\n", m1->data, m2->data);
        printf("  Entropy: %.4f -> %.4f\n", m1->entropy, m2->entropy);
        printf("  Hash: %s -> %s\n", m1->state_hash, m2->state_hash);
    } else {
        printf("  Version not found\n");
    }
}

void tcrystal_stabilize(Timeline* tl) {
    if (!tl) return;
    tl->temporal_stability += 0.05;
    if (tl->temporal_stability > 1.0) tl->temporal_stability = 1.0;
    printf("[TCRYSTAL] Timeline '%s' stability increased to %.2f\n", tl->name, tl->temporal_stability);
}

void tcrystal_show_timelines(void) {
    printf("=== Timelines ===\n");
    printf("%-6s %-20s %-8s %-8s %-10s %s\n", "ID", "Name", "Moments", "Version", "Stability", "Branched");
    for (int i = 0; i < tcdb.timeline_count; i++) {
        Timeline* tl = &tcdb.timelines[i];
        printf("%-6s %-20s %-8d %-8d %-10.2f %s\n",
               tl->id, tl->name, tl->moment_count, tl->current_version,
               tl->temporal_stability, tl->branched ? "YES" : "NO");
    }
}

void tcrystal_show_timeline(Timeline* tl) {
    if (!tl) return;
    printf("=== Timeline '%s' ===\n", tl->name);
    printf("  ID: %s | Version: %d | Moments: %d | Stability: %.2f\n",
           tl->id, tl->current_version, tl->moment_count, tl->temporal_stability);
    printf("  Moments:\n");
    for (int i = 0; i < tl->moment_count; i++) {
        TimeCrystalMoment* m = &tl->moments[i];
        printf("    v%d [%s] '%s' entropy=%.4f\n", m->version, m->state_hash, m->data, m->entropy);
    }
}

void tcrystal_show_realities(void) {
    printf("=== Parallel Realities ===\n");
    printf("%-6s %-24s %-8s %-10s %s\n", "ID", "Name", "Diverg", "Prob", "Data");
    for (int i = 0; i < tcdb.reality_count; i++) {
        ParallelReality* pr = &tcdb.parallel_realities[i];
        printf("%-6s %-24s %-8.2f %-10.2f %s\n",
               pr->id, pr->name, pr->divergence_point, pr->probability, pr->alternate_data);
    }
}

void tcrystal_show_coherence(void) {
    double total_stability = 0.0;
    for (int i = 0; i < tcdb.timeline_count; i++) {
        total_stability += tcdb.timelines[i].temporal_stability;
    }
    tcdb.temporal_coherence = tcdb.timeline_count > 0 ? total_stability / tcdb.timeline_count : 0.0;
    printf("=== Temporal Coherence ===\n");
    printf("  Timelines: %d\n", tcdb.timeline_count);
    printf("  Realities: %d\n", tcdb.reality_count);
    printf("  Total Moments: %d\n", tcdb.total_moments);
    printf("  Coherence: %.4f\n", tcdb.temporal_coherence);
    printf("  Chrono-Locked: %s\n", tcdb.chrono_locked ? "YES" : "NO");
    printf("  Auto-Version: %s\n", tcdb.auto_version ? "ON" : "OFF");
}
