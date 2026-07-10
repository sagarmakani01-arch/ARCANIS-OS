/**
 * arvr.h — AR/VR Framework
 *
 * 3D rendering, scene management, spatial tracking, mixed reality.
 */
#ifndef ARCANIS_ARVR_H
#define ARCANIS_ARVR_H

#include <arcanis/types.h>

#define ARVR_MAX_OBJECTS    2048
#define ARVR_MAX_SCENES     64
#define ARVR_MAX_NAME        64
#define ARVR_MAX_HMD         16

typedef struct { double x, y, z; } arvr_vec3_t;
typedef struct { double w, x, y, z; } arvr_quat_t;
typedef struct { double r, g, b, a; } arvr_color_t;

typedef struct {
    arvr_vec3_t position;
    arvr_quat_t rotation;
    arvr_vec3_t scale;
} arvr_transform_t;

typedef enum {
    ARVR_MESH_CUBE,
    ARVR_MESH_SPHERE,
    ARVR_MESH_PLANE,
    ARVR_MESH_CYLINDER,
    ARVR_MESH_CUSTOM
} arvr_mesh_type_t;

typedef struct {
    char name[ARVR_MAX_NAME];
    arvr_mesh_type_t mesh_type;
    arvr_transform_t transform;
    arvr_color_t color;
    char texture[128];
    int visible;
    int is_light;
    uint64_t vertex_count;
    uint64_t triangle_count;
} arvr_object_t;

typedef struct {
    char name[ARVR_MAX_NAME];
    arvr_object_t objects[ARVR_MAX_OBJECTS];
    uint32_t num_objects;
    arvr_color_t ambient_light;
    arvr_vec3_t gravity;
    uint32_t fps;
    int active;
} arvr_scene_t;

typedef enum {
    ARVR_HMD_NONE,
    ARVR_HMD_META,
    ARVR_HMD_VALVE,
    ARVR_HMD_APPLE,
    ARVR_HMD_PICO
} arvr_hmd_type_t;

typedef struct {
    arvr_hmd_type_t type;
    char name[32];
    int connected;
    int tracking;
    double fps;
    double resolution_w;
    double resolution_h;
    double field_of_view;
    double latency_ms;
    double battery;
    arvr_vec3_t position;
    arvr_quat_t orientation;
} arvr_hmd_t;

typedef enum {
    ARVR_TRACK_HAND,
    ARVR_TRACK_EYE,
    ARVR_TRACK_BODY,
    ARVR_TRACK_CONTROLLER
} arvr_track_type_t;

typedef struct {
    arvr_track_type_t type;
    int detected;
    arvr_vec3_t position;
    arvr_quat_t rotation;
    double confidence;
} arvr_tracker_t;

typedef struct {
    arvr_scene_t scenes[ARVR_MAX_SCENES];
    uint32_t num_scenes;
    uint32_t active_scene;

    arvr_hmd_t hmds[ARVR_MAX_HMD];
    uint32_t num_hmds;

    arvr_tracker_t hand_trackers[2];
    arvr_tracker_t eye_tracker;
    arvr_tracker_t body_tracker;

    uint64_t total_frames;
    double avg_fps;
    int rendering;
    int passthrough;
} arvr_system_t;

void arvr_init(arvr_system_t* sys);

int  arvr_create_scene(arvr_system_t* sys, const char* name);
int  arvr_set_active_scene(arvr_system_t* sys, const char* name);

int  arvr_add_object(arvr_system_t* sys, const char* scene_name,
                     const char* obj_name, arvr_mesh_type_t mesh);
int  arvr_set_transform(arvr_system_t* sys, const char* scene_name,
                        const char* obj_name, arvr_transform_t t);
int  arvr_list_objects(arvr_system_t* sys, const char* scene_name,
                       char* buf, uint32_t buf_len);

int  arvr_connect_hmd(arvr_system_t* sys, arvr_hmd_type_t type);
int  arvr_get_hmd_status(arvr_system_t* sys, char* buf, uint32_t buf_len);

int  arvr_render_frame(arvr_system_t* sys);
int  arvr_get_info(arvr_system_t* sys, char* buf, uint32_t buf_len);

#endif
