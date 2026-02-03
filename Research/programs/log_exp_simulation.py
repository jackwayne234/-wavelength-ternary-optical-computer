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
FDTD Simulation for Log/Exp Converters

This module simulates the saturable absorber (log converter) and gain medium
(exp converter) using Meep FDTD. Since Meep doesn't natively support intensity-
dependent materials, we use parametric sweeps at multiple input powers.

Log Converter (Saturable Absorber):
    Physics: I_out = I_sat * ln(1 + I_in/I_sat)
    Implementation: Lossy material with absorption coefficient that we
    effectively model by running at different input powers and fitting.

Exp Converter (Gain Medium):
    Physics: I_out = I_in * exp(g*L)
    Implementation: Negative imaginary susceptibility for optical gain.
    Includes pump wavelength for population inversion.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import meep as mp

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


def run_log_converter_simulation(
    length_um: float = 50.0,
    i_sat_ratio: float = 1.0,
    input_powers: list = None,
    wavelength_um: float = 1.55,
    resolution: int = 20
) -> dict:
    """
    Simulates a saturable absorber (log converter) at multiple input powers.

    Since Meep doesn't support intensity-dependent materials directly, we
    model the saturable absorption by running multiple simulations with
    different absorption coefficients that correspond to the saturation
    behavior at each input power level.

    Saturable absorber transfer function:
        I_out = I_sat * ln(1 + I_in/I_sat)

    At low intensities (I_in << I_sat):
        I_out ≈ I_in  (linear regime)
    At high intensities (I_in >> I_sat):
        I_out ≈ I_sat * ln(I_in/I_sat)  (logarithmic compression)

    Args:
        length_um: Saturable absorber length in microns
        i_sat_ratio: Saturation intensity parameter (relative units)
        input_powers: List of input power levels to simulate (relative units)
        wavelength_um: Operating wavelength
        resolution: Meep resolution (pixels per micron)

    Returns:
        Dictionary with input_powers, output_powers, and fitted parameters
    """
    print(f"\n{'='*60}")
    print(f"LOG CONVERTER (SATURABLE ABSORBER) SIMULATION")
    print(f"{'='*60}")
    print(f"Length: {length_um} um")
    print(f"I_sat ratio: {i_sat_ratio}")
    print(f"Wavelength: {wavelength_um} um")

    if input_powers is None:
        # Logarithmically spaced input powers from 0.1 to 100 (relative units)
        input_powers = np.logspace(-1, 2, 20)

    freq = 1.0 / wavelength_um

    # Geometry dimensions
    cell_x = length_um + 4.0  # Add margin for PML
    cell_y = 4.0
    pml_thickness = 1.0
    wg_width = 0.5

    # Material: LiNbO3 base with saturable absorption
    # We model different saturation states by adjusting the loss
    n_core = 2.2
    base_alpha = 0.1  # Base absorption coefficient (1/um)

    output_powers = []

    for i, p_in in enumerate(input_powers):
        # Calculate effective absorption coefficient based on saturation
        # alpha_eff = alpha_0 / (1 + I/I_sat)
        # This models absorption bleaching at high intensities
        alpha_eff = base_alpha / (1.0 + p_in / i_sat_ratio)

        # Convert absorption to imaginary part of refractive index
        # alpha = 4*pi*k/lambda -> k = alpha*lambda/(4*pi)
        k_imag = alpha_eff * wavelength_um / (4.0 * np.pi)

        # Create lossy material
        material = mp.Medium(index=n_core, D_conductivity=2*np.pi*freq*k_imag/n_core)

        geometry = [
            mp.Block(
                mp.Vector3(length_um, wg_width, mp.inf),
                center=mp.Vector3(0, 0, 0),
                material=material
            )
        ]

        # Source amplitude scales with sqrt(input power)
        source_amp = np.sqrt(p_in)

        sources = [
            mp.Source(
                mp.ContinuousSource(frequency=freq),
                component=mp.Ez,
                center=mp.Vector3(-length_um/2 - 0.5, 0, 0),
                size=mp.Vector3(0, wg_width, 0),
                amplitude=source_amp
            )
        ]

        sim = mp.Simulation(
            cell_size=mp.Vector3(cell_x, cell_y, 0),
            boundary_layers=[mp.PML(pml_thickness)],
            geometry=geometry,
            sources=sources,
            resolution=resolution,
        )

        # Monitor at output
        output_point = mp.Vector3(length_um/2 + 0.5, 0, 0)

        # Run until steady state
        sim.run(until=50)

        # Get field amplitude at output
        ez_out = abs(sim.get_field_point(mp.Ez, output_point))
        p_out = ez_out**2  # Power proportional to |E|^2

        output_powers.append(p_out)

        if (i + 1) % 5 == 0:
            print(f"  Completed {i+1}/{len(input_powers)} power levels")

        sim.reset_meep()

    output_powers = np.array(output_powers)

    # Normalize to match expected log transfer function scale
    # Fit to I_out = A * ln(1 + B * I_in)
    from scipy.optimize import curve_fit

    def log_transfer(x, a, b):
        return a * np.log(1 + b * x)

    try:
        popt, _ = curve_fit(log_transfer, input_powers, output_powers,
                           p0=[1.0, 1.0], maxfev=5000)
        fit_a, fit_b = popt
        fitted_output = log_transfer(input_powers, fit_a, fit_b)
        r_squared = 1 - np.sum((output_powers - fitted_output)**2) / np.sum((output_powers - np.mean(output_powers))**2)
    except Exception as e:
        print(f"  Warning: Curve fitting failed: {e}")
        fit_a, fit_b = 1.0, 1.0
        r_squared = 0.0

    print(f"\nResults:")
    print(f"  Fitted parameters: A={fit_a:.4f}, B={fit_b:.4f}")
    print(f"  R-squared: {r_squared:.4f}")

    return {
        'input_powers': input_powers,
        'output_powers': output_powers,
        'fit_a': fit_a,
        'fit_b': fit_b,
        'r_squared': r_squared,
        'length_um': length_um,
        'i_sat_ratio': i_sat_ratio
    }


def run_exp_converter_simulation(
    length_um: float = 50.0,
    gain_coefficient: float = 0.05,
    wavelength_um: float = 1.55,
    pump_wavelength_um: float = 0.98,
    resolution: int = 20
) -> dict:
    """
    Simulates a gain medium (exp converter) using negative absorption.

    The gain medium provides exponential amplification:
        I_out = I_in * exp(g * L)

    We model this using Meep's ability to specify negative conductivity,
    which effectively creates optical gain.

    Args:
        length_um: Gain medium length in microns
        gain_coefficient: Gain per unit length (1/um)
        wavelength_um: Signal wavelength
        pump_wavelength_um: Pump wavelength for population inversion
        resolution: Meep resolution (pixels per micron)

    Returns:
        Dictionary with simulation results
    """
    print(f"\n{'='*60}")
    print(f"EXP CONVERTER (GAIN MEDIUM) SIMULATION")
    print(f"{'='*60}")
    print(f"Length: {length_um} um")
    print(f"Gain coefficient: {gain_coefficient} /um")
    print(f"Signal wavelength: {wavelength_um} um")
    print(f"Pump wavelength: {pump_wavelength_um} um")

    freq_signal = 1.0 / wavelength_um
    freq_pump = 1.0 / pump_wavelength_um

    # Geometry dimensions
    cell_x = length_um + 6.0
    cell_y = 5.0
    pml_thickness = 1.0
    wg_width = 0.5

    # Material: gain medium with negative loss (gain)
    # We use small gain to prevent instabilities
    n_core = 2.2

    # Negative conductivity creates gain
    # The gain should be modest to avoid runaway amplification
    # D_conductivity < 0 for gain
    gain_k = -gain_coefficient * wavelength_um / (4.0 * np.pi)
    d_cond = 2*np.pi*freq_signal*gain_k/n_core

    # Clamp gain to prevent instabilities
    d_cond = max(d_cond, -0.1)

    material_gain = mp.Medium(index=n_core, D_conductivity=d_cond)

    geometry = [
        mp.Block(
            mp.Vector3(length_um, wg_width, mp.inf),
            center=mp.Vector3(0, 0, 0),
            material=material_gain
        )
    ]

    # Signal source (what we want to amplify)
    sources = [
        mp.Source(
            mp.ContinuousSource(frequency=freq_signal),
            component=mp.Ez,
            center=mp.Vector3(-length_um/2 - 1.0, 0, 0),
            size=mp.Vector3(0, wg_width, 0),
            amplitude=1.0
        ),
        # Pump source (for population inversion visualization)
        mp.Source(
            mp.ContinuousSource(frequency=freq_pump),
            component=mp.Ez,
            center=mp.Vector3(-length_um/2 - 1.0, 0, 0),
            size=mp.Vector3(0, wg_width, 0),
            amplitude=0.5  # Weaker pump for visualization
        )
    ]

    sim = mp.Simulation(
        cell_size=mp.Vector3(cell_x, cell_y, 0),
        boundary_layers=[mp.PML(pml_thickness)],
        geometry=geometry,
        sources=sources,
        resolution=resolution,
    )

    # Monitor points along the waveguide
    n_monitors = 10
    monitor_positions = np.linspace(-length_um/2 + 2, length_um/2 - 2, n_monitors)
    monitor_points = [mp.Vector3(x, 0, 0) for x in monitor_positions]

    # Run simulation
    sim.run(until=80)

    # Get field amplitudes along the waveguide
    field_amplitudes = []
    for pt in monitor_points:
        ez = abs(sim.get_field_point(mp.Ez, pt))
        field_amplitudes.append(ez)

    field_amplitudes = np.array(field_amplitudes)
    powers = field_amplitudes**2

    # Fit to exponential: P = P0 * exp(g * x)
    # Take log: ln(P) = ln(P0) + g * x
    from scipy.stats import linregress

    # Normalize positions to start at 0
    x_normalized = monitor_positions - monitor_positions[0]

    # Avoid log(0) issues
    valid = powers > 1e-10
    if np.sum(valid) > 2:
        log_powers = np.log(powers[valid])
        x_valid = x_normalized[valid]
        slope, intercept, r_value, _, _ = linregress(x_valid, log_powers)
        measured_gain = slope
        r_squared = r_value**2
    else:
        measured_gain = 0.0
        r_squared = 0.0

    expected_gain = gain_coefficient
    gain_error = abs(measured_gain - expected_gain) / expected_gain * 100 if expected_gain != 0 else 0

    print(f"\nResults:")
    print(f"  Expected gain coefficient: {expected_gain:.4f} /um")
    print(f"  Measured gain coefficient: {measured_gain:.4f} /um")
    print(f"  Gain error: {gain_error:.1f}%")
    print(f"  R-squared (exp fit): {r_squared:.4f}")

    return {
        'positions': monitor_positions,
        'powers': powers,
        'field_amplitudes': field_amplitudes,
        'measured_gain': measured_gain,
        'expected_gain': expected_gain,
        'r_squared': r_squared,
        'length_um': length_um,
        'gain_coefficient': gain_coefficient
    }


def plot_transfer_functions(log_data: dict, exp_data: dict):
    """
    Creates publication-quality plots of the log and exp transfer functions.

    Args:
        log_data: Results from run_log_converter_simulation()
        exp_data: Results from run_exp_converter_simulation()
    """
    print(f"\n{'='*60}")
    print(f"GENERATING PLOTS")
    print(f"{'='*60}")

    # Style settings
    plt.style.use('default')
    plt.rcParams.update({
        'font.size': 12,
        'font.family': 'serif',
        'axes.linewidth': 1.5,
        'lines.linewidth': 2.0
    })

    # ===== LOG CONVERTER PLOT =====
    fig1, ax1 = plt.subplots(figsize=(8, 6))

    input_powers = log_data['input_powers']
    output_powers = log_data['output_powers']
    fit_a = log_data['fit_a']
    fit_b = log_data['fit_b']

    # Simulated data
    ax1.loglog(input_powers, output_powers, 'bo', markersize=8, label='FDTD Simulation')

    # Fitted log curve
    x_fit = np.logspace(np.log10(min(input_powers)), np.log10(max(input_powers)), 100)
    y_fit = fit_a * np.log(1 + fit_b * x_fit)
    ax1.loglog(x_fit, y_fit, 'r-', linewidth=2, label=f'Fit: {fit_a:.2f}·ln(1 + {fit_b:.2f}·I)')

    # Ideal linear reference
    y_linear = input_powers * 0.3  # Scale for comparison
    ax1.loglog(input_powers, y_linear, 'g--', alpha=0.5, label='Linear reference')

    ax1.set_xlabel('Input Power (a.u.)', fontsize=14)
    ax1.set_ylabel('Output Power (a.u.)', fontsize=14)
    ax1.set_title(f'Saturable Absorber (Log Converter)\n'
                  f'L={log_data["length_um"]}μm, R²={log_data["r_squared"]:.3f}',
                  fontsize=14, fontweight='bold')
    ax1.legend(loc='lower right', fontsize=10)
    ax1.grid(True, which='both', alpha=0.3)

    plt.tight_layout()
    log_plot_path = os.path.join(PNG_DIR, 'log_converter_transfer.png')
    plt.savefig(log_plot_path, dpi=300)
    print(f"  Saved: {log_plot_path}")
    plt.close()

    # ===== EXP CONVERTER PLOT =====
    fig2, ax2 = plt.subplots(figsize=(8, 6))

    positions = exp_data['positions']
    powers = exp_data['powers']
    measured_gain = exp_data['measured_gain']

    # Normalize position to start at 0
    x_norm = positions - positions[0]

    # Simulated data
    ax2.semilogy(x_norm, powers, 'bo-', markersize=8, label='FDTD Simulation')

    # Ideal exponential
    x_ideal = np.linspace(0, max(x_norm), 100)
    p0 = powers[0]
    y_ideal = p0 * np.exp(exp_data['expected_gain'] * x_ideal)
    ax2.semilogy(x_ideal, y_ideal, 'r--', linewidth=2,
                 label=f'Ideal: exp({exp_data["expected_gain"]:.3f}·x)')

    # Fitted exponential
    y_fitted = p0 * np.exp(measured_gain * x_ideal)
    ax2.semilogy(x_ideal, y_fitted, 'g-', linewidth=2,
                 label=f'Fitted: exp({measured_gain:.3f}·x)')

    ax2.set_xlabel('Position along waveguide (μm)', fontsize=14)
    ax2.set_ylabel('Power (a.u.)', fontsize=14)
    ax2.set_title(f'Gain Medium (Exp Converter)\n'
                  f'L={exp_data["length_um"]}μm, g={exp_data["gain_coefficient"]}/μm, '
                  f'R²={exp_data["r_squared"]:.3f}',
                  fontsize=14, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=10)
    ax2.grid(True, which='both', alpha=0.3)

    plt.tight_layout()
    exp_plot_path = os.path.join(PNG_DIR, 'exp_converter_transfer.png')
    plt.savefig(exp_plot_path, dpi=300)
    print(f"  Saved: {exp_plot_path}")
    plt.close()


def save_csv_data(log_data: dict, exp_data: dict):
    """Saves simulation results to CSV files."""

    # Log converter data
    log_csv_path = os.path.join(CSV_DIR, 'log_converter_data.csv')
    header = "Input_Power,Output_Power,Fit_A,Fit_B,R_squared,Length_um,I_sat_ratio"
    data_rows = []
    for i, (p_in, p_out) in enumerate(zip(log_data['input_powers'], log_data['output_powers'])):
        if i == 0:
            data_rows.append(f"{p_in},{p_out},{log_data['fit_a']},{log_data['fit_b']},"
                           f"{log_data['r_squared']},{log_data['length_um']},{log_data['i_sat_ratio']}")
        else:
            data_rows.append(f"{p_in},{p_out},,,,")

    with open(log_csv_path, 'w') as f:
        f.write(header + '\n')
        for row in data_rows:
            f.write(row + '\n')
    print(f"  Saved: {log_csv_path}")

    # Exp converter data
    exp_csv_path = os.path.join(CSV_DIR, 'exp_converter_data.csv')
    header = "Position_um,Power,Measured_gain,Expected_gain,R_squared,Length_um"
    data_rows = []
    for i, (pos, pwr) in enumerate(zip(exp_data['positions'], exp_data['powers'])):
        if i == 0:
            data_rows.append(f"{pos},{pwr},{exp_data['measured_gain']},{exp_data['expected_gain']},"
                           f"{exp_data['r_squared']},{exp_data['length_um']}")
        else:
            data_rows.append(f"{pos},{pwr},,,,")

    with open(exp_csv_path, 'w') as f:
        f.write(header + '\n')
        for row in data_rows:
            f.write(row + '\n')
    print(f"  Saved: {exp_csv_path}")


def main():
    """Run complete log/exp converter characterization."""
    print("\n" + "="*70)
    print("LOG/EXP CONVERTER FDTD SIMULATION SUITE")
    print("Wavelength-Division Ternary Optical Computer")
    print("="*70)

    # Run log converter simulation
    log_data = run_log_converter_simulation(
        length_um=50.0,
        i_sat_ratio=1.0,
        input_powers=np.logspace(-1, 2, 15),  # Fewer points for faster run
        wavelength_um=1.55,
        resolution=15  # Lower resolution for speed
    )

    # Run exp converter simulation
    exp_data = run_exp_converter_simulation(
        length_um=50.0,
        gain_coefficient=0.05,
        wavelength_um=1.55,
        pump_wavelength_um=0.98,
        resolution=15
    )

    # Generate plots
    plot_transfer_functions(log_data, exp_data)

    # Save data
    save_csv_data(log_data, exp_data)

    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
    print(f"\nOutput files:")
    print(f"  - {os.path.join(PNG_DIR, 'log_converter_transfer.png')}")
    print(f"  - {os.path.join(PNG_DIR, 'exp_converter_transfer.png')}")
    print(f"  - {os.path.join(CSV_DIR, 'log_converter_data.csv')}")
    print(f"  - {os.path.join(CSV_DIR, 'exp_converter_data.csv')}")

    return log_data, exp_data


if __name__ == "__main__":
    main()
