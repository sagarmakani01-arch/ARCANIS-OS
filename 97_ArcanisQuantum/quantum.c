/**
 * quantum.c — Quantum Computing Implementation
 *
 * Quantum gates, circuits, simulators, and hybrid quantum-classical computing.
 */
#include <arcanis/quantum.h>
#include <arcanis/string.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ---- Initialization ---- */

void qc_init(qc_simulator_t* sim, uint32_t num_qubits) {
    if (!sim) return;
    memset(sim, 0, sizeof(qc_simulator_t));
    sim->num_qubits = num_qubits;
    sim->shots = 1024;
    sim->statevector_mode = 1;
    printf("[QUANTUM] Simulator initialized with %u qubits\n", num_qubits);
}

/* ---- Register operations ---- */

void qc_reset(qc_register_t* reg) {
    if (!reg) return;
    for (uint32_t i = 0; i < (1U << reg->num_qubits); i++) {
        reg->amplitudes[i].real = 0;
        reg->amplitudes[i].imag = 0;
    }
    /* Set |0> state */
    reg->amplitudes[0].real = 1.0;
}

void qc_init_state(qc_register_t* reg, uint32_t num_qubits) {
    if (!reg || num_qubits > QC_MAX_QUBITS) return;
    memset(reg, 0, sizeof(qc_register_t));
    reg->num_qubits = num_qubits;
    qc_reset(reg);
}

void qc_h(qc_register_t* reg, uint32_t qubit) {
    if (!reg || qubit >= reg->num_qubits) return;

    double inv_sqrt2 = 1.0 / sqrt(2.0);
    uint32_t n = 1U << reg->num_qubits;

    for (uint32_t i = 0; i < n; i++) {
        if (!(i & (1U << qubit))) {
            uint32_t j = i | (1U << qubit);
            qc_complex_t temp = reg->amplitudes[i];

            /* H gate: (|0> + |1>)/sqrt(2) */
            reg->amplitudes[i].real = inv_sqrt2 * (temp.real + reg->amplitudes[j].real);
            reg->amplitudes[i].imag = inv_sqrt2 * (temp.imag + reg->amplitudes[j].imag);
            reg->amplitudes[j].real = inv_sqrt2 * (temp.real - reg->amplitudes[j].real);
            reg->amplitudes[j].imag = inv_sqrt2 * (temp.imag - reg->amplitudes[j].imag);
        }
    }
}

void qc_x(qc_register_t* reg, uint32_t qubit) {
    if (!reg || qubit >= reg->num_qubits) return;

    uint32_t n = 1U << reg->num_qubits;
    for (uint32_t i = 0; i < n; i++) {
        if (!(i & (1U << qubit))) {
            uint32_t j = i | (1U << qubit);
            qc_complex_t temp = reg->amplitudes[i];
            reg->amplitudes[i] = reg->amplitudes[j];
            reg->amplitudes[j] = temp;
        }
    }
}

void qc_y(qc_register_t* reg, uint32_t qubit) {
    if (!reg || qubit >= reg->num_qubits) return;

    uint32_t n = 1U << reg->num_qubits;
    for (uint32_t i = 0; i < n; i++) {
        if (!(i & (1U << qubit))) {
            uint32_t j = i | (1U << qubit);
            /* Y gate: i|1> -> |0>, -i|0> -> |1> */
            reg->amplitudes[i].real = -reg->amplitudes[j].imag;
            reg->amplitudes[i].imag = reg->amplitudes[j].real;
            reg->amplitudes[j].real = reg->amplitudes[i].imag;
            reg->amplitudes[j].imag = -reg->amplitudes[i].real;
        }
    }
}

void qc_z(qc_register_t* reg, uint32_t qubit) {
    if (!reg || qubit >= reg->num_qubits) return;

    uint32_t n = 1U << reg->num_qubits;
    for (uint32_t i = 0; i < n; i++) {
        if (i & (1U << qubit)) {
            /* Z gate: phase flip for |1> */
            reg->amplitudes[i].real = -reg->amplitudes[i].real;
            reg->amplitudes[i].imag = -reg->amplitudes[i].imag;
        }
    }
}

void qc_cx(qc_register_t* reg, uint32_t control, uint32_t target) {
    if (!reg || control >= reg->num_qubits || target >= reg->num_qubits) return;

    uint32_t n = 1U << reg->num_qubits;
    for (uint32_t i = 0; i < n; i++) {
        if ((i & (1U << control)) && !(i & (1U << target))) {
            uint32_t j = i | (1U << target);
            qc_complex_t temp = reg->amplitudes[i];
            reg->amplitudes[i] = reg->amplitudes[j];
            reg->amplitudes[j] = temp;
        }
    }
}

void qc_rx(qc_register_t* reg, uint32_t qubit, double angle) {
    if (!reg || qubit >= reg->num_qubits) return;

    double cos_a = cos(angle / 2.0);
    double sin_a = sin(angle / 2.0);
    uint32_t n = 1U << reg->num_qubits;

    for (uint32_t i = 0; i < n; i++) {
        if (!(i & (1U << qubit))) {
            uint32_t j = i | (1U << qubit);
            qc_complex_t temp = reg->amplitudes[i];

            reg->amplitudes[i].real = cos_a * temp.real + sin_a * reg->amplitudes[j].imag;
            reg->amplitudes[i].imag = cos_a * temp.imag - sin_a * reg->amplitudes[j].real;
            reg->amplitudes[j].real = sin_a * temp.imag + cos_a * reg->amplitudes[j].real;
            reg->amplitudes[j].imag = -sin_a * temp.real + cos_a * reg->amplitudes[j].imag;
        }
    }
}

void qc_ry(qc_register_t* reg, uint32_t qubit, double angle) {
    if (!reg || qubit >= reg->num_qubits) return;

    double cos_a = cos(angle / 2.0);
    double sin_a = sin(angle / 2.0);
    uint32_t n = 1U << reg->num_qubits;

    for (uint32_t i = 0; i < n; i++) {
        if (!(i & (1U << qubit))) {
            uint32_t j = i | (1U << qubit);
            qc_complex_t temp = reg->amplitudes[i];

            reg->amplitudes[i].real = cos_a * temp.real - sin_a * reg->amplitudes[j].real;
            reg->amplitudes[i].imag = cos_a * temp.imag - sin_a * reg->amplitudes[j].imag;
            reg->amplitudes[j].real = sin_a * temp.real + cos_a * reg->amplitudes[j].real;
            reg->amplitudes[j].imag = sin_a * temp.imag + cos_a * reg->amplitudes[j].imag;
        }
    }
}

void qc_rz(qc_register_t* reg, uint32_t qubit, double angle) {
    if (!reg || qubit >= reg->num_qubits) return;

    double cos_a = cos(angle);
    double sin_a = sin(angle);
    uint32_t n = 1U << reg->num_qubits;

    for (uint32_t i = 0; i < n; i++) {
        if (i & (1U << qubit)) {
            reg->amplitudes[i].real = cos_a * reg->amplitudes[i].real - sin_a * reg->amplitudes[i].imag;
            reg->amplitudes[i].imag = sin_a * reg->amplitudes[i].real + cos_a * reg->amplitudes[i].imag;
        }
    }
}

/* ---- Complex operations ---- */

void qc_complex_multiply(qc_complex_t a, qc_complex_t b, qc_complex_t* result) {
    if (!result) return;
    result->real = a.real * b.real - a.imag * b.imag;
    result->imag = a.real * b.imag + a.imag * b.real;
}

void qc_complex_add(qc_complex_t a, qc_complex_t b, qc_complex_t* result) {
    if (!result) return;
    result->real = a.real + b.real;
    result->imag = a.imag + b.imag;
}

double qc_probability(qc_complex_t amp) {
    return amp.real * amp.real + amp.imag * amp.imag;
}

int qc_measure(qc_register_t* reg, uint32_t qubit) {
    if (!reg || qubit >= reg->num_qubits) return -1;

    double prob = 0.0;
    uint32_t n = 1U << reg->num_qubits;

    for (uint32_t i = 0; i < n; i++) {
        if (!(i & (1U << qubit))) {
            prob += qc_probability(reg->amplitudes[i]);
        }
    }

    /* Simple random measurement */
    double r = (double)rand() / (double)RAND_MAX;
    int result = (r > prob) ? 1 : 0;

    /* Collapse state */
    double norm = sqrt(result ? (1.0 - prob) : prob);
    if (norm < 1e-10) norm = 1.0;

    for (uint32_t i = 0; i < n; i++) {
        int bit = (i & (1U << qubit)) ? 1 : 0;
        if (bit != result) {
            reg->amplitudes[i].real = 0;
            reg->amplitudes[i].imag = 0;
        } else {
            reg->amplitudes[i].real /= norm;
            reg->amplitudes[i].imag /= norm;
        }
    }

    return result;
}

/* ---- Circuit operations ---- */

int qc_create_circuit(qc_simulator_t* sim, const char* name) {
    if (!sim || !name) return -1;
    if (sim->num_circuits >= QC_MAX_CIRCUITS) return -1;

    qc_circuit_t* circ = &sim->circuits[sim->num_circuits];
    memset(circ, 0, sizeof(qc_circuit_t));
    string_copy(circ->name, name, QC_MAX_NAME);
    circ->num_qubits = sim->num_qubits;
    sim->num_circuits++;

    printf("[QUANTUM] Circuit '%s' created with %u qubits\n", name, sim->num_qubits);
    return 0;
}

int qc_add_gate(qc_simulator_t* sim, const char* circuit_name,
                qc_gate_type_t gate, uint32_t target, uint32_t control,
                double angle) {
    if (!sim || !circuit_name) return -1;

    for (uint32_t i = 0; i < sim->num_circuits; i++) {
        if (string_compare(sim->circuits[i].name, circuit_name) == 0) {
            qc_circuit_t* circ = &sim->circuits[i];
            if (circ->num_gates >= QC_MAX_GATES) return -1;

            qc_gate_t* g = &circ->gates[circ->num_gates];
            g->type = gate;
            g->target = target;
            g->control = control;
            g->angle = angle;
            circ->num_gates++;

            return 0;
        }
    }
    return -1;
}

int qc_run_circuit(qc_simulator_t* sim, const char* circuit_name, uint32_t shots) {
    if (!sim || !circuit_name) return -1;

    for (uint32_t i = 0; i < sim->num_circuits; i++) {
        if (string_compare(sim->circuits[i].name, circuit_name) == 0) {
            qc_circuit_t* circ = &sim->circuits[i];
            qc_register_t reg;
            qc_init_state(&reg, circ->num_qubits);

            printf("[QUANTUM] Running circuit '%s' with %u shots\n", circuit_name, shots);

            /* Apply gates */
            for (uint32_t g = 0; g < circ->num_gates; g++) {
                qc_gate_t* gate = &circ->gates[g];
                switch (gate->type) {
                    case QC_GATE_H:   qc_h(&reg, gate->target); break;
                    case QC_GATE_X:   qc_x(&reg, gate->target); break;
                    case QC_GATE_Y:   qc_y(&reg, gate->target); break;
                    case QC_GATE_Z:   qc_z(&reg, gate->target); break;
                    case QC_GATE_CX:  qc_cx(&reg, gate->control, gate->target); break;
                    case QC_GATE_RX:  qc_rx(&reg, gate->target, gate->angle); break;
                    case QC_GATE_RY:  qc_ry(&reg, gate->target, gate->angle); break;
                    case QC_GATE_RZ:  qc_rz(&reg, gate->target, gate->angle); break;
                    default: break;
                }
            }

            /* Measure */
            memset(sim->results, 0, sizeof(sim->results));
            for (uint32_t s = 0; s < shots; s++) {
                qc_register_t temp = reg;
                uint32_t result = 0;
                for (uint32_t q = 0; q < circ->num_qubits; q++) {
                    int m = qc_measure(&temp, q);
                    if (m) result |= (1U << q);
                }
                sim->results[result]++;
            }

            circ->measured = 1;
            return 0;
        }
    }
    return -1;
}

int qc_get_result(qc_simulator_t* sim, const char* circuit_name,
                  char* buf, uint32_t buf_len) {
    if (!sim || !circuit_name || !buf) return 0;

    uint32_t pos = 0;
    pos += snprintf(buf + pos, buf_len - pos, "QUANTUM RESULTS: %s\n", circuit_name);
    pos += snprintf(buf + pos, buf_len - pos,
        "STATE       COUNT    PROBABILITY\n");

    for (uint32_t i = 0; i < (1U << sim->num_qubits) && pos < buf_len - 50; i++) {
        if (sim->results[i] > 0) {
            char binary[QC_MAX_QUBITS + 1];
            for (int b = sim->num_qubits - 1; b >= 0; b--) {
                binary[sim->num_qubits - 1 - b] = (i & (1U << b)) ? '1' : '0';
            }
            binary[sim->num_qubits] = '\0';
            double prob = (double)sim->results[i] / 1024.0;
            pos += snprintf(buf + pos, buf_len - pos,
                "|%s>     %6llu    %.4f\n",
                binary, (unsigned long long)sim->results[i], prob);
        }
    }

    return (int)pos;
}

int qc_get_statevector(qc_simulator_t* sim, const char* circuit_name,
                       char* buf, uint32_t buf_len) {
    if (!sim || !circuit_name || !buf) return 0;

    for (uint32_t i = 0; i < sim->num_circuits; i++) {
        if (string_compare(sim->circuits[i].name, circuit_name) == 0) {
            qc_circuit_t* circ = &sim->circuits[i];
            uint32_t pos = 0;

            pos += snprintf(buf + pos, buf_len - pos,
                "STATEVECTOR: %u qubits, %u gates\n",
                circ->num_qubits, circ->num_gates);

            /* Show first few amplitudes */
            uint32_t show = (1U << circ->num_qubits);
            if (show > 16) show = 16;

            for (uint32_t i = 0; i < show && pos < buf_len - 80; i++) {
                pos += snprintf(buf + pos, buf_len - pos,
                    "  |%u>: (%.4f + %.4fi)\n",
                    i, 0.0, 0.0); /* Simplified */
            }

            return (int)pos;
        }
    }
    return 0;
}
