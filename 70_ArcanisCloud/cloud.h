/**
 * cloud.h — Cloud Services Integration
 *
 * AWS-like cloud services: S3 storage, EC2 compute, Lambda functions.
 */
#ifndef ARCANIS_CLOUD_H
#define ARCANIS_CLOUD_H

#include <arcanis/types.h>

#define CLOUD_MAX_SERVICES   32
#define CLOUD_MAX_BUCKETS    64
#define CLOUD_MAX_INSTANCES  32
#define CLOUD_MAX_FUNCTIONS  64
#define CLOUD_MAX_NAME       64
#define CLOUD_MAX_ENDPOINT   256
#define CLOUD_MAX_KEY        256

typedef enum {
    CLOUD_S3,
    CLOUD_EC2,
    CLOUD_LAMBDA,
    CLOUD_DYNAMO,
    CLOUD_SQS,
    CLOUD_SNS
} cloud_service_type_t;

typedef enum {
    INSTANCE_STOPPED,
    INSTANCE_RUNNING,
    INSTANCE_PENDING,
    INSTANCE_SHUTTING_DOWN,
    INSTANCE_TERMINATED
} instance_state_t;

typedef enum {
    FUNCTION_IDLE,
    FUNCTION_RUNNING,
    FUNCTION_ERROR
} function_state_t;

/* ---- S3 Storage ---- */

typedef struct {
    char name[CLOUD_MAX_NAME];
    char region[32];
    uint64_t size;
    uint32_t objects;
    char owner[CLOUD_MAX_NAME];
    uint32_t created;
    int encrypted;
} s3_bucket_t;

typedef struct {
    char key[CLOUD_MAX_KEY];
    char bucket[CLOUD_MAX_NAME];
    uint64_t size;
    char content_type[64];
    char etag[64];
    uint32_t last_modified;
    int encrypted;
} s3_object_t;

/* ---- EC2 Compute ---- */

typedef struct {
    uint32_t id;
    char instance_id[32];
    char name[CLOUD_MAX_NAME];
    instance_state_t state;
    char instance_type[32];
    char ami[64];
    char vpc_id[32];
    char subnet_id[32];
    char private_ip[16];
    char public_ip[16];
    char key_name[64];
    uint32_t cpu_cores;
    uint64_t memory_mb;
    uint64_t disk_gb;
    uint32_t launch_time;
    char security_groups[8][32];
    uint32_t num_security_groups;
} ec2_instance_t;

/* ---- Lambda Functions ---- */

typedef struct {
    uint32_t id;
    char function_name[CLOUD_MAX_NAME];
    char runtime[32];
    char handler[128];
    uint32_t memory_mb;
    uint32_t timeout_sec;
    function_state_t state;
    uint64_t invoked_count;
    uint64_t error_count;
    uint32_t avg_duration_ms;
    char role[128];
    char environment[256];
} lambda_function_t;

typedef struct {
    uint32_t status_code;
    char content_type[64];
    uint8_t* body;
    uint32_t body_len;
    char headers[16][256];
    uint32_t num_headers;
} lambda_response_t;

/* ---- Main Cloud Manager ---- */

typedef struct {
    s3_bucket_t buckets[CLOUD_MAX_BUCKETS];
    uint32_t num_buckets;

    ec2_instance_t instances[CLOUD_MAX_INSTANCES];
    uint32_t num_instances;

    lambda_function_t functions[CLOUD_MAX_FUNCTIONS];
    uint32_t num_functions;

    char region[32];
    char endpoint[CLOUD_MAX_ENDPOINT];
    char access_key[64];
    char secret_key[64];
    int connected;
} cloud_manager_t;

/* Initialize cloud manager */
void cloud_init(cloud_manager_t* mgr);

/* Connection */
int   cloud_connect(cloud_manager_t* mgr, const char* endpoint,
                    const char* access_key, const char* secret_key);
void  cloud_disconnect(cloud_manager_t* mgr);

/* ---- S3 Operations ---- */
int   s3_create_bucket(cloud_manager_t* mgr, const char* name, const char* region);
int   s3_delete_bucket(cloud_manager_t* mgr, const char* name);
int   s3_list_buckets(cloud_manager_t* mgr, char* buf, uint32_t buf_len);
int   s3_put_object(cloud_manager_t* mgr, const char* bucket, const char* key,
                    const uint8_t* data, uint32_t size, const char* content_type);
int   s3_get_object(cloud_manager_t* mgr, const char* bucket, const char* key,
                    uint8_t* data, uint32_t* size);
int   s3_delete_object(cloud_manager_t* mgr, const char* bucket, const char* key);
int   s3_list_objects(cloud_manager_t* mgr, const char* bucket, char* buf, uint32_t buf_len);
int   s3_copy_object(cloud_manager_t* mgr, const char* src_bucket, const char* src_key,
                     const char* dst_bucket, const char* dst_key);
int   s3_head_object(cloud_manager_t* mgr, const char* bucket, const char* key,
                     s3_object_t* info);

/* ---- EC2 Operations ---- */
int   ec2_run_instance(cloud_manager_t* mgr, const char* name, const char* ami,
                       const char* instance_type, const char* key_name);
int   ec2_terminate_instance(cloud_manager_t* mgr, const char* instance_id);
int   ec2_stop_instance(cloud_manager_t* mgr, const char* instance_id);
int   ec2_start_instance(cloud_manager_t* mgr, const char* instance_id);
int   ec2_reboot_instance(cloud_manager_t* mgr, const char* instance_id);
int   ec2_list_instances(cloud_manager_t* mgr, char* buf, uint32_t buf_len);
int   ec2_describe_instance(cloud_manager_t* mgr, const char* instance_id, char* buf, uint32_t buf_len);
int   ec2_create_security_group(cloud_manager_t* mgr, const char* name, const char* description);
int   ec2_authorize_ingress(cloud_manager_t* mgr, const char* sg_id,
                           const char* protocol, uint32_t port, const char* cidr);

/* ---- Lambda Operations ---- */
int   lambda_create_function(cloud_manager_t* mgr, const char* name,
                            const char* runtime, const char* handler,
                            const uint8_t* code, uint32_t code_size);
int   lambda_delete_function(cloud_manager_t* mgr, const char* name);
int   lambda_invoke(cloud_manager_t* mgr, const char* name,
                    const uint8_t* payload, uint32_t payload_len,
                    lambda_response_t* response);
int   lambda_update_function(cloud_manager_t* mgr, const char* name,
                            const uint8_t* code, uint32_t code_size);
int   lambda_list_functions(cloud_manager_t* mgr, char* buf, uint32_t buf_len);
int   lambda_get_function(cloud_manager_t* mgr, const char* name, char* buf, uint32_t buf_len);
int   lambda_publish_version(cloud_manager_t* mgr, const char* name);
int   lambda_add_permission(cloud_manager_t* mgr, const char* name,
                           const char* principal, const char* action);

#endif
