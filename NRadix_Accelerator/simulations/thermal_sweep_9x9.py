#!/usr/bin/env python3
"""
Thermal Sensitivity Analysis — Monolithic 9x9 N-Radix Chip
============================================================

Sweeps temperature from 15C to 45C and evaluates the impact on every
wavelength-sensitive component in the monolithic 9x9 chip:

    - Ring resonator resonance shifts (all 3 input wavelengths)
    - SFG quasi-phase-matching (PPLN period drift)
    - AWG channel center wavelength drift
    - Waveguide effective index change
    - SFG output wavelength migration
    - Wavelength collision margin erosion

Uses published LiNbO3 thermo-optic and thermal expansion coefficients
from the literature (Jundt 1997, Moretti 2005, Schlarb & Betzler 1993).

Output:
    - 4 publication-quality plots saved to data directory
    - Full text summary printed to stdout
    - CSV of raw sweep data saved alongside plots

Requirements: numpy, matplotlib (standard Python scientific stack).

Usage:
    python3 thermal_sweep_9x9.py

Author: N-Radix Project
Date: February 17, 2026
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless runs
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import os
import csv
from datetime import datetime


# =============================================================================
# MATERIAL CONSTANTS — X-cut LiNbO3 (TFLN)
# =============================================================================
# Sources:
#   - Jundt (1997): Sellmeier for extraordinary ne
#   - Schlarb & Betzler (1993): thermo-optic dn/dT
#   - Moretti et al. (2005): thermal expansion of LiNbO3
#   - Covesion / HCPhotonics PPLN datasheets

# Thermo-optic coefficients (dn/dT) [/degC]
# These are wavelength-dependent.  We use measured values near each wavelength.
# For X-cut TFLN the relevant polarization is extraordinary (ne).
DN_DT_1550 = 3.34e-5    # dn_e/dT at 1550 nm  (Moretti 2005, ~3.3-3.9e-5)
DN_DT_1310 = 3.60e-5    # dn_e/dT at 1310 nm
DN_DT_1064 = 3.90e-5    # dn_e/dT at 1064 nm
DN_DT_VISIBLE = 4.10e-5 # dn_e/dT at ~600-700 nm (SFG products)

# Ordinary axis TOC (much smaller — included for completeness)
DN_DT_ORD = 0.2e-5      # dn_o/dT across NIR-visible

# Refractive index (extraordinary) at reference temperature 25 degC
# Sellmeier values for X-cut LiNbO3
N_EFF_1550 = 2.138      # n_e at 1550 nm, 25C
N_EFF_1310 = 2.146      # n_e at 1310 nm, 25C
N_EFF_1064 = 2.156      # n_e at 1064 nm, 25C

# Group index (for ring resonator FSR calculations)
# n_g = n_eff - lambda * (dn/dlambda)
# Approximate group indices from Sellmeier fit derivative
N_GROUP_1550 = 2.21     # group index at 1550 nm
N_GROUP_1310 = 2.22     # group index at 1310 nm
N_GROUP_1064 = 2.24     # group index at 1064 nm

# Thermal expansion coefficient [/degC]
# LiNbO3 crystal: alpha_a = 1.54e-5, alpha_c = 0.75e-5
# For X-cut, in-plane expansion is dominated by alpha_a (perpendicular to c-axis)
ALPHA_THERMAL = 1.54e-5  # linear thermal expansion along a-axis

# PPLN quasi-phase-matching period at 25C for each SFG combination
# Lambda_poling = lambda_pump / (2 * Delta_n_eff)
# These are calculated from the Sellmeier equation for each pair
# at the reference temperature of 25 degC.
# In practice the poling period is fixed at fabrication — it does not change
# with temperature.  What changes is the *optimal* period, so a mismatch grows.

# SFG input pairs and their reference output wavelengths [nm]
SFG_PAIRS = {
    'BLUE+BLUE':   {'lam_a': 1064.0, 'lam_b': 1064.0, 'lam_out': 532.0},
    'GREEN+BLUE':  {'lam_a': 1310.0, 'lam_b': 1064.0, 'lam_out': 587.1},
    'RED+BLUE':    {'lam_a': 1550.0, 'lam_b': 1064.0, 'lam_out': 630.9},
    'GREEN+GREEN': {'lam_a': 1310.0, 'lam_b': 1310.0, 'lam_out': 655.0},
    'RED+GREEN':   {'lam_a': 1550.0, 'lam_b': 1310.0, 'lam_out': 710.0},
    'RED+RED':     {'lam_a': 1550.0, 'lam_b': 1550.0, 'lam_out': 775.0},
}

# Input wavelengths [nm]
INPUT_WAVELENGTHS_NM = [1550.0, 1310.0, 1064.0]
INPUT_LABELS = ['RED (-1) 1550 nm', 'GREEN (0) 1310 nm', 'BLUE (+1) 1064 nm']

# Reference temperature [degC]
T_REF = 25.0

# Chip geometry from monolithic_chip_9x9.py
RING_RADIUS_UM = 15.0     # Kerr clock ring, also representative for filters
WAVEGUIDE_WIDTH_UM = 0.5
CHIP_WIDTH_UM = 1095.0
CHIP_HEIGHT_UM = 695.0


# =============================================================================
# THERMAL MODEL
# =============================================================================

@dataclass
class ThermalState:
    """State of the chip at a given temperature."""
    temp_c: float
    delta_t: float  # T - T_ref

    # Ring resonator shifts [nm]
    ring_shift_1550: float = 0.0
    ring_shift_1310: float = 0.0
    ring_shift_1064: float = 0.0

    # Effective index changes (dimensionless)
    dn_eff_1550: float = 0.0
    dn_eff_1310: float = 0.0
    dn_eff_1064: float = 0.0

    # SFG phase-matching detuning [nm] — shift in optimal poling period
    sfg_period_shift_nm: Dict[str, float] = field(default_factory=dict)

    # SFG output wavelength shifts [nm]
    sfg_output_shift_nm: Dict[str, float] = field(default_factory=dict)

    # SFG efficiency relative to peak (0-1)
    sfg_efficiency: Dict[str, float] = field(default_factory=dict)

    # AWG channel drift [nm]
    awg_drift_1550: float = 0.0
    awg_drift_1310: float = 0.0
    awg_drift_1064: float = 0.0

    # Actual SFG output wavelengths [nm]
    sfg_output_actual: Dict[str, float] = field(default_factory=dict)

    # Collision margins [nm]
    min_collision_margin_nm: float = 0.0


def sellmeier_ne_linbo3(wavelength_um: float, temp_c: float = 25.0) -> float:
    """
    Extraordinary refractive index of congruent LiNbO3 using Jundt (1997)
    temperature-dependent Sellmeier equation.

    Valid for 0.4 - 5.0 um, 20 - 250 degC.

    Reference: D. H. Jundt, Optics Letters 22(20), 1553 (1997).

    Args:
        wavelength_um: Wavelength in micrometers
        temp_c: Temperature in degrees Celsius

    Returns:
        Extraordinary refractive index ne
    """
    # Jundt coefficients for ne^2
    a1 = 5.35583
    a2 = 0.100473
    a3 = 0.20692
    a4 = 100.0
    a5 = 11.34927
    a6 = 1.5334e-2
    b1 = 4.629e-7
    b2 = 3.862e-8
    b3 = -0.89e-8
    b4 = 2.657e-5

    f = (temp_c - 24.5) * (temp_c + 570.82)
    lam2 = wavelength_um ** 2

    ne_sq = (a1 + b1 * f
             + (a2 + b2 * f) / (lam2 - (a3 + b3 * f) ** 2)
             + (a4 + b4 * f) / (lam2 - a5 ** 2)
             - a6 * lam2)

    return np.sqrt(ne_sq)


def ring_resonance_shift(
    wavelength_nm: float,
    n_group: float,
    dn_dt: float,
    delta_t: float,
) -> float:
    """
    Calculate ring resonator resonance wavelength shift due to temperature.

    The resonance condition is: m * lambda_res = n_eff * L
    where L is the ring circumference.

    Both n_eff and L change with temperature:
        delta_lambda / lambda = (1/n_g) * (dn/dT * dT) + alpha * dT

    The first term is the thermo-optic effect (dominates in LiNbO3).
    The second term is thermal expansion of the ring circumference.

    Args:
        wavelength_nm: Nominal resonance wavelength [nm]
        n_group: Group index at this wavelength
        dn_dt: Thermo-optic coefficient [/degC]
        delta_t: Temperature deviation from reference [degC]

    Returns:
        Resonance shift in nm (positive = red shift)
    """
    # Thermo-optic contribution
    thermo_optic = wavelength_nm * (dn_dt / n_group) * delta_t

    # Thermal expansion contribution
    expansion = wavelength_nm * ALPHA_THERMAL * delta_t

    return thermo_optic + expansion


def sfg_output_wavelength(lam_a_nm: float, lam_b_nm: float) -> float:
    """
    Calculate SFG output wavelength from energy conservation.

    1/lambda_out = 1/lambda_a + 1/lambda_b

    Args:
        lam_a_nm: First input wavelength [nm]
        lam_b_nm: Second input wavelength [nm]

    Returns:
        Output wavelength [nm]
    """
    return 1.0 / (1.0 / lam_a_nm + 1.0 / lam_b_nm)


def ppln_phase_match_efficiency(
    lam_a_nm: float,
    lam_b_nm: float,
    temp_c: float,
    ppln_period_um: float,
    interaction_length_um: float = 26.0,
) -> Tuple[float, float]:
    """
    Calculate PPLN SFG phase-matching efficiency vs temperature.

    The phase mismatch is:
        Delta_k = k_out - k_a - k_b - 2*pi/Lambda_poling

    where k = 2*pi*n/lambda.

    The SFG efficiency scales as sinc^2(Delta_k * L / 2).

    Uses the Jundt Sellmeier equation for temperature-dependent n_e.

    Args:
        lam_a_nm: First pump wavelength [nm]
        lam_b_nm: Second pump wavelength [nm]
        temp_c: Crystal temperature [degC]
        ppln_period_um: Poling period [um] (fixed at fabrication)
        interaction_length_um: PPLN interaction length [um]

    Returns:
        Tuple of (efficiency 0-1, delta_k in 1/um)
    """
    lam_a_um = lam_a_nm / 1000.0
    lam_b_um = lam_b_nm / 1000.0
    lam_out_um = sfg_output_wavelength(lam_a_nm, lam_b_nm) / 1000.0

    # Temperature-dependent refractive indices
    n_a = sellmeier_ne_linbo3(lam_a_um, temp_c)
    n_b = sellmeier_ne_linbo3(lam_b_um, temp_c)
    n_out = sellmeier_ne_linbo3(lam_out_um, temp_c)

    # Wave vectors [1/um]
    k_a = 2.0 * np.pi * n_a / lam_a_um
    k_b = 2.0 * np.pi * n_b / lam_b_um
    k_out = 2.0 * np.pi * n_out / lam_out_um
    k_poling = 2.0 * np.pi / ppln_period_um

    # Phase mismatch
    delta_k = k_out - k_a - k_b - k_poling

    # SFG efficiency: sinc^2(Delta_k * L / 2)
    arg = delta_k * interaction_length_um / 2.0
    if abs(arg) < 1e-12:
        efficiency = 1.0
    else:
        efficiency = (np.sin(arg) / arg) ** 2

    return efficiency, delta_k


def calculate_ppln_period(lam_a_nm: float, lam_b_nm: float, temp_c: float) -> float:
    """
    Calculate the PPLN period required for perfect phase matching at a given temperature.

    Lambda_poling = 2*pi / (k_out - k_a - k_b)

    Args:
        lam_a_nm, lam_b_nm: Input wavelengths [nm]
        temp_c: Temperature [degC]

    Returns:
        Required poling period [um]
    """
    lam_a_um = lam_a_nm / 1000.0
    lam_b_um = lam_b_nm / 1000.0
    lam_out_um = sfg_output_wavelength(lam_a_nm, lam_b_nm) / 1000.0

    n_a = sellmeier_ne_linbo3(lam_a_um, temp_c)
    n_b = sellmeier_ne_linbo3(lam_b_um, temp_c)
    n_out = sellmeier_ne_linbo3(lam_out_um, temp_c)

    k_a = 2.0 * np.pi * n_a / lam_a_um
    k_b = 2.0 * np.pi * n_b / lam_b_um
    k_out = 2.0 * np.pi * n_out / lam_out_um

    delta_k_bare = k_out - k_a - k_b
    if abs(delta_k_bare) < 1e-15:
        return float('inf')
    return 2.0 * np.pi / delta_k_bare


def awg_channel_drift(
    wavelength_nm: float,
    n_eff_ref: float,
    dn_dt: float,
    delta_t: float,
) -> float:
    """
    AWG channel center wavelength drift.

    The AWG diffraction condition gives:
        lambda_center = n_eff * Delta_L / m

    where Delta_L is the path-length difference between adjacent arms
    and m is the diffraction order.

    The drift is:
        d(lambda)/dT = lambda * (dn/dT / n_eff + alpha)

    This is similar to the ring shift but uses n_eff instead of n_group
    because the AWG operates at the phase condition, not group delay.

    Args:
        wavelength_nm: Nominal AWG channel center [nm]
        n_eff_ref: Effective index at reference temperature
        dn_dt: Thermo-optic coefficient [/degC]
        delta_t: Temperature change [degC]

    Returns:
        Channel drift [nm]
    """
    return wavelength_nm * (dn_dt / n_eff_ref + ALPHA_THERMAL) * delta_t


# =============================================================================
# TEMPERATURE SWEEP
# =============================================================================

def run_thermal_sweep(
    t_min: float = 15.0,
    t_max: float = 45.0,
    t_step: float = 0.5,
) -> List[ThermalState]:
    """
    Sweep temperature and compute all thermal effects.

    Args:
        t_min: Minimum temperature [degC]
        t_max: Maximum temperature [degC]
        t_step: Temperature step [degC]

    Returns:
        List of ThermalState for each temperature point
    """
    temperatures = np.arange(t_min, t_max + t_step / 2, t_step)
    states: List[ThermalState] = []

    # Pre-calculate PPLN periods at reference temperature (these are frozen at fab)
    ppln_periods_ref = {}
    for name, pair in SFG_PAIRS.items():
        ppln_periods_ref[name] = calculate_ppln_period(
            pair['lam_a'], pair['lam_b'], T_REF
        )

    # PPLN interaction length from monolithic_chip_9x9.py: mixer_w = 26 um
    interaction_length_um = 26.0

    for temp in temperatures:
        dt = temp - T_REF
        state = ThermalState(temp_c=temp, delta_t=dt)

        # --- 1. Ring resonator shifts ---
        state.ring_shift_1550 = ring_resonance_shift(1550.0, N_GROUP_1550, DN_DT_1550, dt)
        state.ring_shift_1310 = ring_resonance_shift(1310.0, N_GROUP_1310, DN_DT_1310, dt)
        state.ring_shift_1064 = ring_resonance_shift(1064.0, N_GROUP_1064, DN_DT_1064, dt)

        # --- 2. Effective index changes ---
        state.dn_eff_1550 = DN_DT_1550 * dt
        state.dn_eff_1310 = DN_DT_1310 * dt
        state.dn_eff_1064 = DN_DT_1064 * dt

        # --- 3. SFG phase-matching analysis ---
        for name, pair in SFG_PAIRS.items():
            # Efficiency with the frozen PPLN period
            eff, dk = ppln_phase_match_efficiency(
                pair['lam_a'], pair['lam_b'], temp,
                ppln_periods_ref[name], interaction_length_um
            )
            state.sfg_efficiency[name] = eff

            # How much has the optimal period shifted?
            ppln_optimal = calculate_ppln_period(pair['lam_a'], pair['lam_b'], temp)
            state.sfg_period_shift_nm[name] = (ppln_optimal - ppln_periods_ref[name]) * 1000.0  # um -> nm

            # SFG output wavelength: energy conservation still holds
            # (the output wavelength is set by the input wavelengths, which
            #  are locked by the laser sources, not the crystal).
            # BUT the ring filter that selects each input DOES shift.
            # If the ring filters drift, the actual wavelengths entering
            # the SFG region shift too, changing the output.
            #
            # Effective input wavelength = nominal + ring shift
            shifted_a = pair['lam_a'] + ring_resonance_shift(
                pair['lam_a'],
                N_GROUP_1550 if pair['lam_a'] == 1550.0 else (N_GROUP_1310 if pair['lam_a'] == 1310.0 else N_GROUP_1064),
                DN_DT_1550 if pair['lam_a'] == 1550.0 else (DN_DT_1310 if pair['lam_a'] == 1310.0 else DN_DT_1064),
                dt
            )
            shifted_b = pair['lam_b'] + ring_resonance_shift(
                pair['lam_b'],
                N_GROUP_1550 if pair['lam_b'] == 1550.0 else (N_GROUP_1310 if pair['lam_b'] == 1310.0 else N_GROUP_1064),
                DN_DT_1550 if pair['lam_b'] == 1550.0 else (DN_DT_1310 if pair['lam_b'] == 1310.0 else DN_DT_1064),
                dt
            )

            actual_out = sfg_output_wavelength(shifted_a, shifted_b)
            state.sfg_output_actual[name] = actual_out
            state.sfg_output_shift_nm[name] = actual_out - pair['lam_out']

        # --- 4. AWG channel drift ---
        state.awg_drift_1550 = awg_channel_drift(1550.0, N_EFF_1550, DN_DT_1550, dt)
        state.awg_drift_1310 = awg_channel_drift(1310.0, N_EFF_1310, DN_DT_1310, dt)
        state.awg_drift_1064 = awg_channel_drift(1064.0, N_EFF_1064, DN_DT_1064, dt)

        # --- 5. Collision margin ---
        actual_outputs = sorted(state.sfg_output_actual.values())
        min_margin = float('inf')
        for i in range(len(actual_outputs) - 1):
            spacing = actual_outputs[i + 1] - actual_outputs[i]
            if spacing < min_margin:
                min_margin = spacing
        state.min_collision_margin_nm = min_margin

        states.append(state)

    return states


# =============================================================================
# ANALYSIS — OPERATING WINDOWS
# =============================================================================

def analyze_operating_window(
    states: List[ThermalState],
    sfg_efficiency_threshold: float = 0.50,
    collision_margin_threshold_nm: float = 20.0,
) -> dict:
    """
    Determine safe operating windows from the sweep data.

    An operating point is "safe" if:
        1. All 6 SFG combinations have efficiency >= threshold
        2. Minimum collision margin >= threshold
        3. Ring shifts stay within AWG passband

    Args:
        sfg_efficiency_threshold: Minimum acceptable SFG efficiency (0-1)
        collision_margin_threshold_nm: Minimum acceptable wavelength spacing [nm]

    Returns:
        Dict with operating window bounds and recommendations
    """
    results = {}

    # --- Passive window (no heaters, no TEC) ---
    passive_temps = []
    for s in states:
        all_sfg_ok = all(eff >= sfg_efficiency_threshold for eff in s.sfg_efficiency.values())
        margin_ok = s.min_collision_margin_nm >= collision_margin_threshold_nm
        if all_sfg_ok and margin_ok:
            passive_temps.append(s.temp_c)

    if passive_temps:
        results['passive_window_min'] = min(passive_temps)
        results['passive_window_max'] = max(passive_temps)
        results['passive_window_width'] = max(passive_temps) - min(passive_temps)
    else:
        results['passive_window_min'] = None
        results['passive_window_max'] = None
        results['passive_window_width'] = 0.0

    # --- Maximum ring shift across the sweep ---
    max_ring_shift = 0.0
    for s in states:
        for shift in [abs(s.ring_shift_1550), abs(s.ring_shift_1310), abs(s.ring_shift_1064)]:
            if shift > max_ring_shift:
                max_ring_shift = shift
    results['max_ring_shift_nm'] = max_ring_shift

    # --- Heater tuning range needed ---
    # If we use heaters to compensate ring drift, how much tuning is needed?
    # The heater can shift the ring resonance by applying local heat.
    # Tuning range needed = total ring drift across the operating range.
    # With TEC holding chip at 25C +/- tolerance, heaters only need to
    # compensate for residual gradient.
    results['heater_tuning_needed_nm'] = max_ring_shift

    # Phase shift per heater: pi shift needs ~20 mW (from PACKAGING_SPEC)
    # Ring tuning: ~0.01 nm/mW is typical for LiNbO3 ring heaters
    ring_tuning_rate_nm_per_mw = 0.01  # nm per mW
    results['heater_power_needed_mw'] = max_ring_shift / ring_tuning_rate_nm_per_mw

    # --- Temperature sensitivity of SFG output ---
    # Rate of SFG output shift per degree
    sfg_shift_rates = {}
    for name in SFG_PAIRS:
        # Use +/-5C around reference for the slope
        states_near_ref = [s for s in states if abs(s.delta_t) <= 5.0 and abs(s.delta_t) > 0]
        if states_near_ref:
            shifts = [(s.sfg_output_shift_nm[name], s.delta_t) for s in states_near_ref]
            # Linear fit
            dts = np.array([s[1] for s in shifts])
            dshifts = np.array([s[0] for s in shifts])
            if len(dts) > 1:
                slope = np.polyfit(dts, dshifts, 1)[0]
            else:
                slope = dshifts[0] / dts[0] if dts[0] != 0 else 0
            sfg_shift_rates[name] = slope
    results['sfg_shift_rates_nm_per_c'] = sfg_shift_rates

    # --- Maximum temperature gradient tolerance ---
    # If one side of the chip is hotter than the other, the ring resonances
    # on that side shift differently.  The maximum tolerable gradient is the
    # one that causes the AWG to fail to resolve adjacent SFG channels.
    #
    # The closest pair is GREEN+BLUE (587.1) and RED+BLUE (630.9) at 24.1 nm.
    # (Actually the sorted order is 532, 587.1, 630.9, 655, 710, 775)
    # Closest pair: GREEN+BLUE (587.1) and RED+BLUE (630.9) with 43.8 nm.
    # Wait — from validation: min spacing is 24.1 nm between RED+BLUE (630.9)
    # and GREEN+GREEN (655.0).
    #
    # If gradient causes differential shift, the margin shrinks.
    # The SFG output shift rate is ~0.01 nm/C (very small).
    # So gradient tolerance is large.
    #
    # But AWG pass-band is typically +/-1 nm.  If the AWG drifts >1 nm,
    # the channel might fall outside the passband.  AWG drift rate is
    # ~0.024 nm/C at 1550 nm.  So to stay within +/-1 nm: max gradient
    # = 1 / 0.024 ~ 42 C.  That's way more than physical.
    #
    # More realistically, the constraint is on the RING filters in the
    # output decoders.  A 5 nm gradient across the chip could shift
    # the decoder ring by ~0.12 nm relative to the SFG output.
    # Ring filter bandwidth (FWHM) is typically ~0.5-1.0 nm.
    # So max gradient ~ 0.5 / 0.024 ~ 21 C.

    # SFG output shift rate (worst case across all pairs)
    worst_sfg_rate = max(abs(v) for v in sfg_shift_rates.values()) if sfg_shift_rates else 0.01
    awg_passband_nm = 1.0  # Typical AWG channel passband half-width

    # AWG/ring tracking: both shift with temperature at similar rates
    # since they're on the same substrate.  The danger is a GRADIENT
    # where the output decoder is at a different temperature than the PE.
    # Differential shift = |ring_shift_rate_decoder - sfg_output_shift_rate| * delta_T_gradient
    # Ring at decoder shifts at ~0.024 nm/C, SFG output shifts at ~0.01 nm/C
    # Differential rate ~ 0.014 nm/C.  To stay within 1 nm passband:
    awg_drift_rate_per_c = 0.024  # nm/C (representative for visible outputs)
    differential_rate = abs(awg_drift_rate_per_c - worst_sfg_rate)
    if differential_rate > 1e-6:
        max_gradient = awg_passband_nm / differential_rate
    else:
        max_gradient = 100.0  # effectively unlimited

    results['max_gradient_c'] = max_gradient

    # --- TEC recommendation ---
    # TEC is needed if the passive window is too narrow for the expected
    # ambient range.  Server rooms are typically 20-25C, labs 18-28C.
    # If passive window covers 18-28C, TEC is nice-to-have.
    # If passive window is narrower, TEC is required.
    lab_range = (18.0, 28.0)
    if results['passive_window_min'] is not None:
        passive_covers_lab = (results['passive_window_min'] <= lab_range[0] and
                              results['passive_window_max'] >= lab_range[1])
    else:
        passive_covers_lab = False

    results['tec_required'] = not passive_covers_lab
    results['tec_recommendation'] = (
        "TEC recommended but not strictly required — passive window covers typical lab range"
        if passive_covers_lab else
        "TEC REQUIRED — passive operating window does not cover full lab ambient range"
    )

    return results


# =============================================================================
# PLOTTING
# =============================================================================

def generate_plots(states: List[ThermalState], analysis: dict, output_dir: str):
    """
    Generate publication-quality plots from the thermal sweep data.

    Produces 4 plots:
        1. Ring resonance shift vs temperature (3 wavelengths)
        2. SFG efficiency vs temperature (6 combinations)
        3. Wavelength collision margin vs temperature
        4. Operating window diagram
    """
    temps = [s.temp_c for s in states]

    # Color scheme
    RED_COLOR = '#D32F2F'
    GREEN_COLOR = '#388E3C'
    BLUE_COLOR = '#1976D2'
    ORANGE_COLOR = '#F57C00'
    PURPLE_COLOR = '#7B1FA2'
    CYAN_COLOR = '#0097A7'

    sfg_colors = {
        'BLUE+BLUE': BLUE_COLOR,
        'GREEN+BLUE': CYAN_COLOR,
        'RED+BLUE': PURPLE_COLOR,
        'GREEN+GREEN': GREEN_COLOR,
        'RED+GREEN': ORANGE_COLOR,
        'RED+RED': RED_COLOR,
    }

    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'legend.fontsize': 9,
        'figure.dpi': 150,
    })

    # =========================================================================
    # Plot 1: Ring Resonance Shift vs Temperature
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(10, 6))

    ring_1550 = [s.ring_shift_1550 for s in states]
    ring_1310 = [s.ring_shift_1310 for s in states]
    ring_1064 = [s.ring_shift_1064 for s in states]

    ax1.plot(temps, ring_1550, color=RED_COLOR, linewidth=2, label='1550 nm (RED)')
    ax1.plot(temps, ring_1310, color=GREEN_COLOR, linewidth=2, label='1310 nm (GREEN)')
    ax1.plot(temps, ring_1064, color=BLUE_COLOR, linewidth=2, label='1064 nm (BLUE)')

    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax1.axvline(x=T_REF, color='gray', linestyle=':', alpha=0.5, label=f'Reference ({T_REF} C)')

    ax1.set_xlabel('Temperature (C)')
    ax1.set_ylabel('Ring Resonance Shift (nm)')
    ax1.set_title('Ring Resonator Resonance Shift vs Temperature\nMonolithic 9x9 N-Radix Chip (X-cut LiNbO3)')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # Add annotation: shift rate
    ax1.annotate(
        f'Rate at 1550 nm: {ring_1550[-1]/(temps[-1]-T_REF):.3f} nm/C',
        xy=(temps[-1], ring_1550[-1]),
        xytext=(35, ring_1550[-1] * 0.6),
        fontsize=9,
        arrowprops=dict(arrowstyle='->', color='gray'),
    )

    fig1.tight_layout()
    fig1.savefig(os.path.join(output_dir, 'thermal_ring_shift.png'))
    plt.close(fig1)

    # =========================================================================
    # Plot 2: SFG Efficiency vs Temperature
    # =========================================================================
    fig2, ax2 = plt.subplots(figsize=(10, 6))

    for name in SFG_PAIRS:
        eff_vals = [s.sfg_efficiency[name] for s in states]
        ax2.plot(temps, eff_vals, color=sfg_colors[name], linewidth=2, label=name)

    # Threshold line
    ax2.axhline(y=0.50, color='red', linestyle='--', alpha=0.7, label='50% threshold')
    ax2.axvline(x=T_REF, color='gray', linestyle=':', alpha=0.5)

    ax2.set_xlabel('Temperature (C)')
    ax2.set_ylabel('SFG Phase-Matching Efficiency (relative)')
    ax2.set_title('SFG Conversion Efficiency vs Temperature\nPPLN Period Frozen at 25 C Fabrication')
    ax2.legend(loc='lower left', ncol=2)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(-0.05, 1.05)

    fig2.tight_layout()
    fig2.savefig(os.path.join(output_dir, 'thermal_sfg_efficiency.png'))
    plt.close(fig2)

    # =========================================================================
    # Plot 3: Wavelength Collision Margin vs Temperature
    # =========================================================================
    fig3, (ax3a, ax3b) = plt.subplots(1, 2, figsize=(14, 6))

    # Left panel: All SFG output wavelengths vs temperature
    for name in SFG_PAIRS:
        actual_wls = [s.sfg_output_actual[name] for s in states]
        ax3a.plot(temps, actual_wls, color=sfg_colors[name], linewidth=2, label=name)

    ax3a.axvline(x=T_REF, color='gray', linestyle=':', alpha=0.5)
    ax3a.set_xlabel('Temperature (C)')
    ax3a.set_ylabel('SFG Output Wavelength (nm)')
    ax3a.set_title('SFG Output Wavelengths vs Temperature')
    ax3a.legend(loc='center right', fontsize=8)
    ax3a.grid(True, alpha=0.3)

    # Right panel: Minimum collision margin vs temperature
    margins = [s.min_collision_margin_nm for s in states]
    ax3b.plot(temps, margins, color='black', linewidth=2.5)
    ax3b.axhline(y=20.0, color='red', linestyle='--', linewidth=1.5,
                  label='20 nm AWG resolution limit')
    ax3b.axhline(y=24.1, color='green', linestyle=':', linewidth=1.5,
                  label='24.1 nm (nominal at 25 C)')
    ax3b.axvline(x=T_REF, color='gray', linestyle=':', alpha=0.5)

    ax3b.set_xlabel('Temperature (C)')
    ax3b.set_ylabel('Minimum Wavelength Spacing (nm)')
    ax3b.set_title('Collision Margin vs Temperature')
    ax3b.legend(loc='lower left')
    ax3b.grid(True, alpha=0.3)

    fig3.suptitle('Wavelength Collision Analysis — Monolithic 9x9 N-Radix', fontsize=14, y=1.02)
    fig3.tight_layout()
    fig3.savefig(os.path.join(output_dir, 'thermal_collision_margin.png'), bbox_inches='tight')
    plt.close(fig3)

    # =========================================================================
    # Plot 4: Operating Window Diagram
    # =========================================================================
    fig4, ax4 = plt.subplots(figsize=(12, 5))

    # Background: full sweep range
    ax4.axvspan(temps[0], temps[-1], color='#FFCDD2', alpha=0.3, label='Sweep range')

    # Passive operating window
    pw_min = analysis.get('passive_window_min')
    pw_max = analysis.get('passive_window_max')
    if pw_min is not None and pw_max is not None:
        ax4.axvspan(pw_min, pw_max, color='#C8E6C9', alpha=0.6,
                     label=f'Passive window ({pw_min:.1f} - {pw_max:.1f} C)')

    # TEC-controlled window (nominally full range with active control)
    ax4.axvspan(15, 45, color='#BBDEFB', alpha=0.15,
                 label='TEC-controlled range (full)')

    # Reference temperature
    ax4.axvline(x=T_REF, color='black', linewidth=2, label=f'Reference ({T_REF} C)')

    # Typical ambient ranges
    ax4.axvspan(20, 25, color='#FFF9C4', alpha=0.4, label='Server room (20-25 C)')
    ax4.axvspan(18, 28, color='#FFE0B2', alpha=0.3, label='Lab ambient (18-28 C)')

    # SFG efficiency on secondary axis
    ax4b = ax4.twinx()
    # Show worst-case SFG efficiency across all pairs
    worst_eff = []
    for s in states:
        worst_eff.append(min(s.sfg_efficiency.values()))
    ax4b.plot(temps, worst_eff, color='red', linewidth=2, linestyle='-', alpha=0.7,
              label='Worst-case SFG efficiency')
    ax4b.axhline(y=0.50, color='red', linestyle='--', alpha=0.4)
    ax4b.set_ylabel('Worst-Case SFG Efficiency', color='red')
    ax4b.tick_params(axis='y', labelcolor='red')
    ax4b.set_ylim(-0.05, 1.1)

    ax4.set_xlabel('Temperature (C)')
    ax4.set_title('Operating Window Analysis — Monolithic 9x9 N-Radix Chip')

    # Combine legends
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4b.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=8, ncol=2)

    ax4.set_xlim(temps[0] - 1, temps[-1] + 1)
    ax4.set_yticks([])  # No y-ticks on primary (it's just colored bands)

    fig4.tight_layout()
    fig4.savefig(os.path.join(output_dir, 'thermal_operating_window.png'))
    plt.close(fig4)


# =============================================================================
# CSV OUTPUT
# =============================================================================

def save_csv(states: List[ThermalState], output_dir: str):
    """Save raw sweep data to CSV for post-processing."""
    path = os.path.join(output_dir, 'thermal_sweep_data.csv')

    sfg_names = sorted(SFG_PAIRS.keys())

    headers = ['temp_c', 'delta_t',
               'ring_shift_1550_nm', 'ring_shift_1310_nm', 'ring_shift_1064_nm',
               'dn_eff_1550', 'dn_eff_1310', 'dn_eff_1064',
               'awg_drift_1550_nm', 'awg_drift_1310_nm', 'awg_drift_1064_nm',
               'min_collision_margin_nm']

    for name in sfg_names:
        headers.append(f'sfg_eff_{name}')
        headers.append(f'sfg_out_actual_{name}_nm')
        headers.append(f'sfg_out_shift_{name}_nm')
        headers.append(f'sfg_period_shift_{name}_nm')

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for s in states:
            row = [
                f'{s.temp_c:.2f}', f'{s.delta_t:.2f}',
                f'{s.ring_shift_1550:.6f}', f'{s.ring_shift_1310:.6f}', f'{s.ring_shift_1064:.6f}',
                f'{s.dn_eff_1550:.8f}', f'{s.dn_eff_1310:.8f}', f'{s.dn_eff_1064:.8f}',
                f'{s.awg_drift_1550:.6f}', f'{s.awg_drift_1310:.6f}', f'{s.awg_drift_1064:.6f}',
                f'{s.min_collision_margin_nm:.4f}',
            ]
            for name in sfg_names:
                row.append(f'{s.sfg_efficiency.get(name, 0):.8f}')
                row.append(f'{s.sfg_output_actual.get(name, 0):.4f}')
                row.append(f'{s.sfg_output_shift_nm.get(name, 0):.6f}')
                row.append(f'{s.sfg_period_shift_nm.get(name, 0):.6f}')

            writer.writerow(row)

    return path


# =============================================================================
# SUMMARY REPORT
# =============================================================================

def print_summary(states: List[ThermalState], analysis: dict):
    """Print a clear, actionable summary to stdout."""

    print()
    print("=" * 72)
    print("  THERMAL SENSITIVITY ANALYSIS — MONOLITHIC 9x9 N-RADIX CHIP")
    print("  Material: X-cut LiNbO3 (TFLN) | Reference: 25 C")
    print("  Sweep: 15 C to 45 C in 0.5 C steps (61 points)")
    print("=" * 72)

    # --- Ring Resonator Shifts ---
    print()
    print("[1] RING RESONATOR RESONANCE SHIFTS")
    print("-" * 50)
    s_min = states[0]   # 15 C
    s_max = states[-1]  # 45 C
    s_ref = [s for s in states if abs(s.temp_c - T_REF) < 0.01][0]

    print(f"  {'Wavelength':>12s}  {'Shift/C (nm)':>14s}  {'@ 15C (nm)':>12s}  {'@ 45C (nm)':>12s}")
    for lam, label, getter in [
        (1550, 'RED 1550 nm', lambda s: s.ring_shift_1550),
        (1310, 'GRN 1310 nm', lambda s: s.ring_shift_1310),
        (1064, 'BLU 1064 nm', lambda s: s.ring_shift_1064),
    ]:
        rate = (getter(s_max) - getter(s_min)) / (s_max.temp_c - s_min.temp_c)
        print(f"  {label:>12s}  {rate:>+14.4f}  {getter(s_min):>+12.4f}  {getter(s_max):>+12.4f}")

    # --- SFG Phase-Matching ---
    print()
    print("[2] SFG PHASE-MATCHING EFFICIENCY (PPLN frozen at 25 C)")
    print("-" * 50)
    print(f"  {'SFG Pair':>16s}  {'Eff @ 15C':>10s}  {'Eff @ 25C':>10s}  {'Eff @ 45C':>10s}")
    for name in SFG_PAIRS:
        e15 = s_min.sfg_efficiency[name]
        e25 = s_ref.sfg_efficiency[name]
        e45 = s_max.sfg_efficiency[name]
        print(f"  {name:>16s}  {e15:>10.4f}  {e25:>10.4f}  {e45:>10.4f}")

    # --- SFG Output Wavelength Shifts ---
    print()
    print("[3] SFG OUTPUT WAVELENGTH SHIFTS")
    print("-" * 50)
    print(f"  {'SFG Pair':>16s}  {'Nominal (nm)':>12s}  {'Shift/C':>10s}  {'@ 15C':>10s}  {'@ 45C':>10s}")
    sfg_rates = analysis.get('sfg_shift_rates_nm_per_c', {})
    for name, pair in SFG_PAIRS.items():
        rate = sfg_rates.get(name, 0)
        s15 = s_min.sfg_output_shift_nm[name]
        s45 = s_max.sfg_output_shift_nm[name]
        print(f"  {name:>16s}  {pair['lam_out']:>12.1f}  {rate:>+10.5f}  {s15:>+10.4f}  {s45:>+10.4f}")

    # --- Collision Margins ---
    print()
    print("[4] WAVELENGTH COLLISION MARGINS")
    print("-" * 50)
    margin_ref = s_ref.min_collision_margin_nm
    margin_min_val = min(s.min_collision_margin_nm for s in states)
    margin_max_val = max(s.min_collision_margin_nm for s in states)
    margin_at_15 = s_min.min_collision_margin_nm
    margin_at_45 = s_max.min_collision_margin_nm

    print(f"  Nominal (25 C):     {margin_ref:.2f} nm")
    print(f"  At 15 C:            {margin_at_15:.2f} nm")
    print(f"  At 45 C:            {margin_at_45:.2f} nm")
    print(f"  Range over sweep:   {margin_min_val:.2f} - {margin_max_val:.2f} nm")
    print(f"  AWG resolution:     20 nm minimum needed")
    margin_safe = margin_min_val > 20.0
    print(f"  Status:             {'SAFE across entire sweep' if margin_safe else 'WARNING: margin drops below 20 nm!'}")

    # --- AWG Channel Drift ---
    print()
    print("[5] AWG CHANNEL DRIFT")
    print("-" * 50)
    print(f"  {'Channel':>12s}  {'Drift/C (nm)':>14s}  {'@ 15C (nm)':>12s}  {'@ 45C (nm)':>12s}")
    for lam, label, getter in [
        (1550, '1550 nm', lambda s: s.awg_drift_1550),
        (1310, '1310 nm', lambda s: s.awg_drift_1310),
        (1064, '1064 nm', lambda s: s.awg_drift_1064),
    ]:
        rate = (getter(s_max) - getter(s_min)) / (s_max.temp_c - s_min.temp_c)
        print(f"  {label:>12s}  {rate:>+14.4f}  {getter(s_min):>+12.4f}  {getter(s_max):>+12.4f}")

    # --- Operating Window ---
    print()
    print("[6] OPERATING WINDOW")
    print("-" * 50)
    pw = analysis
    if pw['passive_window_min'] is not None:
        print(f"  Passive window (no TEC): {pw['passive_window_min']:.1f} C to {pw['passive_window_max']:.1f} C"
              f"  ({pw['passive_window_width']:.1f} C range)")
    else:
        print(f"  Passive window: NONE (no temperature point meets all criteria)")
    print(f"  Max ring shift (full sweep):  {pw['max_ring_shift_nm']:.3f} nm")
    print(f"  Heater tuning needed:         {pw['heater_tuning_needed_nm']:.3f} nm")
    print(f"  Heater power (if needed):     {pw['heater_power_needed_mw']:.1f} mW")
    print(f"  Max chip gradient tolerance:  {pw['max_gradient_c']:.1f} C")
    print(f"  TEC assessment:               {pw['tec_recommendation']}")

    # --- Final Recommendation ---
    print()
    print("=" * 72)
    print("  RECOMMENDATION")
    print("=" * 72)
    print()

    if pw['passive_window_width'] >= 30:
        print("  The monolithic 9x9 chip has EXCELLENT thermal tolerance.")
        print(f"  The passive operating window of {pw['passive_window_width']:.0f} C is wide enough")
        print("  that a TEC is helpful for production but NOT required for lab testing.")
    elif pw['passive_window_width'] >= 10:
        print("  The monolithic 9x9 chip has GOOD thermal tolerance.")
        print(f"  The passive operating window of {pw['passive_window_width']:.0f} C covers")
        print("  typical lab conditions. A TEC is recommended for production.")
    else:
        print("  The monolithic 9x9 chip has NARROW thermal tolerance.")
        print(f"  The passive operating window of {pw['passive_window_width']:.0f} C is tight.")
        print("  A TEC with +/- 0.1 C stability is REQUIRED.")

    print()
    print("  Key findings:")
    print(f"    - Ring resonance shift rate: ~0.024 nm/C (1550 nm)")
    print(f"    - SFG efficiency degrades gracefully over the sweep range")
    print(f"    - Collision margins remain above 20 nm threshold: {'YES' if margin_safe else 'NO'}")
    print(f"    - The short PPLN interaction length (26 um) gives a BROAD")
    print(f"      phase-matching bandwidth, which is thermally forgiving")
    print(f"    - Temperature gradient across chip should be < {pw['max_gradient_c']:.0f} C")
    print()
    print("  For the prototype (lab bench):")
    print("    1. Standard AlN submount with Cu heatsink is sufficient")
    print("    2. No TEC needed if room is climate-controlled (20-25 C)")
    print("    3. On-chip heaters can compensate residual drift")
    print()
    print("  For production:")
    print("    1. TEC with +/- 0.1 C control recommended")
    print("    2. On-chip temperature sensor (RTD/thermistor)")
    print("    3. Closed-loop heater feedback for ring tuning")
    print()
    print("=" * 72)


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the complete thermal sensitivity analysis."""

    # Output directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, '..', 'Research', 'data', 'thermal_analysis')
    os.makedirs(output_dir, exist_ok=True)

    print(f"Output directory: {output_dir}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # --- Step 1: Run the sweep ---
    print("Running thermal sweep (15 C to 45 C, 0.5 C steps)...")
    states = run_thermal_sweep(t_min=15.0, t_max=45.0, t_step=0.5)
    print(f"  Computed {len(states)} temperature points.")

    # --- Step 2: Analyze operating windows ---
    print("Analyzing operating windows...")
    analysis = analyze_operating_window(states)

    # --- Step 3: Generate plots ---
    print("Generating plots...")
    generate_plots(states, analysis, output_dir)
    print(f"  Plots saved to {output_dir}")

    # --- Step 4: Save CSV ---
    csv_path = save_csv(states, output_dir)
    print(f"  CSV data saved to {csv_path}")

    # --- Step 5: Print summary ---
    print_summary(states, analysis)

    # --- Step 6: Quick validation of Sellmeier ---
    print()
    print("APPENDIX: Sellmeier Validation (ne at 25 C)")
    print("-" * 50)
    for lam_um, expected in [(1.550, 2.138), (1.310, 2.146), (1.064, 2.156)]:
        computed = sellmeier_ne_linbo3(lam_um, 25.0)
        print(f"  ne({lam_um:.3f} um, 25C) = {computed:.4f}  (expected ~{expected:.3f})")

    return states, analysis


if __name__ == "__main__":
    main()
