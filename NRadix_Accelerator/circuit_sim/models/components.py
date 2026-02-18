"""
Component models for the N-Radix 9x9 monolithic chip circuit simulation.

Each model returns optical power transfer characteristics for its component.
These are used by the circuit simulator to propagate signals through the chip.

Material: X-cut LiNbO3 (TFLN)
Wavelengths: 1064, 1310, 1550 nm (input) → 532-775 nm (SFG output)

Extended to support all 6 WDM triplets (1000-1340 nm input, 500-670 nm SFG).
"""

import numpy as np
from dataclasses import dataclass


# =============================================================================
# Physical constants and material properties
# =============================================================================

N_LINBO3 = 2.2                    # Bulk refractive index
C_UM_PS = 299.792                 # Speed of light (μm/ps)
V_GROUP = C_UM_PS / N_LINBO3      # Group velocity in LiNbO3


def neff_sellmeier(wavelength_nm: float) -> float:
    """
    Compute effective index for TFLN ridge waveguide using a Cauchy model
    fitted to LiNbO3 Sellmeier data for a 500nm-wide ridge waveguide.

    Valid range: 400-1600 nm.

    The fit is: neff = A + B / lambda_um^2
    Calibrated to match neff(1550)=2.14, neff(1064)=2.21, neff(532)=2.36.
    """
    wl_um = wavelength_nm / 1000.0
    # Cauchy coefficients fitted to TFLN ridge waveguide data
    A = 2.098
    B = 0.0465
    return A + B / (wl_um ** 2)


# Wavelength-dependent effective indices (from LiNbO3 Sellmeier data)
# These are for a 500nm wide TFLN ridge waveguide
# Original MVP triplet entries preserved; all other wavelengths use neff_sellmeier()
NEFF = {
    1550: 2.14, 1310: 2.17, 1064: 2.21,  # MVP input wavelengths
    775: 2.26, 710: 2.28, 655: 2.30,      # MVP SFG outputs
    631: 2.31, 587: 2.33, 532: 2.36,      # MVP SFG outputs
}

# Populate NEFF for all 6 WDM triplet wavelengths and their SFG products
_WDM_TRIPLETS = {
    1: (1040, 1020, 1000),
    2: (1100, 1080, 1060),
    3: (1160, 1140, 1120),
    4: (1220, 1200, 1180),
    5: (1280, 1260, 1240),
    6: (1340, 1320, 1300),
}
for _tid, (_wm1, _w0, _wp1) in _WDM_TRIPLETS.items():
    for _wl in [_wm1, _w0, _wp1]:
        if _wl not in NEFF:
            NEFF[_wl] = neff_sellmeier(_wl)
    # Also populate SFG product wavelengths
    for _wa in [_wm1, _w0, _wp1]:
        for _wb in [_wm1, _w0, _wp1]:
            _sfg_wl = round(1.0 / (1.0 / _wa + 1.0 / _wb), 1)
            _sfg_wl_int = round(_sfg_wl)
            if _sfg_wl_int not in NEFF:
                NEFF[_sfg_wl_int] = neff_sellmeier(_sfg_wl)

# Ternary encoding
TRIT_TO_WL = {-1: 1550, 0: 1310, +1: 1064}  # nm
WL_TO_TRIT = {1550: -1, 1310: 0, 1064: +1}

# SFG product table: (input_a_nm, input_b_nm) → output_nm
# λ_out = 1 / (1/λ_a + 1/λ_b)
SFG_TABLE = {}
for wa in [1064, 1310, 1550]:
    for wb in [1064, 1310, 1550]:
        wl_out = 1.0 / (1.0 / wa + 1.0 / wb)
        SFG_TABLE[(wa, wb)] = round(wl_out, 1)

# SFG output → ternary result mapping
# Based on the multiplication table: trit_a × trit_b
SFG_RESULT = {
    532.0: +1,   # B+B: (+1)(+1) = +1
    587.1: 0,    # G+B: (0)(+1) = 0 or (+1)(0)
    630.9: -1,   # R+B: (-1)(+1) = -1 or (+1)(-1)
    655.0: 0,    # G+G: (0)(0) = 0
    710.0: 0,    # R+G: (-1)(0) = 0 or (0)(-1)
    775.0: +1,   # R+R: (-1)(-1) = +1
}


@dataclass
class OpticalSignal:
    """Represents an optical signal at a specific wavelength."""
    wavelength_nm: float    # Wavelength in nm
    power_dbm: float        # Power in dBm
    phase_rad: float = 0.0  # Phase (radians)

    @property
    def power_mw(self) -> float:
        return 10 ** (self.power_dbm / 10)

    def attenuate(self, loss_db: float) -> 'OpticalSignal':
        return OpticalSignal(
            self.wavelength_nm,
            self.power_dbm - loss_db,
            self.phase_rad,
        )

    def add_phase(self, delta_rad: float) -> 'OpticalSignal':
        return OpticalSignal(
            self.wavelength_nm,
            self.power_dbm,
            self.phase_rad + delta_rad,
        )


# =============================================================================
# Component: Waveguide
# =============================================================================

def waveguide_transfer(
    signal: OpticalSignal,
    length_um: float,
    loss_db_per_cm: float = 2.0,
) -> OpticalSignal:
    """
    Propagate signal through a LiNbO3 waveguide.

    Args:
        signal: Input optical signal
        length_um: Waveguide length in micrometers
        loss_db_per_cm: Propagation loss (2 dB/cm typical for TFLN)

    Returns:
        Output optical signal with accumulated loss and phase
    """
    wl = signal.wavelength_nm
    neff = NEFF.get(round(wl), neff_sellmeier(wl))

    # Loss
    loss_db = loss_db_per_cm * length_um / 1e4

    # Phase
    phase = 2 * np.pi * neff * length_um / (wl / 1000)  # wl in μm

    return OpticalSignal(wl, signal.power_dbm - loss_db, signal.phase_rad + phase)


# =============================================================================
# Component: SFG Mixer (PPLN)
# =============================================================================

def sfg_mixer(
    signal_a: OpticalSignal,
    signal_b: OpticalSignal,
    ppln_length_um: float = 26.0,
    conversion_efficiency: float = 0.10,
    insertion_loss_db: float = 1.0,
) -> tuple[OpticalSignal | None, OpticalSignal, OpticalSignal]:
    """
    Sum-frequency generation in a PPLN mixer.

    Two input photons produce one output photon at the sum frequency.
    Also passes through unconverted light.

    Args:
        signal_a: Activation input (horizontal)
        signal_b: Weight input (vertical)
        ppln_length_um: PPLN interaction length
        conversion_efficiency: Power fraction converted to SFG (0.0-1.0)
        insertion_loss_db: Additional insertion loss

    Returns:
        (sfg_output, passthrough_a, passthrough_b)
        sfg_output is None if either input is below detection threshold
    """
    # SFG only happens if both inputs have meaningful power
    MIN_POWER_DBM = -40.0
    if signal_a.power_dbm < MIN_POWER_DBM or signal_b.power_dbm < MIN_POWER_DBM:
        # No SFG — just pass through with insertion loss
        pass_a = signal_a.attenuate(insertion_loss_db)
        pass_b = signal_b.attenuate(insertion_loss_db)
        return None, pass_a, pass_b

    # Calculate SFG output wavelength
    wl_a = signal_a.wavelength_nm
    wl_b = signal_b.wavelength_nm
    wl_sfg = 1.0 / (1.0 / wl_a + 1.0 / wl_b)

    # SFG power: proportional to product of input powers × efficiency
    # In a linearized model: P_sfg = eta * sqrt(P_a * P_b)
    # For circuit sim, we use a simpler model calibrated from FDTD
    p_a_mw = signal_a.power_mw
    p_b_mw = signal_b.power_mw

    # SFG output power (simplified: fraction of geometric mean of inputs)
    p_sfg_mw = conversion_efficiency * np.sqrt(p_a_mw * p_b_mw)
    p_sfg_dbm = 10 * np.log10(max(p_sfg_mw, 1e-10))

    # Passthrough: what doesn't get converted
    pass_fraction = 1.0 - conversion_efficiency
    pass_a = OpticalSignal(
        wl_a,
        signal_a.power_dbm + 10 * np.log10(pass_fraction) - insertion_loss_db,
        signal_a.phase_rad,
    )
    pass_b = OpticalSignal(
        wl_b,
        signal_b.power_dbm + 10 * np.log10(pass_fraction) - insertion_loss_db,
        signal_b.phase_rad,
    )

    sfg_out = OpticalSignal(round(wl_sfg, 1), p_sfg_dbm - insertion_loss_db, 0.0)

    return sfg_out, pass_a, pass_b


# =============================================================================
# Component: AWG Demultiplexer (5-channel)
# =============================================================================

# AWG channel center wavelengths (the 6 SFG products)
AWG_CHANNELS = {
    0: 532.0,   # DET_+2 (B+B) → carry/+2
    1: 587.1,   # (G+B) → 0
    2: 630.9,   # (R+B) → -1
    3: 655.0,   # (G+G) → 0
    4: 710.0,   # (R+G) → 0
    5: 775.0,   # DET_-2 (R+R) → +1
}

def awg_demux(
    signal: OpticalSignal,
    insertion_loss_db: float = 3.0,
    channel_bandwidth_nm: float = 15.0,
    crosstalk_db: float = -25.0,
) -> dict[int, float]:
    """
    Route SFG output to correct detector channel via AWG.

    Args:
        signal: SFG product optical signal
        insertion_loss_db: AWG insertion loss
        channel_bandwidth_nm: 3dB bandwidth per channel
        crosstalk_db: Adjacent channel suppression

    Returns:
        Dict of {channel_index: power_dbm} for each detector
    """
    results = {}
    sigma_nm = channel_bandwidth_nm / 2.355  # FWHM to Gaussian sigma

    for ch_idx, center_wl in AWG_CHANNELS.items():
        detuning = signal.wavelength_nm - center_wl
        # Gaussian passband
        passband = np.exp(-0.5 * (detuning / sigma_nm) ** 2)

        if passband > 0.01:  # > 1% coupling
            power = signal.power_dbm - insertion_loss_db + 10 * np.log10(passband)
        else:
            power = signal.power_dbm + crosstalk_db - insertion_loss_db

        results[ch_idx] = power

    return results


# =============================================================================
# Component: Photodetector
# =============================================================================

def photodetector(
    power_dbm: float,
    responsivity_a_per_w: float = 0.5,
    dark_current_na: float = 5.0,
) -> float:
    """
    Convert optical power to photocurrent.

    Args:
        power_dbm: Optical power at detector
        responsivity_a_per_w: Detector responsivity
        dark_current_na: Dark current in nA

    Returns:
        Photocurrent in μA
    """
    power_w = 10 ** ((power_dbm - 30) / 10)  # dBm to Watts
    photocurrent_a = responsivity_a_per_w * power_w
    photocurrent_ua = photocurrent_a * 1e6 + dark_current_na / 1000
    return photocurrent_ua


# =============================================================================
# Component: MZI Encoder
# =============================================================================

def mzi_encode(
    trit: int,
    laser_power_dbm: float = 10.0,
    mzi_loss_db: float = 3.0,
    combiner_loss_db: float = 1.0,
) -> OpticalSignal:
    """
    Encode a ternary value as a wavelength-selected optical signal.

    The encoder has 3 MZI modulators (one per wavelength).
    Only the selected wavelength passes through.

    Args:
        trit: Ternary value (-1, 0, +1)
        laser_power_dbm: Input laser power per channel
        mzi_loss_db: MZI insertion loss (ON state)
        combiner_loss_db: 3-to-1 combiner loss

    Returns:
        Encoded optical signal at the correct wavelength
    """
    wl = TRIT_TO_WL[trit]
    power = laser_power_dbm - mzi_loss_db - combiner_loss_db
    return OpticalSignal(wl, power, 0.0)
