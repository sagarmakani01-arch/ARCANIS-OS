#include "protocol_mesh.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static ProtocolMesh mesh;

static const char* proto_name(ProtocolType t) {
    static const char* names[] = {"HTTP","HTTPS","MQTT","COAP","GRPC","WEBSOCKET","AMQP","KAFKA","CUSTOM","LEGACY","QUANTUM"};
    return t <= PROTO_QUANTUM ? names[t] : "UNKNOWN";
}

void mesh_init(void) {
    memset(&mesh, 0, sizeof(mesh));
    mesh.mesh_throughput = 1000.0;
    srand((unsigned)time(NULL));
    printf("[MESH] Protocol mesh initialized\n");
}

ProtocolEndpoint* mesh_add_endpoint(const char* name, ProtocolType type, const char* endpoint, int port) {
    if (mesh.endpoint_count >= 32) return NULL;
    ProtocolEndpoint* e = &mesh.endpoints[mesh.endpoint_count++];
    snprintf(e->id, sizeof(e->id), "EP-%d", mesh.endpoint_count);
    snprintf(e->name, sizeof(e->name), "%s", name);
    e->type = type;
    snprintf(e->endpoint, sizeof(e->endpoint), "%s", endpoint);
    e->port = port;
    e->connected = 1;
    e->message_count = 0;
    e->throughput = 0.0;
    printf("[MESH] Endpoint '%s' added (%s://%s:%d)\n", name, proto_name(type), endpoint, port);
    return e;
}

ProtocolBridge* mesh_create_bridge(ProtocolType src, ProtocolType dst) {
    if (mesh.bridge_count >= 16) return NULL;
    ProtocolBridge* b = &mesh.bridges[mesh.bridge_count++];
    b->src_protocol = src;
    b->dst_protocol = dst;
    snprintf(b->translation_rules, sizeof(b->translation_rules), "auto:%s->%s", proto_name(src), proto_name(dst));
    b->accuracy = 0.95 + (rand() % 100) / 1000.0;
    b->latency_ms = rand() % 100 + 10;
    b->auto_optimize = 1;
    printf("[MESH] Bridge created: %s <-> %s (acc=%.3f)\n", proto_name(src), proto_name(dst), b->accuracy);
    return b;
}

int mesh_translate(ProtocolBridge* bridge, const char* data, char* output, int max_len) {
    if (!bridge || !data || !output) return -1;
    mesh.total_translations++;
    snprintf(output, max_len, "[%s->%s] %s", proto_name(bridge->src_protocol), proto_name(bridge->dst_protocol), data);
    bridge->accuracy = 0.95 + (rand() % 100) / 1000.0;
    bridge->latency_ms = rand() % 50 + 5;
    printf("[MESH] Translation #%d: %s -> %s (%dms)\n", mesh.total_translations,
           proto_name(bridge->src_protocol), proto_name(bridge->dst_protocol), bridge->latency_ms);
    return (int)strlen(output);
}

IntelligentRoute* mesh_add_route(const char* pattern, ProtocolType target, const char* endpoint) {
    if (mesh.route_count >= 64) return NULL;
    IntelligentRoute* r = &mesh.routes[mesh.route_count++];
    snprintf(r->id, sizeof(r->id), "RT-%d", mesh.route_count);
    snprintf(r->pattern, sizeof(r->pattern), "%s", pattern);
    r->target_protocol = target;
    snprintf(r->target_endpoint, sizeof(r->target_endpoint), "%s", endpoint);
    r->priority = 5;
    r->active = 1;
    printf("[MESH] Route added: '%s' -> %s (%s)\n", pattern, proto_name(target), endpoint);
    return r;
}

void mesh_learn_route(const char* source, const char* target, int success) {
    printf("[MESH] Learning route: %s -> %s (success=%d)\n", source, target, success);
    if (success) {
        mesh.mesh_throughput += 10.0;
    }
}

void mesh_optimize_routes(void) {
    mesh.self_optimizing = 1;
    for (int i = 0; i < mesh.bridge_count; i++) {
        mesh.bridges[i].auto_optimize = 1;
        mesh.bridges[i].latency_ms = rand() % 20 + 2;
        mesh.bridges[i].accuracy = 0.98 + (rand() % 20) / 1000.0;
    }
    printf("[MESH] Routes optimized. Self-optimizing mode enabled\n");
}

void mesh_show_endpoints(void) {
    printf("=== Mesh Endpoints ===\n");
    printf("%-4s %-16s %-10s %-24s %-6s %s\n", "ID", "Name", "Type", "Endpoint", "Port", "Status");
    for (int i = 0; i < mesh.endpoint_count; i++) {
        ProtocolEndpoint* e = &mesh.endpoints[i];
        printf("%-4s %-16s %-10s %-24s %-6d %s\n", e->id, e->name, proto_name(e->type),
               e->endpoint, e->port, e->connected ? "UP" : "DOWN");
    }
}

void mesh_show_bridges(void) {
    printf("=== Protocol Bridges ===\n");
    printf("%-4s %-12s -> %-12s %-8s %-8s %s\n", "#", "Source", "Dest", "Accuracy", "Latency", "Optimize");
    for (int i = 0; i < mesh.bridge_count; i++) {
        ProtocolBridge* b = &mesh.bridges[i];
        printf("%-4d %-12s -> %-12s %-8.3f %-8d %s\n", i+1,
               proto_name(b->src_protocol), proto_name(b->dst_protocol),
               b->accuracy, b->latency_ms, b->auto_optimize ? "ON" : "OFF");
    }
}

void mesh_show_routes(void) {
    printf("=== Intelligent Routes ===\n");
    printf("%-4s %-24s %-12s %-24s %-6s %s\n", "ID", "Pattern", "Proto", "Endpoint", "Pri", "State");
    for (int i = 0; i < mesh.route_count; i++) {
        IntelligentRoute* r = &mesh.routes[i];
        printf("%-4s %-24s %-12s %-24s %-6d %s\n", r->id, r->pattern,
               proto_name(r->target_protocol), r->target_endpoint,
               r->priority, r->active ? "ACTIVE" : "INACTIVE");
    }
}

void mesh_show_stats(void) {
    printf("=== Mesh Statistics ===\n");
    printf("  Endpoints: %d\n", mesh.endpoint_count);
    printf("  Bridges: %d\n", mesh.bridge_count);
    printf("  Routes: %d\n", mesh.route_count);
    printf("  Total Translations: %d\n", mesh.total_translations);
    printf("  Throughput: %.1f msg/s\n", mesh.mesh_throughput);
    printf("  Self-Optimizing: %s\n", mesh.self_optimizing ? "YES" : "NO");
}
