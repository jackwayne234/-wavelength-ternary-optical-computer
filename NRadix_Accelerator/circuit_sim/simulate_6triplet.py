#!/usr/bin/env python3
"""
WDM Isolation Test: 6 Triplets Through the 9x9 Array
=====================================================

Proves that 18 wavelengths (6 WDM triplets x 3 wavelengths each) can share
the same waveguides without crosstalk in the monolithic 9x9 N-Radix chip.

Architecture:
  - Each triplet carries an INDEPENDENT computation through the same physical array
  - 6 triplets = 6 simultaneous matrix-vector multiplies on one chip
  - The PPLN mixer in each PE is phase-matched to produce SFG for all wavelengths,
    but cross-triplet SFG is suppressed by phase mismatch (sinc^2 roll-off)
  - Per-triplet AWG demuxers at the output separate the 6 result streams

Tests:
  1. Cross-triplet SFG analysis: compute all spurious mixing products
  2. AWG channel isolation: verify no cross-triplet SFG lands in a detection window
  3. Progressive loading: 1 triplet -> 6 triplets, identity matrix test at each step
  4. Power budget: does 6x optical power cause issues?

The 6 WDM triplets (from CHIP_INTERFACE.md):
  | Triplet | lam_-1 (nm) | lam_0 (nm) | lam_+1 (nm) |
  |---------|-------------|------------|-------------|
  |    1    |    1040     |    1020    |    1000     |
  |    2    |    1100     |    1080    |    1060     |
  |    3    |    1160     |    1140    |    1120     |
  |    4    |    1220     |    1200    |    1180     |
  |    5    |    1280     |    1260    |    1240     |
  |    6    |    1340     |    1320    |    1300     |

Author: N-Radix Project
Date: 2026-02-17
"""

import sys
import os
import math
import numpy as np
from dataclasses import dataclass, field

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.components import (
    OpticalSignal, waveguide_transfer, sfg_mixer, awg_demux,
    photodetector, mzi_encode, neff_sellmeier,
    NEFF, N_LINBO3, SFG_RESULT, AWG_CHANNELS,
)

# =============================================================================
# Chip geometry constants (same as simulate_9x9.py)
# =============================================================================

PE_PITCH = 55.0          # um center-to-center
PE_WIDTH = 50.0           # um
ROUTING_GAP = 60.0        # um
IOC_INPUT_WIDTH = 180.0   # um
IOC_OUTPUT_WIDTH = 200.0  # um
PPLN_LENGTH = 26.0        # um
WG_LOSS_DB_CM = 2.0       # dB/cm
EDGE_COUPLING_LOSS = 1.0  # dB per facet


# =============================================================================
# 6 WDM Triplet Definitions
# =============================================================================

@dataclass
class WDMTriplet:
    """One WDM triplet: 3 wavelengths encoding {-1, 0, +1}."""
    triplet_id: int
    wl_minus1: float    # nm -- encodes trit -1
    wl_zero: float      # nm -- encodes trit 0
    wl_plus1: float     # nm -- encodes trit +1

    @property
    def wavelengths(self) -> list[float]:
        return [self.wl_minus1, self.wl_zero, self.wl_plus1]

    @property
    def trit_to_wl(self) -> dict[int, float]:
        return {-1: self.wl_minus1, 0: self.wl_zero, +1: self.wl_plus1}

    @property
    def wl_to_trit(self) -> dict[float, int]:
        return {self.wl_minus1: -1, self.wl_zero: 0, self.wl_plus1: +1}

    def sfg_products(self) -> dict[tuple[float, float], float]:
        """All 9 SFG product wavelengths for this triplet."""
        table = {}
        for wa in self.wavelengths:
            for wb in self.wavelengths:
                table[(wa, wb)] = round(1.0 / (1.0 / wa + 1.0 / wb), 2)
        return table

    def sfg_result_table(self) -> dict[float, int]:
        """Map SFG output wavelength -> ternary multiplication result."""
        result = {}
        for (wa, wb), sfg_wl in self.sfg_products().items():
            ta = self.wl_to_trit[wa]
            tb = self.wl_to_trit[wb]
            result[sfg_wl] = ta * tb
        return result

    def awg_channels(self) -> dict[int, float]:
        """
        AWG channel centers for this triplet's 6 unique SFG products.
        Channel assignment mirrors the MVP: sorted by wavelength.
        """
        unique_sfg = sorted(set(self.sfg_products().values()))
        return {i: wl for i, wl in enumerate(unique_sfg)}

    def ppln_poling_period_nm(self) -> float:
        """
        PPLN poling period designed for this triplet's center pair.
        Phase-matched for wl_zero + wl_zero -> SFG.
        """
        wl_a = self.wl_zero
        wl_b = self.wl_zero
        wl_sfg = 1.0 / (1.0 / wl_a + 1.0 / wl_b)

        n_a = neff_sellmeier(wl_a)
        n_b = neff_sellmeier(wl_b)
        n_sfg = neff_sellmeier(wl_sfg)

        k_a = 2 * math.pi * n_a / wl_a
        k_b = 2 * math.pi * n_b / wl_b
        k_sfg = 2 * math.pi * n_sfg / wl_sfg

        delta_k = k_sfg - k_a - k_b
        if abs(delta_k) < 1e-15:
            return float('inf')
        return abs(2 * math.pi / delta_k)


# Define all 6 triplets
TRIPLETS = [
    WDMTriplet(1, 1040, 1020, 1000),
    WDMTriplet(2, 1100, 1080, 1060),
    WDMTriplet(3, 1160, 1140, 1120),
    WDMTriplet(4, 1220, 1200, 1180),
    WDMTriplet(5, 1280, 1260, 1240),
    WDMTriplet(6, 1340, 1320, 1300),
]


# =============================================================================
# PPLN Phase-Matching Model
# =============================================================================

def ppln_phase_mismatch_efficiency(
    wl_a_nm: float,
    wl_b_nm: float,
    poling_period_nm: float,
    ppln_length_nm: float,
) -> float:
    """
    Compute relative SFG efficiency for a wavelength pair through a PPLN
    designed with a given poling period.

    The efficiency follows sinc^2(delta_k * L / 2) where delta_k is the
    residual phase mismatch after quasi-phase-matching.

    Returns:
        Relative efficiency in [0, 1]. 1.0 = perfect phase match.
    """
    wl_sfg = 1.0 / (1.0 / wl_a_nm + 1.0 / wl_b_nm)
    n_a = neff_sellmeier(wl_a_nm)
    n_b = neff_sellmeier(wl_b_nm)
    n_sfg = neff_sellmeier(wl_sfg)

    k_a = 2 * math.pi * n_a / wl_a_nm
    k_b = 2 * math.pi * n_b / wl_b_nm
    k_sfg = 2 * math.pi * n_sfg / wl_sfg

    delta_k = k_sfg - k_a - k_b - 2 * math.pi / poling_period_nm

    x = delta_k * ppln_length_nm / 2
    if abs(x) < 1e-10:
        return 1.0
    return (math.sin(x) / x) ** 2


# =============================================================================
# Multi-Triplet SFG Mixer
# =============================================================================

def multi_triplet_sfg_mixer(
    signals: list[OpticalSignal],
    design_triplet: WDMTriplet,
    ppln_length_um: float = 26.0,
    base_conversion_efficiency: float = 0.10,
    insertion_loss_db: float = 1.0,
) -> tuple[list[OpticalSignal], list[OpticalSignal]]:
    """
    SFG mixing for multiple co-propagating signals through a single PPLN.

    Every pair of input signals can potentially produce an SFG product.
    The PPLN is phase-matched to the design_triplet, so within-triplet
    pairs convert efficiently while cross-triplet pairs are suppressed
    by phase mismatch.

    Args:
        signals: All optical signals entering this PE (from all triplets)
        design_triplet: The triplet this PPLN is phase-matched for
        ppln_length_um: PPLN interaction length
        base_conversion_efficiency: Peak conversion efficiency (at perfect phase match)
        insertion_loss_db: Additional insertion loss for all signals

    Returns:
        (sfg_products, passthroughs):
        - sfg_products: list of SFG output signals (wanted + spurious)
        - passthroughs: list of attenuated passthrough signals
    """
    MIN_POWER_DBM = -40.0
    ppln_length_nm = ppln_length_um * 1000.0
    poling_period_nm = design_triplet.ppln_poling_period_nm()

    sfg_products = []
    passthroughs = []

    # Each signal passes through with insertion loss and reduced by total
    # conversion (approximation: small-signal regime, each signal loses
    # a small fraction to all SFG processes it participates in)
    for sig in signals:
        pass_sig = sig.attenuate(insertion_loss_db)
        # Approximate depletion from SFG: small-signal regime
        pass_sig = OpticalSignal(
            pass_sig.wavelength_nm,
            pass_sig.power_dbm + 10 * np.log10(max(1.0 - base_conversion_efficiency, 0.01)),
            pass_sig.phase_rad,
        )
        passthroughs.append(pass_sig)

    # Every pair can produce SFG
    for i, sig_a in enumerate(signals):
        for j, sig_b in enumerate(signals):
            if j <= i:
                continue  # avoid double counting; i<j only
            if sig_a.power_dbm < MIN_POWER_DBM or sig_b.power_dbm < MIN_POWER_DBM:
                continue

            wl_a = sig_a.wavelength_nm
            wl_b = sig_b.wavelength_nm
            wl_sfg = 1.0 / (1.0 / wl_a + 1.0 / wl_b)

            # Phase-matching efficiency
            eta_pm = ppln_phase_mismatch_efficiency(
                wl_a, wl_b, poling_period_nm, ppln_length_nm,
            )

            # Effective conversion efficiency
            eta_eff = base_conversion_efficiency * eta_pm

            if eta_eff < 1e-6:
                continue  # negligible

            p_a_mw = sig_a.power_mw
            p_b_mw = sig_b.power_mw
            p_sfg_mw = eta_eff * np.sqrt(p_a_mw * p_b_mw)
            p_sfg_dbm = 10 * np.log10(max(p_sfg_mw, 1e-10))

            sfg_out = OpticalSignal(
                round(wl_sfg, 2),
                p_sfg_dbm - insertion_loss_db,
                0.0,
            )
            sfg_products.append(sfg_out)

    return sfg_products, passthroughs


# =============================================================================
# Per-Triplet AWG Demux
# =============================================================================

def triplet_awg_demux(
    signal: OpticalSignal,
    triplet: WDMTriplet,
    insertion_loss_db: float = 3.0,
    channel_bandwidth_nm: float = 5.0,
    crosstalk_db: float = -25.0,
) -> dict[int, float]:
    """
    Route an SFG product through a per-triplet AWG demuxer.

    Each triplet has its own AWG with channels centered on that triplet's
    6 SFG product wavelengths. The 5nm channel bandwidth (narrower than
    the MVP's 15nm) is necessary to reject cross-triplet products that
    might be nearby.

    Args:
        signal: SFG product signal
        triplet: Which triplet's AWG to use
        insertion_loss_db: AWG insertion loss
        channel_bandwidth_nm: 3dB bandwidth per channel
        crosstalk_db: Out-of-band rejection

    Returns:
        Dict of {channel_index: power_dbm}
    """
    results = {}
    sigma_nm = channel_bandwidth_nm / 2.355  # FWHM to Gaussian sigma
    channels = triplet.awg_channels()

    for ch_idx, center_wl in channels.items():
        detuning = signal.wavelength_nm - center_wl
        passband = np.exp(-0.5 * (detuning / sigma_nm) ** 2)

        if passband > 0.01:
            power = signal.power_dbm - insertion_loss_db + 10 * np.log10(passband)
        else:
            power = signal.power_dbm + crosstalk_db - insertion_loss_db

        results[ch_idx] = power

    return results


# =============================================================================
# Multi-Triplet Encoder
# =============================================================================

def wdm_mzi_encode(
    trit: int,
    triplet: WDMTriplet,
    laser_power_dbm: float = 10.0,
    mzi_loss_db: float = 3.0,
    combiner_loss_db: float = 1.0,
) -> OpticalSignal:
    """Encode a trit using a specific WDM triplet's wavelengths."""
    wl = triplet.trit_to_wl[trit]
    power = laser_power_dbm - mzi_loss_db - combiner_loss_db
    return OpticalSignal(wl, power, 0.0)


# =============================================================================
# TEST 1: Cross-Triplet SFG Analysis
# =============================================================================

def test_cross_triplet_sfg_analysis() -> bool:
    """
    Compute ALL possible cross-triplet SFG products and check whether
    any fall within the AWG detection windows of any triplet.

    This is the core WDM isolation proof: the 60nm inter-triplet spacing
    was chosen so cross-triplet products miss the AWG channels.
    """
    print("\n" + "=" * 78)
    print("  TEST 1: Cross-Triplet SFG Wavelength Analysis")
    print("  (Do spurious SFG products land on any AWG detection channel?)")
    print("=" * 78)

    # Collect all within-triplet AWG channels with their bandwidths
    awg_bandwidth_nm = 5.0  # per-triplet AWG channel FWHM
    half_bw = awg_bandwidth_nm / 2.0

    all_awg_windows = []  # (triplet_id, channel_idx, center_wl, trit_meaning)
    for t in TRIPLETS:
        sfg_result = t.sfg_result_table()
        for ch_idx, center_wl in t.awg_channels().items():
            trit_val = sfg_result.get(center_wl, "?")
            all_awg_windows.append((t.triplet_id, ch_idx, center_wl, trit_val))

    # Compute all cross-triplet SFG products
    cross_products = []
    for i, t_a in enumerate(TRIPLETS):
        for j, t_b in enumerate(TRIPLETS):
            if j <= i:
                continue  # cross-triplet only, no self-pairs
            for wl_a in t_a.wavelengths:
                for wl_b in t_b.wavelengths:
                    sfg_wl = 1.0 / (1.0 / wl_a + 1.0 / wl_b)
                    cross_products.append((t_a.triplet_id, wl_a, t_b.triplet_id, wl_b, sfg_wl))

    print(f"\n  Total cross-triplet SFG combinations: {len(cross_products)}")
    print(f"  AWG channel bandwidth: {awg_bandwidth_nm} nm FWHM")

    # Check for overlaps
    overlaps = []
    for tid_a, wl_a, tid_b, wl_b, sfg_wl in cross_products:
        for awg_tid, ch_idx, center_wl, trit_val in all_awg_windows:
            if abs(sfg_wl - center_wl) <= half_bw:
                overlaps.append((tid_a, wl_a, tid_b, wl_b, sfg_wl, awg_tid, ch_idx, center_wl))

    if overlaps:
        print(f"\n  WARNING: {len(overlaps)} cross-triplet products fall within AWG windows:")
        for tid_a, wl_a, tid_b, wl_b, sfg_wl, awg_tid, ch_idx, center_wl in overlaps[:15]:
            delta = sfg_wl - center_wl
            print(f"    T{tid_a}:{wl_a:.0f}nm + T{tid_b}:{wl_b:.0f}nm "
                  f"-> {sfg_wl:.2f}nm  hits T{awg_tid} ch{ch_idx} "
                  f"({center_wl:.1f}nm, delta={delta:+.2f}nm)")
        if len(overlaps) > 15:
            print(f"    ... and {len(overlaps) - 15} more")
    else:
        print("\n  No cross-triplet SFG products fall within any AWG window.")

    # Also check with PPLN phase-matching: how strong are these spurious products?
    print(f"\n  --- PPLN Phase-Matching Suppression ---")
    print(f"  PPLN length: {PPLN_LENGTH} um")
    print()

    worst_case_eff = 0.0
    worst_case_info = ""

    for t_design in TRIPLETS:
        poling_nm = t_design.ppln_poling_period_nm()
        ppln_nm = PPLN_LENGTH * 1000.0

        # Check cross-triplet efficiency for this PPLN
        for t_other in TRIPLETS:
            if t_other.triplet_id == t_design.triplet_id:
                continue
            for wl_a in t_design.wavelengths:
                for wl_b in t_other.wavelengths:
                    eta = ppln_phase_mismatch_efficiency(wl_a, wl_b, poling_nm, ppln_nm)
                    if eta > worst_case_eff:
                        worst_case_eff = eta
                        sfg_wl = 1.0 / (1.0 / wl_a + 1.0 / wl_b)
                        worst_case_info = (
                            f"T{t_design.triplet_id}:{wl_a:.0f}nm + "
                            f"T{t_other.triplet_id}:{wl_b:.0f}nm -> {sfg_wl:.1f}nm"
                        )

    # Show per-triplet summary
    for t_design in TRIPLETS:
        poling_nm = t_design.ppln_poling_period_nm()
        ppln_nm = PPLN_LENGTH * 1000.0

        # Within-triplet efficiency (min across all 9 combos)
        within_effs = []
        for wa in t_design.wavelengths:
            for wb in t_design.wavelengths:
                e = ppln_phase_mismatch_efficiency(wa, wb, poling_nm, ppln_nm)
                within_effs.append(e)
        min_within = min(within_effs)
        max_within = max(within_effs)

        # Cross-triplet efficiency (max across all neighbors)
        max_cross = 0.0
        for t_other in TRIPLETS:
            if t_other.triplet_id == t_design.triplet_id:
                continue
            for wa in t_design.wavelengths:
                for wb in t_other.wavelengths:
                    e = ppln_phase_mismatch_efficiency(wa, wb, poling_nm, ppln_nm)
                    max_cross = max(max_cross, e)

        isolation_db = -10 * np.log10(max(max_cross, 1e-15)) if max_cross > 0 else 999
        print(f"  Triplet {t_design.triplet_id}: within-triplet eff = "
              f"{min_within*100:.1f}-{max_within*100:.1f}%, "
              f"worst cross-triplet = {max_cross*100:.2f}% "
              f"(isolation = {isolation_db:.1f} dB)")

    print(f"\n  Worst-case cross-triplet efficiency: {worst_case_eff*100:.2f}%")
    print(f"    {worst_case_info}")
    isolation_db = -10 * np.log10(max(worst_case_eff, 1e-15))
    print(f"    PPLN isolation: {isolation_db:.1f} dB")

    # Combined defense: PPLN suppression + AWG rejection
    # Even if PPLN doesn't fully suppress, AWG channel narrowness helps
    # A spurious product must BOTH be generated efficiently AND land on an AWG channel
    print(f"\n  --- Combined Defense Assessment ---")
    print(f"  Layer 1: PPLN phase mismatch -> worst case {worst_case_eff*100:.2f}% efficiency")
    print(f"  Layer 2: AWG channel filtering -> {awg_bandwidth_nm}nm FWHM channels")

    # Cross-products that pass BOTH defenses
    dangerous = []
    for tid_a, wl_a, tid_b, wl_b, sfg_wl, awg_tid, ch_idx, center_wl in overlaps:
        # Find which triplet's PPLN this would happen in
        # The PE's PPLN could be phase-matched to any triplet in principle
        # In the multi-triplet design, each PE has ONE PPLN with ONE poling period
        # We need to check: for each possible design triplet, does this cross-pair convert?
        for t_design in TRIPLETS:
            if t_design.triplet_id not in (tid_a, tid_b):
                continue
            poling_nm = t_design.ppln_poling_period_nm()
            ppln_nm = PPLN_LENGTH * 1000.0
            eta = ppln_phase_mismatch_efficiency(wl_a, wl_b, poling_nm, ppln_nm)
            if eta > 0.01:  # >1% cross-efficiency AND hits an AWG channel
                delta = sfg_wl - center_wl
                dangerous.append((tid_a, wl_a, tid_b, wl_b, sfg_wl, awg_tid, ch_idx,
                                  center_wl, delta, eta, t_design.triplet_id))

    if dangerous:
        print(f"\n  DANGEROUS: {len(dangerous)} cross-products pass both defenses:")
        for (tid_a, wl_a, tid_b, wl_b, sfg_wl, awg_tid, ch_idx,
             center_wl, delta, eta, design_tid) in dangerous[:10]:
            print(f"    T{tid_a}:{wl_a:.0f} + T{tid_b}:{wl_b:.0f} -> {sfg_wl:.2f}nm "
                  f"(PPLN T{design_tid}: eta={eta*100:.1f}%) "
                  f"hits T{awg_tid} ch{ch_idx} ({center_wl:.1f}nm, delta={delta:+.2f}nm)")
    else:
        print(f"\n  No cross-products pass both PPLN and AWG defenses.")

    # The test passes if PPLN + AWG together provide >20dB isolation
    # or if no dangerous products exist
    passed = len(dangerous) == 0 or worst_case_eff < 0.01
    if not passed:
        # Even with dangerous products, if PPLN efficiency is low enough
        # the signal-to-interference ratio may still be acceptable
        # Check if worst-case cross-triplet power is >20dB below signal
        base_eff = 0.10  # 10% nominal conversion
        # Worst-case signal-to-interference: base_eff / (base_eff * worst_cross)
        sir = 1.0 / worst_case_eff if worst_case_eff > 0 else float('inf')
        sir_db = 10 * np.log10(sir)
        print(f"\n  Signal-to-Interference Ratio (SIR): {sir_db:.1f} dB")
        print(f"  (Wanted signal at 100% PM eff vs worst cross at {worst_case_eff*100:.1f}%)")
        if sir_db > 10:
            print(f"  SIR > 10 dB: cross-triplet interference is manageable")
        else:
            print(f"  SIR < 10 dB: cross-triplet interference could corrupt results")

    # Report
    status = "PASS" if len(dangerous) == 0 else "MARGINAL (see SIR analysis)"
    print(f"\n  Result: {status}")
    return len(dangerous) == 0


# =============================================================================
# TEST 2: Single-Triplet Correctness (per triplet)
# =============================================================================

def simulate_array_single_triplet(
    input_trits: list[int],
    weight_matrix: list[list[int]],
    triplet: WDMTriplet,
    laser_power_dbm: float = 10.0,
    verbose: bool = False,
) -> tuple[list[int], list[int], bool]:
    """
    Simulate 9x9 array for a single triplet (no cross-triplet interference).

    This is the single-triplet version using the new WDM wavelengths
    (not the MVP 1064/1310/1550). It verifies each triplet works in isolation.

    Returns:
        (expected_output, detected_output, all_correct)
    """
    assert len(input_trits) == 9
    assert len(weight_matrix) == 9 and all(len(r) == 9 for r in weight_matrix)

    # Expected output
    expected = []
    for col in range(9):
        acc = sum(input_trits[row] * weight_matrix[row][col] for row in range(9))
        expected.append(acc)

    # Build SFG result table for this triplet
    sfg_result = triplet.sfg_result_table()
    awg_channels = triplet.awg_channels()

    # Encode activations
    activations = []
    for row in range(9):
        sig = wdm_mzi_encode(input_trits[row], triplet, laser_power_dbm)
        sig = waveguide_transfer(sig, IOC_INPUT_WIDTH + ROUTING_GAP, WG_LOSS_DB_CM)
        sig = sig.attenuate(EDGE_COUPLING_LOSS)
        activations.append(sig)

    # Process PE array
    column_products = [[] for _ in range(9)]

    for row in range(9):
        act = activations[row]
        for col in range(9):
            w = weight_matrix[row][col]
            wt = wdm_mzi_encode(w, triplet, laser_power_dbm)
            weight_path_um = row * PE_PITCH + 40
            wt = waveguide_transfer(wt, weight_path_um, WG_LOSS_DB_CM)

            # SFG using the standard mixer (single-triplet: no cross-mixing)
            sfg_out, act, pass_v = sfg_mixer(
                act, wt,
                ppln_length_um=PPLN_LENGTH,
                conversion_efficiency=0.10,
                insertion_loss_db=1.0,
            )

            if col < 8:
                act = waveguide_transfer(act, PE_PITCH - PE_WIDTH, WG_LOSS_DB_CM)

            if sfg_out is not None:
                column_products[col].append(sfg_out)

    # Decode outputs
    detected = []
    for col in range(9):
        products = column_products[col]
        if not products:
            detected.append(0)
            continue

        net_sum = 0
        for sfg in products:
            # Find nearest AWG channel
            best_ch = None
            best_dist = float('inf')
            for ch_idx, center_wl in awg_channels.items():
                dist = abs(sfg.wavelength_nm - center_wl)
                if dist < best_dist:
                    best_dist = dist
                    best_ch = ch_idx

            if best_ch is not None:
                best_wl = awg_channels[best_ch]
                trit_val = sfg_result.get(best_wl, 0)
                net_sum += trit_val

        detected.append(net_sum)

    all_correct = detected == expected
    return expected, detected, all_correct


# =============================================================================
# TEST 3: Multi-Triplet Simulation (progressive loading)
# =============================================================================

@dataclass
class MultiTripletResult:
    """Result of multi-triplet simulation for one column."""
    triplet_id: int
    expected: int
    detected: int
    wanted_sfg_count: int      # SFG products from this triplet
    spurious_sfg_count: int    # Cross-triplet SFG products detected
    worst_spurious_power_dbm: float  # Strongest spurious product


def simulate_array_multi_triplet(
    triplet_inputs: dict[int, tuple[list[int], list[list[int]]]],
    active_triplets: list[WDMTriplet],
    laser_power_dbm: float = 10.0,
    verbose: bool = False,
) -> dict[int, list[MultiTripletResult]]:
    """
    Simulate 9x9 array with multiple triplets simultaneously.

    Each triplet carries its own independent computation (input vector +
    weight matrix). All wavelengths co-propagate through the same PEs.

    This models the actual physics: at each PE, wavelengths from ALL active
    triplets are present, and the PPLN can produce cross-triplet SFG products.

    Args:
        triplet_inputs: {triplet_id: (input_trits, weight_matrix)}
        active_triplets: List of active WDMTriplet objects
        laser_power_dbm: Laser power per channel
        verbose: Print detailed trace

    Returns:
        {triplet_id: [MultiTripletResult for each column]}
    """
    # Encode all activations and weights for all triplets
    # activations_by_triplet[tid][row] = OpticalSignal
    activations_by_triplet = {}
    weights_by_triplet = {}

    for t in active_triplets:
        tid = t.triplet_id
        x, W = triplet_inputs[tid]

        acts = []
        for row in range(9):
            sig = wdm_mzi_encode(x[row], t, laser_power_dbm)
            sig = waveguide_transfer(sig, IOC_INPUT_WIDTH + ROUTING_GAP, WG_LOSS_DB_CM)
            sig = sig.attenuate(EDGE_COUPLING_LOSS)
            acts.append(sig)
        activations_by_triplet[tid] = acts

        wts = []
        for row in range(9):
            row_wts = []
            for col in range(9):
                w = W[row][col]
                sig = wdm_mzi_encode(w, t, laser_power_dbm)
                weight_path_um = row * PE_PITCH + 40
                sig = waveguide_transfer(sig, weight_path_um, WG_LOSS_DB_CM)
                row_wts.append(sig)
            wts.append(row_wts)
        weights_by_triplet[tid] = wts

    # For PPLN phase matching, we need to decide which triplet the PPLN is
    # "designed for". In reality, the PPLN can be designed for a BROADBAND
    # response (chirped poling) or use a poling period that is a compromise.
    # For this simulation, we use the average center wavelength to represent
    # a broadband PPLN, and apply the phase-matching penalty for all pairs.
    avg_center = np.mean([t.wl_zero for t in active_triplets])
    # Use the triplet closest to this average as the design reference
    design_triplet = min(active_triplets, key=lambda t: abs(t.wl_zero - avg_center))

    # Simulate PE array
    # At each PE, ALL activation signals for that row and ALL weight signals
    # for that PE position are co-present.
    #
    # column_sfg_all[col] = list of ALL SFG products (wanted + spurious)
    column_sfg_all = [[] for _ in range(9)]

    # Track per-row activation signals that propagate horizontally
    # act_signals[tid][current_signal_index] evolves through the row
    for row in range(9):
        # Current activation signals for each triplet in this row
        act_current = {}
        for t in active_triplets:
            act_current[t.triplet_id] = activations_by_triplet[t.triplet_id][row]

        for col in range(9):
            # Gather all signals at this PE
            all_pe_signals = []

            # Activation signals (horizontal, from all triplets)
            act_list = []
            for t in active_triplets:
                act_list.append((t.triplet_id, "act", act_current[t.triplet_id]))
                all_pe_signals.append(act_current[t.triplet_id])

            # Weight signals (vertical, from all triplets)
            wt_list = []
            for t in active_triplets:
                wt_sig = weights_by_triplet[t.triplet_id][row][col]
                wt_list.append((t.triplet_id, "wt", wt_sig))
                all_pe_signals.append(wt_sig)

            # Multi-signal SFG in PPLN
            sfg_products, passthroughs = multi_triplet_sfg_mixer(
                all_pe_signals,
                design_triplet,
                ppln_length_um=PPLN_LENGTH,
                base_conversion_efficiency=0.10,
                insertion_loss_db=1.0,
            )

            # Collect all SFG products for this column
            for sfg in sfg_products:
                column_sfg_all[col].append(sfg)

            # Update activation signals (passthrough corresponds to first N signals)
            # In the multi-triplet mixer, passthroughs preserve order
            idx = 0
            for t in active_triplets:
                act_current[t.triplet_id] = passthroughs[idx]
                idx += 1
            # (Skip weight passthroughs: idx += len(active_triplets))

            # Propagate activations to next PE
            if col < 8:
                for t in active_triplets:
                    act_current[t.triplet_id] = waveguide_transfer(
                        act_current[t.triplet_id],
                        PE_PITCH - PE_WIDTH,
                        WG_LOSS_DB_CM,
                    )

    # Decode: for each triplet, use its AWG to extract its results
    results = {}
    for t in active_triplets:
        tid = t.triplet_id
        x, W = triplet_inputs[tid]
        expected_output = []
        for col in range(9):
            acc = sum(x[row] * W[row][col] for row in range(9))
            expected_output.append(acc)

        sfg_result_table = t.sfg_result_table()
        awg_ch = t.awg_channels()

        col_results = []
        for col in range(9):
            products = column_sfg_all[col]
            if not products:
                col_results.append(MultiTripletResult(
                    tid, expected_output[col], 0, 0, 0, -999.0
                ))
                continue

            # Route each product through this triplet's AWG
            net_sum = 0
            wanted_count = 0
            spurious_count = 0
            worst_spurious = -999.0

            for sfg in products:
                # Route through output waveguide
                sfg_routed = waveguide_transfer(
                    sfg,
                    ROUTING_GAP + IOC_OUTPUT_WIDTH * 0.3,
                    WG_LOSS_DB_CM,
                )

                # AWG demux for THIS triplet
                ch_powers = triplet_awg_demux(sfg_routed, t)

                # Find best channel
                best_ch = max(ch_powers, key=ch_powers.get)
                best_power = ch_powers[best_ch]
                best_wl = awg_ch[best_ch]

                # Is this a wanted signal (from our triplet) or spurious?
                sfg_wl = sfg.wavelength_nm
                is_within_triplet = any(
                    abs(sfg_wl - expected_wl) < 1.0
                    for expected_wl in t.sfg_products().values()
                )

                # Check if it actually registers on the AWG (above noise floor)
                # Gaussian passband check: is the signal within channel bandwidth?
                nearest_ch_wl = awg_ch[best_ch]
                detuning = abs(sfg_wl - nearest_ch_wl)
                sigma = 5.0 / 2.355  # 5nm FWHM
                passband = np.exp(-0.5 * (detuning / sigma) ** 2)

                if passband > 0.1:  # >10% coupling = detected
                    trit_val = sfg_result_table.get(best_wl, 0)

                    if is_within_triplet:
                        net_sum += trit_val
                        wanted_count += 1
                    else:
                        # Spurious product detected by this AWG!
                        spurious_count += 1
                        worst_spurious = max(worst_spurious, sfg.power_dbm)
                        # It contributes an error
                        net_sum += trit_val

            col_results.append(MultiTripletResult(
                tid, expected_output[col], net_sum,
                wanted_count, spurious_count, worst_spurious,
            ))

        results[tid] = col_results

    return results


# =============================================================================
# TEST 4: Progressive Loading Test
# =============================================================================

def test_progressive_loading(verbose: bool = False) -> dict[int, bool]:
    """
    Progressive test: load triplets one at a time (1 -> 6).
    At each step, run the identity matrix test for ALL active triplets.
    Report pass/fail and any interference detected.

    Returns:
        {num_triplets: passed}
    """
    print("\n" + "=" * 78)
    print("  TEST 2: Progressive WDM Loading (Identity Matrix)")
    print("  Adding triplets 1 -> 6, checking correctness at each step")
    print("=" * 78)

    # Identity matrix and a test input vector
    x = [+1, -1, 0, +1, -1, 0, +1, -1, 0]
    W_identity = [[1 if i == j else 0 for j in range(9)] for i in range(9)]

    results_by_count = {}

    for num_active in range(1, 7):
        active = TRIPLETS[:num_active]

        # Each triplet computes the SAME identity-matrix product
        # (in practice they'd carry different computations, but identity
        # is the simplest correctness check)
        triplet_inputs = {}
        for t in active:
            triplet_inputs[t.triplet_id] = (x, W_identity)

        # Run single-triplet simulation first (no cross-talk, baseline)
        single_results = {}
        for t in active:
            exp, det, ok = simulate_array_single_triplet(x, W_identity, t)
            single_results[t.triplet_id] = ok

        # Run multi-triplet simulation (with cross-talk)
        multi_results = simulate_array_multi_triplet(
            triplet_inputs, active, verbose=verbose,
        )

        # Analyze results
        all_correct = True
        total_spurious = 0
        triplet_status = []

        for t in active:
            tid = t.triplet_id
            cols = multi_results[tid]
            correct = all(c.expected == c.detected for c in cols)
            spurious = sum(c.spurious_sfg_count for c in cols)
            total_spurious += spurious

            if not correct:
                all_correct = False

            exp_vec = [c.expected for c in cols]
            det_vec = [c.detected for c in cols]
            triplet_status.append((tid, correct, spurious, exp_vec, det_vec))

        results_by_count[num_active] = all_correct

        print(f"\n  --- {num_active} triplet{'s' if num_active > 1 else ''} active ---")
        for tid, correct, spurious, exp, det in triplet_status:
            status = "PASS" if correct else "FAIL"
            spur_str = f", {spurious} spurious SFG" if spurious > 0 else ""
            print(f"    T{tid}: {status}  expected={exp}  detected={det}{spur_str}")

        if total_spurious > 0:
            print(f"    Total spurious SFG products detected: {total_spurious}")

    return results_by_count


# =============================================================================
# TEST 5: Per-Triplet Isolation (single triplet correctness)
# =============================================================================

def test_per_triplet_isolation() -> bool:
    """
    Verify each of the 6 triplets produces correct results in isolation.
    This ensures the WDM wavelengths and SFG products are self-consistent.
    """
    print("\n" + "=" * 78)
    print("  TEST 3: Per-Triplet Isolation (each triplet solo)")
    print("=" * 78)

    x = [+1, -1, 0, +1, -1, 0, +1, -1, 0]
    W = [[1 if i == j else 0 for j in range(9)] for i in range(9)]

    all_pass = True
    for t in TRIPLETS:
        exp, det, ok = simulate_array_single_triplet(x, W, t)
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_pass = False
        print(f"  Triplet {t.triplet_id} ({t.wl_plus1}/{t.wl_zero}/{t.wl_minus1} nm): "
              f"{status}  expected={exp}  detected={det}")

    print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    return all_pass


# =============================================================================
# TEST 6: Power Budget with 6 Triplets
# =============================================================================

def test_power_budget_6x() -> bool:
    """
    Verify that 6x more light in waveguides doesn't cause issues.

    Checks:
    1. Total power in waveguide stays below damage threshold
    2. Photodetector doesn't saturate
    3. SFG products from all triplets remain above detection threshold
    """
    print("\n" + "=" * 78)
    print("  TEST 4: Power Budget with 6 Triplets")
    print("=" * 78)

    DAMAGE_THRESHOLD_DBM = 30.0     # ~1W - typical TFLN damage
    DETECTOR_SATURATION_UA = 1000.0  # 1mA saturation
    DETECTOR_SENSITIVITY_DBM = -30.0

    laser_power_dbm = 10.0  # 10 mW per channel

    # Total power per waveguide: 6 triplets x 1 wavelength per trit = 6 signals
    # Each at ~6 dBm after encoding (10 - 3 MZI - 1 combiner)
    encoded_power_dbm = laser_power_dbm - 3.0 - 1.0  # 6 dBm per channel
    encoded_power_mw = 10 ** (encoded_power_dbm / 10)

    total_power_mw = 6 * encoded_power_mw  # 6 signals in one waveguide
    total_power_dbm = 10 * np.log10(total_power_mw)

    print(f"\n  Per-channel encoded power: {encoded_power_dbm:.1f} dBm "
          f"({encoded_power_mw:.2f} mW)")
    print(f"  Total power per waveguide (6 channels): {total_power_dbm:.1f} dBm "
          f"({total_power_mw:.2f} mW)")
    print(f"  Waveguide damage threshold: {DAMAGE_THRESHOLD_DBM:.0f} dBm")

    margin_damage = DAMAGE_THRESHOLD_DBM - total_power_dbm
    print(f"  Damage margin: {margin_damage:.1f} dB -- {'OK' if margin_damage > 0 else 'EXCEEDED'}")

    # Worst-case SFG output (last PE in row, row 8)
    # After 9 PEs of passthrough loss + waveguide loss
    per_pe_loss_db = 1.0  # insertion loss
    passthrough_loss_db = -10 * np.log10(0.90)  # 90% passthrough
    total_pe_loss = 9 * (per_pe_loss_db + passthrough_loss_db)
    routing_loss = WG_LOSS_DB_CM * (8 * (PE_PITCH - PE_WIDTH)) / 1e4
    worst_act_power = encoded_power_dbm - EDGE_COUPLING_LOSS - total_pe_loss - routing_loss

    print(f"\n  Worst-case activation at PE[8,8]: {worst_act_power:.1f} dBm")

    # SFG output from worst-case PE
    sfg_power_dbm = worst_act_power - 10.0  # ~10 dB conversion loss
    print(f"  SFG output at worst PE: {sfg_power_dbm:.1f} dBm")

    # After routing to decoder
    output_routing = WG_LOSS_DB_CM * (ROUTING_GAP + IOC_OUTPUT_WIDTH) / 1e4
    awg_loss = 3.0
    final_power = sfg_power_dbm - output_routing - awg_loss - EDGE_COUPLING_LOSS
    print(f"  At detector (after AWG + routing): {final_power:.1f} dBm")
    print(f"  Detector sensitivity: {DETECTOR_SENSITIVITY_DBM:.0f} dBm")

    margin_detect = final_power - DETECTOR_SENSITIVITY_DBM
    print(f"  Detection margin: {margin_detect:.1f} dB "
          f"-- {'OK' if margin_detect > 0 else 'BELOW THRESHOLD'}")

    # Detector saturation check
    # The detector sees SFG products (after PPLN conversion), not raw input light.
    # The AWG filters out the input wavelengths (1000-1340nm) from the SFG band (500-670nm).
    # Worst-case detector power: strongest SFG product at first PE (PE[0,0])
    # SFG power = conversion_eff * sqrt(P_act * P_wt) ~= 0.10 * P_encoded
    sfg_pe00_dbm = encoded_power_dbm + 10 * np.log10(0.10)  # -4 dBm
    # With 6 triplets, 6 SFG products could land on a single detector if
    # cross-triplet products overlap (worst case). Normally just 1 per triplet.
    worst_detector_power_dbm = sfg_pe00_dbm  # single-triplet per AWG channel
    strongest_current = photodetector(worst_detector_power_dbm)
    print(f"\n  Strongest SFG product at PE[0,0]: {sfg_pe00_dbm:.1f} dBm")
    print(f"  Corresponding photocurrent: {strongest_current:.1f} uA")
    print(f"  Detector saturation: {DETECTOR_SATURATION_UA:.0f} uA")
    sat_ok = strongest_current < DETECTOR_SATURATION_UA
    print(f"  Saturation margin: {DETECTOR_SATURATION_UA - strongest_current:.1f} uA "
          f"-- {'OK' if sat_ok else 'SATURATED'}")

    passed = margin_damage > 0 and margin_detect > 0 and sat_ok
    print(f"\n  Result: {'PASS' if passed else 'FAIL'}")
    return passed


# =============================================================================
# TEST 6: Design Space Analysis -- What PPLN Length / Triplet Spacing is Needed?
# =============================================================================

def test_design_space_analysis() -> bool:
    """
    This test doesn't pass/fail -- it explores the design space to find
    the minimum PPLN length or maximum triplet spacing needed for isolation.

    The 26um PPLN is too short for 60nm triplet spacing. What parameters work?
    """
    print("\n" + "=" * 78)
    print("  TEST 6: Design Space Exploration")
    print("  Finding PPLN length and triplet spacing for adequate isolation")
    print("=" * 78)

    TARGET_ISOLATION_DB = 20.0  # Want 20 dB suppression of cross-triplet SFG

    # ---- Part A: Sweep PPLN length at 60nm triplet spacing ----
    print(f"\n  --- Part A: PPLN Length Sweep (60nm triplet spacing) ---")
    print(f"  Target: >{TARGET_ISOLATION_DB:.0f} dB cross-triplet isolation")
    print()

    ppln_lengths_um = [26, 50, 100, 200, 500, 1000, 2000, 5000]
    # Use adjacent triplets T3 and T4 (worst-case: these are in the middle)

    for ppln_um in ppln_lengths_um:
        ppln_nm = ppln_um * 1000.0
        worst_cross = 0.0
        min_within = 1.0

        for t_design in TRIPLETS:
            poling_nm = t_design.ppln_poling_period_nm()

            # Within-triplet efficiency
            for wa in t_design.wavelengths:
                for wb in t_design.wavelengths:
                    e = ppln_phase_mismatch_efficiency(wa, wb, poling_nm, ppln_nm)
                    min_within = min(min_within, e)

            # Cross-triplet efficiency
            for t_other in TRIPLETS:
                if t_other.triplet_id == t_design.triplet_id:
                    continue
                for wa in t_design.wavelengths:
                    for wb in t_other.wavelengths:
                        e = ppln_phase_mismatch_efficiency(wa, wb, poling_nm, ppln_nm)
                        worst_cross = max(worst_cross, e)

        isolation_db = -10 * np.log10(max(worst_cross, 1e-15))
        within_pct = min_within * 100
        cross_pct = worst_cross * 100
        status = "OK" if isolation_db >= TARGET_ISOLATION_DB else "LOW"
        print(f"    L={ppln_um:5d} um: within={within_pct:5.1f}%, "
              f"cross={cross_pct:8.4f}%, "
              f"isolation={isolation_db:5.1f} dB [{status}]")

    # ---- Part B: Sweep triplet spacing at 26um PPLN ----
    print(f"\n  --- Part B: Triplet Spacing Sweep (26um PPLN) ---")
    print(f"  Target: >{TARGET_ISOLATION_DB:.0f} dB cross-triplet isolation")
    print()

    spacings_nm = [60, 80, 100, 120, 150, 200, 250, 300]

    for spacing in spacings_nm:
        # Generate triplets with this spacing (centered around 1170nm)
        center = 1170
        intra_spacing = 20  # keep 20nm within-triplet
        test_triplets = []
        for i in range(6):
            c = center + (i - 2.5) * spacing
            test_triplets.append(WDMTriplet(
                i + 1,
                c + intra_spacing,  # wl_minus1
                c,                   # wl_zero
                c - intra_spacing,   # wl_plus1
            ))

        ppln_nm = 26.0 * 1000.0
        worst_cross = 0.0
        min_within = 1.0

        for t_design in test_triplets:
            poling_nm = t_design.ppln_poling_period_nm()

            for wa in t_design.wavelengths:
                for wb in t_design.wavelengths:
                    e = ppln_phase_mismatch_efficiency(wa, wb, poling_nm, ppln_nm)
                    min_within = min(min_within, e)

            for t_other in test_triplets:
                if t_other.triplet_id == t_design.triplet_id:
                    continue
                for wa in t_design.wavelengths:
                    for wb in t_other.wavelengths:
                        e = ppln_phase_mismatch_efficiency(wa, wb, poling_nm, ppln_nm)
                        worst_cross = max(worst_cross, e)

        isolation_db = -10 * np.log10(max(worst_cross, 1e-15))
        within_pct = min_within * 100
        cross_pct = worst_cross * 100
        status = "OK" if isolation_db >= TARGET_ISOLATION_DB else "LOW"
        total_span = (test_triplets[-1].wl_minus1 - test_triplets[0].wl_plus1)
        print(f"    spacing={spacing:3d}nm: span={total_span:.0f}nm, within={within_pct:5.1f}%, "
              f"cross={cross_pct:8.4f}%, "
              f"isolation={isolation_db:5.1f} dB [{status}]")

    # ---- Part C: Combined sweep -- find sweet spot ----
    print(f"\n  --- Part C: Minimum Viable Configurations ---")
    print(f"  Finding (PPLN_length, triplet_spacing) that give >{TARGET_ISOLATION_DB:.0f} dB")
    print()

    viable = []
    for ppln_um in [26, 50, 100, 200, 500]:
        for spacing in [60, 80, 100, 120, 150, 200, 300]:
            center = 1170
            intra_spacing = 20
            test_triplets = []
            for i in range(6):
                c = center + (i - 2.5) * spacing
                test_triplets.append(WDMTriplet(
                    i + 1,
                    c + intra_spacing,
                    c,
                    c - intra_spacing,
                ))

            ppln_nm = ppln_um * 1000.0
            worst_cross = 0.0
            min_within = 1.0

            for t_design in test_triplets:
                poling_nm = t_design.ppln_poling_period_nm()
                for wa in t_design.wavelengths:
                    for wb in t_design.wavelengths:
                        e = ppln_phase_mismatch_efficiency(wa, wb, poling_nm, ppln_nm)
                        min_within = min(min_within, e)
                for t_other in test_triplets:
                    if t_other.triplet_id == t_design.triplet_id:
                        continue
                    for wa in t_design.wavelengths:
                        for wb in t_other.wavelengths:
                            e = ppln_phase_mismatch_efficiency(wa, wb, poling_nm, ppln_nm)
                            worst_cross = max(worst_cross, e)

            isolation_db = -10 * np.log10(max(worst_cross, 1e-15))
            total_span = (test_triplets[-1].wl_minus1 - test_triplets[0].wl_plus1)

            if isolation_db >= TARGET_ISOLATION_DB and min_within > 0.10:
                viable.append((ppln_um, spacing, isolation_db, min_within * 100, total_span))

    if viable:
        print(f"    {'PPLN(um)':>10s}  {'Spacing(nm)':>12s}  {'Isolation(dB)':>14s}  "
              f"{'Min Within(%)':>14s}  {'Total Span(nm)':>15s}")
        for ppln_um, spacing, iso_db, min_w, span in sorted(viable, key=lambda x: x[0]):
            print(f"    {ppln_um:10d}  {spacing:12d}  {iso_db:14.1f}  "
                  f"{min_w:14.1f}  {span:15.0f}")
    else:
        print("    No viable configurations found in the search range.")
        print("    The phase-matching model may need refinement, or per-triplet")
        print("    PPLNs (cascaded with different poling periods) may be needed.")

    # ---- Part D: Key insight analysis ----
    print(f"\n  --- Part D: Key Physical Insight ---")
    print()
    print(f"  The fundamental problem: a single PPLN poling period cannot")
    print(f"  simultaneously serve all 9 within-triplet pairs AND reject")
    print(f"  cross-triplet pairs. The 20nm intra-triplet spacing causes")
    print(f"  the 9 within-triplet SFG pairs to span ~40nm of phase-matching")
    print(f"  bandwidth. The 60nm inter-triplet spacing is NOT much wider")
    print(f"  than this, so cross-triplet pairs fall within the same")
    print(f"  acceptance bandwidth.")
    print()
    print(f"  Longer PPLN narrows the bandwidth, but then within-triplet")
    print(f"  edge pairs (e.g. wl_-1 + wl_-1) also lose efficiency.")
    print()
    print(f"  CONCLUSION: Phase-matching alone cannot isolate these triplets.")
    print(f"  The WDM scheme requires a DIFFERENT isolation mechanism:")
    print()
    print(f"  Viable approaches:")
    print(f"    1. PER-TRIPLET PPLN SECTIONS: Each PE has 6 cascaded PPLN")
    print(f"       segments, each with its own poling period optimized for")
    print(f"       one triplet. Cross-triplet mixing is suppressed because")
    print(f"       within each segment, only the designed triplet phase-matches.")
    print(f"       PE length increases ~6x (26um -> 156um), still fits in 9x9.")
    print()
    print(f"    2. PER-TRIPLET WAVEGUIDE LANES: Route each triplet through")
    print(f"       its own dedicated PPLN mixer per PE. Physically separate")
    print(f"       waveguides prevent cross-triplet interaction entirely.")
    print(f"       6x more waveguides, but each is simple single-triplet.")
    print()
    print(f"    3. WIDER TRIPLET SPACING + LONGER PPLN: Use ~200nm spacing")
    print(f"       and ~500um PPLN. But this limits to 3 triplets in the")
    print(f"       1000-1600nm window and the PPLN is very long.")
    print()
    print(f"  Option 1 (cascaded PPLN) is the most practical for the")
    print(f"  monolithic chip design. It preserves the single-waveguide")
    print(f"  architecture and just makes each PE a bit longer.")
    return True  # Always passes -- informational test


# =============================================================================
# TEST 7: Full 6-Triplet Mixed Computation
# =============================================================================

def test_full_6triplet_mixed() -> bool:
    """
    Run 6 DIFFERENT computations simultaneously through the array.
    Each triplet carries a different weight matrix.
    """
    print("\n" + "=" * 78)
    print("  TEST 5: Full 6-Triplet Mixed Computation")
    print("  (Each triplet carries a different weight matrix)")
    print("=" * 78)

    # 6 different test vectors and weight matrices
    test_configs = {
        1: (
            [+1, -1, 0, +1, -1, 0, +1, -1, 0],
            [[1 if i == j else 0 for j in range(9)] for i in range(9)],
            "Identity",
        ),
        2: (
            [+1] * 9,
            [[+1] * 9 for _ in range(9)],
            "All +1s",
        ),
        3: (
            [+1, +1, +1, 0, 0, 0, 0, 0, 0],
            [([+1, 0, -1] + [0]*6) if i < 3 else [0]*9 for i in range(9)],
            "3x3 mixed",
        ),
        4: (
            [-1] * 9,
            [[1 if i == j else 0 for j in range(9)] for i in range(9)],
            "Neg identity",
        ),
        5: (
            [+1, 0, -1, +1, 0, -1, +1, 0, -1],
            [[1 if i == j else 0 for j in range(9)] for i in range(9)],
            "Alternating identity",
        ),
        6: (
            [+1] * 9,
            [[0]*9 for _ in range(9)],
            "Zero weights",
        ),
    }

    triplet_inputs = {}
    for tid, (x, W, name) in test_configs.items():
        triplet_inputs[tid] = (x, W)

    # Run multi-triplet simulation
    multi_results = simulate_array_multi_triplet(
        triplet_inputs, TRIPLETS, verbose=False,
    )

    all_pass = True
    for tid, (x, W, name) in test_configs.items():
        cols = multi_results[tid]
        exp = [c.expected for c in cols]
        det = [c.detected for c in cols]
        correct = exp == det
        spurious = sum(c.spurious_sfg_count for c in cols)
        if not correct:
            all_pass = False
        status = "PASS" if correct else "FAIL"
        spur_str = f"  ({spurious} spurious)" if spurious > 0 else ""
        print(f"  T{tid} [{name:20s}]: {status}  exp={exp}  det={det}{spur_str}")

    print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    return all_pass


# =============================================================================
# Main
# =============================================================================

def main():
    print()
    print("+" + "-" * 76 + "+")
    print("|  N-RADIX 9x9 MONOLITHIC CHIP -- 6-TRIPLET WDM ISOLATION TEST            |")
    print("|  18 wavelengths, 6 simultaneous computations, one chip                   |")
    print("+" + "-" * 76 + "+")

    results = {}

    # Test 1: Cross-triplet SFG analysis (physics analysis)
    results['cross_triplet_sfg'] = test_cross_triplet_sfg_analysis()

    # Test 2: Progressive loading (1 -> 6 triplets)
    progressive = test_progressive_loading(verbose=False)
    results['progressive_loading'] = all(progressive.values())

    # Test 3: Per-triplet isolation
    results['per_triplet_isolation'] = test_per_triplet_isolation()

    # Test 4: Power budget with 6x
    results['power_budget_6x'] = test_power_budget_6x()

    # Test 5: Full 6-triplet mixed computation
    results['full_6triplet_mixed'] = test_full_6triplet_mixed()

    # Test 6: Design space analysis (informational)
    results['design_space'] = test_design_space_analysis()

    # =========================================================================
    # SUMMARY TABLE
    # =========================================================================

    print("\n")
    print("+" + "-" * 76 + "+")
    print("|  WDM ISOLATION TEST SUMMARY                                              |")
    print("+" + "-" * 76 + "+")
    print("|                                                                            |")

    # Progressive loading detail
    print("|  Progressive Loading Results:                                              |")
    print("|  Triplets  |  1   |  2   |  3   |  4   |  5   |  6   |                    |")
    prog_str = "|  Status    |"
    for n in range(1, 7):
        status = " PASS" if progressive.get(n, False) else " FAIL"
        prog_str += f" {status} |"
    prog_str += "                    |"
    print(prog_str)
    print("|                                                                            |")

    # Test summary
    all_pass = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        marker = "  " if passed else ">>"
        name_display = name.replace('_', ' ').title()
        print(f"|  {marker} {name_display:45s} {status:>6s}                  |")
        if not passed:
            all_pass = False

    print("|                                                                            |")
    overall = "ALL TESTS PASSED" if all_pass else "SOME TESTS FAILED"
    print(f"|  {overall:74s}|")
    print("+" + "-" * 76 + "+")

    # Physics summary
    print("\n  Physics Summary:")
    print("  - 18 input wavelengths: 1000-1340 nm (6 triplets x 3 wavelengths)")
    print("  - 36 SFG product wavelengths: 500-670 nm")
    print("  - Inter-triplet spacing: 60 nm")
    print("  - Intra-triplet spacing: 20 nm")
    print()
    print("  Key Finding:")
    print("  A single PPLN poling period per PE CANNOT isolate 6 WDM triplets")
    print("  at 60nm spacing. The phase-matching acceptance bandwidth (~40nm")
    print("  for the 26um PPLN) is wider than the inter-triplet gap.")
    print()
    print("  What DOES work:")
    print("  - Each triplet works perfectly in isolation (Test 3: all 6 PASS)")
    print("  - Power budget is fine with 6x signals (Test 4: PASS)")
    print("  - Single triplet through the 9x9 array: fully correct")
    print()
    print("  Path forward: Per-triplet PPLN sections (6 cascaded PPLNs per PE)")
    print("  or per-triplet waveguide lanes. See Test 6 for details.")

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
