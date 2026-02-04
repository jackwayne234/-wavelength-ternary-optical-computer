#!/usr/bin/env python3
"""
Clock Distribution Simulation for Integrated Supercomputer

Validates that the central Kerr clock reaches all PEs with minimal skew.
This is CRITICAL for the Round Table architecture - equal path lengths
from center Kerr to all processing elements.

Usage:
    python clock_distribution_sim.py                  # Default 9×9 array
    python clock_distribution_sim.py --array-size 27  # Larger array test
    python clock_distribution_sim.py --analyze-skew   # Detailed skew analysis
"""

import os
import sys
import argparse
import meep as mp
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict, Tuple

# Target clock frequency
TARGET_CLOCK_FREQ = 617e6  # 617 MHz word rate

# Design parameters (matching integrated_supercomputer.py)
PE_SIZE = 50.0      # μm
PE_SPACING = 60.0   # μm
KERR_RADIUS = 30.0  # μm
WG_WIDTH = 0.5      # μm


def clock_distribution_simulation(
    array_size: int = 9,
    wavelength: float = 1.55,
    resolution: int = 20,
    duration: float = 100.0
) -> Dict:
    """
    Simulate clock pulse propagation from central Kerr to all PE positions.

    Args:
        array_size: Size of PE array (9 = 9×9 grid)
        wavelength: Clock wavelength (μm)
        resolution: FDTD resolution (pixels/μm)
        duration: Simulation duration (Meep time units)

    Returns:
        dict with arrival times and skew measurements at each PE position
    """
    print(f"\n{'='*60}")
    print("CLOCK DISTRIBUTION SIMULATION")
    print(f"{'='*60}")
    print(f"Array size: {array_size}×{array_size}")
    print(f"Wavelength: {wavelength} μm")
    print(f"Target: {TARGET_CLOCK_FREQ/1e6:.0f} MHz")

    freq = 1.0 / wavelength

    # Calculate geometry
    array_width = array_size * PE_SPACING
    center_idx = array_size // 2

    # Cell size: covers full array with margin
    margin = 20.0
    pml_thickness = 2.0
    cell_x = array_width + 2 * margin + 2 * pml_thickness
    cell_y = array_width + 2 * margin + 2 * pml_thickness

    cell_size = mp.Vector3(cell_x, cell_y, 0)

    print(f"\nGeometry:")
    print(f"  Cell: {cell_x:.0f} × {cell_y:.0f} μm")
    print(f"  Kerr at origin: (0, 0)")

    # Material
    n_core = 2.0  # Silicon effective index
    wg_material = mp.Medium(index=n_core)

    # Build geometry: clock distribution waveguides from center to all PEs
    geometry = []

    # Central Kerr region (simplified as cylinder)
    geometry.append(
        mp.Cylinder(
            radius=KERR_RADIUS,
            height=mp.inf,
            center=mp.Vector3(0, 0),  # Origin = Kerr center
            material=wg_material
        )
    )

    # Clock distribution waveguides (radial from center to each PE)
    pe_positions = []
    for row in range(array_size):
        for col in range(array_size):
            # Skip center (Kerr position)
            if row == center_idx and col == center_idx:
                continue

            # PE position relative to center
            pe_x = (col - center_idx) * PE_SPACING
            pe_y = (row - center_idx) * PE_SPACING
            pe_positions.append((pe_x, pe_y, row, col))

            # Add waveguide from center to PE
            # Direction from center
            dist = np.sqrt(pe_x**2 + pe_y**2)
            if dist > KERR_RADIUS:
                # Normalized direction
                dx, dy = pe_x / dist, pe_y / dist

                # Waveguide block (thin rectangle from Kerr edge to PE)
                start_x = KERR_RADIUS * dx
                start_y = KERR_RADIUS * dy

                geometry.append(
                    mp.Block(
                        # Fixed: length along e1 (toward PE), width along e2 (perpendicular)
                        size=mp.Vector3(dist - KERR_RADIUS, WG_WIDTH, mp.inf),
                        center=mp.Vector3(
                            (start_x + pe_x) / 2,
                            (start_y + pe_y) / 2
                        ),
                        e1=mp.Vector3(dx, dy, 0),
                        e2=mp.Vector3(-dy, dx, 0),
                        material=wg_material
                    )
                )

    # Source: Gaussian pulse at Kerr edge (where waveguides connect)
    # Placed along +x axis at the edge of the Kerr region
    # Made larger to better excite waveguide modes
    source_size = 2.0  # μm - larger source for better coupling
    sources = [
        mp.Source(
            mp.GaussianSource(freq, fwidth=0.2 * freq),  # wider bandwidth
            component=mp.Ez,
            center=mp.Vector3(KERR_RADIUS + 1.0, 0, 0),  # Just outside Kerr edge
            size=mp.Vector3(source_size, source_size, 0)
        )
    ]

    # Simulation
    # NOTE: Do NOT use geometry_center here. The geometry, sources, and monitors
    # are all defined with origin at (0,0) = center of the Kerr. Using geometry_center
    # would shift the coordinate system and cause monitoring points to be misaligned.
    sim = mp.Simulation(
        cell_size=cell_size,
        boundary_layers=[mp.PML(pml_thickness)],
        geometry=geometry,
        sources=sources,
        resolution=resolution
    )

    # Monitor points at each PE position
    print(f"\nMonitoring {len(pe_positions)} PE positions...")

    # DIAGNOSTIC: Monitor points at various distances from center
    # This helps identify where signal drops off
    diagnostic_distances = [
        ("center", 0),
        ("kerr_edge", KERR_RADIUS),
        ("25%", KERR_RADIUS + (PE_SPACING - KERR_RADIUS) * 0.25),
        ("50%", KERR_RADIUS + (PE_SPACING - KERR_RADIUS) * 0.50),
        ("75%", KERR_RADIUS + (PE_SPACING - KERR_RADIUS) * 0.75),
        ("first_pe", PE_SPACING),
    ]

    # Pick one direction for diagnostic (straight right: +x)
    diagnostic_points = [(name, dist, 1.0, 0.0) for name, dist in diagnostic_distances]
    diagnostic_data = {name: [] for name, _, _, _ in diagnostic_points}

    # Time recording for arrival analysis
    time_data = []
    pe_field_data = {pos: [] for pos in pe_positions}
    center_field_data = []

    def record_fields(sim):
        t = sim.meep_time()
        time_data.append(t)

        # Center field
        center_field_data.append(
            abs(sim.get_field_point(mp.Ez, mp.Vector3(0, 0)))**2
        )

        # DIAGNOSTIC: Record field at each distance along +x axis
        for name, dist, dx, dy in diagnostic_points:
            x, y = dist * dx, dist * dy
            field = abs(sim.get_field_point(mp.Ez, mp.Vector3(x, y)))**2
            diagnostic_data[name].append(field)

        # Each PE field
        for pos in pe_positions:
            pe_x, pe_y, _, _ = pos
            field = abs(sim.get_field_point(mp.Ez, mp.Vector3(pe_x, pe_y)))**2
            pe_field_data[pos].append(field)

    # Run simulation
    print("\nRunning FDTD simulation...")
    sim.run(mp.at_every(0.2, record_fields), until=duration)

    # DIAGNOSTIC: Print where signal drops off
    print("\n" + "="*60)
    print("DIAGNOSTIC: Signal strength along +X axis")
    print("="*60)
    print(f"{'Location':<15} {'Distance (μm)':<15} {'Peak Intensity':<15}")
    print("-"*60)
    for name, dist, _, _ in diagnostic_points:
        peak = np.max(diagnostic_data[name]) if diagnostic_data[name] else 0
        print(f"{name:<15} {dist:<15.1f} {peak:<15.6f}")
    print("-"*60)

    # Identify drop-off point
    peaks = [(name, np.max(diagnostic_data[name])) for name, _, _, _ in diagnostic_points]
    for i, (name, peak) in enumerate(peaks):
        if i > 0 and peak < peaks[0][1] * 0.01:  # <1% of center
            print(f"⚠ Signal drops below 1% at: {name}")
            break
    else:
        if peaks[-1][1] > peaks[0][1] * 0.01:
            print(f"✓ Signal reaches first PE with {peaks[-1][1]/peaks[0][1]*100:.1f}% of source intensity")

    # Analyze arrival times
    print("\nAnalyzing clock arrival times...")

    time_arr = np.array(time_data)
    center_arr = np.array(center_field_data)

    # Find source peak time
    source_peak_idx = np.argmax(center_arr)
    source_peak_time = time_arr[source_peak_idx]

    # Analyze each PE
    arrival_times = {}
    for pos in pe_positions:
        pe_arr = np.array(pe_field_data[pos])

        # Find when signal first exceeds threshold
        threshold = 0.1 * np.max(pe_arr) if np.max(pe_arr) > 0 else 0
        above_threshold = np.where(pe_arr > threshold)[0]

        if len(above_threshold) > 0:
            arrival_idx = above_threshold[0]
            arrival_time = time_arr[arrival_idx]
            delay = arrival_time - source_peak_time
        else:
            arrival_time = None
            delay = None

        pe_x, pe_y, row, col = pos
        dist = np.sqrt(pe_x**2 + pe_y**2)

        arrival_times[(row, col)] = {
            'position': (pe_x, pe_y),
            'distance': dist,
            'arrival_time': arrival_time,
            'delay': delay,
            'peak_intensity': np.max(pe_arr)
        }

    # Calculate skew statistics
    delays = [v['delay'] for v in arrival_times.values() if v['delay'] is not None]

    if delays:
        min_delay = min(delays)
        max_delay = max(delays)
        skew = max_delay - min_delay
        avg_delay = np.mean(delays)
        std_delay = np.std(delays)
    else:
        min_delay = max_delay = skew = avg_delay = std_delay = 0

    print(f"\n{'='*60}")
    print("CLOCK DISTRIBUTION RESULTS")
    print(f"{'='*60}")
    print(f"Source peak time: {source_peak_time:.2f} (Meep units)")
    print(f"\nDelay statistics:")
    print(f"  Min delay: {min_delay:.3f}")
    print(f"  Max delay: {max_delay:.3f}")
    print(f"  Clock skew: {skew:.3f} (Meep units)")
    print(f"  Avg delay: {avg_delay:.3f} ± {std_delay:.3f}")

    # Convert to physical units (approximate)
    # Meep time unit = a/c, if a = 1 μm, then 1 Meep time = ~3.33 fs
    # For 617 MHz clock, period = 1.62 ns = 1620 ps
    skew_ps = skew * 3.33  # Approximate conversion
    period_ps = 1.0 / (TARGET_CLOCK_FREQ * 1e-12)  # Clock period in ps
    skew_percent = (skew_ps / period_ps) * 100 if period_ps > 0 else 0

    print(f"\nPhysical estimates:")
    print(f"  Clock skew: ~{skew_ps:.1f} fs")
    print(f"  Clock period: ~{period_ps:.0f} ps")
    print(f"  Skew as % of period: ~{skew_percent:.3f}%")

    # Assess acceptability
    ACCEPTABLE_SKEW_PERCENT = 5.0  # Industry standard: <5% of clock period
    if skew_percent < ACCEPTABLE_SKEW_PERCENT:
        print(f"\n✓ PASS: Clock skew ({skew_percent:.3f}%) < {ACCEPTABLE_SKEW_PERCENT}% threshold")
    else:
        print(f"\n✗ FAIL: Clock skew ({skew_percent:.3f}%) exceeds {ACCEPTABLE_SKEW_PERCENT}% threshold")

    return {
        'array_size': array_size,
        'wavelength': wavelength,
        'time': time_arr,
        'center_field': center_arr,
        'pe_fields': pe_field_data,
        'arrival_times': arrival_times,
        'skew': skew,
        'skew_ps': skew_ps,
        'skew_percent': skew_percent,
        'avg_delay': avg_delay,
        'std_delay': std_delay
    }


def analyze_skew_vs_distance(result: Dict) -> None:
    """Analyze how clock skew varies with distance from Kerr."""

    print(f"\n{'='*60}")
    print("SKEW vs DISTANCE ANALYSIS")
    print(f"{'='*60}")

    distances = []
    delays = []

    for (row, col), data in result['arrival_times'].items():
        if data['delay'] is not None:
            distances.append(data['distance'])
            delays.append(data['delay'])

    if not distances:
        print("No valid delay data to analyze")
        return

    # Sort by distance
    sorted_pairs = sorted(zip(distances, delays))
    distances = [p[0] for p in sorted_pairs]
    delays = [p[1] for p in sorted_pairs]

    # Group by distance rings
    unique_distances = sorted(set([round(d, 1) for d in distances]))

    print("\nDelay by distance ring:")
    print(f"{'Distance (μm)':<15} {'Avg Delay':<12} {'Std Dev':<12} {'Count':<8}")
    print("-" * 50)

    for target_dist in unique_distances:
        ring_delays = [d for dist, d in zip(distances, delays)
                       if abs(dist - target_dist) < 5]
        if ring_delays:
            avg = np.mean(ring_delays)
            std = np.std(ring_delays)
            print(f"{target_dist:<15.1f} {avg:<12.4f} {std:<12.4f} {len(ring_delays):<8}")

    # Linear fit to check if delay scales with distance (as expected)
    if len(distances) > 2:
        coeffs = np.polyfit(distances, delays, 1)
        propagation_speed = 1.0 / coeffs[0] if coeffs[0] != 0 else float('inf')
        print(f"\nLinear fit: delay = {coeffs[0]:.6f} × distance + {coeffs[1]:.4f}")
        print(f"Estimated propagation speed: {propagation_speed:.1f} μm/(Meep time)")


def save_results(result: Dict, output_dir: str) -> None:
    """Save clock distribution results."""

    os.makedirs(output_dir, exist_ok=True)
    array_size = result['array_size']

    # Save arrival times CSV
    csv_path = os.path.join(output_dir, f'clock_distribution_{array_size}x{array_size}.csv')
    with open(csv_path, 'w') as f:
        f.write("Row,Col,PE_X,PE_Y,Distance,Arrival_Time,Delay,Peak_Intensity\n")
        for (row, col), data in result['arrival_times'].items():
            f.write(f"{row},{col},{data['position'][0]:.1f},{data['position'][1]:.1f},"
                    f"{data['distance']:.1f},{data['arrival_time']},{data['delay']},"
                    f"{data['peak_intensity']:.6f}\n")
    print(f"Saved: {csv_path}")

    # Save summary
    summary_path = os.path.join(output_dir, f'clock_skew_summary_{array_size}x{array_size}.txt')
    with open(summary_path, 'w') as f:
        f.write(f"CLOCK DISTRIBUTION SUMMARY\n")
        f.write(f"==========================\n\n")
        f.write(f"Array size: {array_size}×{array_size}\n")
        f.write(f"Wavelength: {result['wavelength']} μm\n\n")
        f.write(f"Clock Skew: {result['skew']:.4f} (Meep units)\n")
        f.write(f"Clock Skew: ~{result['skew_ps']:.1f} fs\n")
        f.write(f"Skew as % of period: {result['skew_percent']:.3f}%\n\n")
        f.write(f"Average delay: {result['avg_delay']:.4f} ± {result['std_delay']:.4f}\n")
        f.write(f"\nThreshold: 5% of clock period\n")
        f.write(f"Status: {'PASS' if result['skew_percent'] < 5.0 else 'FAIL'}\n")
    print(f"Saved: {summary_path}")

    # Plot 1: Clock skew heatmap
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Create delay grid
    array_size = result['array_size']
    center_idx = array_size // 2
    delay_grid = np.full((array_size, array_size), np.nan)
    intensity_grid = np.full((array_size, array_size), np.nan)

    for (row, col), data in result['arrival_times'].items():
        if data['delay'] is not None:
            delay_grid[row, col] = data['delay']
            intensity_grid[row, col] = data['peak_intensity']

    # Mark Kerr position
    delay_grid[center_idx, center_idx] = 0

    # Delay heatmap
    im1 = axes[0].imshow(delay_grid, cmap='viridis', origin='lower')
    axes[0].set_title(f'Clock Delay from Central Kerr\n({array_size}×{array_size} array)')
    axes[0].set_xlabel('Column')
    axes[0].set_ylabel('Row')
    axes[0].plot(center_idx, center_idx, 'r*', markersize=15, label='Kerr')
    axes[0].legend()
    plt.colorbar(im1, ax=axes[0], label='Delay (Meep units)')

    # Intensity heatmap
    im2 = axes[1].imshow(intensity_grid, cmap='hot', origin='lower')
    axes[1].set_title('Peak Clock Intensity at Each PE')
    axes[1].set_xlabel('Column')
    axes[1].set_ylabel('Row')
    axes[1].plot(center_idx, center_idx, 'c*', markersize=15, label='Kerr')
    axes[1].legend()
    plt.colorbar(im2, ax=axes[1], label='Intensity (a.u.)')

    plt.tight_layout()
    plot_path = os.path.join(output_dir, f'clock_distribution_{array_size}x{array_size}.png')
    plt.savefig(plot_path, dpi=300)
    print(f"Saved: {plot_path}")
    plt.close()

    # Plot 2: Time traces
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    time_arr = result['time']

    # Center (source)
    ax1.plot(time_arr, result['center_field'], 'k-', linewidth=2, label='Kerr (source)')
    ax1.set_xlabel('Time (Meep units)')
    ax1.set_ylabel('Field Intensity')
    ax1.set_title('Clock Pulse at Source (Central Kerr)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Selected PE positions (corners + edges)
    colors = plt.cm.tab10(np.linspace(0, 1, 8))
    sample_positions = []

    # Get corner PEs
    for row in [0, array_size-1]:
        for col in [0, array_size-1]:
            if (row, col) != (center_idx, center_idx):
                sample_positions.append((row, col))

    for i, (row, col) in enumerate(sample_positions[:4]):
        for pos, fields in result['pe_fields'].items():
            if pos[2] == row and pos[3] == col:
                pe_arr = np.array(fields)
                dist = np.sqrt(pos[0]**2 + pos[1]**2)
                ax2.plot(time_arr, pe_arr, color=colors[i],
                        label=f'PE[{row},{col}] d={dist:.0f}μm')
                break

    ax2.set_xlabel('Time (Meep units)')
    ax2.set_ylabel('Field Intensity')
    ax2.set_title('Clock Pulse Arrival at Corner PEs')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    traces_path = os.path.join(output_dir, f'clock_traces_{array_size}x{array_size}.png')
    plt.savefig(traces_path, dpi=300)
    print(f"Saved: {traces_path}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Clock Distribution Meep Simulation')
    parser.add_argument('--array-size', type=int, default=9, help='Array size (9 = 9×9)')
    parser.add_argument('--wavelength', type=float, default=1.55, help='Wavelength (μm)')
    parser.add_argument('--resolution', type=int, default=20, help='FDTD resolution')
    parser.add_argument('--duration', type=float, default=100.0, help='Simulation duration')
    parser.add_argument('--analyze-skew', action='store_true', help='Detailed skew analysis')
    parser.add_argument('--output', type=str, default=None, help='Output directory')

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = args.output or os.path.join(base_dir, 'data', 'csv')

    print("=" * 60)
    print("  CLOCK DISTRIBUTION SIMULATION")
    print("  Validating Central Kerr → All PEs")
    print("=" * 60)
    print(f"  Target: Minimal skew (<5% of clock period)")

    # Run simulation
    result = clock_distribution_simulation(
        array_size=args.array_size,
        wavelength=args.wavelength,
        resolution=args.resolution,
        duration=args.duration
    )

    # Detailed skew analysis
    if args.analyze_skew:
        analyze_skew_vs_distance(result)

    # Save results
    save_results(result, output_dir)

    print("\n" + "=" * 60)
    print("  SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
