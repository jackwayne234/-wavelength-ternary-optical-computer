#!/usr/bin/env python3
"""
Optical Component Simulation for Ternary Optical Computer

This module loads and uses REAL Meep FDTD simulation results for:
- SFG mixer wavelength combinations (from universal_mixer.py runs)
- Material characterization data

Instead of analytical approximations, we use the ground-truth physics
simulations that were already run.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict
from enum import Enum
from pathlib import Path

# Physical constants
C = 299792458  # Speed of light (m/s)

# Data directory (relative to this file)
DATA_DIR = Path(__file__).parent.parent / "data"
CSV_DIR = DATA_DIR / "csv"
PNG_DIR = DATA_DIR / "png"

# Wavelengths for ternary encoding (from your Meep simulations)
LAMBDA_RED = 1.55     # μm - trit value -1
LAMBDA_GREEN = 1.216  # μm - trit value 0
LAMBDA_BLUE = 1.0     # μm - trit value +1


class TritValue(Enum):
    """Ternary trit values with wavelength encoding."""
    NEG = (-1, LAMBDA_RED, "RED")
    ZERO = (0, LAMBDA_GREEN, "GREEN")
    POS = (1, LAMBDA_BLUE, "BLUE")

    @property
    def value_int(self):
        return self.value[0]

    @property
    def wavelength(self):
        return self.value[1]

    @property
    def color_name(self):
        return self.value[2]


@dataclass
class MeepMixerResult:
    """Parsed result from a Meep SFG mixer simulation."""
    input1: str  # Color name (RED, GREEN, BLUE)
    input2: str
    wavelength1: float  # μm
    wavelength2: float
    frequencies: np.ndarray  # Meep frequency units
    wavelengths: np.ndarray  # μm
    flux: np.ndarray  # a.u.
    target_sum_wavelength: float  # μm
    peak_flux_at_sum: float
    peak_flux_at_input1: float
    peak_flux_at_input2: float


class MeepDataLoader:
    """
    Load and parse real Meep FDTD simulation results.
    """

    def __init__(self, csv_dir: Path = CSV_DIR):
        self.csv_dir = Path(csv_dir)
        self._mixer_cache: Dict[str, MeepMixerResult] = {}
        self._load_all_mixer_data()

    def _load_all_mixer_data(self):
        """Load all available mixer CSV files."""
        color_wavelengths = {
            'RED': LAMBDA_RED,
            'GREEN': LAMBDA_GREEN,
            'BLUE': LAMBDA_BLUE
        }

        # Find all mixer data files
        for csv_file in self.csv_dir.glob("mixer_data_*.csv"):
            # Parse filename: mixer_data_COLOR1_COLOR2.csv
            parts = csv_file.stem.replace("mixer_data_", "").split("_")
            if len(parts) == 2:
                color1, color2 = parts
                if color1 in color_wavelengths and color2 in color_wavelengths:
                    result = self._load_mixer_csv(
                        csv_file,
                        color1, color2,
                        color_wavelengths[color1],
                        color_wavelengths[color2]
                    )
                    if result:
                        key = f"{color1}_{color2}"
                        self._mixer_cache[key] = result

    def _load_mixer_csv(self, filepath: Path, color1: str, color2: str,
                        wvl1: float, wvl2: float) -> Optional[MeepMixerResult]:
        """Load a single mixer CSV file."""
        try:
            data = np.genfromtxt(filepath, delimiter=',', skip_header=1)
            if data.size == 0:
                return None

            frequencies = data[:, 0]
            wavelengths = data[:, 1]
            flux = data[:, 2]

            # Calculate target sum wavelength
            freq1 = 1.0 / wvl1
            freq2 = 1.0 / wvl2
            freq_sum = freq1 + freq2
            wvl_sum = 1.0 / freq_sum

            # Find peak flux at key wavelengths
            def flux_at_wavelength(target_wvl):
                idx = np.argmin(np.abs(wavelengths - target_wvl))
                return flux[idx]

            return MeepMixerResult(
                input1=color1,
                input2=color2,
                wavelength1=wvl1,
                wavelength2=wvl2,
                frequencies=frequencies,
                wavelengths=wavelengths,
                flux=flux,
                target_sum_wavelength=wvl_sum,
                peak_flux_at_sum=flux_at_wavelength(wvl_sum),
                peak_flux_at_input1=flux_at_wavelength(wvl1),
                peak_flux_at_input2=flux_at_wavelength(wvl2)
            )
        except Exception as e:
            print(f"Warning: Could not load {filepath}: {e}")
            return None

    def get_mixer_result(self, color1: str, color2: str) -> Optional[MeepMixerResult]:
        """
        Get mixer result for two input colors.

        Args:
            color1, color2: 'RED', 'GREEN', or 'BLUE'

        Returns:
            MeepMixerResult or None if not found
        """
        # Try both orderings
        key1 = f"{color1}_{color2}"
        key2 = f"{color2}_{color1}"

        if key1 in self._mixer_cache:
            return self._mixer_cache[key1]
        elif key2 in self._mixer_cache:
            return self._mixer_cache[key2]
        return None

    def list_available_combinations(self) -> List[str]:
        """List all available mixer combinations."""
        return list(self._mixer_cache.keys())


class TernaryMixerSimulator:
    """
    Simulate ternary arithmetic using REAL Meep FDTD data.
    """

    def __init__(self, meep_loader: MeepDataLoader = None):
        self.loader = meep_loader or MeepDataLoader()

    def get_output_spectrum(self, trit_a: TritValue, trit_b: TritValue) -> Optional[MeepMixerResult]:
        """
        Get the REAL Meep-simulated output spectrum for mixing two trits.

        Args:
            trit_a, trit_b: Input trit values

        Returns:
            MeepMixerResult with full spectrum data
        """
        return self.loader.get_mixer_result(trit_a.color_name, trit_b.color_name)

    def simulate_addition(self, trit_a: TritValue, trit_b: TritValue) -> Dict:
        """
        Simulate ternary addition using real Meep data.

        Returns dict with:
        - result_trit: The output trit value
        - carry: Carry value (-1, 0, or +1)
        - meep_data: The actual FDTD simulation result
        - peak_analysis: Analysis of output peaks
        """
        # Mathematical result
        sum_val = trit_a.value_int + trit_b.value_int

        if sum_val > 1:
            result_trit = TritValue.NEG  # -1 with carry +1
            carry = 1
        elif sum_val < -1:
            result_trit = TritValue.POS  # +1 with carry -1
            carry = -1
        else:
            result_trit = [t for t in TritValue if t.value_int == sum_val][0]
            carry = 0

        # Get real Meep data
        meep_result = self.get_output_spectrum(trit_a, trit_b)

        # Analyze output spectrum
        peak_analysis = None
        if meep_result:
            peak_analysis = self._analyze_peaks(meep_result)

        return {
            'input_a': trit_a,
            'input_b': trit_b,
            'result_int': sum_val,
            'result_trit': result_trit,
            'carry': carry,
            'meep_data': meep_result,
            'peak_analysis': peak_analysis
        }

    def _analyze_peaks(self, meep_result: MeepMixerResult) -> Dict:
        """Analyze the peaks in the output spectrum."""
        wavelengths = meep_result.wavelengths
        flux = meep_result.flux

        # Find all local maxima
        peaks = []
        for i in range(1, len(flux) - 1):
            if flux[i] > flux[i-1] and flux[i] > flux[i+1] and flux[i] > 0.01 * np.max(flux):
                peaks.append({
                    'wavelength': wavelengths[i],
                    'flux': flux[i],
                    'relative_strength': flux[i] / np.max(flux)
                })

        # Sort by flux strength
        peaks.sort(key=lambda x: x['flux'], reverse=True)

        # Identify which peaks correspond to which trit values
        trit_peaks = {}
        for trit in TritValue:
            idx = np.argmin(np.abs(wavelengths - trit.wavelength))
            trit_peaks[trit.color_name] = {
                'wavelength': trit.wavelength,
                'flux': flux[idx],
                'relative': flux[idx] / np.max(flux) if np.max(flux) > 0 else 0
            }

        # Sum frequency peak
        sum_idx = np.argmin(np.abs(wavelengths - meep_result.target_sum_wavelength))
        sum_peak = {
            'wavelength': meep_result.target_sum_wavelength,
            'flux': flux[sum_idx],
            'relative': flux[sum_idx] / np.max(flux) if np.max(flux) > 0 else 0
        }

        return {
            'all_peaks': peaks[:5],  # Top 5 peaks
            'trit_wavelength_flux': trit_peaks,
            'sum_frequency_peak': sum_peak,
            'max_flux': np.max(flux),
            'dominant_wavelength': wavelengths[np.argmax(flux)]
        }


def plot_mixer_spectrum(meep_result: MeepMixerResult, title: str = None) -> plt.Figure:
    """
    Plot a mixer spectrum with annotated wavelengths.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot spectrum
    ax.plot(meep_result.wavelengths, meep_result.flux, 'k-', linewidth=1.5, label='Output Spectrum')

    # Mark input wavelengths
    colors = {'RED': '#D55E00', 'GREEN': '#009E73', 'BLUE': '#0072B2'}

    ax.axvline(x=meep_result.wavelength1, color=colors.get(meep_result.input1, 'gray'),
               linestyle='--', linewidth=1.5, alpha=0.8,
               label=f'Input: {meep_result.input1} ({meep_result.wavelength1} μm)')

    ax.axvline(x=meep_result.wavelength2, color=colors.get(meep_result.input2, 'gray'),
               linestyle='--', linewidth=1.5, alpha=0.8,
               label=f'Input: {meep_result.input2} ({meep_result.wavelength2} μm)')

    # Mark sum frequency
    ax.axvline(x=meep_result.target_sum_wavelength, color='#CC79A7',
               linestyle='-', linewidth=2.5, alpha=0.9,
               label=f'SFG Output ({meep_result.target_sum_wavelength:.3f} μm)')

    ax.set_xlabel('Wavelength (μm)', fontsize=12)
    ax.set_ylabel('Flux (a.u.)', fontsize=12)
    ax.set_title(title or f'Meep FDTD: {meep_result.input1} + {meep_result.input2}', fontsize=14)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_ternary_addition_table(simulator: TernaryMixerSimulator) -> plt.Figure:
    """
    Plot ternary addition table with REAL Meep peak flux data.
    """
    fig, axes = plt.subplots(3, 3, figsize=(14, 12))

    trits = [TritValue.NEG, TritValue.ZERO, TritValue.POS]
    labels = ['-1 (RED)', '0 (GREEN)', '+1 (BLUE)']

    for i, trit_a in enumerate(trits):
        for j, trit_b in enumerate(trits):
            ax = axes[i, j]

            result = simulator.simulate_addition(trit_a, trit_b)
            meep_data = result['meep_data']

            if meep_data:
                # Plot actual Meep spectrum
                ax.plot(meep_data.wavelengths, meep_data.flux, 'k-', linewidth=0.8)

                # Mark SFG output
                ax.axvline(x=meep_data.target_sum_wavelength, color='magenta',
                           linestyle='--', alpha=0.7)

                ax.set_xlim(0.5, 2.0)

                # Title with result
                carry_str = f" (c={result['carry']:+d})" if result['carry'] != 0 else ""
                ax.set_title(f"{trit_a.value_int}+{trit_b.value_int}={result['result_int']}{carry_str}",
                             fontsize=10, fontweight='bold')
            else:
                ax.text(0.5, 0.5, 'No Meep data', ha='center', va='center',
                        transform=ax.transAxes, fontsize=10)
                ax.set_title(f"{trit_a.value_int}+{trit_b.value_int}", fontsize=10)

            ax.set_xlabel('λ (μm)' if i == 2 else '', fontsize=8)
            ax.set_ylabel('Flux' if j == 0 else '', fontsize=8)
            ax.tick_params(labelsize=7)

    # Row/column labels
    for i, label in enumerate(labels):
        axes[i, 0].set_ylabel(f'{label}\n\nFlux', fontsize=9)
        axes[2, i].set_xlabel(f'λ (μm)\n\n{label}', fontsize=9)

    fig.suptitle('Ternary Addition: Real Meep FDTD Spectra', fontsize=14, fontweight='bold')
    plt.tight_layout()
    return fig


def analyze_sfg_efficiency(simulator: TernaryMixerSimulator) -> Dict:
    """
    Analyze SFG conversion efficiency for all trit combinations.
    Uses REAL Meep data.
    """
    trits = [TritValue.NEG, TritValue.ZERO, TritValue.POS]
    results = {}

    for trit_a in trits:
        for trit_b in trits:
            key = f"{trit_a.color_name}+{trit_b.color_name}"
            result = simulator.simulate_addition(trit_a, trit_b)
            meep_data = result['meep_data']

            if meep_data:
                # Calculate conversion efficiency
                input_flux = meep_data.peak_flux_at_input1 + meep_data.peak_flux_at_input2
                sfg_flux = meep_data.peak_flux_at_sum

                if input_flux > 0:
                    efficiency = sfg_flux / input_flux
                else:
                    efficiency = 0

                results[key] = {
                    'input_wavelengths': (meep_data.wavelength1, meep_data.wavelength2),
                    'sfg_wavelength': meep_data.target_sum_wavelength,
                    'sfg_flux': sfg_flux,
                    'input_flux_total': input_flux,
                    'conversion_efficiency': efficiency,
                    'max_output_flux': np.max(meep_data.flux),
                    'dominant_output_wavelength': meep_data.wavelengths[np.argmax(meep_data.flux)]
                }
            else:
                results[key] = {'error': 'No Meep data available'}

    return results


def print_sfg_analysis(analysis: Dict):
    """Print formatted SFG analysis."""
    print("\n" + "=" * 70)
    print("  SFG CONVERSION ANALYSIS (from Meep FDTD data)")
    print("=" * 70)

    print(f"\n{'Combination':<20} {'SFG λ (μm)':<12} {'SFG Flux':<12} {'Dom. λ (μm)':<12} {'Eff.':<10}")
    print("-" * 70)

    for key, data in sorted(analysis.items()):
        if 'error' not in data:
            print(f"{key:<20} {data['sfg_wavelength']:<12.3f} "
                  f"{data['sfg_flux']:<12.2e} "
                  f"{data['dominant_output_wavelength']:<12.3f} "
                  f"{data['conversion_efficiency']*100:<10.2f}%")
        else:
            print(f"{key:<20} {data['error']}")


def run_meep_based_simulation():
    """
    Run simulation using REAL Meep FDTD data.
    """
    print("=" * 70)
    print("  OPTICAL SIMULATION - Using Real Meep FDTD Data")
    print("=" * 70)

    # Load Meep data
    print("\nLoading Meep simulation results...")
    loader = MeepDataLoader()
    available = loader.list_available_combinations()
    print(f"Found {len(available)} mixer combinations: {', '.join(available)}")

    # Create simulator
    simulator = TernaryMixerSimulator(loader)

    # Demonstrate with RED + BLUE (should produce GREEN via SFG)
    print("\n" + "=" * 60)
    print("  DEMO: RED + BLUE -> SFG (should produce GREEN-ish)")
    print("=" * 60)

    result = simulator.simulate_addition(TritValue.NEG, TritValue.POS)
    print(f"\n  Input A: {result['input_a'].color_name} ({result['input_a'].wavelength} μm) = {result['input_a'].value_int}")
    print(f"  Input B: {result['input_b'].color_name} ({result['input_b'].wavelength} μm) = {result['input_b'].value_int}")
    print(f"  Math result: {result['input_a'].value_int} + {result['input_b'].value_int} = {result['result_int']}")
    print(f"  Output trit: {result['result_trit'].color_name} (carry={result['carry']})")

    if result['meep_data']:
        meep = result['meep_data']
        print(f"\n  Meep FDTD Results:")
        print(f"    Target SFG wavelength: {meep.target_sum_wavelength:.4f} μm")
        print(f"    SFG peak flux: {meep.peak_flux_at_sum:.4e}")
        print(f"    Input 1 peak flux: {meep.peak_flux_at_input1:.4e}")
        print(f"    Input 2 peak flux: {meep.peak_flux_at_input2:.4e}")

    if result['peak_analysis']:
        pa = result['peak_analysis']
        print(f"\n  Spectrum Analysis:")
        print(f"    Dominant output wavelength: {pa['dominant_wavelength']:.4f} μm")
        print(f"    Max flux: {pa['max_flux']:.4e}")
        print(f"    Top peaks:")
        for i, peak in enumerate(pa['all_peaks'][:3]):
            print(f"      {i+1}. λ={peak['wavelength']:.3f} μm, flux={peak['flux']:.2e} ({peak['relative_strength']*100:.1f}%)")

    # Full SFG analysis
    print("\n" + "=" * 60)
    print("  FULL SFG EFFICIENCY ANALYSIS")
    print("=" * 60)

    analysis = analyze_sfg_efficiency(simulator)
    print_sfg_analysis(analysis)

    # Key finding
    print("\n" + "=" * 60)
    print("  KEY FINDINGS FROM MEEP DATA")
    print("=" * 60)

    # Find best SFG combination
    best_combo = None
    best_eff = 0
    for key, data in analysis.items():
        if 'error' not in data and data['conversion_efficiency'] > best_eff:
            best_eff = data['conversion_efficiency']
            best_combo = key

    if best_combo:
        print(f"\n  Best SFG efficiency: {best_combo} at {best_eff*100:.2f}%")

    # Check distinguishability
    print("\n  Output distinguishability (dominant wavelength for each combo):")
    for key, data in sorted(analysis.items()):
        if 'error' not in data:
            dom = data['dominant_output_wavelength']
            # Classify
            if dom > 1.4:
                channel = "RED range"
            elif dom > 1.1:
                channel = "GREEN range"
            elif dom > 0.8:
                channel = "BLUE range"
            else:
                channel = "SFG/UV"
            print(f"    {key}: {dom:.3f} μm ({channel})")

    print("\n" + "=" * 70)
    print("  SIMULATION COMPLETE - Using Real Physics Data")
    print("=" * 70)

    return simulator, analysis


def generate_plots(output_dir: str = None):
    """Generate visualization plots using real Meep data."""
    if output_dir is None:
        output_dir = DATA_DIR / "plots"
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    print(f"\nGenerating plots to {output_dir}...")

    loader = MeepDataLoader()
    simulator = TernaryMixerSimulator(loader)

    # Individual mixer spectra
    for combo in loader.list_available_combinations():
        colors = combo.split("_")
        if len(colors) == 2:
            trit_a = [t for t in TritValue if t.color_name == colors[0]][0]
            trit_b = [t for t in TritValue if t.color_name == colors[1]][0]
            meep_data = loader.get_mixer_result(colors[0], colors[1])
            if meep_data:
                fig = plot_mixer_spectrum(meep_data, f"Meep FDTD: {combo}")
                fig.savefig(output_dir / f"meep_spectrum_{combo}.png", dpi=150)
                plt.close(fig)
                print(f"  Saved: meep_spectrum_{combo}.png")

    # Full addition table
    fig = plot_ternary_addition_table(simulator)
    fig.savefig(output_dir / "meep_ternary_addition_table.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: meep_ternary_addition_table.png")

    print(f"\nAll plots saved to: {output_dir}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--plots':
        output_dir = sys.argv[2] if len(sys.argv) > 2 else None
        run_meep_based_simulation()
        generate_plots(output_dir)
    else:
        run_meep_based_simulation()
        print("\nRun with --plots [output_dir] to generate visualization images.")
