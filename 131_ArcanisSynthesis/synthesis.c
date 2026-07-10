#include "synthesis.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#define MAX_SCENES 10
#define MAX_VOXELS 64
#define MAX_RULES 10

typedef struct {
    int x, y, z;
    char material[32];
    double density;
    int color_r, color_g, color_b;
    double velocity_x, velocity_y, velocity_z;
} Voxel;

typedef struct {
    char name[48];
    char rule_pattern[64];
    char effect[64];
    int active;
} PhysicsRule;

typedef struct {
    char id[32];
    char name[48];
    Voxel voxels[MAX_VOXELS];
    int voxel_count;
    double gravity;
    double temperature;
} SynthesizedScene;

typedef struct {
    SynthesizedScene scenes[MAX_SCENES];
    int scene_count;
    PhysicsRule rules[MAX_RULES];
    int rule_count;
} RealitySynthesizer;

static RealitySynthesizer rs;

static const char *materials[] = {"stone", "water", "wood", "metal", "glass", "air", "fire", "earth"};

void synth_init(void) {
    srand(time(NULL));
    memset(&rs, 0, sizeof(rs));
    rs.rule_count = 4;
    strncpy(rs.rules[0].name, "gravity", 48);
    strncpy(rs.rules[0].rule_pattern, "gravity:*", 64);
    strncpy(rs.rules[0].effect, "apply_gravity", 64);
    rs.rules[0].active = 1;
    strncpy(rs.rules[1].name, "collision", 48);
    strncpy(rs.rules[1].rule_pattern, "collision:*", 64);
    strncpy(rs.rules[1].effect, "resolve_collision", 64);
    rs.rules[1].active = 1;
    strncpy(rs.rules[2].name, "buoyancy", 48);
    strncpy(rs.rules[2].rule_pattern, "buoyancy:*", 64);
    strncpy(rs.rules[2].effect, "apply_buoyancy", 64);
    rs.rules[2].active = 1;
    strncpy(rs.rules[3].name, "temperature", 48);
    strncpy(rs.rules[3].rule_pattern, "temperature:*", 64);
    strncpy(rs.rules[3].effect, "thermal_expand", 64);
    rs.rules[3].active = 1;
    printf("[SYNTH] Reality synthesizer initialized with %d physics rules\n", rs.rule_count);
}

void synth_generate_scene(const char *name) {
    if (rs.scene_count >= MAX_SCENES) { printf("[SYNTH] Scene limit reached\n"); return; }
    SynthesizedScene *s = &rs.scenes[rs.scene_count++];
    snprintf(s->id, sizeof(s->id), "SCN-%03d", rs.scene_count);
    strncpy(s->name, name, sizeof(s->name) - 1);
    s->voxel_count = 0;
    s->gravity = 9.81;
    s->temperature = 20.0 + (rand() % 300) / 10.0;
    for (int i = 0; i < 8; i++) {
        Voxel *v = &s->voxels[s->voxel_count++];
        v->x = rand() % 10;
        v->y = rand() % 10;
        v->z = rand() % 10;
        strncpy(v->material, materials[rand() % 8], sizeof(v->material) - 1);
        v->density = (rand() % 1000) / 100.0 + 0.1;
        v->color_r = rand() % 256;
        v->color_g = rand() % 256;
        v->color_b = rand() % 256;
        v->velocity_x = v->velocity_y = v->velocity_z = 0.0;
    }
    printf("[SYNTH] Generated scene '%s' (%s) with %d voxels, %.1fK\n", s->name, s->id, s->voxel_count, s->temperature);
}

void synth_add_voxel(const char *scene_id, int x, int y, int z, const char *material) {
    for (int i = 0; i < rs.scene_count; i++) {
        if (strcmp(rs.scenes[i].id, scene_id) == 0) {
            if (rs.scenes[i].voxel_count >= MAX_VOXELS) { printf("[SYNTH] Voxel limit\n"); return; }
            Voxel *v = &rs.scenes[i].voxels[rs.scenes[i].voxel_count++];
            v->x = x; v->y = y; v->z = z;
            strncpy(v->material, material, sizeof(v->material) - 1);
            v->density = (rand() % 1000) / 100.0 + 0.1;
            v->color_r = rand() % 256;
            v->color_g = rand() % 256;
            v->color_b = rand() % 256;
            printf("[SYNTH] Added voxel (%d,%d,%d) of %s to %s\n", x, y, z, material, scene_id);
            return;
        }
    }
    printf("[SYNTH] Scene %s not found\n", scene_id);
}

void synth_apply_rule(const char *rule_name, const char *scene_id) {
    for (int i = 0; i < rs.rule_count; i++) {
        if (strcmp(rs.rules[i].name, rule_name) == 0) {
            printf("[SYNTH] Applying rule '%s' -> %s on %s\n", rule_name, rs.rules[i].effect, scene_id);
            for (int j = 0; j < rs.scene_count; j++) {
                if (strcmp(rs.scenes[j].id, scene_id) == 0) {
                    if (strcmp(rule_name, "gravity") == 0) {
                        for (int k = 0; k < rs.scenes[j].voxel_count; k++) {
                            rs.scenes[j].voxels[k].velocity_y -= rs.scenes[j].gravity * 0.01;
                        }
                        printf("[SYNTH] Gravity applied to %d voxels\n", rs.scenes[j].voxel_count);
                    }
                    return;
                }
            }
            return;
        }
    }
    printf("[SYNTH] Rule '%s' not found\n", rule_name);
}

void synth_physics_simulate(const char *scene_id) {
    for (int i = 0; i < rs.scene_count; i++) {
        if (strcmp(rs.scenes[i].id, scene_id) == 0) {
            printf("\n=== PHYSICS SIMULATION: %s ===\n", rs.scenes[i].name);
            printf("Gravity: %.2f m/s^2, Temperature: %.1f K\n", rs.scenes[i].gravity, rs.scenes[i].temperature);
            for (int j = 0; j < rs.scenes[i].voxel_count; j++) {
                Voxel *v = &rs.scenes[i].voxels[j];
                v->velocity_y -= rs.scenes[i].gravity * 0.016;
                printf("Voxel[%d] (%d,%d,%d) %s: vel=(%.2f,%.2f,%.2f)\n",
                       j, v->x, v->y, v->z, v->material,
                       v->velocity_x, v->velocity_y, v->velocity_z);
            }
            return;
        }
    }
    printf("[SYNTH] Scene %s not found\n", scene_id);
}

void synth_texture(const char *scene_id) {
    for (int i = 0; i < rs.scene_count; i++) {
        if (strcmp(rs.scenes[i].id, scene_id) == 0) {
            printf("[SYNTH] Texturing scene '%s'\n", rs.scenes[i].name);
            for (int j = 0; j < rs.scenes[i].voxel_count; j++) {
                rs.scenes[i].voxels[j].color_r = rand() % 256;
                rs.scenes[i].voxels[j].color_g = rand() % 256;
                rs.scenes[i].voxels[j].color_b = rand() % 256;
            }
            printf("[SYNTH] Assigned random colors to %d voxels\n", rs.scenes[i].voxel_count);
            return;
        }
    }
    printf("[SYNTH] Scene %s not found\n", scene_id);
}

void synth_show_scenes(void) {
    printf("\n=== SYNTHESIZED SCENES ===\n");
    printf("%-10s %-25s %-10s %-10s %-10s\n", "ID", "Name", "Voxels", "Gravity", "Temp(K)");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < rs.scene_count; i++)
        printf("%-10s %-25s %-10d %-10.2f %-10.1f\n",
               rs.scenes[i].id, rs.scenes[i].name,
               rs.scenes[i].voxel_count, rs.scenes[i].gravity, rs.scenes[i].temperature);
}

void synth_show_scene(const char *scene_id) {
    for (int i = 0; i < rs.scene_count; i++) {
        if (strcmp(rs.scenes[i].id, scene_id) == 0) {
            printf("\n=== SCENE: %s ===\n", rs.scenes[i].name);
            printf("%-5s %-5s %-5s %-12s %-8s %-18s\n", "X", "Y", "Z", "Material", "Density", "Color (R,G,B)");
            printf("------------------------------------------------------------\n");
            for (int j = 0; j < rs.scenes[i].voxel_count; j++)
                printf("%-5d %-5d %-5d %-12s %-8.2f (%3d,%3d,%3d)\n",
                       rs.scenes[i].voxels[j].x, rs.scenes[i].voxels[j].y,
                       rs.scenes[i].voxels[j].z, rs.scenes[i].voxels[j].material,
                       rs.scenes[i].voxels[j].density,
                       rs.scenes[i].voxels[j].color_r, rs.scenes[i].voxels[j].color_g,
                       rs.scenes[i].voxels[j].color_b);
            return;
        }
    }
    printf("[SYNTH] Scene %s not found\n", scene_id);
}

void synth_show_rules(void) {
    printf("\n=== PHYSICS RULES ===\n");
    printf("%-20s %-25s %-20s %-8s\n", "Name", "Pattern", "Effect", "Active");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < rs.rule_count; i++)
        printf("%-20s %-25s %-20s %-8s\n",
               rs.rules[i].name, rs.rules[i].rule_pattern,
               rs.rules[i].effect, rs.rules[i].active ? "yes" : "no");
}
