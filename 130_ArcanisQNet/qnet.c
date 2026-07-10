#include "qnet.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

#define MAX_NODES 10
#define MAX_PAIRS 20
#define MAX_PACKETS 30
#define MAX_KEYS 10

typedef struct {
    char id[32];
    char name[48];
    int qubits_available;
    double fidelity;
    int entangled_count;
} QuantumNode;

typedef struct {
    char id[32];
    char node_a[32];
    char node_b[32];
    double entanglement;
    double bell_state_measure;
} QubitPair;

typedef struct {
    char id[32];
    char source[32];
    char dest[32];
    char payload[128];
    int qubits_used;
    double teleportation_progress;
} QuantumPacket;

typedef struct {
    char id[32];
    char key_data[64];
    int key_length;
    double security_level;
} QKDKey;

typedef struct {
    QuantumNode nodes[MAX_NODES];
    int node_count;
    QubitPair pairs[MAX_PAIRS];
    int pair_count;
    QuantumPacket packets[MAX_PACKETS];
    int packet_count;
    QKDKey keys[MAX_KEYS];
    int key_count;
} QNet;

static QNet qn;

void qnet_init(void) {
    srand(time(NULL));
    memset(&qn, 0, sizeof(qn));
    printf("[QNET] Quantum network initialized\n");
}

void qnet_add_node(const char *name, int qubits) {
    if (qn.node_count >= MAX_NODES) { printf("[QNET] Node limit reached\n"); return; }
    QuantumNode *n = &qn.nodes[qn.node_count++];
    snprintf(n->id, sizeof(n->id), "NODE-%03d", qn.node_count);
    strncpy(n->name, name, sizeof(n->name) - 1);
    n->qubits_available = qubits;
    n->fidelity = 0.9 + (rand() % 100) / 1000.0;
    n->entangled_count = 0;
    printf("[QNET] Node '%s' (%s): %d qubits, fidelity %.3f\n", n->name, n->id, n->qubits_available, n->fidelity);
}

void qnet_entangle(const char *node_id_a, const char *node_id_b) {
    if (qn.pair_count >= MAX_PAIRS) { printf("[QNET] Pair limit reached\n"); return; }
    QubitPair *p = &qn.pairs[qn.pair_count++];
    snprintf(p->id, sizeof(p->id), "ENT-%03d", qn.pair_count);
    strncpy(p->node_a, node_id_a, sizeof(p->node_a) - 1);
    strncpy(p->node_b, node_id_b, sizeof(p->node_b) - 1);
    p->entanglement = 0.85 + (rand() % 150) / 1000.0;
    if (p->entanglement > 1.0) p->entanglement = 1.0;
    p->bell_state_measure = (rand() % 4) + 1;
    for (int i = 0; i < qn.node_count; i++) {
        if (strcmp(qn.nodes[i].id, node_id_a) == 0) qn.nodes[i].entangled_count++;
        if (strcmp(qn.nodes[i].id, node_id_b) == 0) qn.nodes[i].entangled_count++;
    }
    printf("[QNET] Entangled %s <-> %s (pair %s, e=%.3f)\n", node_id_a, node_id_b, p->id, p->entanglement);
}

void qnet_send_quantum(const char *src, const char *dest, const char *payload) {
    if (qn.packet_count >= MAX_PACKETS) { printf("[QNET] Packet limit reached\n"); return; }
    QuantumPacket *p = &qn.packets[qn.packet_count++];
    snprintf(p->id, sizeof(p->id), "PKT-%03d", qn.packet_count);
    strncpy(p->source, src, sizeof(p->source) - 1);
    strncpy(p->dest, dest, sizeof(p->dest) - 1);
    strncpy(p->payload, payload, sizeof(p->payload) - 1);
    p->qubits_used = rand() % 8 + 1;
    p->teleportation_progress = 0.0;
    printf("[QNET] Quantum packet %s: %s -> %s ('%s', %d qubits)\n",
           p->id, src, dest, payload, p->qubits_used);
}

void qnet_teleport(const char *packet_id) {
    for (int i = 0; i < qn.packet_count; i++) {
        if (strcmp(qn.packets[i].id, packet_id) == 0) {
            qn.packets[i].teleportation_progress = 1.0;
            printf("[QNET] Teleported packet %s successfully\n", packet_id);
            return;
        }
    }
    printf("[QNET] Packet %s not found\n", packet_id);
}

void qnet_generate_qkd_key(const char *node_a, const char *node_b) {
    if (qn.key_count >= MAX_KEYS) { printf("[QNET] Key limit reached\n"); return; }
    QKDKey *k = &qn.keys[qn.key_count++];
    snprintf(k->id, sizeof(k->id), "KEY-%03d", qn.key_count);
    k->key_length = rand() % 128 + 64;
    for (int i = 0; i < (int)sizeof(k->key_data) - 1; i++)
        k->key_data[i] = "01"[rand() % 2];
    k->key_data[sizeof(k->key_data) - 1] = 0;
    k->security_level = 0.95 + (rand() % 50) / 1000.0;
    if (k->security_level > 1.0) k->security_level = 1.0;
    printf("[QNET] QKD key %s generated for %s<->%s (%d bits, security %.3f)\n",
           k->id, node_a, node_b, k->key_length, k->security_level);
}

void qnet_show_nodes(void) {
    printf("\n=== QUANTUM NODES ===\n");
    printf("%-10s %-20s %-8s %-10s %-10s\n", "ID", "Name", "Qubits", "Fidelity", "Entangled");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < qn.node_count; i++)
        printf("%-10s %-20s %-8d %-10.3f %-10d\n",
               qn.nodes[i].id, qn.nodes[i].name,
               qn.nodes[i].qubits_available, qn.nodes[i].fidelity,
               qn.nodes[i].entangled_count);
}

void qnet_show_entanglements(void) {
    printf("\n=== ENTANGLEMENTS ===\n");
    printf("%-10s %-15s %-15s %-12s %-12s\n", "ID", "Node A", "Node B", "Entanglement", "Bell State");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < qn.pair_count; i++)
        printf("%-10s %-15s %-15s %-12.3f %-12.0f\n",
               qn.pairs[i].id, qn.pairs[i].node_a, qn.pairs[i].node_b,
               qn.pairs[i].entanglement, qn.pairs[i].bell_state_measure);
}

void qnet_show_packets(void) {
    printf("\n=== QUANTUM PACKETS ===\n");
    printf("%-10s %-15s %-15s %-20s %-8s %-12s\n", "ID", "Source", "Dest", "Payload", "Qubits", "Progress");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < qn.packet_count; i++)
        printf("%-10s %-15s %-15s %-20s %-8d %-12.2f\n",
               qn.packets[i].id, qn.packets[i].source, qn.packets[i].dest,
               qn.packets[i].payload, qn.packets[i].qubits_used,
               qn.packets[i].teleportation_progress);
}

void qnet_show_keys(void) {
    printf("\n=== QKD KEYS ===\n");
    printf("%-10s %-15s %-15s %-10s %-12s\n", "ID", "Key Data", "Length", "Security", "Status");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < qn.key_count; i++)
        printf("%-10s %-15s %-10d %-12.3f %s\n",
               qn.keys[i].id, qn.keys[i].key_data,
               qn.keys[i].key_length, qn.keys[i].security_level, "active");
}

void qnet_show_stats(void) {
    printf("\n=== QNET STATS ===\n");
    printf("Nodes: %d\n", qn.node_count);
    printf("Entanglement pairs: %d\n", qn.pair_count);
    printf("Packets transmitted: %d\n", qn.packet_count);
    printf("QKD keys generated: %d\n", qn.key_count);
}
