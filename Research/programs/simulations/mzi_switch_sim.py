#!/usr/bin/env python3
"""
Mach-Zehnder Interferometer (MZI) Switch Simulation

FDTD simulation of MZI optical switch for ternary computer wavelength gating.
Tests switching behavior at RED (1.55um), GREEN (1.216um), and BLUE (1.0um).

IMPROVED VERSION (v2):
- MMI-based splitter/combiner for balanced 50/50 splitting
- Calculated arm length for proper phase accumulation: L = 0.5*lambda/delta_n
- Tapered transitions for reduced mode mismatch loss
- Higher resolution (40 pixels/um) for accuracy
- Target extinction ratio: >15-20 dB

Usage:
    python mzi_switch_sim.py                    # Run ON/OFF comparison at 1.55um
    python mzi_switch_sim.py --wavelength 1.55  # Single wavelength
    python mzi_switch_sim.py --phase-sweep      # Sweep phase for switching curve
    python mzi_switch_sim.py --all-wavelengths  # Test all ternary wavelengths
"""

import os
import sys
import argparse
import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# Ternary wavelengths (um)
WAVELENGTHS = {
    'RED': 1.55,
    'GREEN': 1.216,
    'BLUE': 1.0
}


def run_mzi_simulation(wavelength: float, phase_shift: float = 0.0,
                       resolution: int = 40, label: str = ""):
    """
    Simulate MZI switch at given wavelength and phase shift.

    IMPROVED DESIGN:
    - MMI-based splitter/combiner for balanced 50/50 splitting
    - Calculated arm length for proper phase accumulation
    - Tapered transitions for reduced mode mismatch

    Args:
        wavelength: Operating wavelength (um)
        phase_shift: Phase shift in one arm (radians), simulated via index change
        resolution: FDTD resolution (pixels/um) - 40 for good accuracy
        label: Label for output files

    Returns:
        dict with bar_flux, input_flux, bar_transmission, extinction info
    """
    print(f"\n--- MZI SWITCH SIMULATION (IMPROVED) ---")
    print(f"Wavelength: {wavelength} um, Phase shift: {phase_shift:.3f} rad ({phase_shift/np.pi:.3f} pi)")

    # Physical parameters
    freq = 1.0 / wavelength

    # Material - Silicon nitride for broadband operation
    n_core = 2.0            # SiN refractive index
    n_clad = 1.44           # SiO2 cladding

    # Geometry (all in um)
    wg_width = 0.5          # Waveguide width
    arm_separation = 2.0    # Distance between arm centers

    # Calculate arm length for proper phase accumulation
    # For pi phase shift: delta_phi = 2*pi * delta_n * L / lambda
    # We want: delta_n * L / lambda = 0.5 for pi shift
    # Using a realistic delta_n = 0.01 (thermo-optic or electro-optic)
    delta_n_design = 0.01   # Design index change for pi shift
    arm_length = 0.5 * wavelength / delta_n_design  # ~77.5 um for 1.55um

    # For the simulation, we scale delta_n based on desired phase
    # delta_phi = 2*pi * delta_n * L / lambda
    # delta_n = delta_phi * lambda / (2*pi * L)
    delta_n = phase_shift * wavelength / (2 * np.pi * arm_length)
    n_shifted = n_core + delta_n

    # MMI splitter/combiner parameters
    # MMI width to cover both output arms
    mmi_width = arm_separation + wg_width * 2
    # MMI length for 50/50 splitting (approximate beat length)
    mmi_length = 0.5 * n_core * mmi_width**2 / wavelength

    # Taper length for adiabatic transition
    taper_length = 3.0

    # Input/output waveguide lengths
    io_wg_length = 4.0

    # Cell dimensions
    cell_x = io_wg_length + taper_length + mmi_length + arm_length + mmi_length + taper_length + io_wg_length + 4
    cell_y = mmi_width + 8
    pml_thickness = 1.5

    print(f"Design parameters:")
    print(f"  Arm length: {arm_length:.2f} um (for pi shift with dn={delta_n_design})")
    print(f"  Arm separation: {arm_separation:.2f} um")
    print(f"  MMI region: {mmi_length:.2f} um x {mmi_width:.2f} um")
    print(f"  Index shift for {phase_shift:.3f} rad: dn = {delta_n:.6f}")
    print(f"  Verification: delta_phi = 2*pi * {delta_n:.6f} * {arm_length:.2f} / {wavelength} = {2*np.pi*delta_n*arm_length/wavelength:.4f} rad")
    print(f"  Cell size: {cell_x:.1f} x {cell_y:.1f} um")
    print(f"  Resolution: {resolution} pixels/um")

    # Materials
    core_material = mp.Medium(index=n_core)
    shifted_material = mp.Medium(index=n_shifted)
    clad_material = mp.Medium(index=n_clad)

    cell_size = mp.Vector3(cell_x, cell_y, 0)

    # Calculate key x positions
    x_left_edge = -cell_x / 2 + pml_thickness
    x_input_end = x_left_edge + io_wg_length
    x_taper1_end = x_input_end + taper_length
    x_mmi1_end = x_taper1_end + mmi_length
    x_arms_end = x_mmi1_end + arm_length
    x_mmi2_end = x_arms_end + mmi_length
    x_taper2_end = x_mmi2_end + taper_length
    x_right_edge = cell_x / 2 - pml_thickness

    geometry = []

    # === Input waveguide ===
    geometry.append(
        mp.Block(
            mp.Vector3(io_wg_length, wg_width, mp.inf),
            center=mp.Vector3(x_left_edge + io_wg_length / 2, 0),
            material=core_material
        )
    )

    # === Input taper (wg_width -> mmi_width) ===
    # Use a series of blocks to approximate taper
    n_taper_segments = 10
    for i in range(n_taper_segments):
        frac = (i + 0.5) / n_taper_segments
        seg_width = wg_width + frac * (mmi_width - wg_width)
        seg_x = x_input_end + (i + 0.5) * taper_length / n_taper_segments
        geometry.append(
            mp.Block(
                mp.Vector3(taper_length / n_taper_segments + 0.1, seg_width, mp.inf),
                center=mp.Vector3(seg_x, 0),
                material=core_material
            )
        )

    # === MMI splitter region ===
    geometry.append(
        mp.Block(
            mp.Vector3(mmi_length, mmi_width, mp.inf),
            center=mp.Vector3(x_taper1_end + mmi_length / 2, 0),
            material=core_material
        )
    )

    # === MZI Arms ===
    # Upper arm (reference)
    geometry.append(
        mp.Block(
            mp.Vector3(arm_length, wg_width, mp.inf),
            center=mp.Vector3(x_mmi1_end + arm_length / 2, arm_separation / 2),
            material=core_material
        )
    )

    # Lower arm (with phase shift)
    geometry.append(
        mp.Block(
            mp.Vector3(arm_length, wg_width, mp.inf),
            center=mp.Vector3(x_mmi1_end + arm_length / 2, -arm_separation / 2),
            material=shifted_material
        )
    )

    # === MMI combiner region ===
    geometry.append(
        mp.Block(
            mp.Vector3(mmi_length, mmi_width, mp.inf),
            center=mp.Vector3(x_arms_end + mmi_length / 2, 0),
            material=core_material
        )
    )

    # === Output taper (mmi_width -> wg_width) ===
    for i in range(n_taper_segments):
        frac = (i + 0.5) / n_taper_segments
        seg_width = mmi_width - frac * (mmi_width - wg_width)
        seg_x = x_mmi2_end + (i + 0.5) * taper_length / n_taper_segments
        geometry.append(
            mp.Block(
                mp.Vector3(taper_length / n_taper_segments + 0.1, seg_width, mp.inf),
                center=mp.Vector3(seg_x, 0),
                material=core_material
            )
        )

    # === Output waveguide (bar port at y=0) ===
    geometry.append(
        mp.Block(
            mp.Vector3(io_wg_length, wg_width, mp.inf),
            center=mp.Vector3(x_taper2_end + io_wg_length / 2, 0),
            material=core_material
        )
    )

    # Source - Gaussian source with narrow bandwidth for cleaner excitation
    sources = [
        mp.Source(
            mp.GaussianSource(freq, fwidth=0.02 * freq),  # Very narrow bandwidth
            component=mp.Ez,
            center=mp.Vector3(x_left_edge + 0.5, 0),
            size=mp.Vector3(0, wg_width * 2, 0)
        )
    ]

    # Simulation with subpixel averaging for accuracy
    sim = mp.Simulation(
        cell_size=cell_size,
        boundary_layers=[mp.PML(pml_thickness)],
        geometry=geometry,
        sources=sources,
        resolution=resolution,
        default_material=clad_material,
        eps_averaging=True
    )

    # Flux monitors
    nfreq = 21  # Fewer frequency points for faster computation
    df = 0.05 * freq  # Narrow frequency range

    # Bar port monitor (at y=0)
    bar_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(x_right_edge - 0.5, 0),
            size=mp.Vector3(0, wg_width * 2, 0)
        )
    )

    # Input monitor (for normalization)
    input_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(x_left_edge + 2, 0),
            size=mp.Vector3(0, wg_width * 2, 0)
        )
    )

    # Run simulation with field decay monitoring
    print("Running FDTD simulation...")
    sim.run(until_after_sources=mp.stop_when_fields_decayed(
        100, mp.Ez, mp.Vector3(x_right_edge - 1, 0), 1e-5
    ))

    # Get results
    freqs = mp.get_flux_freqs(bar_mon)
    bar_flux = np.array(mp.get_fluxes(bar_mon))
    input_flux = np.array(mp.get_fluxes(input_mon))

    # Normalize - handle any negative flux
    bar_flux_abs = np.abs(bar_flux)
    input_flux_abs = np.abs(input_flux)

    bar_transmission = bar_flux_abs / (input_flux_abs + 1e-20)

    # Find values at center frequency
    center_idx = len(freqs) // 2
    bar_T = bar_transmission[center_idx]

    print(f"\nResults at lambda = {wavelength} um:")
    print(f"  Bar port transmission: {bar_T:.4f} ({10*np.log10(bar_T + 1e-20):.2f} dB)")
    print(f"  Input flux: {input_flux[center_idx]:.6f}")
    print(f"  Bar flux: {bar_flux[center_idx]:.6f}")

    return {
        'wavelength': wavelength,
        'phase_shift': phase_shift,
        'frequencies': freqs,
        'wavelengths': [1/f for f in freqs],
        'bar_flux': bar_flux,
        'input_flux': input_flux,
        'bar_transmission': bar_transmission,
        'bar_T_center': bar_T,
        'arm_length': arm_length,
        'arm_separation': arm_separation,
        'delta_n': delta_n,
        'mmi_length': mmi_length
    }


def run_phase_sweep(wavelength: float, n_points: int = 21, resolution: int = 30):
    """
    Sweep phase shift to generate MZI switching curve.
    Measures bar port transmission as function of phase.

    For ideal MZI:
    - Phase = 0: constructive interference -> T_bar ~ 1
    - Phase = pi: destructive interference -> T_bar ~ 0
    """
    print(f"\n=== PHASE SWEEP at lambda = {wavelength} um ===")

    phases = np.linspace(0, 2 * np.pi, n_points)
    bar_values = []

    for i, phase in enumerate(phases):
        print(f"\n[{i+1}/{n_points}] Phase = {phase:.3f} rad ({phase/np.pi:.2f} pi)")
        result = run_mzi_simulation(wavelength, phase, resolution=resolution)
        bar_values.append(result['bar_T_center'])

    bar_values = np.array(bar_values)

    # Calculate extinction ratio from max/min
    T_max = np.max(bar_values)
    T_min = np.min(bar_values)
    if T_min > 1e-10:
        extinction_db = 10 * np.log10(T_max / T_min)
    else:
        extinction_db = 10 * np.log10(T_max / 1e-10)

    print(f"\n=== PHASE SWEEP RESULTS ===")
    print(f"  Max transmission: {T_max:.4f}")
    print(f"  Min transmission: {T_min:.6f}")
    print(f"  EXTINCTION RATIO: {extinction_db:.2f} dB")

    return {
        'wavelength': wavelength,
        'phases': phases,
        'bar_transmission': bar_values,
        'T_max': T_max,
        'T_min': T_min,
        'extinction_ratio_db': extinction_db
    }


def run_on_off_comparison(wavelength: float, resolution: int = 40):
    """
    Run MZI at phase=0 and phase=pi to directly measure extinction ratio.
    This is the primary metric for switch quality.
    """
    print(f"\n{'='*60}")
    print(f"  MZI ON/OFF COMPARISON at lambda = {wavelength} um")
    print(f"{'='*60}")

    # ON state: phase = 0 (constructive interference)
    print("\n>>> ON STATE (phase = 0)")
    result_on = run_mzi_simulation(wavelength, 0.0, resolution)
    T_on = result_on['bar_T_center']

    # OFF state: phase = pi (destructive interference)
    print("\n>>> OFF STATE (phase = pi)")
    result_off = run_mzi_simulation(wavelength, np.pi, resolution)
    T_off = result_off['bar_T_center']

    # Calculate extinction ratio
    if T_off > 1e-10:
        extinction_db = 10 * np.log10(T_on / T_off)
    else:
        extinction_db = 10 * np.log10(T_on / 1e-10)

    print(f"\n{'='*60}")
    print(f"  MZI SWITCH PERFORMANCE")
    print(f"{'='*60}")
    print(f"  Wavelength: {wavelength} um")
    print(f"  ON state (phase=0):  T = {T_on:.4f} ({10*np.log10(T_on+1e-20):.2f} dB)")
    print(f"  OFF state (phase=pi): T = {T_off:.6f} ({10*np.log10(T_off+1e-20):.2f} dB)")
    print(f"  EXTINCTION RATIO: {extinction_db:.2f} dB")
    print(f"  Target: >15-20 dB for good switch")
    print(f"{'='*60}")

    return {
        'wavelength': wavelength,
        'T_on': T_on,
        'T_off': T_off,
        'extinction_ratio_db': extinction_db,
        'arm_length': result_on['arm_length'],
        'arm_separation': result_on['arm_separation']
    }


def save_results(result: dict, output_dir: str):
    """Save simulation results to CSV and PNG."""
    os.makedirs(output_dir, exist_ok=True)

    if 'phases' in result:
        # Phase sweep results
        wvl_nm = int(result['wavelength'] * 1000)

        # Save CSV
        csv_path = os.path.join(output_dir, f"mzi_phase_sweep_{wvl_nm}nm.csv")
        header = "Phase (rad),Phase (pi),Bar Transmission"
        data = np.column_stack((
            result['phases'],
            result['phases'] / np.pi,
            result['bar_transmission']
        ))
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(result['phases'] / np.pi, result['bar_transmission'],
                'b-o', linewidth=2, markersize=6, label='Bar port')

        ax.set_xlabel('Phase shift (pi radians)', fontsize=12)
        ax.set_ylabel('Transmission', fontsize=12)
        ax.set_title(f'MZI Switching Curve at lambda = {result["wavelength"]} um\n'
                     f'Extinction Ratio: {result["extinction_ratio_db"]:.1f} dB',
                     fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 2)
        ax.set_ylim(0, max(1.1, np.max(result['bar_transmission']) * 1.1))

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"mzi_switching_curve_{wvl_nm}nm.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()

    elif 'T_on' in result:
        # ON/OFF comparison results
        wvl_nm = int(result['wavelength'] * 1000)

        # Save summary CSV
        csv_path = os.path.join(output_dir, f"mzi_extinction_{wvl_nm}nm.csv")
        with open(csv_path, 'w') as f:
            f.write("Metric,Value\n")
            f.write(f"Wavelength (um),{result['wavelength']}\n")
            f.write(f"T_on,{result['T_on']}\n")
            f.write(f"T_off,{result['T_off']}\n")
            f.write(f"Extinction Ratio (dB),{result['extinction_ratio_db']}\n")
            f.write(f"Arm Length (um),{result['arm_length']}\n")
            f.write(f"Arm Separation (um),{result['arm_separation']}\n")
        print(f"Saved: {csv_path}")

    else:
        # Single simulation results
        wvl_nm = int(result['wavelength'] * 1000)
        phase_deg = int(np.degrees(result['phase_shift']))

        # Save spectrum CSV
        csv_path = os.path.join(output_dir, f"mzi_spectrum_{wvl_nm}nm_phase{phase_deg}.csv")
        header = "Frequency (Meep),Wavelength (um),Bar Flux,Input Flux,Bar T"
        data = np.column_stack((
            result['frequencies'],
            result['wavelengths'],
            result['bar_flux'],
            result['input_flux'],
            result['bar_transmission']
        ))
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot spectrum
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(result['wavelengths'], result['bar_transmission'], 'b-',
                 linewidth=2, label='Bar port')
        ax.axvline(x=result['wavelength'], color='green', linestyle=':',
                    linewidth=1.5, label=f'lambda = {result["wavelength"]} um')
        ax.set_xlabel('Wavelength (um)', fontsize=11)
        ax.set_ylabel('Transmission', fontsize=11)
        ax.set_title(f'MZI Transmission Spectrum (Phase = {result["phase_shift"]:.2f} rad)',
                      fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"mzi_spectrum_{wvl_nm}nm_phase{phase_deg}.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()


def main():
    parser = argparse.ArgumentParser(description='MZI Switch Meep FDTD Simulation (Improved)')
    parser.add_argument('--wavelength', type=float, help='Single wavelength (um)')
    parser.add_argument('--phase', type=float, default=0.0, help='Phase shift (radians)')
    parser.add_argument('--phase-sweep', action='store_true', help='Run phase sweep')
    parser.add_argument('--all-wavelengths', action='store_true', help='Test all ternary wavelengths')
    parser.add_argument('--resolution', type=int, default=40, help='FDTD resolution (default: 40)')
    parser.add_argument('--output', type=str, default=None, help='Output directory')

    args = parser.parse_args()

    # Determine output directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = args.output or os.path.join(base_dir, 'data', 'csv')

    print("=" * 60)
    print("  MZI SWITCH - Meep FDTD Simulation (IMPROVED)")
    print("  For Ternary Optical Computer Wavelength Gating")
    print("=" * 60)
    print("\nImprovements:")
    print("  - MMI-based splitter/combiner for balanced 50/50 splitting")
    print("  - Calculated arm length for proper phase accumulation")
    print("  - Tapered transitions for reduced loss")
    print("  - Higher resolution for accuracy")

    if args.phase_sweep:
        # Run phase sweep
        wvl = args.wavelength or 1.55
        result = run_phase_sweep(wvl, n_points=11, resolution=args.resolution)
        save_results(result, output_dir)

    elif args.all_wavelengths:
        # Test all ternary wavelengths
        for color, wvl in WAVELENGTHS.items():
            print(f"\n{'='*60}")
            print(f"  Testing {color} wavelength: {wvl} um")
            print('='*60)

            result = run_on_off_comparison(wvl, args.resolution)
            save_results(result, output_dir)

    elif args.wavelength:
        # Single wavelength with specified phase
        result = run_mzi_simulation(args.wavelength, args.phase, args.resolution)
        save_results(result, output_dir)

    else:
        # Default: run ON/OFF comparison for RED wavelength
        print("\nDefault run: RED wavelength (1.55 um) ON/OFF comparison")
        result = run_on_off_comparison(1.55, args.resolution)
        save_results(result, output_dir)

    print("\n" + "=" * 60)
    print("  SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
