# Copyright (c) 2026 Christopher Riner
# Licensed under the MIT License. See LICENSE file for details.
#
# Wavelength-Division Ternary Optical Computer
# https://github.com/jackwayne234/-wavelength-ternary-optical-computer
#
# This file is part of an open source research project to develop a
# ternary optical computer using wavelength-division multiplexing.
# The research is documented in the paper published on Zenodo:
# DOI: 10.5281/zenodo.18437600

"""
Fabrication Mask Layer Generator

Extracts individual mask layers from the complete chip GDS for foundry
fabrication. Each layer corresponds to a specific fabrication process step.

Layer Mapping:
    WAVEGUIDE (1, 0)      -> RIE etch 400nm LiNbO3
    METAL1_HEATER (10, 0) -> Liftoff 100nm TiN heaters
    METAL2_PAD (12, 0)    -> Liftoff 500nm Au bond pads
    CHI2_POLING (2, 0), (4, 0) -> PPLN electrode patterning
    DOPING_SA (13, 0)     -> Er/Yb implant for saturable absorber
    DOPING_GAIN (14, 0)   -> Er/Yb implant for gain medium

Output:
    - Individual GDS files per mask layer
    - Process traveler markdown document
    - Alignment mark additions for multi-layer registration
"""

import os
import sys
import gdsfactory as gf
from gdsfactory.component import Component
import numpy as np

# Activate the generic PDK
gf.gpdk.PDK.activate()

# Ensure we can import local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Base directory for data output
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
GDS_DIR = os.path.join(DATA_DIR, 'gds')
MASK_DIR = os.path.join(GDS_DIR, 'masks')

# Ensure directories exist
os.makedirs(MASK_DIR, exist_ok=True)

# =============================================================================
# LAYER DEFINITIONS
# =============================================================================
# Source layers from ternary_chip_generator.py

LAYER_MAPPING = {
    'WAVEGUIDE': {
        'source_layers': [(1, 0)],
        'description': 'Waveguide core pattern',
        'process': 'RIE etch 400nm LiNbO3',
        'notes': 'Main waveguide layer - defines all optical paths'
    },
    'METAL1_HEATER': {
        'source_layers': [(10, 0)],
        'description': 'Heater electrodes for MZI phase shifters',
        'process': 'Liftoff 100nm TiN',
        'notes': 'Thermo-optic phase control for MZI switches'
    },
    'METAL2_PAD': {
        'source_layers': [(12, 0)],
        'description': 'Bond pads for electrical connections',
        'process': 'Liftoff 500nm Au',
        'notes': 'Wire bonding pads for heater control and detector readout'
    },
    'CHI2_POLING': {
        'source_layers': [(2, 0), (4, 0)],
        'description': 'Periodically poled LiNbO3 regions',
        'process': 'PPLN electrode patterning + high-voltage poling',
        'notes': 'Defines chi2 nonlinear regions for SFG/DFG mixers'
    },
    'DOPING_SA': {
        'source_layers': [(13, 0)],
        'description': 'Saturable absorber doping regions',
        'process': 'Er/Yb ion implant (log converter)',
        'notes': 'Creates saturable absorption for log-domain processing'
    },
    'DOPING_GAIN': {
        'source_layers': [(14, 0)],
        'description': 'Gain medium doping regions',
        'process': 'Er/Yb ion implant (exp converter / SOA)',
        'notes': 'Creates optical gain for amplification and exp conversion'
    }
}

# Alignment mark layer
ALIGNMENT_LAYER = (99, 0)


def add_alignment_marks(
    component: Component,
    chip_size_um: tuple = (10000, 10000),
    mark_size_um: float = 100.0,
    mark_spacing_um: float = 500.0
) -> Component:
    """
    Adds alignment marks at chip corners for multi-layer registration.

    Standard alignment marks include:
    - Cross marks at all four corners
    - Vernier scales for fine alignment verification
    - Layer identification text

    Args:
        component: GDS component to add marks to
        chip_size_um: (width, height) of chip in microns
        mark_size_um: Size of alignment cross
        mark_spacing_um: Distance from chip edge to marks

    Returns:
        Modified component with alignment marks
    """
    w, h = chip_size_um
    corners = [
        (-w/2 + mark_spacing_um, -h/2 + mark_spacing_um),   # Bottom-left
        (w/2 - mark_spacing_um, -h/2 + mark_spacing_um),    # Bottom-right
        (-w/2 + mark_spacing_um, h/2 - mark_spacing_um),    # Top-left
        (w/2 - mark_spacing_um, h/2 - mark_spacing_um),     # Top-right
    ]

    cross_width = mark_size_um / 10

    for i, (cx, cy) in enumerate(corners):
        # Horizontal bar of cross
        component.add_polygon(
            [
                (cx - mark_size_um/2, cy - cross_width/2),
                (cx + mark_size_um/2, cy - cross_width/2),
                (cx + mark_size_um/2, cy + cross_width/2),
                (cx - mark_size_um/2, cy + cross_width/2),
            ],
            layer=ALIGNMENT_LAYER
        )

        # Vertical bar of cross
        component.add_polygon(
            [
                (cx - cross_width/2, cy - mark_size_um/2),
                (cx + cross_width/2, cy - mark_size_um/2),
                (cx + cross_width/2, cy + mark_size_um/2),
                (cx - cross_width/2, cy + mark_size_um/2),
            ],
            layer=ALIGNMENT_LAYER
        )

        # Corner identification number
        component.add_label(
            f"ALN_{i+1}",
            position=(cx, cy - mark_size_um/2 - 20),
            layer=ALIGNMENT_LAYER
        )

    return component


def extract_layer(
    source_component: Component,
    layer_spec: tuple,
    name: str = "extracted"
) -> Component:
    """
    Extracts a single layer from a component into a new component.

    Args:
        source_component: Source GDS component
        layer_spec: (layer, datatype) tuple to extract
        name: Name for the new component

    Returns:
        New component containing only the specified layer
    """
    c = gf.Component(name)

    # Get all polygons from the source component
    polygons = source_component.get_polygons(by_spec=True)

    if layer_spec in polygons:
        for poly in polygons[layer_spec]:
            c.add_polygon(poly, layer=layer_spec)

    return c


def extract_mask_layers(
    input_gds: str = None,
    output_dir: str = MASK_DIR,
    layer_mapping: dict = LAYER_MAPPING,
    add_marks: bool = True
) -> dict:
    """
    Extracts individual mask layers from a chip GDS file.

    Args:
        input_gds: Path to input GDS file (if None, generates test chip)
        output_dir: Directory for output mask GDS files
        layer_mapping: Dictionary mapping mask names to source layers
        add_marks: Whether to add alignment marks to each mask

    Returns:
        Dictionary with paths to generated mask files
    """
    print(f"\n{'='*60}")
    print("MASK LAYER EXTRACTION")
    print("="*60)

    # Load or generate source component
    if input_gds and os.path.exists(input_gds):
        print(f"Loading source GDS: {input_gds}")
        source = gf.import_gds(input_gds)
    else:
        print("No input GDS specified. Generating test chip...")
        source = generate_test_chip()

    # Get chip bounding box for alignment marks
    # Handle both gdsfactory API versions
    try:
        bbox = source.bbox()  # gdsfactory 9.x uses method
        chip_width = bbox.width
        chip_height = bbox.height
        chip_size = (chip_width, chip_height)
        print(f"Chip size: {chip_width:.0f} x {chip_height:.0f} um")
    except (TypeError, AttributeError):
        try:
            bbox = source.bbox  # older versions use property
            if bbox is not None:
                chip_width = bbox[1][0] - bbox[0][0]
                chip_height = bbox[1][1] - bbox[0][1]
                chip_size = (chip_width, chip_height)
                print(f"Chip size: {chip_width:.0f} x {chip_height:.0f} um")
            else:
                chip_size = (10000, 10000)
        except Exception:
            chip_size = (10000, 10000)
            print("Using default chip size: 10000 x 10000 um")

    # Extract each mask layer
    output_files = {}
    os.makedirs(output_dir, exist_ok=True)

    for mask_name, layer_info in layer_mapping.items():
        print(f"\nExtracting {mask_name}...")
        print(f"  Source layers: {layer_info['source_layers']}")
        print(f"  Process: {layer_info['process']}")

        # Create new component for this mask
        mask = gf.Component(f"MASK_{mask_name}")

        # Extract all source layers for this mask
        # Handle different gdsfactory API versions
        polygon_count = 0
        try:
            # gdsfactory 9.x API
            for layer_spec in layer_info['source_layers']:
                layer, datatype = layer_spec
                try:
                    polys = source.get_polygons(layer=(layer, datatype))
                    for poly in polys:
                        mask.add_polygon(poly, layer=layer_spec)
                        polygon_count += 1
                except Exception:
                    pass
        except Exception:
            # Fallback: try older API
            try:
                polygons = source.get_polygons(by_spec=True)
                for layer_spec in layer_info['source_layers']:
                    if layer_spec in polygons:
                        for poly in polygons[layer_spec]:
                            mask.add_polygon(poly, layer=layer_spec)
                            polygon_count += 1
            except Exception:
                pass

        print(f"  Extracted {polygon_count} polygons")

        # Add alignment marks
        if add_marks and polygon_count > 0:
            add_alignment_marks(mask, chip_size_um=chip_size)
            print(f"  Added alignment marks at corners")

        # Add mask identification label
        mask.add_label(
            f"MASK: {mask_name}",
            position=(chip_size[0]/2 - 1000, chip_size[1]/2 - 100),
            layer=(100, 0)
        )
        mask.add_label(
            f"PROCESS: {layer_info['process']}",
            position=(chip_size[0]/2 - 1000, chip_size[1]/2 - 200),
            layer=(100, 0)
        )

        # Write GDS file
        output_path = os.path.join(output_dir, f"{mask_name}.gds")
        mask.write_gds(output_path)
        output_files[mask_name] = output_path
        print(f"  Saved: {output_path}")

    return output_files


def generate_test_chip() -> Component:
    """
    Generates a test chip with all required layers for mask extraction testing.

    This creates a simplified chip layout that includes examples of all
    the layer types used in the full 81-trit processor.
    """
    c = gf.Component("TEST_CHIP_FOR_MASKS")

    # Waveguide layer (1, 0)
    # Simple straight waveguides
    for i in range(5):
        y = i * 50 - 100
        c.add_polygon(
            [(0, y - 0.25), (500, y - 0.25), (500, y + 0.25), (0, y + 0.25)],
            layer=(1, 0)
        )

    # MMI splitter shape
    c.add_polygon(
        [(100, -30), (120, -30), (120, 30), (100, 30)],
        layer=(1, 0)
    )

    # Heater layer (10, 0)
    for i in range(3):
        x = 150 + i * 100
        c.add_polygon(
            [(x, -20), (x + 50, -20), (x + 50, -15), (x, -15)],
            layer=(10, 0)
        )

    # Bond pads layer (12, 0)
    pad_positions = [(50, 150), (200, 150), (350, 150), (500, 150)]
    for px, py in pad_positions:
        c.add_polygon(
            [(px - 30, py - 30), (px + 30, py - 30),
             (px + 30, py + 30), (px - 30, py + 30)],
            layer=(12, 0)
        )

    # Chi2 poling regions (2, 0) and (4, 0)
    # SFG mixer region
    c.add_polygon(
        [(200, -10), (280, -10), (280, 10), (200, 10)],
        layer=(2, 0)
    )
    # DFG mixer region
    c.add_polygon(
        [(320, -10), (400, -10), (400, 10), (320, 10)],
        layer=(4, 0)
    )

    # Saturable absorber doping (13, 0)
    c.add_polygon(
        [(420, -5), (470, -5), (470, 5), (420, 5)],
        layer=(13, 0)
    )

    # Gain medium doping (14, 0)
    c.add_polygon(
        [(50, 50), (100, 50), (100, 60), (50, 60)],
        layer=(14, 0)
    )

    # Add some labels
    c.add_label("TEST_CHIP", position=(250, 180), layer=(100, 0))
    c.add_label("WAVEGUIDES", position=(50, -120), layer=(100, 0))
    c.add_label("HEATERS", position=(200, -40), layer=(100, 0))
    c.add_label("CHI2_SFG", position=(240, 20), layer=(100, 0))
    c.add_label("CHI2_DFG", position=(360, 20), layer=(100, 0))
    c.add_label("LOG_SA", position=(445, 15), layer=(100, 0))
    c.add_label("EXP_GAIN", position=(75, 70), layer=(100, 0))

    return c


def generate_process_traveler(
    output_file: str,
    layer_mapping: dict = LAYER_MAPPING,
    mask_files: dict = None
) -> str:
    """
    Generates a process traveler document for foundry fabrication.

    The process traveler specifies the order of fabrication steps,
    process parameters, and quality control checkpoints.

    Args:
        output_file: Path for output markdown file
        layer_mapping: Layer definitions
        mask_files: Dictionary of generated mask file paths

    Returns:
        Path to generated traveler document
    """
    print(f"\nGenerating process traveler: {output_file}")

    content = """# Fabrication Process Traveler
## Wavelength-Division Ternary Optical Computer

### Chip Information
- **Project:** 81-Trit Optical ALU
- **Substrate:** X-cut LiNbO3 (Lithium Niobate)
- **Chip Size:** ~10mm x 10mm
- **Feature Size:** 500nm (waveguide width)
- **Alignment Tolerance:** 0.5-2.0 um

---

## Process Flow

### Step 1: Waveguide Definition
| Parameter | Value |
|-----------|-------|
| **Mask** | WAVEGUIDE.gds |
| **Layer** | (1, 0) |
| **Process** | RIE etch |
| **Etch Depth** | 400 nm |
| **Resist** | ZEP520A (positive) |
| **Pattern** | E-beam lithography |
| **QC Check** | SEM cross-section, sidewall angle 85-90° |

### Step 2: PPLN Electrode Patterning
| Parameter | Value |
|-----------|-------|
| **Mask** | CHI2_POLING.gds |
| **Layers** | (2, 0), (4, 0) |
| **Process** | Liftoff + high-voltage poling |
| **Electrode** | 200nm Cr/Au |
| **Poling Voltage** | 21 kV/mm |
| **Period** | 6.5-7.0 um (SFG), 10-12 um (DFG) |
| **QC Check** | SHG efficiency test |

### Step 3: Heater Metal Deposition
| Parameter | Value |
|-----------|-------|
| **Mask** | METAL1_HEATER.gds |
| **Layer** | (10, 0) |
| **Process** | Liftoff |
| **Material** | 100nm TiN |
| **Resist** | PMMA (bilayer) |
| **QC Check** | Sheet resistance 50-100 Ω/□ |

### Step 4: Ion Implantation (Log Converter)
| Parameter | Value |
|-----------|-------|
| **Mask** | DOPING_SA.gds |
| **Layer** | (13, 0) |
| **Process** | Er/Yb ion implant |
| **Er Dose** | 1e15 cm⁻² |
| **Yb Dose** | 5e14 cm⁻² |
| **Energy** | 200 keV |
| **QC Check** | PL spectrum, absorption at 1.55um |

### Step 5: Ion Implantation (Gain Medium)
| Parameter | Value |
|-----------|-------|
| **Mask** | DOPING_GAIN.gds |
| **Layer** | (14, 0) |
| **Process** | Er/Yb ion implant |
| **Er Dose** | 2e15 cm⁻² |
| **Yb Dose** | 1e15 cm⁻² |
| **Energy** | 200 keV |
| **QC Check** | PL spectrum, gain at 1.55um with 980nm pump |

### Step 6: Bond Pad Metallization
| Parameter | Value |
|-----------|-------|
| **Mask** | METAL2_PAD.gds |
| **Layer** | (12, 0) |
| **Process** | Liftoff |
| **Material** | 20nm Ti / 500nm Au |
| **Pad Size** | 100 x 100 um |
| **QC Check** | Wire bond pull test >5g |

### Step 7: Anneal
| Parameter | Value |
|-----------|-------|
| **Process** | RTA anneal |
| **Temperature** | 600°C |
| **Duration** | 30 minutes |
| **Atmosphere** | O₂ |
| **Purpose** | Activate implanted dopants |

---

## Alignment Mark Specifications

- **Location:** All four chip corners
- **Mark Type:** Cross alignment marks
- **Size:** 100 um
- **Tolerance:** ±0.5 um between layers

---

## Quality Control Checkpoints

| Step | Measurement | Acceptance Criteria |
|------|-------------|---------------------|
| After Step 1 | Waveguide width | 500 ± 20 nm |
| After Step 1 | Etch depth | 400 ± 10 nm |
| After Step 2 | Poling period | Target ± 50 nm |
| After Step 3 | Heater resistance | 50-100 Ω/□ |
| After Step 4 | SA absorption | >3 dB at 1.55um |
| After Step 5 | Gain | >10 dB at 1.55um |
| Final | Insertion loss | <3 dB/cm |

---

## Mask Files

"""

    if mask_files:
        content += "| Mask Name | File Path | Process Step |\n"
        content += "|-----------|-----------|-------------|\n"
        for mask_name, path in mask_files.items():
            process = layer_mapping.get(mask_name, {}).get('process', 'N/A')
            content += f"| {mask_name} | `{os.path.basename(path)}` | {process} |\n"

    content += """
---

## Notes

1. **Alignment:** Use WAVEGUIDE layer as reference for all subsequent layers.
   Layer-to-layer alignment should be <1 um for optimal device performance.

2. **PPLN Poling:** Poling should be done at room temperature with careful
   voltage ramping to prevent cracking. Monitor current during poling.

3. **Doping:** Er/Yb co-doping provides efficient pump absorption (Yb)
   and emission at telecom wavelengths (Er). Anneal is critical for
   optical activation.

4. **Testing:** After fabrication, test devices should be characterized for:
   - Waveguide propagation loss
   - SFG/DFG conversion efficiency
   - Heater response time
   - Saturable absorber saturation intensity
   - Amplifier gain and recovery time

---

*Generated by mask_layer_generator.py*
*Wavelength-Division Ternary Optical Computer Project*
"""

    with open(output_file, 'w') as f:
        f.write(content)

    print(f"  Saved: {output_file}")
    return output_file


def main():
    """Run mask layer generation."""
    print("\n" + "="*70)
    print("FABRICATION MASK LAYER GENERATOR")
    print("Wavelength-Division Ternary Optical Computer")
    print("="*70)

    # Check if a full chip GDS exists
    full_chip_candidates = [
        os.path.join(GDS_DIR, 'ternary_81trit_optical_carry.gds'),
        os.path.join(GDS_DIR, 'ternary_81trit.gds'),
        os.path.join(GDS_DIR, 'alu_with_selectors.gds'),
    ]

    input_gds = None
    for candidate in full_chip_candidates:
        if os.path.exists(candidate):
            input_gds = candidate
            break

    if input_gds:
        print(f"\nFound existing chip GDS: {input_gds}")
    else:
        print("\nNo existing chip GDS found. Will generate test chip.")

    # Extract mask layers
    mask_files = extract_mask_layers(
        input_gds=input_gds,
        output_dir=MASK_DIR,
        layer_mapping=LAYER_MAPPING,
        add_marks=True
    )

    # Generate process traveler
    traveler_path = os.path.join(MASK_DIR, 'process_traveler.md')
    generate_process_traveler(traveler_path, LAYER_MAPPING, mask_files)

    # Summary
    print("\n" + "="*70)
    print("MASK GENERATION COMPLETE")
    print("="*70)
    print(f"\nGenerated mask files:")
    for mask_name, path in mask_files.items():
        print(f"  - {mask_name}: {path}")
    print(f"\nProcess traveler: {traveler_path}")

    print(f"\nTo view masks in KLayout:")
    print(f"  klayout {MASK_DIR}/*.gds")

    return mask_files


if __name__ == "__main__":
    main()
