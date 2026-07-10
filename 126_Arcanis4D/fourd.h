#ifndef FOURD_H
#define FOURD_H

#include <stddef.h>

typedef enum {
    TIMELINE_LINEAR,
    TIMELINE_BRANCHING,
    TIMELINE_CYCLIC,
    TIMELINE_PARALLEL
} TimeDimension;

typedef struct {
    char id[32];
    char name[64];
    double timestamp;
    double duration;
    TimeDimension dimension;
    char data[1024];
    char causality[8][32];
} TemporalEvent;

typedef struct {
    char id[32];
    char name[64];
    double spatial_pos[3];
    double temporal_pos;
    double temporal_velocity;
    double mass;
    TemporalEvent events[16];
    int event_count;
} FourDObject;

typedef struct {
    char id[32];
    char name[64];
    double field_strength;
    double curvature;
    TimeDimension dimension;
    FourDObject objects[16];
} TimeField;

typedef struct {
    TimeField fields[8];
    int object_count;
    int event_count;
    double temporal_coherence;
    double entropy;
    int time_crystals_active;
    int paradox_count;
} FourDEngine;

void fourd_init(FourdEngine *engine);
int fourd_create_field(FourdEngine *engine, const char *id, const char *name, TimeDimension dim);
int fourd_create_object(FourdEngine *engine, const char *id, const char *name);
int fourd_add_event(FourdEngine *engine, int field_idx, int obj_idx, TemporalEvent event);
int fourd_travel(FourdEngine *engine, int obj_idx, double delta_time);
int fourd_detect_paradox(FourdEngine *engine);
int fourd_resolve_paradox(FourdEngine *engine);
void fourd_show_fields(FourdEngine *engine);
void fourd_show_objects(FourdEngine *engine);
void fourd_show_timeline(FourdEngine *engine);
void fourd_show_stats(FourdEngine *engine);

#endif /* FOURD_H */
