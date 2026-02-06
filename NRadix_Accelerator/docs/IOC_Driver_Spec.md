# IOC Driver Software Technical Specification

**Document ID:** SPEC-IOC-001
**Version:** 0.1.0-draft
**Date:** 2026-02-04
**Author:** Christopher Riner
**Status:** Draft - RFC

---

## Executive Summary

The Input/Output Converter (IOC) is the hardware/software bridge between conventional binary computing systems and the optical ternary processing chip. This document specifies the driver software architecture, interfaces, timing requirements, and implementation guidance for the IOC subsystem.

**Target audience:** Systems programmers implementing the IOC driver stack.

---

## Table of Contents

1. [System Context](#1-system-context)
2. [Functional Requirements](#2-functional-requirements)
3. [Data Encoding](#3-data-encoding)
4. [Timing Budget](#4-timing-budget)
5. [Hardware Interface](#5-hardware-interface)
6. [Software Architecture](#6-software-architecture)
7. [API Specification](#7-api-specification)
8. [Error Handling](#8-error-handling)
9. [Performance Targets](#9-performance-targets)
10. [Implementation Guidance](#10-implementation-guidance)
11. [Open Questions](#11-open-questions)

---

## 1. System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HOST SYSTEM                                     │
│  ┌─────────────┐    ┌─────────────────────────────────────────────────────┐ │
│  │ Application │───>│                   IOC DRIVER                         │ │
│  │   (Binary)  │<───│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │ │
│  └─────────────┘    │  │ Binary  │  │ Channel │  │  FPGA   │  │Physical │ │ │
│                     │  │↔Ternary │─>│  Pack   │─>│ Control │─>│ Layer   │ │ │
│                     │  │ Convert │  │ Manager │  │  Logic  │  │Interface│ │ │
│                     │  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │ │
│                     └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ PCIe / Proprietary Bus
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              IOC HARDWARE                                    │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        FPGA / ASIC Control                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │   Timing    │  │   Laser     │  │ Photodetect │  │   Channel   │   │  │
│  │  │ Generation  │  │  Modulator  │  │   Reader    │  │   Router    │   │  │
│  │  │   (617MHz)  │  │   Control   │  │   (ADC)     │  │   (WDM)     │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ Fiber / Free-space optics
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     OPTICAL TERNARY PROCESSING CHIP                          │
│                                                                              │
│   Wavelength-encoded balanced ternary computation @ 617 MHz                  │
│   1550nm = -1  │  1310nm = 0  │  1064nm = +1                                │
│                                                                              │
│   PEs are SIMPLE: SFG mixer + optical routing only                          │
│   Weights STREAMED from optical RAM (not stored per-PE)                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Functional Requirements

### 2.1 Core Functions

| ID | Function | Description |
|----|----------|-------------|
| F01 | Binary→Ternary | Convert host binary data to balanced ternary representation |
| F02 | Ternary→Wavelength | Map ternary trits to wavelength channel assignments |
| F03 | Wavelength→Ternary | Decode photodetector readings to ternary trits |
| F04 | Ternary→Binary | Convert balanced ternary results back to host binary |
| F05 | Channel Management | Allocate/deallocate WDM channels for parallel operations |
| F06 | Clock Sync | Synchronize host operations with 617 MHz Kerr clock |
| F07 | Error Detection | Detect transmission errors, wavelength drift, timing faults |

### 2.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NF01 | Roundtrip latency (conversion only) | ≤6.5ns |
| NF02 | Maximum sustained throughput | 617M trits/sec × 144 channels |
| NF03 | Channel utilization efficiency | ≥95% at full load |
| NF04 | BER (Bit Error Rate) | <10^-12 |
| NF05 | Mean Time Between Failures | >100,000 hours |

---

## 3. Data Encoding

### 3.1 Balanced Ternary Representation

Balanced ternary uses digit values {-1, 0, +1} rather than {0, 1, 2}. This eliminates the need for separate sign bits and makes arithmetic symmetric around zero.

**Internal representation (2-bit encoding):**
```
Trit Value    Encoding    Notes
   -1           0b00      Could also use 0b11 (sign-magnitude)
    0           0b01
   +1           0b10
  (invalid)     0b11      Reserved / error detection
```

**Rationale:** 2-bit encoding wastes 1 bit per trit but enables fast parallel operations and built-in error detection (0b11 is never valid).

### 3.2 Wavelength Mapping

```
Trit    Wavelength    Band        Laser Type
 -1      1550 nm      C-Band      DFB/EML (Telecom standard)
  0      1310 nm      O-Band      DFB (Telecom standard)
 +1      1064 nm      NIR         Nd:YAG / DPSS
```

**Why these wavelengths:**
- 1550/1310nm: Standard telecom, cheap components, low fiber attenuation
- 1064nm: Common industrial laser, distinct from telecom bands
- No SFG collision products overlap with input wavelengths (verified)

### 3.3 Binary ↔ Balanced Ternary Conversion

**Binary to Balanced Ternary:**

```c
// Standard algorithm: divide by 3, adjust remainder 2 to -1
void binary_to_balanced_ternary(int64_t value, int8_t* trits, size_t max_trits) {
    bool negative = value < 0;
    if (negative) value = -value;

    size_t i = 0;
    while (value != 0 && i < max_trits) {
        int remainder = value % 3;
        value /= 3;

        if (remainder == 2) {
            trits[i] = -1;  // -1 trit, carry +1
            value += 1;
        } else {
            trits[i] = remainder;  // 0 or 1
        }
        i++;
    }

    if (negative) {
        for (size_t j = 0; j < i; j++) {
            trits[j] = -trits[j];  // Negate: just flip all signs
        }
    }
}
```

**Balanced Ternary to Binary:**

```c
int64_t balanced_ternary_to_binary(const int8_t* trits, size_t num_trits) {
    int64_t result = 0;
    int64_t power = 1;

    for (size_t i = 0; i < num_trits; i++) {
        result += trits[i] * power;
        power *= 3;
    }

    return result;
}
```

**Trit width requirements:**

| Binary bits | Trits needed | Formula |
|-------------|--------------|---------|
| 8           | 6            | ceil(8 / log2(3)) = ceil(8 / 1.585) = 6 |
| 16          | 11           | ceil(16 / 1.585) = 11 |
| 32          | 21           | ceil(32 / 1.585) = 21 |
| 64          | 41           | ceil(64 / 1.585) = 41 |

---

## 4. Timing Budget

### 4.1 Clock Domains

```
┌────────────────────────────────────────────────────────────────────────┐
│                         TIMING ARCHITECTURE                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  HOST DOMAIN          IOC DOMAIN              OPTICAL DOMAIN            │
│  (variable)           (617 MHz derived)       (617 MHz Kerr)            │
│                                                                         │
│  ┌─────────┐          ┌─────────────┐         ┌─────────────┐          │
│  │ Host    │  async   │ IOC Clock   │  sync   │ Kerr Clock  │          │
│  │ Clock   │ ──────── │ (617 MHz    │ ─────── │ (617 MHz    │          │
│  │         │  FIFO    │  PLL-locked)│  direct │  optical)   │          │
│  └─────────┘          └─────────────┘         └─────────────┘          │
│                                                                         │
│  Period: variable     Period: 1.621 ns        Period: 1.621 ns         │
│                                                                         │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Latency Breakdown

**Conversion latency (6.5ns total roundtrip):**

| Stage | Direction | Latency | Notes |
|-------|-----------|---------|-------|
| Binary→Ternary | In | ~1.5ns | Combinational logic, pipelined |
| Ternary→Wavelength | In | ~0.5ns | LUT-based, trivial |
| Laser modulation | In | ~0.5ns | Direct modulation EML |
| **Input total** | | **~2.5ns** | |
| Photodetection | Out | ~1.0ns | InGaAs PIN + TIA |
| Wavelength→Ternary | Out | ~0.5ns | Threshold comparator |
| Ternary→Binary | Out | ~1.5ns | Combinational logic, pipelined |
| **Output total** | | **~3.0ns** | |
| **Roundtrip** | | **~5.5ns** | (margin: 1.0ns) |

**Context:** Clock period is ~1.62ns, so conversion happens in ~4 clock cycles. This is acceptable—the optical chip does the heavy computation, not the conversion.

### 4.3 Pipeline Depth

The conversion logic should be pipelined to maintain throughput:

```
Clock  0    1    2    3    4    5    6    7    8
       │    │    │    │    │    │    │    │    │
In[0]  ├─B2T─┼─T2W─┼─MOD─┼─►  optical chip  ►─┼─DET─┼─W2T─┼─T2B─┤ Out[0]
In[1]       ├─B2T─┼─T2W─┼─MOD─┼─►  optical  ►─┼─DET─┼─W2T─┼─T2B─┤ Out[1]
In[2]            ├─B2T─┼─T2W─┼─MOD─┼─► chip ►─┼─DET─┼─W2T─┼─T2B─┤ Out[2]
...

Throughput: 617M operations/sec per channel (after pipeline fill)
Latency: ~4 cycles + chip processing time
```

---

## 5. Hardware Interface

### 5.1 Interface Options Analysis

| Interface | Bandwidth | Latency | Complexity | Recommendation |
|-----------|-----------|---------|------------|----------------|
| PCIe Gen4 x16 | 32 GB/s | ~200ns | High | **Prototype: Yes** |
| PCIe Gen5 x16 | 64 GB/s | ~150ns | High | Production target |
| USB4 | 5 GB/s | ~1μs | Medium | No (too slow) |
| Custom LVDS | Configurable | ~10ns | Very High | ASIC phase only |
| CXL 2.0 | 64 GB/s | ~80ns | Very High | Future option |

**Recommendation:** PCIe Gen4 x16 for prototype, with CXL consideration for production.

### 5.2 Register Map (Memory-Mapped I/O)

Base address assigned by PCIe BAR0.

```
Offset      Size    Name                Description
──────────────────────────────────────────────────────────────────────
0x0000      4       IOC_VERSION         Hardware/firmware version (RO)
0x0004      4       IOC_STATUS          Global status register (RO)
0x0008      4       IOC_CONTROL         Global control register (RW)
0x000C      4       IOC_IRQ_STATUS      Interrupt status (R/W1C)
0x0010      4       IOC_IRQ_ENABLE      Interrupt enable mask (RW)
0x0014      4       IOC_CLOCK_STATUS    Clock sync status (RO)
0x0018      4       RESERVED
0x001C      4       RESERVED

Channel Registers (per channel, 64 bytes each):
0x0100 + (ch * 0x40) + 0x00     4    CH_STATUS      Channel status (RO)
0x0100 + (ch * 0x40) + 0x04     4    CH_CONTROL     Channel control (RW)
0x0100 + (ch * 0x40) + 0x08     4    CH_TX_COUNT    Trits transmitted (RO)
0x0100 + (ch * 0x40) + 0x0C     4    CH_RX_COUNT    Trits received (RO)
0x0100 + (ch * 0x40) + 0x10     4    CH_ERROR_COUNT Error counter (RO)
0x0100 + (ch * 0x40) + 0x14     4    CH_WAVELENGTH  Wavelength config (RW)
0x0100 + (ch * 0x40) + 0x18     4    CH_LASER_PWR   Laser power level (RW)
0x0100 + (ch * 0x40) + 0x1C     4    CH_THRESHOLD   Detection threshold (RW)
0x0100 + (ch * 0x40) + 0x20     8    CH_TX_FIFO     Transmit FIFO (WO)
0x0100 + (ch * 0x40) + 0x28     8    CH_RX_FIFO     Receive FIFO (RO)
...

DMA Registers:
0x2000      8       DMA_TX_ADDR        TX DMA base address (RW)
0x2008      4       DMA_TX_SIZE        TX DMA buffer size (RW)
0x200C      4       DMA_TX_HEAD        TX DMA head pointer (RW)
0x2010      4       DMA_TX_TAIL        TX DMA tail pointer (RO)
0x2014      4       DMA_TX_CONTROL     TX DMA control (RW)
0x2020      8       DMA_RX_ADDR        RX DMA base address (RW)
0x2028      4       DMA_RX_SIZE        RX DMA buffer size (RW)
0x202C      4       DMA_RX_HEAD        RX DMA head pointer (RO)
0x2030      4       DMA_RX_TAIL        RX DMA tail pointer (RW)
0x2034      4       DMA_RX_CONTROL     RX DMA control (RW)
```

### 5.3 DMA vs MMIO Decision

**Use DMA for:**
- Bulk data transfers (>64 bytes)
- Sustained throughput operations
- Background data movement

**Use MMIO for:**
- Control register access
- Status polling
- Low-latency single-trit operations
- Configuration changes

**Hybrid approach:** Ring buffer DMA with MMIO doorbell for low-latency notification.

### 5.4 Channel Architecture

```
144 Total Channels = 6 Triplet Groups × 8 Dense WDM × 3 Wavelengths

Triplet Group 0:  Ch 0-23   (1550/1310/1064 nm base)
Triplet Group 1:  Ch 24-47  (frequency-shifted set 1)
Triplet Group 2:  Ch 48-71  (frequency-shifted set 2)
Triplet Group 3:  Ch 72-95  (frequency-shifted set 3)
Triplet Group 4:  Ch 96-119 (frequency-shifted set 4)
Triplet Group 5:  Ch 120-143 (frequency-shifted set 5)

Within each group:
  Dense WDM 0: Ch N+0, N+1, N+2     (3 wavelengths)
  Dense WDM 1: Ch N+3, N+4, N+5
  ...
  Dense WDM 7: Ch N+21, N+22, N+23
```

**Channel allocation strategy:**
- Allocate in triplet groups for trit-parallel operations
- Use DWDM channels within a group for word-parallel operations
- Support both static allocation and dynamic channel pooling

---

## 6. Software Architecture

### 6.1 Layer Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER SPACE                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Application Layer                         │    │
│  │  libioc.so - User-space library                              │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │    │
│  │  │  ioc_open()  │ │ ioc_submit() │ │ ioc_convert()│         │    │
│  │  │  ioc_close() │ │ ioc_poll()   │ │ ioc_status() │         │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              │ ioctl / mmap                          │
│                              ▼                                       │
├─────────────────────────────────────────────────────────────────────┤
│                        KERNEL SPACE                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    IOC Kernel Driver                         │    │
│  │  ioc.ko                                                      │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │    │
│  │  │  PCIe Probe  │ │ DMA Engine   │ │  IRQ Handler │         │    │
│  │  │  BAR Mapping │ │ Ring Buffers │ │  Completion  │         │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘         │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │    │
│  │  │  Channel Mgr │ │ Clock Sync   │ │  Error Mgr   │         │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│                              │ PCIe TLPs                             │
│                              ▼                                       │
├─────────────────────────────────────────────────────────────────────┤
│                        HARDWARE                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    FPGA / ASIC                               │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Kernel Driver Responsibilities

1. **PCIe enumeration and BAR mapping**
2. **DMA buffer allocation** (CMA or IOMMU-mapped)
3. **Interrupt handling** (MSI-X preferred, one vector per channel group)
4. **Clock synchronization** with Kerr clock reference
5. **Channel state management**
6. **Error logging and recovery**
7. **Power management** (laser safety on suspend)

### 6.3 User-Space Library Responsibilities

1. **Binary ↔ Ternary conversion** (hot path, must be fast)
2. **Channel allocation API**
3. **Submission queue management**
4. **Completion polling / event notification**
5. **Statistics and diagnostics**

### 6.4 FPGA Logic Responsibilities

1. **Timing generation** (617 MHz from PLL, locked to Kerr reference)
2. **Laser modulator drive signals** (DAC + timing)
3. **Photodetector ADC sampling**
4. **Wavelength discrimination** (threshold logic)
5. **DMA engine** (scatter-gather, descriptor rings)
6. **Channel routing** (WDM mux/demux control)

---

## 7. API Specification

### 7.1 Core Types

```c
#include <stdint.h>
#include <stdbool.h>

/* Trit representation: -1, 0, +1 stored in int8_t */
typedef int8_t ioc_trit_t;

/* Packed trit array: 4 trits per byte using 2-bit encoding */
typedef struct {
    uint8_t* data;
    size_t   num_trits;
} ioc_trit_array_t;

/* Channel handle */
typedef struct ioc_channel* ioc_channel_t;

/* Device handle */
typedef struct ioc_device* ioc_device_t;

/* Operation handle for async operations */
typedef struct ioc_op* ioc_op_t;

/* Channel configuration */
typedef struct {
    uint8_t  triplet_group;    /* 0-5 */
    uint8_t  dwdm_channel;     /* 0-7 */
    uint8_t  wavelength_slot;  /* 0-2 (which trit in triplet) */
    uint16_t laser_power_mw;   /* Laser power in milliwatts */
    uint16_t threshold_mv;     /* Detection threshold in millivolts */
} ioc_channel_config_t;

/* Operation flags */
typedef enum {
    IOC_FLAG_NONE      = 0,
    IOC_FLAG_ASYNC     = (1 << 0),  /* Non-blocking submission */
    IOC_FLAG_NO_COPY   = (1 << 1),  /* Zero-copy DMA (buffer must be aligned) */
    IOC_FLAG_FENCE     = (1 << 2),  /* Memory fence before operation */
} ioc_flags_t;

/* Error codes */
typedef enum {
    IOC_OK              = 0,
    IOC_ERR_INVALID     = -1,
    IOC_ERR_NO_DEVICE   = -2,
    IOC_ERR_NO_CHANNEL  = -3,
    IOC_ERR_TIMEOUT     = -4,
    IOC_ERR_CLOCK_SYNC  = -5,
    IOC_ERR_LASER_FAULT = -6,
    IOC_ERR_OVERFLOW    = -7,
    IOC_ERR_UNDERFLOW   = -8,
    IOC_ERR_DMA         = -9,
    IOC_ERR_CONVERSION  = -10,
} ioc_error_t;
```

### 7.2 Device Management

```c
/**
 * Open IOC device
 *
 * @param device_id  Device index (0 for first device, -1 for any)
 * @param flags      Reserved, pass 0
 * @return           Device handle, or NULL on error (check errno)
 */
ioc_device_t ioc_open(int device_id, uint32_t flags);

/**
 * Close IOC device
 *
 * @param dev  Device handle
 */
void ioc_close(ioc_device_t dev);

/**
 * Get device capabilities
 */
typedef struct {
    uint32_t num_channels;
    uint32_t num_triplet_groups;
    uint32_t max_trits_per_transfer;
    uint32_t clock_freq_hz;
    uint32_t firmware_version;
    char     serial_number[32];
} ioc_caps_t;

ioc_error_t ioc_get_caps(ioc_device_t dev, ioc_caps_t* caps);
```

### 7.3 Channel Management

```c
/**
 * Allocate a channel
 *
 * @param dev     Device handle
 * @param config  Channel configuration (NULL for auto-config)
 * @return        Channel handle, or NULL on error
 */
ioc_channel_t ioc_channel_alloc(ioc_device_t dev, const ioc_channel_config_t* config);

/**
 * Allocate a triplet (3 channels for one trit stream)
 *
 * @param dev     Device handle
 * @param group   Triplet group (0-5), or -1 for any
 * @param chans   Output array of 3 channel handles
 * @return        IOC_OK on success
 */
ioc_error_t ioc_triplet_alloc(ioc_device_t dev, int group, ioc_channel_t chans[3]);

/**
 * Free channel(s)
 */
void ioc_channel_free(ioc_channel_t chan);
void ioc_triplet_free(ioc_channel_t chans[3]);
```

### 7.4 Conversion Functions (Zero-Copy Path)

```c
/**
 * Convert binary to balanced ternary (in-place optimized)
 *
 * @param binary      Input binary data
 * @param binary_len  Length in bytes
 * @param trits       Output trit array (caller-allocated)
 * @return            Number of trits written, or negative error
 *
 * Note: trits->data must have capacity for ceil(binary_len * 8 / log2(3)) trits
 */
ssize_t ioc_binary_to_ternary(const void* binary, size_t binary_len,
                              ioc_trit_array_t* trits);

/**
 * Convert balanced ternary to binary
 *
 * @param trits       Input trit array
 * @param binary      Output binary buffer (caller-allocated)
 * @param binary_len  Output buffer size
 * @return            Bytes written, or negative error
 */
ssize_t ioc_ternary_to_binary(const ioc_trit_array_t* trits,
                              void* binary, size_t binary_len);

/**
 * SIMD-optimized batch conversion (AVX-512 when available)
 *
 * Converts 64 bytes (512 bits) at a time using vectorized operations.
 * Input must be 64-byte aligned. Output must have space for 324 trits.
 */
ssize_t ioc_binary_to_ternary_simd(const void* binary, size_t binary_len,
                                   ioc_trit_array_t* trits);
```

### 7.5 Data Transfer

```c
/**
 * Synchronous transmit (blocking)
 *
 * @param chan   Channel handle
 * @param trits  Trit data to transmit
 * @return       IOC_OK on success
 */
ioc_error_t ioc_transmit(ioc_channel_t chan, const ioc_trit_array_t* trits);

/**
 * Synchronous receive (blocking)
 *
 * @param chan   Channel handle
 * @param trits  Output trit buffer
 * @param count  Number of trits to receive
 * @return       Trits received, or negative error
 */
ssize_t ioc_receive(ioc_channel_t chan, ioc_trit_array_t* trits, size_t count);

/**
 * Asynchronous submit
 *
 * @param chan   Channel handle
 * @param trits  Trit data (must remain valid until completion)
 * @param flags  Operation flags
 * @return       Operation handle for polling
 */
ioc_op_t ioc_submit_async(ioc_channel_t chan, const ioc_trit_array_t* trits,
                          ioc_flags_t flags);

/**
 * Poll for completion
 *
 * @param op       Operation handle
 * @param timeout  Timeout in microseconds (-1 for infinite)
 * @return         IOC_OK if complete, IOC_ERR_TIMEOUT if not ready
 */
ioc_error_t ioc_poll(ioc_op_t op, int64_t timeout_us);

/**
 * Batch submission (scatter-gather)
 *
 * @param dev      Device handle
 * @param ops      Array of operation descriptors
 * @param num_ops  Number of operations
 * @param flags    Submission flags
 * @return         Number of ops submitted, or negative error
 */
typedef struct {
    ioc_channel_t     chan;
    ioc_trit_array_t* trits;
    bool              is_transmit;  /* true=TX, false=RX */
} ioc_batch_op_t;

ssize_t ioc_submit_batch(ioc_device_t dev, ioc_batch_op_t* ops, size_t num_ops,
                         ioc_flags_t flags);
```

### 7.6 High-Level Convenience API

```c
/**
 * One-shot binary compute operation
 *
 * Handles all conversion, transmission, and result retrieval.
 *
 * @param dev          Device handle
 * @param input        Binary input data
 * @param input_len    Input length in bytes
 * @param output       Binary output buffer
 * @param output_len   Output buffer size
 * @param op_code      Operation code for optical chip
 * @return             Bytes written to output, or negative error
 */
ssize_t ioc_compute(ioc_device_t dev,
                    const void* input, size_t input_len,
                    void* output, size_t output_len,
                    uint32_t op_code);

/**
 * Ternary arithmetic (stays in ternary domain)
 *
 * For operations that chain multiple ternary computations without
 * converting back to binary between each step.
 */
ioc_error_t ioc_ternary_add(ioc_device_t dev,
                            const ioc_trit_array_t* a,
                            const ioc_trit_array_t* b,
                            ioc_trit_array_t* result);

ioc_error_t ioc_ternary_mul(ioc_device_t dev,
                            const ioc_trit_array_t* a,
                            const ioc_trit_array_t* b,
                            ioc_trit_array_t* result);
```

---

## 8. Error Handling

### 8.1 Error Categories

| Category | Examples | Recovery Strategy |
|----------|----------|-------------------|
| **Transient** | Clock glitch, single bit error | Auto-retry (up to 3x) |
| **Channel** | Laser drift, detector saturation | Recalibrate channel |
| **Device** | DMA timeout, PCIe error | Reset subsystem |
| **Fatal** | Laser failure, clock loss | Fail operation, alert user |

### 8.2 Error Detection Mechanisms

**Wavelength verification:**
- Each photodetector output includes wavelength discrimination
- If detected wavelength doesn't match expected trit encoding, flag error

**Timing verification:**
- Each transmission includes implicit clock sync check
- Drift >5% of clock period triggers resync

**Parity/CRC option:**
- Optional CRC-8 per 64-trit block (configurable)
- Trade 8 trits overhead for error detection per block

### 8.3 Error Reporting

```c
/**
 * Get detailed error information
 */
typedef struct {
    ioc_error_t   code;
    uint32_t      channel_id;
    uint64_t      timestamp_ns;
    uint32_t      hw_error_reg;
    char          message[128];
} ioc_error_info_t;

ioc_error_t ioc_get_last_error(ioc_device_t dev, ioc_error_info_t* info);

/**
 * Error callback registration
 */
typedef void (*ioc_error_callback_t)(ioc_device_t dev,
                                     const ioc_error_info_t* info,
                                     void* user_data);

void ioc_set_error_callback(ioc_device_t dev, ioc_error_callback_t cb,
                            void* user_data);
```

---

## 9. Performance Targets

### 9.1 Throughput

| Configuration | Channels | Theoretical Max | Target |
|---------------|----------|-----------------|--------|
| Single triplet | 3 | 1.85 Gtrit/s | 1.5 Gtrit/s |
| Full DWDM (1 group) | 24 | 14.8 Gtrit/s | 12 Gtrit/s |
| All groups | 144 | 88.8 Gtrit/s | 70 Gtrit/s |

### 9.2 Latency (Software Path)

| Operation | Target | Notes |
|-----------|--------|-------|
| Binary→Ternary (64B) | <100ns | SIMD path |
| Ternary→Binary (64B) | <100ns | SIMD path |
| User→Kernel transition | <500ns | ioctl overhead |
| DMA setup | <200ns | Pre-mapped buffers |
| **Total software overhead** | **<1μs** | Excludes optical processing |

### 9.3 Resource Usage

| Resource | Target |
|----------|--------|
| Kernel memory | <16 MB per device |
| User library memory | <4 MB per context |
| CPU usage (idle) | <1% |
| CPU usage (full throughput) | <10% per core |

---

## 10. Implementation Guidance

### 10.1 FPGA Recommendations

**Prototype phase:**
- **Target:** Xilinx Alveo U50 or Intel Agilex F-Series
- **Rationale:** PCIe Gen4, adequate logic for 144 channels, good tooling

**Key FPGA blocks:**
- PCIe hard IP
- High-speed transceivers (for DWDM control interface)
- DSP slices for threshold comparison
- Block RAM for FIFO buffers

**Clock architecture:**
```
External Kerr Clock Reference (617 MHz)
         │
         ▼
    ┌─────────┐
    │  MMCM   │──► 617 MHz (optical timing domain)
    │  /PLL   │──► 308.5 MHz (DDR interface)
    │         │──► 154.25 MHz (logic domain)
    └─────────┘
```

### 10.2 Kernel Driver Guidelines

**Use existing frameworks:**
- `vfio-pci` for user-space DMA (simplifies development)
- `dma-buf` for zero-copy between subsystems
- Consider DPDK/SPDK patterns for high-performance path

**Interrupt strategy:**
- MSI-X with one vector per triplet group (6 vectors minimum)
- Interrupt coalescing: batch completions, fire every 1μs or 64 completions
- Support polling mode for ultra-low-latency path

**Memory management:**
- Pre-allocate DMA buffers at probe time
- Use huge pages (2MB) for DMA ring buffers
- NUMA-aware allocation when possible

### 10.3 Conversion Optimization

**SIMD implementation targets:**
- AVX-512 on x86-64 (primary)
- NEON on ARM64 (secondary)
- Scalar fallback (always)

**Lookup table approach for small conversions:**
```c
// Pre-computed table: 8-bit binary → 6 trits
// Table size: 256 entries × 6 bytes = 1.5 KB (fits in L1)
static const int8_t binary_to_trit_lut[256][6] = {
    [0x00] = { 0,  0,  0,  0,  0,  0},
    [0x01] = { 1,  0,  0,  0,  0,  0},
    [0x02] = {-1,  1,  0,  0,  0,  0},
    [0x03] = { 0,  1,  0,  0,  0,  0},
    // ... 252 more entries
};
```

### 10.4 Testing Strategy

**Unit tests:**
- Conversion correctness (exhaustive for 16-bit, statistical for larger)
- Channel allocation/deallocation
- Error injection and recovery

**Integration tests:**
- Loopback mode (TX→optical chip bypass→RX)
- Clock sync verification
- DMA stress testing

**Performance tests:**
- Throughput benchmarks at various channel counts
- Latency histograms
- Long-haul stability (72+ hour runs)

---

## 11. Open Questions

These require decisions before implementation proceeds:

### 11.1 Interface Selection

**Q1: PCIe vs CXL for production?**
- PCIe Gen4/5 is proven, well-supported
- CXL offers cache coherency, lower latency
- CXL tooling and availability may limit prototype options

**Recommendation:** Start with PCIe Gen4, design for CXL migration.

### 11.2 FPGA vs ASIC Timeline

**Q2: When to transition from FPGA prototype to ASIC?**
- FPGA: Faster iteration, higher per-unit cost, lower performance
- ASIC: 6-12 month lead time, high NRE, production economics

**Dependencies:** Need proven architecture before ASIC investment.

### 11.3 Channel Parallelism Model

**Q3: How should applications express parallelism?**

Option A: Explicit channel management (current spec)
```c
ioc_channel_t chans[144];
// Application manages all channels explicitly
```

Option B: Thread-like abstraction
```c
ioc_stream_t stream = ioc_stream_create(dev, width=64);
// Runtime manages channel allocation
```

Option C: Hybrid
```c
// High-level for simple cases, low-level available
```

**Recommendation:** Implement Option A first, add Option C later.

### 11.4 Error Correction

**Q4: How much error correction overhead is acceptable?**

| Scheme | Overhead | Detection | Correction |
|--------|----------|-----------|------------|
| None | 0% | No | No |
| Parity (1/64) | 1.5% | Single-trit | No |
| CRC-8 (8/64) | 12.5% | Burst ≤8 | No |
| RS(72,64) | 12.5% | Any 4 | Any 4 |

**Considerations:**
- Physical layer is very clean (BER <10^-15 expected)
- Software ECC may be overkill
- Make it configurable, default to CRC-8

### 11.5 Multi-Device Scaling

**Q5: How to handle multiple IOC devices?**
- Single driver instance managing N devices?
- Device affinity for NUMA systems?
- Cross-device operations?

**Recommendation:** Design for multi-device from start, even if prototype is single-device.

---

## Appendix A: Balanced Ternary Reference

### A.1 Arithmetic Properties

| Operation | Binary | Balanced Ternary |
|-----------|--------|------------------|
| Negation | Subtract from 2^n | Flip all signs |
| Addition | Ripple carry | Ripple carry (same) |
| Subtraction | Add negative | Add negative (trivial) |
| Sign detection | Check MSB | Check MST (most significant trit) |
| Comparison | Subtract, check sign | Same (but simpler) |

### A.2 Value Ranges

| Trits | Min Value | Max Value | Binary Equivalent |
|-------|-----------|-----------|-------------------|
| 1 | -1 | 1 | ~1.58 bits |
| 6 | -364 | 364 | ~8.5 bits |
| 11 | -88,573 | 88,573 | ~17 bits |
| 21 | -5.23×10^9 | 5.23×10^9 | ~33 bits |
| 41 | -1.65×10^19 | 1.65×10^19 | ~65 bits |

### A.3 Conversion Examples

```
Binary 42:
  42 ÷ 3 = 14 R 0  → trit[0] = 0
  14 ÷ 3 =  4 R 2  → trit[1] = -1, carry 1 → 5
   5 ÷ 3 =  1 R 2  → trit[2] = -1, carry 1 → 2
   2 ÷ 3 =  0 R 2  → trit[3] = -1, carry 1 → 1
   1 ÷ 3 =  0 R 1  → trit[4] = 1

Result: 42₁₀ = (+1)(-1)(-1)(-1)(0)₃ = 1T̄T̄T̄0 (where T̄ = -1)

Verify: 1×81 + (-1)×27 + (-1)×9 + (-1)×3 + 0×1 = 81 - 27 - 9 - 3 = 42 ✓
```

---

## Appendix B: Wavelength Collision Analysis

The chosen wavelengths (1550/1310/1064 nm) were selected to avoid SFG (sum-frequency generation) collisions:

```
SFG outputs for all input combinations:
  1550 + 1550 = 775 nm   (not in input set)
  1550 + 1310 = 710 nm   (not in input set)
  1550 + 1064 = 631 nm   (not in input set)
  1310 + 1310 = 655 nm   (not in input set)
  1310 + 1064 = 587 nm   (not in input set)
  1064 + 1064 = 532 nm   (not in input set)

All SFG products are distinct and non-overlapping with inputs. ✓
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-02-04 | C. Riner | Initial draft |

---

**Document Owner:** Christopher Riner
**Review Status:** Draft - Pending Technical Review
**Next Review:** TBD
