# N-Radix 9x9 Monolithic Chip -- Post-Fabrication Test Bench Design

**Version:** 1.1
**Date:** 2026-02-18
**Author:** Christopher Riner (with Claude)
**Status:** COMPLETE -- Circuit simulation 8/8 tests PASS (including IOC domain modes)
**Chip Under Test:** Monolithic 9x9 N-Radix, 81 PEs, 1095 x 695 um, X-cut LiNbO3 (TFLN)

---

## Table of Contents

1. [System Block Diagram](#1-system-block-diagram)
2. [Bill of Materials -- MVP Configuration](#2-bill-of-materials--mvp-configuration)
3. [Bill of Materials -- Full Configuration](#3-bill-of-materials--full-configuration)
4. [FPGA Firmware Specification](#4-fpga-firmware-specification)
5. [PC Software Specification](#5-pc-software-specification)
6. [Physical Setup Procedure](#6-physical-setup-procedure)
7. [Cost Summary](#7-cost-summary)

---

## 1. System Block Diagram

### 1.1 Full Signal Chain

```
 ============================================================================
 HOST PC (Python)                    USB/UART
 ============================================================================
    |                                   ^
    | Test vectors, commands            | Results, pass/fail
    v                                   |
 ============================================================================
 FPGA CONTROL BOARD (Zynq 7020)
 ============================================================================
    |              |              |                    ^
    | 3x GPIO      | SPI/I2C     | DAC outputs        | SPI
    | (mod enable)  | (heater     | (laser current     | (ADC data)
    |               |  DAC ctrl)  |  modulation)       |
    v               v             v                    |
 +----------+  +----------+  +-------------------+    |
 | EOM / RF |  | Heater   |  | Laser Drivers     |    |
 | Drivers  |  | Driver   |  | x3 (CLD1015 or    |    |
 | (opt.)   |  | Board    |  |  equivalent)       |    |
 +----------+  +----------+  +-------------------+    |
    |               |             |     |     |        |
    |               |             |     |     |        |
    |            wire bonds   1550nm 1310nm 1064nm     |
    |               |          SM fiber pigtails       |
    |               v             |     |     |        |
    |          +----+----+        v     v     v        |
    |          |  ~1100  |    +-------------------+    |
    |          |  Bond   |    | V-Groove Fiber    |    |
    |          |  Pads   |    | Array (2-4 ch)    |    |
    |          | (heater |    | 127um pitch       |    |
    |          |  + pwr) |    +-------------------+    |
    |          +----+----+        |                    |
    |               |             |  Edge coupling     |
 ==|===============|=============|=====================|========
   |     CHIP BOUNDARY           |                     |
 ==|===============|=============|=====================|========
    |               |             v                    |
    |               |    +-----------------------------+------+
    |               |    |  N-RADIX MONOLITHIC CHIP           |
    |               |    |  1095 x 695 um, LiNbO3 (TFLN)     |
    |               |    |                                     |
    |               +--->|  IOC INPUT      9x9 PE      IOC    |
    |    (heater         |  (9 encoders)   ARRAY      OUTPUT   |
    |     tuning)        |                (81 PEs)   (9 dec)   |
    |                    |                             |       |
    |                    |  Kerr clock                 |       |
    |                    |  (617 MHz)                  |       |
    |                    |                             v       |
    |                    |                    +--------+--+    |
    |                    |                    | 405 photo-|    |
    |                    |                    | detectors |    |
    |                    |                    | (on-chip) |    |
    |                    +--------------------|-----+------+   |
    |                                        |     |
    |                                   wire bonds (photocurrent)
    |                                        |     |
    |                    +-------------------v-----v----------+
    |                    |  TIA Board                          |
    |                    |  (Transimpedance Amplifiers)        |
    |                    |  5 channels per PE output           |
    |                    |  MVP: 5-10 ch for 1-2 PEs          |
    |                    |  Full: 45 ch for 9 column outputs  |
    |                    +-------------------+----------------+
    |                                        |
    |                                   analog voltage
    |                                        |
    |                    +-------------------v----------------+
    |                    |  ADC Board                          |
    |                    |  MVP: 8-ch 12-bit, 1-10 MSPS       |
    |                    |  Full: 48-ch 14-bit, 125 MSPS      |
    +------------------------------------------------------>  |
                         +------------------------------------+
                                        |
                                   SPI to FPGA
                                        |
                                        v
                              (back to FPGA above)
```

### 1.2 MVP Simplified Signal Chain

For the absolute minimum viable test, we only need to verify that ONE PE
computes correctly. That means:

```
 PC (Python)
    |  USB/UART
    v
 FPGA (Zynq 7020 dev board)
    |
    +---> 3x Laser Drivers ---> 3x DFB Lasers ---> Fiber Array
    |                                                   |
    |                                              edge couple
    |                                                   |
    |                                            [ CHIP ]
    |                                                   |
    |                                          5 photodetectors
    |                                          (from 1 PE output)
    |                                                   |
    +<--- ADC <--- 5x TIA channels <--- wire bond probes
```

### 1.3 Signal Types Summary

| Connection | Signal Type | Count (MVP) | Count (Full) |
|------------|-------------|-------------|--------------|
| FPGA --> Laser drivers | Analog current mod | 3 | 3 |
| Lasers --> Fiber array | Optical (1064/1310/1550 nm) | 3 fibers | 3 fibers |
| Fiber array --> Chip | Optical edge-coupled | 2-4 ports | 2-4 ports |
| Chip --> TIA (wire bond) | Photocurrent (1-100 uA) | 5 | 45+ |
| TIA --> ADC | Analog voltage (0-3.6 V) | 5 | 45+ |
| ADC --> FPGA | SPI digital | 1 bus | multiple |
| FPGA --> PC | USB/UART | 1 | 1 |
| FPGA --> Heater DACs | SPI/I2C | 0 (MVP) | 486 |

---

## 2. Bill of Materials -- MVP Configuration

The MVP goal: prove that the chip produces the correct SFG output
wavelengths for at least one PE when given known ternary inputs.

### 2.1 Laser Sources

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| 1 | 1550 nm DFB laser, butterfly, SM fiber, FC/APC | Thorlabs DFB1550L (20 mW) | 1 | $400 | $400 | C-band, narrow linewidth, internal TEC + isolator. Pigtailed = no alignment needed on laser side. |
| 2 | 1310 nm DFB laser, butterfly, SM fiber, FC/APC | Thorlabs DFB1310 (20 mW) | 1 | $400 | $400 | O-band, same form factor as 1550 nm unit. |
| 3 | 1064 nm laser, fiber-coupled | Thorlabs FPL1064S (50 mW FP) or CNI MGL-FN-1064 | 1 | $350 | $350 | 1064 nm is less common in DFB butterfly. Thorlabs FPL1064S is a Fabry-Perot butterfly (~$300-400). Alternative: CNI DPSS module ($200-300) with separate fiber coupling. |

**Subtotal Lasers: ~$1,150**

**Budget alternative:** Telecom SFP+ transceivers contain 1550 nm and 1310 nm DFB lasers. Used SFP+ modules can be found for $5-20 each on eBay. You would need to break open the SFP+ module and drive the bare laser diode directly. Not elegant, but functional for $40 instead of $800. The 1064 nm source has no SFP equivalent, so you still need a dedicated module.

### 2.2 Laser Drivers and TEC Controllers

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| 4 | Butterfly laser controller (current + TEC) | Thorlabs CLD1015 | 3 | $1,500 | $4,500 | All-in-one: laser current driver (up to 1.5 A), TEC controller (0.005 degC stability), butterfly mount. One per laser. Touchscreen control. This is the expensive-but-easy path. |

**Subtotal Laser Drivers (recommended): ~$4,500**

**Budget alternative: ~$300 total.** Build your own laser driver boards:
- Wavelength Electronics WLD3343 laser driver IC ($25 each, 3x = $75). 500 mA, low noise. Needs a simple PCB.
- Wavelength Electronics WTC3243 TEC controller IC ($25 each, 3x = $75). Pairs with the WLD.
- Custom PCB fab (JLCPCB, 5 boards): $30
- Passive components (resistors, caps, connectors): $50
- Butterfly socket (14-pin): $25 each, 3x = $75
- Total DIY driver cost: ~$300
- Trade-off: requires PCB design and soldering skills. Christopher likely has this.

**Modulation note:** For MVP testing, we do NOT need 617 MHz modulation. We can test statically: set each laser to ON or OFF, wait for the chip to settle, read the detectors. This is DC testing. 617 MHz modulation is only needed for throughput testing later. This dramatically simplifies the laser driver requirements -- any DC current source works.

### 2.3 Optical Components

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| 5 | V-groove fiber array (2-ch, 127 um pitch, SMF-28) | OZ Optics or PHIX custom | 1 | $300 | $300 | Edge-couple to chip. 2 channels minimum (Operand A, Operand B). Order angle-polished for low back-reflection. Lead time 4-6 weeks. |
| 6 | SM fiber patch cables (FC/APC to bare fiber or FC/APC to FC/APC) | Thorlabs P1-SMF28E-FC | 3 | $30 | $90 | One per laser, connect laser pigtail to fiber array or WDM combiner. |
| 7 | 3-to-1 WDM fiber combiner (1064/1310/1550 nm) | Thorlabs WD202A or custom WDM | 1 | $200 | $200 | Combines three wavelengths into one fiber for single-input coupling. Alternatively, use a broadband 3x1 fiber coupler (~$100), accepting 5 dB excess loss. |
| 8 | FC/APC mating sleeves | Thorlabs ADAFC2 | 6 | $8 | $48 | For connecting fiber patch cables to each other. |

**Subtotal Optical: ~$638**

### 2.4 Alignment and Mechanical

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| 9 | 3-axis fiber alignment stage | Thorlabs MBT616D (MicroBlock) | 1 | $350 | $350 | 3-axis differential micrometer stage. 0.5 um resolution. For positioning fiber array relative to chip facet. The NanoMax (MAX313D, ~$900) is better but overkill for MVP. MicroBlock is adequate. |
| 10 | Chip mounting stage / sample holder | Thorlabs APY002 or custom | 1 | $100 | $100 | Vacuum chuck or mechanical clamp to hold the packaged chip. If chip is wire-bonded to a PCB carrier, just clamp the PCB. |
| 11 | Optical breadboard (12" x 12") | Thorlabs MB1212 | 1 | $150 | $150 | Small steel breadboard. All components mount to this. Not a full optical table -- that is overkill and expensive. |
| 12 | Assorted posts, post holders, clamps | Thorlabs TR2, PH2, CF125 | lot | $100 | $100 | Mounting hardware for stages and fiber holders. |
| 13 | USB microscope or loupe | AmScope or generic USB | 1 | $30 | $30 | For visual alignment of fiber to chip edge. |

**Subtotal Alignment/Mechanical: ~$730**

### 2.5 Electronics -- FPGA and Control

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| 14 | FPGA dev board with ADC | Red Pitaya STEMlab 125-14 | 1 | $300 | $300 | Zynq 7010 FPGA, 2x 14-bit ADC at 125 MSPS, 2x DAC, GPIO, Ethernet, USB. Pre-built board with excellent software ecosystem. Can directly sample TIA outputs and generate laser control signals. The ADC is fast enough for 617 MHz testing later (with aliasing, or at sub-Nyquist for initial DC testing). |

**Alternative FPGA option:** ALINX AX7020 Zynq 7020 board (~$150). More GPIO pins (108 via gold-finger expansion) but no built-in ADC -- you would need external ADC boards. Better for the full configuration where you need many channels.

**Budget alternative:** Arduino Due ($25) + ADS1115 16-bit ADC ($3 each). For DC testing only. Cannot do 617 MHz, but proves the chip works. Total: ~$40.

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| 15 | External ADC breakout (8-ch, 12-bit) | ADS7950 eval board or MCP3008 + breakout | 1 | $50 | $50 | Backup ADC for additional channels beyond the Red Pitaya's 2 built-in channels. |

**Subtotal FPGA/Control: ~$350**

### 2.6 Electronics -- TIA (Transimpedance Amplifiers)

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| 16 | TIA eval board (2-ch, >100 MHz BW) | TI OPA857EVM | 1 | $119 | $119 | OPA857: wideband TIA, 100 MHz BW at 20 kOhm gain. 2 selectable gains (5k/20k). Enough bandwidth for DC testing and early dynamic tests. One board gives 1 channel. |
| 17 | Additional TIA channels (DIY) | OPA857IRGTR IC ($7 ea) on custom PCB | 4 | $10 | $40 | Build 4 more TIA channels on a simple PCB (JLCPCB ~$5 for 5 boards). Total 5 channels = 1 PE output. |
| 18 | Si photodiode (external, for alignment check) | Thorlabs FDS100 or SM05PD1A | 1 | $50 | $50 | Silicon photodiode, 350-1100 nm. Mount on the alignment stage to verify light is coming through the chip before connecting TIA to on-chip detectors. |

**Subtotal TIA: ~$209**

**Note on TIA for MVP:** The on-chip photodetectors output photocurrent. For DC testing, you can use a simple op-amp in transimpedance configuration (LM358 + 100k feedback resistor) -- costs $1. The OPA857 is for when you want speed. Start cheap, upgrade if needed.

### 2.7 Chip Packaging and Electrical Interface

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| 19 | AlN submount (25 x 25 mm) | Custom from MTI Corp or University surplus | 1 | $50 | $50 | High thermal conductivity ceramic for die attach. |
| 20 | Wire bonding service (chip to PCB carrier) | University or contract (SPT Roth, Palomar) | 1 | $300 | $300 | MVP: bond only the 5 detector pads for 1 PE + ground + power = ~10 bonds. Full bonding of all 1100 pads is a separate step. Most universities with a clean room offer wire bonding as a service for $100-500. |
| 21 | PCB carrier board (custom, for wire bond out) | JLCPCB 4-layer PCB | 5 | $10 | $50 | Fan-out from chip bond pads to standard 2.54 mm headers. Design in KiCad. 5 boards for $50 at JLCPCB with DHL shipping. |
| 22 | Thermal epoxy (die attach) | Arctic Silver Thermal Adhesive or Epotek H20E | 1 | $15 | $15 | For bonding die to AlN submount. |

**Subtotal Packaging: ~$415**

**Critical note:** Wire bonding is the gating item. If Christopher does not have access to a wire bonder, alternatives include:
- **Probe station:** Use tungsten needle probes to contact individual bond pads. No bonding needed, but only tests a few pads at a time. Probe stations cost $500-2000 used on eBay.
- **Conductive epoxy:** Silver epoxy micro-dots applied with a sharp needle under microscope. Crude but works for a few pads.
- **University partnership:** Many EE departments will let you use their wire bonder for a small fee or collaboration.

### 2.8 Thermal Management

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| 23 | TEC (Peltier) module (20x20 mm) | TEC1-01706 or similar small TEC | 1 | $10 | $10 | Mount under the AlN submount. 6A max, ~15W cooling. Way more than needed for 2-3 W chip dissipation. |
| 24 | TEC controller | Thorlabs TC200 or DIY (MAX1978 eval) | 1 | $200 | $200 | Controls the TEC to hold chip at 25 degC +/- 0.1 degC. The Thorlabs TC200 is ~$800. Budget: MAX1978 eval board from Analog Devices is ~$200, or build with a PID + PWM H-bridge for ~$30 using an Arduino. |
| 25 | NTC thermistor (10k, SMD) | Generic 10k NTC | 2 | $2 | $4 | Epoxy one to the AlN submount near the chip. Second as spare. |
| 26 | Small heatsink + fan | Generic 40 mm aluminum heatsink | 1 | $10 | $10 | Bolted under the TEC cold side to dissipate heat. |

**Subtotal Thermal: ~$224**

**MVP shortcut:** The chip dissipates 2-3 W max (and only if all heaters are active). For MVP testing at room temperature with only a few heaters active, the chip dissipation is negligible. An aluminum block as a passive heatsink may suffice. Skip the TEC entirely for first tests, monitor temperature with the thermistor, and add active cooling only if drift is observed.

### 2.9 Test Equipment (Assumed Available or Optional)

| # | Component | Notes | If Needed, Cost |
|---|-----------|-------|-----------------|
| 27 | Multimeter | Measure voltages, currents, resistance. Christopher almost certainly has one. | $30 |
| 28 | Oscilloscope (optional for MVP) | Useful for debugging TIA outputs and timing. Not strictly needed for DC testing. | $300 used |
| 29 | Optical power meter (optional) | Verify laser output power at chip facet. Can substitute a photodiode + multimeter. | $200-500 |
| 30 | Soldering station | For assembling PCBs, TIA boards. | $50 |

**Subtotal Test Equipment: $0 (assumed available) to ~$580**

### 2.10 MVP Cost Summary

| Category | Cost |
|----------|------|
| Laser sources | $1,150 |
| Laser drivers (budget DIY) | $300 |
| Optical components | $638 |
| Alignment / mechanical | $730 |
| FPGA / control | $350 |
| TIA amplifiers | $209 |
| Chip packaging | $415 |
| Thermal management | $224 |
| **MVP TOTAL** | **$4,016** |

**With Thorlabs CLD1015 drivers instead of DIY:** Add $4,200 --> total $8,216

**Absolute bare-bones MVP** (maximum DIY, skip TEC, use Arduino, salvage SFP lasers for 1550/1310, build all TIAs from op-amps):

| Item | Cost |
|------|------|
| Salvaged SFP+ lasers (1550 + 1310) | $40 |
| CNI 1064 nm DPSS module | $200 |
| DIY laser drivers (WLD3343 x3) | $300 |
| V-groove fiber array | $300 |
| WDM combiner | $100 |
| Fiber patch cables | $90 |
| MicroBlock stage | $350 |
| Breadboard + posts | $150 |
| Arduino Due + ADS1115 ADCs | $40 |
| DIY TIA (op-amps, 5 ch) | $10 |
| Chip packaging + wire bond | $365 |
| Thermal (passive heatsink only) | $10 |
| **BARE-BONES TOTAL** | **~$1,955** |

---

## 3. Bill of Materials -- Full Configuration

Everything in MVP, plus upgrades for comprehensive testing of all 81 PEs.

### 3.1 Upgraded Electronics

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| F1 | FPGA board (more GPIO) | ALINX AX7020 (Zynq 7020) | 1 | $170 | $170 | 108 GPIO via expansion. Dual-core ARM A9 + 85k logic cells. Enough I/O for ADC buses, heater DACs, laser control. |
| F2 | Multi-channel ADC (48-ch, 14-bit) | AD7616 eval board (16-ch) x3 | 3 | $150 | $450 | 16 channels per board, 14-bit, 1 MSPS per channel. SPI interface to FPGA. 48 channels covers 9 PE outputs x 5 detectors + spares. |
| F3 | Multi-channel DAC (for heater control) | AD5370 (40-ch, 16-bit DAC) x2 | 2 | $100 | $200 | 80 DAC channels total. 486 heaters / 80 = 6.1, so you would need multiplexing. But only a fraction of heaters are active at once. |
| F4 | Analog multiplexer boards | CD74HC4067 (16:1 mux) x8 | 8 | $5 | $40 | Expand DAC channels to cover all 486 heaters. 8 mux boards x 16 channels = 128 channels per DAC output. |
| F5 | Multi-channel TIA array (custom PCB) | OPA857 x 45 on custom 4-layer PCB | 1 | $500 | $500 | 45 TIA channels (9 column outputs x 5 detectors). Custom PCB with proper ground planes. OPA857 at $7 each = $315 in ICs + $185 in PCB and passives. |
| F6 | High-speed oscilloscope | Rigol DS1104Z (100 MHz, 4-ch) | 1 | $400 | $400 | Essential for debugging timing, TIA outputs, clock recovery. 100 MHz bandwidth, 1 GSa/s. |
| F7 | RF signal generator (617 MHz) | Siglent SDG2042X (40 MHz) or SDG6052X (500 MHz) | 1 | $500 | $500 | For generating 617 MHz modulation signals to laser drivers. The SDG6052X does 500 MHz; for true 617 MHz you may need a DDS board ($50) or PLL synthesizer. |

**Subtotal Upgraded Electronics: ~$2,260**

### 3.2 Upgraded Optical

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| F8 | Electro-optic modulator (EOM), 1550 nm | Thorlabs LN05S-FC (10 GHz LiNbO3 EOM) | 1 | $800 | $800 | For high-speed modulation of the 1550 nm channel at 617 MHz. Inline fiber, FC/APC. |
| F9 | EOM, 1310 nm | EOSpace or iXblue equivalent | 1 | $800 | $800 | 1310 nm EOM. Less common, slightly more expensive. |
| F10 | EOM, 1064 nm | Custom or Jenoptik equivalent | 1 | $1,000 | $1,000 | 1064 nm EOMs exist but are specialty items. May need free-space modulation with an AOM ($500) as alternative. |
| F11 | RF amplifier (for driving EOMs) | Mini-Circuits ZHL-1A (1 GHz, +29 dBm) | 3 | $150 | $450 | EOMs need ~5 V peak-to-peak RF drive. Amplify the FPGA/DDS output. |
| F12 | Optical spectrum analyzer (fiber-coupled) | Thorlabs CCS200 (compact spectrometer, 200-1000 nm) | 1 | $2,500 | $2,500 | Verify SFG output wavelengths directly from chip. Covers visible range (500-800 nm) where SFG products appear. Critical for validating that the correct multiplication products are generated. |

**Subtotal Upgraded Optical: ~$5,550**

### 3.3 Upgraded Thermal

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| F13 | Precision TEC controller | Thorlabs TED4015 (15 A) | 1 | $1,200 | $1,200 | Laboratory-grade temperature controller. 0.001 degC stability. PID auto-tune. |
| F14 | RTD temperature sensor (PT100, thin-film) | Heraeus M222 or similar | 2 | $15 | $30 | More accurate than NTC thermistor. 4-wire measurement for precision. |

**Subtotal Upgraded Thermal: ~$1,230**

### 3.4 Upgraded Packaging

| # | Component | Suggested Part | Qty | Unit Cost | Total | Notes |
|---|-----------|---------------|-----|-----------|-------|-------|
| F15 | Full wire bonding (all 1100 pads) | Contract service | 1 | $1,500 | $1,500 | Bond all 405 detector pads, 486 heater pads, 162 carry I/O, power, ground. This is a significant job -- 1100 bonds at ~$1-2 per bond. |
| F16 | Custom carrier PCB (high density) | 6-layer PCB, JLCPCB | 5 | $30 | $150 | Higher layer count for routing 1100 signals. BGA-like pad field on one side, standard headers on the other. |
| F17 | Probe station (used) | Signatone, Cascade, or Wentworth | 1 | $1,500 | $1,500 | Used probe station from eBay. For die-level testing before wire bonding. Includes XYZ manipulators, microscope, and vacuum chuck. |

**Subtotal Upgraded Packaging: ~$3,150**

### 3.5 Full Configuration Cost Summary

| Category | MVP Cost | Full Upgrade | Full Total |
|----------|----------|--------------|------------|
| Laser sources | $1,150 | -- | $1,150 |
| Laser drivers (DIY) | $300 | -- | $300 |
| Optical components | $638 | $5,550 | $6,188 |
| Alignment / mechanical | $730 | -- | $730 |
| FPGA / control | $350 | $2,260 | $2,610 |
| TIA amplifiers | $209 | (included in F5) | $500 |
| Chip packaging | $415 | $3,150 | $3,565 |
| Thermal management | $224 | $1,230 | $1,454 |
| **TOTAL** | **$4,016** | **$12,190** | **$16,497** |

---

## 4. FPGA Firmware Specification

### 4.1 FPGA Platform Selection

**Recommended: Red Pitaya STEMlab 125-14** for MVP

| Feature | Red Pitaya 125-14 | ALINX AX7020 | Arduino Due |
|---------|-------------------|--------------|-------------|
| FPGA | Zynq 7010 | Zynq 7020 | None (ARM) |
| ADC | 2x 14-bit, 125 MSPS | None (external) | None (external) |
| DAC | 2x 14-bit, 125 MSPS | None (external) | 2x 12-bit DAC |
| GPIO | ~16 digital I/O | 108 via connector | 54 digital I/O |
| Price | ~$300 | ~$170 | ~$25 |
| Software | Linux + Python + SCPI | Vivado + custom | Arduino IDE |
| Best for | MVP (built-in ADC) | Full (max I/O) | Bare-bones DC test |

For MVP, the Red Pitaya is ideal because it has built-in high-speed ADCs that can directly sample TIA outputs without additional hardware. The built-in DACs can drive laser current modulation.

For the full configuration, add the ALINX AX7020 as a dedicated I/O expander for heater DACs and multiplexed ADC channels, controlled by the Red Pitaya over SPI or UART.

### 4.2 I/O Count Analysis

**MVP (1-2 PE test):**

| Signal | Direction | Count | Interface |
|--------|-----------|-------|-----------|
| Laser enable (3 wavelengths) | Output | 3 | GPIO |
| Laser current set (analog) | Output | 3 | DAC (Red Pitaya 2x DAC + 1 GPIO PWM) |
| TIA readout (5 detectors, 1 PE) | Input | 5 | ADC (Red Pitaya 2x ADC + 3x ext ADS1115) |
| Temperature sensor (NTC) | Input | 1 | ADC (shared) |
| **Total I/O** | | **12** | Fits easily |

**Full (81 PE test):**

| Signal | Direction | Count | Interface |
|--------|-----------|-------|-----------|
| Laser enable | Output | 3 | GPIO |
| Laser current mod | Output | 3 | DAC |
| TIA readout (45 detectors) | Input | 45 | 3x AD7616 (48 ch total) via SPI |
| Heater DAC (486 heaters) | Output | 486 | 2x AD5370 (80 ch) + 8x mux (128:1) |
| Carry chain I/O | Bidir | 162 | GPIO via shift registers (74HC595/165) |
| Temperature sensors | Input | 4 | I2C (MCP9808) |
| **Total logical I/O** | | **~700** | Requires multiplexing |

**Pin budget for ALINX AX7020 (full config):**

| Bus | FPGA Pins Used | Connects To |
|-----|---------------|-------------|
| SPI bus 1 (ADCs) | 6 (SCLK, MOSI, MISO, 3x CS) | 3x AD7616 |
| SPI bus 2 (DACs) | 4 (SCLK, MOSI, 2x CS) | 2x AD5370 |
| SPI bus 3 (Red Pitaya link) | 4 | Inter-FPGA comm |
| MUX address lines | 4 | CD74HC4067 shared |
| MUX enable lines | 8 | 8x CD74HC4067 |
| Shift register bus (carry chain) | 4 (CLK, DATA_IN, DATA_OUT, LATCH) | 74HC595/165 daisy chain |
| Laser control | 6 | 3x enable + 3x analog |
| I2C (temp sensors) | 2 | MCP9808 |
| UART (to PC) | 2 | USB-UART |
| **Total FPGA pins** | **~40** | Well within 108 available |

### 4.3 Firmware Architecture

```
+------------------------------------------------------------------+
|  FPGA Firmware (Verilog / VHDL)                                   |
|                                                                    |
|  +------------------+  +------------------+  +-----------------+  |
|  | TEST SEQUENCER   |  | LASER CONTROL    |  | CLOCK SYNC      |  |
|  | (ARM Cortex-A9)  |  | MODULE           |  | MODULE          |  |
|  |                  |  |                  |  |                 |  |
|  | - Load test      |  | - 3 channel      |  | - Detect Kerr   |  |
|  |   vectors from   |  |   enable/disable |  |   clock output  |  |
|  |   PC via UART    |  | - Current DAC    |  |   (if available)|  |
|  | - Step through   |  |   control        |  | - Generate ext  |  |
|  |   test cases     |  | - Modulation     |  |   clock (PLL)   |  |
|  | - Compare results|  |   waveform gen   |  | - Phase lock     |  |
|  | - Report pass/   |  |   (DDS for       |  |   to chip clock |  |
|  |   fail           |  |    617 MHz)      |  |                 |  |
|  +--------+---------+  +--------+---------+  +--------+--------+  |
|           |                      |                      |          |
|  +--------v---------+  +--------v---------+  +---------v-------+  |
|  | ADC READER        |  | DAC WRITER       |  | HEATER CONTROL  |  |
|  |                  |  |                  |  |                 |  |
|  | - SPI master to  |  | - SPI master to  |  | - MUX address   |  |
|  |   AD7616 x3      |  |   Red Pitaya     |  |   sequencer     |  |
|  | - 48 ch readout  |  |   DAC or ext DAC |  | - DAC value     |  |
|  | - Threshold      |  | - Waveform RAM   |  |   from lookup   |  |
|  |   detection      |  |   for modulation |  |   table          |  |
|  | - Data FIFO to   |  |   patterns       |  | - Thermal        |  |
|  |   ARM            |  |                  |  |   feedback loop  |  |
|  +------------------+  +------------------+  +-----------------+  |
|                                                                    |
|  +--------------------------------------------------------------+  |
|  | UART / USB INTERFACE                                          |  |
|  | - Command parser (ASCII protocol)                             |  |
|  | - Result streaming (CSV or binary)                            |  |
|  | - Register read/write for debug                               |  |
|  +--------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

### 4.4 Firmware Functional Requirements

**F4.4.1 -- Laser Control**

The firmware must be able to independently turn each of the three lasers (1550 nm, 1310 nm, 1064 nm) on or off. For DC testing:

| Ternary Input | 1550 nm (RED/-1) | 1310 nm (GREEN/0) | 1064 nm (BLUE/+1) |
|---------------|-------------------|--------------------|---------------------|
| -1 | ON | OFF | OFF |
| 0 | OFF | ON | OFF |
| +1 | OFF | OFF | ON |

The firmware sets the appropriate laser enable GPIO pins based on the test vector. For each test case, it applies the input, waits for propagation + settling time (~100 ns for the chip + ~1 us for TIA settling), then triggers ADC readout.

**F4.4.2 -- ADC Readout and Threshold Detection**

Each PE output has 5 photodetectors. The firmware reads all 5 channels and determines which detector(s) fired:

| Detector | Expected SFG Wavelength | Meaning |
|----------|------------------------|---------|
| DET_-2 | 775.0 nm (RED+RED) | Overflow: borrow |
| DET_-1 | 710.0 nm (RED+GREEN) | Result trit = -1 |
| DET_0 | 655.0 nm (GREEN+GREEN) | Result trit = 0 |
| DET_+1 | 587.1 nm (GREEN+BLUE) | Result trit = +1 |
| DET_+2 | 532.0 nm (BLUE+BLUE) | Overflow: carry |

**Decision logic (pseudocode):**
```
threshold = calibrated_baseline + 3 * noise_sigma
active_detectors = [i for i in range(5) if adc_reading[i] > threshold[i]]
if len(active_detectors) == 1:
    result = detector_to_trit[active_detectors[0]]
    status = PASS if result == expected else FAIL
elif len(active_detectors) == 0:
    status = FAIL_NO_SIGNAL
else:
    status = FAIL_MULTIPLE  # crosstalk or alignment issue
```

**F4.4.3 -- Test Vector Execution**

**PE Architecture Note:** The chip has two PE operation modes, determined by the IOC (not by the PE hardware -- all PEs physically perform the same SFG frequency addition):

- **ADD/SUB mode:** IOC sends raw ternary-encoded wavelengths. SFG adds the trit values directly. Result is ternary addition (with carry/borrow).
- **MUL/DIV mode:** IOC sends log-domain encoded wavelengths. SFG adds the log-encoded values, which is equivalent to multiplication in the original domain.

All PEs physically just add. The IOC determines the meaning of the inputs and outputs.

**Addition truth table (ADD/SUB mode) -- 9 cases:**

| Operand A | Operand B | Expected Sum | Expected Carry |
|-----------|-----------|-------------|----------------|
| -1 | -1 | +1 | -1 |
| -1 | 0 | -1 | 0 |
| -1 | +1 | 0 | 0 |
| 0 | -1 | -1 | 0 |
| 0 | 0 | 0 | 0 |
| 0 | +1 | +1 | 0 |
| +1 | -1 | 0 | 0 |
| +1 | 0 | +1 | 0 |
| +1 | +1 | -1 | +1 |

**Multiplication truth table (MUL/DIV mode, log-domain) -- 9 cases:**

| Operand A | Operand B | Expected Product | Expected Carry |
|-----------|-----------|-----------------|----------------|
| -1 | -1 | +1 | 0 |
| -1 | 0 | 0 | 0 |
| -1 | +1 | -1 | 0 |
| 0 | -1 | 0 | 0 |
| 0 | 0 | 0 | 0 |
| 0 | +1 | 0 | 0 |
| +1 | -1 | -1 | 0 |
| +1 | 0 | 0 | 0 |
| +1 | +1 | +1 | 0 |

Note: In MUL/DIV mode, the IOC log-encodes values so that SFG addition of log-encoded trits produces the correct multiplication result. The firmware stores both truth tables and validates against the appropriate one based on the IOC domain mode being tested.

**F4.4.4 -- Clock Synchronization (Future)**

For dynamic testing at 617 MHz:

1. If the chip provides a clock output (photodetector on the Kerr clock bus), the firmware detects it with the ADC, extracts the frequency, and locks a PLL to it.
2. If no clock output is available, the firmware generates a 617 MHz reference using an internal DDS (or external synthesizer) and assumes the chip's Kerr clock will self-synchronize (since the modulation rate determines when photons arrive).
3. For MVP DC testing, clock synchronization is not needed.

### 4.5 Firmware Development Plan

| Phase | Description | Complexity | Time |
|-------|-------------|------------|------|
| Phase 1 | DC test: GPIO laser on/off, ADC read, UART report | Simple | 1 week |
| Phase 2 | Automated test vector sweep, threshold calibration | Medium | 1 week |
| Phase 3 | Heater DAC control, temperature feedback | Medium | 1 week |
| Phase 4 | DDS modulation at 617 MHz, clock sync | Hard | 2-4 weeks |

For MVP, only Phases 1-2 are needed. The Red Pitaya can be programmed in Python via its SCPI interface, making Phase 1 trivially simple (see PC Software section).

---

## 5. PC Software Specification

### 5.1 Language and Framework

**Language:** Python 3.10+
**Dependencies:** pyserial, numpy, matplotlib, pandas
**Interface:** USB serial to FPGA (or Ethernet/SCPI if using Red Pitaya)

### 5.2 Architecture

```
nradix_testbench/
    |
    +-- main.py                  # CLI entry point
    +-- config.py                # Test bench configuration
    +-- drivers/
    |   +-- fpga_interface.py    # UART/SCPI communication
    |   +-- laser_control.py     # Laser on/off/modulation
    |   +-- adc_reader.py        # Read detector values
    |   +-- heater_control.py    # Set heater DAC values
    |   +-- thermal.py           # Temperature monitoring
    |
    +-- test_engine/
    |   +-- test_vectors.py      # Truth tables and test cases
    |   +-- calibration.py       # Baseline/threshold calibration
    |   +-- runner.py            # Execute test sequences
    |   +-- comparator.py        # Compare actual vs expected
    |
    +-- reporting/
    |   +-- logger.py            # Real-time logging
    |   +-- report_gen.py        # Generate HTML/PDF reports
    |   +-- plots.py             # Matplotlib visualizations
    |
    +-- data/
    |   +-- test_results/        # Timestamped result files
    |   +-- calibration/         # Saved calibration data
    |
    +-- tests/
        +-- test_vectors_test.py # Unit tests for truth tables
        +-- test_interface.py    # Mock FPGA tests
```

### 5.3 Key Functions

**5.3.1 -- FPGA Interface (Red Pitaya SCPI)**

```python
import socket

class RedPitayaInterface:
    def __init__(self, ip: str = "192.168.1.100", port: int = 5000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

    def set_laser(self, wavelength_nm: int, state: bool) -> None:
        """Turn a laser on or off via GPIO pin."""
        pin_map = {1550: "DIO0_P", 1310: "DIO1_P", 1064: "DIO2_P"}
        pin = pin_map[wavelength_nm]
        val = "1" if state else "0"
        self._send(f"DIG:PIN {pin},{val}")

    def read_adc(self, channel: int) -> float:
        """Read ADC channel voltage."""
        self._send(f"ACQ:SOUR CH{channel}")
        self._send("ACQ:START")
        self._send("ACQ:TRIG NOW")
        # Wait for acquisition
        data = self._query("ACQ:SOUR:DATA?")
        return float(data.split(",")[0])

    def _send(self, cmd: str) -> None:
        self.sock.sendall((cmd + "\r\n").encode())

    def _query(self, cmd: str) -> str:
        self._send(cmd)
        return self.sock.recv(4096).decode().strip()
```

**5.3.2 -- Test Vector Engine**

```python
from dataclasses import dataclass
from typing import List

@dataclass
class TritTestVector:
    operand_a: int      # -1, 0, or +1
    operand_b: int      # -1, 0, or +1
    expected_result: int # -1, 0, or +1
    expected_carry: int  # -1, 0, or +1

MULTIPLICATION_VECTORS: List[TritTestVector] = [
    TritTestVector(-1, -1, +1, 0),
    TritTestVector(-1,  0,  0, 0),
    TritTestVector(-1, +1, -1, 0),
    TritTestVector( 0, -1,  0, 0),
    TritTestVector( 0,  0,  0, 0),
    TritTestVector( 0, +1,  0, 0),
    TritTestVector(+1, -1, -1, 0),
    TritTestVector(+1,  0,  0, 0),
    TritTestVector(+1, +1, +1, 0),
]

ADDITION_VECTORS: List[TritTestVector] = [
    TritTestVector(-1, -1, +1, -1),  # -1 + -1 = -2 = +1 carry -1
    TritTestVector(-1,  0, -1,  0),
    TritTestVector(-1, +1,  0,  0),
    TritTestVector( 0, -1, -1,  0),
    TritTestVector( 0,  0,  0,  0),
    TritTestVector( 0, +1, +1,  0),
    TritTestVector(+1, -1,  0,  0),
    TritTestVector(+1,  0, +1,  0),
    TritTestVector(+1, +1, -1, +1),  # +1 + +1 = +2 = -1 carry +1
]
```

**5.3.3 -- Test Runner**

```python
def run_single_pe_test(
    interface: RedPitayaInterface,
    vectors: List[TritTestVector],
    settling_time_ms: float = 10.0,
) -> dict:
    """Run all test vectors against one PE and return results."""

    results = []
    wavelength_map = {-1: 1550, 0: 1310, +1: 1064}

    for vec in vectors:
        # Set operand A laser
        for wl in [1550, 1310, 1064]:
            interface.set_laser(wl, wl == wavelength_map[vec.operand_a])

        # Wait for light to propagate and TIA to settle
        time.sleep(settling_time_ms / 1000.0)

        # Read all 5 detector channels
        readings = {}
        for det_idx, det_name in enumerate(
            ["DET_-2", "DET_-1", "DET_0", "DET_+1", "DET_+2"]
        ):
            readings[det_name] = interface.read_adc(det_idx)

        # Determine which detector fired
        max_det = max(readings, key=readings.get)
        max_val = readings[max_det]

        # Map detector to trit value
        det_to_trit = {
            "DET_-2": -2, "DET_-1": -1, "DET_0": 0,
            "DET_+1": +1, "DET_+2": +2
        }
        measured_result = det_to_trit[max_det]

        passed = (measured_result == vec.expected_result)

        results.append({
            "operand_a": vec.operand_a,
            "operand_b": vec.operand_b,
            "expected": vec.expected_result,
            "measured": measured_result,
            "readings": readings,
            "passed": passed,
        })

    return {
        "total": len(results),
        "passed": sum(1 for r in results if r["passed"]),
        "failed": sum(1 for r in results if not r["passed"]),
        "details": results,
    }
```

### 5.4 Data Format

Test results are saved as JSON for machine readability and CSV for human readability:

**JSON (primary):**
```json
{
    "test_run_id": "2026-02-17_001",
    "chip_id": "NR9X9-001",
    "timestamp": "2026-02-17T14:30:00Z",
    "configuration": {
        "pe_under_test": [0, 0],
        "laser_powers_mw": {"1550": 10, "1310": 10, "1064": 10},
        "settling_time_ms": 10,
        "temperature_c": 25.1
    },
    "results": {
        "total": 9,
        "passed": 9,
        "failed": 0,
        "details": [
            {
                "operand_a": -1,
                "operand_b": -1,
                "expected": 1,
                "measured": 1,
                "readings": {
                    "DET_-2": 0.02,
                    "DET_-1": 0.03,
                    "DET_0": 0.01,
                    "DET_+1": 2.87,
                    "DET_+2": 0.04
                },
                "passed": true
            }
        ]
    }
}
```

**CSV (human-readable summary):**
```
test_id,op_a,op_b,expected,measured,det_-2,det_-1,det_0,det_+1,det_+2,pass
1,-1,-1,+1,+1,0.02,0.03,0.01,2.87,0.04,PASS
2,-1,0,0,0,0.01,0.02,2.91,0.03,0.01,PASS
...
```

### 5.5 Report Generation

The software generates an HTML report after each test run:
- Summary table (pass/fail counts, percentage)
- Detector reading heatmaps (5 detectors x 9 test cases)
- Signal-to-noise ratio per detector
- Temperature log over the test duration
- Comparison to expected truth table
- Laser power readings (if optical power meter is connected)

---

## 6. Physical Setup Procedure

### 6.1 Overview -- From Box of Parts to First Measurement

| Step | Task | Time Estimate |
|------|------|---------------|
| 1 | Assemble mechanical platform | 1-2 hours |
| 2 | Set up laser drivers and verify lasers | 2-4 hours |
| 3 | Mount and wire-bond chip (or probe) | 1-4 hours (wire bond) or 30 min (probe) |
| 4 | Fiber alignment to chip | 2-8 hours (first time) |
| 5 | Connect TIA and verify detector signals | 1-2 hours |
| 6 | Connect FPGA and run first test | 1 hour |
| 7 | Calibrate thresholds | 1-2 hours |
| 8 | Run full test suite | 30 min |

**Total estimated time to first measurement: 1-2 days**

### 6.2 Step 1: Assemble Mechanical Platform

1. Mount the 12" x 12" steel breadboard on a stable surface (heavy desk or table). Avoid locations with vibration (near HVAC, washing machine, foot traffic).

2. Mount the MicroBlock 3-axis stage (or NanoMax) to the breadboard using M6 cap screws in the breadboard's 1" grid.

3. Mount the chip holder opposite the fiber stage, also on the breadboard, at approximately the right height. The chip facet and fiber tip should be at the same height.

4. Verify the stage axes: X = lateral (perpendicular to fiber axis), Y = vertical, Z = along fiber axis (toward/away from chip).

5. Mount the USB microscope on a post holder, aimed at the gap between the fiber array and the chip edge. This is your alignment camera.

### 6.3 Step 2: Set Up Laser Drivers and Verify Lasers

1. **If using Thorlabs CLD1015:** Insert butterfly laser into the CLD1015 socket. Connect power. Set current limit to 80% of laser's rated max. Slowly increase current until power output stabilizes (monitor via CLD1015 built-in photodiode readout).

2. **If using DIY drivers:** Assemble WLD3343 driver board. Connect butterfly laser via 14-pin socket. CRITICAL: Always connect laser ground before power. Set current limit resistor for max safe current. Power on and verify with a fiber-coupled power meter or a simple InGaAs photodiode + multimeter.

3. Verify each laser independently:
   - 1550 nm: Use an InGaAs photodiode or IR viewer card. Fiber output should show >1 mW.
   - 1310 nm: Same as above.
   - 1064 nm: Visible on a phosphor IR card. Should be well above 1 mW.

4. Connect all three laser fibers to the WDM combiner. Verify that all three wavelengths appear at the combiner output (use an optical spectrum analyzer if available, or just verify power adds up).

5. Connect the combiner output to the V-groove fiber array input via FC/APC patch cable.

### 6.4 Step 3: Mount and Interface the Chip

**Option A: Wire-bonded chip on PCB carrier (recommended for repeated testing)**

1. Apply thermal epoxy to the AlN submount. Place the chip die face-up using tweezers under a microscope. Cure epoxy per manufacturer instructions (typically 150 degC for 1 hour, or room-temp cure for 24 hours with appropriate adhesive).

2. Attach the AlN submount to the PCB carrier board with thermal epoxy.

3. Wire bond the following pads (MVP minimum):
   - 2x GND pads (distributed)
   - 1x VDD pad
   - 5x photodetector pads for PE[0,8] (the bottom-right PE, closest to the output edge)
   - Total: 8 wire bonds

4. Solder header pins to the PCB carrier for easy connection to TIA board.

5. Mount the PCB carrier on the chip holder, with the chip facet (left edge) accessible for fiber coupling.

**Option B: Probe station (for die-level testing without bonding)**

1. Place the chip on the probe station vacuum chuck.
2. Use tungsten needle probes to contact individual bond pads.
3. One probe per detector pad, one for ground, one for VDD.
4. This is slower but does not require wire bonding. Good for initial verification.

### 6.5 Step 4: Fiber Alignment to Chip

This is the most critical and time-consuming step. Take your time.

1. **Coarse alignment:**
   - Position the V-groove fiber array on the 3-axis stage.
   - Using the USB microscope, bring the fiber tips within ~100 um of the chip's left edge (where the edge couplers are).
   - The fiber array channels should be approximately aligned with the chip's input_a and input_b ports (Y = 2.0 mm and Y = 1.4 mm from the bottom corner).

2. **Illuminate for alignment:**
   - Turn on the 1550 nm laser at low power (~1 mW).
   - Use an InGaAs camera or IR card behind/above the chip to look for scattered light from the chip. This indicates some light is entering.

3. **Active alignment:**
   - Connect one of the on-chip photodetector pads (via wire bond or probe) to a TIA or simple current meter (nanoamp range).
   - Slowly move the fiber in X (lateral) while monitoring detector current. You are looking for a peak.
   - Once you find the X peak, optimize Y (vertical).
   - Then optimize Z (gap). Move closer until current peaks, then back off slightly.
   - Iterate X/Y/Z until maximum detector current is achieved.
   - Expected coupling loss: 1-3 dB per facet. If you are getting >10 dB loss, the alignment is poor -- keep optimizing.

4. **Lock alignment:**
   - Once optimal position is found, if using UV-cure adhesive: apply a small drop of UV-cure adhesive (Norland NOA 61 or similar) between the fiber array and chip facet. Cure with a UV lamp (365 nm, 30 seconds).
   - If not using adhesive: do not touch the stage. Any vibration will shift the alignment. Consider adding a small clamp or set screw.

5. **Verify coupling:**
   - With alignment locked, turn on all three lasers sequentially.
   - Verify that detector current is present for each wavelength.
   - Record the coupling efficiency (input power vs detected power).

### 6.6 Step 5: Connect TIA and Verify Detector Signals

1. Connect the wire-bonded detector pads to the TIA board inputs via short wires (<10 cm to minimize noise pickup).

2. Apply reverse bias to the photodetectors: -1 V to -3 V. Start at -1 V. This is provided through the PCB carrier (a voltage divider or LDO from VDD).

3. Power on the TIA. Connect TIA output to an oscilloscope or multimeter.

4. Turn on each laser one at a time:
   - 1550 nm ON, others OFF --> should see signal on DET_-1 or DET_-2 (the detectors corresponding to RED-containing SFG products).
   - Wait: for a SINGLE laser with no partner wavelength, there is no SFG product. You need BOTH operand A and operand B lasers on simultaneously to produce SFG.

5. **Correct procedure for SFG verification:**
   - Both lasers must be on simultaneously. The SFG mixer in the PE produces output only when two input wavelengths are present.
   - Set Operand A = BLUE (+1, 1064 nm) and Operand B = BLUE (+1, 1064 nm): expect BLUE+BLUE SFG at 532 nm on DET_+2.
   - Set Operand A = RED (-1, 1550 nm) and Operand B = RED (-1, 1550 nm): expect RED+RED SFG at 775 nm on DET_-2.
   - If you see signal on the expected detectors, the chip is working.

6. Record baseline readings with all lasers OFF (dark current) and with each combination ON (signal levels). This data is used for threshold calibration.

### 6.7 Step 6: Connect FPGA and Run First Test

1. **Red Pitaya setup:**
   - Connect Red Pitaya to your network via Ethernet.
   - Access web interface at `rp-XXXX.local` (XXXX = serial number).
   - Install SCPI server if not already running.
   - Verify you can send commands from Python on your PC.

2. **Connect signals:**
   - Red Pitaya GPIO pins --> laser enable signals (via level shifter if needed, lasers may need 5 V logic, Red Pitaya outputs 3.3 V).
   - Red Pitaya ADC Input 1 --> TIA output (start with one channel).
   - Red Pitaya DAC Output 1 --> laser current control (if using analog modulation).

3. **Run the basic test script:**
   ```
   python main.py --mode dc_test --pe 0,8 --vectors multiplication
   ```

4. The script will:
   - Turn on each laser combination per the truth table
   - Wait for settling
   - Read the ADC
   - Compare to expected
   - Print PASS/FAIL for each test case

5. If all 9 multiplication vectors pass: the chip works. Celebrate.

### 6.8 Step 7: Calibrate Thresholds

1. Run a calibration routine:
   - Measure dark current (all lasers off) for each detector: this is the noise floor.
   - Measure each known-good SFG combination: this is the signal level.
   - Set threshold = (noise_floor + signal_level) / 2.
   - Save calibration data to `data/calibration/`.

2. Re-run tests with calibrated thresholds. False positives/negatives should disappear.

3. Measure signal-to-noise ratio (SNR):
   - SNR = 20 * log10(signal / noise).
   - Target: SNR > 20 dB for reliable detection.
   - If SNR < 10 dB: check fiber alignment, laser power, TIA gain.

### 6.9 Step 8: Thermal Stabilization (If Needed)

1. Attach NTC thermistor to the AlN submount with thermal epoxy.

2. Connect thermistor to ADC (or dedicated temperature monitor).

3. Monitor chip temperature over 30 minutes of continuous testing.

4. If temperature drifts by more than 0.5 degC:
   - Add the TEC module under the AlN submount.
   - Connect TEC to TEC controller.
   - Set target temperature to 25.0 degC.
   - Enable PID loop.
   - Verify stability to +/- 0.1 degC.

5. If temperature is stable without TEC: skip the TEC. One less thing to break.

---

## 7. Cost Summary

### 7.1 MVP Configuration

| Category | Budget Path | Comfortable Path |
|----------|-------------|------------------|
| Laser sources | $1,150 | $1,150 |
| Laser drivers | $300 (DIY) | $4,500 (CLD1015 x3) |
| Optical components | $638 | $638 |
| Alignment/mechanical | $730 | $730 |
| FPGA/control | $350 | $350 |
| TIA amplifiers | $209 | $209 |
| Chip packaging | $415 | $415 |
| Thermal management | $224 | $224 |
| **TOTAL** | **$4,016** | **$8,216** |

### 7.2 Full Configuration

| Category | Cost |
|----------|------|
| MVP (budget path) | $4,016 |
| Upgraded electronics | $2,260 |
| Upgraded optical (EOMs, OSA) | $5,550 |
| Upgraded thermal | $1,230 |
| Upgraded packaging (full wire bond, probe station) | $3,150 |
| **FULL TOTAL** | **$16,206** |

### 7.3 Bare-Bones MVP (Maximum DIY)

| Item | Cost |
|------|------|
| Salvaged SFP+ lasers (1550 + 1310) | $40 |
| CNI 1064 nm DPSS module | $200 |
| DIY laser drivers (WLD3343 x3) | $300 |
| V-groove fiber array (2 ch) | $300 |
| Broadband 3x1 coupler | $100 |
| Fiber patch cables | $90 |
| MicroBlock 3-axis stage | $350 |
| Steel breadboard + posts | $150 |
| Arduino Due + ADS1115 x2 | $40 |
| DIY TIA (LM358 x5) | $10 |
| AlN submount + die attach | $65 |
| Wire bonding (8 bonds, university service) | $100 |
| NTC thermistor + passive heatsink | $15 |
| PCB carrier (JLCPCB) | $50 |
| **TOTAL** | **$1,810** |

### 7.4 What Christopher Likely Already Has

| Item | Likely Has? | If Not, Cost |
|------|-------------|--------------|
| Multimeter | Yes | $30 |
| Soldering station | Yes | $50 |
| Computer with Python | Yes | $0 |
| USB cables | Yes | $0 |
| Basic hand tools | Yes | $0 |
| Oscilloscope | Maybe | $300 used |
| Optical power meter | Probably not | $200 |
| Fiber cleaver | Probably not | $50 (basic) |
| IR viewing card | Probably not | $20 |
| UV cure lamp (365 nm) | Probably not | $25 |

### 7.5 Recommended Purchase Order (Phased)

**Phase 1 -- Order immediately (long lead-time items):**
- V-groove fiber array (4-6 week lead time from OZ Optics or PHIX)
- Custom PCB carrier boards (1-2 week from JLCPCB)
- Wire bonding service booking (schedule with university)

**Phase 2 -- Order next (standard items):**
- Laser sources (Thorlabs ships in 1-3 days for stock items)
- Laser driver components (WLD3343, butterfly sockets)
- Red Pitaya STEMlab 125-14
- MicroBlock stage and breadboard
- Fiber patch cables and WDM combiner

**Phase 3 -- Order after chip arrives:**
- TIA components (OPA857 ICs)
- Thermal management components (TEC, thermistor)
- Mounting hardware (posts, holders)

**Phase 4 -- Order after first light:**
- Oscilloscope (if needed for debugging)
- Additional ADC channels
- EOM for dynamic testing

---

## Appendix A: Key Specifications Quick Reference

| Parameter | Value | Source |
|-----------|-------|--------|
| Chip size | 1095 x 695 um | MONOLITHIC_9x9_VALIDATION.md |
| Array size | 9x9 = 81 PEs | Architecture spec |
| PE pitch | 55 um | monolithic_chip_9x9.py |
| Input wavelengths | 1550, 1310, 1064 nm | CHIP_INTERFACE.md |
| SFG outputs | 532.0, 587.1, 630.9, 655.0, 710.0, 775.0 nm | MONOLITHIC_9x9_VALIDATION.md |
| Detector count | 5 per PE x 81 PEs = 405 | PACKAGING_SPEC.md |
| Heater count | 486 | PACKAGING_SPEC.md |
| Total bond pads | ~1100 | PACKAGING_SPEC.md |
| Kerr clock freq | 617 MHz | Architecture spec |
| Power margin | 18.70 dB | MONOLITHIC_9x9_VALIDATION.md |
| Coupling loss target | 1-2 dB per facet | PACKAGING_SPEC.md |
| Operating temp | 20-40 degC, +/- 0.1 degC | PACKAGING_SPEC.md |
| Chip dissipation | 2-3 W max | PACKAGING_SPEC.md |
| Detector photocurrent | 1-100 uA | CHIP_INTERFACE.md |
| Detector bandwidth | >1 GHz | CHIP_INTERFACE.md |

## Appendix B: Ternary SFG Truth Table (Physical Basis)

The SFG (Sum-Frequency Generation) process converts two input photons into one output photon whose frequency is the sum of the input frequencies. This is the physical mechanism by which every PE computes -- all PEs physically perform addition via SFG. The IOC determines meaning: in ADD/SUB mode, inputs are raw ternary values and SFG performs straight addition; in MUL/DIV mode, the IOC log-encodes inputs so that SFG addition of logs yields multiplication in the original domain.

| Input A (wavelength) | Input B (wavelength) | SFG Output (wavelength) | SFG Output (frequency) | Trit Result |
|---------------------|---------------------|------------------------|----------------------|-------------|
| 1550 nm (RED, -1) | 1550 nm (RED, -1) | 775.0 nm | 387 THz | DET_-2: borrow |
| 1550 nm (RED, -1) | 1310 nm (GREEN, 0) | 710.0 nm | 423 THz | DET_-1: result -1 |
| 1550 nm (RED, -1) | 1064 nm (BLUE, +1) | 630.9 nm | 476 THz | DET_0: result 0 |
| 1310 nm (GREEN, 0) | 1310 nm (GREEN, 0) | 655.0 nm | 458 THz | DET_0: result 0 |
| 1310 nm (GREEN, 0) | 1064 nm (BLUE, +1) | 587.1 nm | 511 THz | DET_+1: result +1 |
| 1064 nm (BLUE, +1) | 1064 nm (BLUE, +1) | 532.0 nm | 564 THz | DET_+2: carry |

Minimum wavelength spacing between SFG products: 24.1 nm (between 630.9 and 655.0). This is sufficient for AWG-based demultiplexing on-chip.

---

*Document generated 2026-02-17, updated 2026-02-18. Budget estimates are approximate and based on publicly available pricing as of February 2026. Actual costs may vary. All component suggestions are recommendations -- equivalent parts from other vendors will work.*
