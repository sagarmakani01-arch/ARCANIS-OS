#include "reality.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static RealityEngine re;

void reality_init(void) {
    memset(&re, 0, sizeof(re));
    re.active_layer = REALITY_PHYSICAL;
    re.reality_blend = 0.0;
    re.fps = 60.0;
    srand((unsigned)time(NULL));

    reality_create_scene("Physical World", REALITY_PHYSICAL, ANCHOR_STATIC);
    reality_create_scene("AR Overlay", REALITY_AUGMENTED, ANCHOR_DYNAMIC);
    reality_create_scene("VR Environment", REALITY_VIRTUAL, ANCHOR_VOLATILE);
    reality_create_scene("Simulation", REALITY_SIMULATED, ANCHOR_PERSISTENT);

    for (int i = 0; i < re.layer_count; i++) {
        re.visible_layers[i] = re.scenes[i].layer;
    }
    printf("[REALITY] Engine initialized with %d layers\n", re.scene_count);
}

RealityScene* reality_create_scene(const char* name, RealityLayer layer, AnchorType anchor) {
    if (re.scene_count >= 32) return NULL;
    RealityScene* s = &re.scenes[re.scene_count++];
    snprintf(s->id, sizeof(s->id), "SCN-%d", re.scene_count);
    snprintf(s->name, sizeof(s->name), "%s", name);
    s->layer = layer;
    s->anchor_type = anchor;
    s->object_count = 0;
    s->environment_lighting = 1.0;
    s->active = 1;
    snprintf(s->environment_map, sizeof(s->environment_map), "default_env");
    memset(&s->origin, 0, sizeof(s->origin));
    re.layer_count = re.scene_count;
    printf("[REALITY] Created scene '%s' (id=%s, layer=%d)\n", name, s->id, layer);
    return s;
}

RealityObject* reality_add_object(RealityScene* scene, const char* name, RealityLayer layer) {
    if (!scene || scene->object_count >= 64) return NULL;
    RealityObject* o = &scene->objects[scene->object_count++];
    snprintf(o->id, sizeof(o->id), "OBJ-%d", scene->object_count);
    snprintf(o->name, sizeof(o->name), "%s", name);
    o->layer = layer;
    memset(&o->transform, 0, sizeof(o->transform));
    o->transform.scale = 1.0;
    snprintf(o->material, sizeof(o->material), "default");
    o->interactive = 1;
    o->physics_enabled = 1;
    o->visible = 1;
    printf("[REALITY] Added object '%s' to scene '%s'\n", name, scene->name);
    return o;
}

void reality_set_transform(RealityObject* obj, double x, double y, double z) {
    if (!obj) return;
    obj->transform.x = x;
    obj->transform.y = y;
    obj->transform.z = z;
}

void reality_set_layer_active(RealityLayer layer, int active) {
    for (int i = 0; i < re.scene_count; i++) {
        if (re.scenes[i].layer == layer) {
            re.scenes[i].active = active;
        }
    }
    printf("[REALITY] Layer %d set to %s\n", layer, active ? "active" : "inactive");
}

void reality_blend_layers(RealityLayer a, RealityLayer b, double blend) {
    re.reality_blend = blend;
    printf("[REALITY] Blend between layer %d and %d set to %.2f\n", a, b, blend);
}

void reality_sync_cross_layer(RealityObject* obj, RealityLayer target) {
    if (!obj) return;
    re.cross_layer_sync++;
    printf("[REALITY] Cross-layer sync #%d: object '%s' -> layer %d\n", re.cross_layer_sync, obj->name, target);
}

void reality_show_scene(const char* name) {
    for (int i = 0; i < re.scene_count; i++) {
        if (strcmp(re.scenes[i].name, name) == 0) {
            RealityScene* s = &re.scenes[i];
            printf("=== Scene: %s ===\n", s->name);
            printf("  ID: %s\n", s->id);
            printf("  Layer: %d\n", s->layer);
            printf("  Anchor: %d\n", s->anchor_type);
            printf("  Objects: %d\n", s->object_count);
            printf("  Active: %d\n", s->active);
            printf("  Lighting: %.2f\n", s->environment_lighting);
            return;
        }
    }
    printf("[REALITY] Scene '%s' not found\n", name);
}

void reality_show_layers(void) {
    printf("=== Reality Layers ===\n");
    for (int i = 0; i < re.scene_count; i++) {
        const char* names[] = {"PHYSICAL", "AUGMENTED", "VIRTUAL", "SIMULATED", "MIXED"};
        printf("  Layer %d (%s): %s\n", re.scenes[i].layer,
               re.scenes[i].layer < 5 ? names[re.scenes[i].layer] : "UNKNOWN",
               re.scenes[i].active ? "ACTIVE" : "INACTIVE");
    }
    printf("  Reality Blend: %.2f\n", re.reality_blend);
}

void reality_show_objects(RealityScene* scene) {
    if (!scene) return;
    printf("=== Objects in '%s' ===\n", scene->name);
    for (int i = 0; i < scene->object_count; i++) {
        RealityObject* o = &scene->objects[i];
        printf("  [%s] %s (%.1f,%.1f,%.1f) visible=%d\n",
               o->id, o->name, o->transform.x, o->transform.y, o->transform.z, o->visible);
    }
}

void reality_frame_update(void) {
    re.frame_count++;
    re.fps = 60.0 + (rand() % 100) / 10.0 - 5.0;
    printf("[REALITY] Frame %d updated (FPS: %.1f)\n", re.frame_count, re.fps);
}
