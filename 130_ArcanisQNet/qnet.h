#ifndef QNET_H
#define QNET_H

#include <stddef.h>

typedef struct {
    int id_a;
    int id_b;
    double entanglement;
    double fidelity;
    double distance_km;
    int measurements;
} QubitPair;

typedef struct {
    char id[32];
    char source_node[64];
    char dest_node[64];
    int qubits[8];
    char payload[1024];
    double teleportation_progress;
    int error_correction;
} QuantumPacket;

typedef struct {
    char id[32];
    char name[64];
    char location[64];
    int qubits_available;
    double fidelity;
    QubitPair entanglement_pairs[32];
    int pair_count;
    int quantum_memory;
    int active;
} QuantumNode;

typedef struct {
    char id[32];
    char key[256];
    int key_length;
    double bit_error_rate;
    double generated_at;
    int compromised;
    char nodes[2][64];
} QKDKey;

typedef struct {
    QuantumNode nodes[8];
    int node_count;
    QuantumPacket packets[32];
    int packet_count;
    QKDKey keys[16];
    int key_count;
    int total_entanglements;
    double network_fidelity;
    double quantum_throughput;
    int epr_pairs_created;
} QNet;

void qnet_init(QNet *net);
int qnet_add_node(QNet *net, const char *name, const char *location, int qubits);
int qnet_entangle(QNet *net, int node_a, int node_b);
int qnet_send_quantum(QNet *net, int src, int dst, const char *data);
int qnet_teleport(QNet *net, int packet_idx);
int qnet_generate_qkd_key(QNet *net, int node_a, int node_b);
double qnet_measure_entanglement(QNet *net, int pair_idx);
void qnet_show_nodes(QNet *net);
void qnet_show_entanglements(QNet *net);
void qnet_show_packets(QNet *net);
void qnet_show_keys(QNet *net);
void qnet_show_stats(QNet *net);

#endif /* QNET_H */
