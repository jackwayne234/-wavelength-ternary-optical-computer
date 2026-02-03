#!/usr/bin/env python3
"""
Arrayed Waveguide Grating (AWG) Demultiplexer Simulation

FDTD simulation of AWG for separating ternary wavelengths in the decoder.
Must cleanly separate RED (1.55um), GREEN (1.216um), BLUE (1.0um),
and SFG outputs for 5-level detection.

Usage:
    python awg_demux_sim.py                     # Run broadband test
    python awg_demux_sim.py --wavelength 1.55   # Single wavelength routing
    python awg_demux_sim.py --sweep             # Full wavelength sweep
"""

import os
import sys
import argparse
import meep as mp
import numpy as np
import matplotlib.pyplot as plt

# Ternary wavelengths (um) - sorted by wavelength for channel assignment
WAVELENGTHS = {
    'SFG_RB': 0.608,   # RED + BLUE sum frequency (shortest)
    'SFG_RG': 0.681,   # RED + GREEN sum frequency
    'BLUE': 1.0,
    'GREEN': 1.216,
    'RED': 1.55,       # longest
}

# Target output channels
N_CHANNELS = 5


def calculate_awg_parameters(wavelengths: dict, n_eff: float = 1.8,
                             n_group: float = 1.9):
    """
    Calculate proper AWG design parameters for the target wavelengths.

    AWG design equations:
    - Path length difference: delta_L = m * lambda_c / n_eff
    - Free spectral range: FSR = lambda_c^2 / (n_g * delta_L)
    - Angular dispersion: d(theta)/d(lambda) = m / (n_s * d)

    For very wide wavelength spans, we need FSR > wavelength span.

    Args:
        wavelengths: dict of target wavelengths (um)
        n_eff: Effective index of arrayed waveguides
        n_group: Group index for dispersion

    Returns:
        dict with calculated AWG parameters
    """
    wvls = sorted(wavelengths.values())
    lambda_min = min(wvls)  # 0.608 um
    lambda_max = max(wvls)  # 1.55 um
    lambda_center = (lambda_min + lambda_max) / 2  # ~1.08 um

    # Total wavelength span
    delta_lambda_total = lambda_max - lambda_min  # ~0.94 um

    # For such a wide wavelength span, we MUST have FSR > delta_lambda
    # FSR = lambda_c^2 / (n_g * delta_L) = lambda_c / (m * n_g / n_eff)
    # For FSR > 1.0 um (with margin), we need:
    # m < lambda_c * n_eff / (n_g * 1.0)
    # m < 1.079 * 1.8 / (1.9 * 1.0) = 1.02
    # So we must use m = 1 for this wide wavelength span

    diffraction_order = 1

    # With m=1, we need to maximize angular dispersion through geometry
    # dispersion = m / (n_s * d)
    # Smaller pitch = more dispersion, but limited by waveguide width

    # Array pitch - small but practical
    array_pitch = 0.8  # um

    # Path length difference
    delta_L = diffraction_order * lambda_center / n_eff

    # Free spectral range
    FSR = lambda_center**2 / (n_group * delta_L)

    # Number of array waveguides
    n_array = 20

    # Large FPR radius to give room for output spread
    # Output span = R * tan(theta_max) where theta_max = dispersion * delta_lambda/2
    dispersion = diffraction_order / (n_eff * array_pitch)
    theta_max = dispersion * delta_lambda_total / 2
    # We want output span ~ 2 * R * tan(theta_max) to fit all channels
    # For theta_max ~ 0.32 rad (18 deg), tan ~ 0.33, so R=20 gives span ~ 13um
    fpr_radius = 20.0  # um

    print(f"\n  AWG Design Parameters:")
    print(f"    Center wavelength: {lambda_center:.3f} um")
    print(f"    Wavelength span: {delta_lambda_total:.3f} um")
    print(f"    Diffraction order m: {diffraction_order}")
    print(f"    Path length increment delta_L: {delta_L:.4f} um")
    print(f"    Free spectral range: {FSR:.3f} um (must be > {delta_lambda_total:.3f})")
    print(f"    Number of array waveguides: {n_array}")
    print(f"    Array pitch: {array_pitch:.2f} um")
    print(f"    FPR radius: {fpr_radius:.1f} um")
    print(f"    Angular dispersion: {dispersion:.3f} rad/um")
    print(f"    Max output angle: {np.degrees(theta_max):.1f} deg")

    return {
        'lambda_center': lambda_center,
        'delta_lambda': delta_lambda_total,
        'diffraction_order': diffraction_order,
        'delta_L': delta_L,
        'FSR': FSR,
        'n_array': n_array,
        'fpr_radius': fpr_radius,
        'array_pitch': array_pitch,
        'n_eff': n_eff,
        'n_group': n_group,
    }


def create_awg_geometry(n_channels: int = 5, awg_params: dict = None):
    """
    Create AWG geometry for Meep simulation with proper physics-based sizing.

    This creates a compact AWG with:
    - Input waveguide -> Input FPR (slab region) -> Array waveguides -> Output FPR -> Output waveguides
    - All components are properly connected with no gaps

    Args:
        n_channels: Number of output channels
        awg_params: Pre-calculated AWG parameters

    Returns:
        dict with geometry list and port positions
    """
    if awg_params is None:
        awg_params = calculate_awg_parameters(WAVELENGTHS)

    # Material parameters
    n_core = 2.0        # Waveguide core index (Si3N4)
    n_clad = 1.44       # Cladding index (SiO2)

    # Extract parameters
    delta_L = awg_params['delta_L']
    fpr_radius = awg_params['fpr_radius']
    n_array = awg_params['n_array']
    array_pitch = awg_params['array_pitch']
    lambda_center = awg_params['lambda_center']

    # Waveguide width - ensure single mode at shortest wavelength
    lambda_min = min(WAVELENGTHS.values())
    wg_width_cutoff = lambda_min / (2 * np.sqrt(n_core**2 - n_clad**2))
    wg_width = min(0.35, wg_width_cutoff * 0.8)
    wg_width = max(0.25, wg_width)

    print(f"    Waveguide width: {wg_width:.3f} um")

    # Base array waveguide length (minimum)
    array_length_base = 8.0

    geometry = []
    core_material = mp.Medium(index=n_core)

    # Calculate array span
    array_span = (n_array - 1) * array_pitch
    fpr_height = array_span + 4 * wg_width  # Extra margin

    # Compute total device length
    max_array_length = array_length_base + (n_array - 1) * delta_L
    total_length = 5 + fpr_radius + max_array_length + fpr_radius + 5 + 10

    # Cell size
    cell_x = total_length + 6  # Add margin for PML
    cell_y = max(fpr_height + 6, 20)

    print(f"    Cell size: {cell_x:.1f} x {cell_y:.1f} um")

    # ========== COORDINATE SYSTEM ==========
    # Origin at center of cell
    # Input on left, output on right

    x_input_start = -cell_x/2 + 2
    x_input_end = x_input_start + 5
    x_fpr1_start = x_input_end
    x_fpr1_end = x_fpr1_start + fpr_radius
    x_array_start = x_fpr1_end
    x_fpr2_start = x_array_start + max_array_length
    x_fpr2_end = x_fpr2_start + fpr_radius
    x_output_start = x_fpr2_end

    # ========== INPUT WAVEGUIDE ==========
    geometry.append(
        mp.Block(
            mp.Vector3(5, wg_width, mp.inf),
            center=mp.Vector3((x_input_start + x_input_end)/2, 0),
            material=core_material
        )
    )

    # Input taper to improve coupling to FPR
    taper_length = 2.0
    geometry.append(
        mp.Prism(
            vertices=[
                mp.Vector3(x_input_end, -wg_width/2),
                mp.Vector3(x_input_end, wg_width/2),
                mp.Vector3(x_input_end + taper_length, wg_width * 2),
                mp.Vector3(x_input_end + taper_length, -wg_width * 2),
            ],
            height=mp.inf,
            material=core_material
        )
    )

    # ========== INPUT FPR (SLAB REGION) ==========
    # The FPR is a slab waveguide that allows light to diffract
    geometry.append(
        mp.Block(
            mp.Vector3(fpr_radius, fpr_height, mp.inf),
            center=mp.Vector3((x_fpr1_start + x_fpr1_end)/2, 0),
            material=core_material
        )
    )

    # ========== ARRAY WAVEGUIDES ==========
    array_positions = []
    for i in range(n_array):
        # Y position centered around zero
        y_pos = (i - (n_array - 1)/2) * array_pitch

        # Length increases with index for phase difference
        length = array_length_base + i * delta_L

        # The array waveguide starts at x_array_start and ends at varying positions
        # We need them all to end at the same x (x_fpr2_start) for proper connection
        # So we use the maximum length and make all waveguides that long
        # The phase difference comes from the optical path, not physical end position

        # Actually, for proper AWG operation with FDTD, we should have
        # waveguides of different physical lengths ending at the same FPR

        # Create waveguide from array start to its end
        wg_end_x = x_array_start + length

        geometry.append(
            mp.Block(
                mp.Vector3(length, wg_width, mp.inf),
                center=mp.Vector3(x_array_start + length/2, y_pos),
                material=core_material
            )
        )

        # Add extension to connect to output FPR if needed
        if wg_end_x < x_fpr2_start:
            ext_length = x_fpr2_start - wg_end_x
            geometry.append(
                mp.Block(
                    mp.Vector3(ext_length + 0.01, wg_width, mp.inf),
                    center=mp.Vector3(wg_end_x + ext_length/2, y_pos),
                    material=core_material
                )
            )

        array_positions.append({
            'index': i,
            'y': y_pos,
            'length': length,
        })

    # ========== OUTPUT FPR ==========
    geometry.append(
        mp.Block(
            mp.Vector3(fpr_radius, fpr_height, mp.inf),
            center=mp.Vector3((x_fpr2_start + x_fpr2_end)/2, 0),
            material=core_material
        )
    )

    # ========== OUTPUT WAVEGUIDES ==========
    output_positions = []
    sorted_wavelengths = sorted(WAVELENGTHS.items(), key=lambda x: x[1])

    # Calculate output positions using AWG grating equation
    # The angular dispersion of an AWG is: d(theta)/d(lambda) = m / (n_s * d * R)
    # where m = diffraction order, n_s = slab index, d = array pitch, R = FPR radius
    #
    # For wavelength lambda, the output position is:
    # y = R * sin(theta) where theta = m * (lambda - lambda_c) / (n_s * d)

    m = awg_params['diffraction_order']
    n_s = n_core  # Slab effective index (approximate as core)
    d = array_pitch
    R = fpr_radius

    # The dispersion factor determines how much the output angle changes per wavelength
    # For low-order AWG (m=1), we need larger FPR or smaller pitch for good separation
    dispersion = m / (n_s * d)  # radians per um of wavelength

    output_wg_length = 5.0
    for i, (name, wvl) in enumerate(sorted_wavelengths):
        # Calculate output angle from grating equation
        delta_lambda = wvl - lambda_center
        theta = dispersion * delta_lambda  # Output angle in radians

        # Y position at output FPR edge
        y_pos = R * np.sin(theta)

        # Clamp to FPR bounds
        max_y = fpr_height / 2 - wg_width
        y_pos = np.clip(y_pos, -max_y, max_y)

        geometry.append(
            mp.Block(
                mp.Vector3(output_wg_length, wg_width, mp.inf),
                center=mp.Vector3(x_output_start + output_wg_length/2, y_pos),
                material=core_material
            )
        )

        output_positions.append({
            'channel': i,
            'name': name,
            'wavelength': wvl,
            'y': y_pos,
            'x': x_output_start + output_wg_length,
            'theta_deg': np.degrees(theta),
        })
        print(f"    Output Ch{i} ({name}, {wvl:.3f}um): y={y_pos:.2f}um, theta={np.degrees(theta):.1f}deg")

    return {
        'geometry': geometry,
        'cell_size': (cell_x, cell_y),
        'input_pos': (x_input_start + 1, 0),
        'output_positions': output_positions,
        'array_positions': array_positions,
        'n_core': n_core,
        'n_clad': n_clad,
        'wg_width': wg_width,
        'fpr_radius': fpr_radius,
        'awg_params': awg_params,
        'fpr_height': fpr_height,
    }


def run_awg_simulation(wavelength: float = None, resolution: int = 15,
                       n_channels: int = 5):
    """
    Run AWG demultiplexer simulation.

    Args:
        wavelength: Test wavelength (um), None for broadband
        resolution: FDTD resolution (pixels/um)
        n_channels: Number of output channels

    Returns:
        dict with channel responses
    """
    print(f"\n--- AWG DEMULTIPLEXER SIMULATION ---")
    if wavelength:
        print(f"Test wavelength: {wavelength} um")
    else:
        print("Broadband simulation")

    # Calculate proper AWG parameters first
    awg_params = calculate_awg_parameters(WAVELENGTHS)

    # Create AWG geometry with calculated parameters
    awg = create_awg_geometry(n_channels=n_channels, awg_params=awg_params)

    cell_x, cell_y = awg['cell_size']
    cell_size = mp.Vector3(cell_x, cell_y, 0)
    pml_thickness = 1.0

    print(f"\n  Simulation cell: {cell_x:.1f} x {cell_y:.1f} um")
    print(f"  Resolution: {resolution} pixels/um")

    # Source setup
    if wavelength:
        freq = 1.0 / wavelength
        freq_width = 0.15 * freq  # 15% bandwidth
        source = mp.Source(
            mp.GaussianSource(freq, fwidth=freq_width),
            component=mp.Ez,
            center=mp.Vector3(awg['input_pos'][0], awg['input_pos'][1]),
            size=mp.Vector3(0, awg['wg_width'] * 2, 0)
        )
        sim_time_factor = 2.0
    else:
        # Broadband source covering all ternary wavelengths (0.55 to 1.7 um)
        freq_min = 1.0 / 1.7
        freq_max = 1.0 / 0.55
        freq_center = (freq_min + freq_max) / 2
        freq_width = (freq_max - freq_min) * 0.8
        source = mp.Source(
            mp.GaussianSource(freq_center, fwidth=freq_width),
            component=mp.Ez,
            center=mp.Vector3(awg['input_pos'][0], awg['input_pos'][1]),
            size=mp.Vector3(0, awg['wg_width'] * 2, 0)
        )
        sim_time_factor = 3.0
        print(f"  Source freq: {freq_center:.3f} +/- {freq_width:.3f}")

    # Create simulation with cladding background
    sim = mp.Simulation(
        cell_size=cell_size,
        boundary_layers=[mp.PML(pml_thickness)],
        geometry=awg['geometry'],
        sources=[source],
        resolution=resolution,
        default_material=mp.Medium(index=awg['n_clad'])
    )

    # Flux monitor parameters
    if wavelength:
        mon_freq = 1.0 / wavelength
        mon_df = 0.3 * mon_freq
        nfreq = 100
    else:
        mon_freq = freq_center
        mon_df = freq_width
        nfreq = 200

    # Add flux monitors at each output channel
    channel_monitors = []
    for out in awg['output_positions']:
        mon = sim.add_flux(
            mon_freq, mon_df, nfreq,
            mp.FluxRegion(
                center=mp.Vector3(out['x'] - 1, out['y']),
                size=mp.Vector3(0, awg['wg_width'] * 3, 0)
            )
        )
        channel_monitors.append(mon)

    # Input monitor for normalization
    input_mon = sim.add_flux(
        mon_freq, mon_df, nfreq,
        mp.FluxRegion(
            center=mp.Vector3(awg['input_pos'][0] + 2, awg['input_pos'][1]),
            size=mp.Vector3(0, awg['wg_width'] * 3, 0)
        )
    )

    # Calculate simulation time based on device size and group velocity
    # Time for light to traverse device: L * n_g / c
    # In Meep units (c=1): time = L * n_g
    n_g = awg_params['n_group']
    min_time = cell_x * n_g * sim_time_factor

    print(f"\n  Running FDTD simulation...")
    print(f"  Estimated time: {min_time:.1f} Meep units")

    # Run for fixed time to ensure light propagates through
    sim.run(until=min_time)

    actual_time = sim.meep_time()
    print(f"  Completed at t = {actual_time:.1f}")

    # Collect results
    freqs = np.array(mp.get_flux_freqs(channel_monitors[0]))
    wavelengths_out = 1.0 / freqs
    input_flux = np.array(mp.get_fluxes(input_mon))

    # Handle negative flux (can happen at boundaries)
    input_flux = np.maximum(np.abs(input_flux), 1e-20)

    channel_results = []
    print(f"\n  Channel Results:")
    for i, mon in enumerate(channel_monitors):
        flux = np.array(mp.get_fluxes(mon))
        # Use absolute value to handle any sign issues
        transmission = np.abs(flux) / input_flux

        # Find peak wavelength for this channel
        peak_idx = np.argmax(transmission)
        peak_wvl = wavelengths_out[peak_idx]
        peak_T = transmission[peak_idx]

        # Get transmission at target wavelength
        out_info = awg['output_positions'][i]
        target_wvl = out_info['wavelength']
        target_idx = np.argmin(np.abs(wavelengths_out - target_wvl))
        target_T = transmission[target_idx]

        channel_results.append({
            'channel': i,
            'name': out_info['name'],
            'target_wavelength': target_wvl,
            'flux': flux,
            'transmission': transmission,
            'peak_wavelength': peak_wvl,
            'peak_transmission': peak_T,
            'target_transmission': target_T
        })

        print(f"    Ch{i} ({out_info['name']:6s}): target={target_wvl:.3f}um, "
              f"T@target={target_T:.4f}, peak@{peak_wvl:.3f}um T={peak_T:.4f}")

    # Calculate crosstalk matrix
    crosstalk_matrix = np.zeros((n_channels, n_channels))
    for i, ch_i in enumerate(channel_results):
        target_wvl = ch_i['target_wavelength']
        target_idx = np.argmin(np.abs(wavelengths_out - target_wvl))
        for j, ch_j in enumerate(channel_results):
            if i != j and ch_i['transmission'][target_idx] > 1e-10:
                crosstalk_matrix[i, j] = ch_j['transmission'][target_idx] / ch_i['transmission'][target_idx]

    max_xt = np.max(crosstalk_matrix)
    if max_xt > 1e-10:
        print(f"\n  Max crosstalk: {max_xt:.4f} ({10*np.log10(max_xt):.1f} dB)")
    else:
        print(f"\n  Crosstalk: negligible")

    return {
        'frequencies': freqs,
        'wavelengths': wavelengths_out,
        'input_flux': input_flux,
        'channels': channel_results,
        'crosstalk_matrix': crosstalk_matrix,
        'n_channels': n_channels,
        'test_wavelength': wavelength,
        'awg_params': awg_params,
        'simulation_time': actual_time
    }


def run_wavelength_routing_test():
    """
    Test AWG routing for each ternary wavelength.
    """
    print("\n=== AWG WAVELENGTH ROUTING TEST ===")

    results = {}
    for name, wvl in WAVELENGTHS.items():
        print(f"\n--- Testing {name} ({wvl} um) ---")
        result = run_awg_simulation(wavelength=wvl, resolution=12)

        # Find which channel has maximum response at this wavelength
        max_ch = -1
        max_T = 0
        for ch in result['channels']:
            idx = np.argmin(np.abs(result['wavelengths'] - wvl))
            T = ch['transmission'][idx]
            if T > max_T:
                max_T = T
                max_ch = ch['channel']

        results[name] = {
            'wavelength': wvl,
            'routed_to_channel': max_ch,
            'transmission': max_T,
            'full_result': result
        }
        print(f"  {name} ({wvl} um) -> Channel {max_ch}, T = {max_T:.4f}")

    return results


def save_results(result: dict, output_dir: str, label: str = ""):
    """Save AWG simulation results."""
    os.makedirs(output_dir, exist_ok=True)

    # Determine filename
    if result.get('test_wavelength'):
        wvl_nm = int(result['test_wavelength'] * 1000)
        base_name = f"awg_response_{wvl_nm}nm"
    else:
        base_name = f"awg_broadband{label}"

    # Save CSV
    csv_path = os.path.join(output_dir, f"{base_name}.csv")

    data_cols = [result['frequencies'], result['wavelengths'], result['input_flux']]
    header_parts = ["Frequency (Meep)", "Wavelength (um)", "Input Flux"]

    for ch in result['channels']:
        data_cols.append(ch['flux'])
        data_cols.append(ch['transmission'])
        header_parts.append(f"Ch{ch['channel']} Flux")
        header_parts.append(f"Ch{ch['channel']} T")

    data = np.column_stack(data_cols)
    header = ",".join(header_parts)
    np.savetxt(csv_path, data, delimiter=",", header=header, comments='')
    print(f"Saved: {csv_path}")

    # Plot channel responses
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    colors = plt.cm.tab10(np.linspace(0, 1, result['n_channels']))

    for ch in result['channels']:
        ax1.plot(result['wavelengths'], ch['transmission'],
                 color=colors[ch['channel']], linewidth=1.5,
                 label=f"Ch {ch['channel']} ({ch['name']})")

    # Mark target wavelengths
    for name, wvl in WAVELENGTHS.items():
        if 0.5 < wvl < 2.0:
            ax1.axvline(x=wvl, color='gray', linestyle=':', alpha=0.5)
            ax1.text(wvl, ax1.get_ylim()[1] * 0.95 if ax1.get_ylim()[1] > 0 else 0.1,
                     name, fontsize=8, ha='center', rotation=90)

    ax1.set_xlabel('Wavelength (um)', fontsize=12)
    ax1.set_ylabel('Transmission', fontsize=12)
    ax1.set_title('AWG Channel Response (Meep FDTD)', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0.5, 2.0)

    # Crosstalk matrix
    im = ax2.imshow(result['crosstalk_matrix'], cmap='hot_r', aspect='auto')
    ax2.set_xlabel('Source Channel', fontsize=12)
    ax2.set_ylabel('Measured Channel', fontsize=12)
    ax2.set_title('Crosstalk Matrix', fontsize=12)
    ax2.set_xticks(range(result['n_channels']))
    ax2.set_yticks(range(result['n_channels']))
    plt.colorbar(im, ax=ax2, label='Relative Power')

    plt.tight_layout()
    plot_path = os.path.join(output_dir, f"{base_name}.png")
    plt.savefig(plot_path, dpi=300)
    print(f"Saved: {plot_path}")
    plt.close()

    # Save crosstalk matrix
    xtalk_path = os.path.join(output_dir, f"{base_name}_crosstalk.csv")
    np.savetxt(xtalk_path, result['crosstalk_matrix'], delimiter=",",
               header=",".join([f"Ch{i}" for i in range(result['n_channels'])]),
               comments='')
    print(f"Saved: {xtalk_path}")


def main():
    parser = argparse.ArgumentParser(description='AWG Demultiplexer Meep FDTD Simulation')
    parser.add_argument('--wavelength', type=float, help='Test single wavelength (um)')
    parser.add_argument('--sweep', action='store_true', help='Test all ternary wavelengths')
    parser.add_argument('--broadband', action='store_true', help='Broadband simulation (default)')
    parser.add_argument('--channels', type=int, default=5, help='Number of output channels')
    parser.add_argument('--resolution', type=int, default=15, help='FDTD resolution')
    parser.add_argument('--output', type=str, default=None, help='Output directory')

    args = parser.parse_args()

    # Output directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = args.output or os.path.join(base_dir, 'data', 'csv')

    print("=" * 60)
    print("  AWG DEMULTIPLEXER - Meep FDTD Simulation")
    print("  For Ternary Optical Computer Wavelength Separation")
    print("=" * 60)
    print(f"  Target wavelengths:")
    for name, wvl in WAVELENGTHS.items():
        print(f"    {name}: {wvl} um")
    print(f"  Output channels: {args.channels}")

    if args.sweep:
        results = run_wavelength_routing_test()

        summary_path = os.path.join(output_dir, "awg_routing_summary.csv")
        os.makedirs(output_dir, exist_ok=True)
        with open(summary_path, 'w') as f:
            f.write("Wavelength Name,Wavelength (um),Routed Channel,Transmission\n")
            for name, data in results.items():
                f.write(f"{name},{data['wavelength']},{data['routed_to_channel']},{data['transmission']:.4f}\n")
        print(f"\nSaved routing summary: {summary_path}")

    elif args.wavelength:
        result = run_awg_simulation(args.wavelength, args.resolution, args.channels)
        save_results(result, output_dir)

    else:
        result = run_awg_simulation(None, args.resolution, args.channels)
        save_results(result, output_dir)

    print("\n" + "=" * 60)
    print("  SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
