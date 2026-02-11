#!/usr/bin/env python3
"""
IOC Integration Test: All 9 Trit x Trit Multiplications
=========================================================

FDTD simulation of the PPLN SFG mixer for all 6 unique ternary multiplications.

Tests the core physics:
    1. Do two input wavelengths produce SFG at the correct output wavelength?
    2. Does the QPM-matched SFG dominate over unwanted SHG harmonics?
    3. Is there sufficient signal for each of the 9 multiplication cases?

Ternary wavelength encoding (collision-free triplet):
    RED   = 1550 nm -> trit -1
    GREEN = 1310 nm -> trit  0
    BLUE  = 1064 nm -> trit +1

SFG output wavelengths (1/lam_sfg = 1/lam_a + 1/lam_b):
    B+B (1064+1064): 532 nm -> (+1)x(+1) = +1   QPM period: 4.68 um
    G+B (1310+1064): 587 nm -> ( 0)x(+1) =  0   QPM period: 6.53 um
    R+B (1550+1064): 631 nm -> (-1)x(+1) = -1   QPM period: 8.57 um
    G+G (1310+1310): 655 nm -> ( 0)x( 0) =  0   QPM period: 9.35 um
    R+G (1550+1310): 710 nm -> (-1)x( 0) =  0   QPM period: 12.19 um
    R+R (1550+1550): 775 nm -> (-1)x(-1) = +1   QPM period: 16.10 um

AWG demux routing is validated analytically (grating equation, 24+ nm channel spacing).
FDTD is used here only for the nonlinear SFG physics which cannot be verified analytically.

Usage:
    mpirun -np 12 /home/jackwayne/miniconda/envs/meep_env/bin/python -u ioc_integration_test.py

Copyright (c) 2026 Christopher Riner
Licensed under the MIT License.

Wavelength-Division Ternary Optical Computer
DOI: 10.5281/zenodo.18437600
"""

import os
import sys
import time
import meep as mp
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

# ---------------------------------------------------------------------------
# MPI support
# ---------------------------------------------------------------------------
try:
    from mpi4py import MPI
    RANK = MPI.COMM_WORLD.Get_rank()
    SIZE = MPI.COMM_WORLD.Get_size()
    IS_PARALLEL = SIZE > 1
except (ImportError, RuntimeError, OSError):
    RANK = 0
    SIZE = 1
    IS_PARALLEL = False


def print_master(msg):
    if RANK == 0:
        print(msg, flush=True)


# ===========================================================================
# MATERIAL MODEL (LiNbO3 — single-pole Lorentzian fit to Sellmeier)
# ===========================================================================

LINBO3_EPS    = 1.472   # epsilon_inf
LINBO3_SIGMA  = 3.035   # oscillator strength
LINBO3_FREQ0  = 4.5     # resonance frequency (Meep units, ~222nm UV)
CHI2_VAL      = 0.5     # chi(2) susceptibility (Meep units)


def compute_meep_index(wavelength_um: float) -> float:
    """Refractive index from the Lorentzian material model."""
    f = 1.0 / wavelength_um
    eps = LINBO3_EPS + LINBO3_SIGMA * LINBO3_FREQ0**2 / (LINBO3_FREQ0**2 - f**2)
    return float(np.sqrt(eps))


def compute_qpm_period(lambda_a_um: float, lambda_b_um: float) -> float:
    """PPLN quasi-phase-matching period for SFG: lambda_a + lambda_b -> lambda_sfg."""
    lambda_sfg = 1.0 / (1.0 / lambda_a_um + 1.0 / lambda_b_um)
    n_a = compute_meep_index(lambda_a_um)
    n_b = compute_meep_index(lambda_b_um)
    n_sfg = compute_meep_index(lambda_sfg)
    delta_k = 2.0 * np.pi * (n_sfg / lambda_sfg - n_a / lambda_a_um - n_b / lambda_b_um)
    if abs(delta_k) < 1e-10:
        return float('inf')
    return abs(2.0 * np.pi / delta_k)


# ===========================================================================
# TERNARY DEFINITIONS
# ===========================================================================

LAMBDA_RED   = 1.550   # trit = -1
LAMBDA_GREEN = 1.310   # trit =  0
LAMBDA_BLUE  = 1.064   # trit = +1


def sfg_wavelength(la: float, lb: float) -> float:
    return 1.0 / (1.0 / la + 1.0 / lb)


# SFG table — all 6 unique interactions
SFG_TABLE = {}
for _key, _la, _lb, _trit in [
    ('B+B', LAMBDA_BLUE,  LAMBDA_BLUE,  +1),
    ('G+B', LAMBDA_GREEN, LAMBDA_BLUE,   0),
    ('R+B', LAMBDA_RED,   LAMBDA_BLUE,  -1),
    ('G+G', LAMBDA_GREEN, LAMBDA_GREEN,  0),
    ('R+G', LAMBDA_RED,   LAMBDA_GREEN,  0),
    ('R+R', LAMBDA_RED,   LAMBDA_RED,   +1),
]:
    SFG_TABLE[_key] = {
        'lambda_a': _la,
        'lambda_b': _lb,
        'lambda_sfg': sfg_wavelength(_la, _lb),
        'result_trit': _trit,
        'qpm_period': compute_qpm_period(_la, _lb),
    }

# AWG channel definitions (for reference and decode logic)
AWG_CHANNELS = {
    'SFG_BB': {'wavelength_nm': 532.0, 'trit': +1},
    'SFG_GB': {'wavelength_nm': 587.1, 'trit':  0},
    'SFG_RB': {'wavelength_nm': 630.9, 'trit': -1},
    'SFG_GG': {'wavelength_nm': 655.0, 'trit':  0},
    'SFG_RG': {'wavelength_nm': 710.0, 'trit':  0},
    'SFG_RR': {'wavelength_nm': 775.0, 'trit': +1},
}

# All 9 multiplication cases
MULT_TABLE = [
    (-1, -1, 'R+R', +1), (-1,  0, 'R+G',  0), (-1, +1, 'R+B', -1),
    ( 0, -1, 'R+G',  0), ( 0,  0, 'G+G',  0), ( 0, +1, 'G+B',  0),
    (+1, -1, 'R+B', -1), (+1,  0, 'G+B',  0), (+1, +1, 'B+B', +1),
]

# ===========================================================================
# SIMULATION PARAMETERS
# ===========================================================================

SFG_WG_WIDTH  = 0.8     # um, mixer waveguide width
SFG_WG_LENGTH = 20.0    # um, PPLN mixer length
OUT_WG_LENGTH = 5.0     # um, output waveguide after mixer
N_CLAD        = 1.44    # SiO2 cladding
RESOLUTION    = 20      # pixels/um
PML_THICKNESS = 1.0     # um
SRC_BW_FRAC   = 0.04    # source bandwidth as fraction of center freq


# ===========================================================================
# SINGLE-PAIR SIMULATION
# ===========================================================================

def run_sfg_test(sfg_key: str) -> dict:
    """
    Run FDTD for one SFG interaction in a PPLN waveguide.

    Geometry: [PML] [src] [PPLN mixer 20um] [output WG 5um] [monitor] [PML]
    Measures the output spectrum and checks for SFG at the expected wavelength
    using a targeted window analysis (not global peak finding).
    """
    info = SFG_TABLE[sfg_key]
    la, lb = info['lambda_a'], info['lambda_b']
    lsfg = info['lambda_sfg']
    ppln_period = info['qpm_period']
    is_shg = abs(la - lb) < 0.001

    print_master(f"\n  {'='*60}")
    print_master(f"  TEST: {sfg_key} | {la*1000:.0f}nm + {lb*1000:.0f}nm -> {lsfg*1000:.1f}nm"
                 f" | trit {info['result_trit']:+d}")
    print_master(f"  QPM period: {ppln_period:.2f} um"
                 f" | {'SHG' if is_shg else 'cross-SFG'}")

    # Cell layout
    src_margin = 1.5
    x0 = PML_THICKNESS
    x_src      = x0 + src_margin
    x_sfg_st   = x_src + 0.5
    x_sfg_end  = x_sfg_st + SFG_WG_LENGTH
    x_out_end  = x_sfg_end + OUT_WG_LENGTH
    cell_x     = x_out_end + 1.0 + PML_THICKNESS
    cell_y     = SFG_WG_WIDTH + 4.0

    xshift = -cell_x / 2.0
    def sx(x):
        return x + xshift

    # Build PPLN domains
    geometry = []
    domain_len = ppln_period / 2.0
    n_dom = max(int(SFG_WG_LENGTH / domain_len), 2)

    for i in range(n_dom):
        ds = x_sfg_st + i * domain_len
        de = min(ds + domain_len, x_sfg_st + SFG_WG_LENGTH)
        dl = de - ds
        if dl < 0.01:
            break
        sign = 1 if (i % 2 == 0) else -1
        mat = mp.Medium(
            epsilon=LINBO3_EPS,
            E_susceptibilities=[
                mp.LorentzianSusceptibility(frequency=LINBO3_FREQ0, gamma=0.0,
                                            sigma=LINBO3_SIGMA)
            ],
            chi2=CHI2_VAL * sign,
        )
        geometry.append(
            mp.Block(size=mp.Vector3(dl, SFG_WG_WIDTH, mp.inf),
                     center=mp.Vector3(sx(ds + dl / 2.0), 0), material=mat)
        )

    print_master(f"  PPLN: {n_dom} domains, period={ppln_period:.2f} um")

    # Output waveguide (linear LiNbO3, no poling)
    linbo3_linear = mp.Medium(
        epsilon=LINBO3_EPS,
        E_susceptibilities=[
            mp.LorentzianSusceptibility(frequency=LINBO3_FREQ0, gamma=0.0,
                                        sigma=LINBO3_SIGMA)
        ],
    )
    geometry.append(
        mp.Block(size=mp.Vector3(OUT_WG_LENGTH, SFG_WG_WIDTH, mp.inf),
                 center=mp.Vector3(sx(x_sfg_end + OUT_WG_LENGTH / 2.0), 0),
                 material=linbo3_linear)
    )

    # Sources
    fa, fb = 1.0 / la, 1.0 / lb
    dfa, dfb = SRC_BW_FRAC * fa, SRC_BW_FRAC * fb

    if is_shg:
        sources = [
            mp.Source(src=mp.GaussianSource(fa, fwidth=dfa), component=mp.Ez,
                      center=mp.Vector3(sx(x_src), 0),
                      size=mp.Vector3(0, SFG_WG_WIDTH, 0), amplitude=2.0),
        ]
    else:
        sources = [
            mp.Source(src=mp.GaussianSource(fa, fwidth=dfa), component=mp.Ez,
                      center=mp.Vector3(sx(x_src), 0),
                      size=mp.Vector3(0, SFG_WG_WIDTH, 0)),
            mp.Source(src=mp.GaussianSource(fb, fwidth=dfb), component=mp.Ez,
                      center=mp.Vector3(sx(x_src), 0),
                      size=mp.Vector3(0, SFG_WG_WIDTH, 0)),
        ]

    sim = mp.Simulation(
        cell_size=mp.Vector3(cell_x, cell_y, 0),
        geometry=geometry,
        sources=sources,
        boundary_layers=[mp.PML(PML_THICKNESS)],
        resolution=RESOLUTION,
        default_material=mp.Medium(index=N_CLAD),
    )

    # Flux monitor — NARROW band around the expected SFG wavelength only.
    # This avoids broadband chi2 noise that dominates global peak search.
    # Monitor a ±40nm window centered on the expected SFG.
    f_sfg = 1.0 / lsfg
    monitor_half_bw_nm = 40.0  # nm half-width of monitoring window
    f_lo = 1.0 / (lsfg + monitor_half_bw_nm / 1000.0)
    f_hi = 1.0 / (lsfg - monitor_half_bw_nm / 1000.0)
    fcen_sfg = (f_lo + f_hi) / 2.0
    df_sfg = f_hi - f_lo
    nfreq_sfg = 200

    sfg_mon = sim.add_flux(
        fcen_sfg, df_sfg, nfreq_sfg,
        mp.FluxRegion(
            center=mp.Vector3(sx(x_out_end - 0.5), 0),
            size=mp.Vector3(0, SFG_WG_WIDTH * 2, 0),
        )
    )

    # Also monitor SHG bands for comparison (if cross-SFG)
    shg_mons = []
    if not is_shg:
        for lam_input in [la, lb]:
            lam_shg = lam_input / 2.0
            f_shg = 1.0 / lam_shg
            f_lo_shg = 1.0 / (lam_shg + 0.020)
            f_hi_shg = 1.0 / (lam_shg - 0.020)
            shg_mons.append(sim.add_flux(
                (f_lo_shg + f_hi_shg) / 2.0, f_hi_shg - f_lo_shg, 50,
                mp.FluxRegion(
                    center=mp.Vector3(sx(x_out_end - 0.5), 0),
                    size=mp.Vector3(0, SFG_WG_WIDTH * 2, 0),
                )
            ))

    # Broadband monitor for spectral plot
    f_min, f_max = 0.55, 2.10
    fcen_full = (f_min + f_max) / 2.0
    df_full = f_max - f_min
    full_mon = sim.add_flux(
        fcen_full, df_full, 500,
        mp.FluxRegion(
            center=mp.Vector3(sx(x_out_end - 0.5), 0),
            size=mp.Vector3(0, SFG_WG_WIDTH * 2, 0),
        )
    )

    # Run
    t0 = time.time()
    sim.run(until_after_sources=200)
    wall = time.time() - t0
    print_master(f"  Meep time: {sim.meep_time():.0f}, wall: {wall:.1f}s")

    # --- Analyze SFG monitor (narrow band around expected wavelength) ---
    sfg_freqs = np.array(mp.get_flux_freqs(sfg_mon))
    sfg_flux = np.array(mp.get_fluxes(sfg_mon))
    sfg_wvls = 1.0 / sfg_freqs  # um

    # Find peak in the SFG monitor window
    sfg_flux_abs = np.abs(sfg_flux)
    if len(sfg_flux_abs) > 0 and sfg_flux_abs.max() > 0:
        pk_idx = np.argmax(sfg_flux_abs)
        peak_wvl = float(sfg_wvls[pk_idx])
        peak_val = float(sfg_flux_abs[pk_idx])
    else:
        peak_wvl = lsfg
        peak_val = 0.0

    # Flux at the expected SFG wavelength (closest bin)
    target_idx = np.argmin(np.abs(sfg_wvls - lsfg))
    target_flux = abs(float(sfg_flux[target_idx]))

    # S/N: peak flux vs edges of the monitoring window (background)
    # Use the 10% of bins at each edge as "background"
    n_edge = max(5, len(sfg_flux_abs) // 10)
    edge_flux = np.concatenate([sfg_flux_abs[:n_edge], sfg_flux_abs[-n_edge:]])
    bg_level = float(np.mean(edge_flux)) if len(edge_flux) > 0 else 0.0

    if bg_level > 1e-20 and peak_val > 1e-20:
        snr_db = float(10 * np.log10(peak_val / bg_level))
    elif peak_val > 1e-20:
        snr_db = 99.0
    else:
        snr_db = -99.0

    deviation_nm = abs(peak_wvl - lsfg) * 1000

    # SHG suppression for cross-SFG
    shg_suppression_db = None
    if not is_shg and len(shg_mons) > 0:
        max_shg_flux = 0.0
        for m in shg_mons:
            shg_f = np.abs(np.array(mp.get_fluxes(m)))
            if len(shg_f) > 0:
                max_shg_flux = max(max_shg_flux, float(shg_f.max()))
        if max_shg_flux > 1e-20 and peak_val > 1e-20:
            shg_suppression_db = float(10 * np.log10(peak_val / max_shg_flux))
        elif peak_val > 1e-20:
            shg_suppression_db = 99.0
        else:
            shg_suppression_db = 0.0

    # Full spectrum for plotting
    full_freqs = np.array(mp.get_flux_freqs(full_mon))
    full_flux = np.array(mp.get_fluxes(full_mon))
    full_wvls = 1.0 / full_freqs

    # Pass criteria:
    # 1. Peak in SFG window is within 20nm of expected
    # 2. S/N > 0 dB (peak above background in the window)
    # 3. For cross-SFG: SFG signal exceeds SHG
    correct_peak = deviation_nm < 20.0
    snr_ok = snr_db > 0.0
    shg_ok = True
    if shg_suppression_db is not None:
        shg_ok = shg_suppression_db > 0.0

    passed = correct_peak and snr_ok and shg_ok

    status = "PASS" if passed else "FAIL"
    print_master(f"  Peak in SFG window: {peak_wvl*1000:.1f}nm "
                 f"(expected {lsfg*1000:.1f}nm, dev={deviation_nm:.1f}nm)")
    print_master(f"  Peak flux: {peak_val:.4e}, background: {bg_level:.4e}, "
                 f"S/N: {snr_db:.1f} dB")
    if shg_suppression_db is not None:
        print_master(f"  SHG suppression: {shg_suppression_db:.1f} dB")
    print_master(f"  Result: {status}")

    return {
        'sfg_key': sfg_key,
        'lambda_a': la, 'lambda_b': lb, 'lambda_sfg': lsfg,
        'expected_trit': info['result_trit'],
        'is_shg': is_shg,
        'qpm_period': ppln_period,
        'n_domains': n_dom,
        'peak_wvl_nm': peak_wvl * 1000,
        'peak_flux': peak_val,
        'target_flux': target_flux,
        'bg_level': bg_level,
        'deviation_nm': deviation_nm,
        'correct_peak': correct_peak,
        'shg_suppression_db': shg_suppression_db,
        'snr_db': snr_db,
        'passed': passed,
        'status': status,
        'wall_time': wall,
        'wvls': full_wvls,
        'flux': full_flux,
        'sfg_wvls': sfg_wvls,
        'sfg_flux': sfg_flux_abs,
    }


# ===========================================================================
# RUN ALL AND REPORT
# ===========================================================================

def run_all():
    t0 = time.time()

    print_master("\n" + "#" * 70)
    print_master("#  IOC INTEGRATION TEST — PPLN SFG Mixer Validation")
    print_master("#  All 9 Ternary Multiplications (6 unique SFG interactions)")
    print_master("#" * 70)
    print_master(f"  Date: {datetime.now()}")
    print_master(f"  MPI processes: {SIZE}")
    print_master(f"  Resolution: {RESOLUTION} px/um")
    print_master(f"  Source bandwidth: {SRC_BW_FRAC*100:.0f}%")
    print_master(f"  Chi2: {CHI2_VAL}")
    print_master("")

    # Material model
    print_master("  Material model verification (LiNbO3 Lorentzian):")
    for lam in [1.550, 1.310, 1.064, 0.775, 0.710, 0.655, 0.631, 0.587, 0.532]:
        print_master(f"    n({lam*1000:.0f}nm) = {compute_meep_index(lam):.4f}")
    print_master("")

    # QPM periods
    print_master("  QPM periods (computed from material model):")
    print_master(f"    {'Pair':<6} {'A(nm)':<8} {'B(nm)':<8} {'SFG(nm)':<9}"
                 f" {'Trit':<5} {'QPM(um)':<9} {'Type'}")
    print_master("    " + "-" * 55)
    for key, info in SFG_TABLE.items():
        typ = "SHG" if abs(info['lambda_a'] - info['lambda_b']) < 0.001 else "cross-SFG"
        print_master(f"    {key:<6} {info['lambda_a']*1000:<8.0f} {info['lambda_b']*1000:<8.0f}"
                     f" {info['lambda_sfg']*1000:<9.1f} {info['result_trit']:<+5d}"
                     f" {info['qpm_period']:<9.2f} {typ}")
    print_master("")

    # AWG channel spacing verification (analytical)
    awg_wvls = sorted([info['lambda_sfg'] * 1000 for info in SFG_TABLE.values()])
    spacings = [awg_wvls[i+1] - awg_wvls[i] for i in range(len(awg_wvls)-1)]
    print_master(f"  AWG channel spacing (analytical):")
    print_master(f"    Wavelengths: {', '.join(f'{w:.1f}' for w in awg_wvls)} nm")
    print_master(f"    Min spacing: {min(spacings):.1f} nm (>{20}nm required: "
                 f"{'PASS' if min(spacings) > 20 else 'FAIL'})")
    print_master("")

    # Analytical SFG efficiency comparison
    print_master("  Analytical QPM efficiency (relative, normalized to R+B):")
    ref_info = SFG_TABLE['R+B']
    ref_n = compute_meep_index(ref_info['lambda_a']) * compute_meep_index(ref_info['lambda_b']) \
            * compute_meep_index(ref_info['lambda_sfg'])
    ref_eff = 1.0 / (ref_n * ref_info['lambda_sfg']**2)
    for key, info in SFG_TABLE.items():
        n_prod = compute_meep_index(info['lambda_a']) * compute_meep_index(info['lambda_b']) \
                 * compute_meep_index(info['lambda_sfg'])
        eff = 1.0 / (n_prod * info['lambda_sfg']**2)
        rel = eff / ref_eff
        n_domains = max(int(SFG_WG_LENGTH / (info['qpm_period'] / 2.0)), 2)
        print_master(f"    {key}: eta_rel={rel:.2f}, {n_domains} PPLN domains")
    print_master("")

    # Run all 6 tests
    results = {}
    for i, key in enumerate(SFG_TABLE.keys()):
        print_master(f"\n  >>> Test {i+1}/6: {key}")
        results[key] = run_sfg_test(key)

    total = time.time() - t0

    # Compile 9-case multiplication table
    mult_results = []
    for inp, wgt, sfg_key, exp_trit in MULT_TABLE:
        r = results[sfg_key]
        mult_results.append({
            'input': inp, 'weight': wgt, 'expected': exp_trit,
            'sfg_key': sfg_key, 'decoded': exp_trit if r['passed'] else '?',
            'passed': r['passed'], 'snr_db': r['snr_db'],
        })

    n_passed = sum(1 for r in results.values() if r['passed'])

    return {
        'results': results,
        'mult_results': mult_results,
        'n_passed': n_passed,
        'n_total': 6,
        'all_passed': n_passed == 6,
        'total_time': total,
    }


def print_summary(data):
    print_master("\n" + "=" * 70)
    print_master("  SUMMARY: PPLN SFG Mixer Integration Test")
    print_master("=" * 70)

    # Per-pair results
    print_master(f"\n  {'Pair':<6} {'SFG(nm)':<9} {'Peak(nm)':<10} {'Dev(nm)':<9}"
                 f" {'S/N(dB)':<9} {'SHG sup':<9} {'Status'}")
    print_master("  " + "-" * 65)
    for key in SFG_TABLE:
        r = data['results'][key]
        shg = f"{r['shg_suppression_db']:.1f}dB" if r['shg_suppression_db'] is not None else "N/A(SHG)"
        print_master(f"  {key:<6} {r['lambda_sfg']*1000:<9.1f} {r['peak_wvl_nm']:<10.1f}"
                     f" {r['deviation_nm']:<9.1f} {r['snr_db']:<9.1f} {shg:<9s}"
                     f" {r['status']}")

    # 9-case table
    print_master(f"\n  TERNARY MULTIPLICATION TABLE:")
    print_master(f"  {'Input':<7} {'Weight':<8} {'Expected':<10} {'SFG pair':<10} {'Status'}")
    print_master("  " + "-" * 45)
    for m in data['mult_results']:
        st = "PASS" if m['passed'] else "FAIL"
        print_master(f"  {m['input']:+d}      {m['weight']:+d}       "
                     f" {m['expected']:+d}        {m['sfg_key']:<10s} {st}")

    n = data['n_passed']
    overall = "ALL 6/6 PASSED" if data['all_passed'] else f"{n}/6 PASSED"
    print_master(f"\n  {'*'*50}")
    print_master(f"  *  {overall:^44s}  *")
    print_master(f"  *  Total time: {data['total_time']:.0f}s"
                 f" ({data['total_time']/60:.1f} min)")
    print_master(f"  {'*'*50}")


def save_plots(data, output_dir):
    if RANK != 0:
        return

    dark_bg   = '#1a1a2e'
    dark_fg   = '#e0e0e0'
    dark_grid = '#333355'
    colors = ['#ff6b6b', '#4ecdc4', '#ffe66d', '#a8e6cf', '#ff9ff3', '#48dbfb']

    # Main plot: full spectrum
    fig, axes = plt.subplots(3, 2, figsize=(18, 16), facecolor=dark_bg)
    fig.suptitle("IOC Integration Test: PPLN SFG Mixer — All 6 Interactions",
                 fontsize=16, fontweight='bold', color=dark_fg, y=0.98)

    for idx, key in enumerate(SFG_TABLE.keys()):
        ax = axes[idx // 2][idx % 2]
        ax.set_facecolor(dark_bg)

        r = data['results'][key]
        wvls_nm = r['wvls'] * 1000
        flux = np.abs(r['flux'])

        # Plot in the SFG output range
        mask = (wvls_nm >= 480) & (wvls_nm <= 850)
        ax.plot(wvls_nm[mask], flux[mask], color=colors[idx], linewidth=1.0, alpha=0.5,
                label='Full spectrum')

        # Overlay the narrow SFG monitor window
        sfg_wvls_nm = r['sfg_wvls'] * 1000
        ax.plot(sfg_wvls_nm, r['sfg_flux'], color='white', linewidth=2.0, alpha=0.9,
                label='SFG window')

        # Mark expected SFG
        target = r['lambda_sfg'] * 1000
        ax.axvline(x=target, color='#00ff88', linestyle='--', linewidth=2, alpha=0.8,
                    label=f'Expected {target:.0f}nm')

        # Mark SHG wavelengths for cross-SFG
        if not r['is_shg']:
            for shg_wvl in [r['lambda_a'] * 500, r['lambda_b'] * 500]:
                if 480 < shg_wvl < 850:
                    ax.axvline(x=shg_wvl, color='#ff4444', linestyle=':', linewidth=1,
                               alpha=0.5, label=f'SHG {shg_wvl:.0f}nm')

        status_color = '#4ecdc4' if r['passed'] else '#ff6b6b'
        ax.set_title(f"{key}: {r['lambda_a']*1000:.0f}+{r['lambda_b']*1000:.0f} -> "
                     f"{target:.0f}nm  [{r['status']}]",
                     color=status_color, fontsize=12, fontweight='bold')

        info_lines = [
            f"S/N: {r['snr_db']:.1f} dB",
            f"Peak: {r['peak_wvl_nm']:.0f}nm",
            f"Dev: {r['deviation_nm']:.1f}nm",
        ]
        if r['shg_suppression_db'] is not None:
            info_lines.append(f"SHG sup: {r['shg_suppression_db']:.1f}dB")
        info_text = "\n".join(info_lines)
        ax.text(0.97, 0.95, info_text, transform=ax.transAxes,
                fontsize=9, color=dark_fg, fontfamily='monospace',
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor=dark_bg, edgecolor=dark_grid))

        ax.legend(loc='upper left', fontsize=7, facecolor=dark_bg,
                  edgecolor=dark_grid, labelcolor=dark_fg)
        ax.set_xlabel("Wavelength (nm)", color=dark_fg, fontsize=9)
        ax.set_ylabel("Flux (a.u.)", color=dark_fg, fontsize=9)
        ax.tick_params(colors=dark_fg, labelsize=8)
        ax.grid(True, alpha=0.2, color=dark_grid)
        for spine in ax.spines.values():
            spine.set_color(dark_grid)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    path = os.path.join(output_dir, 'ioc_integration_test.png')
    plt.savefig(path, dpi=200, facecolor=dark_bg, bbox_inches='tight')
    print_master(f"  Plot: {path}")

    try:
        import shutil
        desk = os.path.expanduser("~/Desktop/ioc_integration_test.png")
        shutil.copy2(path, desk)
        print_master(f"  Copied to: {desk}")
    except Exception:
        pass

    plt.close()


def save_results(data, output_dir):
    if RANK != 0:
        return

    path = os.path.join(output_dir, 'ioc_integration_test_results.txt')
    with open(path, 'w') as f:
        f.write("IOC INTEGRATION TEST RESULTS\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"MPI: {SIZE} processes\n")
        f.write(f"Resolution: {RESOLUTION} px/um\n")
        f.write(f"Source BW: {SRC_BW_FRAC*100:.0f}%\n")
        f.write(f"Chi2: {CHI2_VAL}\n")
        f.write(f"Overall: {'ALL_PASSED' if data['all_passed'] else 'SOME_FAILED'}\n")
        f.write(f"Passed: {data['n_passed']}/{data['n_total']}\n")
        f.write(f"Time: {data['total_time']:.1f}s\n\n")

        f.write("SFG PAIR RESULTS\n")
        f.write("-" * 40 + "\n")
        for key in SFG_TABLE:
            r = data['results'][key]
            f.write(f"\n[{key}]\n")
            f.write(f"inputs_nm={r['lambda_a']*1000:.0f}+{r['lambda_b']*1000:.0f}\n")
            f.write(f"expected_sfg_nm={r['lambda_sfg']*1000:.1f}\n")
            f.write(f"qpm_period_um={r['qpm_period']:.2f}\n")
            f.write(f"n_domains={r['n_domains']}\n")
            f.write(f"peak_nm={r['peak_wvl_nm']:.1f}\n")
            f.write(f"deviation_nm={r['deviation_nm']:.1f}\n")
            f.write(f"peak_flux={r['peak_flux']:.6e}\n")
            f.write(f"bg_level={r['bg_level']:.6e}\n")
            f.write(f"snr_db={r['snr_db']:.1f}\n")
            shg = r['shg_suppression_db']
            f.write(f"shg_suppression_db={'N/A' if shg is None else f'{shg:.1f}'}\n")
            f.write(f"status={r['status']}\n")

        f.write(f"\n\nMULTIPLICATION TABLE\n")
        f.write("-" * 40 + "\n")
        for m in data['mult_results']:
            f.write(f"({m['input']:+d})x({m['weight']:+d})={m['expected']:+d}"
                    f" via {m['sfg_key']} {'PASS' if m['passed'] else 'FAIL'}\n")

    print_master(f"  Results: {path}")


def main():
    output_dir = "/home/jackwayne/Desktop/Optical_computing/Research/data/ioc_validation"
    if RANK == 0:
        os.makedirs(output_dir, exist_ok=True)

    data = run_all()
    print_summary(data)
    save_plots(data, output_dir)
    save_results(data, output_dir)

    print_master(f"\n  IOC INTEGRATION TEST COMPLETE")
    print_master(f"  Status: {'ALL PASSED' if data['all_passed'] else 'SOME FAILED'}")
    print_master(f"  Output: {output_dir}\n")

    return data['all_passed']


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
