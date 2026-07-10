/**
 * hardware_opt.h — Hardware Optimization
 *
 * GPU acceleration, FPGA support, and ARM optimization.
 */
#ifndef ARCANIS_HARDWARE_OPT_H
#define ARCANIS_HARDWARE_OPT_H

#include <arcanis/types.h>

#define HW_MAX_GPUS        8
#define HW_MAX_FPGAS       4
#define HW_MAX_ACCELS      16
#define HW_MAX_NAME        64
#define HW_MAX_MEMORY      (4ULL * 1024 * 1024 * 1024)  /* 4GB */

typedef enum {
    GPU_VENDOR_NVIDIA,
    GPU_VENDOR_AMD,
    GPU_VENDOR_INTEL,
    GPU_VENDOR_ARM
} gpu_vendor_t;

typedef enum {
    GPU_STATE_IDLE,
    GPU_STATE_ACTIVE,
    GPU_STATE_ERROR
} gpu_state_t;

typedef enum {
    ACCEL_TYPE_GPU,
    ACCEL_TYPE_FPGA,
    ACCEL_TYPE_DSP,
    ACCEL_TYPE_NPU,
    ACCEL_TYPE_VPU
} accel_type_t;

/* ---- GPU ---- */

typedef struct {
    uint32_t id;
    char name[HW_MAX_NAME];
    gpu_vendor_t vendor;
    gpu_state_t state;
    uint32_t pci_id;
    uint32_t cuda_cores;
    uint32_t compute_units;
    uint64_t memory_size;
    uint64_t memory_used;
    uint32_t clock_mhz;
    uint32_t temperature;
    uint32_t power_usage;
    float    utilization;
    char driver[64];
    char firmware[64];
    int  initialized;
} gpu_device_t;

typedef struct {
    uint32_t gpu_id;
    uint32_t grid_x, grid_y, grid_z;
    uint32_t block_x, block_y, block_z;
    uint32_t shared_mem;
    uint32_t registers;
} gpu_kernel_config_t;

typedef struct {
    char name[64];
    uint32_t* data;
    uint32_t size;
    int on_gpu;
} gpu_buffer_t;

/* ---- FPGA ---- */

typedef enum {
    FPGA_STATE_UNCONFIGURED,
    FPGA_STATE_CONFIGURED,
    FPGA_STATE_RUNNING,
    FPGA_STATE_ERROR
} fpga_state_t;

typedef struct {
    uint32_t id;
    char name[HW_MAX_NAME];
    fpga_state_t state;
    uint32_t logic_cells;
    uint32_t dsp_slices;
    uint32_t bram_kb;
    uint32_t frequency_mhz;
    uint32_t power_mw;
    char bitstream[256];
    int configured;
    uint64_t utilization;
} fpga_device_t;

typedef struct {
    char name[64];
    uint32_t input_size;
    uint32_t output_size;
    uint32_t latency;
    uint32_t throughput;
    int (*process)(const uint8_t* in, uint8_t* out, uint32_t size);
} fpga_accelerator_t;

/* ---- ARM Optimization ---- */

typedef enum {
    ARM_CORTEX_A,
    ARM_CORTEX_M,
    ARM_NEON,
    ARM_SVE
} arm_feature_t;

typedef struct {
    uint32_t id;
    char name[HW_MAX_NAME];
    arm_feature_t features[16];
    uint32_t num_features;
    uint32_t cores;
    uint32_t frequency_mhz;
    uint32_t cache_l1_kb;
    uint32_t cache_l2_kb;
    uint32_t cache_l3_kb;
    int  neon_support;
    int  sve_support;
    char isa_version[32];
} arm_processor_t;

/* ---- Main Hardware Manager ---- */

typedef struct {
    gpu_device_t gpus[HW_MAX_GPUS];
    uint32_t num_gpus;

    fpga_device_t fpgas[HW_MAX_FPGAS];
    uint32_t num_fpgas;

    arm_processor_t arm_cpus[4];
    uint32_t num_arm_cpus;

    accel_type_t accelerators[HW_MAX_ACCELS];
    uint32_t num_accelerators;
} hardware_manager_t;

/* Initialize hardware manager */
void hw_init(hardware_manager_t* mgr);

/* ---- GPU Operations ---- */
int   hw_detect_gpus(hardware_manager_t* mgr);
int   hw_init_gpu(hardware_manager_t* mgr, uint32_t gpu_id);
int   hw_gpu_allocate_memory(hardware_manager_t* mgr, uint32_t gpu_id,
                             uint64_t size, gpu_buffer_t* buf);
int   hw_gpu_free_memory(hardware_manager_t* mgr, gpu_buffer_t* buf);
int   hw_gpu_memcpy_to_device(hardware_manager_t* mgr, gpu_buffer_t* buf,
                              const void* host_data, uint64_t size);
int   hw_gpu_memcpy_from_device(hardware_manager_t* mgr, gpu_buffer_t* buf,
                                void* host_data, uint64_t size);
int   hw_gpu_launch_kernel(hardware_manager_t* mgr, uint32_t gpu_id,
                           const gpu_kernel_config_t* config);
int   hw_gpu_synchronize(hardware_manager_t* mgr, uint32_t gpu_id);
int   hw_gpu_get_info(hardware_manager_t* mgr, uint32_t gpu_id, char* buf, uint32_t buf_len);
int   hw_gpu_get_stats(hardware_manager_t* mgr, uint32_t gpu_id, char* buf, uint32_t buf_len);
int   hw_list_gpus(hardware_manager_t* mgr, char* buf, uint32_t buf_len);

/* ---- FPGA Operations ---- */
int   hw_detect_fpgas(hardware_manager_t* mgr);
int   hw_fpga_configure(hardware_manager_t* mgr, uint32_t fpga_id, const char* bitstream);
int   hw_fpga_deconfigure(hardware_manager_t* mgr, uint32_t fpga_id);
int   hw_fpga_register_accelerator(hardware_manager_t* mgr, uint32_t fpga_id,
                                   const fpga_accelerator_t* accel);
int   hw_fpga_execute(hardware_manager_t* mgr, uint32_t fpga_id,
                      const char* accel_name, const uint8_t* input,
                      uint8_t* output, uint32_t size);
int   hw_fpga_get_info(hardware_manager_t* mgr, uint32_t fpga_id, char* buf, uint32_t buf_len);
int   hw_list_fpgas(hardware_manager_t* mgr, char* buf, uint32_t buf_len);

/* ---- ARM Operations ---- */
int   hw_detect_arm(hardware_manager_t* mgr);
int   hw_arm_enable_neon(hardware_manager_t* mgr, uint32_t cpu_id);
int   hw_arm_enable_sve(hardware_manager_t* mgr, uint32_t cpu_id);
int   hw_arm_get_info(hardware_manager_t* mgr, uint32_t cpu_id, char* buf, uint32_t buf_len);

/* ---- Accelerator Operations ---- */
int   hw_register_accelerator(hardware_manager_t* mgr, accel_type_t type, const char* name);
int   hw_accel_execute(hardware_manager_t* mgr, uint32_t accel_id,
                       const void* input, void* output, uint32_t size);
int   hw_list_accelerators(hardware_manager_t* mgr, char* buf, uint32_t buf_len);

#endif
