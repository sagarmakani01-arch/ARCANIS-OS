#ifndef ARCANIS_EXADATA_H
#define ARCANIS_EXADATA_H

typedef enum {
    DIMENSION_TIMESERIES,
    DIMENSION_GRAPH,
    DIMENSION_RELATIONAL,
    DIMENSION_DOCUMENT,
    DIMENSION_VECTOR,
    DIMENSION_SPATIAL,
    DIMENSION_EVENT
} DataDimension;

typedef struct {
    char id[32];
    DataDimension dimension;
    char name[64];
    char schema[512];
    int record_count;
    double storage_mb;
    int indexed;
} DataStore;

typedef struct {
    double timestamp;
    char metric[64];
    double value;
    char tags[256];
} TimeSeriesPoint;

typedef struct {
    char id[32];
    char source[64];
    char target[64];
    char relationship[64];
    double weight;
    int directed;
} GraphEdge;

typedef struct {
    char id[32];
    char key[128];
    char value[2048];
    double embedding[128];
    int embedding_dim;
} VectorDocument;

typedef struct {
    char id[32];
    char event_type[64];
    double timestamp;
    char payload[2048];
    int priority;
} EventRecord;

typedef struct {
    DataStore stores[32];
    int store_count;
    TimeSeriesPoint ts_buffer[1024];
    int ts_count;
    GraphEdge graph_edges[512];
    int edge_count;
    VectorDocument vectors[256];
    int vec_count;
    char active_queries[64][256];
    int query_count;
    double query_throughput;
    int auto_optimize;
} ExaDataFabric;

void exadata_init(void);
DataStore* exadata_create_store(const char* name, DataDimension dim, const char* schema);
int exadata_ingest_timeseries(const char* metric, double value, const char* tags);
int exadata_add_graph_edge(const char* src, const char* tgt, const char* rel, double w);
int exadata_store_vector(const char* key, const char* value, double* embedding, int dim);
EventRecord* exadata_log_event(const char* type, const char* payload, int priority);
void exadata_query(const char* query, DataDimension dim);
void exadata_cross_dimension_query(const char* pattern);
void exadata_optimize_stores(void);
void exadata_show_stores(void);
void exadata_show_stats(void);

#endif
