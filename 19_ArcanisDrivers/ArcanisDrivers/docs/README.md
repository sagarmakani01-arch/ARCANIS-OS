# ArcanisDrivers

Hardware Communication Layers for ArcanisOS

## Overview

ArcanisDrivers provides a complete driver framework for hardware communication in ArcanisOS. The architecture is designed for safe execution, modularity, and hardware independence.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                      │
├─────────────────────────────────────────────────────────┤
│                      Drivers                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ Keyboard │  │  Mouse   │  │ Display  │  │ Storage  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│  ┌──────────┐                                          │
│  │ Network  │                                          │
│  └──────────┘                                          │
├─────────────────────────────────────────────────────────┤
│              Hardware Abstraction Layer (HAL)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ I/O Ports│  │ Memory   │  │   IRQ    │  │  Timer   ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
├─────────────────────────────────────────────────────────┤
│                 Plug-and-Play System                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │   PCI    │  │   ISA    │  │   USB    │              │
│  └──────────┘  └──────────┘  └──────────┘              │
├─────────────────────────────────────────────────────────┤
│                   Core Framework                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Events  │  │ Memory   │  │ Ring Buf │              │
│  └──────────┘  └──────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────┘
```

## Components

### Core Framework (`src/core/`)

- **driver.c**: Base driver and device management
- **driver_event.c**: Event system for driver communication

### Hardware Abstraction Layer (`src/hal/`)

- **hal.c**: Platform-independent hardware access

### Plug-and-Play System (`src/pnp/`)

- **pnp.c**: Device enumeration and driver matching

### Utilities (`src/utils/`)

- **driver_memory.c**: Memory pool management
- **driver_ringbuffer.c**: Ring buffer for data streaming

### Drivers (`src/drivers/`)

- **keyboard.c**: PS/2 keyboard driver
- **mouse.c**: PS/2 mouse driver
- **display.c**: VGA display driver
- **storage.c**: ATA/IDE storage driver
- **network.c**: NE2000 network driver

## Building

### Prerequisites

- CMake 3.10+
- C11 compatible compiler
- Windows SDK (for platform-specific I/O)

### Build Commands

```bash
# Create build directory
mkdir build && cd build

# Configure
cmake ..

# Build
cmake --build .

# Run tests
./arcanis_test
```

### CMake Options

```bash
cmake -DBUILD_EXAMPLES=ON ..    # Build example programs
cmake -DBUILD_TESTS=ON ..      # Build test programs
cmake -DCMAKE_BUILD_TYPE=Release ..  # Release build
```

## Driver API

### Creating a Driver

```c
#include "arcanis_drivers.h"

// Define driver operations
static DriverOps my_driver_ops = {
    .init = my_init,
    .shutdown = my_shutdown,
    .probe = my_probe,
    .attach = my_attach,
    .detach = my_detach
};

// Create and register driver
Driver my_driver;
driver_create(&my_driver, "my_driver", DRIVER_TYPE_INPUT, &my_driver_ops);
driver_register(&my_driver);
```

### Device Operations

```c
// Open device
device->ops->open(device);

// Read data
size_t bytes_read;
device->ops->read(device, buffer, offset, length, &bytes_read);

// Write data
device->ops->write(device, buffer, offset, length, &bytes_written);

// Close device
device->ops->close(device);
```

### Event System

```c
// Subscribe to events
EventDispatcher dispatcher;
event_dispatcher_init(&dispatcher);

uint32_t listener_id;
event_subscribe(&dispatcher, my_callback, user_data, &listener_id);

// Emit events
DriverEvent event = {
    .type = EVENT_DEVICE_CONNECTED,
    .source = device
};
event_emit(&dispatcher, &event);

// Unsubscribe
event_unsubscribe(&dispatcher, listener_id);
```

### HAL Usage

```c
// Initialize HAL
HALContext hal;
hal_init(&hal);

// I/O operations
uint8_t value;
hal_io_read(&hal, port, &value);
hal_io_write(&hal, port, value);

// IRQ handling
hal_irq_enable(&hal, irq_num);
hal_irq_register(&hal, irq_num, handler, data);

// Memory mapping
void* virt_addr;
hal_memory_map(&hal, phys_addr, size, &virt_addr);
```

## Keyboard Driver

```c
KeyboardDriver kbd;
keyboard_init_driver(&kbd, &hal);

// Set callback for key events
keyboard_set_callback(&kbd, on_key_event, NULL);

// Check key state
if (keyboard_is_key_pressed(&kbd, KEY_ENTER)) {
    // Enter key pressed
}

// Get modifiers
bool shift, ctrl, alt, gui;
keyboard_get_modifiers(&kbd, &shift, &ctrl, &alt, &gui);
```

## Mouse Driver

```c
MouseDriver mouse;
mouse_init_driver(&mouse, &hal);

// Set callback
mouse_set_callback(&mouse, on_mouse_event, NULL);

// Get position
int32_t x, y;
mouse_get_position(&mouse, &x, &y);

// Set bounds
mouse_set_bounds(&mouse, 0, 0, 1024, 768);

// Check buttons
if (mouse_is_button_pressed(&mouse, MOUSE_BUTTON_LEFT)) {
    // Left button pressed
}
```

## Display Driver

```c
DisplayDriver display;
display_init_driver(&display, &hal);

// Set mode
display_set_mode(&display, DISPLAY_MODE_GFX_640x480);

// Clear screen
Color bg = display_make_color_rgb(0, 0, 0);
display_clear(&display, bg);

// Draw pixel
Color red = display_make_color_rgb(255, 0, 0);
display_set_pixel(&display, 100, 100, red);

// Draw rectangle
Rect rect = { .x = 50, .y = 50, .width = 200, .height = 100 };
display_fill_rect(&display, rect, red);

// Flush to screen
display_flush(&display);
```

## Storage Driver

```c
StorageDriver storage;
storage_init_driver(&storage, &hal, 0x1F0, 0x3F6, 0);

// Identify drive
storage_identify(&storage);

// Get info
StorageInfo info;
storage_get_info(&storage, &info);
printf("Drive: %s\n", info.model);

// Read sectors
uint8_t buffer[512];
storage_read_sectors(&storage, 0, 1, buffer);

// Write sectors
storage_write_sectors(&storage, 0, 1, buffer);
```

## Network Driver

```c
NetworkDriver net;
network_init_driver(&net, &hal, 0x300, 10);

// Set callback
network_set_callback(&net, on_net_event, NULL);

// Configure
network_set_ip(&net, ip_addr, subnet, gateway);

// Get MAC
uint8_t mac[6];
network_get_mac(&net, mac);

// Send packet
network_send_packet(&net, packet_data, packet_len);
```

## Utilities

### Ring Buffer

```c
RingBuffer rb;
uint8_t data[1024];
ringbuffer_init(&rb, data, sizeof(data));

// Write data
size_t written;
ringbuffer_write(&rb, input_data, len, &written);

// Read data
size_t read;
ringbuffer_read(&rb, output_data, len, &read);
```

### Memory Pool

```c
MemoryManager mgr;
memory_init(&mgr);

uint8_t pool[4096];
memory_pool_create(&mgr, pool, sizeof(pool), 64);

// Allocate
void* ptr = memory_alloc(&mgr, 64);

// Free
memory_free(&mgr, ptr);
```

## File Structure

```
ArcanisDrivers/
├── include/
│   ├── drivers/
│   │   ├── driver.h
│   │   ├── driver_event.h
│   │   ├── keyboard.h
│   │   ├── mouse.h
│   │   ├── display.h
│   │   ├── storage.h
│   │   └── network.h
│   ├── hal/
│   │   └── hal.h
│   ├── pnp/
│   │   └── pnp.h
│   ├── utils/
│   │   ├── driver_memory.h
│   │   └── driver_ringbuffer.h
│   └── arcanis_drivers.h
├── src/
│   ├── core/
│   │   ├── driver.c
│   │   └── driver_event.c
│   ├── hal/
│   │   └── hal.c
│   ├── pnp/
│   │   └── pnp.c
│   ├── drivers/
│   │   ├── keyboard.c
│   │   ├── mouse.c
│   │   ├── display.c
│   │   ├── storage.c
│   │   └── network.c
│   ├── utils/
│   │   ├── driver_memory.c
│   │   └── driver_ringbuffer.c
│   └── arcanis_drivers.c
├── examples/
│   └── main.c
├── tests/
│   └── test_main.c
└── CMakeLists.txt
```

## Design Principles

1. **Safe Execution**: All driver operations return status codes
2. **Modular Design**: Drivers can be loaded/unloaded independently
3. **Hardware Independence**: HAL abstracts platform-specific operations
4. **Event-Driven**: Asynchronous event system for driver communication
5. **Resource Management**: Proper memory pooling and buffer management

## License

Part of the ArcanisOS project.
