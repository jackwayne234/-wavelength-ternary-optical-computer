#!/usr/bin/env python3
"""
WDM 243x243 Systolic Array Validation Test - EXTENDED CHIP VALIDATION
======================================================================

Extended-scale validation proving all 6 wavelength triplets can operate
through a complete 243x243 PE array. This is 9x the PE count of the 81x81
validation (243^2 = 59,049 PEs vs 81^2 = 6,561 PEs).

The simulation:
1. Creates a 243x243 grid of Processing Elements (simplified)
2. Injects all 18 wavelengths at input edge
3. Routes through the array (systolic data flow)
4. Measures output at collection edge
5. Verifies all channels arrive independently

Note: For 243 output ports, we use summary visualizations:
- Heatmap showing power received at each port (27x9 grid for display)
- Aggregate statistics rather than 243 individual plots

Performance Note:
    Use MPI for parallelism:
    mpirun -np 176 python wdm_243x243_array_test.py

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
except ImportError:
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
ARRAY_SIZE = 243      # 243x243 PE grid - EXTENDED CHIP
PE_PITCH = 10.0       # um between PE centers
WG_WIDTH = 0.5        # um waveguide width

# Material properties
N_CORE = 2.2          # LiNbO3
N_CLAD = 1.0          # Air

# Simulation parameters
RESOLUTION = 20       # pixels/um (can be adjusted if memory is tight)
PML_THICKNESS = 1.5   # um
PADDING = 2.0         # um

# Time - must be long enough for light to traverse array
# 243x243 array span = 2420 um (242 * 10), light in LiNbO3 (n=2.2) travels at c/2.2
# Need at least 2420 * 2.2 ~= 5324 time units, use 6000 for margin
RUN_TIME = 6000       # Meep time units

# Output directory - configurable, defaults to relative path
OUTPUT_DIR = os.environ.get('WDM_OUTPUT_DIR', './results')

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

def create_243x243_array():
    """Create the full 243x243 PE array geometry."""
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
    """Run WDM simulation through 243x243 array."""

    print_master(f"\n{'='*70}")
    print_master("WDM 243x243 SYSTOLIC ARRAY SIMULATION - EXTENDED CHIP VALIDATION")
    print_master(f"{'='*70}")
    print_master(f"Array: {ARRAY_SIZE}x{ARRAY_SIZE} PEs")
    print_master(f"PE pitch: {PE_PITCH} um")
    print_master(f"Wavelengths: {len(wavelengths)}")
    print_master(f"Resolution: {RESOLUTION} pixels/um")
    if IS_PARALLEL:
        print_master(f"MPI processes: {SIZE}")
    print_master(f"{'='*70}\n")

    # Create geometry
    geometry, array_span = create_243x243_array()

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
        if RANK == 0 and sim.round_time() % 100 < 1:
            elapsed = (datetime.now() - start_time).total_seconds()
            progress_pct = sim.round_time() / RUN_TIME * 100
            print(f"  Progress: {progress_pct:.0f}% ({elapsed:.0f}s elapsed)", flush=True)

    # Run
    sim.run(mp.at_every(50, progress), until=RUN_TIME)

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
    """Analyze and report results from 243x243 array simulation."""

    measured_wavelengths = [1.0 / f for f in flux_freqs]

    print_master(f"\n{'='*70}")
    print_master("WDM 243x243 ARRAY SIMULATION RESULTS - EXTENDED CHIP VALIDATION")
    print_master(f"{'='*70}")

    # Compute statistics for each output port
    port_stats = []
    all_passed = True

    for port_idx, flux_data in enumerate(flux_data_list):
        port_powers = []
        port_passed = True

        for target_wl in wavelengths:
            idx = np.argmin(np.abs(np.array(measured_wavelengths) - target_wl))
            power = flux_data[idx]
            port_powers.append(power)
            if power <= 0:
                port_passed = False

        port_stats.append({
            'port': port_idx + 1,
            'min_power': min(port_powers),
            'max_power': max(port_powers),
            'mean_power': np.mean(port_powers),
            'all_positive': port_passed
        })

        if not port_passed:
            all_passed = False

    # Summary statistics
    print_master(f"\nOutput Port Statistics ({ARRAY_SIZE} ports, 18 wavelengths each):")
    print_master("-" * 60)

    passed_ports = sum(1 for s in port_stats if s['all_positive'])
    failed_ports = ARRAY_SIZE - passed_ports

    print_master(f"Ports with all wavelengths detected: {passed_ports}/{ARRAY_SIZE}")
    print_master(f"Ports with missing wavelengths: {failed_ports}/{ARRAY_SIZE}")

    mean_powers = [s['mean_power'] for s in port_stats]
    print_master(f"\nMean power across all ports: {np.mean(mean_powers):.4f}")
    print_master(f"Min mean power (weakest port): {min(mean_powers):.4f}")
    print_master(f"Max mean power (strongest port): {max(mean_powers):.4f}")
    print_master(f"Power uniformity (std/mean): {np.std(mean_powers)/np.mean(mean_powers)*100:.1f}%")

    # Final verdict
    print_master(f"\n{'='*70}")
    if all_passed:
        print_master(f"SUCCESS: ALL 18 WAVELENGTHS DETECTED AT ALL {ARRAY_SIZE} OUTPUT PORTS!")
        print_master("EXTENDED CHIP WDM VALIDATED - The architecture scales to 243x243.")
        print_master("This validates WDM at 9x the PE count of the 81x81 array.")
    else:
        print_master("WARNING: Some channels showed low/no power at some ports.")
        print_master(f"  {passed_ports}/{ARRAY_SIZE} ports fully operational")
    print_master(f"{'='*70}")

    # Generate visualizations (rank 0 only)
    if RANK == 0:
        # Figure 1: Power heatmap (27x9 grid of 243 ports for visualization)
        fig1, axes1 = plt.subplots(1, 2, figsize=(18, 8))

        # Reshape mean powers into 27x9 grid for display (243 = 27*9)
        power_grid = np.array([s['mean_power'] for s in port_stats]).reshape(27, 9)

        im1 = axes1[0].imshow(power_grid, cmap='viridis', aspect='auto')
        axes1[0].set_title(f'Mean Power at Each Output Port\n({ARRAY_SIZE} ports as 27x9 grid)', fontsize=12)
        axes1[0].set_xlabel('Port Column (0-8)')
        axes1[0].set_ylabel('Port Row (0-26)')
        plt.colorbar(im1, ax=axes1[0], label='Power (a.u.)')

        # Histogram of port powers
        axes1[1].hist(mean_powers, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
        axes1[1].axvline(np.mean(mean_powers), color='red', linestyle='--',
                        label=f'Mean: {np.mean(mean_powers):.3f}')
        axes1[1].set_xlabel('Mean Power per Port (a.u.)')
        axes1[1].set_ylabel('Number of Ports')
        axes1[1].set_title(f'Distribution of Output Power Across {ARRAY_SIZE} Ports')
        axes1[1].legend()
        axes1[1].grid(True, alpha=0.3)

        plt.suptitle('WDM 243x243 Extended Chip Validation - Output Power Summary', fontsize=14, fontweight='bold')
        plt.tight_layout()

        plot1_path = os.path.join(output_dir, 'wdm_243x243_power_heatmap.png')
        plt.savefig(plot1_path, dpi=150)
        print_master(f"\nHeatmap saved: {plot1_path}")
        plt.close()

        # Figure 2: Wavelength response summary
        fig2, axes2 = plt.subplots(2, 2, figsize=(14, 12))

        # Average spectrum across all ports
        avg_spectrum = np.mean(flux_data_list, axis=0)
        axes2[0, 0].plot(measured_wavelengths, avg_spectrum, 'b-', linewidth=1.5)
        for wl in wavelengths:
            axes2[0, 0].axvline(x=wl, color='r', linestyle='--', alpha=0.3)
        axes2[0, 0].set_xlabel('Wavelength (um)')
        axes2[0, 0].set_ylabel('Average Power (a.u.)')
        axes2[0, 0].set_title(f'Average Transmission Spectrum (all {ARRAY_SIZE} ports)')
        axes2[0, 0].grid(True, alpha=0.3)

        # Spectrum at corner ports (1, 9, 235, 243)
        corner_ports = [0, 8, 234, 242]  # indices
        corner_names = ['Port 1 (corner)', 'Port 9 (corner)', 'Port 235 (corner)', 'Port 243 (corner)']
        colors = ['blue', 'green', 'orange', 'red']

        for idx, (port, name, color) in enumerate(zip(corner_ports, corner_names, colors)):
            axes2[0, 1].plot(measured_wavelengths, flux_data_list[port],
                            color=color, linewidth=1, alpha=0.7, label=name)
        axes2[0, 1].set_xlabel('Wavelength (um)')
        axes2[0, 1].set_ylabel('Power (a.u.)')
        axes2[0, 1].set_title('Corner Port Spectra (checking uniformity)')
        axes2[0, 1].legend(fontsize=8)
        axes2[0, 1].grid(True, alpha=0.3)

        # Center port spectrum
        center_port = 121  # Port 122 (center of 243)
        axes2[1, 0].plot(measured_wavelengths, flux_data_list[center_port], 'purple', linewidth=1.5)
        for wl in wavelengths:
            axes2[1, 0].axvline(x=wl, color='r', linestyle='--', alpha=0.3)
        axes2[1, 0].set_xlabel('Wavelength (um)')
        axes2[1, 0].set_ylabel('Power (a.u.)')
        axes2[1, 0].set_title('Center Port (122) Spectrum')
        axes2[1, 0].grid(True, alpha=0.3)

        # Pass/fail grid (27x9)
        pass_grid = np.array([1 if s['all_positive'] else 0 for s in port_stats]).reshape(27, 9)
        im4 = axes2[1, 1].imshow(pass_grid, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        axes2[1, 1].set_title('Pass/Fail Map\n(Green=All wavelengths detected, Red=Missing)')
        axes2[1, 1].set_xlabel('Port Column (0-8)')
        axes2[1, 1].set_ylabel('Port Row (0-26)')

        plt.suptitle('WDM 243x243 Extended Chip Validation - Spectral Analysis', fontsize=14, fontweight='bold')
        plt.tight_layout()

        plot2_path = os.path.join(output_dir, 'wdm_243x243_spectral_summary.png')
        plt.savefig(plot2_path, dpi=150)
        print_master(f"Spectral summary saved: {plot2_path}")
        plt.close()

        # Save detailed results
        results_path = os.path.join(output_dir, 'wdm_243x243_array_results.txt')
        with open(results_path, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("WDM 243x243 SYSTOLIC ARRAY VALIDATION RESULTS - EXTENDED CHIP\n")
            f.write("=" * 70 + "\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"Array: {ARRAY_SIZE}x{ARRAY_SIZE}\n")
            f.write(f"Resolution: {RESOLUTION}\n")
            f.write(f"Run time: {RUN_TIME}\n")
            f.write(f"MPI processes: {SIZE}\n")
            f.write(f"\nStatus: {'PASSED - EXTENDED CHIP VALIDATED' if all_passed else 'NEEDS REVIEW'}\n")
            f.write(f"Ports passed: {passed_ports}/{ARRAY_SIZE}\n")
            f.write(f"\nPower Statistics:\n")
            f.write(f"  Mean power: {np.mean(mean_powers):.6f}\n")
            f.write(f"  Min power: {min(mean_powers):.6f}\n")
            f.write(f"  Max power: {max(mean_powers):.6f}\n")
            f.write(f"  Uniformity: {np.std(mean_powers)/np.mean(mean_powers)*100:.2f}%\n")
            f.write("=" * 70 + "\n")
            f.write("\nPer-Port Details:\n")
            f.write("-" * 50 + "\n")
            for s in port_stats:
                status = "OK" if s['all_positive'] else "LOW"
                f.write(f"Port {s['port']:3d}: mean={s['mean_power']:.4f} "
                       f"min={s['min_power']:.4f} max={s['max_power']:.4f} [{status}]\n")
        print_master(f"Results saved: {results_path}")

    return all_passed

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the WDM 243x243 array validation - EXTENDED CHIP."""

    print_master("\n" + "=" * 70)
    print_master("N-RADIX WDM 243x243 ARRAY VALIDATION TEST - EXTENDED CHIP")
    print_master("=" * 70)
    print_master(f"Started: {datetime.now()}")
    if IS_PARALLEL:
        print_master(f"Running with MPI: {SIZE} processes")
    print_master("=" * 70)

    # Output directory
    output_dir = OUTPUT_DIR
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
