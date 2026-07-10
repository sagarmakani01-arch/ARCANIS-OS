/**
 * apigateway.h — API Gateway & Service Mesh
 *
 * API gateway, service discovery, load balancing, rate limiting.
 */
#ifndef ARCANIS_APIGATEWAY_H
#define ARCANIS_APIGATEWAY_H

#include <arcanis/types.h>

#define AG_MAX_SERVICES      128
#define AG_MAX_ROUTES        512
#define AG_MAX_MIDDLEWARE    64
#define AG_MAX_NAME          64
#define AG_MAX_HOST          128

typedef enum {
    AG_SERVICE_UP,
    AG_SERVICE_DOWN,
    AG_SERVICE_DEGRADED
} ag_service_state_t;

typedef struct {
    char service_id[32];
    char name[AG_MAX_NAME];
    char host[AG_MAX_HOST];
    uint16_t port;
    ag_service_state_t state;

    uint32_t priority;
    uint64_t request_count;
    uint64_t success_count;
    uint64_t error_count;
    double avg_latency_ms;
    uint32_t weight;
    int healthy;
} ag_service_t;

typedef enum {
    AG_ALGO_ROUND_ROBIN,
    AG_ALGO_LEAST_CONNECTIONS,
    AG_ALGO_IP_HASH,
    AG_ALGO_WEIGHTED
} ag_lb_algo_t;

typedef struct {
    char name[AG_MAX_NAME];
    char path[128];
    char method[8];
    char target_service[AG_MAX_NAME];
    uint32_t rate_limit; /* req/s */
    uint32_t timeout_ms;
    int is_authenticated;
    int is_cached;
    ag_lb_algo_t lb_algo;
    uint64_t hit_count;
} ag_route_t;

typedef enum {
    AG_MW_AUTH,
    AG_MW_RATE_LIMIT,
    AG_MW_CORS,
    AG_MW_LOGGING,
    AG_MW_CACHE,
    AG_MW_COMPRESS
} ag_mw_type_t;

typedef struct {
    ag_mw_type_t type;
    char name[32];
    char config[256];
    int enabled;
    int order;
} ag_middleware_t;

typedef struct {
    ag_service_t services[AG_MAX_SERVICES];
    uint32_t num_services;

    ag_route_t routes[AG_MAX_ROUTES];
    uint32_t num_routes;

    ag_middleware_t middleware[AG_MAX_MIDDLEWARE];
    uint32_t num_middleware;

    ag_lb_algo_t default_lb;
    uint32_t rr_counter;
    uint64_t total_requests;
    uint64_t total_errors;
} ag_gateway_t;

void ag_init(ag_gateway_t* gw);
int  ag_add_service(ag_gateway_t* gw, const char* name, const char* host,
                    uint16_t port, uint32_t weight);
int  ag_remove_service(ag_gateway_t* gw, const char* name);
int  ag_health_check(ag_gateway_t* gw, const char* name);
int  ag_list_services(ag_gateway_t* gw, char* buf, uint32_t buf_len);

int  ag_add_route(ag_gateway_t* gw, const char* name, const char* path,
                  const char* method, const char* target_service);
int  ag_remove_route(ag_gateway_t* gw, const char* name);
int  ag_list_routes(ag_gateway_t* gw, char* buf, uint32_t buf_len);

int  ag_add_middleware(ag_gateway_t* gw, ag_mw_type_t type, const char* config);
int  ag_list_middleware(ag_gateway_t* gw, char* buf, uint32_t buf_len);

int  ag_set_load_balancer(ag_gateway_t* gw, ag_lb_algo_t algo);
int  ag_get_stats(ag_gateway_t* gw, char* buf, uint32_t buf_len);

#endif
