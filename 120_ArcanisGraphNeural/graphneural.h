#ifndef ARCANIS_GRAPHNEURAL_H
#define ARCANIS_GRAPHNEURAL_H

typedef struct {
    int id;
    char label[64];
    double features[128];
    int feature_dim;
    double embedding[64];
    int community_id;
    double centrality;
} GraphNode;

typedef struct {
    int source_id;
    int target_id;
    double weight;
    char relation[32];
    int directed;
    double message[64];
} GraphEdge;

typedef struct {
    GraphNode nodes[256];
    int node_count;
    GraphEdge edges[1024];
    int edge_count;
    double adjacency[256][256];
    double laplacian[256][256];
    int computed;
} Graph;

typedef struct {
    double layer_weights[64][64];
    double layer_biases[64];
    double activations[64];
    int input_dim;
    int output_dim;
    char activation[16];
} GNNLayer;

typedef struct {
    GNNLayer layers[8];
    int layer_count;
    double learning_rate;
    int epochs;
    double loss;
    double accuracy;
    int trained;
} GNNModel;

typedef struct {
    Graph graph;
    GNNModel models[8];
    int model_count;
    int total_predictions;
    int link_predictions;
    int node_classifications;
    int community_detections;
} GraphNeuralEngine;

void gne_init(void);
GraphNode* gne_add_node(const char* label, double* features, int dim);
GraphEdge* gne_add_edge(int src, int tgt, double weight, const char* relation, int directed);
GNNModel* gne_create_model(int input_dim, int hidden_dim, int output_dim, const char* activation);
void gne_train_model(GNNModel* m, int epochs);
double gne_predict_link(GNNModel* m, int node_a, int node_b);
int gne_classify_node(GNNModel* m, int node_id);
void gne_detect_communities(int num_clusters);
void gne_compute_centrality(void);
void gne_show_graph(void);
void gne_show_model(GNNModel* m);
void gne_show_communities(void);
void gne_show_predictions(void);

#endif
