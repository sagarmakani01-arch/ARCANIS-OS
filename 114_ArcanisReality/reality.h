#ifndef ARCANIS_REALITY_H
#define ARCANIS_REALITY_H

typedef enum {
    REALITY_PHYSICAL,
    REALITY_AUGMENTED,
    REALITY_VIRTUAL,
    REALITY_SIMULATED,
    REALITY_MIXED
} RealityLayer;

typedef enum {
    ANCHOR_STATIC,
    ANCHOR_DYNAMIC,
    ANCHOR_VOLATILE,
    ANCHOR_PERSISTENT
} AnchorType;

typedef struct {
    double x, y, z;
    double rx, ry, rz;
    double scale;
} SpatialTransform;

typedef struct {
    char id[32];
    char name[64];
    RealityLayer layer;
    SpatialTransform transform;
    char mesh_data[2048];
    char material[64];
    int interactive;
    int physics_enabled;
    int visible;
} RealityObject;

typedef struct {
    char id[32];
    char name[64];
    RealityLayer layer;
    AnchorType anchor_type;
    SpatialTransform origin;
    RealityObject objects[64];
    int object_count;
    double environment_lighting;
    char environment_map[64];
    int active;
} RealityScene;

typedef struct {
    RealityScene scenes[32];
    int scene_count;
    RealityLayer active_layer;
    RealityLayer visible_layers[8];
    int layer_count;
    double reality_blend;
    int frame_count;
    double fps;
    int cross_layer_sync;
} RealityEngine;

void reality_init(void);
RealityScene* reality_create_scene(const char* name, RealityLayer layer, AnchorType anchor);
RealityObject* reality_add_object(RealityScene* scene, const char* name, RealityLayer layer);
void reality_set_transform(RealityObject* obj, double x, double y, double z);
void reality_set_layer_active(RealityLayer layer, int active);
void reality_blend_layers(RealityLayer a, RealityLayer b, double blend);
void reality_sync_cross_layer(RealityObject* obj, RealityLayer target);
void reality_show_scene(const char* name);
void reality_show_layers(void);
void reality_show_objects(RealityScene* scene);
void reality_frame_update(void);

#endif
