/**
 * apigateway.c — API Gateway & Service Mesh Implementation
 */
#include <arcanis/apigateway.h>
#include <arcanis/string.h>
#include <stdio.h>
#include <string.h>

void ag_init(ag_gateway_t* gw) {
    if (!gw) return;
    memset(gw, 0, sizeof(ag_gateway_t));
    gw->default_lb = AG_ALGO_ROUND_ROBIN;
    printf("[API GATEWAY] Initialized\n");
}

int ag_add_service(ag_gateway_t* gw, const char* name, const char* host,
                   uint16_t port, uint32_t weight) {
    if (!gw || !name || !host) return -1;
    if (gw->num_services >= AG_MAX_SERVICES) return -1;
    ag_service_t* s = &gw->services[gw->num_services];
    memset(s, 0, sizeof(ag_service_t));
    snprintf(s->service_id, 32, "svc-%u", gw->num_services);
    string_copy(s->name, name, AG_MAX_NAME);
    string_copy(s->host, host, AG_MAX_HOST);
    s->port = port;
    s->state = AG_SERVICE_UP;
    s->weight = weight ? weight : 1;
    s->healthy = 1;
    gw->num_services++;
    printf("[API GATEWAY] Service '%s' added (%s:%u)\n", name, host, port);
    return 0;
}

int ag_remove_service(ag_gateway_t* gw, const char* name) {
    if (!gw || !name) return -1;
    for (uint32_t i = 0; i < gw->num_services; i++) {
        if (string_compare(gw->services[i].name, name) == 0) {
            for (uint32_t j = i; j < gw->num_services - 1; j++)
                gw->services[j] = gw->services[j + 1];
            gw->num_services--;
            return 0;
        }
    }
    return -1;
}

int ag_health_check(ag_gateway_t* gw, const char* name) {
    if (!gw || !name) return -1;
    for (uint32_t i = 0; i < gw->num_services; i++) {
        if (string_compare(gw->services[i].name, name) == 0) {
            gw->services[i].healthy = 1;
            gw->services[i].state = AG_SERVICE_UP;
            return 0;
        }
    }
    return -1;
}

int ag_list_services(ag_gateway_t* gw, char* buf, uint32_t buf_len) {
    if (!gw || !buf) return 0;
    uint32_t pos = 0;
    const char* states[] = {"UP", "DOWN", "DEGRADED"};
    pos += snprintf(buf + pos, buf_len - pos, "SERVICES: %u\n", gw->num_services);
    pos += snprintf(buf + pos, buf_len - pos,
        "ID        NAME             HOST:PORT              STATUS  WEIGHT  LATENCY  REQS\n");
    for (uint32_t i = 0; i < gw->num_services && pos < buf_len - 130; i++) {
        ag_service_t* s = &gw->services[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-9s %-16s %-22s %-7s %5u  %5.1fms %7llu\n",
            s->service_id, s->name, "", states[s->state],
            s->weight, s->avg_latency_ms,
            (unsigned long long)s->request_count);
    }
    return (int)pos;
}

int ag_add_route(ag_gateway_t* gw, const char* name, const char* path,
                 const char* method, const char* target_service) {
    if (!gw || !name || !path || !method || !target_service) return -1;
    if (gw->num_routes >= AG_MAX_ROUTES) return -1;
    ag_route_t* r = &gw->routes[gw->num_routes];
    memset(r, 0, sizeof(ag_route_t));
    string_copy(r->name, name, AG_MAX_NAME);
    string_copy(r->path, path, 128);
    string_copy(r->method, method, 8);
    string_copy(r->target_service, target_service, AG_MAX_NAME);
    r->rate_limit = 100;
    r->timeout_ms = 5000;
    gw->num_routes++;
    printf("[API GATEWAY] Route '%s' (%s %s -> %s)\n", name, method, path, target_service);
    return 0;
}

int ag_remove_route(ag_gateway_t* gw, const char* name) {
    if (!gw || !name) return -1;
    for (uint32_t i = 0; i < gw->num_routes; i++)
        if (string_compare(gw->routes[i].name, name) == 0) {
            for (uint32_t j = i; j < gw->num_routes - 1; j++)
                gw->routes[j] = gw->routes[j + 1];
            gw->num_routes--;
            return 0;
        }
    return -1;
}

int ag_list_routes(ag_gateway_t* gw, char* buf, uint32_t buf_len) {
    if (!gw || !buf) return 0;
    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "ROUTES: %u\n", gw->num_routes);
    pos += snprintf(buf + pos, buf_len - pos,
        "NAME             PATH             METHOD  TARGET SERVICE     HITS\n");
    for (uint32_t i = 0; i < gw->num_routes && pos < buf_len - 120; i++) {
        ag_route_t* r = &gw->routes[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-16s %-16s %-7s %-18s %llu\n",
            r->name, r->path, r->method, r->target_service,
            (unsigned long long)r->hit_count);
    }
    return (int)pos;
}

int ag_add_middleware(ag_gateway_t* gw, ag_mw_type_t type, const char* config) {
    if (!gw || !config) return -1;
    if (gw->num_middleware >= AG_MAX_MIDDLEWARE) return -1;
    ag_middleware_t* m = &gw->middleware[gw->num_middleware];
    m->type = type;
    string_copy(m->name, "mw", 32);
    string_copy(m->config, config, 256);
    m->enabled = 1;
    m->order = gw->num_middleware;
    gw->num_middleware++;
    return 0;
}

int ag_list_middleware(ag_gateway_t* gw, char* buf, uint32_t buf_len) {
    if (!gw || !buf) return 0;
    uint32_t pos = 0;
    const char* type_names[] = {"Auth", "RateLimit", "CORS", "Logging", "Cache", "Compress"};
    pos += snprintf(buf + pos, buf_len - pos, "MIDDLEWARE: %u\n", gw->num_middleware);
    for (uint32_t i = 0; i < gw->num_middleware && pos < buf_len - 80; i++) {
        pos += snprintf(buf + pos, buf_len - pos,
            "  [%s] %s\n", type_names[gw->middleware[i].type], gw->middleware[i].config);
    }
    return (int)pos;
}

int ag_set_load_balancer(ag_gateway_t* gw, ag_lb_algo_t algo) {
    if (!gw) return -1;
    gw->default_lb = algo;
    const char* names[] = {"round-robin", "least-connections", "ip-hash", "weighted"};
    printf("[API GATEWAY] Load balancer changed to %s\n", names[algo]);
    return 0;
}

int ag_get_stats(ag_gateway_t* gw, char* buf, uint32_t buf_len) {
    if (!gw || !buf) return 0;
    uint32_t up=0, down=0;
    for (uint32_t i = 0; i < gw->num_services; i++) {
        if (gw->services[i].state == AG_SERVICE_UP) up++;
        else down++;
    }
    const char* algo_names[] = {"round-robin", "least-connections", "ip-hash", "weighted"};
    return snprintf(buf, buf_len,
        "API Gateway Stats:\n"
        "  LB Algorithm: %s\n"
        "  Services: %u (%u up, %u down)\n"
        "  Routes: %u\n"
        "  Middleware: %u\n"
        "  Total Requests: %llu\n"
        "  Total Errors: %llu\n",
        algo_names[gw->default_lb], gw->num_services, up, down,
        gw->num_routes, gw->num_middleware,
        (unsigned long long)gw->total_requests,
        (unsigned long long)gw->total_errors);
}
