#ifndef ARCANIS_HOLO_H
#define ARCANIS_HOLO_H

typedef enum {
    HOLO_PIXEL,
    HOLO_CUBE,
    HOLO_SPHERE,
    HOLO_VOXEL,
    HOLO_TENSOR
} HoloUnitType;

typedef struct {
    double x, y, z;
    double amplitude;
    double phase;
    double frequency;
    int active;
} HoloPixel;

typedef struct {
    char id[32];
    char name[64];
    HoloUnitType type;
    HoloPixel pixels[512];
    int pixel_count;
    double volume[3];
    double resolution;
    double coherence;
    int computed;
} HoloField;

typedef struct {
    char id[32];
    char name[64];
    double data[4096];
    int data_size;
    HoloField encoding;
    int encoded;
    double density;
    double read_speed;
} HoloStorage;

typedef struct {
    char id[32];
    char name[64];
    HoloField input_field;
    HoloField output_field;
    double transform_matrix[16];
    char operation[32];
    int completed;
} HoloCompute;

typedef struct {
    HoloField fields[16];
    int field_count;
    HoloStorage storage_units[16];
    int storage_count;
    HoloCompute compute_units[8];
    int compute_count;
    int total_pixels;
    double fabric_coherence;
    int entanglement_enabled;
    int auto_optimize;
} HoloFabric;

void holo_init(void);
HoloField* holo_create_field(const char* name, HoloUnitType type, double resolution);
HoloPixel* holo_set_pixel(HoloField* f, double x, double y, double z, double amp);
HoloStorage* holo_encode_data(const char* name, double* data, int size);
int holo_decode_data(HoloStorage* s, double* output);
HoloCompute* holo_create_compute(const char* name, HoloField* input, const char* operation);
int holo_execute_compute(HoloCompute* c);
void holo_entangle(HoloField* a, HoloField* b);
void holo_show_fields(void);
void holo_show_storage(void);
void holo_show_fabric(void);
void holo_optimize(void);

#endif
