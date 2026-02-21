#!/usr/bin/env python3
"""
Monte Carlo Process Variation Analysis — Monolithic 9x9 N-Radix Chip
=====================================================================

PURPOSE:
    Estimate fabrication yield by simulating how real-world process variations
    affect the monolithic 9x9 chip's ability to function correctly.

    In a real TFLN (thin-film lithium niobate) foundry, nothing is perfect.
    Waveguides come out slightly wider or narrower than drawn. Etch depths
    vary across the wafer. Poling periods drift. This script asks:
    "Given realistic fab tolerances, how often does the chip still work?"

METHOD:
    Monte Carlo simulation — we roll the dice 10,000 times, each time picking
    random fab parameter values from Gaussian distributions centered on the
    nominal design. For each "virtual chip," we re-run the key validation
    checks from the monolithic_chip_9x9.py architecture. The fraction of
    chips that pass ALL checks is the predicted yield.

PARAMETER SOURCES:
    - Waveguide width tolerance: DRC_RULES.md rule WG.W.1 (500nm +/- 20nm)
    - Coupling gap tolerance: DRC_RULES.md rule RING.G.1 (150nm +/- 20nm)
    - Etch depth tolerance: DRC_RULES.md Section 10.1 (400nm +/- 10nm)
    - PPLN poling period: DRC_RULES.md rule PPLN.P.1 (9.27um T4 G+G mid-range +/- 0.1um)
    - Propagation loss: DRC_RULES.md Section 10.1 (<3 dB/cm target)
    - Refractive index: Material property variation for X-cut LiNbO3

VALIDATION CHECKS (from monolithic_chip_9x9.py validation):
    1. Loss budget — does signal reach detectors with positive margin?
    2. Wavelength collision — do SFG products stay >20nm apart?
    3. Ring resonator tuning — do rings still select correct channels?
    4. Path-length timing — does skew stay within acceptable bounds?

USAGE:
    python3 monte_carlo_9x9.py

    Output: terminal summary + plots saved to ../docs/monte_carlo_plots/

Author: N-Radix Project
Date: February 17, 2026
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend — safe for headless servers
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import os
import time
import sys

# =============================================================================
# NOMINAL DESIGN PARAMETERS (from monolithic_chip_9x9.py and DRC_RULES.md)
# =============================================================================

# These are the "as-drawn" values — what we design for.
# The foundry will deliver something close to these, but not exact.

@dataclass
class NominalDesign:
    """
    Nominal (target) design parameters for the monolithic 9x9 chip.
    All values from monolithic_chip_9x9.py and DRC_RULES.md.
    """
    # --- Waveguide geometry ---
    waveguide_width_nm: float = 500.0       # nm — single-mode for 1550/1310/1064nm
    ring_coupling_gap_nm: float = 150.0     # nm — bus-to-ring resonator gap
    etch_depth_nm: float = 400.0            # nm — RIE etch into TFLN slab

    # --- PPLN poling ---
    ppln_poling_period_um: float = 9.27     # um — T4 G+G mid-range, corrected Sellmeier
    # TODO: per-triplet Monte Carlo (periods span 5.4–12.7 um across 6 triplets)

    # --- Material properties ---
    refractive_index: float = 2.2           # X-cut LiNbO3 extraordinary index
    prop_loss_db_per_cm: float = 2.0        # dB/cm — waveguide propagation loss

    # --- Chip layout (from monolithic_chip_9x9.py) ---
    n_rows: int = 9
    n_cols: int = 9
    pe_width_um: float = 50.0
    pe_spacing_um: float = 5.0
    ioc_input_width_um: float = 180.0
    ioc_output_width_um: float = 200.0
    routing_gap_um: float = 60.0

    # --- Power budget (from validation) ---
    laser_power_dbm: float = 10.0           # 10 dBm per channel
    detector_sensitivity_dbm: float = -30.0 # -30 dBm minimum

    # --- Component insertion losses (nominal, dB) ---
    mzi_loss_db: float = 3.0                # MZI modulator insertion loss
    combiner_loss_db: float = 3.0           # 3:1 wavelength combiner
    sfg_conversion_loss_db: float = 10.0    # SFG conversion efficiency (~10%)
    awg_loss_db: float = 3.0                # AWG demux insertion loss
    edge_coupling_loss_db: float = 2.0      # Edge coupling (1 dB/facet x 2)

    # --- Timing ---
    clock_freq_mhz: float = 617.0           # Kerr clock frequency
    c_speed_um_ps: float = 299.792          # Speed of light in um/ps

    # --- Input wavelengths (nm) ---
    lambda_red_nm: float = 1550.0           # RED = trit value -1
    lambda_green_nm: float = 1310.0         # GREEN = trit value 0
    lambda_blue_nm: float = 1064.0          # BLUE = trit value +1

    @property
    def pe_pitch_um(self) -> float:
        return self.pe_width_um + self.pe_spacing_um

    @property
    def array_width_um(self) -> float:
        return self.n_cols * self.pe_pitch_um

    @property
    def array_height_um(self) -> float:
        return self.n_rows * self.pe_pitch_um

    @property
    def v_group_um_ps(self) -> float:
        """Group velocity in waveguide (um/ps)."""
        return self.c_speed_um_ps / self.refractive_index

    @property
    def clock_period_ps(self) -> float:
        return 1e6 / self.clock_freq_mhz  # ~1621 ps


# =============================================================================
# PROCESS VARIATION MODEL
# =============================================================================

@dataclass
class ProcessVariation:
    """
    Defines the Gaussian variation ranges for each fab parameter.

    CONVENTION: sigma values are 1-sigma. The distribution is clipped at
    +/- 3 sigma to avoid physically impossible values.

    WHY THESE VALUES:
    -----------------
    Waveguide width (sigma = 6.67nm, so 3*sigma = 20nm):
        DRC rule WG.W.1 specifies 500nm +/- 20nm. Modern TFLN foundries
        (e.g., HyperLight, LIGENTEC) achieve ~10nm uniformity across a die,
        but wafer-to-wafer variation pushes this to ~20nm. We use 3*sigma = 20nm
        which means 99.7% of chips fall within the DRC spec.

    Ring coupling gap (sigma = 5nm, so 3*sigma = 15nm):
        DRC rule RING.G.1 specifies 150nm +/- 20nm. The coupling gap controls
        the ring's extinction ratio and Q-factor. Tighter tolerance than the
        waveguide width because it's a gap (defined by two edges).

    PPLN poling period (sigma = 0.033um, so 3*sigma = 0.1um):
        Representative T4 G+G mid-range period (9.27 um, corrected Sellmeier).
        Actual periods span 5.4-12.7 um across 6 triplets. DRC_RULES.md
        Section 10.1: poling period tolerance +/- 50nm. We use a slightly
        more conservative 3*sigma = 100nm. Poling uniformity depends on
        the voltage pulse shape and LiNbO3 crystal quality. Period errors
        shift the phase-matching bandwidth.

    Etch depth (sigma = 3.33nm, so 3*sigma = 10nm):
        DRC_RULES.md Section 10.1: 400nm +/- 10nm. RIE etch depth is
        controlled by time and plasma conditions. Across-wafer uniformity
        is typically 2-5%. A 10nm variation on 400nm is 2.5%, achievable
        with modern TFLN processes.

    Propagation loss (sigma = 0.167 dB/cm, so 3*sigma = 0.5 dB/cm):
        DRC_RULES.md targets <3 dB/cm. Nominal is 2.0 dB/cm. Loss depends
        on sidewall roughness (set by etch quality), material absorption,
        and waveguide geometry. 0.5 dB/cm variation at 3*sigma is realistic.

    Refractive index (sigma = 0.00167, so 3*sigma = 0.005):
        LiNbO3 refractive index varies with crystal orientation, stoichiometry,
        and temperature. The extraordinary index at 1550nm is ~2.138 for
        bulk, higher in thin-film due to confinement. We use 2.2 as nominal
        with +/- 0.005 at 3*sigma.
    """
    # Parameter: (1-sigma value)
    waveguide_width_sigma_nm: float = 6.67     # 3*sigma = 20nm
    ring_gap_sigma_nm: float = 5.0             # 3*sigma = 15nm
    ppln_period_sigma_um: float = 0.033        # 3*sigma = 0.1um
    etch_depth_sigma_nm: float = 3.33          # 3*sigma = 10nm
    prop_loss_sigma_db_per_cm: float = 0.167   # 3*sigma = 0.5 dB/cm
    refractive_index_sigma: float = 0.00167    # 3*sigma = 0.005

    # Component loss variations (1-sigma)
    mzi_loss_sigma_db: float = 0.5             # MZI loss varies with alignment
    combiner_loss_sigma_db: float = 0.3        # Combiner loss variation
    sfg_loss_sigma_db: float = 1.5             # SFG efficiency is sensitive
    awg_loss_sigma_db: float = 0.5             # AWG loss variation
    coupling_loss_sigma_db: float = 0.5        # Facet quality variation


# =============================================================================
# SAMPLED CHIP (one Monte Carlo trial)
# =============================================================================

@dataclass
class SampledChip:
    """
    One Monte Carlo realization of the chip — a specific set of
    fab parameter values drawn from the process variation distributions.
    """
    waveguide_width_nm: float = 500.0
    ring_coupling_gap_nm: float = 150.0
    ppln_poling_period_um: float = 9.27
    etch_depth_nm: float = 400.0
    prop_loss_db_per_cm: float = 2.0
    refractive_index: float = 2.2
    mzi_loss_db: float = 3.0
    combiner_loss_db: float = 3.0
    sfg_conversion_loss_db: float = 10.0
    awg_loss_db: float = 3.0
    edge_coupling_loss_db: float = 2.0


def sample_chip(nominal: NominalDesign, variation: ProcessVariation,
                rng: np.random.Generator) -> SampledChip:
    """
    Draw one random chip realization from the process variation model.

    Uses truncated Gaussian: values are clipped to +/- 3*sigma to avoid
    physically impossible results (e.g., negative waveguide width).
    """
    def draw(mean: float, sigma: float) -> float:
        """Draw from Gaussian, clipped at +/- 3*sigma."""
        val = rng.normal(mean, sigma)
        return np.clip(val, mean - 3 * sigma, mean + 3 * sigma)

    # For losses, ensure they don't go negative
    def draw_positive(mean: float, sigma: float) -> float:
        val = draw(mean, sigma)
        return max(val, 0.1)  # Physical minimum — some loss always exists

    return SampledChip(
        waveguide_width_nm=draw(nominal.waveguide_width_nm,
                                variation.waveguide_width_sigma_nm),
        ring_coupling_gap_nm=draw(nominal.ring_coupling_gap_nm,
                                  variation.ring_gap_sigma_nm),
        ppln_poling_period_um=draw(nominal.ppln_poling_period_um,
                                   variation.ppln_period_sigma_um),
        etch_depth_nm=draw(nominal.etch_depth_nm,
                           variation.etch_depth_sigma_nm),
        prop_loss_db_per_cm=draw_positive(nominal.prop_loss_db_per_cm,
                                          variation.prop_loss_sigma_db_per_cm),
        refractive_index=draw(nominal.refractive_index,
                              variation.refractive_index_sigma),
        mzi_loss_db=draw_positive(nominal.mzi_loss_db,
                                  variation.mzi_loss_sigma_db),
        combiner_loss_db=draw_positive(nominal.combiner_loss_db,
                                       variation.combiner_loss_sigma_db),
        sfg_conversion_loss_db=draw_positive(nominal.sfg_conversion_loss_db,
                                             variation.sfg_loss_sigma_db),
        awg_loss_db=draw_positive(nominal.awg_loss_db,
                                  variation.awg_loss_sigma_db),
        edge_coupling_loss_db=draw_positive(nominal.edge_coupling_loss_db,
                                            variation.coupling_loss_sigma_db),
    )


# =============================================================================
# VALIDATION CHECKS (reimplemented from monolithic_chip_9x9.py)
# =============================================================================
#
# Each check returns (passed: bool, metric_value: float, margin: float)
# where margin = how far inside the acceptable range we are (positive = good)

def check_loss_budget(chip: SampledChip, nominal: NominalDesign) -> Tuple[bool, float, float]:
    """
    CHECK 1: Loss Budget — does the signal reach the detectors?

    Replicates the loss budget calculation from monolithic_chip_9x9.py
    run_integrated_validation() section [2/4].

    The total optical path goes:
        laser -> edge coupling -> MZI modulator -> combiner ->
        routing waveguide -> 9 PEs (horizontal) -> output routing ->
        AWG demux -> photodetector

    Each segment has propagation loss (length-dependent) plus component
    insertion losses (fixed per component).

    PASS CRITERION: Power at detector > detector sensitivity (-30 dBm)
                    i.e., power margin > 0 dB
    """
    # Propagation loss depends on waveguide width and etch depth through
    # the effective index and mode confinement. For this analysis, we
    # model it directly via the sampled prop_loss value.
    prop_loss_db_per_um = chip.prop_loss_db_per_cm / 1e4

    # Path lengths (same geometry as nominal — layout doesn't change)
    encoder_path_um = nominal.ioc_input_width_um          # ~180 um
    routing_input_um = nominal.routing_gap_um              # ~60 um
    pe_horizontal_um = nominal.n_cols * nominal.pe_pitch_um  # ~495 um
    routing_output_um = (nominal.routing_gap_um +
                         nominal.n_cols * nominal.pe_pitch_um)  # worst case
    decoder_path_um = nominal.ioc_output_width_um          # ~200 um

    total_path_um = (encoder_path_um + routing_input_um +
                     pe_horizontal_um + routing_output_um + decoder_path_um)

    # Propagation loss
    propagation_loss_db = total_path_um * prop_loss_db_per_um

    # Total loss = propagation + all component losses
    total_loss_db = (propagation_loss_db +
                     chip.mzi_loss_db +
                     chip.combiner_loss_db +
                     chip.sfg_conversion_loss_db +
                     chip.awg_loss_db +
                     chip.edge_coupling_loss_db)

    # Power at detector
    power_at_detector_dbm = nominal.laser_power_dbm - total_loss_db
    margin_db = power_at_detector_dbm - nominal.detector_sensitivity_dbm

    passed = margin_db > 0
    return passed, total_loss_db, margin_db


def check_wavelength_collision(chip: SampledChip, nominal: NominalDesign) -> Tuple[bool, float, float]:
    """
    CHECK 2: Wavelength Collision — do SFG products stay separable?

    The 3 input wavelengths (1550/1310/1064 nm) produce 6 SFG products
    via 1/lambda_out = 1/lambda_a + 1/lambda_b. The AWG demux at the
    output must resolve these into separate channels.

    Process variation affects the PPLN poling period, which shifts the
    phase-matching condition. A shifted poling period means slightly
    different SFG conversion efficiency vs. wavelength, but the output
    wavelength itself is set by energy conservation (1/lambda_out =
    1/lambda_a + 1/lambda_b) — it does NOT depend on the poling period.

    However, the refractive index variation affects the effective index,
    which introduces a small wavelength-dependent phase shift. The output
    wavelength is still determined by energy conservation, but the
    EFFECTIVE wavelength seen by the ring resonators shifts due to the
    index change.

    For the collision check, what matters is whether the AWG can still
    separate the 6 SFG products. The AWG channel spacing is fixed by
    the AWG geometry, but the actual SFG wavelengths shift slightly with
    effective index.

    We model this as: the SFG output wavelengths are fixed by energy
    conservation (lambda_out = lambda_a * lambda_b / (lambda_a + lambda_b)),
    but the AWG's channel center wavelengths shift with refractive index.
    The critical metric is the MINIMUM spacing between any two SFG products
    compared to the AWG's minimum resolvable spacing.

    PASS CRITERION: Minimum SFG product spacing > 20nm
                    (AWG needs ~20nm to cleanly separate channels)
    """
    # SFG output wavelengths — determined purely by energy conservation
    # These don't change with fab process (photon energy is conserved)
    lambdas = [nominal.lambda_red_nm, nominal.lambda_green_nm, nominal.lambda_blue_nm]

    sfg_outputs_nm = []
    for i in range(len(lambdas)):
        for j in range(i, len(lambdas)):
            la, lb = lambdas[i], lambdas[j]
            # SFG: 1/lambda_out = 1/lambda_a + 1/lambda_b
            lambda_out = 1.0 / (1.0 / la + 1.0 / lb)
            sfg_outputs_nm.append(lambda_out)

    sfg_outputs_nm.sort()

    # Minimum spacing between any two products
    min_spacing_nm = float('inf')
    for i in range(len(sfg_outputs_nm)):
        for j in range(i + 1, len(sfg_outputs_nm)):
            spacing = abs(sfg_outputs_nm[j] - sfg_outputs_nm[i])
            if spacing < min_spacing_nm:
                min_spacing_nm = spacing

    # AWG resolution is affected by refractive index variation.
    # A change in n shifts the AWG's channel centers.
    # The AWG free spectral range (FSR) and channel spacing depend on
    # the path length difference between array arms, which scales with n.
    # A delta_n / n_nominal fractional change shifts all channels by that fraction.
    delta_n = chip.refractive_index - nominal.refractive_index
    fractional_shift = delta_n / nominal.refractive_index

    # This shift affects the AWG's ability to resolve channels.
    # The AWG passband width narrows or broadens slightly.
    # We model the effective minimum resolvable spacing as:
    awg_min_resolution_nm = 20.0 * (1.0 + 2.0 * abs(fractional_shift))
    # (The 2x factor is because both the SFG products and AWG channels
    #  experience the index shift, doubling the effective misalignment)

    # Effective margin: how much spare spacing we have beyond what AWG needs
    margin_nm = min_spacing_nm - awg_min_resolution_nm

    passed = margin_nm > 0
    return passed, min_spacing_nm, margin_nm


def check_ring_resonator_tuning(chip: SampledChip, nominal: NominalDesign) -> Tuple[bool, float, float]:
    """
    CHECK 3: Ring Resonator Tuning — do rings still select correct channels?

    Ring resonators are used throughout the chip:
    - In the IOC region for wavelength filtering
    - In the Kerr clock for self-pulsing

    The resonance wavelength of a ring is:
        lambda_res = 2 * pi * R * n_eff / m    (m = mode order)

    where n_eff depends on:
    - Waveguide width (changes mode confinement)
    - Etch depth (changes slab thickness)
    - Material refractive index

    Process variations shift lambda_res. If it shifts too far,
    the ring selects the wrong channel or falls between channels.

    The ring can be thermally tuned via heaters (TiN heaters on the chip),
    but this has limits — typical tuning range is ~2-5 nm for LiNbO3.

    PASS CRITERION: Resonance wavelength shift < thermal tuning range (5 nm)
    """
    # Ring parameters
    ring_radius_um = 5.0  # From DRC: RING.R.1 nominal = 5.0 um
    thermal_tuning_range_nm = 5.0  # nm — achievable with TiN heater

    # Effective index model:
    # n_eff depends on waveguide width, etch depth, and material index.
    # We use a linearized sensitivity model based on published TFLN data:
    #
    #   dn_eff/d(width) ~ 0.0002 per nm of width change
    #       Typical for 500nm-wide TFLN ridge waveguides. A 20nm width
    #       change shifts n_eff by ~0.004. (Ref: Zhang et al., Optica 2017;
    #       Desiatov et al., Optica 2019)
    #
    #   dn_eff/d(etch)  ~ 0.0001 per nm of etch depth change
    #       Etch depth modifies slab mode confinement. Less sensitive than
    #       width because the mode is primarily confined laterally.
    #
    #   dn_eff/d(n_mat) ~ 0.8  (80% of bulk index change)
    #       The effective index tracks the bulk material index closely
    #       for well-confined modes.

    delta_width_nm = chip.waveguide_width_nm - nominal.waveguide_width_nm
    delta_etch_nm = chip.etch_depth_nm - nominal.etch_depth_nm
    delta_n_mat = chip.refractive_index - nominal.refractive_index

    # Effective index change
    dn_eff = (0.0002 * delta_width_nm +
              0.0001 * delta_etch_nm +
              0.8 * delta_n_mat)

    # Resonance wavelength shift
    # lambda_res = 2*pi*R*n_eff/m  →  d(lambda)/lambda = dn_eff/n_eff
    # For lambda ~ 1550 nm:
    lambda_target_nm = 1550.0
    n_eff_nominal = nominal.refractive_index * 0.85  # Rough effective index

    delta_lambda_nm = lambda_target_nm * (dn_eff / n_eff_nominal)

    # Coupling gap also affects the ring Q-factor and extinction ratio
    # A wider gap → lower coupling → higher Q but less extinction
    # A narrower gap → higher coupling → lower Q but more extinction
    # The gap doesn't directly shift the resonance wavelength, but it
    # affects whether the ring can effectively filter. We include it
    # as a secondary pass/fail: if gap is too far from nominal, the
    # ring's extinction ratio drops below useful levels.
    delta_gap_nm = chip.ring_coupling_gap_nm - nominal.ring_coupling_gap_nm
    gap_penalty_nm = abs(delta_gap_nm) * 0.02  # Small contribution to effective shift

    total_shift_nm = abs(delta_lambda_nm) + gap_penalty_nm

    margin_nm = thermal_tuning_range_nm - total_shift_nm

    passed = margin_nm > 0
    return passed, total_shift_nm, margin_nm


def check_path_timing(chip: SampledChip, nominal: NominalDesign) -> Tuple[bool, float, float]:
    """
    CHECK 4: Path-Length Timing — does timing skew stay acceptable?

    The monolithic chip uses path-length matching to synchronize photon
    arrival at each PE. The architecture ensures:

    (a) Activation paths (IOC encoder → PE[row, 0]) are all the same
        horizontal distance (ROUTING_GAP = 60 um), so they're inherently
        matched. Process variation doesn't change the geometry.

    (b) Weight paths (bus → PE via vertical drops) are equalized using
        serpentine meanders. The meanders add extra path length to shorter
        routes so all weights arrive simultaneously.

    Process variation affects timing through the refractive index:
    - A different n means a different group velocity
    - If n varies across the chip (e.g., due to etch depth non-uniformity),
      paths that are geometrically equal may have different optical path lengths

    We model within-chip index variation as: the index at each PE differs
    slightly from nominal, with spatial correlation (nearby PEs are similar).

    PASS CRITERION: Maximum timing skew < 5% of clock period
                    (5% of 1621 ps = 81 ps)
    """
    # Group velocity with this chip's refractive index
    v_group = nominal.c_speed_um_ps / chip.refractive_index

    # The path-length equalization targets a fixed geometric length
    # for all weight paths. With perfect equalization, all paths are
    # equal to the longest path: (n_rows - 1) * pe_pitch.
    max_weight_path_um = (nominal.n_rows - 1) * nominal.pe_pitch_um  # 440 um

    # The timing of each path is: t = path_length / v_group
    # If v_group varies across the chip, the timing varies.
    #
    # Model: within-chip index variation is ~10% of chip-to-chip variation
    # This is because most of the process variation is wafer-scale, not die-scale.
    within_chip_index_sigma = 0.1 * abs(chip.refractive_index - nominal.refractive_index) + 0.0001

    # The worst-case skew is between two paths at opposite ends of the chip
    # where the index differs by 2*within_chip_sigma
    delta_n_within = 2 * within_chip_index_sigma

    # Timing skew from index non-uniformity
    # t = L / (c / n)  = L * n / c
    # dt = L * dn / c
    timing_skew_ps = max_weight_path_um * delta_n_within / nominal.c_speed_um_ps

    # Also consider geometric variation — etch depth non-uniformity
    # changes the effective waveguide cross-section, which changes n_eff.
    # This adds ~0.01 ps of skew per 1nm etch variation across 440um path.
    etch_contribution_ps = abs(chip.etch_depth_nm - nominal.etch_depth_nm) * 0.01

    total_skew_ps = timing_skew_ps + etch_contribution_ps

    # Maximum acceptable skew: 5% of clock period
    max_skew_ps = 0.05 * nominal.clock_period_ps
    margin_ps = max_skew_ps - total_skew_ps

    # Also compute skew as percentage of clock period
    skew_percent = (total_skew_ps / nominal.clock_period_ps) * 100

    passed = margin_ps > 0
    return passed, skew_percent, margin_ps


def check_sfg_phase_matching(chip: SampledChip, nominal: NominalDesign) -> Tuple[bool, float, float]:
    """
    CHECK 5: SFG Phase Matching — is PPLN still quasi-phase-matched?

    Sum-frequency generation requires phase matching:
        k_out = k_a + k_b + 2*pi/Lambda_poling

    where Lambda_poling is the PPLN poling period. If the poling period
    drifts, the phase mismatch (delta_k) grows, and SFG efficiency drops.

    The SFG conversion efficiency scales as:
        eta ~ sinc^2(delta_k * L / 2)

    where L is the mixer length (~20 um). The -3dB bandwidth in delta_k
    corresponds to delta_k * L/2 ~ 0.886*pi.

    We compute the phase mismatch from the poling period error and check
    if the efficiency is still within a usable range.

    PASS CRITERION: SFG efficiency > 50% of nominal (i.e., < 3dB penalty)
    """
    # Phase-matching for SFG in PPLN:
    #   k_a + k_b = k_out + K_grating
    # where K_grating = 2*pi / Lambda_poling compensates the material dispersion.
    #
    # The NOMINAL poling period is chosen to achieve perfect phase matching
    # at the nominal refractive index. We first compute what that period
    # should be, then evaluate how the sampled chip's actual period and
    # index deviate from it.
    #
    # For the R+B case (1550 + 1064 → 630.9nm), which has the tightest
    # phase-matching bandwidth:

    lambda_a_um = nominal.lambda_red_nm / 1000    # 1.550 um
    lambda_b_um = nominal.lambda_blue_nm / 1000   # 1.064 um
    lambda_out_um = 1.0 / (1.0/lambda_a_um + 1.0/lambda_b_um)  # 0.6309 um

    # Compute the nominal phase-matched poling period from the nominal index
    n_nom = nominal.refractive_index
    k_a_nom = 2 * np.pi * n_nom / lambda_a_um
    k_b_nom = 2 * np.pi * n_nom / lambda_b_um
    k_out_nom = 2 * np.pi * n_nom / lambda_out_um
    delta_k_material_nom = k_a_nom + k_b_nom - k_out_nom
    # This is what the grating must compensate at nominal
    # Lambda_poling_ideal = 2*pi / delta_k_material_nom
    # (This differs from the hard-coded 6.75um because of dispersion)
    # The design assumes the poling period IS this ideal value.

    # Now compute phase mismatch for the SAMPLED chip
    n_chip = chip.refractive_index
    k_a = 2 * np.pi * n_chip / lambda_a_um
    k_b = 2 * np.pi * n_chip / lambda_b_um
    k_out = 2 * np.pi * n_chip / lambda_out_um
    delta_k_material = k_a + k_b - k_out

    # The grating vector uses the sampled poling period.
    # But the sampled period is a variation around the NOMINAL period,
    # which was designed to match delta_k_material_nom exactly.
    # So we express the sampled period as the nominal ideal + a delta:
    #
    #   Lambda_sampled = Lambda_ideal * (chip.ppln / nominal.ppln)
    #
    # The delta from the process variation in ppln_poling_period_um
    # represents a fractional error in the actual poling period.
    ppln_ratio = chip.ppln_poling_period_um / nominal.ppln_poling_period_um
    k_grating = delta_k_material_nom / ppln_ratio  # Scales inversely with period

    # Phase mismatch = what the material needs minus what the grating provides
    delta_k = delta_k_material - k_grating  # 1/um

    # Mixer length (from DRC: PPLN.L.1, target 20um)
    mixer_length_um = 20.0

    # SFG efficiency relative to perfect phase matching
    arg = delta_k * mixer_length_um / 2.0
    if abs(arg) < 1e-10:
        efficiency_ratio = 1.0
    else:
        efficiency_ratio = (np.sin(arg) / arg) ** 2

    # Efficiency in dB relative to nominal
    if efficiency_ratio > 1e-10:
        efficiency_penalty_db = -10 * np.log10(efficiency_ratio)
    else:
        efficiency_penalty_db = 100.0  # Effectively zero efficiency

    # PASS: efficiency penalty < 3 dB (still >50% of nominal)
    max_penalty_db = 3.0
    margin_db = max_penalty_db - efficiency_penalty_db

    passed = margin_db > 0
    return passed, efficiency_penalty_db, margin_db


# =============================================================================
# MONTE CARLO ENGINE
# =============================================================================

@dataclass
class TrialResult:
    """Results from a single Monte Carlo trial."""
    chip: SampledChip

    # Per-check results: (passed, metric, margin)
    loss_budget: Tuple[bool, float, float] = (True, 0.0, 0.0)
    wavelength_collision: Tuple[bool, float, float] = (True, 0.0, 0.0)
    ring_tuning: Tuple[bool, float, float] = (True, 0.0, 0.0)
    path_timing: Tuple[bool, float, float] = (True, 0.0, 0.0)
    sfg_phase_matching: Tuple[bool, float, float] = (True, 0.0, 0.0)

    @property
    def all_passed(self) -> bool:
        return (self.loss_budget[0] and
                self.wavelength_collision[0] and
                self.ring_tuning[0] and
                self.path_timing[0] and
                self.sfg_phase_matching[0])


def run_monte_carlo(n_trials: int = 10000, seed: int = 42,
                    nominal: Optional[NominalDesign] = None,
                    variation: Optional[ProcessVariation] = None) -> List[TrialResult]:
    """
    Run the Monte Carlo process variation analysis.

    Args:
        n_trials: Number of random chip realizations to test
        seed: Random seed for reproducibility
        nominal: Nominal design parameters (uses defaults if None)
        variation: Process variation model (uses defaults if None)

    Returns:
        List of TrialResult objects, one per trial
    """
    if nominal is None:
        nominal = NominalDesign()
    if variation is None:
        variation = ProcessVariation()

    rng = np.random.default_rng(seed)
    results = []

    print(f"\nRunning {n_trials:,} Monte Carlo trials...")
    print(f"Seed: {seed}")
    print(f"Parameters varied: 11 (6 geometric/material + 5 component losses)")
    print()

    t_start = time.time()
    progress_interval = n_trials // 20  # Print progress every 5%

    for i in range(n_trials):
        # Sample a random chip
        chip = sample_chip(nominal, variation, rng)

        # Run all checks
        trial = TrialResult(chip=chip)
        trial.loss_budget = check_loss_budget(chip, nominal)
        trial.wavelength_collision = check_wavelength_collision(chip, nominal)
        trial.ring_tuning = check_ring_resonator_tuning(chip, nominal)
        trial.path_timing = check_path_timing(chip, nominal)
        trial.sfg_phase_matching = check_sfg_phase_matching(chip, nominal)

        results.append(trial)

        # Progress indicator
        if progress_interval > 0 and (i + 1) % progress_interval == 0:
            pct = (i + 1) / n_trials * 100
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed
            remaining = (n_trials - i - 1) / rate
            print(f"  [{pct:5.1f}%] {i+1:,}/{n_trials:,} trials "
                  f"({elapsed:.1f}s elapsed, ~{remaining:.1f}s remaining)")

    elapsed = time.time() - t_start
    print(f"\nCompleted {n_trials:,} trials in {elapsed:.2f}s "
          f"({n_trials/elapsed:.0f} trials/sec)")

    return results


# =============================================================================
# ANALYSIS & REPORTING
# =============================================================================

def analyze_results(results: List[TrialResult], nominal: NominalDesign) -> Dict:
    """
    Analyze Monte Carlo results and compute summary statistics.
    """
    n = len(results)

    # Per-check pass counts
    loss_pass = sum(1 for r in results if r.loss_budget[0])
    collision_pass = sum(1 for r in results if r.wavelength_collision[0])
    ring_pass = sum(1 for r in results if r.ring_tuning[0])
    timing_pass = sum(1 for r in results if r.path_timing[0])
    sfg_pass = sum(1 for r in results if r.sfg_phase_matching[0])
    all_pass = sum(1 for r in results if r.all_passed)

    # Extract metric arrays
    loss_margins = np.array([r.loss_budget[2] for r in results])
    collision_margins = np.array([r.wavelength_collision[2] for r in results])
    ring_margins = np.array([r.ring_tuning[2] for r in results])
    timing_margins = np.array([r.path_timing[2] for r in results])
    sfg_margins = np.array([r.sfg_phase_matching[2] for r in results])

    loss_metrics = np.array([r.loss_budget[1] for r in results])
    ring_shifts = np.array([r.ring_tuning[1] for r in results])
    timing_skews = np.array([r.path_timing[1] for r in results])
    sfg_penalties = np.array([r.sfg_phase_matching[1] for r in results])

    # Extract parameter arrays for sensitivity analysis
    wg_widths = np.array([r.chip.waveguide_width_nm for r in results])
    gaps = np.array([r.chip.ring_coupling_gap_nm for r in results])
    ppln_periods = np.array([r.chip.ppln_poling_period_um for r in results])
    etch_depths = np.array([r.chip.etch_depth_nm for r in results])
    prop_losses = np.array([r.chip.prop_loss_db_per_cm for r in results])
    ref_indices = np.array([r.chip.refractive_index for r in results])
    pass_fail = np.array([1 if r.all_passed else 0 for r in results])

    analysis = {
        'n_trials': n,

        # Yields
        'yield_overall': all_pass / n * 100,
        'yield_loss_budget': loss_pass / n * 100,
        'yield_collision': collision_pass / n * 100,
        'yield_ring_tuning': ring_pass / n * 100,
        'yield_timing': timing_pass / n * 100,
        'yield_sfg_phase': sfg_pass / n * 100,

        # Margins
        'loss_margin_mean': np.mean(loss_margins),
        'loss_margin_min': np.min(loss_margins),
        'loss_margin_std': np.std(loss_margins),
        'collision_margin_mean': np.mean(collision_margins),
        'collision_margin_min': np.min(collision_margins),
        'ring_margin_mean': np.mean(ring_margins),
        'ring_margin_min': np.min(ring_margins),
        'timing_margin_mean': np.mean(timing_margins),
        'timing_margin_min': np.min(timing_margins),
        'sfg_margin_mean': np.mean(sfg_margins),
        'sfg_margin_min': np.min(sfg_margins),

        # Metric distributions
        'loss_total_db': loss_metrics,
        'ring_shift_nm': ring_shifts,
        'timing_skew_pct': timing_skews,
        'sfg_penalty_db': sfg_penalties,
        'loss_margins': loss_margins,
        'collision_margins': collision_margins,
        'ring_margins': ring_margins,
        'timing_margins': timing_margins,
        'sfg_margins': sfg_margins,

        # Parameter arrays (for sensitivity)
        'wg_widths': wg_widths,
        'gaps': gaps,
        'ppln_periods': ppln_periods,
        'etch_depths': etch_depths,
        'prop_losses': prop_losses,
        'ref_indices': ref_indices,
        'pass_fail': pass_fail,
    }

    # --- Sensitivity analysis ---
    # Compute correlation between each parameter and overall pass/fail
    # Also compute "yield impact" — how much does tightening each parameter
    # by 1 sigma improve yield?
    param_names = ['Waveguide Width', 'Coupling Gap', 'PPLN Period',
                   'Etch Depth', 'Prop Loss', 'Refractive Index']
    param_arrays = [wg_widths, gaps, ppln_periods, etch_depths, prop_losses, ref_indices]

    correlations = {}
    for name, arr in zip(param_names, param_arrays):
        # Point-biserial correlation with pass/fail
        if np.std(arr) > 0 and np.std(pass_fail) > 0:
            corr = np.corrcoef(arr, pass_fail)[0, 1]
        else:
            corr = 0.0
        correlations[name] = corr

    # Rank parameters by |correlation| with yield
    sensitivity_ranking = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
    analysis['sensitivity_ranking'] = sensitivity_ranking
    analysis['correlations'] = correlations

    # --- Yield vs parameter tolerance sweep ---
    # For the top parameter, compute yield at different sigma multiples
    # (This answers: "What if we specified tighter tolerances?")
    analysis['tolerance_sweep'] = {}
    for name, arr in zip(param_names, param_arrays):
        nominal_val = np.mean(arr)  # Close to nominal by construction
        deviations = np.abs(arr - nominal_val)
        sorted_devs = np.sort(deviations)

        # At each percentile of deviation, what's the yield?
        percentiles = [50, 75, 90, 95, 99, 100]
        sweep = []
        for pct in percentiles:
            idx = min(int(pct / 100 * n), n - 1)
            threshold = sorted_devs[idx]
            # Chips within this tolerance
            mask = deviations <= threshold
            if np.sum(mask) > 0:
                yield_at_tolerance = np.mean(pass_fail[mask]) * 100
            else:
                yield_at_tolerance = 0.0
            sweep.append((pct, threshold, yield_at_tolerance))
        analysis['tolerance_sweep'][name] = sweep

    return analysis


def print_summary(analysis: Dict, nominal: NominalDesign) -> None:
    """Print a clear terminal summary of the Monte Carlo results."""

    print()
    print("=" * 72)
    print("  MONTE CARLO PROCESS VARIATION ANALYSIS — MONOLITHIC 9x9 N-RADIX CHIP")
    print("=" * 72)

    print(f"\n  Trials: {analysis['n_trials']:,}")
    print(f"  Chip: 9x9 PE array, LiNbO3 (TFLN), split-edge topology")
    print(f"  Clock: {nominal.clock_freq_mhz:.0f} MHz Kerr (IOC-internal)")

    # --- Per-check yields ---
    print(f"\n{'='*72}")
    print(f"  {'CHECK':<35} {'YIELD':>8}  {'MARGIN (worst)':>14}  {'MARGIN (mean)':>13}")
    print(f"  {'-'*35} {'-'*8}  {'-'*14}  {'-'*13}")

    checks = [
        ('Loss Budget',          'yield_loss_budget',  'loss_margin_min',      'loss_margin_mean',      'dB'),
        ('Wavelength Collision',  'yield_collision',    'collision_margin_min', 'collision_margin_mean', 'nm'),
        ('Ring Resonator Tuning', 'yield_ring_tuning',  'ring_margin_min',      'ring_margin_mean',      'nm'),
        ('Path Timing Skew',     'yield_timing',       'timing_margin_min',    'timing_margin_mean',    'ps'),
        ('SFG Phase Matching',   'yield_sfg_phase',    'sfg_margin_min',       'sfg_margin_mean',       'dB'),
    ]

    for name, yield_key, margin_min_key, margin_mean_key, unit in checks:
        y = analysis[yield_key]
        m_min = analysis[margin_min_key]
        m_mean = analysis[margin_mean_key]
        status = "OK" if y > 99.0 else ("WARN" if y > 95.0 else "LOW")
        print(f"  {name:<35} {y:7.2f}%  {m_min:+10.2f} {unit:<3}  {m_mean:+9.2f} {unit:<3}  [{status}]")

    # --- Overall yield ---
    overall = analysis['yield_overall']
    print(f"\n  {'='*68}")
    print(f"  OVERALL YIELD (all checks pass): {overall:.2f}%")

    if overall >= 99:
        verdict = "EXCELLENT — production-ready process margins"
    elif overall >= 95:
        verdict = "GOOD — acceptable for low-volume / prototyping"
    elif overall >= 90:
        verdict = "MARGINAL — consider tightening critical tolerances"
    elif overall >= 80:
        verdict = "POOR — significant yield loss expected"
    else:
        verdict = "UNACCEPTABLE — redesign required"

    print(f"  Verdict: {verdict}")
    print(f"  {'='*68}")

    # --- Sensitivity ranking ---
    print(f"\n  SENSITIVITY ANALYSIS (which parameter matters most?)")
    print(f"  {'-'*68}")
    print(f"  {'Parameter':<25} {'|r| with yield':>15}  {'Impact':<15}")
    print(f"  {'-'*25} {'-'*15}  {'-'*15}")

    for name, corr in analysis['sensitivity_ranking']:
        if abs(corr) > 0.1:
            impact = "HIGH"
        elif abs(corr) > 0.03:
            impact = "MODERATE"
        else:
            impact = "LOW"
        print(f"  {name:<25} {abs(corr):>15.4f}  {impact:<15}")

    print()
    print(f"  Note: |r| = absolute point-biserial correlation between")
    print(f"  parameter value and pass/fail outcome. Higher = more sensitive.")

    # --- Worst-case margins ---
    print(f"\n  WORST-CASE MARGINS (from {analysis['n_trials']:,} trials)")
    print(f"  {'-'*68}")
    print(f"  Loss budget worst margin:       {analysis['loss_margin_min']:+.2f} dB")
    print(f"  Collision spacing worst margin:  {analysis['collision_margin_min']:+.2f} nm")
    print(f"  Ring tuning worst margin:        {analysis['ring_margin_min']:+.2f} nm")
    print(f"  Timing skew worst margin:        {analysis['timing_margin_min']:+.2f} ps")
    print(f"  SFG phase match worst margin:    {analysis['sfg_margin_min']:+.2f} dB")

    print(f"\n{'='*72}")


def generate_plots(analysis: Dict, output_dir: str) -> None:
    """Generate and save all plots."""

    os.makedirs(output_dir, exist_ok=True)

    # Use a clean style
    plt.rcParams.update({
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'axes.grid': True,
        'grid.alpha': 0.3,
        'font.size': 10,
    })

    # =========================================================================
    # Plot 1: Yield Summary Bar Chart
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 5))

    check_names = ['Loss\nBudget', 'Wavelength\nCollision', 'Ring\nTuning',
                   'Path\nTiming', 'SFG Phase\nMatching', 'OVERALL']
    yields = [analysis['yield_loss_budget'], analysis['yield_collision'],
              analysis['yield_ring_tuning'], analysis['yield_timing'],
              analysis['yield_sfg_phase'], analysis['yield_overall']]

    colors = ['#2ecc71' if y >= 99 else '#f39c12' if y >= 95 else '#e74c3c' for y in yields]
    colors[-1] = '#3498db'  # Overall in blue

    bars = ax.bar(check_names, yields, color=colors, edgecolor='black', linewidth=0.5)

    # Add value labels on bars
    for bar, y in zip(bars, yields):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{y:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=11)

    ax.set_ylim(0, 105)
    ax.set_ylabel('Yield (%)')
    ax.set_title('Monte Carlo Yield Summary — Monolithic 9x9 N-Radix Chip\n'
                 f'({analysis["n_trials"]:,} trials, Gaussian process variations)',
                 fontsize=12)
    ax.axhline(y=99, color='green', linestyle='--', alpha=0.5, label='99% target')
    ax.axhline(y=95, color='orange', linestyle='--', alpha=0.5, label='95% target')
    ax.legend(loc='lower right')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'yield_summary.png'), dpi=150)
    plt.close()
    print(f"  Saved: yield_summary.png")

    # =========================================================================
    # Plot 2: Margin Histograms (2x3 grid)
    # =========================================================================
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))

    margin_data = [
        ('Loss Budget Margin (dB)', analysis['loss_margins'], 0, 'dB'),
        ('Collision Margin (nm)', analysis['collision_margins'], 0, 'nm'),
        ('Ring Tuning Margin (nm)', analysis['ring_margins'], 0, 'nm'),
        ('Timing Margin (ps)', analysis['timing_margins'], 0, 'ps'),
        ('SFG Phase Margin (dB)', analysis['sfg_margins'], 0, 'dB'),
    ]

    for idx, (title, data, threshold, unit) in enumerate(margin_data):
        row, col = idx // 3, idx % 3
        ax = axes[row][col]

        ax.hist(data, bins=80, color='#3498db', edgecolor='none', alpha=0.8)
        ax.axvline(x=threshold, color='red', linewidth=2, linestyle='--', label='Pass/Fail')
        ax.set_xlabel(f'Margin ({unit})')
        ax.set_ylabel('Count')
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=8)

        # Shade the fail region
        xlims = ax.get_xlim()
        ax.axvspan(xlims[0], threshold, alpha=0.1, color='red')

    # Remove the empty 6th subplot
    axes[1][2].set_visible(False)

    fig.suptitle(f'Margin Distributions ({analysis["n_trials"]:,} Monte Carlo trials)',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'margin_histograms.png'), dpi=150)
    plt.close()
    print(f"  Saved: margin_histograms.png")

    # =========================================================================
    # Plot 3: Sensitivity Analysis — Parameter vs. Total Loss
    # =========================================================================
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))

    param_data = [
        ('Waveguide Width (nm)', analysis['wg_widths']),
        ('Coupling Gap (nm)', analysis['gaps']),
        ('PPLN Period (um)', analysis['ppln_periods']),
        ('Etch Depth (nm)', analysis['etch_depths']),
        ('Prop Loss (dB/cm)', analysis['prop_losses']),
        ('Refractive Index', analysis['ref_indices']),
    ]

    for idx, (label, param_vals) in enumerate(param_data):
        row, col = idx // 3, idx % 3
        ax = axes[row][col]

        # Color by pass/fail
        pass_mask = analysis['pass_fail'] == 1
        fail_mask = ~pass_mask

        ax.scatter(param_vals[pass_mask], analysis['loss_margins'][pass_mask],
                   c='#2ecc71', s=1, alpha=0.2, label='Pass')
        if np.any(fail_mask):
            ax.scatter(param_vals[fail_mask], analysis['loss_margins'][fail_mask],
                       c='#e74c3c', s=3, alpha=0.5, label='Fail')

        ax.axhline(y=0, color='red', linewidth=1, linestyle='--')
        ax.set_xlabel(label)
        ax.set_ylabel('Loss Margin (dB)')
        ax.legend(fontsize=7, markerscale=3)

    fig.suptitle('Parameter Sensitivity — Loss Budget Margin vs. Each Parameter',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sensitivity_scatter.png'), dpi=150)
    plt.close()
    print(f"  Saved: sensitivity_scatter.png")

    # =========================================================================
    # Plot 4: Total Loss Distribution
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 5))

    loss_data = analysis['loss_total_db']
    nominal_loss = 21.30  # From validation report

    ax.hist(loss_data, bins=80, color='#9b59b6', edgecolor='none', alpha=0.8,
            label='Monte Carlo distribution')
    ax.axvline(x=nominal_loss, color='blue', linewidth=2, linestyle='-',
               label=f'Nominal ({nominal_loss:.1f} dB)')

    # Mark the max acceptable loss (laser - detector sensitivity)
    max_loss = 10.0 - (-30.0)  # 40 dB
    ax.axvline(x=max_loss, color='red', linewidth=2, linestyle='--',
               label=f'Max acceptable ({max_loss:.0f} dB)')

    ax.set_xlabel('Total Optical Loss (dB)')
    ax.set_ylabel('Count')
    ax.set_title(f'Total Loss Distribution ({analysis["n_trials"]:,} trials)\n'
                 f'Mean: {np.mean(loss_data):.2f} dB, Std: {np.std(loss_data):.2f} dB')
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'loss_distribution.png'), dpi=150)
    plt.close()
    print(f"  Saved: loss_distribution.png")

    # =========================================================================
    # Plot 5: Ring Resonator Wavelength Shift Distribution
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 5))

    ring_data = analysis['ring_shift_nm']
    thermal_limit = 5.0  # nm thermal tuning range

    ax.hist(ring_data, bins=80, color='#e67e22', edgecolor='none', alpha=0.8)
    ax.axvline(x=thermal_limit, color='red', linewidth=2, linestyle='--',
               label=f'Thermal tuning limit ({thermal_limit} nm)')
    ax.axvline(x=0, color='blue', linewidth=1, linestyle='-',
               label='Nominal (no shift)')

    ax.set_xlabel('Ring Resonance Wavelength Shift (nm)')
    ax.set_ylabel('Count')
    ax.set_title(f'Ring Resonator Detuning Distribution\n'
                 f'Mean: {np.mean(ring_data):.3f} nm, '
                 f'Max: {np.max(ring_data):.3f} nm, '
                 f'Thermal limit: {thermal_limit} nm')
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'ring_shift_distribution.png'), dpi=150)
    plt.close()
    print(f"  Saved: ring_shift_distribution.png")

    # =========================================================================
    # Plot 6: SFG Phase Matching Efficiency
    # =========================================================================
    fig, ax = plt.subplots(figsize=(10, 5))

    sfg_data = analysis['sfg_penalty_db']

    ax.hist(sfg_data, bins=80, color='#1abc9c', edgecolor='none', alpha=0.8)
    ax.axvline(x=3.0, color='red', linewidth=2, linestyle='--',
               label='3 dB penalty limit')
    ax.axvline(x=0, color='blue', linewidth=1, linestyle='-',
               label='Perfect phase match')

    ax.set_xlabel('SFG Efficiency Penalty (dB)')
    ax.set_ylabel('Count')
    ax.set_title(f'SFG Phase Matching Efficiency Loss\n'
                 f'Mean penalty: {np.mean(sfg_data):.3f} dB, '
                 f'Max penalty: {np.max(sfg_data):.3f} dB')
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sfg_efficiency_distribution.png'), dpi=150)
    plt.close()
    print(f"  Saved: sfg_efficiency_distribution.png")

    # =========================================================================
    # Plot 7: Cumulative Yield vs. Process Tightness
    # =========================================================================
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))

    for idx, (name, label) in enumerate([
        ('Waveguide Width', 'nm'),
        ('Coupling Gap', 'nm'),
        ('PPLN Period', 'um'),
        ('Etch Depth', 'nm'),
        ('Prop Loss', 'dB/cm'),
        ('Refractive Index', ''),
    ]):
        row, col = idx // 3, idx % 3
        ax = axes[row][col]

        sweep = analysis['tolerance_sweep'][name]
        pcts = [s[0] for s in sweep]
        thresholds = [s[1] for s in sweep]
        sweep_yields = [s[2] for s in sweep]

        ax.plot(pcts, sweep_yields, 'o-', color='#2980b9', linewidth=2, markersize=5)
        ax.set_xlabel(f'% of chips included (by {name} tolerance)')
        ax.set_ylabel('Yield (%)')
        ax.set_title(f'{name} ({label})', fontsize=10)
        ax.set_ylim(0, 105)
        ax.axhline(y=99, color='green', linestyle='--', alpha=0.3)

        # Add tolerance values as secondary labels
        for pct, thresh, yld in sweep:
            if pct in [50, 90, 100]:
                ax.annotate(f'{thresh:.3f}', xy=(pct, yld),
                           xytext=(0, -15), textcoords='offset points',
                           fontsize=7, ha='center', color='gray')

    fig.suptitle('Yield vs. Process Tolerance Window\n'
                 '(Selecting chips within N-th percentile of each parameter)',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'yield_vs_tolerance.png'), dpi=150)
    plt.close()
    print(f"  Saved: yield_vs_tolerance.png")

    print(f"\n  All plots saved to: {output_dir}/")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 72)
    print("  MONTE CARLO PROCESS VARIATION ANALYSIS")
    print("  Monolithic 9x9 N-Radix Chip — TFLN Foundry Tolerances")
    print("  Date: 2026-02-17")
    print("=" * 72)

    # --- Configuration ---
    N_TRIALS = 10_000
    SEED = 42
    nominal = NominalDesign()
    variation = ProcessVariation()

    # --- Print parameter table ---
    print("\n  NOMINAL DESIGN PARAMETERS:")
    print(f"  {'-'*60}")
    print(f"  {'Parameter':<30} {'Nominal':>10} {'3-sigma':>10} {'Unit':<8}")
    print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*8}")
    print(f"  {'Waveguide width':<30} {nominal.waveguide_width_nm:>10.1f} {3*variation.waveguide_width_sigma_nm:>10.1f} {'nm':<8}")
    print(f"  {'Ring coupling gap':<30} {nominal.ring_coupling_gap_nm:>10.1f} {3*variation.ring_gap_sigma_nm:>10.1f} {'nm':<8}")
    print(f"  {'PPLN poling period':<30} {nominal.ppln_poling_period_um:>10.3f} {3*variation.ppln_period_sigma_um:>10.3f} {'um':<8}")
    print(f"  {'Etch depth':<30} {nominal.etch_depth_nm:>10.1f} {3*variation.etch_depth_sigma_nm:>10.1f} {'nm':<8}")
    print(f"  {'Propagation loss':<30} {nominal.prop_loss_db_per_cm:>10.2f} {3*variation.prop_loss_sigma_db_per_cm:>10.3f} {'dB/cm':<8}")
    print(f"  {'Refractive index':<30} {nominal.refractive_index:>10.3f} {3*variation.refractive_index_sigma:>10.4f} {'':<8}")
    print()
    print(f"  COMPONENT LOSS VARIATIONS (1-sigma):")
    print(f"  {'-'*60}")
    print(f"  {'MZI modulator':<30} {nominal.mzi_loss_db:>10.1f} +/- {variation.mzi_loss_sigma_db:.1f} dB")
    print(f"  {'Wavelength combiner':<30} {nominal.combiner_loss_db:>10.1f} +/- {variation.combiner_loss_sigma_db:.1f} dB")
    print(f"  {'SFG conversion':<30} {nominal.sfg_conversion_loss_db:>10.1f} +/- {variation.sfg_loss_sigma_db:.1f} dB")
    print(f"  {'AWG demux':<30} {nominal.awg_loss_db:>10.1f} +/- {variation.awg_loss_sigma_db:.1f} dB")
    print(f"  {'Edge coupling':<30} {nominal.edge_coupling_loss_db:>10.1f} +/- {variation.coupling_loss_sigma_db:.1f} dB")

    # --- Run Monte Carlo ---
    results = run_monte_carlo(
        n_trials=N_TRIALS,
        seed=SEED,
        nominal=nominal,
        variation=variation,
    )

    # --- Analyze ---
    analysis = analyze_results(results, nominal)

    # --- Print summary ---
    print_summary(analysis, nominal)

    # --- Generate plots ---
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plot_dir = os.path.join(base_dir, 'docs', 'monte_carlo_plots')
    print(f"\n  Generating plots...")
    generate_plots(analysis, plot_dir)

    # --- Write machine-readable results ---
    results_file = os.path.join(plot_dir, 'results_summary.txt')
    with open(results_file, 'w') as f:
        f.write(f"Monte Carlo Process Variation Analysis Results\n")
        f.write(f"Date: 2026-02-17\n")
        f.write(f"Trials: {N_TRIALS}\n")
        f.write(f"Seed: {SEED}\n\n")
        f.write(f"Overall Yield: {analysis['yield_overall']:.2f}%\n\n")
        f.write(f"Per-Check Yields:\n")
        f.write(f"  Loss Budget:          {analysis['yield_loss_budget']:.2f}%\n")
        f.write(f"  Wavelength Collision:  {analysis['yield_collision']:.2f}%\n")
        f.write(f"  Ring Tuning:           {analysis['yield_ring_tuning']:.2f}%\n")
        f.write(f"  Path Timing:           {analysis['yield_timing']:.2f}%\n")
        f.write(f"  SFG Phase Matching:    {analysis['yield_sfg_phase']:.2f}%\n\n")
        f.write(f"Worst-Case Margins:\n")
        f.write(f"  Loss Budget:          {analysis['loss_margin_min']:+.2f} dB\n")
        f.write(f"  Wavelength Collision:  {analysis['collision_margin_min']:+.2f} nm\n")
        f.write(f"  Ring Tuning:           {analysis['ring_margin_min']:+.2f} nm\n")
        f.write(f"  Path Timing:           {analysis['timing_margin_min']:+.2f} ps\n")
        f.write(f"  SFG Phase Matching:    {analysis['sfg_margin_min']:+.2f} dB\n\n")
        f.write(f"Sensitivity Ranking:\n")
        for name, corr in analysis['sensitivity_ranking']:
            f.write(f"  {name:<25} |r| = {abs(corr):.4f}\n")

    print(f"  Results saved to: {results_file}")

    print(f"\n{'='*72}")
    print(f"  ANALYSIS COMPLETE")
    print(f"{'='*72}")

    return analysis


if __name__ == "__main__":
    analysis = main()
