#include "portal.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
    int object_id;
    char object_type[32];
    char source_layer[32];
    char target_layer[32];
    float transition_progress;
    int synced;
} PortalObject;

typedef struct {
    int portal_id;
    char source_layer[32];
    char target_layer[32];
    float stability;
    int object_count;
    PortalObject objects[12];
    int active;
} Portal;

typedef struct {
    Portal portals[10];
    int portal_count;
    int total_objects;
} RealityBridge;

static RealityBridge rb;

void portal_init(void) {
    rb.portal_count = 0;
    rb.total_objects = 0;
    srand((unsigned)time(NULL));
}

void portal_create(const char *src, const char *tgt) {
    if (rb.portal_count >= 10) return;
    Portal *p = &rb.portals[rb.portal_count++];
    p->portal_id = rb.portal_count;
    snprintf(p->source_layer, sizeof(p->source_layer), "%s", src);
    snprintf(p->target_layer, sizeof(p->target_layer), "%s", tgt);
    p->stability = 0.95f;
    p->object_count = 0;
    p->active = 1;
    printf("Portal #%d: %s <-> %s (stability=%.2f)\n", p->portal_id, src, tgt, p->stability);
}

void portal_send_object(int portal_id, const char *type, const char *src, const char *tgt) {
    for (int i = 0; i < rb.portal_count; i++) {
        if (rb.portals[i].portal_id == portal_id && rb.portals[i].object_count < 12) {
            PortalObject *o = &rb.portals[i].objects[rb.portals[i].object_count++];
            o->object_id = ++rb.total_objects;
            snprintf(o->object_type, sizeof(o->object_type), "%s", type);
            snprintf(o->source_layer, sizeof(o->source_layer), "%s", src);
            snprintf(o->target_layer, sizeof(o->target_layer), "%s", tgt);
            o->transition_progress = (float)rand() / RAND_MAX;
            o->synced = 0;
            printf("Object #%d (%s) entering portal #%d (progress=%.2f)\n",
                   o->object_id, type, portal_id, o->transition_progress);
            return;
        }
    }
}

void portal_sync(int portal_id) {
    for (int i = 0; i < rb.portal_count; i++) {
        if (rb.portals[i].portal_id == portal_id) {
            for (int j = 0; j < rb.portals[i].object_count; j++) {
                rb.portals[i].objects[j].synced = 1;
            }
            printf("Portal #%d synced %d objects\n", portal_id, rb.portals[i].object_count);
            return;
        }
    }
}

void portal_bridge_realities(const char *r1, const char *r2) {
    portal_create(r1, r2);
    printf("Bridge created between %s and %s\n", r1, r2);
}

void portal_collapse_to_single(const char *target_layer) {
    for (int i = 0; i < rb.portal_count; i++) {
        for (int j = 0; j < rb.portals[i].object_count; j++) {
            snprintf(rb.portals[i].objects[j].target_layer,
                     sizeof(rb.portals[i].objects[j].target_layer), "%s", target_layer);
            rb.portals[i].objects[j].transition_progress = 1.0f;
        }
    }
    printf("All objects collapsed to %s\n", target_layer);
}

void portal_show_portals(void) {
    printf("\n%-4s %-16s %-16s %-10s %-6s %s\n",
           "ID", "Source", "Target", "Stability", "Objs", "Active");
    printf("----------------------------------------------------------\n");
    for (int i = 0; i < rb.portal_count; i++) {
        printf("%-4d %-16s %-16s %-10.2f %-6d %s\n",
               rb.portals[i].portal_id,
               rb.portals[i].source_layer, rb.portals[i].target_layer,
               rb.portals[i].stability, rb.portals[i].object_count,
               rb.portals[i].active ? "yes" : "no");
    }
}

void portal_show_objects(int portal_id) {
    for (int i = 0; i < rb.portal_count; i++) {
        if (rb.portals[i].portal_id == portal_id) {
            printf("\nObjects in Portal #%d:\n", portal_id);
            printf("%-4s %-16s %-16s %-16s %-6s %s\n",
                   "ID", "Type", "Source", "Target", "Prog", "Sync");
            printf("----------------------------------------------------------\n");
            for (int j = 0; j < rb.portals[i].object_count; j++) {
                printf("%-4d %-16s %-16s %-16s %-6.2f %s\n",
                       rb.portals[i].objects[j].object_id,
                       rb.portals[i].objects[j].object_type,
                       rb.portals[i].objects[j].source_layer,
                       rb.portals[i].objects[j].target_layer,
                       rb.portals[i].objects[j].transition_progress,
                       rb.portals[i].objects[j].synced ? "yes" : "no");
            }
            return;
        }
    }
}

void portal_show_bridge(void) {
    printf("\n=== Reality Bridge ===\n");
    printf("%-20s %d\n", "Total Portals", rb.portal_count);
    printf("%-20s %d\n", "Total Objects", rb.total_objects);
}
