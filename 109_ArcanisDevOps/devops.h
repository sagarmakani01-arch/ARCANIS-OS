#ifndef ARCANIS_DEVOPS_H
#define ARCANIS_DEVOPS_H

typedef enum {
    PIPELINE_IDLE,
    PIPELINE_RUNNING,
    PIPELINE_FAILED,
    PIPELINE_SUCCESS
} PipelineState;

typedef enum {
    STAGE_CHECKOUT,
    STAGE_BUILD,
    STAGE_TEST,
    STAGE_PACKAGE,
    STAGE_DEPLOY
} StageType;

typedef struct {
    char id[32];
    char name[64];
    StageType type;
    char command[256];
    int order;
    int duration_ms;
    int exit_code;
} PipelineStage;

typedef struct {
    char id[32];
    char name[64];
    char repo[256];
    char branch[64];
    PipelineState state;
    PipelineStage stages[16];
    int stage_count;
    int current_stage;
    int started_at;
    int finished_at;
} Pipeline;

typedef struct {
    char id[32];
    char name[64];
    char version[32];
    char path[256];
    char checksum[64];
    int size;
    int created_at;
} Artifact;

typedef struct {
    char name[64];
    char value[256];
} EnvVar;

typedef struct {
    char name[64];
    char image[128];
    PipelineStage stages[8];
    int stage_count;
} Deployment;

Pipeline* devops_create_pipeline(const char* name, const char* repo, const char* branch);
void devops_add_stage(Pipeline* p, StageType type, const char* command, int order);
int devops_run_pipeline(Pipeline* p);
void devops_list_pipelines(void);
Artifact* devops_create_artifact(const char* name, const char* version, const char* path);
void devops_list_artifacts(void);
EnvVar* devops_set_env(const char* name, const char* value);
void devops_list_env(void);
Deployment* devops_create_deployment(const char* name, const char* image);
void devops_list_deployments(void);

#endif
