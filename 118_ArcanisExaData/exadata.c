#include "exadata.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static ExaDataFabric edf;

static const char* dim_str(DataDimension d) {
    static const char* s[] = {"TIMESERIES","GRAPH","RELATIONAL","DOCUMENT","VECTOR","SPATIAL","EVENT"};
    return d <= DIMENSION_EVENT ? s[d] : "UNKNOWN";
}

void exadata_init(void) {
    memset(&edf, 0, sizeof(edf));
    edf.query_throughput = 0.0;
    edf.auto_optimize = 1;
    srand((unsigned)time(NULL));

    exadata_create_store("metrics", DIMENSION_TIMESERIES, "timestamp,metric,value,tags");
    exadata_create_store("dependencies", DIMENSION_GRAPH, "source,target,relationship,weight");
    exadata_create_store("docs", DIMENSION_DOCUMENT, "key,value,embedding");
    printf("[EXADATA] Fabric initialized with %d stores\n", edf.store_count);
}

DataStore* exadata_create_store(const char* name, DataDimension dim, const char* schema) {
    if (edf.store_count >= 32) return NULL;
    DataStore* s = &edf.stores[edf.store_count++];
    snprintf(s->id, sizeof(s->id), "DS-%d", edf.store_count);
    s->dimension = dim;
    snprintf(s->name, sizeof(s->name), "%s", name);
    snprintf(s->schema, sizeof(s->schema), "%s", schema);
    s->record_count = 0;
    s->storage_mb = 0.0;
    s->indexed = 1;
    printf("[EXADATA] Store '%s' created (dim=%s)\n", name, dim_str(dim));
    return s;
}

int exadata_ingest_timeseries(const char* metric, double value, const char* tags) {
    if (edf.ts_count >= 1024) return -1;
    TimeSeriesPoint* p = &edf.ts_buffer[edf.ts_count++];
    p->timestamp = (double)time(NULL);
    snprintf(p->metric, sizeof(p->metric), "%s", metric);
    p->value = value;
    snprintf(p->tags, sizeof(p->tags), "%s", tags);
    printf("[EXADATA] Timeseries ingested: %s=%.2f [%s]\n", metric, value, tags);
    return edf.ts_count;
}

int exadata_add_graph_edge(const char* src, const char* tgt, const char* rel, double w) {
    if (edf.edge_count >= 512) return -1;
    GraphEdge* e = &edf.graph_edges[edf.edge_count++];
    snprintf(e->id, sizeof(e->id), "GE-%d", edf.edge_count);
    snprintf(e->source, sizeof(e->source), "%s", src);
    snprintf(e->target, sizeof(e->target), "%s", tgt);
    snprintf(e->relationship, sizeof(e->relationship), "%s", rel);
    e->weight = w;
    e->directed = 1;
    printf("[EXADATA] Edge added: %s --[%s]--> %s (w=%.2f)\n", src, rel, tgt, w);
    return edf.edge_count;
}

int exadata_store_vector(const char* key, const char* value, double* embedding, int dim) {
    if (edf.vec_count >= 256) return -1;
    VectorDocument* v = &edf.vectors[edf.vec_count++];
    snprintf(v->id, sizeof(v->id), "VEC-%d", edf.vec_count);
    snprintf(v->key, sizeof(v->key), "%s", key);
    snprintf(v->value, sizeof(v->value), "%s", value);
    int copy_dim = dim < 128 ? dim : 128;
    memcpy(v->embedding, embedding, copy_dim * sizeof(double));
    v->embedding_dim = copy_dim;
    printf("[EXADATA] Vector stored: %s (dim=%d)\n", key, copy_dim);
    return edf.vec_count;
}

EventRecord* exadata_log_event(const char* type, const char* payload, int priority) {
    static EventRecord ev;
    snprintf(ev.id, sizeof(ev.id), "EVT-%d", rand() % 10000);
    snprintf(ev.event_type, sizeof(ev.event_type), "%s", type);
    ev.timestamp = (double)time(NULL);
    snprintf(ev.payload, sizeof(ev.payload), "%s", payload);
    ev.priority = priority;
    printf("[EXADATA] Event logged: %s (pri=%d)\n", type, priority);
    return &ev;
}

void exadata_query(const char* query, DataDimension dim) {
    if (edf.query_count < 64) {
        snprintf(edf.active_queries[edf.query_count], 256, "%s", query);
    }
    edf.query_count++;
    edf.query_throughput = edf.query_count * 10.0;
    printf("[EXADATA] Query #%d [%s]: %s\n", edf.query_count, dim_str(dim), query);
}

void exadata_cross_dimension_query(const char* pattern) {
    printf("[EXADATA] Cross-dimension query: %s\n", pattern);
    printf("[EXADATA] Join across stores: ts=%d edges=%d vecs=%d\n",
           edf.ts_count, edf.edge_count, edf.vec_count);
}

void exadata_optimize_stores(void) {
    edf.auto_optimize = 1;
    for (int i = 0; i < edf.store_count; i++) {
        edf.stores[i].indexed = 1;
        edf.stores[i].storage_mb = (edf.stores[i].record_count * 0.001);
    }
    printf("[EXADATA] Stores optimized, indexes rebuilt\n");
}

void exadata_show_stores(void) {
    printf("=== Data Stores ===\n");
    printf("%-6s %-20s %-14s %-8s %-10s %s\n", "ID", "Name", "Dimension", "Records", "Size(MB)", "Indexed");
    for (int i = 0; i < edf.store_count; i++) {
        DataStore* s = &edf.stores[i];
        printf("%-6s %-20s %-14s %-8d %-10.2f %s\n",
               s->id, s->name, dim_str(s->dimension),
               s->record_count, s->storage_mb, s->indexed ? "YES" : "NO");
    }
}

void exadata_show_stats(void) {
    printf("=== ExaData Stats ===\n");
    printf("  Stores: %d\n", edf.store_count);
    printf("  TimeSeries Points: %d\n", edf.ts_count);
    printf("  Graph Edges: %d\n", edf.edge_count);
    printf("  Vector Documents: %d\n", edf.vec_count);
    printf("  Queries Executed: %d\n", edf.query_count);
    printf("  Throughput: %.1f q/s\n", edf.query_throughput);
    printf("  Auto-Optimize: %s\n", edf.auto_optimize ? "ON" : "OFF");
}
