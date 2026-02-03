#!/usr/bin/env python3
"""
Kerr Resonator Simulation for Optical Clock

FDTD simulation of ring resonator with Kerr nonlinearity for self-pulsing
optical clock generation. Critical for timing in the ternary optical computer.

Usage:
    python kerr_resonator_sim.py                     # Default simulation
    python kerr_resonator_sim.py --radius 10         # Specific radius
    python kerr_resonator_sim.py --sweep-power       # Power sweep for bistability
    python kerr_resonator_sim.py --time-domain       # Full time-domain for pulsing
"""

import os
import sys
import argparse
import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# Target clock frequency
TARGET_CLOCK_FREQ = 617e6  # 617 MHz word rate


def run_kerr_resonator(wavelength: float = 1.55, radius: float = 10.0,
                       chi3: float = 1e-3, resolution: int = 30):
    """
    Simulate Kerr ring resonator.

    Args:
        wavelength: Operating wavelength (μm)
        radius: Ring radius (μm)
        chi3: Third-order susceptibility (Kerr coefficient)
        resolution: FDTD resolution (pixels/μm)

    Returns:
        dict with resonance properties, Q factor, Kerr shift
    """
    print(f"\n--- KERR RESONATOR SIMULATION ---")
    print(f"Wavelength: {wavelength} μm, Radius: {radius} μm")
    print(f"χ³ (Kerr): {chi3}")

    freq = 1.0 / wavelength

    # Geometry parameters
    wg_width = 0.5
    coupling_gap = 0.2
    bus_length = 30.0

    # Cell dimensions
    cell_x = bus_length + 10
    cell_y = 2 * radius + wg_width * 4 + 6
    pml_thickness = 1.5

    # Material with Kerr nonlinearity
    n_core = 2.0
    # Meep chi3 is the Kerr nonlinearity χ^(3)
    kerr_material = mp.Medium(index=n_core, chi3=chi3)
    linear_material = mp.Medium(index=n_core)

    cell_size = mp.Vector3(cell_x, cell_y, 0)

    # Build geometry
    geometry = []

    # Bus waveguide (linear, at bottom)
    bus_y = -cell_y/2 + pml_thickness + 2
    geometry.append(
        mp.Block(
            mp.Vector3(bus_length, wg_width, mp.inf),
            center=mp.Vector3(0, bus_y),
            material=linear_material
        )
    )

    # Ring resonator (with Kerr nonlinearity)
    # Correct formula: ring outer edge should be coupling_gap away from bus top edge
    # Ring outer edge = ring_center_y - (radius + wg_width/2)
    # Bus top edge = bus_y + wg_width/2
    # Gap = ring outer edge - bus top edge = coupling_gap
    # Therefore: ring_center_y = bus_y + wg_width + coupling_gap + radius
    ring_center_y = bus_y + wg_width + coupling_gap + radius

    # Build ring using cylinder (Meep supports this directly)
    # Outer cylinder - inner cylinder = ring
    geometry.append(
        mp.Cylinder(
            radius=radius + wg_width/2,
            height=mp.inf,
            center=mp.Vector3(0, ring_center_y),
            material=kerr_material
        )
    )
    # Remove inner part (air)
    geometry.append(
        mp.Cylinder(
            radius=radius - wg_width/2,
            height=mp.inf,
            center=mp.Vector3(0, ring_center_y),
            material=mp.air
        )
    )

    # Source - CW at resonance
    sources = [
        mp.Source(
            mp.GaussianSource(freq, fwidth=0.05 * freq),
            component=mp.Ez,
            center=mp.Vector3(-bus_length/2 + 2, bus_y),
            size=mp.Vector3(0, wg_width * 2, 0)
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

    # Flux monitors - use more frequency points for accurate Q measurement
    nfreq = 500
    df = 0.2 * freq  # Narrower frequency range for better resolution

    # Through port (bus output)
    through_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(bus_length/2 - 2, bus_y),
            size=mp.Vector3(0, wg_width * 2, 0)
        )
    )

    # Drop port (if add-drop config) - monitor at ring
    # For basic ring, we monitor the field inside the ring
    ring_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(0, ring_center_y + radius),
            size=mp.Vector3(wg_width * 2, 0, 0)
        )
    )

    # Input monitor
    input_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(-bus_length/2 + 4, bus_y),
            size=mp.Vector3(0, wg_width * 2, 0)
        )
    )

    # Run - use longer decay time and stricter threshold for accurate Q measurement
    print("Running FDTD simulation...")
    sim.run(until_after_sources=mp.stop_when_fields_decayed(
        200, mp.Ez, mp.Vector3(bus_length/2 - 3, bus_y), 1e-7
    ))

    # Results
    freqs = np.array(mp.get_flux_freqs(through_mon))
    wavelengths = 1.0 / freqs
    through_flux = np.array(mp.get_fluxes(through_mon))
    ring_flux = np.array(mp.get_fluxes(ring_mon))
    input_flux = np.array(mp.get_fluxes(input_mon))

    # Transmission
    through_T = through_flux / (input_flux + 1e-20)

    # Find resonance dips
    resonance_indices = []
    for i in range(1, len(through_T) - 1):
        if through_T[i] < through_T[i-1] and through_T[i] < through_T[i+1]:
            if through_T[i] < 0.5:  # Significant dip
                resonance_indices.append(i)

    resonances = []
    for idx in resonance_indices:
        res_wvl = wavelengths[idx]
        res_T = through_T[idx]

        # Estimate Q from FWHM
        half_depth = (1 + res_T) / 2
        left_idx = idx
        right_idx = idx
        while left_idx > 0 and through_T[left_idx] < half_depth:
            left_idx -= 1
        while right_idx < len(through_T) - 1 and through_T[right_idx] < half_depth:
            right_idx += 1

        if right_idx > left_idx:
            fwhm = wavelengths[left_idx] - wavelengths[right_idx]
            Q = res_wvl / (fwhm + 1e-10)
        else:
            Q = 0

        resonances.append({
            'wavelength': res_wvl,
            'transmission': res_T,
            'Q': Q
        })

    # FSR calculation
    if len(resonances) >= 2:
        FSR = abs(resonances[0]['wavelength'] - resonances[1]['wavelength'])
    else:
        # Theoretical FSR
        n_eff = n_core * 0.9  # Approximate effective index
        circumference = 2 * np.pi * radius
        FSR = wavelength**2 / (n_eff * circumference)

    # Finesse
    if len(resonances) > 0 and resonances[0]['Q'] > 0:
        finesse = FSR * resonances[0]['Q'] / wavelength
    else:
        finesse = 0

    # Kerr shift estimate
    # Δλ = λ * (n2 * I) / n
    # For self-pulsing, need bistability threshold
    n2 = chi3 / (n_core**2)  # Simplified relation
    kerr_shift_per_watt = wavelength * n2 / (n_core * wg_width**2)

    print(f"\nResults:")
    print(f"  Resonances found: {len(resonances)}")
    if len(resonances) > 0:
        print(f"  Nearest resonance: {resonances[0]['wavelength']:.4f} μm")
        print(f"  Q factor: {resonances[0]['Q']:.0f}")
    print(f"  FSR: {FSR*1e3:.2f} nm")
    print(f"  Finesse: {finesse:.1f}")
    print(f"  Kerr shift coefficient: {kerr_shift_per_watt:.2e} μm/W")

    return {
        'wavelength': wavelength,
        'radius': radius,
        'chi3': chi3,
        'frequencies': freqs,
        'wavelengths': wavelengths,
        'through_flux': through_flux,
        'ring_flux': ring_flux,
        'through_T': through_T,
        'resonances': resonances,
        'FSR': FSR,
        'finesse': finesse,
        'kerr_shift_per_watt': kerr_shift_per_watt
    }


def run_power_sweep(wavelength: float = 1.55, radius: float = 10.0,
                    chi3_values: list = None):
    """
    Sweep Kerr coefficient (equivalent to power sweep) for bistability analysis.
    """
    if chi3_values is None:
        chi3_values = [0, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2]

    print(f"\n=== KERR COEFFICIENT SWEEP ===")

    results = []
    for chi3 in chi3_values:
        result = run_kerr_resonator(wavelength, radius, chi3, resolution=30)
        results.append(result)

    return {
        'wavelength': wavelength,
        'radius': radius,
        'chi3_values': chi3_values,
        'results': results
    }


def run_time_domain_simulation(wavelength: float = 1.55, radius: float = 10.0,
                               chi3: float = 1e-2, duration: float = 500.0,
                               resolution: int = 30):
    """
    Run time-domain simulation to observe self-pulsing dynamics.
    """
    print(f"\n--- TIME-DOMAIN KERR RESONATOR ---")
    print(f"Duration: {duration} Meep time units")

    freq = 1.0 / wavelength

    # Geometry (same as above)
    wg_width = 0.5
    coupling_gap = 0.2
    bus_length = 30.0

    cell_x = bus_length + 10
    cell_y = 2 * radius + wg_width * 4 + 6
    pml_thickness = 1.5

    n_core = 2.0
    kerr_material = mp.Medium(index=n_core, chi3=chi3)
    linear_material = mp.Medium(index=n_core)

    cell_size = mp.Vector3(cell_x, cell_y, 0)
    bus_y = -cell_y/2 + pml_thickness + 2
    # Correct formula: ring outer edge should be coupling_gap away from bus top edge
    # Ring outer edge = ring_center_y - (radius + wg_width/2)
    # Bus top edge = bus_y + wg_width/2
    # Gap = ring outer edge - bus top edge = coupling_gap
    # Therefore: ring_center_y = bus_y + wg_width + coupling_gap + radius
    ring_center_y = bus_y + wg_width + coupling_gap + radius

    geometry = [
        mp.Block(
            mp.Vector3(bus_length, wg_width, mp.inf),
            center=mp.Vector3(0, bus_y),
            material=linear_material
        ),
        mp.Cylinder(
            radius=radius + wg_width/2,
            height=mp.inf,
            center=mp.Vector3(0, ring_center_y),
            material=kerr_material
        ),
        mp.Cylinder(
            radius=radius - wg_width/2,
            height=mp.inf,
            center=mp.Vector3(0, ring_center_y),
            material=mp.air
        )
    ]

    # CW source (continuous)
    sources = [
        mp.Source(
            mp.ContinuousSource(freq),
            component=mp.Ez,
            center=mp.Vector3(-bus_length/2 + 2, bus_y),
            size=mp.Vector3(0, wg_width * 2, 0)
        )
    ]

    sim = mp.Simulation(
        cell_size=cell_size,
        boundary_layers=[mp.PML(pml_thickness)],
        geometry=geometry,
        sources=sources,
        resolution=resolution
    )

    # Record field at output over time
    output_pos = mp.Vector3(bus_length/2 - 2, bus_y)
    ring_pos = mp.Vector3(0, ring_center_y)

    time_data = []
    output_data = []
    ring_data = []

    def record_fields(sim):
        time_data.append(sim.meep_time())
        output_data.append(abs(sim.get_field_point(mp.Ez, output_pos))**2)
        ring_data.append(abs(sim.get_field_point(mp.Ez, ring_pos))**2)

    # Run with recording
    print("Running time-domain simulation...")
    sim.run(mp.at_every(0.5, record_fields), until=duration)

    time_arr = np.array(time_data)
    output_arr = np.array(output_data)
    ring_arr = np.array(ring_data)

    # Analyze for pulsing
    # Look for oscillations in ring intensity
    if len(ring_arr) > 10:
        ring_fft = np.fft.fft(ring_arr - np.mean(ring_arr))
        freqs_fft = np.fft.fftfreq(len(ring_arr), d=0.5)

        # Find dominant frequency (excluding DC)
        mag = np.abs(ring_fft)
        mag[0] = 0  # Remove DC
        peak_idx = np.argmax(mag[:len(mag)//2])
        pulsing_freq = abs(freqs_fft[peak_idx])
    else:
        pulsing_freq = 0

    print(f"\nTime-domain results:")
    print(f"  Recorded {len(time_data)} time points")
    print(f"  Dominant oscillation frequency: {pulsing_freq:.4f} (Meep units)")
    if pulsing_freq > 0:
        period = 1.0 / pulsing_freq
        print(f"  Oscillation period: {period:.2f} (Meep time)")

    return {
        'wavelength': wavelength,
        'radius': radius,
        'chi3': chi3,
        'duration': duration,
        'time': time_arr,
        'output_intensity': output_arr,
        'ring_intensity': ring_arr,
        'pulsing_frequency': pulsing_freq
    }


def save_results(result: dict, output_dir: str):
    """Save Kerr resonator results."""
    os.makedirs(output_dir, exist_ok=True)

    if 'chi3_values' in result:
        # Chi3 sweep
        csv_path = os.path.join(output_dir, "kerr_chi3_sweep.csv")
        header = "Chi3,FSR (nm),Finesse,Q (first resonance)"
        data = []
        for r in result['results']:
            Q = r['resonances'][0]['Q'] if len(r['resonances']) > 0 else 0
            data.append([r['chi3'], r['FSR'] * 1000, r['finesse'], Q])
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        chi3_vals = [r['chi3'] for r in result['results']]
        Q_vals = [r['resonances'][0]['Q'] if len(r['resonances']) > 0 else 0
                  for r in result['results']]
        finesse_vals = [r['finesse'] for r in result['results']]

        ax1.semilogx(chi3_vals[1:], Q_vals[1:], 'b-o', linewidth=2, markersize=8)
        ax1.set_xlabel('χ³ (Kerr coefficient)', fontsize=12)
        ax1.set_ylabel('Q Factor', fontsize=12)
        ax1.set_title('Q vs Kerr Nonlinearity', fontsize=12)
        ax1.grid(True, alpha=0.3)

        ax2.semilogx(chi3_vals[1:], finesse_vals[1:], 'r-s', linewidth=2, markersize=8)
        ax2.set_xlabel('χ³ (Kerr coefficient)', fontsize=12)
        ax2.set_ylabel('Finesse', fontsize=12)
        ax2.set_title('Finesse vs Kerr Nonlinearity', fontsize=12)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, "kerr_chi3_sweep.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()

    elif 'time' in result:
        # Time-domain
        csv_path = os.path.join(output_dir, "kerr_time_domain.csv")
        header = "Time,Output Intensity,Ring Intensity"
        data = np.column_stack((result['time'], result['output_intensity'], result['ring_intensity']))
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        ax1.plot(result['time'], result['output_intensity'], 'b-', linewidth=1)
        ax1.set_xlabel('Time (Meep units)', fontsize=12)
        ax1.set_ylabel('Output Intensity', fontsize=12)
        ax1.set_title('Kerr Resonator Time-Domain Response', fontsize=12)
        ax1.grid(True, alpha=0.3)

        ax2.plot(result['time'], result['ring_intensity'], 'r-', linewidth=1)
        ax2.set_xlabel('Time (Meep units)', fontsize=12)
        ax2.set_ylabel('Ring Intensity', fontsize=12)
        ax2.set_title(f'Ring Cavity (Pulsing freq: {result["pulsing_frequency"]:.4f})', fontsize=12)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, "kerr_time_domain.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()

    else:
        # Single simulation
        radius_um = int(result['radius'])

        csv_path = os.path.join(output_dir, f"kerr_resonator_R{radius_um}um.csv")
        header = "Frequency (Meep),Wavelength (um),Through Flux,Ring Flux,Through T"
        data = np.column_stack((
            result['frequencies'], result['wavelengths'],
            result['through_flux'], result['ring_flux'], result['through_T']
        ))
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(result['wavelengths'], result['through_T'], 'b-', linewidth=1.5)

        # Mark resonances
        for res in result['resonances']:
            ax.axvline(x=res['wavelength'], color='red', linestyle='--', alpha=0.5)
            ax.annotate(f"Q={res['Q']:.0f}", xy=(res['wavelength'], res['transmission']),
                        fontsize=8, ha='center')

        ax.set_xlabel('Wavelength (μm)', fontsize=12)
        ax.set_ylabel('Through Transmission', fontsize=12)
        ax.set_title(f'Kerr Ring Resonator (R = {result["radius"]} μm, χ³ = {result["chi3"]})\n'
                     f'FSR = {result["FSR"]*1000:.1f} nm, Finesse = {result["finesse"]:.1f}',
                     fontsize=12)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"kerr_resonator_R{radius_um}um.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()


def main():
    parser = argparse.ArgumentParser(description='Kerr Resonator Meep FDTD Simulation')
    parser.add_argument('--wavelength', type=float, default=1.55, help='Wavelength (μm)')
    parser.add_argument('--radius', type=float, default=10.0, help='Ring radius (μm)')
    parser.add_argument('--chi3', type=float, default=1e-3, help='Kerr coefficient')
    parser.add_argument('--sweep-power', action='store_true', help='Sweep χ³ values')
    parser.add_argument('--time-domain', action='store_true', help='Time-domain simulation')
    parser.add_argument('--duration', type=float, default=500.0, help='Time-domain duration')
    parser.add_argument('--resolution', type=int, default=30, help='FDTD resolution')
    parser.add_argument('--output', type=str, default=None, help='Output directory')

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = args.output or os.path.join(base_dir, 'data', 'csv')

    print("=" * 60)
    print("  KERR RESONATOR - Meep FDTD Simulation")
    print("  Optical Clock for Ternary Computer")
    print("=" * 60)
    print(f"  Target clock: {TARGET_CLOCK_FREQ/1e6:.0f} MHz")

    if args.sweep_power:
        result = run_power_sweep(args.wavelength, args.radius)
        save_results(result, output_dir)

    elif args.time_domain:
        result = run_time_domain_simulation(args.wavelength, args.radius,
                                            args.chi3, args.duration, args.resolution)
        save_results(result, output_dir)

    else:
        result = run_kerr_resonator(args.wavelength, args.radius, args.chi3, args.resolution)
        save_results(result, output_dir)

    print("\n" + "=" * 60)
    print("  SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
