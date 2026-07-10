#ifndef ARCANIS_BIOFS_H
#define ARCANIS_BIOFS_H

typedef enum {
    NUCLEOTIDE_A,  // Adenine
    NUCLEOTIDE_T,  // Thymine
    NUCLEOTIDE_G,  // Guanine
    NUCLEOTIDE_C   // Cytosine
} Nucleotide;

typedef struct {
    Nucleotide pairs[1024];
    int length;
    double stability;
    int redundancy_level;
} DnaStrand;

typedef struct {
    char name[64];
    DnaStrand strand;
    double health_score;
    int mutation_count;
    int auto_repair_count;
    int generation;
    double fitness;
} BioSequence;

typedef struct {
    char name[64];
    char encoded_data[4096];
    BioSequence sequences[32];
    int sequence_count;
    double entropy;
    double growth_rate;
    int auto_defrag_count;
} BioFile;

typedef struct {
    char name[64];
    BioFile files[128];
    int file_count;
    int directory_count;
    double organic_growth;
    int adaptive_depth;
    int predictive_cache_hits;
} BioDirectory;

typedef struct {
    BioDirectory root;
    int total_sequences;
    int total_mutations;
    int healing_events;
    double storage_efficiency;
    int evolutionary_cycles;
} BioFileSystem;

void biofs_init(void);
BioFile* biofs_create_file(const char* path, const char* data);
int biofs_write_dna(BioFile* f, const char* data);
char* biofs_read_dna(BioFile* f);
void biofs_repair(BioFile* f);
void biofs_evolve(int generations);
void biofs_defragment(void);
void biofs_show_health(void);
void biofs_show_tree(const char* path);
void biofs_show_genetics(void);
double biofs_calculate_entropy(BioFile* f);

#endif
