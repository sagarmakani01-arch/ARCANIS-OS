# Research: Hardware Interaction

**Path:** `research/hardware-interaction.md`  
**Version:** 0.1.0  
**Status:** Draft

---

## Hardware Abstraction Layer (HAL) Philosophy

The Arcanis HAL is not a thin wrapper over hardware — it is a **declarative interface** where hardware describes its capabilities and the OS generates the appropriate interaction logic.

## Hardware Types

### 1. CPU / Architecture
- **x86-64** — Intel/AMD, complex legacy (SMM, ACPI, UEFI, MTRRs, etc.)
- **ARM64** — Apple Silicon, Qualcomm, AWS Graviton; simpler but fragmented (GIC, SMMU)
- **RISC-V** — Open ISA, extensible (custom instructions), no legacy baggage
- **Key research areas:** CPU features for security (MPK, MTE, CHERI concepts)

### 2. Memory
- **NUMA** — Non-uniform memory access, locality optimization
- **Persistent memory** — Intel Optane, CXL-attached memory
- **Heterogeneous memory** — HBM, GDDR, LPDDR — unified access patterns
- **Key research areas:** AI-driven page placement, tiered memory management

### 3. Storage
- **NVMe** — High-queue-depth, low-latency, PCIe-attached
- **SATA / AHCI** — Legacy but still common
- **Open-channel SSDs** — Host-managed FTL, better control
- **Key research areas:** Learned I/O scheduling, logical-physical mapping

### 4. Networking
- **Ethernet** — 1G to 400G, TCP/IP offload
- **InfiniBand** — HPC, RDMA
- **CXL** — Cache-coherent interconnect, memory pooling
- **Key research areas:** AI-driven congestion control, programmable NICs (eBPF on hardware)

### 5. Accelerators
- **GPUs** — NVIDIA CUDA, AMD ROCm, Intel Xe
- **NPUs / TPUs** — Neural processing units, Google TPU, Apple Neural Engine
- **FPGAs** — Reconfigurable logic
- **Key research areas:** Unified accelerator abstraction, runtime kernel generation

## Driver Model: Declarative Driver Synthesis

```yaml
# Example: Declarative device description (YAML)
device:
  name: "arcanis-nvme-v1"
  class: storage
  bus: pcie
  registers:
    - name: "doorbell"
      offset: 0x1000
      size: 4
      access: write
    - name: "completion_queue_head"
      offset: 0x2000
      size: 4
      access: read-write
  interrupts:
    - name: "io-complete"
      vector: 0
      type: msi-x
  protocol: nvme
```

The **Driver Synthesis Engine** (project 91) takes this description and:

1. Generates memory-mapped I/O access routines
2. Generates interrupt service routines
3. Generates DMA management code
4. Validates against the kernel API contract
5. Produces a loadable driver module

## Hardware Security

- **IOMMU / SMMU** — DMA remapping, device isolation
- **TPM 2.0** — Secure boot, measured boot, attestation
- **Trusted Execution Environment** — Intel SGX, AMD SEV, ARM TrustZone
- **Memory encryption** — Intel TME, AMD SME
- **Secure enclave** — Apple Secure Enclave (reference design)

## Initial Target Hardware

For development and prototyping:

```
CPU:    x86-64 (AMD Ryzen / Intel Core)  ← easiest toolchain
RAM:    ≥8GB, NUMA-aware if available
Storage: NVMe ≥256GB   ← for performance research
Network: 1G Ethernet   ← simple, well-understood
GPU:    None required  ← AI runs on CPU initially
```

## Long-Term Hardware Goals

- **RISC-V as primary platform** — Open ISA, custom AI extensions, full control
- **CHERI-inspired capabilities** — Hardware-enforced memory safety
- **AI accelerator integration** — On-chip NPU for kernel AI workloads
- **Open firmware** — Coreboot / openSBI for RISC-V

---

*Hardware is the foundation. The OS must understand it as deeply as software.*
