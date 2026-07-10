#ifndef UNIDOC_H
#define UNIDOC_H

typedef struct {
    char id[32];
    char content[2048];
    char fragment_type[32];
    char source_module[64];
    char tags[8][64];
    double embedding[64];
    char connections[8][32];
} DocFragment;

typedef struct {
    char id[32];
    char query_text[256];
    DocFragment results[16];
    int result_count;
    double latency_ms;
    int cross_module;
} UniversalQuery;

typedef struct {
    char source[32];
    char target[32];
    double weight;
    char relation[32];
} Edge;

typedef struct {
    DocFragment nodes[32];
    Edge edges[64];
} KnowledgeGraph;

typedef struct {
    DocFragment fragments[128];
    int fragment_count;
    UniversalQuery queries[16];
    int query_count;
    KnowledgeGraph graph;
    int index_built;
    int total_documents;
    int natural_language_active;
    int search_depth;
    int auto_index;
} UniversalDocEngine;

void unidoc_init(UniversalDocEngine *engine);
void unidoc_ingest(UniversalDocEngine *engine, const char *content, const char *source_module, const char *tags);
void unidoc_query(UniversalDocEngine *engine, const char *query_text);
void unidoc_search_natural(UniversalDocEngine *engine, const char *query);
void unidoc_connect(UniversalDocEngine *engine, const char *frag_a, const char *frag_b, const char *relation);
void unidoc_build_index(UniversalDocEngine *engine);
void unidoc_show_documents(const UniversalDocEngine *engine);
void unidoc_show_graph(const UniversalDocEngine *engine);
void unidoc_show_stats(const UniversalDocEngine *engine);

#endif
