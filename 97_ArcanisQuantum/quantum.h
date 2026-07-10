/**
 * quantum.h — Quantum Computing Preparation
 *
 * Quantum gates, circuits, simulators, and hybrid quantum-classical computing.
 */
#ifndef ARCANIS_QUANTUM_H
#define ARCANIS_QUANTUM_H

#include <arcanis/types.h>

#define QC_MAX_QUBITS        64
#define QC_MAX_GATES         256
#define QC_MAX_CIRCUITS      32
#define QC_MAX_NAME          64
#define QC_MAX_SHOTS         10000

/* Complex number for quantum state amplitudes */
typedef struct {
    double real;
    double imag;
} qc_complex_t;

/* Quantum gate types */
typedef enum {
    QC_GATE_H,      /* Hadamard */
    QC_GATE_X,      /* Pauli-X (NOT) */
    QC_GATE_Y,      /* Pauli-Y */
    QC_GATE_Z,      /* Pauli-Z (phase) */
    QC_GATE_CX,     /* CNOT (controlled-X) */
    QC_GATE_CCX,    /* Toffoli (CCX) */
    QC_GATE_RX,     /* Rotation around X */
    QC_GATE_RY,     /* Rotation around Y */
    QC_GATE_RZ,     /* Rotation around Z */
    QC_GATE_T,      /* T gate (pi/8) */
    QC_GATE_S,      /* S gate (pi/4) */
    QC_GATE_MEASURE /* Measurement */
} qc_gate_type_t;

/* Quantum gate */
typedef struct {
    qc_gate_type_t type;
    uint32_t target;
    uint32_t control;
    double angle;
} qc_gate_t;

/* Quantum register (qubit state) */
typedef struct {
    uint32_t num_qubits;
    qc_complex_t amplitudes[1 << QC_MAX_QUBITS]; /* 2^n amplitudes */
} qc_register_t;

/* Quantum circuit */
typedef struct {
    char name[QC_MAX_NAME];
    qc_gate_t gates[QC_MAX_GATES];
    uint32_t num_gates;
    uint32_t num_qubits;
    int measured;
} qc_circuit_t;

/* Quantum simulator */
typedef struct {
    qc_circuit_t circuits[QC_MAX_CIRCUITS];
    uint32_t num_circuits;
    uint32_t num_qubits;
    uint32_t shots;
    uint64_t results[1 << QC_MAX_QUBITS]; /* Measurement counts */
    int statevector_mode;
} qc_simulator_t;

/* Initialize simulator */
void qc_init(qc_simulator_t* sim, uint32_t num_qubits);

/* Register operations */
void qc_reset(qc_register_t* reg);
void qc_init_state(qc_register_t* reg, uint32_t num_qubits);
void qc_h(qc_register_t* reg, uint32_t qubit);
void qc_x(qc_register_t* reg, uint32_t qubit);
void qc_y(qc_register_t* reg, uint32_t qubit);
void qc_z(qc_register_t* reg, uint32_t qubit);
void qc_cx(qc_register_t* reg, uint32_t control, uint32_t target);
void qc_rx(qc_register_t* reg, uint32_t qubit, double angle);
void qc_ry(qc_register_t* reg, uint32_t qubit, double angle);
void qc_rz(qc_register_t* reg, uint32_t qubit, double angle);

/* Circuit operations */
int   qc_create_circuit(qc_simulator_t* sim, const char* name);
int   qc_add_gate(qc_simulator_t* sim, const char* circuit_name,
                  qc_gate_type_t gate, uint32_t target, uint32_t control,
                  double angle);
int   qc_run_circuit(qc_simulator_t* sim, const char* circuit_name, uint32_t shots);
int   qc_get_result(qc_simulator_t* sim, const char* circuit_name,
                    char* buf, uint32_t buf_len);

/* Statevector */
int   qc_get_statevector(qc_simulator_t* sim, const char* circuit_name,
                         char* buf, uint32_t buf_len);

/* Utility */
void  qc_complex_multiply(qc_complex_t a, qc_complex_t b, qc_complex_t* result);
void  qc_complex_add(qc_complex_t a, qc_complex_t b, qc_complex_t* result);
double qc_probability(qc_complex_t amp);
int   qc_measure(qc_register_t* reg, uint32_t qubit);

#endif
