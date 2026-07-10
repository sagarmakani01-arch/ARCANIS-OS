#ifndef BIO_OS_H
#define BIO_OS_H

typedef enum {
    MOLECULE_DNA, MOLECULE_RNA, MOLECULE_PROTEIN, MOLECULE_LIPID, MOLECULE_CARBOHYDRATE
} BioMoleculeType;

typedef struct {
    char id[32];
    BioMoleculeType type;
    char sequence_data[1024];
    int length;
    double folding_energy;
    double stability;
    char function[64];
} BioSequence;

typedef struct {
    char id[32];
    char type[32];
    BioSequence sequences[8];
    int sequence_count;
    double energy_level;
    double replication_rate;
    double health;
    double age;
} BioCell;

typedef struct {
    BioCell cells[32];
    int cell_count;
    int total_sequences;
    double system_health;
    double evolution_rate;
    int bio_computing_ops;
    int protein_synthesis_active;
} BioSystem;

void bio_init(BioSystem *system);
void bio_create_cell(BioSystem *system, const char *type);
void bio_add_sequence(BioSystem *system, BioCell *cell, BioMoleculeType type, const char *data);
void bio_replicate(BioSystem *system, BioCell *cell);
void bio_compute(const BioSequence *seq, const char *operation);
void bio_show_cells(const BioSystem *system);
void bio_show_sequences(const BioSystem *system);
void bio_show_system(const BioSystem *system);

#endif
