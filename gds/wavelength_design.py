"""
Wavelength Selection & Poling Period Calculator
================================================
Selects input (RGB) and weight (+1/-1) wavelengths, computes all 6 SFG
output wavelengths, verifies spectral separation, and calculates PPLN
poling periods for quasi-phase-matched SFG in lithium niobate.

Physics:
  SFG: ω₃ = ω₁ + ω₂  →  1/λ₃ = 1/λ₁ + 1/λ₂
  QPM: Λ = 1/(n₃/λ₃ - n₁/λ₁ - n₂/λ₂)

Platform: Thin-film lithium niobate on insulator (LNOI)
"""

import math


# =====================================================================
# Sellmeier equation for lithium niobate (extraordinary polarization)
# 5% MgO-doped congruent LiNbO3 at 25°C
# Ref: Gayer et al., Appl. Phys. B 91, 2008
# =====================================================================
def n_LN(wavelength_um):
    """Refractive index of MgO:LN (extraordinary) at given wavelength in microns."""
    lam2 = wavelength_um ** 2
    # Sellmeier coefficients (extraordinary, 5% MgO:CLN, 25°C)
    A = 5.756
    B = 0.0983
    C = 0.2020 ** 2  # 0.040804
    D = -0.0202
    n2 = A + B / (lam2 - C) + D * lam2
    return math.sqrt(n2)


# =====================================================================
# Wavelength selection
# =====================================================================
# Input channels (C-band telecom, 20 nm spacing for clear separation)
LAMBDA_R = 1.560  # um (1560 nm)
LAMBDA_G = 1.540  # um (1540 nm)
LAMBDA_B = 1.520  # um (1520 nm)

# Weight channels (1 um band, 30 nm spacing)
LAMBDA_PLUS  = 1.070  # um (1070 nm) → represents +1
LAMBDA_MINUS = 1.040  # um (1040 nm) → represents -1

inputs = {"R": LAMBDA_R, "G": LAMBDA_G, "B": LAMBDA_B}
weights = {"+1": LAMBDA_PLUS, "-1": LAMBDA_MINUS}


def sfg_wavelength(lam1, lam2):
    """SFG output wavelength: 1/λ₃ = 1/λ₁ + 1/λ₂"""
    return (lam1 * lam2) / (lam1 + lam2)


def poling_period(lam_input, lam_weight, lam_sfg):
    """
    Quasi-phase-matching poling period for PPLN.
    Λ = 1 / (n₃/λ₃ - n₁/λ₁ - n₂/λ₂)
    All wavelengths in microns, returns period in microns.
    """
    n1 = n_LN(lam_input)
    n2 = n_LN(lam_weight)
    n3 = n_LN(lam_sfg)
    delta_k_over_2pi = n3 / lam_sfg - n1 / lam_input - n2 / lam_weight
    if delta_k_over_2pi == 0:
        return float('inf')
    return 1.0 / delta_k_over_2pi


def main():
    print("=" * 70)
    print("WAVELENGTH-TERNARY HYBRID SFG CHIP — WAVELENGTH DESIGN")
    print("=" * 70)

    # --- Input wavelengths ---
    print("\n--- INPUT WAVELENGTHS (data channels) ---")
    for name, lam in inputs.items():
        n = n_LN(lam)
        print(f"  {name}: {lam*1000:.0f} nm  (n = {n:.4f})")

    # --- Weight wavelengths ---
    print("\n--- WEIGHT WAVELENGTHS (always on) ---")
    for name, lam in weights.items():
        n = n_LN(lam)
        print(f"  {name}: {lam*1000:.0f} nm  (n = {n:.4f})")

    # --- SFG outputs ---
    print("\n--- SFG OUTPUT WAVELENGTHS ---")
    print(f"  {'Pair':<8} {'λ_in (nm)':<12} {'λ_wt (nm)':<12} {'λ_SFG (nm)':<12} {'n_SFG':<8}")
    print(f"  {'-'*52}")

    sfg_results = []
    for iname, lam_in in inputs.items():
        for wname, lam_wt in weights.items():
            lam_sfg = sfg_wavelength(lam_in, lam_wt)
            n_sfg = n_LN(lam_sfg)
            label = f"{iname}{wname}"
            sfg_results.append((label, lam_in, lam_wt, lam_sfg, n_sfg))
            print(f"  {label:<8} {lam_in*1000:<12.0f} {lam_wt*1000:<12.0f} {lam_sfg*1000:<12.2f} {n_sfg:<8.4f}")

    # --- Spectral separation check ---
    print("\n--- SPECTRAL SEPARATION CHECK ---")
    sorted_sfg = sorted(sfg_results, key=lambda x: x[3])
    min_sep = float('inf')
    min_pair = ""
    for i in range(len(sorted_sfg) - 1):
        sep = (sorted_sfg[i+1][3] - sorted_sfg[i][3]) * 1000  # nm
        pair_str = f"{sorted_sfg[i][0]} → {sorted_sfg[i+1][0]}"
        print(f"  {pair_str:<16} Δλ = {sep:.2f} nm")
        if sep < min_sep:
            min_sep = sep
            min_pair = pair_str

    print(f"\n  Minimum separation: {min_sep:.2f} nm ({min_pair})")
    if min_sep >= 2.0:
        print(f"  ✓ All outputs separated by ≥2 nm — standard bandpass filters work")
    elif min_sep >= 0.5:
        print(f"  △ Tight separation — need narrow bandpass or WDM demux")
    else:
        print(f"  ✗ Outputs too close — choose different wavelengths!")

    # --- Poling periods ---
    print("\n--- PPLN POLING PERIODS (quasi-phase-matching) ---")
    print(f"  {'Pair':<8} {'λ_SFG (nm)':<12} {'Λ (μm)':<12} {'Λ (nm)':<12}")
    print(f"  {'-'*44}")
    for label, lam_in, lam_wt, lam_sfg, _ in sfg_results:
        period = poling_period(lam_in, lam_wt, lam_sfg)
        print(f"  {label:<8} {lam_sfg*1000:<12.2f} {period:<12.3f} {period*1000:<12.1f}")

    # --- Summary table for GDS ---
    print("\n--- COMPONENT SUMMARY FOR GDS ---")
    print(f"  Platform:         LNOI (thin-film lithium niobate on insulator)")
    print(f"  Waveguide:        ~800 nm wide × 400 nm thick (single-mode @ 1550 nm)")
    print(f"  Bend radius:      ≥50 μm (low loss)")
    print(f"  Input couplers:   Edge or grating, 3 channels @ {LAMBDA_R*1000:.0f}/{LAMBDA_G*1000:.0f}/{LAMBDA_B*1000:.0f} nm")
    print(f"  Weight couplers:  Edge or grating, 2 channels @ {LAMBDA_PLUS*1000:.0f}/{LAMBDA_MINUS*1000:.0f} nm")
    print(f"  SFG elements:     6 per chamber, PPLN with individual poling periods")
    print(f"  Gates:            Electro-optic MZI switches (LN native EO effect)")
    print(f"  Detectors:        Si photodiodes (sensitive @ ~617-635 nm)")
    print(f"  Output demux:     AWG or cascaded ring filters to separate 6 SFG outputs")
    print(f"  Total chip area:  ~2 mm × 3 mm (estimated)")


if __name__ == "__main__":
    main()
