#!/usr/bin/env python3
"""
Test script to validate the new Sellmeier material model.
Compare against expected LiNbO3 refractive indices.
"""
import numpy as np

# Sellmeier coefficients for LiNbO3 ordinary ray (Jundt 1997)
SELLMEIER_A1 = 1.0       # Fixed term
SELLMEIER_B1 = 2.6734    # First oscillator strength  
SELLMEIER_B2 = 1.2290    # Second oscillator strength
SELLMEIER_C1 = 0.1327    # First resonance wavelength (μm)
SELLMEIER_C2 = 0.2431    # Second resonance wavelength (μm)

def compute_sellmeier_index(wavelength_um):
    """Refractive index from Sellmeier equation."""
    wl2 = wavelength_um**2
    c1_sq = SELLMEIER_C1**2
    c2_sq = SELLMEIER_C2**2
    n2 = SELLMEIER_A1 + SELLMEIER_B1*wl2/(wl2 - c1_sq) + SELLMEIER_B2*wl2/(wl2 - c2_sq)
    return float(np.sqrt(n2))

def compute_old_lorentzian_index(wavelength_um):
    """Old Lorentzian model for comparison."""
    LINBO3_EPS = 1.472
    LINBO3_SIGMA = 3.035
    LINBO3_FREQ0 = 4.5
    
    f = 1.0 / wavelength_um
    eps = LINBO3_EPS + LINBO3_SIGMA * LINBO3_FREQ0**2 / (LINBO3_FREQ0**2 - f**2)
    return float(np.sqrt(eps))

if __name__ == "__main__":
    print("LiNbO3 Refractive Index Comparison")
    print("=" * 50)
    print(f"{'λ(nm)':<8} {'Sellmeier':<10} {'Old Lor.':<10} {'Diff':<8}")
    print("-" * 40)
    
    # Test wavelengths from our triplets
    wavelengths = [1000, 1020, 1040, 1060, 1080, 1100, 1120, 1140, 1160,
                   1180, 1200, 1220, 1240, 1260, 1280, 1300, 1320, 1340,
                   1550]  # Include 1550nm (telecom reference)
    
    for wl_nm in wavelengths:
        wl_um = wl_nm / 1000.0
        n_sellmeier = compute_sellmeier_index(wl_um)
        n_lorentzian = compute_old_lorentzian_index(wl_um)
        diff = n_sellmeier - n_lorentzian
        
        print(f"{wl_nm:<8} {n_sellmeier:<10.4f} {n_lorentzian:<10.4f} {diff:<+8.4f}")
    
    print("\nExpected LiNbO3 indices at key wavelengths:")
    print("1000nm: ~2.25, 1550nm: ~2.20 (literature values)")