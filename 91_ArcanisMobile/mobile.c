/**
 * mobile.c — Mobile Device Support Implementation
 *
 * Mobile device management, touch input, sensors, and battery.
 */
#include <arcanis/mobile.h>
#include <arcanis/string.h>
#include <arcanis/heap.h>
#include <stdio.h>

/* ---- Initialization ---- */

void mobile_init(mobile_manager_t* mgr) {
    if (!mgr) return;
    memset(mgr, 0, sizeof(mobile_manager_t));
    mgr->next_id = 1;
}

/* ---- Device management ---- */

static mobile_device_t* find_device(mobile_manager_t* mgr, uint32_t id) {
    for (uint32_t i = 0; i < mgr->num_devices; i++) {
        if (mgr->devices[i].id == id)
            return &mgr->devices[i];
    }
    return NULL;
}

int mobile_register_device(mobile_manager_t* mgr, const char* name,
                          mobile_device_type_t type, const char* model) {
    if (!mgr || !name) return -1;
    if (mgr->num_devices >= MOBILE_MAX_DEVICES) return -1;

    mobile_device_t* dev = &mgr->devices[mgr->num_devices];
    memset(dev, 0, sizeof(mobile_device_t));

    dev->id = mgr->next_id++;
    string_copy(dev->name, name, MOBILE_MAX_NAME);
    dev->type = type;
    if (model) string_copy(dev->model, model, 64);
    string_copy(dev->manufacturer, "Arcanis", 64);
    string_copy(dev->os_version, "2.1.0", 32);
    dev->screen_width = 1080;
    dev->screen_height = 1920;
    dev->dpi = 420;
    dev->battery_level = 85.0;
    dev->battery_charging = 0;
    dev->memory_total = 8ULL * 1024 * 1024 * 1024;
    dev->memory_used = 3ULL * 1024 * 1024 * 1024;
    dev->storage_total = 128ULL * 1024 * 1024 * 1024;
    dev->storage_used = 45ULL * 1024 * 1024 * 1024;

    /* Register default sensors */
    dev->num_sensors = 6;
    sensor_type_t default_sensors[] = {
        SENSOR_ACCEL, SENSOR_GYRO, SENSOR_MAG,
        SENSOR_LIGHT, SENSOR_PROXIMITY, SENSOR_TEMP
    };
    for (uint32_t i = 0; i < dev->num_sensors; i++) {
        dev->sensors[i].id = i + 1;
        dev->sensors[i].type = default_sensors[i];
        dev->sensors[i].enabled = 1;
        dev->sensors[i].sampling_rate = 60;
    }

    /* Register default gestures */
    dev->num_gestures = 4;
    const char* gesture_names[] = {"tap", "swipe", "pinch", "rotate"};
    for (uint32_t i = 0; i < dev->num_gestures; i++) {
        dev->gestures[i].id = i + 1;
        string_copy(dev->gestures[i].name, gesture_names[i], 32);
        dev->gestures[i].fingers = i < 2 ? 1 : 2;
    }

    mgr->num_devices++;
    printf("[MOBILE] Device '%s' registered (type=%d)\n", name, type);
    return (int)dev->id;
}

int mobile_unregister_device(mobile_manager_t* mgr, uint32_t device_id) {
    if (!mgr) return -1;

    for (uint32_t i = 0; i < mgr->num_devices; i++) {
        if (mgr->devices[i].id == device_id) {
            printf("[MOBILE] Device '%s' unregistered\n", mgr->devices[i].name);
            for (uint32_t j = i; j < mgr->num_devices - 1; j++)
                mgr->devices[j] = mgr->devices[j + 1];
            mgr->num_devices--;
            return 0;
        }
    }
    return -1;
}

int mobile_list_devices(mobile_manager_t* mgr, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    const char* type_names[] = {"Phone", "Tablet", "Wearable", "TV", "IoT"};
    uint32_t pos = 0;

    pos += snprintf(buf + pos, buf_len - pos, "MOBILE DEVICES: %u\n", mgr->num_devices);
    pos += snprintf(buf + pos, buf_len - pos, "ID  NAME            TYPE      MODEL           BATTERY\n");
    pos += snprintf(buf + pos, buf_len - pos, "------------------------------------------------------\n");

    for (uint32_t i = 0; i < mgr->num_devices && pos < buf_len - 150; i++) {
        mobile_device_t* d = &mgr->devices[i];
        pos += snprintf(buf + pos, buf_len - pos,
            "%-3u %-15s %-9s %-15s %.0f%%\n",
            d->id, d->name, type_names[d->type], d->model,
            d->battery_level);
    }

    return (int)pos;
}

int mobile_get_device_info(mobile_manager_t* mgr, uint32_t device_id, char* buf, uint32_t buf_len) {
    if (!mgr || !buf) return 0;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    const char* type_names[] = {"Phone", "Tablet", "Wearable", "TV", "IoT"};
    return snprintf(buf, buf_len,
        "Device: %s\n"
        "  Type: %s\n"
        "  Model: %s\n"
        "  Manufacturer: %s\n"
        "  OS Version: %s\n"
        "  Screen: %ux%u @ %u DPI\n"
        "  Battery: %.0f%% (%s)\n"
        "  Memory: %llu/%llu MB\n"
        "  Storage: %llu/%llu GB\n"
        "  Sensors: %u active\n"
        "  Gestures: %u registered\n",
        dev->name, type_names[dev->type], dev->model,
        dev->manufacturer, dev->os_version,
        dev->screen_width, dev->screen_height, dev->dpi,
        dev->battery_level, dev->battery_charging ? "charging" : "discharging",
        (unsigned long long)(dev->memory_used / (1024 * 1024)),
        (unsigned long long)(dev->memory_total / (1024 * 1024)),
        (unsigned long long)(dev->storage_used / (1024 * 1024 * 1024)),
        (unsigned long long)(dev->storage_total / (1024 * 1024 * 1024)),
        dev->num_sensors, dev->num_gestures);
}

/* ---- Sensor management ---- */

int mobile_enable_sensor(mobile_manager_t* mgr, uint32_t device_id, sensor_type_t sensor) {
    if (!mgr) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    for (uint32_t i = 0; i < dev->num_sensors; i++) {
        if (dev->sensors[i].type == sensor) {
            dev->sensors[i].enabled = 1;
            printf("[MOBILE] Sensor %d enabled\n", sensor);
            return 0;
        }
    }
    return -1;
}

int mobile_disable_sensor(mobile_manager_t* mgr, uint32_t device_id, sensor_type_t sensor) {
    if (!mgr) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    for (uint32_t i = 0; i < dev->num_sensors; i++) {
        if (dev->sensors[i].type == sensor) {
            dev->sensors[i].enabled = 0;
            printf("[MOBILE] Sensor %d disabled\n", sensor);
            return 0;
        }
    }
    return -1;
}

int mobile_read_sensor(mobile_manager_t* mgr, uint32_t device_id, sensor_type_t sensor,
                       sensor_data_t* data) {
    if (!mgr || !data) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    for (uint32_t i = 0; i < dev->num_sensors; i++) {
        if (dev->sensors[i].type == sensor) {
            /* Simulate sensor reading */
            data->x = (float)(rand() % 1000) / 100.0f;
            data->y = (float)(rand() % 1000) / 100.0f;
            data->z = (float)(rand() % 1000) / 100.0f;
            data->timestamp = 0;
            dev->sensors[i].last_reading = *data;
            dev->sensors[i].total_readings++;
            return 0;
        }
    }
    return -1;
}

int mobile_set_sampling_rate(mobile_manager_t* mgr, uint32_t device_id,
                             sensor_type_t sensor, uint32_t rate_hz) {
    if (!mgr) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    for (uint32_t i = 0; i < dev->num_sensors; i++) {
        if (dev->sensors[i].type == sensor) {
            dev->sensors[i].sampling_rate = rate_hz;
            printf("[MOBILE] Sensor %d sampling rate set to %u Hz\n", sensor, rate_hz);
            return 0;
        }
    }
    return -1;
}

/* ---- Touch/Gesture ---- */

int mobile_register_gesture(mobile_manager_t* mgr, uint32_t device_id,
                            const touch_gesture_t* gesture) {
    if (!mgr || !gesture) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;
    if (dev->num_gestures >= MOBILE_MAX_GESTURES) return -1;

    touch_gesture_t* g = &dev->gestures[dev->num_gestures++];
    memcpy(g, gesture, sizeof(touch_gesture_t));
    g->id = dev->num_gestures;

    printf("[MOBILE] Gesture '%s' registered\n", gesture->name);
    return 0;
}

int mobile_process_touch(mobile_manager_t* mgr, uint32_t device_id,
                         const touch_event_t* event) {
    if (!mgr || !event) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    printf("[MOBILE] Touch at (%.1f, %.1f) pressure=%.2f\n",
           event->x, event->y, event->pressure);
    return 0;
}

int mobile_recognize_gesture(mobile_manager_t* mgr, uint32_t device_id,
                             const touch_event_t* events, uint32_t count,
                             char* gesture_name) {
    if (!mgr || !events || !gesture_name) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    /* Simple gesture recognition */
    if (count == 1) {
        string_copy(gesture_name, "tap", 32);
    } else if (count > 1) {
        float dx = events[count - 1].x - events[0].x;
        float dy = events[count - 1].y - events[0].y;
        if (dx > 50) string_copy(gesture_name, "swipe_right", 32);
        else if (dx < -50) string_copy(gesture_name, "swipe_left", 32);
        else if (dy > 50) string_copy(gesture_name, "swipe_down", 32);
        else if (dy < -50) string_copy(gesture_name, "swipe_up", 32);
        else string_copy(gesture_name, "drag", 32);
    } else {
        string_copy(gesture_name, "unknown", 32);
    }

    printf("[MOBILE] Gesture recognized: %s\n", gesture_name);
    return 0;
}

/* ---- Battery management ---- */

int mobile_get_battery_info(mobile_manager_t* mgr, uint32_t device_id,
                            float* level, int* charging, uint32_t* temp) {
    if (!mgr) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    if (level) *level = dev->battery_level;
    if (charging) *charging = dev->battery_charging;
    if (temp) *temp = dev->battery_temp;
    return 0;
}

int mobile_set_power_mode(mobile_manager_t* mgr, uint32_t device_id, const char* mode) {
    if (!mgr || !mode) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    printf("[MOBILE] Power mode set to '%s'\n", mode);
    return 0;
}

/* ---- Display ---- */

int mobile_set_brightness(mobile_manager_t* mgr, uint32_t device_id, uint32_t level) {
    if (!mgr) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    printf("[MOBILE] Brightness set to %u%%\n", level);
    return 0;
}

int mobile_set_orientation(mobile_manager_t* mgr, uint32_t device_id, const char* orientation) {
    if (!mgr || !orientation) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    printf("[MOBILE] Orientation set to '%s'\n", orientation);
    return 0;
}

int mobile_set_resolution(mobile_manager_t* mgr, uint32_t device_id,
                          uint32_t width, uint32_t height) {
    if (!mgr) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    dev->screen_width = width;
    dev->screen_height = height;
    printf("[MOBILE] Resolution set to %ux%u\n", width, height);
    return 0;
}

/* ---- Connectivity ---- */

int mobile_connect_wifi(mobile_manager_t* mgr, uint32_t device_id, const char* ssid) {
    if (!mgr || !ssid) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    dev->wifi_connected = 1;
    string_copy(dev->ip_address, "192.168.1.100", 16);
    printf("[MOBILE] Connected to WiFi '%s'\n", ssid);
    return 0;
}

int mobile_disconnect_wifi(mobile_manager_t* mgr, uint32_t device_id) {
    if (!mgr) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    dev->wifi_connected = 0;
    printf("[MOBILE] WiFi disconnected\n");
    return 0;
}

int mobile_enable_bluetooth(mobile_manager_t* mgr, uint32_t device_id) {
    if (!mgr) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    dev->bluetooth_enabled = 1;
    printf("[MOBILE] Bluetooth enabled\n");
    return 0;
}

int mobile_disable_bluetooth(mobile_manager_t* mgr, uint32_t device_id) {
    if (!mgr) return -1;

    mobile_device_t* dev = find_device(mgr, device_id);
    if (!dev) return -1;

    dev->bluetooth_enabled = 0;
    printf("[MOBILE] Bluetooth disabled\n");
    return 0;
}
