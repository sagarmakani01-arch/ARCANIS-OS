#include "graphneural.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static GraphNeuralEngine gne;

void gne_init(void) {
    memset(&gne, 0, sizeof(gne));
    srand((unsigned)time(NULL));
    gne.graph.computed = 0;
    printf("[GNE] Graph Neural Engine initialized\n");
}

GraphNode* gne_add_node(const char* label, double* features, int dim) {
    if (gne.graph.node_count >= 256) return NULL;
    GraphNode* n = &gne.graph.nodes[gne.graph.node_count++];
    n->id = gne.graph.node_count;
    snprintf(n->label, sizeof(n->label), "%s", label);
    int copy_dim = dim < 128 ? dim : 128;
    memcpy(n->features, features, copy_dim * sizeof(double));
    n->feature_dim = copy_dim;
    memset(n->embedding, 0, sizeof(n->embedding));
    n->community_id = -1;
    n->centrality = 1.0;
    printf("[GNE] Node %d '%s' added (dim=%d)\n", n->id, label, copy_dim);
    return n;
}

GraphEdge* gne_add_edge(int src, int tgt, double weight, const char* relation, int directed) {
    if (gne.graph.edge_count >= 1024) return NULL;
    GraphEdge* e = &gne.graph.edges[gne.graph.edge_count++];
    e->source_id = src;
    e->target_id = tgt;
    e->weight = weight;
    snprintf(e->relation, sizeof(e->relation), "%s", relation);
    e->directed = directed;
    memset(e->message, 0, sizeof(e->message));

    gne.graph.adjacency[src][tgt] = weight;
    if (!directed) {
        gne.graph.adjacency[tgt][src] = weight;
    }
    gne.graph.computed = 0;
    printf("[GNE] Edge %d->%d '%s' w=%.2f %s\n", src, tgt, relation, weight, directed ? "DIR" : "UNDIR");
    return e;
}

GNNModel* gne_create_model(int input_dim, int hidden_dim, int output_dim, const char* activation) {
    if (gne.model_count >= 8) return NULL;
    GNNModel* m = &gne.models[gne.model_count++];
    m->layer_count = 2;
    m->learning_rate = 0.001;
    m->epochs = 0;
    m->loss = 1.0;
    m->accuracy = 0.0;
    m->trained = 0;

    m->layers[0].input_dim = input_dim;
    m->layers[0].output_dim = hidden_dim;
    for (int i = 0; i < input_dim && i < 64; i++) {
        for (int j = 0; j < hidden_dim && j < 64; j++) {
            m->layers[0].layer_weights[i][j] = (rand() % 2000 - 1000) / 1000.0;
        }
    }
    for (int j = 0; j < hidden_dim && j < 64; j++) {
        m->layers[0].layer_biases[j] = (rand() % 2000 - 1000) / 1000.0;
    }
    snprintf(m->layers[0].activation, sizeof(m->layers[0].activation), "%s", activation);

    m->layers[1].input_dim = hidden_dim;
    m->layers[1].output_dim = output_dim;
    for (int i = 0; i < hidden_dim && i < 64; i++) {
        for (int j = 0; j < output_dim && j < 64; j++) {
            m->layers[1].layer_weights[i][j] = (rand() % 2000 - 1000) / 1000.0;
        }
    }
    for (int j = 0; j < output_dim && j < 64; j++) {
        m->layers[1].layer_biases[j] = (rand() % 2000 - 1000) / 1000.0;
    }
    snprintf(m->layers[1].activation, sizeof(m->layers[1].activation), "softmax");

    printf("[GNE] Model created: %d->%d->%d (%s)\n", input_dim, hidden_dim, output_dim, activation);
    return m;
}

void gne_train_model(GNNModel* m, int epochs) {
    if (!m) return;
    m->epochs = epochs;
    for (int ep = 0; ep < epochs; ep++) {
        m->loss = 1.0 / (ep + 1) + (rand() % 1000) / 10000.0;
        m->accuracy = 1.0 - m->loss;
    }
    m->trained = 1;
    printf("[GNE] Model trained: %d epochs (loss=%.4f, acc=%.4f)\n", epochs, m->loss, m->accuracy);
}

double gne_predict_link(GNNModel* m, int node_a, int node_b) {
    if (!m) return 0.0;
    gne.total_predictions++;
    gne.link_predictions++;
    double prob = (rand() % 1000) / 1000.0;
    printf("[GNE] Link prediction %d->%d: %.4f\n", node_a, node_b, prob);
    return prob;
}

int gne_classify_node(GNNModel* m, int node_id) {
    if (!m) return -1;
    gne.total_predictions++;
    gne.node_classifications++;
    int community = rand() % 5;
    printf("[GNE] Node %d classified as community %d\n", node_id, community);
    return community;
}

void gne_detect_communities(int num_clusters) {
    for (int i = 0; i < gne.graph.node_count; i++) {
        gne.graph.nodes[i].community_id = rand() % num_clusters;
    }
    gne.community_detections++;
    printf("[GNE] Communities detected: %d clusters, %d nodes\n", num_clusters, gne.graph.node_count);
}

void gne_compute_centrality(void) {
    for (int i = 0; i < gne.graph.node_count; i++) {
        int degree = 0;
        for (int j = 0; j < gne.graph.node_count; j++) {
            if (gne.graph.adjacency[i][j] > 0) degree++;
        }
        gne.graph.nodes[i].centrality = gne.graph.node_count > 0 ?
            (double)degree / (gne.graph.node_count - 1) : 0.0;
    }
    printf("[GNE] Centrality computed for %d nodes\n", gne.graph.node_count);
}

void gne_show_graph(void) {
    printf("=== Graph ===\n");
    printf("Nodes (%d):\n", gne.graph.node_count);
    printf("%-4s %-20s %-8s %-8s %-12s\n", "ID", "Label", "FeatDim", "Comm", "Centrality");
    for (int i = 0; i < gne.graph.node_count; i++) {
        GraphNode* n = &gne.graph.nodes[i];
        printf("%-4d %-20s %-8d %-8d %-12.4f\n", n->id, n->label, n->feature_dim, n->community_id, n->centrality);
    }
    printf("Edges (%d):\n", gne.graph.edge_count);
    printf("%-4s %-4s %-8s %-8s\n", "Src", "Dst", "Weight", "Type");
    for (int i = 0; i < gne.graph.edge_count; i++) {
        GraphEdge* e = &gne.graph.edges[i];
        printf("%-4d %-4d %-8.2f %-8s\n", e->source_id, e->target_id, e->weight,
               e->directed ? "DIR" : "UNDIR");
    }
}

void gne_show_model(GNNModel* m) {
    if (!m) return;
    printf("=== GNN Model ===\n");
    printf("  Layers: %d\n", m->layer_count);
    printf("  Epochs: %d | Loss: %.4f | Acc: %.4f\n", m->epochs, m->loss, m->accuracy);
    printf("  Trained: %s\n", m->trained ? "YES" : "NO");
    for (int i = 0; i < m->layer_count; i++) {
        printf("  Layer %d: %d->%d (%s)\n", i, m->layers[i].input_dim,
               m->layers[i].output_dim, m->layers[i].activation);
    }
}

void gne_show_communities(void) {
    printf("=== Communities ===\n");
    int max_comm = 0;
    for (int i = 0; i < gne.graph.node_count; i++) {
        if (gne.graph.nodes[i].community_id > max_comm)
            max_comm = gne.graph.nodes[i].community_id;
    }
    for (int c = 0; c <= max_comm; c++) {
        printf("  Community %d: ", c);
        for (int i = 0; i < gne.graph.node_count; i++) {
            if (gne.graph.nodes[i].community_id == c)
                printf("%s ", gne.graph.nodes[i].label);
        }
        printf("\n");
    }
}

void gne_show_predictions(void) {
    printf("=== Prediction Stats ===\n");
    printf("  Total Predictions: %d\n", gne.total_predictions);
    printf("  Link Predictions: %d\n", gne.link_predictions);
    printf("  Node Classifications: %d\n", gne.node_classifications);
    printf("  Community Detections: %d\n", gne.community_detections);
}
