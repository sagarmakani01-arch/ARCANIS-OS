#include "arcanis_drivers.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name) static void test_##name(void)
#define RUN_TEST(name) do { \
    printf("Running test: %s...", #name); \
    test_##name(); \
    printf(" PASSED\n"); \
    tests_passed++; \
} while(0)

#define ASSERT_TRUE(expr) do { \
    if (!(expr)) { \
        printf(" FAILED\n  Assert failed: %s at line %d\n", #expr, __LINE__); \
        tests_failed++; \
        return; \
    } \
} while(0)

#define ASSERT_EQUAL(a, b) do { \
    if ((a) != (b)) { \
        printf(" FAILED\n  Assert failed: %s == %s at line %d\n", #a, #b, __LINE__); \
        tests_failed++; \
        return; \
    } \
} while(0)

#define ASSERT_STR_EQUAL(a, b) do { \
    if (strcmp((a), (b)) != 0) { \
        printf(" FAILED\n  Assert failed: \"%s\" == \"%s\" at line %d\n", (a), (b), __LINE__); \
        tests_failed++; \
        return; \
    } \
} while(0)

TEST(driver_create_destroy) {
    Driver drv;
    DriverOps ops;
    memset(&ops, 0, sizeof(ops));

    DriverStatus status = driver_create(&drv, "test_driver", DRIVER_TYPE_INPUT, &ops);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_STR_EQUAL(drv.name, "test_driver");
    ASSERT_EQUAL(drv.type, DRIVER_TYPE_INPUT);
    ASSERT_EQUAL(drv.initialized, false);

    status = driver_destroy(&drv);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
}

TEST(driver_register_unregister) {
    Driver drv;
    DriverOps ops;
    memset(&ops, 0, sizeof(ops));

    driver_create(&drv, "test_reg", DRIVER_TYPE_DISPLAY, &ops);

    DriverStatus status = driver_register(&drv);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);

    Driver* found = driver_find_by_name("test_reg");
    ASSERT_TRUE(found != NULL);
    ASSERT_EQUAL(found, &drv);

    status = driver_unregister(&drv);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);

    found = driver_find_by_name("test_reg");
    ASSERT_TRUE(found == NULL);

    driver_destroy(&drv);
}

TEST(driver_find_by_type) {
    Driver drv;
    DriverOps ops;
    memset(&ops, 0, sizeof(ops));

    driver_create(&drv, "test_type", DRIVER_TYPE_STORAGE, &ops);
    driver_register(&drv);

    Driver* found = driver_find_by_type(DRIVER_TYPE_STORAGE);
    ASSERT_TRUE(found != NULL);

    found = driver_find_by_type(DRIVER_TYPE_NETWORK);
    ASSERT_TRUE(found == NULL);

    driver_unregister(&drv);
    driver_destroy(&drv);
}

TEST(device_create_destroy) {
    Driver drv;
    Device dev;
    DriverOps ops;
    memset(&ops, 0, sizeof(ops));

    driver_create(&drv, "test_dev_drv", DRIVER_TYPE_INPUT, &ops);

    DriverStatus status = device_create(&dev, "test_device", &drv);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_STR_EQUAL(dev.name, "test_device");
    ASSERT_EQUAL(dev.driver, &drv);
    ASSERT_EQUAL(drv.device_count, 1);

    status = device_destroy(&dev);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_EQUAL(drv.device_count, 0);

    driver_destroy(&drv);
}

TEST(event_dispatcher) {
    EventDispatcher dispatcher;
    event_dispatcher_init(&dispatcher);

    uint32_t listener_count = 0;
    DriverStatus status = event_subscribe(&dispatcher, NULL, NULL, &listener_count);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);

    status = event_unsubscribe(&dispatcher, listener_count);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
}

TEST(event_queue) {
    EventQueue queue;
    event_queue_init(&queue);

    ASSERT_TRUE(event_queue_empty(&queue));

    DriverEvent event1 = { .type = EVENT_DEVICE_CONNECTED };
    DriverStatus status = event_queue_push(&queue, &event1);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_TRUE(!event_queue_empty(&queue));

    DriverEvent event2;
    status = event_queue_pop(&queue, &event2);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_EQUAL(event2.type, EVENT_DEVICE_CONNECTED);
    ASSERT_TRUE(event_queue_empty(&queue));
}

TEST(memory_pool) {
    MemoryManager mgr;
    memory_init(&mgr);

    uint8_t pool_data[4096];
    DriverStatus status = memory_pool_create(&mgr, pool_data, sizeof(pool_data), 64);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);

    void* ptr1 = memory_alloc(&mgr, 64);
    ASSERT_TRUE(ptr1 != NULL);

    void* ptr2 = memory_alloc(&mgr, 64);
    ASSERT_TRUE(ptr2 != NULL);
    ASSERT_TRUE(ptr1 != ptr2);

    memory_free(&mgr, ptr1);
    memory_free(&mgr, ptr2);

    void* ptr3 = memory_alloc(&mgr, 128);
    ASSERT_TRUE(ptr3 != NULL);

    memory_free(&mgr, ptr3);
}

TEST(memory_aligned_alloc) {
    MemoryManager mgr;
    memory_init(&mgr);

    uint8_t pool_data[4096];
    memory_pool_create(&mgr, pool_data, sizeof(pool_data), 64);

    void* ptr = memory_alloc_aligned(&mgr, 64, 16);
    ASSERT_TRUE(ptr != NULL);
    ASSERT_EQUAL(((uintptr_t)ptr) % 16, 0);

    memory_free(&mgr, ptr);
}

TEST(ringbuffer_basic) {
    RingBuffer rb;
    uint8_t data[256];

    DriverStatus status = ringbuffer_init(&rb, data, sizeof(data));
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_TRUE(ringbuffer_empty(&rb));

    status = ringbuffer_push(&rb, 0x41);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_EQUAL(ringbuffer_count(&rb), 1);

    uint8_t byte;
    status = ringbuffer_pop(&rb, &byte);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_EQUAL(byte, 0x41);
    ASSERT_TRUE(ringbuffer_empty(&rb));
}

TEST(ringbuffer_write_read) {
    RingBuffer rb;
    uint8_t buf[256];
    ringbuffer_init(&rb, buf, sizeof(buf));

    const char* test_str = "Hello, Arcanis!";
    size_t written;
    DriverStatus status = ringbuffer_write(&rb, (const uint8_t*)test_str, strlen(test_str), &written);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_EQUAL(written, strlen(test_str));

    char read_buf[64];
    size_t read_len;
    status = ringbuffer_read(&rb, (uint8_t*)read_buf, strlen(test_str), &read_len);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_EQUAL(read_len, strlen(test_str));
    read_buf[read_len] = '\0';
    ASSERT_STR_EQUAL(read_buf, test_str);
}

TEST(ringbuffer_full) {
    RingBuffer rb;
    uint8_t data[8];
    ringbuffer_init(&rb, data, sizeof(data));

    for (int i = 0; i < 8; i++) {
        ringbuffer_push(&rb, (uint8_t)i);
    }

    ASSERT_TRUE(ringbuffer_full(&rb));

    DriverStatus status = ringbuffer_push(&rb, 0xFF);
    ASSERT_EQUAL(status, DRIVER_STATUS_NO_MEMORY);

    ringbuffer_flush(&rb);
    ASSERT_TRUE(ringbuffer_empty(&rb));
}

TEST(hal_init) {
    HALContext ctx;
    DriverStatus status = hal_init(&ctx);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_TRUE(ctx.initialized);

    HALInfo info;
    status = hal_get_info(&ctx, &info);
    ASSERT_EQUAL(status, DRIVER_STATUS_OK);
    ASSERT_EQUAL(info.magic, 0x41524348);

    hal_shutdown(&ctx);
    ASSERT_TRUE(!ctx.initialized);
}

TEST(status_strings) {
    ASSERT_STR_EQUAL(driver_status_str(DRIVER_STATUS_OK), "OK");
    ASSERT_STR_EQUAL(driver_status_str(DRIVER_STATUS_ERROR), "Error");
    ASSERT_STR_EQUAL(driver_status_str(DRIVER_STATUS_TIMEOUT), "Timeout");
    ASSERT_STR_EQUAL(driver_status_str(DRIVER_STATUS_NO_MEMORY), "No Memory");
}

TEST(type_strings) {
    ASSERT_STR_EQUAL(driver_type_str(DRIVER_TYPE_INPUT), "Input");
    ASSERT_STR_EQUAL(driver_type_str(DRIVER_TYPE_DISPLAY), "Display");
    ASSERT_STR_EQUAL(driver_type_str(DRIVER_TYPE_STORAGE), "Storage");
    ASSERT_STR_EQUAL(driver_type_str(DRIVER_TYPE_NETWORK), "Network");
}

TEST(network_utilities) {
    uint32_t ip = network_str_to_ip("192.168.1.100");
    ASSERT_EQUAL(ip, 0x6401A8C0);

    char ip_str[16];
    network_ip_to_str(ip, ip_str);
    ASSERT_STR_EQUAL(ip_str, "192.168.1.100");

    uint16_t checksum = network_calc_checksum("test", 4);
    ASSERT_TRUE(checksum != 0);

    uint8_t mac1[6] = {0x00, 0x11, 0x22, 0x33, 0x44, 0x55};
    uint8_t mac2[6] = {0x00, 0x11, 0x22, 0x33, 0x44, 0x55};
    uint8_t mac3[6] = {0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF};

    ASSERT_TRUE(network_cmp_mac(mac1, mac2));
    ASSERT_TRUE(!network_cmp_mac(mac1, mac3));

    uint8_t mac4[6];
    network_set_mac_addr(mac4, mac1);
    ASSERT_TRUE(network_cmp_mac(mac1, mac4));
}

TEST(display_colors) {
    Color c1 = display_make_color(255, 128, 64, 255);
    ASSERT_EQUAL(c1.red, 255);
    ASSERT_EQUAL(c1.green, 128);
    ASSERT_EQUAL(c1.blue, 64);
    ASSERT_EQUAL(c1.alpha, 255);

    Color c2 = display_make_color_rgb(100, 200, 50);
    ASSERT_EQUAL(c2.red, 100);
    ASSERT_EQUAL(c2.green, 200);
    ASSERT_EQUAL(c2.blue, 50);
    ASSERT_EQUAL(c2.alpha, 255);
}

TEST(version_check) {
    const char* version = arcanis_drivers_version();
    ASSERT_TRUE(version != NULL);
    ASSERT_TRUE(strlen(version) > 0);
}

int main(void) {
    printf("ArcanisDrivers Test Suite\n");
    printf("========================\n\n");

    RUN_TEST(driver_create_destroy);
    RUN_TEST(driver_register_unregister);
    RUN_TEST(driver_find_by_type);
    RUN_TEST(device_create_destroy);
    RUN_TEST(event_dispatcher);
    RUN_TEST(event_queue);
    RUN_TEST(memory_pool);
    RUN_TEST(memory_aligned_alloc);
    RUN_TEST(ringbuffer_basic);
    RUN_TEST(ringbuffer_write_read);
    RUN_TEST(ringbuffer_full);
    RUN_TEST(hal_init);
    RUN_TEST(status_strings);
    RUN_TEST(type_strings);
    RUN_TEST(network_utilities);
    RUN_TEST(display_colors);
    RUN_TEST(version_check);

    printf("\n========================\n");
    printf("Results: %d passed, %d failed\n", tests_passed, tests_failed);

    return tests_failed > 0 ? 1 : 0;
}
