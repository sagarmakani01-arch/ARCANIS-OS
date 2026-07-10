/**
 * mobile.h — Mobile Device Support
 *
 * Mobile device management, touch input, sensors, and battery.
 */
#ifndef ARCANIS_MOBILE_H
#define ARCANIS_MOBILE_H

#include <arcanis/types.h>

#define MOBILE_MAX_DEVICES    8
#define MOBILE_MAX_SENSORS    32
#define MOBILE_MAX_APPS       64
#define MOBILE_MAX_NAME       64
#define MOBILE_MAX_GESTURES   16

typedef enum {
    DEVICE_PHONE,
    DEVICE_TABLET,
    DEVICE_WEARABLE,
    DEVICE_TV,
    DEVICE_IOT
} mobile_device_type_t;

typedef enum {
    SENSOR_ACCEL,
    SENSOR_GYRO,
    SENSOR_MAG,
    SENSOR_LIGHT,
    SENSOR_PROXIMITY,
    SENSOR_BARO,
    SENSOR_TEMP,
    SENSOR_HUMIDITY
} sensor_type_t;

typedef struct {
    float x, y, z;
    uint64_t timestamp;
} sensor_data_t;

typedef struct {
    uint32_t id;
    char name[MOBILE_MAX_NAME];
    sensor_type_t type;
    int enabled;
    uint32_t sampling_rate;
    sensor_data_t last_reading;
    uint64_t total_readings;
} mobile_sensor_t;

typedef struct {
    uint32_t id;
    float x, y;
    float pressure;
    uint32_t timestamp;
    int multi_touch;
    int gesture;
} touch_event_t;

typedef struct {
    uint32_t id;
    char name[32];
    uint32_t fingers;
    float min_x, min_y;
    float max_x, max_y;
    int recognized;
} touch_gesture_t;

typedef struct {
    uint32_t id;
    char name[MOBILE_MAX_NAME];
    mobile_device_type_t type;
    char model[64];
    char manufacturer[64];
    char os_version[32];
    uint32_t screen_width;
    uint32_t screen_height;
    uint32_t dpi;
    float battery_level;
    int battery_charging;
    uint32_t battery_temp;
    float cpu_usage;
    uint64_t memory_total;
    uint64_t memory_used;
    uint32_t storage_total;
    uint32_t storage_used;
    int wifi_connected;
    int bluetooth_enabled;
    int cellular_connected;
    char ip_address[16];
    mobile_sensor_t sensors[MOBILE_MAX_SENSORS];
    uint32_t num_sensors;
    touch_gesture_t gestures[MOBILE_MAX_GESTURES];
    uint32_t num_gestures;
} mobile_device_t;

typedef struct {
    mobile_device_t devices[MOBILE_MAX_DEVICES];
    uint32_t num_devices;
    uint32_t next_id;
} mobile_manager_t;

/* Initialize mobile manager */
void mobile_init(mobile_manager_t* mgr);

/* Device management */
int   mobile_register_device(mobile_manager_t* mgr, const char* name,
                            mobile_device_type_t type, const char* model);
int   mobile_unregister_device(mobile_manager_t* mgr, uint32_t device_id);
int   mobile_list_devices(mobile_manager_t* mgr, char* buf, uint32_t buf_len);
int   mobile_get_device_info(mobile_manager_t* mgr, uint32_t device_id, char* buf, uint32_t buf_len);

/* Sensor management */
int   mobile_enable_sensor(mobile_manager_t* mgr, uint32_t device_id, sensor_type_t sensor);
int   mobile_disable_sensor(mobile_manager_t* mgr, uint32_t device_id, sensor_type_t sensor);
int   mobile_read_sensor(mobile_manager_t* mgr, uint32_t device_id, sensor_type_t sensor,
                         sensor_data_t* data);
int   mobile_set_sampling_rate(mobile_manager_t* mgr, uint32_t device_id,
                               sensor_type_t sensor, uint32_t rate_hz);

/* Touch/Gesture */
int   mobile_register_gesture(mobile_manager_t* mgr, uint32_t device_id,
                              const touch_gesture_t* gesture);
int   mobile_process_touch(mobile_manager_t* mgr, uint32_t device_id,
                           const touch_event_t* event);
int   mobile_recognize_gesture(mobile_manager_t* mgr, uint32_t device_id,
                               const touch_event_t* events, uint32_t count,
                               char* gesture_name);

/* Battery management */
int   mobile_get_battery_info(mobile_manager_t* mgr, uint32_t device_id,
                              float* level, int* charging, uint32_t* temp);
int   mobile_set_power_mode(mobile_manager_t* mgr, uint32_t device_id, const char* mode);

/* Display */
int   mobile_set_brightness(mobile_manager_t* mgr, uint32_t device_id, uint32_t level);
int   mobile_set_orientation(mobile_manager_t* mgr, uint32_t device_id, const char* orientation);
int   mobile_set_resolution(mobile_manager_t* mgr, uint32_t device_id,
                            uint32_t width, uint32_t height);

/* Connectivity */
int   mobile_connect_wifi(mobile_manager_t* mgr, uint32_t device_id, const char* ssid);
int   mobile_disconnect_wifi(mobile_manager_t* mgr, uint32_t device_id);
int   mobile_enable_bluetooth(mobile_manager_t* mgr, uint32_t device_id);
int   mobile_disable_bluetooth(mobile_manager_t* mgr, uint32_t device_id);

#endif
