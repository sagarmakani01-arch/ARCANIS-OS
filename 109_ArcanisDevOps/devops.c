#include "devops.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static Pipeline pipelines[16];
static int pipeline_count = 0;
static Artifact artifacts[32];
static int artifact_count = 0;
static EnvVar env_vars[32];
static int env_count = 0;
static Deployment deployments[16];
static int deploy_count = 0;

Pipeline* devops_create_pipeline(const char* name, const char* repo, const char* branch) {
    if (pipeline_count >= 16) return NULL;
    Pipeline* p = &pipelines[pipeline_count++];
    snprintf(p->id, 32, "pipe-%d", pipeline_count);
    snprintf(p->name, 64, "%s", name);
    snprintf(p->repo, 256, "%s", repo);
    snprintf(p->branch, 64, "%s", branch);
    p->state = PIPELINE_IDLE;
    p->stage_count = 0;
    p->current_stage = 0;
    p->started_at = 0;
    p->finished_at = 0;
    printf("Pipeline '%s' created (repo: %s, branch: %s)\n", name, repo, branch);
    return p;
}

void devops_add_stage(Pipeline* p, StageType type, const char* command, int order) {
    if (p->stage_count >= 16) return;
    PipelineStage* s = &p->stages[p->stage_count++];
    snprintf(s->id, 32, "stage-%d", p->stage_count);
    s->type = type;
    snprintf(s->command, 256, "%s", command);
    s->order = order;
    s->duration_ms = 0;
    s->exit_code = -1;
    const char* type_names[] = {"checkout", "build", "test", "package", "deploy"};
    printf("  + Stage: %s -> %s\n", type_names[type], command);
}

int devops_run_pipeline(Pipeline* p) {
    if (!p) return -1;
    p->state = PIPELINE_RUNNING;
    p->started_at = (int)time(NULL);
    printf("\n=== Running Pipeline: %s ===\n", p->name);
    printf("Repo: %s | Branch: %s\n\n", p->repo, p->branch);
    for (int i = 0; i < p->stage_count; i++) {
        PipelineStage* s = &p->stages[i];
        p->current_stage = i;
        printf("[%d/%d] Stage: %s\n", i + 1, p->stage_count, s->command);
        s->duration_ms = rand() % 3000 + 500;
        s->exit_code = (rand() % 10 > 1) ? 0 : 1;
        if (s->exit_code == 0) {
            printf("  \033[32mPASS\033[0m (%d ms)\n", s->duration_ms);
        } else {
            printf("  \033[31mFAIL\033[0m (exit code %d)\n", s->exit_code);
            p->state = PIPELINE_FAILED;
            p->finished_at = (int)time(NULL);
            printf("\nPipeline FAILED at stage %d\n", i + 1);
            return -1;
        }
    }
    p->state = PIPELINE_SUCCESS;
    p->finished_at = (int)time(NULL);
    int total = p->finished_at - p->started_at;
    printf("\n\033[32mPipeline SUCCESS\033[0m (duration: %d s)\n", total);
    return 0;
}

void devops_list_pipelines(void) {
    printf("\nPipelines:\n");
    printf("  %-8s %-20s %-10s\n", "ID", "NAME", "STATE");
    printf("  ------ -------------------- ----------\n");
    for (int i = 0; i < pipeline_count; i++) {
        Pipeline* p = &pipelines[i];
        const char* states[] = {"idle", "running", "failed", "success"};
        printf("  %-8s %-20s %-10s\n", p->id, p->name, states[p->state]);
    }
}

Artifact* devops_create_artifact(const char* name, const char* version, const char* path) {
    if (artifact_count >= 32) return NULL;
    Artifact* a = &artifacts[artifact_count++];
    snprintf(a->id, 32, "art-%d", artifact_count);
    snprintf(a->name, 64, "%s", name);
    snprintf(a->version, 32, "%s", version);
    snprintf(a->path, 256, "%s", path);
    snprintf(a->checksum, 64, "sha256:%08x", rand());
    a->size = rand() % 100000 + 1000;
    a->created_at = (int)time(NULL);
    printf("Artifact '%s' v%s created\n", name, version);
    return a;
}

void devops_list_artifacts(void) {
    printf("\nArtifacts:\n");
    printf("  %-8s %-20s %-8s %-10s %s\n", "ID", "NAME", "VERSION", "SIZE", "CHECKSUM");
    printf("  ------ -------------------- -------- ---------- -----------------\n");
    for (int i = 0; i < artifact_count; i++) {
        Artifact* a = &artifacts[i];
        printf("  %-8s %-20s %-8s %-10d %s\n", a->id, a->name, a->version, a->size, a->checksum);
    }
}

EnvVar* devops_set_env(const char* name, const char* value) {
    for (int i = 0; i < env_count; i++) {
        if (strcmp(env_vars[i].name, name) == 0) {
            snprintf(env_vars[i].value, 256, "%s", value);
            printf("Env '%s' = '%s' (updated)\n", name, value);
            return &env_vars[i];
        }
    }
    if (env_count >= 32) return NULL;
    EnvVar* e = &env_vars[env_count++];
    snprintf(e->name, 64, "%s", name);
    snprintf(e->value, 256, "%s", value);
    printf("Env '%s' = '%s' (set)\n", name, value);
    return e;
}

void devops_list_env(void) {
    printf("\nEnvironment:\n");
    for (int i = 0; i < env_count; i++) {
        printf("  %s=%s\n", env_vars[i].name, env_vars[i].value);
    }
}

Deployment* devops_create_deployment(const char* name, const char* image) {
    if (deploy_count >= 16) return NULL;
    Deployment* d = &deployments[deploy_count++];
    snprintf(d->name, 64, "%s", name);
    snprintf(d->image, 128, "%s", image);
    d->stage_count = 0;
    printf("Deployment '%s' created (image: %s)\n", name, image);
    return d;
}

void devops_list_deployments(void) {
    printf("\nDeployments:\n");
    printf("  %-20s %-20s\n", "NAME", "IMAGE");
    printf("  -------------------- --------------------\n");
    for (int i = 0; i < deploy_count; i++) {
        printf("  %-20s %-20s\n", deployments[i].name, deployments[i].image);
    }
}
