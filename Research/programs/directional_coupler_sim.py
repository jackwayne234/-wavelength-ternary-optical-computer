#!/usr/bin/env python3
"""
Directional Coupler Simulation

FDTD simulation of directional couplers for 50/50 beam splitting.
Tests wavelength-dependent coupling for RED, GREEN, BLUE channels.

Usage:
    python directional_coupler_sim.py                    # Default test
    python directional_coupler_sim.py --wavelength 1.55  # Single wavelength
    python directional_coupler_sim.py --sweep-gap        # Gap sweep for optimization
    python directional_coupler_sim.py --sweep-params     # 2D parameter sweep
    python directional_coupler_sim.py --all-wavelengths  # Test all ternary wavelengths

Theory:
    For 50% coupling, the coupling length L should satisfy: L = pi / (2 * kappa)
    where kappa is the coupling coefficient. Larger gap -> weaker coupling ->
    need longer length for same power transfer.
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


def run_coupler_simulation(wavelength: float, gap: float = 0.25,
                           coupling_length: float = 6.0,
                           resolution: int = 25):
    """
    Simulate directional coupler at given wavelength.

    Args:
        wavelength: Operating wavelength (um)
        gap: Gap between waveguides (um) - default tuned for 50/50 split
        coupling_length: Length of coupling region (um) - default tuned for 50/50 split
        resolution: FDTD resolution (pixels/um)

    Returns:
        dict with through/cross port power and coupling ratio
    """
    print(f"\n--- DIRECTIONAL COUPLER SIMULATION ---")
    print(f"Wavelength: {wavelength} um, Gap: {gap} um, Length: {coupling_length} um")

    freq = 1.0 / wavelength

    # Geometry parameters (um)
    wg_width = 0.5
    wg_separation = wg_width + gap  # Center-to-center
    bend_length = 5.0  # S-bend length to separate waveguides
    straight_length = 5.0  # Input/output straight sections

    # Cell dimensions
    cell_x = 2 * straight_length + 2 * bend_length + coupling_length + 6
    cell_y = 2 * wg_separation + 4 * wg_width + 4
    pml_thickness = 1.0

    # Material
    n_core = 2.0
    core_material = mp.Medium(index=n_core)

    cell_size = mp.Vector3(cell_x, cell_y, 0)

    # Build geometry
    geometry = []

    # Input waveguides (separated)
    input_sep = wg_separation + 2  # Wider separation at input
    x_start = -cell_x/2 + pml_thickness + 1

    # Upper input waveguide
    geometry.append(
        mp.Block(
            mp.Vector3(straight_length, wg_width, mp.inf),
            center=mp.Vector3(x_start + straight_length/2, input_sep/2),
            material=core_material
        )
    )

    # Lower input waveguide
    geometry.append(
        mp.Block(
            mp.Vector3(straight_length, wg_width, mp.inf),
            center=mp.Vector3(x_start + straight_length/2, -input_sep/2),
            material=core_material
        )
    )

    # S-bends to bring waveguides together
    bend_start = x_start + straight_length
    n_bend_segments = 10

    for i in range(n_bend_segments):
        t = (i + 0.5) / n_bend_segments
        x_pos = bend_start + t * bend_length

        # Sinusoidal S-bend profile
        y_upper = input_sep/2 - (input_sep/2 - wg_separation/2) * (1 - np.cos(np.pi * t)) / 2
        y_lower = -input_sep/2 + (input_sep/2 - wg_separation/2) * (1 - np.cos(np.pi * t)) / 2

        geometry.append(
            mp.Block(
                mp.Vector3(bend_length/n_bend_segments + 0.1, wg_width, mp.inf),
                center=mp.Vector3(x_pos, y_upper),
                material=core_material
            )
        )
        geometry.append(
            mp.Block(
                mp.Vector3(bend_length/n_bend_segments + 0.1, wg_width, mp.inf),
                center=mp.Vector3(x_pos, y_lower),
                material=core_material
            )
        )

    # Coupling region (parallel waveguides)
    coupling_start = bend_start + bend_length
    geometry.append(
        mp.Block(
            mp.Vector3(coupling_length, wg_width, mp.inf),
            center=mp.Vector3(coupling_start + coupling_length/2, wg_separation/2),
            material=core_material
        )
    )
    geometry.append(
        mp.Block(
            mp.Vector3(coupling_length, wg_width, mp.inf),
            center=mp.Vector3(coupling_start + coupling_length/2, -wg_separation/2),
            material=core_material
        )
    )

    # Output S-bends to separate waveguides
    bend2_start = coupling_start + coupling_length

    for i in range(n_bend_segments):
        t = (i + 0.5) / n_bend_segments
        x_pos = bend2_start + t * bend_length

        y_upper = wg_separation/2 + (input_sep/2 - wg_separation/2) * (1 - np.cos(np.pi * t)) / 2
        y_lower = -wg_separation/2 - (input_sep/2 - wg_separation/2) * (1 - np.cos(np.pi * t)) / 2

        geometry.append(
            mp.Block(
                mp.Vector3(bend_length/n_bend_segments + 0.1, wg_width, mp.inf),
                center=mp.Vector3(x_pos, y_upper),
                material=core_material
            )
        )
        geometry.append(
            mp.Block(
                mp.Vector3(bend_length/n_bend_segments + 0.1, wg_width, mp.inf),
                center=mp.Vector3(x_pos, y_lower),
                material=core_material
            )
        )

    # Output straight sections
    output_start = bend2_start + bend_length
    geometry.append(
        mp.Block(
            mp.Vector3(straight_length, wg_width, mp.inf),
            center=mp.Vector3(output_start + straight_length/2, input_sep/2),
            material=core_material
        )
    )
    geometry.append(
        mp.Block(
            mp.Vector3(straight_length, wg_width, mp.inf),
            center=mp.Vector3(output_start + straight_length/2, -input_sep/2),
            material=core_material
        )
    )

    # Source - inject into upper waveguide only
    sources = [
        mp.Source(
            mp.GaussianSource(freq, fwidth=0.1 * freq),
            component=mp.Ez,
            center=mp.Vector3(x_start + 1, input_sep/2),
            size=mp.Vector3(0, wg_width * 1.5, 0)
        )
    ]

    # Simulation
    sim = mp.Simulation(
        cell_size=cell_size,
        boundary_layers=[mp.PML(pml_thickness)],
        geometry=geometry,
        sources=sources,
        resolution=resolution
    )

    # Flux monitors
    nfreq = 50
    df = 0.15 * freq

    # Through port (upper output)
    through_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(cell_x/2 - pml_thickness - 1, input_sep/2),
            size=mp.Vector3(0, wg_width * 2, 0)
        )
    )

    # Cross port (lower output)
    cross_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(cell_x/2 - pml_thickness - 1, -input_sep/2),
            size=mp.Vector3(0, wg_width * 2, 0)
        )
    )

    # Input monitor
    input_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(x_start + 2, input_sep/2),
            size=mp.Vector3(0, wg_width * 2, 0)
        )
    )

    # Run
    print("Running FDTD simulation...")
    sim.run(until_after_sources=mp.stop_when_fields_decayed(
        50, mp.Ez, mp.Vector3(cell_x/2 - pml_thickness - 2, 0), 1e-4
    ))

    # Results
    freqs = np.array(mp.get_flux_freqs(through_mon))
    wavelengths = 1.0 / freqs
    through_flux = np.array(mp.get_fluxes(through_mon))
    cross_flux = np.array(mp.get_fluxes(cross_mon))
    input_flux = np.array(mp.get_fluxes(input_mon))

    # Normalize
    through_T = through_flux / (input_flux + 1e-20)
    cross_T = cross_flux / (input_flux + 1e-20)

    # Values at center frequency
    center_idx = len(freqs) // 2
    through_center = through_T[center_idx]
    cross_center = cross_T[center_idx]
    total = through_center + cross_center

    # Coupling ratio
    if total > 0:
        coupling_ratio = cross_center / total
    else:
        coupling_ratio = 0

    # Splitting ratio (how close to 50/50)
    split_error = abs(coupling_ratio - 0.5) * 100

    print(f"\nResults at lambda = {wavelength} um:")
    print(f"  Through port: {through_center:.4f}")
    print(f"  Cross port: {cross_center:.4f}")
    print(f"  Coupling ratio: {coupling_ratio:.4f} ({coupling_ratio*100:.1f}%)")
    print(f"  Split error from 50/50: {split_error:.1f}%")

    return {
        'wavelength': wavelength,
        'gap': gap,
        'coupling_length': coupling_length,
        'frequencies': freqs,
        'wavelengths': wavelengths,
        'through_flux': through_flux,
        'cross_flux': cross_flux,
        'through_T': through_T,
        'cross_T': cross_T,
        'through_center': through_center,
        'cross_center': cross_center,
        'coupling_ratio': coupling_ratio,
        'split_error_percent': split_error
    }


def run_gap_sweep(wavelength: float, gaps: list = None):
    """
    Sweep coupling gap to find optimal 50/50 splitting.
    """
    if gaps is None:
        gaps = [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]

    print(f"\n=== GAP SWEEP at lambda = {wavelength} um ===")

    results = []
    for gap in gaps:
        result = run_coupler_simulation(wavelength, gap=gap, resolution=20)
        results.append(result)

    return {
        'wavelength': wavelength,
        'gaps': gaps,
        'results': results
    }


def run_parameter_sweep(wavelength: float, gaps: list = None, lengths: list = None):
    """
    2D parameter sweep over gap and coupling length to find optimal 50/50 splitting.

    For 50% coupling: L = pi / (2 * kappa), where kappa decreases with larger gap.
    """
    if gaps is None:
        gaps = [0.2, 0.22, 0.25, 0.27, 0.3]
    if lengths is None:
        lengths = [6.0, 7.0, 8.0, 9.0, 10.0]

    print(f"\n=== 2D PARAMETER SWEEP at lambda = {wavelength} um ===")
    print(f"Gaps: {gaps}")
    print(f"Lengths: {lengths}")

    results = []
    best_result = None
    best_error = float('inf')

    for gap in gaps:
        for length in lengths:
            print(f"\n--- Testing gap={gap} um, length={length} um ---")
            result = run_coupler_simulation(wavelength, gap=gap,
                                            coupling_length=length, resolution=20)
            results.append(result)

            if result['split_error_percent'] < best_error:
                best_error = result['split_error_percent']
                best_result = result

    print(f"\n{'='*60}")
    print(f"BEST PARAMETERS FOUND:")
    print(f"  Gap: {best_result['gap']} um")
    print(f"  Coupling length: {best_result['coupling_length']} um")
    print(f"  Coupling ratio: {best_result['coupling_ratio']*100:.1f}%")
    print(f"  Error from 50/50: {best_result['split_error_percent']:.1f}%")
    print(f"{'='*60}")

    return {
        'wavelength': wavelength,
        'gaps': gaps,
        'lengths': lengths,
        'results': results,
        'best_result': best_result
    }


def save_results(result: dict, output_dir: str):
    """Save coupler simulation results."""
    os.makedirs(output_dir, exist_ok=True)

    if 'gaps' in result and 'lengths' in result:
        # 2D parameter sweep results
        wvl_nm = int(result['wavelength'] * 1000)

        csv_path = os.path.join(output_dir, f"coupler_param_sweep_{wvl_nm}nm.csv")
        header = "Gap (um),Length (um),Through T,Cross T,Coupling Ratio,Split Error (%)"
        data = []
        for r in result['results']:
            data.append([r['gap'], r['coupling_length'], r['through_center'],
                         r['cross_center'], r['coupling_ratio'], r['split_error_percent']])
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot 2D heatmap of coupling ratio
        gaps = result['gaps']
        lengths = result['lengths']
        coupling_matrix = np.zeros((len(gaps), len(lengths)))

        for r in result['results']:
            i = gaps.index(r['gap'])
            j = lengths.index(r['coupling_length'])
            coupling_matrix[i, j] = r['coupling_ratio']

        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(coupling_matrix, aspect='auto', origin='lower',
                       extent=[lengths[0], lengths[-1], gaps[0], gaps[-1]],
                       vmin=0.3, vmax=0.7, cmap='RdYlGn')

        # Add contour at 50%
        X, Y = np.meshgrid(lengths, gaps)
        cs = ax.contour(X, Y, coupling_matrix, levels=[0.48, 0.50, 0.52],
                        colors=['white', 'black', 'white'], linewidths=2)
        ax.clabel(cs, inline=True, fontsize=10, fmt='%.0f%%')

        ax.set_xlabel('Coupling Length (um)', fontsize=12)
        ax.set_ylabel('Gap (um)', fontsize=12)
        ax.set_title(f'Directional Coupler Optimization (lambda = {result["wavelength"]} um)\n'
                     f'Best: gap={result["best_result"]["gap"]} um, '
                     f'L={result["best_result"]["coupling_length"]} um, '
                     f'ratio={result["best_result"]["coupling_ratio"]*100:.1f}%', fontsize=12)

        cbar = plt.colorbar(im)
        cbar.set_label('Coupling Ratio', fontsize=12)

        # Mark best point
        ax.plot(result['best_result']['coupling_length'], result['best_result']['gap'],
                'k*', markersize=20, label='Best 50/50')
        ax.legend()

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"coupler_param_sweep_{wvl_nm}nm.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()

    elif 'gaps' in result:
        # Gap sweep results
        wvl_nm = int(result['wavelength'] * 1000)

        csv_path = os.path.join(output_dir, f"coupler_gap_sweep_{wvl_nm}nm.csv")
        header = "Gap (um),Through T,Cross T,Coupling Ratio,Split Error (%)"
        data = []
        for r in result['results']:
            data.append([r['gap'], r['through_center'], r['cross_center'],
                         r['coupling_ratio'], r['split_error_percent']])
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        gaps = [r['gap'] for r in result['results']]
        through = [r['through_center'] for r in result['results']]
        cross = [r['cross_center'] for r in result['results']]
        ratio = [r['coupling_ratio'] for r in result['results']]

        ax1.plot(gaps, through, 'b-o', linewidth=2, markersize=8, label='Through')
        ax1.plot(gaps, cross, 'r--s', linewidth=2, markersize=8, label='Cross')
        ax1.axhline(y=0.5, color='green', linestyle=':', label='50% target')
        ax1.set_xlabel('Gap (um)', fontsize=12)
        ax1.set_ylabel('Transmission', fontsize=12)
        ax1.set_title(f'Coupler Response vs Gap (lambda = {result["wavelength"]} um)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.plot(gaps, ratio, 'k-o', linewidth=2, markersize=8)
        ax2.axhline(y=0.5, color='green', linestyle='--', label='50/50 target')
        ax2.set_xlabel('Gap (um)', fontsize=12)
        ax2.set_ylabel('Coupling Ratio', fontsize=12)
        ax2.set_title('Coupling Ratio vs Gap', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 1)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"coupler_gap_sweep_{wvl_nm}nm.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()

    else:
        # Single simulation
        wvl_nm = int(result['wavelength'] * 1000)
        gap_nm = int(result['gap'] * 1000)

        csv_path = os.path.join(output_dir, f"coupler_{wvl_nm}nm_gap{gap_nm}nm.csv")
        header = "Frequency (Meep),Wavelength (um),Through Flux,Cross Flux,Through T,Cross T"
        data = np.column_stack((
            result['frequencies'], result['wavelengths'],
            result['through_flux'], result['cross_flux'],
            result['through_T'], result['cross_T']
        ))
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(result['wavelengths'], result['through_T'], 'b-', linewidth=2, label='Through port')
        ax.plot(result['wavelengths'], result['cross_T'], 'r--', linewidth=2, label='Cross port')
        ax.axvline(x=result['wavelength'], color='green', linestyle=':', label=f'lambda = {result["wavelength"]} um')
        ax.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5)

        ax.set_xlabel('Wavelength (um)', fontsize=12)
        ax.set_ylabel('Transmission', fontsize=12)
        ax.set_title(f'Directional Coupler (Gap = {result["gap"]} um, L = {result["coupling_length"]} um)\n'
                     f'Coupling ratio: {result["coupling_ratio"]*100:.1f}%', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"coupler_{wvl_nm}nm_gap{gap_nm}nm.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()


def main():
    parser = argparse.ArgumentParser(description='Directional Coupler Meep FDTD Simulation')
    parser.add_argument('--wavelength', type=float, default=1.55, help='Wavelength (um)')
    parser.add_argument('--gap', type=float, default=0.25, help='Coupling gap (um) - tuned for 50/50')
    parser.add_argument('--length', type=float, default=6.0, help='Coupling length (um) - tuned for 50/50')
    parser.add_argument('--sweep-gap', action='store_true', help='Sweep gap for optimization')
    parser.add_argument('--sweep-params', action='store_true', help='2D sweep of gap and length')
    parser.add_argument('--all-wavelengths', action='store_true', help='Test all ternary wavelengths')
    parser.add_argument('--resolution', type=int, default=25, help='FDTD resolution')
    parser.add_argument('--output', type=str, default=None, help='Output directory')

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = args.output or os.path.join(base_dir, 'data', 'csv')

    print("=" * 60)
    print("  DIRECTIONAL COUPLER - Meep FDTD Simulation")
    print("  For 50/50 Beam Splitting in Ternary Optical Computer")
    print("=" * 60)

    if args.sweep_params:
        result = run_parameter_sweep(args.wavelength)
        save_results(result, output_dir)

    elif args.sweep_gap:
        result = run_gap_sweep(args.wavelength)
        save_results(result, output_dir)

    elif args.all_wavelengths:
        for name, wvl in WAVELENGTHS.items():
            print(f"\n{'='*50}")
            print(f"  Testing {name}: {wvl} um")
            print('='*50)
            result = run_coupler_simulation(wvl, args.gap, args.length, args.resolution)
            save_results(result, output_dir)

    else:
        result = run_coupler_simulation(args.wavelength, args.gap, args.length, args.resolution)
        save_results(result, output_dir)

    print("\n" + "=" * 60)
    print("  SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
