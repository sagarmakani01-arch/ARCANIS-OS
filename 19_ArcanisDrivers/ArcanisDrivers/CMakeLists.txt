cmake_minimum_required(VERSION 3.10)
project(ArcanisDrivers VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

set(SOURCES
    src/core/driver.c
    src/core/driver_event.c
    src/utils/driver_memory.c
    src/utils/driver_ringbuffer.c
    src/hal/hal.c
    src/pnp/pnp.c
    src/drivers/keyboard.c
    src/drivers/mouse.c
    src/drivers/display.c
    src/drivers/storage.c
    src/drivers/network.c
    src/arcanis_drivers.c
)

set(HEADERS
    include/drivers/driver.h
    include/drivers/driver_event.h
    include/drivers/keyboard.h
    include/drivers/mouse.h
    include/drivers/display.h
    include/drivers/storage.h
    include/drivers/network.h
    include/hal/hal.h
    include/pnp/pnp.h
    include/utils/driver_memory.h
    include/utils/driver_ringbuffer.h
    include/arcanis_drivers.h
)

add_library(arcanis_drivers STATIC ${SOURCES} ${HEADERS})

target_include_directories(arcanis_drivers PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

if(MSVC)
    target_compile_definitions(arcanis_drivers PRIVATE _WIN32)
    target_compile_options(arcanis_drivers PRIVATE /W4)
else()
    target_compile_options(arcanis_drivers PRIVATE -Wall -Wextra -pedantic)
endif()

option(BUILD_EXAMPLES "Build example programs" ON)
if(BUILD_EXAMPLES)
    add_executable(arcanis_example examples/main.c)
    target_link_libraries(arcanis_example arcanis_drivers)
endif()

option(BUILD_TESTS "Build test programs" ON)
if(BUILD_TESTS)
    add_executable(arcanis_test tests/test_main.c)
    target_link_libraries(arcanis_test arcanis_drivers)
endif()

install(TARGETS arcanis_drivers
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(FILES ${HEADERS}
    DESTINATION include/arcanis_drivers
)

set_target_properties(arcanis_drivers PROPERTIES
    VERSION ${PROJECT_VERSION}
    SOVERSION 1
    PUBLIC_HEADER "${HEADERS}"
)

message(STATUS "ArcanisDrivers v${PROJECT_VERSION}")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
