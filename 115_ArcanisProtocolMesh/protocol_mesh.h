#ifndef ARCANIS_PROTOCOL_MESH_H
#define ARCANIS_PROTOCOL_MESH_H

typedef enum {
    PROTO_HTTP,
    PROTO_HTTPS,
    PROTO_MQTT,
    PROTO_COAP,
    PROTO_GRPC,
    PROTO_WEBSOCKET,
    PROTO_AMQP,
    PROTO_KAFKA,
    PROTO_CUSTOM,
    PROTO_LEGACY,
    PROTO_QUANTUM
} ProtocolType;

typedef struct {
    ProtocolType src_protocol;
    ProtocolType dst_protocol;
    char translation_rules[1024];
    double accuracy;
    int latency_ms;
    int auto_optimize;
} ProtocolBridge;

typedef struct {
    char id[32];
    char name[64];
    ProtocolType type;
    char endpoint[256];
    int port;
    int connected;
    int message_count;
    double throughput;
} ProtocolEndpoint;

typedef struct {
    char id[32];
    char pattern[256];
    ProtocolType target_protocol;
    char target_endpoint[256];
    int priority;
    int active;
} IntelligentRoute;

typedef struct {
    ProtocolEndpoint endpoints[32];
    int endpoint_count;
    ProtocolBridge bridges[16];
    int bridge_count;
    IntelligentRoute routes[64];
    int route_count;
    int total_translations;
    double mesh_throughput;
    int self_optimizing;
} ProtocolMesh;

void mesh_init(void);
ProtocolEndpoint* mesh_add_endpoint(const char* name, ProtocolType type, const char* endpoint, int port);
ProtocolBridge* mesh_create_bridge(ProtocolType src, ProtocolType dst);
int mesh_translate(ProtocolBridge* bridge, const char* data, char* output, int max_len);
IntelligentRoute* mesh_add_route(const char* pattern, ProtocolType target, const char* endpoint);
void mesh_learn_route(const char* source, const char* target, int success);
void mesh_optimize_routes(void);
void mesh_show_endpoints(void);
void mesh_show_bridges(void);
void mesh_show_routes(void);
void mesh_show_stats(void);

#endif
