#ifndef SYNTHESIS_H
#define SYNTHESIS_H

#include <stddef.h>

typedef enum {
    MAT_STONE,
    MAT_WOOD,
    MAT_METAL,
    MAT_WATER,
    MAT_GLASS,
    MAT_ORGANIC,
    MAT_ENERGY,
    MAT_VOID
} VoxelMaterial;

typedef struct {
    int x, y, z;
    VoxelMaterial material;
    int color[3];
    double density;
    double opacity;
    double emissive;
} Voxel;

typedef struct {
    char id[32];
    char name[64];
    char description[256];
    Voxel voxels[1024];
    int voxel_count;
    int dimensions[3];
    double physical_properties[8];
    double lighting;
    double atmospheric;
    int generated;
} SynthesizedScene;

typedef struct {
    char id[32];
    char pattern[128];
    char rule_type[32];
    char parameters[256];
    int application_count;
} SynthesisRule;

typedef struct {
    SynthesizedScene scenes[8];
    int scene_count;
    SynthesisRule rules[16];
    int rule_count;
    int total_voxels_generated;
    double generation_time_ms;
    double procedural_detail_level;
    int physics_enabled;
    int auto_texture;
} RealitySynthesizer;

void synth_init(RealitySynthesizer *synth);
int synth_generate_scene(RealitySynthesizer *synth, const char *name, const char *description);
int synth_add_voxel(RealitySynthesizer *synth, int scene_idx, int x, int y, int z, VoxelMaterial material);
int synth_apply_rule(RealitySynthesizer *synth, int scene_idx, const char *rule_name);
void synth_physics_simulate(RealitySynthesizer *synth, int scene_idx);
void synth_texture(RealitySynthesizer *synth, int scene_idx);
void synth_show_scenes(RealitySynthesizer *synth);
void synth_show_scene(RealitySynthesizer *synth, const char *scene_name);
void synth_show_rules(RealitySynthesizer *synth);

#endif /* SYNTHESIS_H */
