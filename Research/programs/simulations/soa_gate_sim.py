#!/usr/bin/env python3
"""
Semiconductor Optical Amplifier (SOA) Gate Simulation

FDTD simulation of SOA for Tier 2 RAM gating and signal amplification.
Models gain dynamics, saturation, and switching behavior.

REFINED VERSION: Corrected gain modeling with proper D_conductivity calculation
and improved waveguide geometry using eigenmode source for better mode coupling.

Key improvements:
1. Proper D_conductivity calculation for target gain (negative for amplification)
2. Higher index contrast (n_core=3.4, n_clad=1.5) for better mode confinement
3. EigenModeSource for efficient waveguide coupling
4. Calibrated gain relationship: Gain(dB) ~ 12.7 * |sigma_D| * L (for L in um)

Usage:
    python soa_gate_sim.py                      # Default gain test (20 dB target)
    python soa_gate_sim.py --wavelength 1.55    # Single wavelength
    python soa_gate_sim.py --target-gain 25     # Specify target gain in dB
    python soa_gate_sim.py --sweep-gain         # Sweep gain levels
    python soa_gate_sim.py --switching          # Test switching dynamics
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

# Calibration constant: Gain(dB) = GAIN_CALIBRATION * |sigma_D| * L
# Empirically determined from Meep simulations
GAIN_CALIBRATION = 12.7  # dB per (sigma_D * um)


def calculate_sigma_D(target_gain_dB: float, soa_length_um: float) -> float:
    """
    Calculate the D_conductivity required for target gain.

    In Meep, D_conductivity modifies the permittivity as:
        eps_eff = eps + i * sigma_D / omega

    For gain (amplification), sigma_D must be NEGATIVE.
    Empirically calibrated relationship: Gain(dB) = 12.7 * |sigma_D| * L

    Args:
        target_gain_dB: Target power gain in dB (e.g., 20 dB)
        soa_length_um: SOA active region length in micrometers

    Returns:
        D_conductivity value (negative for gain)
    """
    # Invert the calibrated relationship: |sigma_D| = Gain(dB) / (12.7 * L)
    # Use negative value for gain
    sigma_D = -target_gain_dB / (GAIN_CALIBRATION * soa_length_um)
    return sigma_D


def create_soa_material(target_gain_dB: float, soa_length_um: float,
                        n_core: float = 3.4) -> mp.Medium:
    """
    Create SOA gain material model with properly calculated conductivity.

    Args:
        target_gain_dB: Target power gain in dB
        soa_length_um: SOA active region length in micrometers
        n_core: Refractive index of SOA core material

    Returns:
        Meep material with gain
    """
    sigma_D = calculate_sigma_D(target_gain_dB, soa_length_um)

    soa_material = mp.Medium(
        index=n_core,
        D_conductivity=sigma_D  # Negative value for gain
    )

    return soa_material


def run_soa_simulation(wavelength: float, soa_length: float = 30.0,
                       target_gain_dB: float = 20.0, resolution: int = 20,
                       use_eigenmode: bool = True):
    """
    Simulate SOA gate at given wavelength with improved gain modeling.

    Args:
        wavelength: Operating wavelength (um)
        soa_length: SOA active region length (um)
        target_gain_dB: Target gain in dB
        resolution: FDTD resolution (pixels/um)
        use_eigenmode: Use EigenModeSource for better coupling (recommended)

    Returns:
        dict with gain, ASE noise estimate, and diagnostic data
    """
    print(f"\n--- SOA GATE SIMULATION (REFINED) ---")
    print(f"Wavelength: {wavelength} um, SOA length: {soa_length} um")
    print(f"Target gain: {target_gain_dB} dB")

    freq = 1.0 / wavelength

    # Material parameters - high contrast for good confinement
    n_core = 3.4   # SOA core (InGaAsP-like)
    n_clad = 1.5   # Cladding (air or low-index material)

    # Calculate the required conductivity for target gain
    sigma_D = calculate_sigma_D(target_gain_dB, soa_length)
    print(f"  Calculated D_conductivity: {sigma_D:.6f}")

    # Create materials
    soa_material = mp.Medium(index=n_core, D_conductivity=sigma_D)
    clad_material = mp.Medium(index=n_clad)

    # Waveguide dimensions
    wg_width = 0.4  # Single-mode width for good confinement

    # Cell dimensions
    pml_thickness = 1.0
    cell_x = soa_length + 10  # Extra space for source/monitors
    cell_y = 4.0  # Enough for evanescent field

    cell_size = mp.Vector3(cell_x, cell_y, 0)

    # Geometry: single gain waveguide
    geometry = [
        mp.Block(
            mp.Vector3(soa_length, wg_width, mp.inf),
            center=mp.Vector3(0, 0),
            material=soa_material
        )
    ]

    # Source setup
    if use_eigenmode:
        # EigenModeSource for efficient waveguide mode excitation
        sources = [
            mp.EigenModeSource(
                src=mp.GaussianSource(freq, fwidth=0.1 * freq),
                center=mp.Vector3(-soa_length/2 + 1, 0),
                size=mp.Vector3(0, cell_y - 2*pml_thickness),
                eig_band=1,
                eig_parity=mp.ODD_Z,  # TE-like mode
                eig_match_freq=True
            )
        ]
    else:
        # Simple Gaussian source (fallback)
        sources = [
            mp.Source(
                mp.GaussianSource(freq, fwidth=0.1 * freq),
                component=mp.Ez,
                center=mp.Vector3(-soa_length/2 + 1, 0),
                size=mp.Vector3(0, wg_width * 3)
            )
        ]

    # Simulation
    sim = mp.Simulation(
        cell_size=cell_size,
        boundary_layers=[mp.PML(pml_thickness)],
        geometry=geometry,
        sources=sources,
        default_material=clad_material,
        resolution=resolution
    )

    # Monitor positions - inside the gain region
    input_mon_x = -soa_length/2 + 3
    output_mon_x = soa_length/2 - 3

    # Flux monitors
    nfreq = 11
    df = 0.1 * freq

    input_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(input_mon_x, 0),
            size=mp.Vector3(0, wg_width * 3)
        )
    )

    output_mon = sim.add_flux(
        freq, df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(output_mon_x, 0),
            size=mp.Vector3(0, wg_width * 3)
        )
    )

    # Run simulation
    print("Running FDTD simulation...")
    sim.run(until=200)

    # Results
    freqs = np.array(mp.get_flux_freqs(output_mon))
    wavelengths = 1.0 / freqs
    output_flux = np.abs(np.array(mp.get_fluxes(output_mon)))
    input_flux = np.abs(np.array(mp.get_fluxes(input_mon)))

    # Gain = output / input
    gain = output_flux / (input_flux + 1e-20)

    # At center frequency
    center_idx = len(freqs) // 2
    gain_center = gain[center_idx]

    # Gain in dB
    if gain_center > 0:
        gain_dB = 10 * np.log10(gain_center)
    else:
        gain_dB = -100

    # Noise figure estimate (simplified)
    # NF = 2 * nsp where nsp is population inversion factor
    nsp = 1.5  # Typical value for SOA
    noise_figure_dB = 10 * np.log10(2 * nsp)

    print(f"\nResults at wavelength = {wavelength:.4f} um:")
    print(f"  Input flux:  {input_flux[center_idx]:.6e}")
    print(f"  Output flux: {output_flux[center_idx]:.6e}")
    print(f"  Linear Gain: {gain_center:.4f}x")
    print(f"  Gain (dB):   {gain_dB:.2f} dB")
    print(f"  Target:      {target_gain_dB:.1f} dB")
    print(f"  Estimated NF: {noise_figure_dB:.1f} dB")

    return {
        'wavelength': wavelength,
        'soa_length': soa_length,
        'target_gain_dB': target_gain_dB,
        'sigma_D': sigma_D,
        'frequencies': freqs,
        'wavelengths': wavelengths,
        'output_flux': output_flux,
        'input_flux': input_flux,
        'gain': gain,
        'gain_center': gain_center,
        'gain_dB': gain_dB,
        'noise_figure_dB': noise_figure_dB
    }


def run_gain_sweep(wavelength: float, target_gains_dB: list = None,
                   soa_length: float = 30.0):
    """
    Sweep target gain levels to characterize SOA.
    """
    if target_gains_dB is None:
        target_gains_dB = [5.0, 10.0, 15.0, 20.0, 25.0]

    print(f"\n=== GAIN LEVEL SWEEP at wavelength = {wavelength} um ===")

    results = []
    for g_dB in target_gains_dB:
        result = run_soa_simulation(wavelength, soa_length=soa_length,
                                     target_gain_dB=g_dB, resolution=20)
        results.append(result)

    return {
        'wavelength': wavelength,
        'target_gains_dB': target_gains_dB,
        'soa_length': soa_length,
        'results': results
    }


def run_switching_test(wavelength: float, soa_length: float = 30.0):
    """
    Test SOA switching by comparing ON (with gain) vs OFF (no gain) states.
    """
    print(f"\n=== SOA SWITCHING TEST at wavelength = {wavelength} um ===")

    # OFF state (no gain, sigma_D = 0)
    print("\n--- OFF State (no gain) ---")
    result_off = run_soa_simulation(wavelength, soa_length=soa_length,
                                     target_gain_dB=0.0, resolution=20)

    # ON state (with gain)
    print("\n--- ON State (with gain) ---")
    result_on = run_soa_simulation(wavelength, soa_length=soa_length,
                                    target_gain_dB=20.0, resolution=20)

    extinction_ratio = result_on['gain_center'] / (result_off['gain_center'] + 1e-20)
    extinction_dB = 10 * np.log10(extinction_ratio) if extinction_ratio > 0 else 0

    print(f"\nSwitching Results:")
    print(f"  OFF transmission: {result_off['gain_center']:.4f} ({result_off['gain_dB']:.2f} dB)")
    print(f"  ON gain: {result_on['gain_center']:.4f} ({result_on['gain_dB']:.2f} dB)")
    print(f"  Extinction ratio: {extinction_dB:.1f} dB")

    return {
        'wavelength': wavelength,
        'soa_length': soa_length,
        'off_result': result_off,
        'on_result': result_on,
        'extinction_ratio': extinction_ratio,
        'extinction_dB': extinction_dB
    }


def save_results(result: dict, output_dir: str):
    """Save SOA simulation results."""
    os.makedirs(output_dir, exist_ok=True)

    if 'target_gains_dB' in result:
        # Gain sweep
        wvl_nm = int(result['wavelength'] * 1000)

        csv_path = os.path.join(output_dir, f"soa_gain_sweep_{wvl_nm}nm.csv")
        header = "Target Gain (dB),D_conductivity,Measured Gain (linear),Measured Gain (dB)"
        data = [[r['target_gain_dB'], r['sigma_D'], r['gain_center'], r['gain_dB']]
                for r in result['results']]
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))

        target_dB = [r['target_gain_dB'] for r in result['results']]
        measured_dB = [r['gain_dB'] for r in result['results']]

        ax.plot(target_dB, measured_dB, 'b-o', linewidth=2, markersize=8, label='Measured')
        ax.plot(target_dB, target_dB, 'g--', linewidth=1, alpha=0.7, label='Ideal')
        ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax.set_xlabel('Target Gain (dB)', fontsize=12)
        ax.set_ylabel('Measured Gain (dB)', fontsize=12)
        ax.set_title(f'SOA Gain Calibration (L = {result["soa_length"]} um, wavelength = {result["wavelength"]} um)',
                     fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"soa_gain_sweep_{wvl_nm}nm.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()

    elif 'extinction_dB' in result:
        # Switching test
        wvl_nm = int(result['wavelength'] * 1000)

        csv_path = os.path.join(output_dir, f"soa_switching_{wvl_nm}nm.csv")
        with open(csv_path, 'w') as f:
            f.write("State,Target Gain (dB),Measured Gain (linear),Measured Gain (dB)\n")
            f.write(f"OFF,0,{result['off_result']['gain_center']:.6f},{result['off_result']['gain_dB']:.2f}\n")
            f.write(f"ON,20,{result['on_result']['gain_center']:.6f},{result['on_result']['gain_dB']:.2f}\n")
            f.write(f"Extinction Ratio (dB),{result['extinction_dB']:.2f},\n")
        print(f"Saved: {csv_path}")

        # Plot comparison
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(result['off_result']['wavelengths'], result['off_result']['gain'],
                'b--', linewidth=2, label='OFF (no gain)')
        ax.plot(result['on_result']['wavelengths'], result['on_result']['gain'],
                'r-', linewidth=2, label='ON (with gain)')
        ax.axvline(x=result['wavelength'], color='green', linestyle=':', alpha=0.7)
        ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5, label='Unity gain')

        ax.set_xlabel('Wavelength (um)', fontsize=12)
        ax.set_ylabel('Gain', fontsize=12)
        ax.set_title(f'SOA Switching (wavelength = {result["wavelength"]} um)\n'
                     f'Extinction: {result["extinction_dB"]:.1f} dB', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"soa_switching_{wvl_nm}nm.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()

    else:
        # Single simulation
        wvl_nm = int(result['wavelength'] * 1000)

        csv_path = os.path.join(output_dir, f"soa_{wvl_nm}nm.csv")
        header = "Frequency (Meep),Wavelength (um),Output Flux,Input Flux,Gain"
        data = np.column_stack((
            result['frequencies'], result['wavelengths'],
            result['output_flux'], result['input_flux'], result['gain']
        ))
        np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
        print(f"Saved: {csv_path}")

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(result['wavelengths'], result['gain'], 'b-', linewidth=2)
        ax.axvline(x=result['wavelength'], color='green', linestyle=':')
        ax.axhline(y=1, color='gray', linestyle='--', alpha=0.5)

        ax.set_xlabel('Wavelength (um)', fontsize=12)
        ax.set_ylabel('Gain', fontsize=12)
        ax.set_title(f'SOA Gain Spectrum\nMeasured: {result["gain_dB"]:.1f} dB (target: {result["target_gain_dB"]:.1f} dB)',
                     fontsize=12)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, f"soa_{wvl_nm}nm.png")
        plt.savefig(plot_path, dpi=300)
        print(f"Saved: {plot_path}")
        plt.close()


def main():
    parser = argparse.ArgumentParser(description='SOA Gate Meep FDTD Simulation (Refined)')
    parser.add_argument('--wavelength', type=float, default=1.55, help='Wavelength (um)')
    parser.add_argument('--length', type=float, default=30.0, help='SOA length (um)')
    parser.add_argument('--target-gain', type=float, default=20.0, help='Target gain in dB')
    parser.add_argument('--sweep-gain', action='store_true', help='Sweep gain levels')
    parser.add_argument('--switching', action='store_true', help='Test ON/OFF switching')
    parser.add_argument('--all-wavelengths', action='store_true', help='Test all ternary wavelengths')
    parser.add_argument('--resolution', type=int, default=20, help='FDTD resolution')
    parser.add_argument('--output', type=str, default=None, help='Output directory')

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = args.output or os.path.join(base_dir, 'data', 'csv')

    print("=" * 60)
    print("  SOA GATE - Meep FDTD Simulation (REFINED)")
    print("  Semiconductor Optical Amplifier for Tier 2 RAM")
    print("  Corrected gain modeling with D_conductivity < 0")
    print("=" * 60)

    if args.sweep_gain:
        result = run_gain_sweep(args.wavelength, soa_length=args.length)
        save_results(result, output_dir)

    elif args.switching:
        result = run_switching_test(args.wavelength, soa_length=args.length)
        save_results(result, output_dir)

    elif args.all_wavelengths:
        for name, wvl in WAVELENGTHS.items():
            print(f"\n{'='*50}")
            print(f"  Testing {name}: {wvl} um")
            print('='*50)
            result = run_soa_simulation(wvl, args.length, args.target_gain, args.resolution)
            save_results(result, output_dir)

    else:
        result = run_soa_simulation(args.wavelength, args.length, args.target_gain,
                                     args.resolution)
        save_results(result, output_dir)

    print("\n" + "=" * 60)
    print("  SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
