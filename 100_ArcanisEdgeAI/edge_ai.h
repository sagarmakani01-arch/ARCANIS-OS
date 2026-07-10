/**
 * edge_ai.h — Edge AI & Federated Learning
 *
 * Distributed ML inference, federated learning, model optimization.
 */
#ifndef ARCANIS_EDGE_AI_H
#define ARCANIS_EDGE_AI_H

#include <arcanis/types.h>

#define EA_MAX_MODELS        64
#define EA_MAX_CLIENTS       256
#define EA_MAX_LAYERS        32
#define EA_MAX_NAME          64
#define EA_MAX_MSG           256

typedef enum {
    EA_MODEL_CNN,
    EA_MODEL_RNN,
    EA_MODEL_TRANSFORMER,
    EA_MODEL_MLP,
    EA_MODEL_CUSTOM
} ea_model_type_t;

typedef enum {
    EA_PRECISION_FLOAT32,
    EA_PRECISION_FLOAT16,
    EA_PRECISION_INT8,
    EA_PRECISION_INT4
} ea_precision_t;

typedef struct {
    char name[64];
    uint32_t input_size;
    uint32_t output_size;
    double weights[256];
    double bias[256];
    double output[256];
} ea_layer_t;

typedef struct {
    char name[EA_MAX_NAME];
    ea_model_type_t type;
    ea_precision_t precision;

    ea_layer_t layers[EA_MAX_LAYERS];
    uint32_t num_layers;

    uint32_t input_dim;
    uint32_t output_dim;
    uint32_t total_params;
    uint32_t model_size_kb;

    double accuracy;
    double loss;
    int quantized;
    int deployed;
} ea_model_t;

typedef struct {
    char id[32];
    char name[EA_MAX_NAME];
    char host[64];
    uint16_t port;

    double* local_weights;
    uint32_t weight_size;
    uint32_t samples_count;
    double learning_rate;
    int status; /* 0=offline, 1=online, 2=training */

    double local_loss;
    double local_accuracy;
} ea_client_t;

typedef struct {
    char name[EA_MAX_NAME];
    uint32_t num_rounds;
    uint32_t current_round;
    double global_loss;
    double global_accuracy;

    ea_client_t clients[EA_MAX_CLIENTS];
    uint32_t num_clients;
    uint32_t active_clients;

    double aggregation_weight;
    int differential_privacy;
    double privacy_epsilon;

    uint32_t total_updates;
    uint64_t total_samples;
} ea_federated_t;

typedef struct {
    ea_model_t models[EA_MAX_MODELS];
    uint32_t num_models;

    ea_federated_t federated;
} ea_system_t;

/* Initialize system */
void ea_init(ea_system_t* sys);

/* Model management */
int   ea_create_model(ea_system_t* sys, const char* name, ea_model_type_t type,
                      uint32_t input_dim, uint32_t output_dim);
int   ea_load_model(ea_system_t* sys, const char* name);
int   ea_optimize_model(ea_system_t* sys, const char* name, ea_precision_t precision);
int   ea_get_model_info(ea_system_t* sys, const char* name, char* buf, uint32_t buf_len);
int   ea_list_models(ea_system_t* sys, char* buf, uint32_t buf_len);

/* Inference */
int   ea_infer(ea_system_t* sys, const char* name, double* input, uint32_t input_size,
               double* output, uint32_t output_size);
int   ea_batch_infer(ea_system_t* sys, const char* name, double** inputs,
                     uint32_t batch_size, double** outputs);

/* Federated learning */
int   ea_fed_create(ea_system_t* sys, const char* name, uint32_t num_rounds);
int   ea_fed_add_client(ea_system_t* sys, const char* name, const char* client_name,
                        const char* host, uint16_t port);
int   ea_fed_start_round(ea_system_t* sys, const char* name);
int   ea_fed_aggregate(ea_system_t* sys, const char* name);
int   ea_fed_get_status(ea_system_t* sys, const char* name, char* buf, uint32_t buf_len);

/* Model deployment */
int   ea_deploy_model(ea_system_t* sys, const char* name);
int   ea_undeploy_model(ea_system_t* sys, const char* name);

#endif
