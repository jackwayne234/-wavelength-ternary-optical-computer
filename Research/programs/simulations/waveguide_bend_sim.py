#!/usr/bin/env python3
"""
Waveguide Bend Simulation

FDTD simulation of waveguide bends to characterize bend loss vs radius.
Critical for compact chip layout design.

Usage:
    python waveguide_bend_sim.py                    # Default 90° bend
    python waveguide_bend_sim.py --radius 5         # Specific radius
    python waveguide_bend_sim.py --sweep-radius     # Radius sweep
    python waveguide_bend_sim.py --all-wavelengths  # Test all ternary wavelengths
"""

import os
import sys
import argparse
import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# Ternary wavelengths (μm)
WAVELENGTHS = {
    'RED': 1.55,
    'GREEN': 1.216,
    'BLUE': 1.0
}


def run_bend_simulation(wavelength: float, bend_radius: float = 5.0,
                        bend_angle: float = 90.0, resolution: int = 20):
    """
    Simulate waveguide bend at given wavelength and radius.

    Args:
        wavelength: Operating wavelength (μm)
        bend_radius: Bend radius (μm)
        bend_angle: Bend angle (degrees)
        resolution: FDTD resolution (pixels/μm)

    Returns:
        dict with transmission and bend loss
    """
    print(f"\n--- WAVEGUIDE BEND SIMULATION ---")
    print(f"Wavelength: {wavelength} μm, Radius: {bend_radius} μm, Angle: {bend_angle}°")

    freq = 1.0 / wavelength
    angle_rad = np.radians(bend_angle)

    # Geometry parameters
    wg_width = 0.5
    straight_length = 5.0

    # Material
    n_core = 2.0
    core_material = mp.Medium(index=n_core)

    # PML thickness and margins
    pml_thickness = 1.5
    margin = 2.0

    # Cell size - must accommodate full structure with proper margins
    if bend_angle == 90:
        cell_x = 2*pml_thickness + 2*margin + straight_length + bend_radius
        cell_y = 2*pml_thickness + 2*margin + straight_length + bend_radius
    else:
        cell_x = 2*pml_thickness + 2*margin + straight_length + bend_radius * (1 + np.cos(angle_rad))
        cell_y = 2*pml_thickness + 2*margin + straight_length + bend_radius * np.sin(angle_rad)

    cell_size = mp.Vector3(cell_x, cell_y, 0)
    print(f"Cell size: {cell_x:.2f} x {cell_y:.2f} μm")

    # Reference positions - properly calculated
    input_y = -cell_y/2 + pml_thickness + margin + wg_width/2
    input_x_start = -cell_x/2 + pml_thickness + margin
    input_x_end = input_x_start + straight_length

    bend_center_x = input_x_end
    bend_center_y = input_y + bend_radius

    print(f"Input waveguide: y={input_y:.2f}, x from {input_x_start:.2f} to {input_x_end:.2f}")
    print(f"Bend center: ({bend_center_x:.2f}, {bend_center_y:.2f})")

    # Build bend geometry using segments
    geometry = []

    # Input straight section
    geometry.append(
        mp.Block(
            mp.Vector3(straight_length, wg_width, mp.inf),
            center=mp.Vector3(input_x_start + straight_length/2, input_y),
            material=core_material
        )
    )

    # Curved section using segments
    n_segments = max(18, int(bend_angle / 5))  # ~5° per segment, min 18

    for i in range(n_segments):
        theta1 = -np.pi/2 + i * angle_rad / n_segments
        theta2 = -np.pi/2 + (i + 1) * angle_rad / n_segments
        theta_mid = (theta1 + theta2) / 2

        # Segment center position
        x = bend_center_x + bend_radius * np.cos(theta_mid)
        y = bend_center_y + bend_radius * np.sin(theta_mid)

        # Segment length - 30% overlap for continuity
        seg_length = bend_radius * angle_rad / n_segments * 1.3

        # Orientation
        e1 = mp.Vector3(np.cos(theta_mid + np.pi/2), np.sin(theta_mid + np.pi/2), 0)
        e2 = mp.Vector3(-np.sin(theta_mid + np.pi/2), np.cos(theta_mid + np.pi/2), 0)

        geometry.append(
            mp.Block(
                mp.Vector3(seg_length, wg_width, mp.inf),
                center=mp.Vector3(x, y),
                e1=e1,
                e2=e2,
                material=core_material
            )
        )

    # Output straight section
    if bend_angle == 90:
        # For 90° bend: arc ends at theta=0, which is (center_x + R, center_y)
        # Output goes vertically (+y direction)
        out_x = bend_center_x + bend_radius
        out_y_start = bend_center_y
        print(f"Output waveguide: x={out_x:.2f}, y from {out_y_start:.2f} to {out_y_start + straight_length:.2f}")
        geometry.append(
            mp.Block(
                mp.Vector3(wg_width, straight_length, mp.inf),
                center=mp.Vector3(out_x, out_y_start + straight_length/2),
                material=core_material
            )
        )
        output_pos = mp.Vector3(out_x, out_y_start + straight_length - 1)
        output_size = mp.Vector3(wg_width * 2, 0, 0)
    else:
        end_angle = -np.pi/2 + angle_rad
        out_x = bend_center_x + bend_radius * np.cos(end_angle)
        out_y = bend_center_y + bend_radius * np.sin(end_angle)

        dx = np.cos(end_angle + np.pi/2)
        dy = np.sin(end_angle + np.pi/2)

        geometry.append(
            mp.Block(
                mp.Vector3(straight_length, wg_width, mp.inf),
                center=mp.Vector3(out_x + dx * straight_length/2, out_y + dy * straight_length/2),
                e1=mp.Vector3(dx, dy, 0),
                e2=mp.Vector3(-dy, dx, 0),
                material=core_material
            )
        )
        output_pos = mp.Vector3(out_x + dx * (straight_length - 1), out_y + dy * (straight_length - 1))
        output_size = mp.Vector3(wg_width * 2 * abs(dy) + 0.1, wg_width * 2 * abs(dx) + 0.1, 0)

    # Source - aligned with input waveguide center
    source_x = input_x_start + 1.0
    sources = [
        mp.Source(
            mp.GaussianSource(freq, fwidth=0.15 * freq),
            component=mp.Ez,
            center=mp.Vector3(source_x, input_y),
            size=mp.Vector3(0, wg_width * 2.5, 0)
        )
    ]
    print(f"Source at: ({source_x:.2f}, {input_y:.2f})")

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

    # Output monitor
    output_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(center=output_pos, size=output_size)
    )

    # Input monitor - aligned with input waveguide
    input_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(input_x_start + 2.0, input_y),
            size=mp.Vector3(0, wg_width * 2.5, 0)
        )
    )

    # Run
    print("Running FDTD simulation...")
    sim.run(until_after_sources=mp.stop_when_fields_decayed(
        50, mp.Ez, output_pos, 1e-4
    ))

    # Results
    freqs = np.array(mp.get_flux_freqs(output_mon))
    wavelengths = 1.0 / freqs
    output_flux = np.array(mp.get_fluxes(output_mon))
    input_flux = np.array(mp.get_fluxes(input_mon))

    transmission = output_flux / (input_flux + 1e-20)

    # At center frequency
    center_idx = len(freqs) // 2
    T_center = transmission[center_idx]

    # Bend loss in dB
    if T_center > 0:
        bend_loss_dB = -10 * np.log10(T_center)
    else:
        bend_loss_dB = float('inf')

    # Loss per 90 degrees (normalized)
    loss_per_90 = bend_loss_dB * (90 / bend_angle)

    print(f"\nResults at λ = {wavelength} μm, R = {bend_radius} μm:")
    print(f"  Transmission: {T_center:.4f}")
    print(f"  Bend loss: {bend_loss_dB:.3f} dB")
    print(f"  Loss per 90°: {loss_per_90:.3f} dB")

    return {
        'wavelength': wavelength,
        'bend_radius': bend_radius,
        'bend_angle': bend_angle,
        'frequencies': freqs,
        'wavelengths': wavelengths,
        'output_flux': output_flux,
        'input_flux': input_flux,
        'transmission': transmission,
        'T_center': T_center,
        'bend_loss_dB': bend_loss_dB,
        'loss_per_90_dB': loss_per_90
    }


def run_radius_sweep(wavelength: float, radii: list = None):
    """
    Sweep bend radius to find minimum radius for acceptable loss.
    """
    if radii is None:
        radii = [2.0, 3.0, 5.0, 7.0, 10.0, 15.0, 20.0]

    print(f"\n=== RADIUS SWEEP at λ = {wavelength} μm ===")

    results = []
    for radius in radii:
        result = run_bend_simulation(wavelength, bend_radius=radius, resolution=18)
        results.append(result)

    return {
        'wavelength': wavelength,
        'radii': radii,
        'results': results
    }


def save_results(result: dict, output_dir: str):
    """Save bend simulation results."""
    os.makedirs(output_dir, exist_ok=True)

    if 'radii' in result:
        # Radius sweep
        wvl_nm = int(result['wavelength'] * 1000)

        csv_path = os.path.join(output_dir, f"bend_radius_sweep_{wvl_nm}nm.csv")
        header = "Radius (um),Transmission,Bend Loss (dB),Loss per 90deg (dB)"
        data = [[r['bend_radius'], r['T_center'], r['bend_loss_dB'], r['loss_per_90_dB']]
                for r in result['results']]
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        radii = [r['bend_radius'] for r in result['results']]
        trans = [r['T_center'] for r in result['results']]
        loss = [r['bend_loss_dB'] for r in result['results']]

        ax1.plot(radii, trans, 'b-o', linewidth=2, markersize=8)
        ax1.axhline(y=0.9, color='green', linestyle='--', label='90% threshold')
        ax1.set_xlabel('Bend Radius (μm)', fontsize=12)
        ax1.set_ylabel('Transmission', fontsize=12)
        ax1.set_title(f'Bend Transmission vs Radius (λ = {result["wavelength"]} μm)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.semilogy(radii, loss, 'r-s', linewidth=2, markersize=8)
        ax2.axhline(y=0.5, color='green', linestyle='--', label='0.5 dB threshold')
        ax2.set_xlabel('Bend Radius (μm)', fontsize=12)
        ax2.set_ylabel('Bend Loss (dB)', fontsize=12)
        ax2.set_title('Bend Loss vs Radius', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"bend_radius_sweep_{wvl_nm}nm.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()

    else:
        # Single simulation
        wvl_nm = int(result['wavelength'] * 1000)
        radius_um = int(result['bend_radius'])

        csv_path = os.path.join(output_dir, f"bend_{wvl_nm}nm_R{radius_um}um.csv")
        header = "Frequency (Meep),Wavelength (um),Output Flux,Input Flux,Transmission"
        data = np.column_stack((
            result['frequencies'], result['wavelengths'],
            result['output_flux'], result['input_flux'], result['transmission']
        ))
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(result['wavelengths'], result['transmission'], 'b-', linewidth=2)
        ax.axvline(x=result['wavelength'], color='green', linestyle=':', label=f'λ = {result["wavelength"]} μm')

        ax.set_xlabel('Wavelength (μm)', fontsize=12)
        ax.set_ylabel('Transmission', fontsize=12)
        ax.set_title(f'Waveguide Bend (R = {result["bend_radius"]} μm, {result["bend_angle"]}°)\n'
                     f'Loss: {result["bend_loss_dB"]:.2f} dB', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"bend_{wvl_nm}nm_R{radius_um}um.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()


def main():
    parser = argparse.ArgumentParser(description='Waveguide Bend Meep FDTD Simulation')
    parser.add_argument('--wavelength', type=float, default=1.55, help='Wavelength (μm)')
    parser.add_argument('--radius', type=float, default=5.0, help='Bend radius (μm)')
    parser.add_argument('--angle', type=float, default=90.0, help='Bend angle (degrees)')
    parser.add_argument('--sweep-radius', action='store_true', help='Sweep radius')
    parser.add_argument('--all-wavelengths', action='store_true', help='Test all ternary wavelengths')
    parser.add_argument('--resolution', type=int, default=20, help='FDTD resolution')
    parser.add_argument('--output', type=str, default=None, help='Output directory')

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = args.output or os.path.join(base_dir, 'data', 'csv')

    print("=" * 60)
    print("  WAVEGUIDE BEND - Meep FDTD Simulation")
    print("  Bend Loss Characterization for Chip Layout")
    print("=" * 60)

    if args.sweep_radius:
        result = run_radius_sweep(args.wavelength)
        save_results(result, output_dir)

    elif args.all_wavelengths:
        for name, wvl in WAVELENGTHS.items():
            print(f"\n{'='*50}")
            print(f"  Testing {name}: {wvl} μm")
            print('='*50)
            result = run_bend_simulation(wvl, args.radius, args.angle, args.resolution)
            save_results(result, output_dir)

    else:
        result = run_bend_simulation(args.wavelength, args.radius, args.angle, args.resolution)
        save_results(result, output_dir)

    print("\n" + "=" * 60)
    print("  SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
