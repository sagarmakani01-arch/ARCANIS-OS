/**
 * arvr.c — AR/VR Framework Implementation
 */
#include <arcanis/arvr.h>
#include <arcanis/string.h>
#include <stdio.h>
#include <string.h>

static arvr_scene_t* find_scene(arvr_system_t* sys, const char* name) {
    for (uint32_t i = 0; i < sys->num_scenes; i++)
        if (string_compare(sys->scenes[i].name, name) == 0) return &sys->scenes[i];
    return NULL;
}

static arvr_object_t* find_object(arvr_scene_t* scene, const char* name) {
    for (uint32_t i = 0; i < scene->num_objects; i++)
        if (string_compare(scene->objects[i].name, name) == 0) return &scene->objects[i];
    return NULL;
}

void arvr_init(arvr_system_t* sys) {
    if (!sys) return;
    memset(sys, 0, sizeof(arvr_system_t));
    sys->avg_fps = 90.0;
    sys->rendering = 0;
    printf("[AR/VR] Framework initialized\n");
}

int arvr_create_scene(arvr_system_t* sys, const char* name) {
    if (!sys || !name) return -1;
    if (sys->num_scenes >= ARVR_MAX_SCENES) return -1;
    arvr_scene_t* s = &sys->scenes[sys->num_scenes];
    memset(s, 0, sizeof(arvr_scene_t));
    string_copy(s->name, name, ARVR_MAX_NAME);
    s->fps = 90;
    s->active = 1;
    s->ambient_light = (arvr_color_t){0.2, 0.2, 0.2, 1.0};
    sys->num_scenes++;
    printf("[AR/VR] Scene '%s' created\n", name);
    return 0;
}

int arvr_set_active_scene(arvr_system_t* sys, const char* name) {
    for (uint32_t i = 0; i < sys->num_scenes; i++)
        if (string_compare(sys->scenes[i].name, name) == 0) {
            sys->active_scene = i;
            return 0;
        }
    return -1;
}

int arvr_add_object(arvr_system_t* sys, const char* scene_name,
                    const char* obj_name, arvr_mesh_type_t mesh) {
    if (!sys || !scene_name || !obj_name) return -1;
    arvr_scene_t* s = find_scene(sys, scene_name);
    if (!s || s->num_objects >= ARVR_MAX_OBJECTS) return -1;
    arvr_object_t* o = &s->objects[s->num_objects];
    memset(o, 0, sizeof(arvr_object_t));
    string_copy(o->name, obj_name, ARVR_MAX_NAME);
    o->mesh_type = mesh;
    o->transform = (arvr_transform_t){{0,0,0},{1,0,0,0},{1,1,1}};
    o->color = (arvr_color_t){1,1,1,1};
    o->visible = 1;
    o->vertex_count = mesh <= ARVR_MESH_CYLINDER ? 36 : 1024;
    o->triangle_count = mesh <= ARVR_MESH_CYLINDER ? 12 : 512;
    s->num_objects++;
    return 0;
}

int arvr_set_transform(arvr_system_t* sys, const char* scene_name,
                       const char* obj_name, arvr_transform_t t) {
    arvr_scene_t* s = find_scene(sys, scene_name);
    if (!s) return -1;
    arvr_object_t* o = find_object(s, obj_name);
    if (!o) return -1;
    o->transform = t;
    return 0;
}

int arvr_list_objects(arvr_system_t* sys, const char* scene_name,
                      char* buf, uint32_t buf_len) {
    if (!sys || !scene_name || !buf) return 0;
    arvr_scene_t* s = find_scene(sys, scene_name);
    if (!s) return 0;
    uint32_t pos = 0;
    const char* meshes[] = {"cube", "sphere", "plane", "cylinder", "custom"};
    pos += snprintf(buf + pos, buf_len - pos, "SCENE: %s (%u objects)\n", scene_name, s->num_objects);
    pos += snprintf(buf + pos, buf_len - pos, "NAME             MESH     VISIBLE  VERTS  TRIS\n");
    for (uint32_t i = 0; i < s->num_objects && pos < buf_len - 100; i++) {
        arvr_object_t* o = &s->objects[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-16s %-8s %-8s %5llu %5llu\n",
            o->name, meshes[o->mesh_type], o->visible ? "yes" : "no",
            (unsigned long long)o->vertex_count, (unsigned long long)o->triangle_count);
    }
    return (int)pos;
}

int arvr_connect_hmd(arvr_system_t* sys, arvr_hmd_type_t type) {
    if (!sys || sys->num_hmds >= ARVR_MAX_HMD) return -1;
    arvr_hmd_t* hmd = &sys->hmds[sys->num_hmds];
    memset(hmd, 0, sizeof(arvr_hmd_t));
    hmd->type = type;
    hmd->connected = 1;
    hmd->tracking = 1;
    hmd->fps = 90;
    hmd->latency_ms = 12;
    hmd->battery = 85;
    const char* names[] = {"", "Meta Quest 3", "Valve Index", "Apple Vision Pro", "Pico 4"};
    string_copy(hmd->name, names[type], 32);
    hmd->resolution_w = 2064;
    hmd->resolution_h = 2208;
    hmd->field_of_view = 110;
    sys->num_hmds++;
    printf("[AR/VR] HMD connected: %s\n", hmd->name);
    return 0;
}

int arvr_get_hmd_status(arvr_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t pos = 0;
    for (uint32_t i = 0; i < sys->num_hmds && pos < buf_len - 200; i++) {
        arvr_hmd_t* h = &sys->hmds[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "HMD: %s\n  Connected: %s\n  Tracking: %s\n"
            "  Resolution: %.0fx%.0f\n  FOV: %.1f deg\n"
            "  FPS: %.1f  Latency: %.1f ms  Battery: %.0f%%\n",
            h->name, h->connected ? "yes" : "no", h->tracking ? "yes" : "no",
            h->resolution_w, h->resolution_h, h->field_of_view,
            h->fps, h->latency_ms, h->battery);
    }
    return (int)pos;
}

int arvr_render_frame(arvr_system_t* sys) {
    if (!sys) return -1;
    sys->total_frames++;
    sys->avg_fps = sys->avg_fps * 0.95 + 90.0 * 0.05;
    return 0;
}

int arvr_get_info(arvr_system_t* sys, char* buf, uint32_t buf_len) {
    if (!sys || !buf) return 0;
    uint32_t obj_count = 0;
    for (uint32_t i = 0; i < sys->num_scenes; i++)
        obj_count += sys->scenes[i].num_objects;
    return snprintf(buf, buf_len,
        "AR/VR System:\n"
        "  Scenes: %u\n"
        "  Objects: %u\n"
        "  HMDs: %u\n"
        "  Avg FPS: %.1f\n"
        "  Total Frames: %llu\n"
        "  Passthrough: %s\n",
        sys->num_scenes, obj_count, sys->num_hmds,
        sys->avg_fps, (unsigned long long)sys->total_frames,
        sys->passthrough ? "ON" : "OFF");
}
