#!/usr/bin/env python3
"""
Power Budget Analysis for 81-Trit Optical Carry Processor

Calculates optical loss through the signal and carry paths to determine
where optical amplifiers (SOAs, EDWAs) are needed.

Reference values from literature:
- LiNbO3 waveguide loss: 0.1-0.5 dB/cm
- Silicon waveguide loss: 1-3 dB/cm
- Ring resonator drop port: 1-3 dB
- MMI splitter: 0.3-0.5 dB excess loss
- Y-junction: 0.2-0.5 dB
- OPA conversion efficiency: -3 to -6 dB (50-25%)
- Waveguide bend (5μm radius): 0.1-0.3 dB per 90°
- Detector sensitivity: -30 to -40 dBm typical
"""

from dataclasses import dataclass
from typing import List, Tuple
import math


@dataclass
class ComponentLoss:
    """Loss characteristics of an optical component."""
    name: str
    loss_db: float  # Insertion loss in dB
    notes: str = ""


# Component loss values (conservative estimates for LiNbO3)
COMPONENT_LOSSES = {
    # Waveguides
    "waveguide_per_mm": ComponentLoss("Waveguide (per mm)", 0.05, "LiNbO3, 0.5 dB/cm"),

    # Splitters/Combiners
    "y_junction": ComponentLoss("Y-Junction", 3.3, "3dB split + 0.3dB excess"),
    "mmi_1x2": ComponentLoss("MMI 1x2", 3.5, "3dB split + 0.5dB excess"),
    "mmi_2x2": ComponentLoss("MMI 2x2 (one output)", 3.5, "3dB + 0.5dB excess"),
    "mmi_2x2_combiner": ComponentLoss("MMI 2x2 Combiner", 0.5, "Combining mode, excess loss only"),

    # Ring resonators
    "ring_thru": ComponentLoss("Ring Resonator (thru)", 0.5, "Off-resonance"),
    "ring_drop": ComponentLoss("Ring Resonator (drop)", 2.0, "On-resonance extraction"),
    "ring_add_drop": ComponentLoss("Add-Drop Ring (drop)", 2.5, "Extraction with coupling loss"),

    # Frequency conversion
    "sfg_mixer": ComponentLoss("SFG Mixer", 4.0, "~40% conversion efficiency"),
    "dfg_mixer": ComponentLoss("DFG Mixer", 5.0, "~30% conversion efficiency"),
    "opa_converter": ComponentLoss("OPA Wavelength Converter", 4.0, "~40% conversion efficiency"),

    # Delay lines
    "delay_5ps": ComponentLoss("Delay Line (5ps)", 0.35, "~0.7mm length"),
    "delay_10ps": ComponentLoss("Delay Line (10ps)", 0.7, "~1.4mm length"),
    "delay_15ps": ComponentLoss("Delay Line (15ps)", 1.0, "~2.0mm length"),
    "delay_20ps": ComponentLoss("Delay Line (20ps)", 1.4, "~2.7mm length, default"),

    # Bends
    "bend_180": ComponentLoss("180° Euler Bend", 0.3, "5μm radius"),
    "bend_90": ComponentLoss("90° Bend", 0.15, "5μm radius"),

    # Detectors
    "detector_coupling": ComponentLoss("Detector Coupling", 1.0, "Grating/edge coupler"),

    # AWG
    "awg_demux": ComponentLoss("AWG Demux (per channel)", 3.0, "5-channel"),
}


def calculate_main_signal_path_loss() -> Tuple[float, List[str]]:
    """
    Calculate loss through the main signal path for ONE trit.

    Path: Input → AWG demux → Selector → Combiner → Mixer → AWG demux → Detector
    """
    losses = []

    # Approximate component sequence for main signal
    path = [
        ("AWG input demux", 3.0),
        ("Wavelength selector (ring)", 2.5),
        ("Combiner (A+B)", 0.5),
        ("Carry injector combiner", 0.5),
        ("Routing waveguide (~2mm)", 1.0),
        ("SFG Mixer", 4.0),
        ("Carry tap (thru)", 0.5),
        ("AWG output demux", 3.0),
        ("Detector coupling", 1.0),
    ]

    total = 0
    breakdown = []
    for name, loss in path:
        total += loss
        breakdown.append(f"  {name}: {loss:.1f} dB (cumulative: {total:.1f} dB)")

    return total, breakdown


def calculate_carry_path_loss() -> Tuple[float, List[str]]:
    """
    Calculate loss through the carry path from one trit to the next.

    Path: Mixer output → Carry tap → OPA → Delay → Next trit inject
    """
    path = [
        ("Carry tap (drop port)", 2.5),
        ("Routing to OPA (~0.5mm)", 0.25),
        ("OPA wavelength converter", 4.0),
        ("Routing to delay (~0.5mm)", 0.25),
        ("Delay line (5ps)", 0.35),
        ("Routing to next trit (~1mm)", 0.5),
        ("Carry combiner", 0.5),
        ("Carry injector", 0.5),
    ]

    total = 0
    breakdown = []
    for name, loss in path:
        total += loss
        breakdown.append(f"  {name}: {loss:.1f} dB (cumulative: {total:.1f} dB)")

    return total, breakdown


def calculate_cumulative_carry_loss(num_trits: int = 81) -> List[Tuple[int, float]]:
    """
    Calculate cumulative carry signal loss across the carry chain.

    The carry signal generated at Trit 0 must propagate through
    potentially all 80 subsequent trits (worst case: 0 + 0 = 0, carry 1
    ripples all the way through if all trits are at threshold).

    Returns list of (trit_number, cumulative_loss_db).
    """
    carry_loss_per_trit, _ = calculate_carry_path_loss()

    # Additional: each trit also regenerates carry via OPA (parametric gain)
    # But for worst case, assume no gain

    cumulative = []
    for trit in range(num_trits):
        # Loss accumulates as carry ripples through
        loss = trit * carry_loss_per_trit
        cumulative.append((trit, loss))

    return cumulative


def find_amplifier_positions(
    cumulative_losses: List[Tuple[int, float]],
    max_loss_db: float = 20.0,
    detector_sensitivity_dbm: float = -35.0,
    input_power_dbm: float = 0.0
) -> List[int]:
    """
    Determine where amplifiers should be placed.

    Args:
        cumulative_losses: List of (trit, loss_db) tuples
        max_loss_db: Maximum allowed loss before amplification
        detector_sensitivity_dbm: Minimum detectable power
        input_power_dbm: Input signal power

    Returns:
        List of trit positions where amplifiers are needed.
    """
    amplifier_positions = []
    last_amp_loss = 0

    for trit, total_loss in cumulative_losses:
        loss_since_last_amp = total_loss - last_amp_loss

        if loss_since_last_amp >= max_loss_db:
            amplifier_positions.append(trit)
            last_amp_loss = total_loss

    return amplifier_positions


def calculate_amplified_carry_loss(
    num_trits: int = 81,
    amp_interval: int = 3,
    amp_gain_db: float = 30.0,
    saturation_dbm: float = 10.0,
    input_power_dbm: float = 10.0
) -> List[Tuple[int, float]]:
    """
    Calculate carry signal level with amplifiers every N trits.

    Models realistic SOA behavior with saturation limiting.
    SOAs restore signal to saturation level regardless of input
    (as long as input is above noise floor).

    Returns list of (trit_number, signal_level_dbm).
    """
    carry_loss_per_trit, _ = calculate_carry_path_loss()

    levels = []
    current_level = input_power_dbm  # Absolute power in dBm

    for trit in range(num_trits):
        if trit > 0:
            # Apply loss from previous trit
            current_level -= carry_loss_per_trit

            # Check if amplifier is present (after every amp_interval trits)
            if trit % amp_interval == 0:
                # SOA saturates at output power - this is the key behavior
                # Signal is restored to saturation level (minus small margin)
                current_level = saturation_dbm

        levels.append((trit, current_level))

    return levels


def main():
    print("=" * 70)
    print("POWER BUDGET ANALYSIS: 81-Trit Optical Carry Processor")
    print("=" * 70)
    print()

    # System parameters
    INPUT_POWER_DBM = 10.0  # 10 mW laser input
    DETECTOR_SENSITIVITY_DBM = -30.0  # Typical APD
    MAX_LOSS_BEFORE_AMP = 20.0  # Conservative margin

    print(f"Input power: {INPUT_POWER_DBM} dBm ({10**(INPUT_POWER_DBM/10):.1f} mW)")
    print(f"Detector sensitivity: {DETECTOR_SENSITIVITY_DBM} dBm")
    print(f"Available link budget: {INPUT_POWER_DBM - DETECTOR_SENSITIVITY_DBM} dB")
    print()

    # Main signal path analysis
    print("-" * 70)
    print("MAIN SIGNAL PATH (per trit)")
    print("-" * 70)
    main_loss, main_breakdown = calculate_main_signal_path_loss()
    for line in main_breakdown:
        print(line)
    print(f"\n  TOTAL MAIN PATH LOSS: {main_loss:.1f} dB")
    print(f"  Signal at detector: {INPUT_POWER_DBM - main_loss:.1f} dBm")

    if INPUT_POWER_DBM - main_loss < DETECTOR_SENSITIVITY_DBM:
        print("  ⚠️  WARNING: Signal below detector sensitivity!")
    else:
        margin = (INPUT_POWER_DBM - main_loss) - DETECTOR_SENSITIVITY_DBM
        print(f"  ✓ Margin above sensitivity: {margin:.1f} dB")
    print()

    # Carry path analysis
    print("-" * 70)
    print("CARRY PATH (per trit-to-trit hop)")
    print("-" * 70)
    carry_loss, carry_breakdown = calculate_carry_path_loss()
    for line in carry_breakdown:
        print(line)
    print(f"\n  TOTAL CARRY PATH LOSS: {carry_loss:.1f} dB per hop")
    print()

    # Cumulative carry chain analysis
    print("-" * 70)
    print("CUMULATIVE CARRY CHAIN LOSS")
    print("-" * 70)
    cumulative = calculate_cumulative_carry_loss(81)

    # Show key points
    key_trits = [0, 1, 2, 5, 10, 20, 40, 60, 80]
    print("\n  Trit  | Cumulative Loss | Signal Level | Status")
    print("  ------|-----------------|--------------|--------")

    for trit, loss in cumulative:
        if trit in key_trits:
            signal = INPUT_POWER_DBM - loss
            if signal >= DETECTOR_SENSITIVITY_DBM:
                status = "✓ OK"
            elif signal >= DETECTOR_SENSITIVITY_DBM - 10:
                status = "⚠ LOW"
            else:
                status = "✗ FAIL"
            print(f"  T{trit:3d}  |     {loss:6.1f} dB   |   {signal:6.1f} dBm | {status}")

    print()

    # Determine amplifier positions
    print("-" * 70)
    print("RECOMMENDED AMPLIFIER POSITIONS")
    print("-" * 70)

    amp_positions = find_amplifier_positions(
        cumulative,
        max_loss_db=MAX_LOSS_BEFORE_AMP,
        detector_sensitivity_dbm=DETECTOR_SENSITIVITY_DBM,
        input_power_dbm=INPUT_POWER_DBM
    )

    print(f"\n  Maximum loss between amplifiers: {MAX_LOSS_BEFORE_AMP} dB")
    print(f"  Loss per carry hop: {carry_loss:.1f} dB")
    print(f"  Trits between amplifiers: ~{int(MAX_LOSS_BEFORE_AMP / carry_loss)}")
    print()
    print(f"  Amplifiers needed: {len(amp_positions)}")
    print(f"  Positions (after trit): {amp_positions}")
    print()

    # Amplified carry chain analysis
    print("-" * 70)
    print("AMPLIFIED CARRY CHAIN (with SOAs every 3 trits)")
    print("-" * 70)

    AMP_INTERVAL = 3
    AMP_GAIN = 30.0  # Higher gain SOAs for margin

    SOA_SATURATION = 10.0  # dBm output saturation power
    amplified = calculate_amplified_carry_loss(
        81, AMP_INTERVAL, AMP_GAIN,
        saturation_dbm=SOA_SATURATION,
        input_power_dbm=INPUT_POWER_DBM
    )

    print(f"\n  Amplifier interval: every {AMP_INTERVAL} trits")
    print(f"  SOA gain: +{AMP_GAIN:.0f} dB")
    print(f"  Loss per 3 trits: {carry_loss * 3:.1f} dB")
    print(f"  Net per cycle: {AMP_GAIN - carry_loss * 3:.1f} dB")
    print()

    print(f"  SOA output saturation: {SOA_SATURATION} dBm")
    print()
    print("  Trit  | Signal Level | Status")
    print("  ------|--------------|--------")

    key_trits = [0, 1, 2, 3, 5, 6, 9, 10, 20, 40, 60, 78, 79, 80]
    for trit, signal in amplified:
        if trit in key_trits:
            if signal >= DETECTOR_SENSITIVITY_DBM:
                status = "✓ OK"
            elif signal >= DETECTOR_SENSITIVITY_DBM - 10:
                status = "⚠ LOW"
            else:
                status = "✗ FAIL"

            amp_marker = " [AMP]" if trit > 0 and trit % AMP_INTERVAL == 0 else ""
            print(f"  T{trit:3d}  |   {signal:6.1f} dBm | {status}{amp_marker}")

    # Final signal level
    final_signal = amplified[-1][1]
    print(f"\n  Final signal at T80: {final_signal:.1f} dBm")
    print(f"  Margin above sensitivity: {final_signal - DETECTOR_SENSITIVITY_DBM:.1f} dB")

    if final_signal >= DETECTOR_SENSITIVITY_DBM:
        print("  ✓ CARRY CHAIN VIABLE WITH AMPLIFICATION")
    else:
        print("  ✗ Need more gain or closer amplifier spacing")

    print()

    # Summary recommendations
    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print("""
  1. CARRY CHAIN AMPLIFICATION
     - Place SOA or EDWA after every ~2-3 trits in the carry chain
     - Recommended positions: after trits {amp_pos}
     - Total amplifiers needed: {num_amps} (for carry chain alone)

  2. AMPLIFIER TYPE RECOMMENDATIONS
     - Semiconductor Optical Amplifier (SOA): Fast, compact, broadband
       * Gain: 15-25 dB
       * Bandwidth: >40 nm
       * Good for: all wavelengths

     - Erbium-Doped Waveguide Amplifier (EDWA): Low noise, high gain
       * Gain: 20-30 dB
       * Bandwidth: C-band (1530-1565 nm)
       * Good for: 1.55 μm (Red = -1)

     - Optical Parametric Amplifier (OPA): Already in design!
       * Consider increasing OPA pump power for net gain
       * Could provide amplification AND wavelength conversion

  3. CRITICAL PATHS TO MONITOR
     - Carry chain (longest path): T0 → T80 = {total_carry_loss:.0f} dB potential
     - Corner ALUs (longest routing): ~5 dB extra waveguide loss
     - MSB detector: receives weakest carry signal

  4. ALTERNATIVE: OPTICAL REGENERATORS
     - Instead of linear amplifiers, use 3R regeneration
     - Re-amplify, Re-shape, Re-time at each amplifier position
     - Prevents noise accumulation

  5. LAYOUT OPTIMIZATION
     - Group amplifiers at regular intervals (every 3 trits)
     - Share pump lasers between nearby OPAs
     - Consider folded layout to minimize carry path length
""".format(
        amp_pos=amp_positions[:10],  # Show first 10
        num_amps=len(amp_positions),
        total_carry_loss=cumulative[-1][1]
    ))

    # Generate data for visualization
    print("-" * 70)
    print("DATA FOR VISUALIZATION")
    print("-" * 70)
    print("\n# Trit number vs cumulative loss (for plotting)")
    print("trit_num = [", end="")
    print(", ".join(str(t) for t, _ in cumulative), end="")
    print("]")
    print("loss_db = [", end="")
    print(", ".join(f"{l:.1f}" for _, l in cumulative), end="")
    print("]")
    print()


if __name__ == "__main__":
    main()
