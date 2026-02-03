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
Saturable Absorber Parameter Optimization

This module performs a parameter sweep to find optimal saturable absorber
(log converter) parameters for the ternary optical computer.

Optimization targets:
    1. R-squared fit to ideal ln() curve (target: >0.95)
    2. Dynamic range in dB (target: >20 dB)
    3. Minimum insertion loss at nominal intensity

Parameters swept:
    - I_sat: Saturation intensity (0.1 - 10.0 relative units)
    - Length: Absorber length (20 - 100 um)
    - alpha_0: Base absorption coefficient (1.0 - 10.0 /um)
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from itertools import product

# Ensure we can import local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Base directory for data output
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PNG_DIR = os.path.join(DATA_DIR, 'png')
CSV_DIR = os.path.join(DATA_DIR, 'csv')

# Ensure directories exist
os.makedirs(PNG_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)


def saturable_absorber_model(
    input_powers: np.ndarray,
    i_sat: float,
    length_um: float,
    alpha_0: float
) -> np.ndarray:
    """
    Analytical model of saturable absorber transfer function.

    The saturable absorber has an intensity-dependent absorption:
        alpha(I) = alpha_0 / (1 + I/I_sat)

    For a waveguide of length L, the output intensity is:
        I_out = I_in * exp(-alpha_eff * L)

    where alpha_eff depends on the integrated absorption along the length.

    For deep saturation, this approaches logarithmic behavior:
        I_out ≈ I_sat * ln(1 + I_in/I_sat)

    Args:
        input_powers: Array of input intensities
        i_sat: Saturation intensity
        length_um: Absorber length in microns
        alpha_0: Unsaturated absorption coefficient (1/um)

    Returns:
        Array of output intensities
    """
    # Effective absorption decreases with intensity
    alpha_eff = alpha_0 / (1 + input_powers / i_sat)

    # Transmission through absorber
    transmission = np.exp(-alpha_eff * length_um)

    # Output power
    output_powers = input_powers * transmission

    return output_powers


def ideal_log_curve(x: np.ndarray, scale: float = 1.0) -> np.ndarray:
    """Ideal logarithmic transfer function: y = scale * ln(1 + x)"""
    return scale * np.log(1 + x)


def fit_to_log_curve(
    input_powers: np.ndarray,
    output_powers: np.ndarray
) -> float:
    """
    Fits the transfer data to an ideal log curve and returns R-squared.

    Args:
        input_powers: Input intensity array
        output_powers: Output intensity array

    Returns:
        R-squared value (0 to 1, higher is better)
    """
    def log_func(x, a, b):
        return a * np.log(1 + b * x)

    try:
        # Normalize inputs for fitting stability
        x_norm = input_powers / np.max(input_powers)
        y_norm = output_powers / np.max(output_powers) if np.max(output_powers) > 0 else output_powers

        popt, _ = curve_fit(log_func, x_norm, y_norm, p0=[1.0, 1.0], maxfev=5000)

        # Calculate R-squared
        y_fit = log_func(x_norm, *popt)
        ss_res = np.sum((y_norm - y_fit)**2)
        ss_tot = np.sum((y_norm - np.mean(y_norm))**2)

        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        return max(0.0, min(1.0, r_squared))  # Clamp to [0, 1]

    except Exception:
        return 0.0


def calculate_dynamic_range(
    input_powers: np.ndarray,
    output_powers: np.ndarray
) -> float:
    """
    Calculates the usable dynamic range in dB.

    Dynamic range = 10 * log10(max_output / min_output)

    For a good log converter, we want high dynamic range to distinguish
    between ternary values across a wide input range.

    Args:
        input_powers: Input intensity array
        output_powers: Output intensity array

    Returns:
        Dynamic range in dB
    """
    # Filter out zero/negative values
    valid = output_powers > 1e-10

    if np.sum(valid) < 2:
        return 0.0

    out_valid = output_powers[valid]
    max_out = np.max(out_valid)
    min_out = np.min(out_valid)

    if min_out <= 0:
        return 0.0

    dynamic_range_db = 10 * np.log10(max_out / min_out)
    return dynamic_range_db


def calculate_insertion_loss(
    input_powers: np.ndarray,
    output_powers: np.ndarray,
    nominal_idx: int = None
) -> float:
    """
    Calculates insertion loss at nominal operating intensity.

    Insertion loss (dB) = 10 * log10(P_in / P_out)

    We want low insertion loss to maintain signal strength through
    the log converter.

    Args:
        input_powers: Input intensity array
        output_powers: Output intensity array
        nominal_idx: Index of nominal operating point (default: middle)

    Returns:
        Insertion loss in dB at nominal intensity
    """
    if nominal_idx is None:
        nominal_idx = len(input_powers) // 2

    p_in = input_powers[nominal_idx]
    p_out = output_powers[nominal_idx]

    if p_out <= 0:
        return float('inf')

    insertion_loss_db = 10 * np.log10(p_in / p_out)
    return insertion_loss_db


def sweep_saturation_parameters(
    i_sat_range: tuple = (0.1, 10.0, 5),
    length_range: tuple = (20, 100, 5),
    alpha_range: tuple = (1.0, 10.0, 5),
    n_input_points: int = 50
) -> dict:
    """
    Performs a parameter sweep over saturable absorber parameters.

    Args:
        i_sat_range: (min, max, n_points) for saturation intensity
        length_range: (min, max, n_points) for absorber length in um
        alpha_range: (min, max, n_points) for base absorption coefficient
        n_input_points: Number of input power levels to simulate

    Returns:
        Dictionary containing sweep results and optimal parameters
    """
    print(f"\n{'='*70}")
    print("SATURABLE ABSORBER PARAMETER OPTIMIZATION")
    print("="*70)

    # Generate parameter arrays
    i_sat_values = np.linspace(i_sat_range[0], i_sat_range[1], i_sat_range[2])
    length_values = np.linspace(length_range[0], length_range[1], length_range[2])
    alpha_values = np.linspace(alpha_range[0], alpha_range[1], alpha_range[2])

    # Input power range (logarithmic)
    input_powers = np.logspace(-1, 2, n_input_points)

    print(f"\nParameter ranges:")
    print(f"  I_sat: {i_sat_range[0]} to {i_sat_range[1]} ({i_sat_range[2]} points)")
    print(f"  Length: {length_range[0]} to {length_range[1]} um ({length_range[2]} points)")
    print(f"  alpha_0: {alpha_range[0]} to {alpha_range[1]} /um ({alpha_range[2]} points)")
    print(f"  Total combinations: {len(i_sat_values) * len(length_values) * len(alpha_values)}")

    # Results storage
    results = []
    best_score = -float('inf')
    best_params = None

    total = len(i_sat_values) * len(length_values) * len(alpha_values)
    count = 0

    for i_sat, length, alpha_0 in product(i_sat_values, length_values, alpha_values):
        count += 1

        # Calculate transfer function
        output_powers = saturable_absorber_model(input_powers, i_sat, length, alpha_0)

        # Calculate metrics
        r_squared = fit_to_log_curve(input_powers, output_powers)
        dynamic_range = calculate_dynamic_range(input_powers, output_powers)
        insertion_loss = calculate_insertion_loss(input_powers, output_powers)

        # Composite score: prioritize R², then dynamic range, penalize high loss
        # Weights: R² (0.5), dynamic_range/40 (0.3), (10-loss)/10 (0.2)
        dr_normalized = min(dynamic_range / 40.0, 1.0)  # Normalize to ~1 at 40dB
        loss_penalty = max(0, (20 - insertion_loss) / 20.0)  # Penalty for loss > 20dB

        score = 0.5 * r_squared + 0.3 * dr_normalized + 0.2 * loss_penalty

        results.append({
            'i_sat': i_sat,
            'length': length,
            'alpha_0': alpha_0,
            'r_squared': r_squared,
            'dynamic_range_db': dynamic_range,
            'insertion_loss_db': insertion_loss,
            'score': score
        })

        if score > best_score:
            best_score = score
            best_params = {
                'i_sat': i_sat,
                'length': length,
                'alpha_0': alpha_0,
                'r_squared': r_squared,
                'dynamic_range_db': dynamic_range,
                'insertion_loss_db': insertion_loss,
                'score': score,
                'input_powers': input_powers,
                'output_powers': output_powers
            }

        if count % 25 == 0:
            print(f"  Progress: {count}/{total} ({100*count/total:.0f}%)")

    print(f"\n{'='*70}")
    print("OPTIMIZATION COMPLETE")
    print("="*70)
    print(f"\nBest parameters found:")
    print(f"  I_sat: {best_params['i_sat']:.2f}")
    print(f"  Length: {best_params['length']:.1f} um")
    print(f"  alpha_0: {best_params['alpha_0']:.2f} /um")
    print(f"\nPerformance metrics:")
    print(f"  R-squared: {best_params['r_squared']:.4f} (target: >0.95)")
    print(f"  Dynamic range: {best_params['dynamic_range_db']:.1f} dB (target: >20 dB)")
    print(f"  Insertion loss: {best_params['insertion_loss_db']:.1f} dB")
    print(f"  Composite score: {best_params['score']:.4f}")

    return {
        'all_results': results,
        'best_params': best_params,
        'i_sat_values': i_sat_values,
        'length_values': length_values,
        'alpha_values': alpha_values
    }


def plot_optimization_surface(results: dict):
    """
    Creates visualization of the optimization results.

    Generates:
    1. 2D heatmaps of score vs parameter pairs
    2. Best transfer function plot
    """
    print(f"\nGenerating optimization plots...")

    plt.style.use('default')
    plt.rcParams.update({
        'font.size': 11,
        'font.family': 'serif',
        'axes.linewidth': 1.5
    })

    all_results = results['all_results']
    best = results['best_params']

    # Convert to arrays for easier manipulation
    i_sat_arr = np.array([r['i_sat'] for r in all_results])
    length_arr = np.array([r['length'] for r in all_results])
    alpha_arr = np.array([r['alpha_0'] for r in all_results])
    score_arr = np.array([r['score'] for r in all_results])
    r2_arr = np.array([r['r_squared'] for r in all_results])
    dr_arr = np.array([r['dynamic_range_db'] for r in all_results])

    # ===== Figure 1: Multi-panel optimization surface =====
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Panel 1: Score vs I_sat and Length (averaged over alpha)
    ax1 = axes[0, 0]
    i_sat_unique = results['i_sat_values']
    length_unique = results['length_values']

    score_grid = np.zeros((len(length_unique), len(i_sat_unique)))
    for i, l in enumerate(length_unique):
        for j, isat in enumerate(i_sat_unique):
            mask = (length_arr == l) & (i_sat_arr == isat)
            if np.any(mask):
                score_grid[i, j] = np.mean(score_arr[mask])

    im1 = ax1.imshow(score_grid, aspect='auto', origin='lower',
                     extent=[i_sat_unique[0], i_sat_unique[-1],
                            length_unique[0], length_unique[-1]],
                     cmap='viridis')
    ax1.scatter([best['i_sat']], [best['length']], c='red', s=100,
               marker='*', edgecolors='white', linewidths=2, label='Optimum')
    ax1.set_xlabel('Saturation Intensity (I_sat)')
    ax1.set_ylabel('Length (μm)')
    ax1.set_title('Score vs I_sat & Length\n(averaged over α₀)')
    plt.colorbar(im1, ax=ax1, label='Score')
    ax1.legend()

    # Panel 2: Score vs Length and alpha (averaged over I_sat)
    ax2 = axes[0, 1]
    alpha_unique = results['alpha_values']

    score_grid2 = np.zeros((len(alpha_unique), len(length_unique)))
    for i, a in enumerate(alpha_unique):
        for j, l in enumerate(length_unique):
            mask = (alpha_arr == a) & (length_arr == l)
            if np.any(mask):
                score_grid2[i, j] = np.mean(score_arr[mask])

    im2 = ax2.imshow(score_grid2, aspect='auto', origin='lower',
                     extent=[length_unique[0], length_unique[-1],
                            alpha_unique[0], alpha_unique[-1]],
                     cmap='viridis')
    ax2.scatter([best['length']], [best['alpha_0']], c='red', s=100,
               marker='*', edgecolors='white', linewidths=2, label='Optimum')
    ax2.set_xlabel('Length (μm)')
    ax2.set_ylabel('Base Absorption α₀ (1/μm)')
    ax2.set_title('Score vs Length & α₀\n(averaged over I_sat)')
    plt.colorbar(im2, ax=ax2, label='Score')
    ax2.legend()

    # Panel 3: R-squared distribution
    ax3 = axes[1, 0]
    ax3.hist(r2_arr, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
    ax3.axvline(best['r_squared'], color='red', linestyle='--', linewidth=2,
               label=f"Best: {best['r_squared']:.3f}")
    ax3.axvline(0.95, color='green', linestyle=':', linewidth=2,
               label='Target: 0.95')
    ax3.set_xlabel('R-squared')
    ax3.set_ylabel('Count')
    ax3.set_title('R-squared Distribution')
    ax3.legend()

    # Panel 4: Dynamic range distribution
    ax4 = axes[1, 1]
    ax4.hist(dr_arr, bins=20, color='coral', edgecolor='black', alpha=0.7)
    ax4.axvline(best['dynamic_range_db'], color='red', linestyle='--', linewidth=2,
               label=f"Best: {best['dynamic_range_db']:.1f} dB")
    ax4.axvline(20, color='green', linestyle=':', linewidth=2,
               label='Target: 20 dB')
    ax4.set_xlabel('Dynamic Range (dB)')
    ax4.set_ylabel('Count')
    ax4.set_title('Dynamic Range Distribution')
    ax4.legend()

    plt.tight_layout()
    surface_path = os.path.join(PNG_DIR, 'log_optimization_surface.png')
    plt.savefig(surface_path, dpi=300)
    print(f"  Saved: {surface_path}")
    plt.close()

    # ===== Figure 2: Best transfer function =====
    fig2, ax = plt.subplots(figsize=(8, 6))

    input_powers = best['input_powers']
    output_powers = best['output_powers']

    # Simulated transfer
    ax.loglog(input_powers, output_powers, 'b-', linewidth=2.5,
             label='Optimized SA Transfer')

    # Ideal log curve (scaled)
    scale = np.max(output_powers) / np.log(1 + np.max(input_powers))
    ideal = scale * np.log(1 + input_powers)
    ax.loglog(input_powers, ideal, 'r--', linewidth=2, alpha=0.7,
             label='Ideal log(1+x)')

    # Linear reference
    linear_scale = output_powers[len(output_powers)//2] / input_powers[len(input_powers)//2]
    ax.loglog(input_powers, linear_scale * input_powers, 'g:', linewidth=2, alpha=0.5,
             label='Linear reference')

    ax.set_xlabel('Input Power (a.u.)', fontsize=14)
    ax.set_ylabel('Output Power (a.u.)', fontsize=14)
    ax.set_title(f'Optimized Saturable Absorber Transfer Function\n'
                f'I_sat={best["i_sat"]:.2f}, L={best["length"]:.0f}μm, '
                f'α₀={best["alpha_0"]:.2f}/μm\n'
                f'R²={best["r_squared"]:.3f}, DR={best["dynamic_range_db"]:.1f}dB',
                fontsize=12, fontweight='bold')
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, which='both', alpha=0.3)

    plt.tight_layout()
    transfer_path = os.path.join(PNG_DIR, 'log_optimized_transfer.png')
    plt.savefig(transfer_path, dpi=300)
    print(f"  Saved: {transfer_path}")
    plt.close()


def save_optimization_results(results: dict):
    """Saves optimization results to CSV."""
    csv_path = os.path.join(CSV_DIR, 'log_optimization_results.csv')

    header = "i_sat,length_um,alpha_0,r_squared,dynamic_range_db,insertion_loss_db,score"

    with open(csv_path, 'w') as f:
        f.write(header + '\n')
        for r in results['all_results']:
            row = f"{r['i_sat']},{r['length']},{r['alpha_0']},{r['r_squared']},"
            row += f"{r['dynamic_range_db']},{r['insertion_loss_db']},{r['score']}"
            f.write(row + '\n')

    print(f"  Saved: {csv_path}")


def main():
    """Run complete parameter optimization."""
    print("\n" + "="*70)
    print("SATURABLE ABSORBER PARAMETER OPTIMIZATION SUITE")
    print("Wavelength-Division Ternary Optical Computer")
    print("="*70)

    # Run parameter sweep
    results = sweep_saturation_parameters(
        i_sat_range=(0.5, 5.0, 6),      # Saturation intensity
        length_range=(20, 100, 6),       # Absorber length (um)
        alpha_range=(0.5, 5.0, 6),       # Base absorption (/um)
        n_input_points=30
    )

    # Generate plots
    plot_optimization_surface(results)

    # Save results
    save_optimization_results(results)

    # Print recommended parameters
    best = results['best_params']
    print("\n" + "="*70)
    print("RECOMMENDED PARAMETERS FOR TERNARY OPTICAL COMPUTER")
    print("="*70)
    print(f"\n  I_sat = {best['i_sat']:.2f} (relative units)")
    print(f"  Length = {best['length']:.0f} μm")
    print(f"  α₀ = {best['alpha_0']:.2f} /μm")
    print(f"\nExpected performance:")
    print(f"  - Logarithmic fit quality: R² = {best['r_squared']:.3f}")
    print(f"  - Dynamic range: {best['dynamic_range_db']:.1f} dB")
    print(f"  - Insertion loss: {best['insertion_loss_db']:.1f} dB at nominal")

    # Check against targets
    r2_ok = "PASS" if best['r_squared'] >= 0.95 else "FAIL"
    dr_ok = "PASS" if best['dynamic_range_db'] >= 20 else "FAIL"

    print(f"\nTarget checks:")
    print(f"  - R² > 0.95: {r2_ok} ({best['r_squared']:.3f})")
    print(f"  - DR > 20 dB: {dr_ok} ({best['dynamic_range_db']:.1f} dB)")

    return results


if __name__ == "__main__":
    main()
