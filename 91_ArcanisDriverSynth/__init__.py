"""91_ArcanisDriverSynth — Runtime driver synthesis from hardware specs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class HardwareSpec:
    device_type: str = ""
    vendor_id: int = 0
    product_id: int = 0
    name: str = ""
    bus: str = ""
    capabilities: list[str] = field(default_factory=list)
    registers: dict[str, int] = field(default_factory=dict)
    interrupts: list[int] = field(default_factory=list)
    dma_channels: list[int] = field(default_factory=list)
    io_ports: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class DriverTemplate:
    template_id: str = ""
    device_type: str = ""
    language: str = "c"
    init_code: str = ""
    read_code: str = ""
    write_code: str = ""
    irq_handler_code: str = ""
    shutdown_code: str = ""
    header_code: str = ""


@dataclass
class SynthesizedDriver:
    driver_name: str = ""
    device_name: str = ""
    language: str = "c"
    header: str = ""
    source: str = ""
    build_instructions: str = ""
    warnings: list[str] = field(default_factory=list)


class DriverTemplateLibrary:
    def __init__(self):
        self._templates: dict[str, DriverTemplate] = {}
        self._seed_templates()

    def _seed_templates(self) -> None:
        self._templates["serial"] = DriverTemplate(
            template_id="serial", device_type="serial", language="c",
            header="#ifndef SERIAL_DRIVER_H\n#define SERIAL_DRIVER_H\n#include <stdint.h>\nvoid serial_init(uint16_t port);\nchar serial_read(uint16_t port);\nvoid serial_write(uint16_t port, char c);\n#endif",
            init_code="void serial_init(uint16_t port) {\n    outb(port + 1, 0x00);\n    outb(port + 3, 0x80);\n    outb(port + 0, 0x03);\n    outb(port + 1, 0x00);\n    outb(port + 3, 0x03);\n    outb(port + 2, 0xC7);\n    outb(port + 4, 0x0B);\n}",
            read_code="char serial_read(uint16_t port) {\n    while (!(inb(port + 5) & 0x01));\n    return inb(port);\n}",
            write_code="void serial_write(uint16_t port, char c) {\n    while (!(inb(port + 5) & 0x20));\n    outb(port, c);\n}",
            irq_handler_code="void serial_irq_handler(registers_t* regs) {\n    (void)regs;\n}",
        )
        self._templates["timer"] = DriverTemplate(
            template_id="timer", device_type="timer", language="c",
            header="#ifndef TIMER_DRIVER_H\n#define TIMER_DRIVER_H\n#include <stdint.h>\nvoid timer_init(uint32_t freq);\nuint32_t timer_get_ticks(void);\n#endif",
            init_code="void timer_init(uint32_t freq) {\n    uint32_t divisor = 1193180 / freq;\n    outb(0x43, 0x36);\n    outb(0x40, divisor & 0xFF);\n    outb(0x40, (divisor >> 8) & 0xFF);\n}",
            read_code="uint32_t timer_get_ticks(void) { return ticks; }",
            irq_handler_code="void timer_irq(registers_t* regs) {\n    (void)regs;\n    ticks++;\n}",
        )
        self._templates["input"] = DriverTemplate(
            template_id="input", device_type="input", language="c",
            header="#ifndef INPUT_DRIVER_H\n#define INPUT_DRIVER_H\n#include <stdint.h>\nvoid input_init(void);\nuint8_t input_read_scancode(void);\n#endif",
            init_code="void input_init(void) {\n    /* Enable keyboard IRQ */\n}",
            read_code="uint8_t input_read_scancode(void) {\n    while (!(inb(0x64) & 0x01));\n    return inb(0x60);\n}",
        )

    def get_template(self, device_type: str) -> Optional[DriverTemplate]:
        return self._templates.get(device_type)

    def list_templates(self) -> list[str]:
        return list(self._templates.keys())


class DriverSynthesizer:
    def __init__(self):
        self.template_lib = DriverTemplateLibrary()
        self._synthesized: list[SynthesizedDriver] = []

    def synthesize(self, spec: HardwareSpec) -> SynthesizedDriver:
        template = self.template_lib.get_template(spec.device_type)

        if template:
            driver = self._from_template(template, spec)
        else:
            driver = self._generate_skeleton(spec)

        self._synthesized.append(driver)
        return driver

    def _from_template(self, template: DriverTemplate, spec: HardwareSpec) -> SynthesizedDriver:
        header = template.header.replace("SERIAL_DRIVER_H", f"{spec.name.upper()}_DRIVER_H")
        io_port = spec.io_ports[0][0] if spec.io_ports else 0x3F8
        source = f"/* Auto-generated driver for {spec.name} */\n/* Device: {spec.device_type}, Vendor: 0x{spec.vendor_id:04X} */\n\n{template.init_code}\n\n{template.read_code}\n\n{template.write_code if hasattr(template, 'write_code') else ''}\n"
        source = source.replace("0x3F8", f"0x{io_port:X}")
        return SynthesizedDriver(
            driver_name=f"{spec.name}_driver",
            device_name=spec.name,
            header=header,
            source=source,
            build_instructions="gcc -c -m32 -ffreestanding -nostdlib driver.c -o driver.o",
        )

    def _generate_skeleton(self, spec: HardwareSpec) -> SynthesizedDriver:
        io_lines = []
        for start, end in spec.io_ports:
            io_lines.append(f"/* I/O ports: 0x{start:04X} - 0x{end:04X} */")
        irq_lines = [f"/* IRQ: {irq} */" for irq in spec.interrupts]

        header = f"#ifndef {spec.name.upper()}_DRIVER_H\n#define {spec.name.upper()}_DRIVER_H\n#include <stdint.h>\n\nvoid {spec.name}_init(void);\nvoid {spec.name}_read(void* buf, size_t len);\nvoid {spec.name}_write(const void* buf, size_t len);\nvoid {spec.name}_shutdown(void);\n\n#endif\n"

        source = f"/* Auto-generated skeleton for {spec.name} */\n/* Type: {spec.device_type} */\n/* Capabilities: {', '.join(spec.capabilities)} */\n\n"
        source += "\n".join(io_lines) + "\n\n"
        source += "\n".join(irq_lines) + "\n\n"
        source += f"void {spec.name}_init(void) {{\n    /* TODO: Initialize device */\n}}\n\n"
        source += f"void {spec.name}_read(void* buf, size_t len) {{\n    (void)buf; (void)len;\n    /* TODO: Read from device */\n}}\n\n"
        source += f"void {spec.name}_write(const void* buf, size_t len) {{\n    (void)buf; (void)len;\n    /* TODO: Write to device */\n}}\n\n"
        source += f"void {spec.name}_shutdown(void) {{\n    /* TODO: Shutdown device */\n}}\n"

        return SynthesizedDriver(
            driver_name=f"{spec.name}_driver",
            device_name=spec.name,
            header=header,
            source=source,
            build_instructions="gcc -c -m32 -ffreestanding -nostdlib driver.c -o driver.o",
            warnings=["Generated skeleton — manual implementation required"],
        )

    def get_synthesized(self) -> list[SynthesizedDriver]:
        return list(self._synthesized)
