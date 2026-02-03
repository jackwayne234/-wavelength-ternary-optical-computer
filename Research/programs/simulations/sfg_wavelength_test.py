#!/usr/bin/env python3
"""
SFG Wavelength Triplet Test

Tests the recommended wavelength triplet for ternary optical computing:
- RED (-1):   1550 nm (C-band telecom)
- GREEN (0):  1310 nm (O-band telecom)
- BLUE (+1):  1064 nm (Nd:YAG standard)

This triplet avoids the output collision problem where GREEN+GREEN and RED+BLUE
produced identical 608nm outputs with the old wavelengths.

Usage:
    python sfg_wavelength_test.py                    # Run all 6 combinations
    python sfg_wavelength_test.py --combo RED_GREEN  # Run single combination
    python sfg_wavelength_test.py --old-wavelengths  # Compare with old wavelengths
"""

import os
import sys
import argparse
import meep as mp
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# NEW RECOMMENDED WAVELENGTHS (all outputs distinguishable)
NEW_WAVELENGTHS = {
    'RED': 1.550,    # C-band telecom
    'GREEN': 1.310,  # O-band telecom
    'BLUE': 1.064    # Nd:YAG standard
}

# OLD WAVELENGTHS (for comparison - has collision at 608nm)
OLD_WAVELENGTHS = {
    'RED': 1.550,
    'GREEN': 1.216,
    'BLUE': 1.000
}

# All 6 ternary combinations
COMBINATIONS = [
    ('RED', 'RED'),
    ('RED', 'GREEN'),
    ('RED', 'BLUE'),
    ('GREEN', 'GREEN'),
    ('GREEN', 'BLUE'),
    ('BLUE', 'BLUE')
]


def run_sfg_test(wvl1: float, wvl2: float, label1: str, label2: str,
                 resolution: int = 25) -> dict:
    """
    Run SFG simulation for a wavelength pair.

    Returns dict with frequencies, flux, efficiency metrics.
    """
    print(f"\n{'='*60}")
    print(f"SFG TEST: {label1} ({wvl1} μm) + {label2} ({wvl2} μm)")
    print(f"{'='*60}")

    freq1 = 1.0 / wvl1
    freq2 = 1.0 / wvl2
    freq_sum = freq1 + freq2
    wvl_sum = 1.0 / freq_sum

    print(f"Target SFG output: {wvl_sum*1000:.1f} nm (freq: {freq_sum:.4f})")

    # Geometry
    cell_x = 18
    cell_y = 5
    pml_thickness = 1.0
    wg_width = 1.1  # Optimized from previous work

    # LiNbO3 material
    n_linbo3 = 2.2
    chi2_val = 0.5

    cell_size = mp.Vector3(cell_x, cell_y, 0)
    material = mp.Medium(index=n_linbo3, chi2=chi2_val)

    geometry = [
        mp.Block(
            mp.Vector3(mp.inf, wg_width, mp.inf),
            center=mp.Vector3(),
            material=material
        )
    ]

    sources = [
        mp.Source(
            mp.GaussianSource(freq1, fwidth=0.05*freq1),
            component=mp.Ez,
            center=mp.Vector3(-0.5 * cell_x + pml_thickness + 0.5, 0),
            size=mp.Vector3(0, wg_width, 0)
        ),
        mp.Source(
            mp.GaussianSource(freq2, fwidth=0.05*freq2),
            component=mp.Ez,
            center=mp.Vector3(-0.5 * cell_x + pml_thickness + 0.5, 0),
            size=mp.Vector3(0, wg_width, 0)
        )
    ]

    sim = mp.Simulation(
        cell_size=cell_size,
        boundary_layers=[mp.PML(pml_thickness)],
        geometry=geometry,
        sources=sources,
        resolution=resolution
    )

    # Flux monitor covering input freqs to SFG output
    f_min = min(freq1, freq2) * 0.8
    f_max = freq_sum * 1.2
    fcen_mon = (f_min + f_max) / 2
    df_mon = (f_max - f_min)

    trans = sim.add_flux(
        fcen_mon, df_mon, 600,
        mp.FluxRegion(
            center=mp.Vector3(0.5 * cell_x - pml_thickness - 0.5, 0),
            size=mp.Vector3(0, 2*wg_width, 0)
        )
    )

    print("Running FDTD simulation...")
    sim.run(until_after_sources=mp.stop_when_fields_decayed(
        50, mp.Ez, mp.Vector3(0, 0, 0), 1e-4
    ))

    freqs = np.array(mp.get_flux_freqs(trans))
    flux = np.array(mp.get_fluxes(trans))
    wvls = 1.0 / freqs

    # Find SFG peak
    idx_sum = np.argmin(np.abs(freqs - freq_sum))
    flux_sum = flux[idx_sum]

    # Find input peaks for efficiency calc
    idx_1 = np.argmin(np.abs(freqs - freq1))
    idx_2 = np.argmin(np.abs(freqs - freq2))
    flux_in_total = flux[idx_1] + flux[idx_2]

    efficiency = (flux_sum / flux_in_total) * 100 if flux_in_total > 0 else 0

    print(f"\nResults:")
    print(f"  SFG output wavelength: {wvl_sum*1000:.1f} nm")
    print(f"  SFG flux: {flux_sum:.4e}")
    print(f"  Conversion efficiency: {efficiency:.2f}%")

    return {
        'label1': label1,
        'label2': label2,
        'wvl1': wvl1,
        'wvl2': wvl2,
        'wvl_sum': wvl_sum,
        'wvl_sum_nm': wvl_sum * 1000,
        'freqs': freqs,
        'flux': flux,
        'flux_sum': flux_sum,
        'efficiency': efficiency
    }


def run_all_combinations(wavelengths: dict, output_dir: str) -> list:
    """Run all 6 ternary combinations and save results."""

    results = []

    for c1, c2 in COMBINATIONS:
        wvl1 = wavelengths[c1]
        wvl2 = wavelengths[c2]
        label = f"{c1}_{c2}"

        result = run_sfg_test(wvl1, wvl2, c1, c2)
        result['combo'] = label
        results.append(result)

    # Summary table
    print("\n" + "="*70)
    print("SUMMARY: ALL 6 TERNARY COMBINATIONS")
    print("="*70)
    print(f"{'Combination':<15} {'Input 1':<10} {'Input 2':<10} {'Output':<12} {'Efficiency':<12}")
    print("-"*70)

    # Sort by output wavelength for collision check
    results_sorted = sorted(results, key=lambda x: x['wvl_sum_nm'])

    prev_wvl = 0
    for r in results_sorted:
        spacing = r['wvl_sum_nm'] - prev_wvl if prev_wvl > 0 else 0
        collision = " ⚠️ COLLISION!" if spacing < 5 and prev_wvl > 0 else ""
        print(f"{r['combo']:<15} {r['wvl1']*1000:.0f} nm    {r['wvl2']*1000:.0f} nm    "
              f"{r['wvl_sum_nm']:.1f} nm    {r['efficiency']:.2f}%{collision}")
        prev_wvl = r['wvl_sum_nm']

    print("="*70)

    # Check distinguishability
    output_wvls = [r['wvl_sum_nm'] for r in results_sorted]
    spacings = [output_wvls[i+1] - output_wvls[i] for i in range(len(output_wvls)-1)]
    min_spacing = min(spacings)

    print(f"\nMinimum output spacing: {min_spacing:.1f} nm")
    if min_spacing >= 10:
        print("✓ PASS: All outputs distinguishable (>10nm spacing)")
    elif min_spacing >= 5:
        print("⚠ WARNING: Tight spacing - may need high-res filters")
    else:
        print("✗ FAIL: Outputs too close or colliding!")

    # Save results
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(output_dir, f'sfg_wavelength_test_{timestamp}.csv')

    with open(csv_path, 'w') as f:
        f.write("Combination,Input1_nm,Input2_nm,Output_nm,Flux_SFG,Efficiency_%\n")
        for r in results:
            f.write(f"{r['combo']},{r['wvl1']*1000:.1f},{r['wvl2']*1000:.1f},"
                    f"{r['wvl_sum_nm']:.1f},{r['flux_sum']:.6e},{r['efficiency']:.4f}\n")

    print(f"\nResults saved to: {csv_path}")

    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Bar chart of efficiencies
    combos = [r['combo'] for r in results]
    effs = [r['efficiency'] for r in results]
    colors = ['red' if 'RED' in c and 'RED' in c.split('_')[1] else
              'green' if 'GREEN' in c and 'GREEN' in c.split('_')[1] else
              'blue' if 'BLUE' in c and 'BLUE' in c.split('_')[1] else
              'purple' for c in combos]

    ax1.bar(combos, effs, color=colors, alpha=0.7, edgecolor='black')
    ax1.set_ylabel('Conversion Efficiency (%)')
    ax1.set_title('SFG Efficiency by Combination')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(axis='y', alpha=0.3)

    # Output wavelength diagram
    for i, r in enumerate(results_sorted):
        ax2.barh(i, 50, left=r['wvl_sum_nm']-25, height=0.6,
                color=plt.cm.rainbow(r['wvl_sum_nm']/800), alpha=0.8,
                edgecolor='black')
        ax2.text(r['wvl_sum_nm'], i, f"{r['wvl_sum_nm']:.0f}nm\n{r['combo']}",
                ha='center', va='center', fontsize=8)

    ax2.set_xlabel('Wavelength (nm)')
    ax2.set_title('Output Wavelength Distribution')
    ax2.set_yticks([])
    ax2.set_xlim(450, 850)
    ax2.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, f'sfg_wavelength_test_{timestamp}.png')
    plt.savefig(plot_path, dpi=150)
    print(f"Plot saved to: {plot_path}")
    plt.close()

    return results


def main():
    parser = argparse.ArgumentParser(description='SFG Wavelength Triplet Test')
    parser.add_argument('--combo', type=str, default=None,
                        help='Single combination to test (e.g., RED_GREEN)')
    parser.add_argument('--old-wavelengths', action='store_true',
                        help='Use old wavelengths for comparison')
    parser.add_argument('--resolution', type=int, default=25,
                        help='FDTD resolution (default: 25)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output directory')

    args = parser.parse_args()

    # Select wavelength set
    if args.old_wavelengths:
        wavelengths = OLD_WAVELENGTHS
        wvl_label = "OLD"
        print("\n⚠️  Using OLD wavelengths (has 608nm collision!)")
    else:
        wavelengths = NEW_WAVELENGTHS
        wvl_label = "NEW"
        print("\n✓ Using NEW recommended wavelengths")

    print(f"  RED:   {wavelengths['RED']*1000:.0f} nm")
    print(f"  GREEN: {wavelengths['GREEN']*1000:.0f} nm")
    print(f"  BLUE:  {wavelengths['BLUE']*1000:.0f} nm")

    # Output directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = args.output or os.path.join(base_dir, 'data', 'csv')

    if args.combo:
        # Single combination
        parts = args.combo.upper().split('_')
        if len(parts) != 2 or parts[0] not in wavelengths or parts[1] not in wavelengths:
            print(f"Invalid combination: {args.combo}")
            print("Valid: RED_RED, RED_GREEN, RED_BLUE, GREEN_GREEN, GREEN_BLUE, BLUE_BLUE")
            sys.exit(1)

        c1, c2 = parts
        result = run_sfg_test(wavelengths[c1], wavelengths[c2], c1, c2, args.resolution)
    else:
        # All combinations
        results = run_all_combinations(wavelengths, output_dir)

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
