#include "biofs.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>

static BioFileSystem bfs;

void biofs_init(void) {
    memset(&bfs, 0, sizeof(bfs));
    snprintf(bfs.root.name, 64, "/");
    bfs.total_sequences = 0;
    bfs.healing_events = 0;
    bfs.storage_efficiency = 1.0;
    bfs.evolutionary_cycles = 0;
    printf("Bio-File System initialized (DNA encoding v2.0)\n");
}

static Nucleotide char_to_nucleotide(char c) {
    int idx = (unsigned char)c % 4;
    return (Nucleotide)idx;
}

BioFile* biofs_create_file(const char* path, const char* data) {
    if (bfs.root.file_count >= 128) return NULL;
    BioFile* f = &bfs.root.files[bfs.root.file_count++];
    snprintf(f->name, 64, "%s", path);
    biofs_write_dna(f, data);
    bfs.total_sequences += f->sequence_count;
    printf("BioFile '%s' created (%d DNA sequences, entropy: %.3f)\n",
           path, f->sequence_count, f->entropy);
    return f;
}

int biofs_write_dna(BioFile* f, const char* data) {
    snprintf(f->encoded_data, 4096, "%s", data);
    int len = strlen(data);
    f->sequence_count = 0;
    for (int i = 0; i < len && f->sequence_count < 32; i += 4) {
        BioSequence* seq = &f->sequences[f->sequence_count++];
        snprintf(seq->name, 64, "seq-%d", f->sequence_count);
        seq->strand.length = 0;
        for (int j = 0; j < 8 && (i + j) < len; j++) {
            seq->strand.pairs[seq->strand.length++] = char_to_nucleotide(data[i + j]);
        }
        seq->strand.redundancy_level = 2;
        seq->health_score = 100.0;
        seq->generation = 1;
        seq->fitness = 1.0;
    }
    f->entropy = biofs_calculate_entropy(f);
    return f->sequence_count;
}

char* biofs_read_dna(BioFile* f) {
    static char buffer[4096];
    snprintf(buffer, 4096, "%s", f->encoded_data);
    return buffer;
}

void biofs_repair(BioFile* f) {
    for (int i = 0; i < f->sequence_count; i++) {
        if (f->sequences[i].health_score < 80.0) {
            f->sequences[i].health_score = 100.0;
            f->sequences[i].auto_repair_count++;
            bfs.healing_events++;
        }
    }
    printf("BioFile '%s' repaired (%d healing events)\n", f->name, bfs.healing_events);
}

void biofs_evolve(int generations) {
    for (int g = 0; g < generations; g++) {
        for (int i = 0; i < bfs.root.file_count; i++) {
            BioFile* f = &bfs.root.files[i];
            for (int j = 0; j < f->sequence_count; j++) {
                if ((rand() % 100) < 10) {
                    f->sequences[j].mutation_count++;
                    f->sequences[j].generation++;
                    f->sequences[j].fitness *= 1.0 + (rand() % 10) / 100.0;
                }
            }
        }
        bfs.evolutionary_cycles++;
    }
    printf("Evolved %d generations (fitness improved)\n", generations);
}

void biofs_show_health(void) {
    printf("\n=== Bio-FS Health ===\n");
    printf("Total sequences: %d\n", bfs.total_sequences);
    printf("Healing events: %d\n", bfs.healing_events);
    printf("Evolutionary cycles: %d\n", bfs.evolutionary_cycles);
    printf("Storage efficiency: %.1f%%\n", bfs.storage_efficiency * 100);
    printf("Files: %d | Dirs: %d\n", bfs.root.file_count, bfs.root.directory_count);
}

void biofs_show_genetics(void) {
    printf("\n=== Genetic Statistics ===\n");
    int total_muts = 0, total_repairs = 0;
    for (int i = 0; i < bfs.root.file_count; i++) {
        for (int j = 0; j < bfs.root.files[i].sequence_count; j++) {
            total_muts += bfs.root.files[i].sequences[j].mutation_count;
            total_repairs += bfs.root.files[i].sequences[j].auto_repair_count;
        }
    }
    printf("Total mutations: %d\n", total_muts);
    printf("Total repairs: %d\n", total_repairs);
    printf("Avg generation: %d\n", bfs.evolutionary_cycles);
}

double biofs_calculate_entropy(BioFile* f) {
    double counts[4] = {0};
    for (int i = 0; i < f->sequence_count; i++) {
        for (int j = 0; j < f->sequences[i].strand.length; j++) {
            counts[f->sequences[i].strand.pairs[j]]++;
        }
    }
    double total = counts[0] + counts[1] + counts[2] + counts[3];
    if (total == 0) return 0;
    double entropy = 0;
    for (int i = 0; i < 4; i++) {
        if (counts[i] > 0) {
            double p = counts[i] / total;
            entropy -= p * (p > 0 ? log2(p) : 0);
        }
    }
    return entropy;
}
