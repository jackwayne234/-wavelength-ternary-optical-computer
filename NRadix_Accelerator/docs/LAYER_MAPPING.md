# Layer Mapping Reference

**Wavelength-Division Ternary Optical Computer**
**Version 1.0 | February 5, 2026**

This document provides the definitive layer mapping for foundry submission. Use this to adapt the generic GDS design to any foundry's process design kit (PDK).

---

## Table of Contents

1. [Complete Layer Table](#complete-layer-table)
2. [Layer Stack Cross-Section](#layer-stack-cross-section)
3. [Foundry Mapping Guide](#foundry-mapping-guide)
4. [Critical vs Optional Layers](#critical-vs-optional-layers)
5. [Color Coding for GDS Viewers](#color-coding-for-gds-viewers)
6. [Layer Details and Process Notes](#layer-details-and-process-notes)

---

## Complete Layer Table

### Core Functional Layers

| Layer | Datatype | Name | Purpose | Material | Process | Critical |
|-------|----------|------|---------|----------|---------|----------|
| 1 | 0 | WAVEGUIDE | Waveguide core pattern | LiNbO3 | RIE etch 400nm | **YES** |
| 2 | 0 | CHI2_SFG | SFG mixer region (addition) | PPLN | Electrode + poling | **YES** |
| 3 | 0 | PHOTODET | Photodetector region | Ge/InGaAs | Deposition | **YES** |
| 4 | 0 | CHI2_DFG | DFG mixer region (subtraction) | PPLN | Electrode + poling | **YES** |
| 5 | 0 | KERR_CLK | Kerr clock resonator | LiNbO3 chi3 | Etch | Optional |
| 6 | 0 | AWG_BODY | AWG demultiplexer body | LiNbO3 | Etch | **YES** |
| 7 | 0 | CHI3_MUL | Kerr mixer region (multiply) | LiNbO3 chi3 | Etch | Optional |

### Metal and Electrical Layers

| Layer | Datatype | Name | Purpose | Material | Process | Critical |
|-------|----------|------|---------|----------|---------|----------|
| 10 | 0 | METAL1_HEATER | MZI phase shifter heaters | TiN 100nm | Liftoff | **YES** |
| 11 | 0 | CARRY_PATH | Optical carry delay lines | LiNbO3 | Etch | Optional |
| 12 | 0 | METAL2_PAD | Bond pads, detector contacts | Ti/Au 520nm | Liftoff | **YES** |

### Doping Layers

| Layer | Datatype | Name | Purpose | Material | Process | Critical |
|-------|----------|------|---------|----------|---------|----------|
| 13 | 0 | DOPING_SA | Saturable absorber (log converter) | Er/Yb implant | Ion implant | Optional |
| 14 | 0 | DOPING_GAIN | Gain medium (exp converter/SOA) | Er/Yb implant | Ion implant | Optional |

### Auxiliary Layers

| Layer | Datatype | Name | Purpose | Material | Process | Critical |
|-------|----------|------|---------|----------|---------|----------|
| 20 | 0 | BOUNDARY | Chip boundary / Round Table outline | N/A | Documentation | No |
| 99 | 0 | ALIGNMENT | Alignment marks for layer registration | Cr/Au | Liftoff | **YES** |
| 100 | 0 | LABEL | Text labels (toggle off for fab) | N/A | Documentation | No |

---

## Layer Stack Cross-Section

```
                        CROSS-SECTION (not to scale)

    ═══════════════════════════════════════════════════════════════════════

                     ┌─────────┐                    ┌─────────┐
                     │ METAL2  │                    │ METAL2  │
                     │  PAD    │                    │  PAD    │
                     │(Ti/Au)  │                    │ (12,0)  │
                     └────┬────┘                    └────┬────┘
                          │                              │
    ══════════════════════╪══════════════════════════════╪═════════════════
                          │                              │
                     ┌────┴────┐                         │
                     │  HEATER │                         │
                     │  (TiN)  │                         │
                     │ (10,0)  │                         │
                     └────┬────┘                         │
    ──────────────────────┼─────────────────────────────┼─────────────────
         AIR CLADDING     │      n = 1.0                 │
    ──────────────────────┼─────────────────────────────┼─────────────────
                          │                              │
                    ┌─────┴─────┐              ┌────────┴────────┐
                    │ WAVEGUIDE │              │   PHOTODETECTOR │
                    │   CORE    │              │    (Ge/InGaAs)  │
                    │  (1,0)    │              │      (3,0)      │
                    │  500nm W  │              │                 │
                    │  400nm H  │              │                 │
                    └─────┬─────┘              └────────┬────────┘
                          │                             │
    ══════════════════════╪═════════════════════════════╪═════════════════
                          │     SUBSTRATE               │
                          │     X-cut LiNbO3            │
                          │     n = 2.2                 │
                          │                             │
              ┌───────────┴───────────┐     ┌──────────┴──────────┐
              │   PPLN POLED REGION   │     │   DOPED REGION      │
              │   (2,0) SFG or        │     │   (13,0) SA or      │
              │   (4,0) DFG           │     │   (14,0) GAIN       │
              │   Period: 6.5-12 um   │     │   Er: 1-2e15 cm^-2  │
              └───────────────────────┘     └─────────────────────┘

    ═══════════════════════════════════════════════════════════════════════


    LAYER STACK (VERTICAL ORDER - BOTTOM TO TOP):

    ┌──────────────────────────────────────────────────────────────────────┐
    │  METAL2_PAD (12,0)     Ti 20nm / Au 500nm      Wire bonding          │
    ├──────────────────────────────────────────────────────────────────────┤
    │  METAL1_HEATER (10,0)  TiN 100nm               Phase shifters        │
    ├──────────────────────────────────────────────────────────────────────┤
    │  PHOTODET (3,0)        Ge or InGaAs            Output detection      │
    ├──────────────────────────────────────────────────────────────────────┤
    │  WAVEGUIDE (1,0)       LiNbO3 etch 400nm       Core optical layer    │
    ├──────────────────────────────────────────────────────────────────────┤
    │  DOPING (13,0)(14,0)   Er/Yb implant           Log/Exp converters    │
    ├──────────────────────────────────────────────────────────────────────┤
    │  CHI2 POLING (2,0)(4,0) Electrode + HV         Nonlinear mixing      │
    ├──────────────────────────────────────────────────────────────────────┤
    │  SUBSTRATE             X-cut LiNbO3 500um      Carrier wafer         │
    └──────────────────────────────────────────────────────────────────────┘
```

---

## Foundry Mapping Guide

### AIM Photonics (USA)

AIM uses a silicon photonics platform with SiN options.

| Our Layer | AIM Layer | Notes |
|-----------|-----------|-------|
| (1, 0) WAVEGUIDE | WG or SiN_CORE | Use SiN for lower loss |
| (2, 0) CHI2_SFG | N/A | **Requires hybrid bonding** - no native chi2 |
| (3, 0) PHOTODET | GE_PD | Germanium photodetector |
| (4, 0) CHI2_DFG | N/A | **Requires hybrid bonding** |
| (6, 0) AWG_BODY | WG or SiN_CORE | Same as waveguide |
| (10, 0) HEATER | HEATER or TiN | Thermo-optic tuning |
| (12, 0) METAL2_PAD | M2 or PAD | Bond pad metallization |

**Notes:**
- AIM is silicon-based; chi2 nonlinearity requires heterogeneous integration
- Consider their GaAs or InP options for native nonlinearity
- Excellent for passive components and photodetectors

### IMEC (Belgium)

IMEC offers advanced silicon photonics with various active material integrations.

| Our Layer | IMEC Layer | Notes |
|-----------|-----------|-------|
| (1, 0) WAVEGUIDE | SI or SIN_WG | Check thickness options |
| (2, 0) CHI2_SFG | Custom | Discuss hybrid LiNbO3 integration |
| (3, 0) PHOTODET | GE_PD | Standard Ge detector |
| (4, 0) CHI2_DFG | Custom | Same as SFG |
| (6, 0) AWG_BODY | SI or SIN_WG | Standard waveguide |
| (10, 0) HEATER | HEATER | TiN heater layer |
| (12, 0) METAL2_PAD | M2_PAD | Al or Cu metallization |

**Notes:**
- IMEC has research programs for LiNbO3 on insulator (LNOI)
- Ask about their heterogeneous integration services
- Strong AWG and passive component library

### Ligentec (Switzerland)

Ligentec specializes in ultra-low-loss silicon nitride.

| Our Layer | Ligentec Layer | Notes |
|-----------|---------------|-------|
| (1, 0) WAVEGUIDE | AN800 or AN1200 | 800nm or 1200nm SiN |
| (2, 0) CHI2_SFG | Custom | No native chi2 - post-processing |
| (3, 0) PHOTODET | Custom | External or hybrid |
| (4, 0) CHI2_DFG | Custom | Same as SFG |
| (6, 0) AWG_BODY | AN800 or AN1200 | Standard waveguide |
| (10, 0) HEATER | HEATER | Standard heater |
| (12, 0) METAL2_PAD | METAL | Bond pads |

**Notes:**
- Excellent for passive routing (0.1 dB/cm loss)
- Chi2 requires DR1 poled polymer deposition or LiNbO3 bonding
- Best option if using external nonlinear elements

### HyperLight (USA) - RECOMMENDED

HyperLight is the **best match** for this design - native thin-film LiNbO3.

| Our Layer | HyperLight Layer | Notes |
|-----------|-----------------|-------|
| (1, 0) WAVEGUIDE | WG | Native TFLN waveguide |
| (2, 0) CHI2_SFG | PPLN or EO | **Native support** - periodic poling |
| (3, 0) PHOTODET | Custom | Hybrid Ge or InGaAs |
| (4, 0) CHI2_DFG | PPLN or EO | **Native support** |
| (6, 0) AWG_BODY | WG | Standard waveguide |
| (7, 0) CHI3_MUL | WG | LiNbO3 has weak chi3 |
| (10, 0) HEATER | HEATER | Standard heater |
| (12, 0) METAL2_PAD | METAL | Bond pads |

**Notes:**
- **Primary recommendation** for this project
- Native chi2 d33 ~ 30 pm/V enables efficient SFG/DFG
- Supports wavelength range 0.5-2.0 um
- Ask about periodic poling services for phase matching

### Applied Nanotools (Canada)

High-resolution e-beam lithography services.

| Our Layer | ANT Layer | Notes |
|-----------|-----------|-------|
| (1, 0) WAVEGUIDE | Core | Custom material deposition |
| (2, 0) CHI2_SFG | Custom | Poled polymer or LiNbO3 |
| (3, 0) PHOTODET | Custom | External |
| (10, 0) HEATER | Metal | Custom metallization |
| (12, 0) METAL2_PAD | Metal | Bond pads |

**Notes:**
- Best for R&D and small feature sizes
- Can work with customer-supplied wafers
- Consider for prototyping before full MPW run

---

## Critical vs Optional Layers

### CRITICAL LAYERS (Required for Basic Function)

These layers are **mandatory** for any functional chip:

| Layer | Why Critical |
|-------|-------------|
| (1, 0) WAVEGUIDE | Defines all optical paths - without this, no light propagation |
| (2, 0) CHI2_SFG | Enables addition operation - core arithmetic function |
| (3, 0) PHOTODET | Output readout - required to observe results |
| (6, 0) AWG_BODY | Wavelength separation - essential for ternary decoding |
| (10, 0) HEATER | Active tuning - compensates fab variations |
| (12, 0) METAL2_PAD | Electrical I/O - heater control and detector readout |
| (99, 0) ALIGNMENT | Layer registration - multi-layer alignment |

### OPTIONAL LAYERS (Enhanced Functionality)

These layers add capabilities but are not required for MVP:

| Layer | Function | When to Include |
|-------|----------|-----------------|
| (4, 0) CHI2_DFG | Subtraction | If subtraction operation needed |
| (5, 0) KERR_CLK | On-chip clock | If optical clock distribution used |
| (7, 0) CHI3_MUL | Multiplication | If multiply operation needed |
| (11, 0) CARRY_PATH | Optical carry | If full arithmetic carry chain used |
| (13, 0) DOPING_SA | Log converter | If log-domain processing used |
| (14, 0) DOPING_GAIN | Amplification | If on-chip SOAs needed |

### DOCUMENTATION ONLY (Never Fabricated)

| Layer | Purpose |
|-------|---------|
| (20, 0) BOUNDARY | Chip outline for visualization |
| (100, 0) LABEL | Text annotations - toggle off before export |

---

## Color Coding for GDS Viewers

Recommended colors for KLayout, L-Edit, and other GDS viewers:

### KLayout Layer Properties

```xml
<!-- Copy this to your KLayout layer properties file -->
<!-- File: ~/.klayout/layer_properties.xml -->

<layer-properties>
  <properties>
    <frame-color>#0000ff</frame-color>
    <fill-color>#0000ff</fill-color>
    <frame-brightness>0</frame-brightness>
    <fill-brightness>0</fill-brightness>
    <dither-pattern>I1</dither-pattern>
    <valid>true</valid>
    <visible>true</visible>
    <transparent>false</transparent>
    <width>1</width>
    <marked>false</marked>
    <source>1/0@1</source>
    <name>WAVEGUIDE</name>
  </properties>
</layer-properties>
```

### Color Table

| Layer | Color (Hex) | RGB | Visual |
|-------|-------------|-----|--------|
| (1, 0) WAVEGUIDE | #0066CC | 0, 102, 204 | Blue (optical core) |
| (2, 0) CHI2_SFG | #FF6600 | 255, 102, 0 | Orange (nonlinear) |
| (3, 0) PHOTODET | #9900CC | 153, 0, 204 | Purple (detection) |
| (4, 0) CHI2_DFG | #FF9933 | 255, 153, 51 | Light orange |
| (5, 0) KERR_CLK | #00CC66 | 0, 204, 102 | Green (clock) |
| (6, 0) AWG_BODY | #3399FF | 51, 153, 255 | Light blue |
| (7, 0) CHI3_MUL | #CC6600 | 204, 102, 0 | Brown (chi3) |
| (10, 0) HEATER | #CC0000 | 204, 0, 0 | Red (heat) |
| (11, 0) CARRY | #666666 | 102, 102, 102 | Gray |
| (12, 0) METAL_PAD | #FFCC00 | 255, 204, 0 | Gold (metal) |
| (13, 0) DOPING_SA | #99CC00 | 153, 204, 0 | Yellow-green |
| (14, 0) DOPING_GAIN | #00CC99 | 0, 204, 153 | Teal |
| (99, 0) ALIGNMENT | #FF00FF | 255, 0, 255 | Magenta |
| (100, 0) LABEL | #999999 | 153, 153, 153 | Gray (documentation) |

### Quick Setup Script (KLayout)

Save as `setup_layers.py` and run in KLayout:

```python
# KLayout layer setup script
import pya

view = pya.Application.instance().main_window().current_view()
if view:
    lp = view.begin_layers()

    colors = {
        (1, 0): 0x0066CC,   # WAVEGUIDE - Blue
        (2, 0): 0xFF6600,   # CHI2_SFG - Orange
        (3, 0): 0x9900CC,   # PHOTODET - Purple
        (4, 0): 0xFF9933,   # CHI2_DFG - Light orange
        (5, 0): 0x00CC66,   # KERR_CLK - Green
        (6, 0): 0x3399FF,   # AWG_BODY - Light blue
        (7, 0): 0xCC6600,   # CHI3_MUL - Brown
        (10, 0): 0xCC0000,  # HEATER - Red
        (11, 0): 0x666666,  # CARRY - Gray
        (12, 0): 0xFFCC00,  # METAL_PAD - Gold
        (13, 0): 0x99CC00,  # DOPING_SA - Yellow-green
        (14, 0): 0x00CC99,  # DOPING_GAIN - Teal
        (99, 0): 0xFF00FF,  # ALIGNMENT - Magenta
        (100, 0): 0x999999, # LABEL - Gray
    }

    for (layer, datatype), color in colors.items():
        li = view.layer_info(layer, datatype)
        props = view.layer_properties_iter(li)
        if props:
            p = props.next()
            p.fill_color = color
            p.frame_color = color

    print("Layer colors configured!")
```

---

## Layer Details and Process Notes

### Layer (1, 0) - WAVEGUIDE

**Purpose:** Defines all optical waveguide paths including bus waveguides, ring resonators, Y-junctions, MMI couplers, and AWG waveguide arrays.

**Design Rules:**
- Minimum width: 500 nm (single-mode at 1.55 um)
- Minimum spacing: 500 nm (avoid coupling)
- Minimum bend radius: 5 um (ring resonators can go to 0.8 um with simulation verification)
- Coupling gap: 150 nm for ring-bus coupling

**Process:**
- Material: LiNbO3 thin film on insulator (TFLN)
- Etch depth: 400 nm (partial etch, leaves slab)
- Target sidewall angle: 85-90 degrees
- Resist: ZEP520A or PMMA (positive)
- Lithography: E-beam or DUV stepper

### Layer (2, 0) - CHI2_SFG

**Purpose:** Marks regions for periodic poling to enable sum-frequency generation (addition).

**Design Rules:**
- Mixer length: 20 um minimum for efficient conversion
- Mixer width: 800 nm (phase matching)
- Poling period: 6.5-7.0 um (for 1.55 + 1.0 um -> 0.608 um)

**Process:**
- Deposit electrode pattern (Cr/Au 200 nm)
- Apply high-voltage poling (21 kV/mm)
- Poling at room temperature with current monitoring
- QC: SHG efficiency test

### Layer (3, 0) - PHOTODET

**Purpose:** Marks photodetector absorption regions for output readout.

**Design Rules:**
- Detector length: 20 um minimum
- Detector width: 2-5 um
- Must align with waveguide output

**Process:**
- Germanium epitaxy (for telecom wavelengths)
- Or InGaAs bonding (for visible SFG outputs 0.5-0.8 um)
- Metal contacts to METAL2_PAD layer

### Layer (4, 0) - CHI2_DFG

**Purpose:** Marks regions for periodic poling to enable difference-frequency generation (subtraction).

**Design Rules:**
- Mixer length: 25 um (longer than SFG for lower efficiency)
- Mixer width: 800 nm
- Poling period: 10-12 um (different from SFG)

**Process:** Same as SFG but different poling period.

### Layer (10, 0) - METAL1_HEATER

**Purpose:** Thermo-optic phase shifters for MZI switches and ring resonator tuning.

**Design Rules:**
- Heater width: 2 um minimum
- Heater length: 30-50 um for pi phase shift
- Offset from waveguide: 1 um (avoid optical absorption)
- Sheet resistance: 50-100 ohm/sq

**Process:**
- Material: TiN 100 nm
- Deposition: Sputtering
- Pattern: Liftoff with PMMA bilayer
- QC: Sheet resistance measurement

### Layer (12, 0) - METAL2_PAD

**Purpose:** Wire bonding pads and electrical contacts for heaters and detectors.

**Design Rules:**
- Pad size: 100 x 100 um minimum (wire bonding)
- Pad pitch: 150 um minimum
- Metal stack: Ti adhesion (20 nm) + Au (500 nm)

**Process:**
- Deposition: E-beam evaporation
- Pattern: Liftoff
- QC: Wire bond pull test >5g

### Layer (13, 0) - DOPING_SA

**Purpose:** Creates saturable absorber regions for optical log conversion.

**Design Rules:**
- Region length: 50-100 um
- Must overlap with waveguide core

**Process:**
- Ion species: Er and Yb co-doping
- Er dose: 1e15 cm^-2
- Yb dose: 5e14 cm^-2
- Energy: 200 keV
- Post-implant anneal: 600C, 30 min, O2
- QC: PL spectrum, absorption >3 dB at 1.55 um

### Layer (14, 0) - DOPING_GAIN

**Purpose:** Creates gain regions for optical amplification and exp conversion.

**Design Rules:**
- Region length: 100-500 um
- Must overlap with waveguide core
- Requires pump light input (980 nm)

**Process:**
- Ion species: Er and Yb co-doping (higher dose than SA)
- Er dose: 2e15 cm^-2
- Yb dose: 1e15 cm^-2
- Energy: 200 keV
- Post-implant anneal: 600C, 30 min, O2
- QC: PL spectrum, gain >10 dB with 980 nm pump

---

## Mask File Reference

Individual mask GDS files are generated in:
`/Research/data/gds/masks/`

| Mask File | Layers | Process Step |
|-----------|--------|--------------|
| WAVEGUIDE.gds | (1, 0) | RIE etch 400nm LiNbO3 |
| CHI2_POLING.gds | (2, 0), (4, 0) | PPLN electrode + poling |
| METAL1_HEATER.gds | (10, 0) | Liftoff 100nm TiN |
| METAL2_PAD.gds | (12, 0) | Liftoff 500nm Au |
| DOPING_SA.gds | (13, 0) | Er/Yb implant (log) |
| DOPING_GAIN.gds | (14, 0) | Er/Yb implant (gain) |

See `process_traveler.md` for complete fabrication sequence.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-05 | Initial release - comprehensive layer mapping |

---

*Generated for the Wavelength-Division Ternary Optical Computer Project*
*Paper: DOI 10.5281/zenodo.18437600*
*Repository: https://github.com/jackwayne234/-wavelength-ternary-optical-computer*
