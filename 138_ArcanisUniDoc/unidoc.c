#include "unidoc.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

typedef struct {
    int fragment_id;
    char content[128];
    char source_module[32];
    char tags[64];
    float embedding[4];
} DocFragment;

typedef struct {
    int from_id;
    int to_id;
    float weight;
} GraphEdge;

typedef struct {
    int query_id;
    char query_text[64];
    int result_count;
    int natural_language_active;
} UniversalQuery;

typedef struct {
    DocFragment fragments[32];
    int fragment_count;
    GraphEdge edges[32];
    int edge_count;
    int index_built;
    UniversalQuery queries[16];
    int query_count;
} UniversalDocEngine;

static UniversalDocEngine ude;

void unidoc_init(void) {
    ude.fragment_count = 0;
    ude.edge_count = 0;
    ude.index_built = 0;
    ude.query_count = 0;
    srand((unsigned)time(NULL));
}

void unidoc_ingest(const char *content, const char *module, const char *tags) {
    if (ude.fragment_count >= 32) return;
    DocFragment *f = &ude.fragments[ude.fragment_count++];
    f->fragment_id = ude.fragment_count;
    snprintf(f->content, sizeof(f->content), "%s", content);
    snprintf(f->source_module, sizeof(f->source_module), "%s", module);
    snprintf(f->tags, sizeof(f->tags), "%s", tags);
    for (int i = 0; i < 4; i++)
        f->embedding[i] = ((float)rand() / RAND_MAX) * 2.0f - 1.0f;
    printf("Ingested doc #%d from %s\n", f->fragment_id, module);
}

void unidoc_query(const char *text) {
    if (ude.query_count >= 16) return;
    UniversalQuery *q = &ude.queries[ude.query_count++];
    q->query_id = ude.query_count;
    snprintf(q->query_text, sizeof(q->query_text), "%s", text);
    q->natural_language_active = 0;
    q->result_count = 0;
    printf("Query #%d: '%s'\n", q->query_id, text);
    for (int i = 0; i < ude.fragment_count; i++) {
        if (strstr(ude.fragments[i].content, text)) {
            printf("  Match: doc #%d: %s\n", ude.fragments[i].fragment_id, ude.fragments[i].content);
            q->result_count++;
        }
    }
}

void unidoc_search_natural(const char *text) {
    if (ude.query_count >= 16) return;
    UniversalQuery *q = &ude.queries[ude.query_count++];
    q->query_id = ude.query_count;
    snprintf(q->query_text, sizeof(q->query_text), "%s", text);
    q->natural_language_active = 1;
    q->result_count = 0;
    printf("Natural search: '%s'\n", text);
    for (int i = 0; i < ude.fragment_count; i++) {
        if (strstr(ude.fragments[i].content, text) ||
            strstr(ude.fragments[i].tags, text)) {
            printf("  Found: doc #%d\n", ude.fragments[i].fragment_id);
            q->result_count++;
        }
    }
}

void unidoc_connect(int from_id, int to_id) {
    if (ude.edge_count >= 32) return;
    GraphEdge *e = &ude.edges[ude.edge_count++];
    e->from_id = from_id;
    e->to_id = to_id;
    e->weight = ((float)rand() / RAND_MAX);
    printf("Connected doc %d -> %d (weight=%.2f)\n", from_id, to_id, e->weight);
}

void unidoc_build_index(void) {
    ude.index_built = 1;
    printf("Index built for %d documents, %d edges\n", ude.fragment_count, ude.edge_count);
}

void unidoc_show_documents(void) {
    printf("\n%-3s %-30s %-16s %s\n", "ID", "Content", "Module", "Tags");
    printf("----------------------------------------------------------\n");
    for (int i = 0; i < ude.fragment_count; i++) {
        printf("%-3d %-30s %-16s %s\n",
               ude.fragments[i].fragment_id,
               ude.fragments[i].content,
               ude.fragments[i].source_module,
               ude.fragments[i].tags);
    }
}

void unidoc_show_graph(void) {
    printf("\nGraph Edges:\n");
    printf("%-4s %-4s %s\n", "From", "To", "Weight");
    printf("------------------------\n");
    for (int i = 0; i < ude.edge_count; i++) {
        printf("%-4d %-4d %.2f\n", ude.edges[i].from_id, ude.edges[i].to_id, ude.edges[i].weight);
    }
}

void unidoc_show_stats(void) {
    printf("\n=== Universal Doc Engine ===\n");
    printf("%-20s %d\n", "Documents", ude.fragment_count);
    printf("%-20s %d\n", "Edges", ude.edge_count);
    printf("%-20s %d\n", "Queries", ude.query_count);
    printf("%-20s %s\n", "Index", ude.index_built ? "built" : "not built");
}
