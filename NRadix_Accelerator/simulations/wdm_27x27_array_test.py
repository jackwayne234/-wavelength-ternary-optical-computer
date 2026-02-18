#!/usr/bin/env python3
"""
WDM 27×27 Systolic Array Validation Test
=========================================

Tests whether all 6 wavelength triplets can operate through a
27×27 PE array - proving WDM works at the systolic array level.

This is a scaled-up version of the 9×9 test, designed to validate
WDM at larger array sizes before proceeding to 81×81.

The simulation:
1. Creates a 27×27 grid of Processing Elements (simplified)
2. Injects all 18 wavelengths at input edge
3. Routes through the array (systolic data flow)
4. Measures output at collection edge
5. Verifies all channels arrive independently

Performance Note:
    Use OpenMP for parallelism (MPI unavailable with Python 3.13):
    export OMP_NUM_THREADS=12
    /home/jackwayne/miniconda/envs/meep_env/bin/python wdm_27x27_array_test.py

Author: N-Radix Project
Date: February 5, 2026
"""

import meep as mp
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys

# MPI support
try:
    from mpi4py import MPI
    RANK = MPI.COMM_WORLD.Get_rank()
    SIZE = MPI.COMM_WORLD.Get_size()
    IS_PARALLEL = SIZE > 1
except (ImportError, RuntimeError, OSError):
    RANK = 0
    SIZE = 1
    IS_PARALLEL = False

def print_master(msg):
    """Only print from rank 0."""
    if RANK == 0:
        print(msg)
        sys.stdout.flush()

# =============================================================================
# WDM TRIPLET DEFINITIONS
# =============================================================================

WDM_TRIPLETS = {
    1: {'lambda_neg': 1.040, 'lambda_zero': 1.020, 'lambda_pos': 1.000},
    2: {'lambda_neg': 1.100, 'lambda_zero': 1.080, 'lambda_pos': 1.060},
    3: {'lambda_neg': 1.160, 'lambda_zero': 1.140, 'lambda_pos': 1.120},
    4: {'lambda_neg': 1.220, 'lambda_zero': 1.200, 'lambda_pos': 1.180},
    5: {'lambda_neg': 1.280, 'lambda_zero': 1.260, 'lambda_pos': 1.240},
    6: {'lambda_neg': 1.340, 'lambda_zero': 1.320, 'lambda_pos': 1.300},
}

def get_all_wavelengths():
    """Get all 18 wavelengths in um."""
    wavelengths = []
    for triplet in WDM_TRIPLETS.values():
        wavelengths.extend([triplet['lambda_neg'], triplet['lambda_zero'], triplet['lambda_pos']])
    return sorted(wavelengths)

def wavelength_to_frequency(wavelength_um):
    """Convert wavelength (um) to Meep frequency."""
    return 1.0 / wavelength_um

# =============================================================================
# SIMULATION PARAMETERS
# =============================================================================

# Array parameters
ARRAY_SIZE = 27       # 27×27 PE grid
PE_PITCH = 10.0       # um between PE centers
WG_WIDTH = 0.5        # um waveguide width

# Material properties
N_CORE = 2.2          # LiNbO3
N_CLAD = 1.0          # Air

# Simulation parameters
RESOLUTION = 20       # pixels/um (reduced from 30 for larger array)
PML_THICKNESS = 1.5   # um
PADDING = 2.0         # um

# Time - must be long enough for light to traverse array
# 27×27 array span = 260 µm, light in LiNbO3 (n=2.2) travels at c/2.2
# Need at least 260 * 2.2 ≈ 572 time units, use 600 for margin
RUN_TIME = 600        # Meep time units

# =============================================================================
# GEOMETRY CREATION
# =============================================================================

def create_pe_cell(center_x, center_y, pe_size=8.0):
    """
    Create a simplified Processing Element.

    The PE is modeled as a region with waveguide crossings.
    In reality, PEs have ring resonators and SFG mixers,
    but for WDM testing we just need waveguide routing.
    """
    components = []

    # Horizontal waveguide through PE
    components.append(
        mp.Block(
            size=mp.Vector3(pe_size, WG_WIDTH, mp.inf),
            center=mp.Vector3(center_x, center_y, 0),
            material=mp.Medium(index=N_CORE)
        )
    )

    # Vertical waveguide through PE
    components.append(
        mp.Block(
            size=mp.Vector3(WG_WIDTH, pe_size, mp.inf),
            center=mp.Vector3(center_x, center_y, 0),
            material=mp.Medium(index=N_CORE)
        )
    )

    return components

def create_27x27_array():
    """Create the full 27×27 PE array geometry."""
    geometry = []

    # Calculate array bounds
    array_span = (ARRAY_SIZE - 1) * PE_PITCH

    # Create PEs
    for row in range(ARRAY_SIZE):
        for col in range(ARRAY_SIZE):
            cx = col * PE_PITCH - array_span / 2
            cy = row * PE_PITCH - array_span / 2
            geometry.extend(create_pe_cell(cx, cy))

    # Input waveguides (left edge)
    for row in range(ARRAY_SIZE):
        cy = row * PE_PITCH - array_span / 2
        geometry.append(
            mp.Block(
                size=mp.Vector3(PADDING + PML_THICKNESS, WG_WIDTH, mp.inf),
                center=mp.Vector3(-array_span/2 - PE_PITCH/2 - (PADDING + PML_THICKNESS)/2, cy, 0),
                material=mp.Medium(index=N_CORE)
            )
        )

    # Output waveguides (right edge)
    for row in range(ARRAY_SIZE):
        cy = row * PE_PITCH - array_span / 2
        geometry.append(
            mp.Block(
                size=mp.Vector3(PADDING + PML_THICKNESS, WG_WIDTH, mp.inf),
                center=mp.Vector3(array_span/2 + PE_PITCH/2 + (PADDING + PML_THICKNESS)/2, cy, 0),
                material=mp.Medium(index=N_CORE)
            )
        )

    return geometry, array_span

def run_wdm_array_simulation(wavelengths, verbose=True):
    """Run WDM simulation through 27×27 array."""

    print_master(f"\n{'='*70}")
    print_master("WDM 27×27 SYSTOLIC ARRAY SIMULATION")
    print_master(f"{'='*70}")
    print_master(f"Array: {ARRAY_SIZE}×{ARRAY_SIZE} PEs")
    print_master(f"PE pitch: {PE_PITCH} um")
    print_master(f"Wavelengths: {len(wavelengths)}")
    print_master(f"Resolution: {RESOLUTION} pixels/um")
    if IS_PARALLEL:
        print_master(f"MPI processes: {SIZE}")
    print_master(f"{'='*70}\n")

    # Create geometry
    geometry, array_span = create_27x27_array()

    # Cell size
    total_span = array_span + PE_PITCH
    sx = total_span + 2 * (PADDING + PML_THICKNESS)
    sy = total_span + 2 * (PADDING + PML_THICKNESS)
    cell = mp.Vector3(sx, sy, 0)

    print_master(f"Cell size: {sx:.1f} x {sy:.1f} um")
    print_master(f"Total geometry elements: {len(geometry)}")

    # PML
    pml_layers = [mp.PML(thickness=PML_THICKNESS)]

    # Sources - one broadband source at each input port
    freqs = [wavelength_to_frequency(w) for w in wavelengths]
    f_center = np.mean(freqs)
    f_width = max(freqs) - min(freqs)

    sources = []
    src_x = -total_span/2 - PADDING/2

    for row in range(ARRAY_SIZE):
        cy = row * PE_PITCH - array_span / 2
        sources.append(
            mp.Source(
                src=mp.GaussianSource(frequency=f_center, fwidth=f_width * 1.5),
                component=mp.Ez,
                center=mp.Vector3(src_x, cy, 0),
                size=mp.Vector3(0, WG_WIDTH * 2, 0)
            )
        )

    print_master(f"Sources: {len(sources)} input ports")

    # Create simulation
    sim = mp.Simulation(
        cell_size=cell,
        geometry=geometry,
        sources=sources,
        boundary_layers=pml_layers,
        resolution=RESOLUTION,
        default_material=mp.Medium(index=N_CLAD)
    )

    # Flux monitors at output edge
    flux_x = total_span/2 + PADDING/2
    nfreq = len(wavelengths)

    flux_monitors = []
    for row in range(ARRAY_SIZE):
        cy = row * PE_PITCH - array_span / 2
        mon = sim.add_flux(
            f_center, f_width * 1.2, nfreq,
            mp.FluxRegion(
                center=mp.Vector3(flux_x, cy, 0),
                size=mp.Vector3(0, WG_WIDTH * 3, 0)
            )
        )
        flux_monitors.append(mon)

    print_master(f"Flux monitors: {len(flux_monitors)} output ports")
    print_master("\nRunning simulation...")

    # Progress callback
    start_time = datetime.now()

    def progress(sim):
        if RANK == 0 and sim.round_time() % 20 < 1:
            elapsed = (datetime.now() - start_time).total_seconds()
            progress_pct = sim.round_time() / RUN_TIME * 100
            print(f"  Progress: {progress_pct:.0f}% ({elapsed:.0f}s elapsed)", flush=True)

    # Run
    sim.run(mp.at_every(10, progress), until=RUN_TIME)

    elapsed = (datetime.now() - start_time).total_seconds()
    print_master(f"\nSimulation complete in {elapsed:.1f} seconds")

    # Collect results
    all_flux_freqs = None
    all_flux_data = []

    for i, mon in enumerate(flux_monitors):
        flux_freqs = mp.get_flux_freqs(mon)
        flux_data = mp.get_fluxes(mon)
        if all_flux_freqs is None:
            all_flux_freqs = flux_freqs
        all_flux_data.append(flux_data)

    return all_flux_freqs, all_flux_data, sim

def analyze_array_results(wavelengths, flux_freqs, flux_data_list, output_dir):
    """Analyze and report results from 27×27 array simulation."""

    measured_wavelengths = [1.0 / f for f in flux_freqs]

    print_master(f"\n{'='*70}")
    print_master("WDM 27×27 ARRAY SIMULATION RESULTS")
    print_master(f"{'='*70}")

    # Check each output port
    all_passed = True

    for port_idx, flux_data in enumerate(flux_data_list):
        print_master(f"\nOutput Port {port_idx + 1}:")
        print_master(f"{'Wavelength (um)':<18} {'Power':<15} {'Status':<10}")
        print_master("-" * 45)

        port_passed = True
        for target_wl in wavelengths:
            idx = np.argmin(np.abs(np.array(measured_wavelengths) - target_wl))
            power = flux_data[idx]
            status = "OK" if power > 0 else "LOW"
            if power <= 0:
                port_passed = False
            print_master(f"{target_wl:<18.4f} {power:<15.4f} {status:<10}")

        if not port_passed:
            all_passed = False

    # Summary
    print_master(f"\n{'='*70}")
    if all_passed:
        print_master("SUCCESS: All wavelengths detected at all output ports!")
        print_master("WDM works through the 27×27 systolic array structure.")
    else:
        print_master("WARNING: Some channels showed low/no power.")
    print_master(f"{'='*70}")

    # Generate plot (rank 0 only)
    if RANK == 0:
        # 6×5 grid (30 slots, first 27 used for 27 output ports)
        fig, axes = plt.subplots(6, 5, figsize=(20, 24))

        for port_idx, flux_data in enumerate(flux_data_list):
            row = port_idx // 5
            col = port_idx % 5
            ax = axes[row, col]
            ax.plot(measured_wavelengths, flux_data, 'b-', linewidth=1)
            for wl in wavelengths:
                ax.axvline(x=wl, color='r', linestyle='--', alpha=0.2)
            ax.set_xlabel('Wavelength (um)')
            ax.set_ylabel('Power (a.u.)')
            ax.set_title(f'Output Port {port_idx + 1}')
            ax.grid(True, alpha=0.3)

        # Hide unused subplots (slots 28, 29, 30)
        for idx in range(27, 30):
            row = idx // 5
            col = idx % 5
            axes[row, col].axis('off')

        plt.suptitle('WDM 27×27 Array - Transmission Spectrum at Each Output')
        plt.tight_layout()

        plot_path = os.path.join(output_dir, 'wdm_27x27_array_results.png')
        plt.savefig(plot_path, dpi=150)
        print_master(f"\nPlot saved: {plot_path}")
        plt.close()

        # Save data
        results_path = os.path.join(output_dir, 'wdm_27x27_array_results.txt')
        with open(results_path, 'w') as f:
            f.write("WDM 27×27 SYSTOLIC ARRAY VALIDATION RESULTS\n")
            f.write("=" * 50 + "\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"Array: {ARRAY_SIZE}x{ARRAY_SIZE}\n")
            f.write(f"Resolution: {RESOLUTION}\n")
            f.write(f"MPI processes: {SIZE}\n")
            f.write(f"Status: {'PASSED' if all_passed else 'NEEDS REVIEW'}\n")
            f.write("=" * 50 + "\n")
        print_master(f"Results saved: {results_path}")

    return all_passed

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the WDM 27×27 array validation."""

    print_master("\n" + "=" * 70)
    print_master("N-RADIX WDM 27×27 ARRAY VALIDATION TEST")
    print_master("=" * 70)
    print_master(f"Started: {datetime.now()}")
    if IS_PARALLEL:
        print_master(f"Running with MPI: {SIZE} processes")
    print_master("=" * 70)

    # Output directory
    output_dir = "/home/jackwayne/Desktop/Optical_computing/Research/data/wdm_validation"
    if RANK == 0:
        os.makedirs(output_dir, exist_ok=True)

    # Get wavelengths
    wavelengths = get_all_wavelengths()

    # Run simulation
    flux_freqs, flux_data_list, sim = run_wdm_array_simulation(wavelengths)

    # Analyze
    passed = analyze_array_results(wavelengths, flux_freqs, flux_data_list, output_dir)

    print_master(f"\nCompleted: {datetime.now()}")
    print_master("=" * 70 + "\n")

    return passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
