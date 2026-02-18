#!/usr/bin/env python3
"""
Monolithic 243x243 N-Radix Chip — With EDWA Amplification
==========================================================

SCALING THE MONOLITHIC DESIGN: 59,049 PEs on ONE LiNbO3 Substrate

This design takes the validated 9x9 split-edge topology and scales it to
243x243 — the target production array size. At this scale, propagation
loss kills the signal before it reaches the far side of the chip.

THE SOLUTION: Erbium-Doped Waveguide Amplifiers (EDWA)

EDWA is NATIVE to LiNbO3:
    - Er/Yb co-doping in lithium niobate is well-established
    - Optically pumped (980nm pump laser) — no electrical connection needed
    - The amplifier sections are PASSIVE from an electronic standpoint
    - Light amplifying light — stays in the photonic domain
    - Already in the layer mapping: LAYER_LOG (13,0) and LAYER_GAIN (14,0)

Strategy:
    1. Build 243x243 chip model
    2. Map signal power along every path (horizontal, vertical, weight)
    3. Find where signal crosses detector threshold
    4. Place EDWA stages at calculated intervals
    5. Re-validate with amplification

EDWA Properties (Er:LiNbO3):
    - Net gain: 10-20 dB/cm (pump-dependent)
    - Typical stage: ~500 μm long, ~10-15 dB gain
    - Pump wavelength: 980 nm (standard laser diode)
    - Signal band: 1000-1600 nm (covers all our wavelengths)
    - Noise figure: ~4-6 dB
    - Compatible with SFG outputs (visible range needs different gain medium)

Author: Wavelength-Division Ternary Optical Computer Project
"""

import numpy as np
import os

# =============================================================================
# Physical Constants
# =============================================================================

WAVEGUIDE_WIDTH = 0.5         # μm
N_LINBO3 = 2.2
C_SPEED_UM_PS = 299.792       # μm/ps
V_GROUP_UM_PS = C_SPEED_UM_PS / N_LINBO3

# PE dimensions
PE_WIDTH = 50.0               # μm
PE_HEIGHT = 50.0              # μm
PE_SPACING = 5.0              # μm
PE_PITCH = PE_WIDTH + PE_SPACING  # 55 μm

# Array
N_ROWS = 243
N_COLS = 243
ARRAY_WIDTH = N_COLS * PE_PITCH    # 13,365 μm = 1.34 cm
ARRAY_HEIGHT = N_ROWS * PE_PITCH   # 13,365 μm = 1.34 cm

# IOC regions
IOC_INPUT_WIDTH = 180.0
IOC_OUTPUT_WIDTH = 200.0
ROUTING_GAP = 60.0
MARGIN_X = 50.0
MARGIN_Y = 80.0
WEIGHT_BUS_HEIGHT = 40.0

# Chip dimensions
CHIP_WIDTH = (MARGIN_X + IOC_INPUT_WIDTH + ROUTING_GAP +
              ARRAY_WIDTH + ROUTING_GAP + IOC_OUTPUT_WIDTH + MARGIN_X)
CHIP_HEIGHT = MARGIN_Y + WEIGHT_BUS_HEIGHT + ARRAY_HEIGHT + MARGIN_Y

# Clock
CLOCK_FREQ_MHZ = 617

# =============================================================================
# Loss Model Parameters
# =============================================================================

# Propagation loss in LiNbO3 waveguides
PROP_LOSS_DB_PER_CM = 2.0     # Conservative for TFLN

# Component losses (per instance)
LOSS_MZI_DB = 3.0             # MZI modulator insertion loss
LOSS_COMBINER_DB = 3.0        # 3:1 wavelength combiner
LOSS_SFG_DB = 10.0            # SFG conversion efficiency (~10%)
LOSS_AWG_DB = 3.0             # AWG demux insertion loss
LOSS_EDGE_COUPLING_DB = 2.0   # Fiber-to-chip coupling (2 facets)
LOSS_PE_JUNCTION_DB = 0.3     # Loss per PE waveguide crossing/junction
LOSS_BEND_DB = 0.05           # Loss per waveguide bend

# Power levels
LASER_POWER_DBM = 10.0        # Input laser power per channel
DETECTOR_SENSITIVITY_DBM = -30.0  # Minimum detectable power

# =============================================================================
# EDWA (Erbium-Doped Waveguide Amplifier) Parameters
# =============================================================================

EDWA_GAIN_DB = 12.0           # Net gain per amplifier stage
EDWA_LENGTH_UM = 500.0        # Physical length of EDWA section
EDWA_NOISE_FIGURE_DB = 5.0    # Noise figure per stage
EDWA_PUMP_POWER_MW = 50.0     # Pump power needed per stage
EDWA_PUMP_WAVELENGTH_NM = 980 # Standard Er pump wavelength

# Maximum cascaded amplifier stages before noise accumulates
# ASE noise grows with each stage — eventually SNR is too low
MAX_EDWA_STAGES = 20          # Practical limit for acceptable SNR


# =============================================================================
# Signal Path Analysis
# =============================================================================

def analyze_horizontal_path(n_cols: int = N_COLS) -> dict:
    """
    Analyze signal power along the horizontal activation path.

    Path: Laser → Encoder → Routing Gap → PE[row,0] → PE[row,1] → ... → PE[row, N-1]

    The activation signal traverses all columns in a row.
    At each PE, it passes through the SFG mixer (where it interacts with
    the weight) and continues to the next PE.

    Returns detailed power map at each column position.
    """
    # Fixed losses (input chain)
    input_loss = LOSS_MZI_DB + LOSS_COMBINER_DB + LOSS_EDGE_COUPLING_DB / 2

    # Propagation through encoder + routing gap
    encoder_path_cm = (IOC_INPUT_WIDTH + ROUTING_GAP) / 1e4
    encoder_prop_loss = encoder_path_cm * PROP_LOSS_DB_PER_CM

    # Starting power at array entry
    power_at_entry_dbm = LASER_POWER_DBM - input_loss - encoder_prop_loss

    # Track power at each column
    power_map = []
    current_power = power_at_entry_dbm

    for col in range(n_cols):
        # Loss through this PE
        pe_prop_loss = (PE_WIDTH / 1e4) * PROP_LOSS_DB_PER_CM
        pe_junction_loss = LOSS_PE_JUNCTION_DB
        pe_spacing_loss = (PE_SPACING / 1e4) * PROP_LOSS_DB_PER_CM if col < n_cols - 1 else 0

        total_pe_loss = pe_prop_loss + pe_junction_loss + pe_spacing_loss

        current_power -= total_pe_loss

        power_map.append({
            'col': col,
            'power_dbm': current_power,
            'cumulative_loss_db': power_at_entry_dbm - current_power,
            'above_threshold': current_power > DETECTOR_SENSITIVITY_DBM,
            'margin_db': current_power - DETECTOR_SENSITIVITY_DBM,
        })

    return {
        'power_at_entry_dbm': power_at_entry_dbm,
        'power_map': power_map,
        'final_power_dbm': power_map[-1]['power_dbm'],
        'total_loss_db': power_at_entry_dbm - power_map[-1]['power_dbm'],
    }


def analyze_vertical_path(n_rows: int = N_ROWS) -> dict:
    """
    Analyze signal power along the vertical partial-sum path.

    Path: PE[0,col].out_v → PE[1,col].in_v → ... → PE[N-1,col].out_v → Decoder

    Partial sums accumulate vertically through the systolic array.
    This is the SFG OUTPUT signal (visible wavelengths 500-775 nm),
    which has already undergone conversion loss.

    Returns detailed power map at each row position.
    """
    # The vertical signal starts as an SFG output from PE[0, col]
    # It has already lost the SFG conversion efficiency
    sfg_output_power = LASER_POWER_DBM - LOSS_SFG_DB

    power_map = []
    current_power = sfg_output_power

    for row in range(n_rows):
        # Loss through vertical PE traversal
        pe_prop_loss = (PE_HEIGHT / 1e4) * PROP_LOSS_DB_PER_CM
        pe_junction_loss = LOSS_PE_JUNCTION_DB
        pe_spacing_loss = (PE_SPACING / 1e4) * PROP_LOSS_DB_PER_CM if row < n_rows - 1 else 0

        total_pe_loss = pe_prop_loss + pe_junction_loss + pe_spacing_loss

        current_power -= total_pe_loss

        power_map.append({
            'row': row,
            'power_dbm': current_power,
            'cumulative_loss_db': sfg_output_power - current_power,
            'above_threshold': current_power > DETECTOR_SENSITIVITY_DBM,
            'margin_db': current_power - DETECTOR_SENSITIVITY_DBM,
        })

    # Add output routing and decoder losses
    output_routing_cm = (ROUTING_GAP + IOC_OUTPUT_WIDTH) / 1e4
    output_loss = (output_routing_cm * PROP_LOSS_DB_PER_CM +
                   LOSS_AWG_DB + LOSS_EDGE_COUPLING_DB / 2)

    final_power = power_map[-1]['power_dbm'] - output_loss

    return {
        'sfg_output_power_dbm': sfg_output_power,
        'power_map': power_map,
        'power_before_decoder_dbm': power_map[-1]['power_dbm'],
        'output_chain_loss_db': output_loss,
        'final_power_at_detector_dbm': final_power,
        'total_loss_db': sfg_output_power - final_power,
    }


def analyze_weight_path(n_rows: int = N_ROWS) -> dict:
    """
    Analyze signal power along the weight distribution path.

    Path: Optical RAM → Weight Bus → Drop to column → PE[0,col] → PE[1,col] → ...

    Weights drop vertically from the bus at the top to each row.
    The farthest row (bottom) has the longest path.
    """
    # Weight signal starts from optical RAM output
    weight_power_dbm = LASER_POWER_DBM  # Assume full power from RAM

    # Bus propagation (horizontal across array)
    bus_path_cm = ARRAY_WIDTH / 1e4
    bus_loss = bus_path_cm * PROP_LOSS_DB_PER_CM

    power_map = []

    for row in range(n_rows):
        # Vertical drop distance from bus to this row
        drop_distance_um = row * PE_PITCH
        drop_loss = (drop_distance_um / 1e4) * PROP_LOSS_DB_PER_CM

        # With equalization meander, all paths are equal to max
        max_drop = (n_rows - 1) * PE_PITCH
        meander_extra = max_drop - drop_distance_um
        meander_loss = (meander_extra / 1e4) * PROP_LOSS_DB_PER_CM

        total_weight_loss = bus_loss + drop_loss + meander_loss
        power_at_pe = weight_power_dbm - total_weight_loss

        power_map.append({
            'row': row,
            'power_dbm': power_at_pe,
            'drop_distance_um': drop_distance_um,
            'meander_um': meander_extra,
            'total_path_um': drop_distance_um + meander_extra,
            'above_threshold': power_at_pe > DETECTOR_SENSITIVITY_DBM,
            'margin_db': power_at_pe - DETECTOR_SENSITIVITY_DBM,
        })

    return {
        'weight_input_power_dbm': weight_power_dbm,
        'bus_loss_db': bus_loss,
        'power_map': power_map,
    }


def find_signal_death_point(power_map: list, threshold_dbm: float = DETECTOR_SENSITIVITY_DBM) -> int:
    """Find the first position where signal drops below threshold."""
    for entry in power_map:
        if entry['power_dbm'] < threshold_dbm:
            return entry.get('col', entry.get('row', -1))
    return -1  # Never drops below threshold


# =============================================================================
# EDWA Amplifier Placement
# =============================================================================

def design_amplifier_placement(
    path_analysis: dict,
    path_type: str = "horizontal",
    target_margin_db: float = 3.0,
) -> dict:
    """
    Design optimal EDWA amplifier placement for a signal path.

    Strategy: Place amplifiers BEFORE the signal drops below a safe level.
    We want to amplify while the signal is still well above the noise floor.

    The "reamp threshold" is set to keep the signal above detector sensitivity
    + target margin at all times.

    Args:
        path_analysis: Output from analyze_horizontal_path or analyze_vertical_path
        path_type: "horizontal" or "vertical"
        target_margin_db: Minimum margin above detector sensitivity

    Returns:
        Amplifier placement plan with positions and power levels.
    """
    power_map = path_analysis['power_map']

    # Determine reamp threshold — amplify before signal drops too low
    # We want to re-amplify when signal drops to a level where one more
    # EDWA gain stage brings it back near the starting level
    if path_type == "horizontal":
        starting_power = path_analysis['power_at_entry_dbm']
    else:
        starting_power = path_analysis['sfg_output_power_dbm']

    # Reamp when signal drops by (EDWA_GAIN - margin) dB from starting level
    # This keeps the signal bouncing between starting_power and
    # starting_power - EDWA_GAIN_DB
    reamp_threshold = starting_power - EDWA_GAIN_DB + 2.0  # 2 dB headroom

    amp_positions = []
    current_power = starting_power
    n_stages = 0

    # Walk through the path and place amplifiers
    for entry in power_map:
        pos = entry.get('col', entry.get('row'))
        power = entry['power_dbm']

        # Simulate power with amplification
        # After an amp, power jumps back up by EDWA_GAIN_DB
        simulated_power = power + n_stages * EDWA_GAIN_DB

        if simulated_power < reamp_threshold and n_stages < MAX_EDWA_STAGES:
            amp_positions.append({
                'position': pos,
                'power_before_dbm': simulated_power,
                'power_after_dbm': simulated_power + EDWA_GAIN_DB,
                'stage_number': n_stages + 1,
            })
            n_stages += 1

    # Recalculate power map with amplifiers in place
    amplified_power_map = []
    amp_idx = 0
    cumulative_gain = 0.0

    for entry in power_map:
        pos = entry.get('col', entry.get('row'))

        # Check if there's an amplifier at or before this position
        while amp_idx < len(amp_positions) and amp_positions[amp_idx]['position'] <= pos:
            cumulative_gain += EDWA_GAIN_DB
            amp_idx += 1

        amplified_power = entry['power_dbm'] + cumulative_gain

        amplified_power_map.append({
            **entry,
            'amplified_power_dbm': amplified_power,
            'amplified_margin_db': amplified_power - DETECTOR_SENSITIVITY_DBM,
            'amplified_above_threshold': amplified_power > DETECTOR_SENSITIVITY_DBM,
        })

    # Calculate spacing between amplifiers
    if len(amp_positions) >= 2:
        spacings = [amp_positions[i+1]['position'] - amp_positions[i]['position']
                     for i in range(len(amp_positions) - 1)]
        avg_spacing = np.mean(spacings)
        spacing_um = avg_spacing * PE_PITCH
    elif len(amp_positions) == 1:
        avg_spacing = amp_positions[0]['position']
        spacing_um = avg_spacing * PE_PITCH
    else:
        avg_spacing = 0
        spacing_um = 0

    return {
        'n_amplifiers': len(amp_positions),
        'amp_positions': amp_positions,
        'amplified_power_map': amplified_power_map,
        'avg_spacing_pes': avg_spacing,
        'avg_spacing_um': spacing_um,
        'total_pump_power_mw': len(amp_positions) * EDWA_PUMP_POWER_MW,
        'final_power_dbm': amplified_power_map[-1]['amplified_power_dbm'] if amplified_power_map else None,
        'all_above_threshold': all(e['amplified_above_threshold'] for e in amplified_power_map),
    }


# =============================================================================
# Full Chip Analysis
# =============================================================================

def run_243x243_analysis() -> dict:
    """
    Complete analysis of the 243x243 monolithic chip.

    Phase 1: Unamplified loss profile
    Phase 2: EDWA amplifier placement
    Phase 3: Amplified validation
    """
    results = {}

    print("=" * 70)
    print("  MONOLITHIC 243×243 N-RADIX CHIP — LOSS & AMPLIFICATION ANALYSIS")
    print("=" * 70)

    print(f"\n  Chip: {CHIP_WIDTH:.0f} × {CHIP_HEIGHT:.0f} μm"
          f" ({CHIP_WIDTH/1e4:.2f} × {CHIP_HEIGHT/1e4:.2f} cm)")
    print(f"  Array: {N_ROWS}×{N_COLS} = {N_ROWS * N_COLS:,} PEs")
    print(f"  Material: X-cut LiNbO3 (TFLN)")
    print(f"  Propagation loss: {PROP_LOSS_DB_PER_CM} dB/cm")

    # =========================================================================
    # PHASE 1: Unamplified Loss Profile
    # =========================================================================

    print("\n" + "=" * 70)
    print("  PHASE 1: UNAMPLIFIED LOSS PROFILE")
    print("=" * 70)

    # --- Horizontal (activation) path ---
    print("\n[H] HORIZONTAL PATH (activation through columns)")
    print("-" * 50)

    h_analysis = analyze_horizontal_path(N_COLS)
    h_death = find_signal_death_point(h_analysis['power_map'])

    print(f"  Power at array entry: {h_analysis['power_at_entry_dbm']:.2f} dBm")
    print(f"  Power at final column: {h_analysis['final_power_dbm']:.2f} dBm")
    print(f"  Total horizontal loss: {h_analysis['total_loss_db']:.2f} dB")

    if h_death >= 0:
        print(f"  SIGNAL DEATH at column {h_death}"
              f" ({h_death * PE_PITCH:.0f} μm into array)")
        print(f"  Signal survives {h_death}/{N_COLS} columns"
              f" ({100*h_death/N_COLS:.1f}%)")
    else:
        print(f"  Signal survives all {N_COLS} columns (no death point)")

    # Show power at key positions
    key_cols = [0, 26, 53, 80, 121, 162, 202, 242]
    print(f"\n  Power at key positions:")
    print(f"  {'Col':>5} | {'Power (dBm)':>12} | {'Margin (dB)':>12} | {'Status':>8}")
    print(f"  {'-'*50}")
    for col_idx in key_cols:
        if col_idx < len(h_analysis['power_map']):
            e = h_analysis['power_map'][col_idx]
            status = "OK" if e['above_threshold'] else "DEAD"
            print(f"  {col_idx:>5} | {e['power_dbm']:>12.2f} | {e['margin_db']:>12.2f} | {status:>8}")

    results['h_unamplified'] = h_analysis

    # --- Vertical (partial sum) path ---
    print(f"\n[V] VERTICAL PATH (partial sums through rows)")
    print("-" * 50)

    v_analysis = analyze_vertical_path(N_ROWS)
    v_death = find_signal_death_point(v_analysis['power_map'])

    print(f"  SFG output power: {v_analysis['sfg_output_power_dbm']:.2f} dBm")
    print(f"  Power before decoder: {v_analysis['power_before_decoder_dbm']:.2f} dBm")
    print(f"  Output chain loss: {v_analysis['output_chain_loss_db']:.2f} dB")
    print(f"  Final power at detector: {v_analysis['final_power_at_detector_dbm']:.2f} dBm")
    print(f"  Total vertical loss: {v_analysis['total_loss_db']:.2f} dB")

    if v_death >= 0:
        print(f"  SIGNAL DEATH at row {v_death}"
              f" ({v_death * PE_PITCH:.0f} μm into array)")
        print(f"  Signal survives {v_death}/{N_ROWS} rows"
              f" ({100*v_death/N_ROWS:.1f}%)")
    else:
        print(f"  Signal survives all {N_ROWS} rows (no death point)")

    key_rows = [0, 26, 53, 80, 121, 162, 202, 242]
    print(f"\n  Power at key positions:")
    print(f"  {'Row':>5} | {'Power (dBm)':>12} | {'Margin (dB)':>12} | {'Status':>8}")
    print(f"  {'-'*50}")
    for row_idx in key_rows:
        if row_idx < len(v_analysis['power_map']):
            e = v_analysis['power_map'][row_idx]
            status = "OK" if e['above_threshold'] else "DEAD"
            print(f"  {row_idx:>5} | {e['power_dbm']:>12.2f} | {e['margin_db']:>12.2f} | {status:>8}")

    results['v_unamplified'] = v_analysis

    # --- Weight path ---
    print(f"\n[W] WEIGHT PATH (bus to PE rows)")
    print("-" * 50)

    w_analysis = analyze_weight_path(N_ROWS)

    # Weight paths are equalized, so all rows see the same total loss
    worst_weight = min(w_analysis['power_map'], key=lambda x: x['power_dbm'])
    best_weight = max(w_analysis['power_map'], key=lambda x: x['power_dbm'])

    print(f"  Weight input power: {w_analysis['weight_input_power_dbm']:.2f} dBm")
    print(f"  Bus propagation loss: {w_analysis['bus_loss_db']:.2f} dB")
    print(f"  Best row power: {best_weight['power_dbm']:.2f} dBm (row {best_weight['row']})")
    print(f"  Worst row power: {worst_weight['power_dbm']:.2f} dBm (row {worst_weight['row']})")
    print(f"  All paths equalized to: {worst_weight['total_path_um']:.0f} μm")

    results['w_analysis'] = w_analysis

    # =========================================================================
    # PHASE 2: EDWA AMPLIFIER DESIGN
    # =========================================================================

    print("\n" + "=" * 70)
    print("  PHASE 2: EDWA AMPLIFIER PLACEMENT")
    print("=" * 70)

    print(f"\n  EDWA parameters:")
    print(f"    Gain per stage:     {EDWA_GAIN_DB} dB")
    print(f"    Stage length:       {EDWA_LENGTH_UM} μm")
    print(f"    Noise figure:       {EDWA_NOISE_FIGURE_DB} dB")
    print(f"    Pump power/stage:   {EDWA_PUMP_POWER_MW} mW @ {EDWA_PUMP_WAVELENGTH_NM} nm")
    print(f"    Material:           Er/Yb co-doped LiNbO3 (native)")

    # --- Horizontal amplification ---
    print(f"\n[H-AMP] Horizontal path amplifier placement")
    print("-" * 50)

    h_amp = design_amplifier_placement(h_analysis, path_type="horizontal")

    print(f"  Amplifiers needed: {h_amp['n_amplifiers']}")
    if h_amp['n_amplifiers'] > 0:
        print(f"  Average spacing: every {h_amp['avg_spacing_pes']:.0f} PEs"
              f" ({h_amp['avg_spacing_um']:.0f} μm)")
        print(f"  Total pump power: {h_amp['total_pump_power_mw']:.0f} mW")
        print(f"  Final amplified power: {h_amp['final_power_dbm']:.2f} dBm")
        print(f"  All above threshold: {'YES' if h_amp['all_above_threshold'] else 'NO'}")

        print(f"\n  Amplifier positions (per row — {N_ROWS} rows total):")
        for amp in h_amp['amp_positions']:
            print(f"    Stage {amp['stage_number']}: after column {amp['position']}"
                  f" | {amp['power_before_dbm']:.1f} → {amp['power_after_dbm']:.1f} dBm")

    results['h_amplified'] = h_amp

    # --- Vertical amplification ---
    print(f"\n[V-AMP] Vertical path amplifier placement")
    print("-" * 50)

    v_amp = design_amplifier_placement(v_analysis, path_type="vertical")

    print(f"  Amplifiers needed: {v_amp['n_amplifiers']}")
    if v_amp['n_amplifiers'] > 0:
        print(f"  Average spacing: every {v_amp['avg_spacing_pes']:.0f} PEs"
              f" ({v_amp['avg_spacing_um']:.0f} μm)")
        print(f"  Total pump power: {v_amp['total_pump_power_mw']:.0f} mW")
        print(f"  Final amplified power: {v_amp['final_power_dbm']:.2f} dBm")
        print(f"  All above threshold: {'YES' if v_amp['all_above_threshold'] else 'NO'}")

        print(f"\n  Amplifier positions (per column — {N_COLS} columns total):")
        for amp in v_amp['amp_positions']:
            print(f"    Stage {amp['stage_number']}: after row {amp['position']}"
                  f" | {amp['power_before_dbm']:.1f} → {amp['power_after_dbm']:.1f} dBm")

    results['v_amplified'] = v_amp

    # =========================================================================
    # PHASE 3: AMPLIFIED CHIP VALIDATION
    # =========================================================================

    print("\n" + "=" * 70)
    print("  PHASE 3: AMPLIFIED CHIP VALIDATION")
    print("=" * 70)

    # Total amplifiers on chip
    h_amps_total = h_amp['n_amplifiers'] * N_ROWS  # One set per row
    v_amps_total = v_amp['n_amplifiers'] * N_COLS   # One set per column
    total_amps = h_amps_total + v_amps_total
    total_pump_mw = total_amps * EDWA_PUMP_POWER_MW
    total_pump_w = total_pump_mw / 1000

    # EDWA area overhead
    edwa_area_per_stage = EDWA_LENGTH_UM * 5  # ~500 × 5 μm per stage
    total_edwa_area = total_amps * edwa_area_per_stage
    chip_area = CHIP_WIDTH * CHIP_HEIGHT
    edwa_area_percent = (total_edwa_area / chip_area) * 100

    print(f"\n  Amplifier count:")
    print(f"    Horizontal: {h_amp['n_amplifiers']} per row × {N_ROWS} rows = {h_amps_total}")
    print(f"    Vertical:   {v_amp['n_amplifiers']} per col × {N_COLS} cols = {v_amps_total}")
    print(f"    TOTAL:      {total_amps} EDWA stages on chip")

    print(f"\n  Pump power budget:")
    print(f"    Per stage:  {EDWA_PUMP_POWER_MW} mW")
    print(f"    Total:      {total_pump_mw:.0f} mW = {total_pump_w:.2f} W")

    print(f"\n  Area overhead:")
    print(f"    Per EDWA:   {edwa_area_per_stage:.0f} μm²")
    print(f"    Total EDWA: {total_edwa_area/1e6:.2f} mm²")
    print(f"    Chip area:  {chip_area/1e6:.2f} mm²")
    print(f"    Overhead:   {edwa_area_percent:.1f}%")

    # Signal quality (SNR degradation from cascaded EDWAs)
    max_h_stages = h_amp['n_amplifiers']
    max_v_stages = v_amp['n_amplifiers']
    max_total_stages = max_h_stages + max_v_stages

    # Cascaded noise figure: NF_total ≈ NF_1 + (NF_2-1)/G_1 + ...
    # For identical stages: NF_total ≈ NF_1 (dominates when gain >> noise)
    # Simple approximation: total noise ~ N_stages × NF per stage (in linear)
    total_noise_degradation_db = 10 * np.log10(max_total_stages) + EDWA_NOISE_FIGURE_DB

    print(f"\n  Signal quality:")
    print(f"    Max cascaded stages (worst path): {max_total_stages}")
    print(f"    Noise figure per stage: {EDWA_NOISE_FIGURE_DB} dB")
    print(f"    Total noise degradation: ~{total_noise_degradation_db:.1f} dB")

    # Final power check
    h_final_ok = h_amp['all_above_threshold']
    v_final_ok = v_amp['all_above_threshold']

    # Check amplified vertical path including decoder
    v_final_at_detector = v_amp['final_power_dbm'] - v_analysis['output_chain_loss_db']
    v_detector_ok = v_final_at_detector > DETECTOR_SENSITIVITY_DBM

    print(f"\n  Final power levels (amplified):")
    print(f"    Horizontal (at last PE):  {h_amp['final_power_dbm']:.2f} dBm"
          f"  {'OK' if h_final_ok else 'FAIL'}")
    print(f"    Vertical (before decoder): {v_amp['final_power_dbm']:.2f} dBm"
          f"  {'OK' if v_final_ok else 'FAIL'}")
    print(f"    Vertical (at detector):    {v_final_at_detector:.2f} dBm"
          f"  {'OK' if v_detector_ok else 'FAIL'}")

    results['total_amps'] = total_amps
    results['total_pump_w'] = total_pump_w
    results['edwa_area_percent'] = edwa_area_percent
    results['h_final_ok'] = h_final_ok
    results['v_final_ok'] = v_final_ok
    results['v_detector_ok'] = v_detector_ok

    # =========================================================================
    # PATH-LENGTH EQUALIZATION
    # =========================================================================

    print(f"\n  Path-length equalization:")
    max_weight_path = (N_ROWS - 1) * PE_PITCH
    print(f"    Max weight path (equalized): {max_weight_path:.0f} μm")
    print(f"    Equalization time: {max_weight_path / V_GROUP_UM_PS:.2f} ps")
    print(f"    As % of clock period: "
          f"{(max_weight_path / V_GROUP_UM_PS) / (1e6/CLOCK_FREQ_MHZ) * 100:.2f}%")

    # Activation paths (all identical = inherently matched)
    print(f"    Activation path spread: 0.000 ps (inherently matched)")

    # =========================================================================
    # PERFORMANCE
    # =========================================================================

    total_pes = N_ROWS * N_COLS
    throughput_tflops = total_pes * CLOCK_FREQ_MHZ / 1e6

    print(f"\n  Performance:")
    print(f"    Total PEs: {total_pes:,}")
    print(f"    Clock: {CLOCK_FREQ_MHZ} MHz")
    print(f"    Throughput: {throughput_tflops:.2f} TFLOPS")
    print(f"    vs NVIDIA H100: {throughput_tflops/2000:.1f}x")

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print("\n" + "=" * 70)
    print("  VALIDATION SUMMARY — 243×243 MONOLITHIC CHIP")
    print("=" * 70)

    checks = [
        ("Horizontal signal (amplified)", h_final_ok),
        ("Vertical signal (amplified)", v_final_ok),
        ("Vertical at detector (amplified + decoder)", v_detector_ok),
        ("EDWA stages within limit (<" + str(MAX_EDWA_STAGES) + ")",
         max_total_stages <= MAX_EDWA_STAGES),
        ("Pump power reasonable (<10W)", total_pump_w < 10.0),
        ("Area overhead acceptable (<20%)", edwa_area_percent < 20.0),
    ]

    all_pass = True
    for name, passed in checks:
        symbol = "[+]" if passed else "[X]"
        status = "PASS" if passed else "FAIL"
        print(f"  {symbol} {name}: {status}")
        if not passed:
            all_pass = False

    results['all_pass'] = all_pass

    print()
    if all_pass:
        print("  >>> ALL CHECKS PASSED — 243×243 with EDWA amplification validated <<<")
    else:
        print("  >>> SOME CHECKS FAILED — Review amplifier design <<<")
    print("=" * 70)

    return results


# =============================================================================
# Report Generation
# =============================================================================

def generate_report(results: dict):
    """Generate markdown validation report."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    report_path = os.path.join(base_dir, 'docs', 'MONOLITHIC_243x243_VALIDATION.md')

    h_unamp = results['h_unamplified']
    v_unamp = results['v_unamplified']
    h_amp = results['h_amplified']
    v_amp = results['v_amplified']

    with open(report_path, 'w') as f:
        f.write("# Monolithic 243x243 N-Radix Chip — Validation Report\n\n")
        f.write(f"**Date:** 2026-02-08\n")
        f.write(f"**Topology:** Split-edge (IOC left, array center, IOC right)\n")
        f.write(f"**Material:** X-cut LiNbO3 (TFLN)\n")
        f.write(f"**Array:** 243x243 = 59,049 PEs\n")
        f.write(f"**Amplification:** EDWA (Er/Yb co-doped LiNbO3)\n\n")

        f.write("## Chip Dimensions\n\n")
        f.write(f"- Width: {CHIP_WIDTH:.0f} um ({CHIP_WIDTH/1e4:.2f} cm)\n")
        f.write(f"- Height: {CHIP_HEIGHT:.0f} um ({CHIP_HEIGHT/1e4:.2f} cm)\n")
        f.write(f"- Array area: {ARRAY_WIDTH:.0f} x {ARRAY_HEIGHT:.0f} um "
                f"({ARRAY_WIDTH/1e4:.2f} x {ARRAY_HEIGHT/1e4:.2f} cm)\n\n")

        f.write("## Phase 1: Unamplified Loss Profile\n\n")
        f.write("### Horizontal Path (activation)\n\n")
        f.write(f"- Entry power: {h_unamp['power_at_entry_dbm']:.2f} dBm\n")
        f.write(f"- Exit power: {h_unamp['final_power_dbm']:.2f} dBm\n")
        f.write(f"- Total loss: {h_unamp['total_loss_db']:.2f} dB\n")
        h_death = find_signal_death_point(h_unamp['power_map'])
        if h_death >= 0:
            f.write(f"- **Signal dies at column {h_death}** "
                    f"({100*h_death/N_COLS:.1f}% of array)\n\n")
        else:
            f.write(f"- Signal survives all columns\n\n")

        f.write("### Vertical Path (partial sums)\n\n")
        f.write(f"- SFG output power: {v_unamp['sfg_output_power_dbm']:.2f} dBm\n")
        f.write(f"- Power at detector: {v_unamp['final_power_at_detector_dbm']:.2f} dBm\n")
        f.write(f"- Total loss: {v_unamp['total_loss_db']:.2f} dB\n")
        v_death = find_signal_death_point(v_unamp['power_map'])
        if v_death >= 0:
            f.write(f"- **Signal dies at row {v_death}** "
                    f"({100*v_death/N_ROWS:.1f}% of array)\n\n")
        else:
            f.write(f"- Signal survives all rows\n\n")

        f.write("## Phase 2: EDWA Amplifier Design\n\n")
        f.write(f"| Parameter | Value |\n")
        f.write(f"|-----------|-------|\n")
        f.write(f"| Gain per stage | {EDWA_GAIN_DB} dB |\n")
        f.write(f"| Stage length | {EDWA_LENGTH_UM} um |\n")
        f.write(f"| Noise figure | {EDWA_NOISE_FIGURE_DB} dB |\n")
        f.write(f"| Pump wavelength | {EDWA_PUMP_WAVELENGTH_NM} nm |\n")
        f.write(f"| Pump power/stage | {EDWA_PUMP_POWER_MW} mW |\n\n")

        f.write("### Horizontal Amplifiers\n\n")
        f.write(f"- Stages per row: {h_amp['n_amplifiers']}\n")
        f.write(f"- Spacing: ~{h_amp['avg_spacing_pes']:.0f} PEs "
                f"({h_amp['avg_spacing_um']:.0f} um)\n")
        f.write(f"- Total horizontal amps: {h_amp['n_amplifiers'] * N_ROWS}\n\n")

        if h_amp['amp_positions']:
            f.write("| Stage | After Column | Power Before | Power After |\n")
            f.write("|-------|-------------|-------------|------------|\n")
            for amp in h_amp['amp_positions']:
                f.write(f"| {amp['stage_number']} | {amp['position']} "
                        f"| {amp['power_before_dbm']:.1f} dBm "
                        f"| {amp['power_after_dbm']:.1f} dBm |\n")
            f.write("\n")

        f.write("### Vertical Amplifiers\n\n")
        f.write(f"- Stages per column: {v_amp['n_amplifiers']}\n")
        f.write(f"- Spacing: ~{v_amp['avg_spacing_pes']:.0f} PEs "
                f"({v_amp['avg_spacing_um']:.0f} um)\n")
        f.write(f"- Total vertical amps: {v_amp['n_amplifiers'] * N_COLS}\n\n")

        if v_amp['amp_positions']:
            f.write("| Stage | After Row | Power Before | Power After |\n")
            f.write("|-------|----------|-------------|------------|\n")
            for amp in v_amp['amp_positions']:
                f.write(f"| {amp['stage_number']} | {amp['position']} "
                        f"| {amp['power_before_dbm']:.1f} dBm "
                        f"| {amp['power_after_dbm']:.1f} dBm |\n")
            f.write("\n")

        f.write("## Phase 3: Amplified Chip Summary\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| Total EDWA stages | {results['total_amps']} |\n")
        f.write(f"| Total pump power | {results['total_pump_w']:.2f} W |\n")
        f.write(f"| Area overhead | {results['edwa_area_percent']:.1f}% |\n")
        f.write(f"| Throughput | {N_ROWS*N_COLS*CLOCK_FREQ_MHZ/1e6:.2f} TFLOPS |\n\n")

        f.write("## Validation Results\n\n")
        status = "ALL PASSED" if results['all_pass'] else "SOME FAILED"
        f.write(f"**Overall: {status}**\n\n")
        f.write(f"| Check | Result |\n")
        f.write(f"|-------|--------|\n")
        f.write(f"| Horizontal signal (amplified) | {'PASS' if results['h_final_ok'] else 'FAIL'} |\n")
        f.write(f"| Vertical signal (amplified) | {'PASS' if results['v_final_ok'] else 'FAIL'} |\n")
        f.write(f"| Vertical at detector | {'PASS' if results['v_detector_ok'] else 'FAIL'} |\n")
        f.write(f"| Pump power < 10W | {'PASS' if results['total_pump_w'] < 10 else 'FAIL'} |\n")
        f.write(f"| Area overhead < 20% | {'PASS' if results['edwa_area_percent'] < 20 else 'FAIL'} |\n")

    print(f"\n  Report saved to: {report_path}")
    return report_path


# =============================================================================
# Main
# =============================================================================

def main():
    results = run_243x243_analysis()
    report_path = generate_report(results)
    return results


if __name__ == "__main__":
    main()
