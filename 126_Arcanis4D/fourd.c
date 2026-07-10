#include "fourd.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#define MAX_FIELDS 10
#define MAX_OBJECTS 30
#define MAX_EVENTS 20

typedef struct {
    int year;
    int month;
    int day;
    double temporal_phase;
} TimeCoordinate;

typedef struct {
    char name[48];
    int dimension;
    double curvature;
    TimeCoordinate origin;
} TimeField;

typedef struct {
    char id[32];
    char name[48];
    char field_name[48];
    TimeCoordinate temporal_pos;
    int event_count;
    char events[MAX_EVENTS][64];
} FourDObject;

typedef struct {
    TimeField fields[MAX_FIELDS];
    int field_count;
    FourDObject objects[MAX_OBJECTS];
    int object_count;
    int paradox_count;
    int resolutions;
    int total_events;
} FourDEngine;

static FourDEngine fde;

void fourd_init(void) {
    srand(time(NULL));
    memset(&fde, 0, sizeof(fde));
    fde.field_count = 2;
    strncpy(fde.fields[0].name, "spacetime-continuum", sizeof(fde.fields[0].name) - 1);
    fde.fields[0].dimension = 4;
    fde.fields[0].curvature = 0.01;
    fde.fields[0].origin.year = 2026;
    strncpy(fde.fields[1].name, "temporal-plane", sizeof(fde.fields[1].name) - 1);
    fde.fields[1].dimension = 5;
    fde.fields[1].curvature = 0.05;
    fde.fields[1].origin.year = 2026;
    printf("[4D] Engine initialized with %d time fields\n", fde.field_count);
}

void fourd_create_field(const char *name, int dimension) {
    if (fde.field_count >= MAX_FIELDS) { printf("[4D] Field limit reached\n"); return; }
    TimeField *f = &fde.fields[fde.field_count++];
    strncpy(f->name, name, sizeof(f->name) - 1);
    f->dimension = dimension;
    f->curvature = (rand() % 100) / 100.0;
    f->origin.year = 2026;
    printf("[4D] Created field '%s' (dim: %d, curvature: %.2f)\n", f->name, f->dimension, f->curvature);
}

void fourd_create_object(const char *name, const char *field_name) {
    if (fde.object_count >= MAX_OBJECTS) { printf("[4D] Object limit reached\n"); return; }
    FourDObject *o = &fde.objects[fde.object_count++];
    snprintf(o->id, sizeof(o->id), "4DO-%03d", fde.object_count);
    strncpy(o->name, name, sizeof(o->name) - 1);
    strncpy(o->field_name, field_name, sizeof(o->field_name) - 1);
    o->temporal_pos.year = 2026 + (rand() % 100);
    o->temporal_pos.month = rand() % 12 + 1;
    o->temporal_pos.day = rand() % 28 + 1;
    o->temporal_pos.temporal_phase = (rand() % 1000) / 1000.0;
    o->event_count = 0;
    printf("[4D] Created object '%s' (%s) in field '%s' at %d-%02d-%02d\n",
           o->name, o->id, o->field_name, o->temporal_pos.year, o->temporal_pos.month, o->temporal_pos.day);
}

void fourd_add_event(const char *object_id, const char *event) {
    for (int i = 0; i < fde.object_count; i++) {
        if (strcmp(fde.objects[i].id, object_id) == 0) {
            if (fde.objects[i].event_count >= MAX_EVENTS) { printf("[4D] Event limit for object\n"); return; }
            strncpy(fde.objects[i].events[fde.objects[i].event_count++], event, 64);
            fde.total_events++;
            printf("[4D] Event added to %s: %s\n", object_id, event);
            return;
        }
    }
    printf("[4D] Object %s not found\n", object_id);
}

void fourd_travel(const char *object_id, int delta) {
    for (int i = 0; i < fde.object_count; i++) {
        if (strcmp(fde.objects[i].id, object_id) == 0) {
            fde.objects[i].temporal_pos.year += delta;
            printf("[4D] Object %s traveled %+d years to %d\n", object_id, delta, fde.objects[i].temporal_pos.year);
            return;
        }
    }
    printf("[4D] Object %s not found\n", object_id);
}

void fourd_detect_paradox(void) {
    int found = 0;
    for (int i = 0; i < fde.object_count; i++) {
        for (int j = i + 1; j < fde.object_count; j++) {
            if (strcmp(fde.objects[i].field_name, fde.objects[j].field_name) == 0 &&
                fde.objects[i].temporal_pos.year == fde.objects[j].temporal_pos.year &&
                fde.objects[i].event_count > 0 && fde.objects[j].event_count > 0) {
                found = 1;
                printf("[4D] PARADOX: %s and %s conflict at year %d\n",
                       fde.objects[i].name, fde.objects[j].name, fde.objects[i].temporal_pos.year);
            }
        }
    }
    if (found) fde.paradox_count++;
    else printf("[4D] No paradoxes detected\n");
}

void fourd_resolve_paradox(void) {
    if (fde.paradox_count <= 0) { printf("[4D] No paradoxes to resolve\n"); return; }
    fde.paradox_count--;
    fde.resolutions++;
    printf("[4D] Paradox resolved. Remaining: %d, Total resolutions: %d\n", fde.paradox_count, fde.resolutions);
}

void fourd_show_fields(void) {
    printf("\n=== TIME FIELDS ===\n");
    printf("%-25s %-8s %-12s %-10s\n", "Name", "Dim", "Curvature", "Origin");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < fde.field_count; i++)
        printf("%-25s %-8d %-12.2f %d\n",
               fde.fields[i].name, fde.fields[i].dimension,
               fde.fields[i].curvature, fde.fields[i].origin.year);
}

void fourd_show_objects(void) {
    printf("\n=== 4D OBJECTS ===\n");
    printf("%-10s %-20s %-20s %-12s %-8s\n", "ID", "Name", "Field", "Temporal Pos", "Events");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < fde.object_count; i++)
        printf("%-10s %-20s %-20s %d-%02d  %-8d\n",
               fde.objects[i].id, fde.objects[i].name, fde.objects[i].field_name,
               fde.objects[i].temporal_pos.year, fde.objects[i].temporal_pos.month,
               fde.objects[i].event_count);
}

void fourd_show_timeline(void) {
    printf("\n=== TIMELINE ===\n");
    for (int i = 0; i < fde.object_count; i++) {
        printf("[%d-%02d] %s: ", fde.objects[i].temporal_pos.year, fde.objects[i].temporal_pos.month, fde.objects[i].name);
        for (int j = 0; j < fde.objects[i].event_count; j++)
            printf("%s; ", fde.objects[i].events[j]);
        printf("\n");
    }
}

void fourd_show_stats(void) {
    printf("\n=== 4D STATS ===\n");
    printf("Fields: %d\n", fde.field_count);
    printf("Objects: %d\n", fde.object_count);
    printf("Total events: %d\n", fde.total_events);
    printf("Paradoxes detected: %d\n", fde.paradox_count);
    printf("Resolutions: %d\n", fde.resolutions);
}
