# Copyright (c) 2026 Christopher Riner
# Licensed under the MIT License. See LICENSE file for details.
#
# Wavelength-Division Ternary Optical Computer
# https://github.com/jackwayne234/-wavelength-ternary-optical-computer
#
# Simulation comparing SFG in different materials:
# - LiNbO3 (baseline)
# - Poled polymer (DR1-doped PMMA)
# - KDP crystal
#
# Purpose: Evaluate DIY-accessible materials for Phase 4

import os
import sys
import meep as mp
import numpy as np
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Material database for DIY-accessible nonlinear optical materials
MATERIALS = {
    'LiNbO3': {
        'name': 'Lithium Niobate',
        'n': 2.2,
        'chi2': 30.0,  # pm/V (d33 coefficient)
        'diy_feasible': False,
        'notes': 'Requires HF etching - baseline comparison'
    },
    'DR1_PMMA': {
        'name': 'Disperse Red 1 in PMMA (poled)',
        'n': 1.50,
        'chi2': 35.0,  # pm/V - achieved in literature
        'diy_feasible': True,
        'notes': 'Requires high-voltage poling apparatus'
    },
    'DR1_SU8': {
        'name': 'Disperse Red 1 in SU-8 (poled)',
        'n': 1.55,
        'chi2': 30.0,  # pm/V - estimated
        'diy_feasible': True,
        'notes': 'Combines lithography resist with NLO dopant'
    },
    'KDP': {
        'name': 'Potassium Dihydrogen Phosphate',
        'n': 1.51,
        'chi2': 0.39,  # pm/V - much lower!
        'diy_feasible': True,
        'notes': 'Grown from aqueous solution - low chi2 needs long waveguide'
    },
    'DAST': {
        'name': 'DAST organic crystal',
        'n': 2.1,
        'chi2': 290.0,  # pm/V - very high!
        'diy_feasible': False,  # Hard to grow quality crystals
        'notes': 'Highest known organic chi2, but fragile and hard to grow'
    }
}


def run_sfg_simulation(material_key: str, waveguide_length_um: float = 20.0):
    """
    Simulates Sum Frequency Generation for a given material.

    Args:
        material_key: Key from MATERIALS dict
        waveguide_length_um: Length of the nonlinear waveguide section

    Returns:
        dict with frequencies, flux spectrum, and metadata
    """
    mat = MATERIALS[material_key]
    print(f"\n{'='*60}")
    print(f"Simulating SFG in: {mat['name']}")
    print(f"  n = {mat['n']}, chi2 = {mat['chi2']} pm/V")
    print(f"  Waveguide length: {waveguide_length_um} um")
    print(f"  DIY Feasible: {mat['diy_feasible']}")
    print(f"{'='*60}")

    # Simulation parameters
    resolution = 20  # pixels/um

    # Scale chi2 for Meep (normalized units)
    # Meep chi2 is in different units - we scale relative to LiNbO3 baseline
    chi2_normalized = mat['chi2'] / 30.0 * 0.5  # 0.5 was the LiNbO3 value in original

    # Geometry
    cell_x = waveguide_length_um + 4  # Add space for PML and sources
    cell_y = 6
    pml_thickness = 1.0

    # Waveguide width scales with refractive index for single-mode
    # Higher n = narrower waveguide for same confinement
    wg_width = 0.8 * (2.2 / mat['n'])  # Scale from LiNbO3 baseline
    wg_width = max(0.5, min(2.0, wg_width))  # Clamp to reasonable range

    # Source wavelengths (same as original)
    wvl_a = 1.55  # Telecom
    wvl_b = 1.0   # ~1um
    freq_a = 1 / wvl_a
    freq_b = 1 / wvl_b
    freq_sum = freq_a + freq_b

    df = 0.1 * freq_a  # Pulse bandwidth

    # Build simulation
    cell_size = mp.Vector3(cell_x, cell_y, 0)

    material = mp.Medium(index=mat['n'], chi2=chi2_normalized)

    geometry = [
        mp.Block(
            mp.Vector3(mp.inf, wg_width, mp.inf),
            center=mp.Vector3(),
            material=material
        )
    ]

    sources = [
        mp.Source(
            mp.GaussianSource(freq_a, fwidth=df),
            component=mp.Ez,
            center=mp.Vector3(-0.5 * cell_x + pml_thickness + 0.5, 0),
            size=mp.Vector3(0, wg_width, 0)
        ),
        mp.Source(
            mp.GaussianSource(freq_b, fwidth=df),
            component=mp.Ez,
            center=mp.Vector3(-0.5 * cell_x + pml_thickness + 0.5, 0),
            size=mp.Vector3(0, wg_width, 0)
        )
    ]

    pml_layers = [mp.PML(pml_thickness)]

    sim = mp.Simulation(
        cell_size=cell_size,
        boundary_layers=pml_layers,
        geometry=geometry,
        sources=sources,
        resolution=resolution
    )

    # Flux monitor
    nfreq = 500
    fcen_mon = (freq_sum + freq_a) / 2
    df_mon = freq_sum

    trans = sim.add_flux(
        fcen_mon, df_mon, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(0.5 * cell_x - pml_thickness - 0.5, 0),
            size=mp.Vector3(0, 2 * wg_width, 0)
        )
    )

    # Run
    print("Running simulation...")
    sim.run(until_after_sources=mp.stop_when_fields_decayed(
        50, mp.Ez,
        mp.Vector3(0.5 * cell_x - pml_thickness - 0.5, 0),
        1e-4
    ))

    freqs = np.array(mp.get_flux_freqs(trans))
    flux = np.array(mp.get_fluxes(trans))

    # Find SFG peak
    sum_freq_idx = np.argmin(np.abs(freqs - freq_sum))
    sfg_flux = flux[sum_freq_idx] if sum_freq_idx < len(flux) else 0

    # Find fundamental peaks for reference
    freq_a_idx = np.argmin(np.abs(freqs - freq_a))
    freq_b_idx = np.argmin(np.abs(freqs - freq_b))

    print(f"SFG signal at {freq_sum:.3f}: {sfg_flux:.2e}")

    return {
        'material': material_key,
        'freqs': freqs,
        'flux': flux,
        'freq_a': freq_a,
        'freq_b': freq_b,
        'freq_sum': freq_sum,
        'sfg_flux': sfg_flux,
        'chi2': mat['chi2'],
        'diy_feasible': mat['diy_feasible']
    }


def compare_materials(materials_to_test=None, waveguide_length_um=20.0):
    """
    Run SFG simulations for multiple materials and compare.

    Args:
        materials_to_test: List of material keys, or None for all
        waveguide_length_um: Waveguide length for all tests
    """
    if materials_to_test is None:
        materials_to_test = list(MATERIALS.keys())

    results = []
    for mat_key in materials_to_test:
        result = run_sfg_simulation(mat_key, waveguide_length_um)
        results.append(result)

    # Plot comparison
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))

    # Subplot 1: Full spectra
    ax1 = axes[0]
    for r in results:
        label = f"{r['material']} (chi2={r['chi2']:.1f})"
        if r['diy_feasible']:
            label += " [DIY]"
        ax1.plot(r['freqs'], r['flux'], label=label, alpha=0.7)

    # Mark expected frequencies
    ax1.axvline(x=results[0]['freq_a'], color='gray', linestyle=':', alpha=0.5)
    ax1.axvline(x=results[0]['freq_b'], color='gray', linestyle=':', alpha=0.5)
    ax1.axvline(x=results[0]['freq_sum'], color='red', linestyle='--',
                label=f"SFG target ({results[0]['freq_sum']:.2f})")

    ax1.set_xlabel("Frequency (Meep units)")
    ax1.set_ylabel("Flux (a.u.)")
    ax1.set_title(f"SFG Spectrum Comparison (L={waveguide_length_um}um)")
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)

    # Subplot 2: SFG efficiency bar chart
    ax2 = axes[1]
    mat_names = [r['material'] for r in results]
    sfg_values = [r['sfg_flux'] for r in results]
    colors = ['green' if r['diy_feasible'] else 'blue' for r in results]

    bars = ax2.bar(mat_names, sfg_values, color=colors, alpha=0.7)
    ax2.set_ylabel("SFG Flux at Sum Frequency")
    ax2.set_title("SFG Efficiency by Material (Green = DIY Feasible)")
    ax2.tick_params(axis='x', rotation=45)

    # Add chi2 values on bars
    for bar, r in zip(bars, results):
        height = bar.get_height()
        ax2.annotate(f'chi2={r["chi2"]}',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3),
                     textcoords="offset points",
                     ha='center', va='bottom', fontsize=8)

    plt.tight_layout()

    # Save plot
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    plot_path = os.path.join(data_dir, "polymer_sfg_comparison.png")
    plt.savefig(plot_path, dpi=150)
    print(f"\nComparison plot saved to: {plot_path}")

    # Print summary table
    print("\n" + "="*70)
    print("SUMMARY: SFG EFFICIENCY BY MATERIAL")
    print("="*70)
    print(f"{'Material':<20} {'chi2 (pm/V)':<12} {'SFG Flux':<15} {'DIY?':<8}")
    print("-"*70)

    # Sort by SFG flux
    results_sorted = sorted(results, key=lambda x: x['sfg_flux'], reverse=True)
    for r in results_sorted:
        diy_str = "YES" if r['diy_feasible'] else "no"
        print(f"{r['material']:<20} {r['chi2']:<12.1f} {r['sfg_flux']:<15.2e} {diy_str:<8}")

    print("="*70)

    return results


def test_kdp_length_scaling():
    """
    KDP has low chi2, so test if longer waveguides compensate.
    SFG efficiency scales as L^2 * chi2^2 (in ideal phase-matched case).
    """
    print("\n" + "="*60)
    print("Testing KDP with varying waveguide lengths")
    print("(Low chi2 may be compensated by longer interaction length)")
    print("="*60)

    lengths = [20, 50, 100, 200]  # um
    results = []

    for L in lengths:
        result = run_sfg_simulation('KDP', waveguide_length_um=L)
        result['length'] = L
        results.append(result)

    # Compare to LiNbO3 at 20um
    linbo3_baseline = run_sfg_simulation('LiNbO3', waveguide_length_um=20)

    # Plot
    plt.figure(figsize=(10, 6))
    lengths_arr = [r['length'] for r in results]
    sfg_arr = [r['sfg_flux'] for r in results]

    plt.plot(lengths_arr, sfg_arr, 'bo-', label='KDP', markersize=10)
    plt.axhline(y=linbo3_baseline['sfg_flux'], color='r', linestyle='--',
                label=f'LiNbO3 @ 20um (baseline)')

    plt.xlabel("Waveguide Length (um)")
    plt.ylabel("SFG Flux")
    plt.title("KDP SFG vs Waveguide Length (Can length compensate for low chi2?)")
    plt.legend()
    plt.grid(True, alpha=0.3)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plot_path = os.path.join(base_dir, 'data', "kdp_length_scaling.png")
    plt.savefig(plot_path, dpi=150)
    print(f"\nKDP scaling plot saved to: {plot_path}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Compare SFG in different materials')
    parser.add_argument('--materials', nargs='+', default=None,
                        help='Materials to test (default: all)')
    parser.add_argument('--length', type=float, default=20.0,
                        help='Waveguide length in um (default: 20)')
    parser.add_argument('--kdp-scaling', action='store_true',
                        help='Run KDP length scaling test')
    args = parser.parse_args()

    if args.kdp_scaling:
        test_kdp_length_scaling()
    else:
        compare_materials(args.materials, args.length)
