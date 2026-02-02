# Session Notes - February 2, 2026

## Summary

Comprehensive session covering GDS chip generation, GitHub organization, foundry submission preparation, **wavelength optimization**, and **simulation verification** for the 81-trit ternary optical computer.

---

## What We Accomplished (Session 2 - Afternoon)

### 7. Centered Chip Layout
- Moved frontend (Kerr clock + Y-junction) to **chip center** to minimize signal degradation
- ALUs arranged in 9 zones (3×3) around the center
- Reduces maximum path length by ~50%
- Equalizes signal power across all 81 ALUs

### 8. Wavelength Optimization (MAJOR)

**Problem:** Original wavelengths (1.55, 1.30, 1.00 μm) produced 6 different SFG outputs for 6 input combinations, but we only have 3 detectors.

**Solution:** Choose Green wavelength as harmonic mean of Red and Blue so that:
- R+B (result=0) produces **same SFG output** as G+G (result=0)

**Optimized Input Wavelengths:**
| Color | Old | New | Ternary |
|-------|-----|-----|---------|
| Red | 1.55 μm | **1.550 μm** | -1 |
| Green | 1.30 μm | **1.216 μm** | 0 |
| Blue | 1.00 μm | **1.000 μm** | +1 |

Formula: λ_Green = 2 × λ_Red × λ_Blue / (λ_Red + λ_Blue) = 1.216 μm

### 9. Simulation Verification

Ran all 6 SFG mixer combinations using `universal_mixer.py`:

| A | B | Result | SFG Output | Verified |
|---|---|--------|------------|----------|
| Red | Red | -2 | 0.775 μm | ✓ |
| Red | Green | -1 | 0.681 μm | ✓ |
| Red | Blue | 0 | **0.6078 μm** | ✓ |
| Green | Green | 0 | **0.6080 μm** | ✓ |
| Green | Blue | +1 | 0.549 μm | ✓ |
| Blue | Blue | +2 | 0.500 μm | ✓ |

**Key Result:** R+B and G+G outputs differ by only **0.2 nm** - same detector catches both!

### 10. Output Stage Redesign

Detectors now tuned to **SFG output wavelengths** (not input wavelengths):

| Detector | Wavelength | Detects Result |
|----------|-----------|----------------|
| Det -1 | 0.681 μm | -1 (from R+G) |
| Det 0 | 0.608 μm | 0 (from R+B or G+G) |
| Det +1 | 0.549 μm | +1 (from G+B) |

All outputs in visible range (0.5-0.8 μm) - Si detector compatible!

### 11. Component Parameter Verification

Verified simulation parameters match chip generator:

| Component | Parameter | Value | Source |
|-----------|-----------|-------|--------|
| Ring Resonator | radius | 5.0 μm | PDK minimum |
| | gap | 0.15 μm | Simulation |
| SFG Mixer | length | 20 μm | Simulation |
| | width | 0.8 μm | Simulation |
| Photodetector | length | 2.0 μm | Simulation |
| Material | n_core | 2.2 | LiNbO3 |
| | chi2 | 0.5 | Simulation |

### 12. Data Organization

Organized `Research/data/` into subdirectories:
- `gds/` - Chip layout files
- `png/` - Simulation result images
- `csv/` - Mixer spectral data
- `logs/` - Simulation logs
- `video/` - Selector animations
- `h5/` - Meep HDF5 raw data

---

## What We Accomplished (Session 1 - Morning)

### 1. GitHub Repository Cleanup
- Uploaded `ternary_81trit_optimal.gds` to GitHub
- Reorganized root directory:
  - Moved setup guides to `docs/guides/`
  - Moved shell scripts to `bin/`
  - Moved `citations.bib` to `Research/papers/`
- Added `.gitignore` entries for local files (ebay files, CLAUDE.md, etc.)
- Fixed `tools/README.md` URL (Replit → Render.com)
- Updated README with:
  - Table of contents
  - Recent activity section (collapsible)

### 2. Foundry Submission Documents
- Created `Phase3_Chip_Simulation/DESIGN_SUMMARY.md` - complete design datasheet
- Created `Phase3_Chip_Simulation/foundry_inquiry_email.txt` - template email

**Foundries to contact:**
- Applied Nanotools (Canada) - info@appliednt.com
- Ligentec (Switzerland) - mpw@ligentec.com
- HyperLight (Boston) - info@hyperlightcorp.com (best for LiNbO3)
- AIM Photonics (US) - info@aimphotonics.com

### 3. Chip Generator Enhancements

**New components added:**
- `kerr_resonator()` - Optical clock/timing (layer 5)
- `y_junction()` - Beam splitter
- `awg_demux()` - Arrayed Waveguide Grating for R/G/B separation (layer 6)
- `optical_frontend()` - Complete input stage
- `ternary_output_stage()` - 3-channel wavelength-discriminating detector
- `generate_complete_alu()` - Full ALU with frontend + output
- `generate_complete_81_trit()` - Full 81-trit chip

**Menu options:**
```
1-4:  Basic operations (add/sub/mul/div)
5:    Single ALU (configurable)
6:    N-trit processor
7:    Power-of-3 processor
8:    81-trit processor (basic)
9:    Custom components (a-k)
10:   Complete ALU (frontend + ALU + output)
11:   FULL 81-TRIT CHIP [RECOMMENDED]
```

**Labels:**
- Now on dedicated layer **100/0** (toggle in KLayout)
- Shortened to standard naming: SEL_1550, DET_R, A, B, Q, MIX, etc.

### 4. Architecture Clarification

**Signal flow (updated with SFG output detection):**
```
CW Laser → Kerr Clock → Y-Junction → AWG (demux) → Selectors → Combiner →
    (1.55, 1.216, 1.00 μm)                                          ↓
                                                              SFG Mixer (χ²)
                                                                    ↓
                                                        (0.681, 0.608, 0.549 μm)
                                                                    ↓
                                                           Splitter → 3 Photodetectors
                                                                    ↓
                                                           DET_-1, DET_0, DET_+1 (to GPIO)
```

**Ternary Addition Truth Table:**
| A | B | Result | SFG Output λ | Detector |
|---|---|--------|--------------|----------|
| -1 | -1 | -2 | 0.775 μm | (overflow) |
| -1 | 0 | -1 | 0.681 μm | DET_-1 |
| -1 | +1 | 0 | 0.608 μm | DET_0 |
| 0 | 0 | 0 | 0.608 μm | DET_0 |
| 0 | +1 | +1 | 0.549 μm | DET_+1 |
| +1 | +1 | +2 | 0.500 μm | (overflow) |

**Interface to binary computer:**
- 6 GPIO outputs: V_red_A, V_grn_A, V_blu_A, V_red_B, V_grn_B, V_blu_B
- 3 GPIO inputs: DET_-1, DET_0, DET_+1
- Input lasers always on; selectors gate which wavelengths pass
- Computer sets voltages, physics does the math, read which detector fires

### 5. GDS Files Generated

| File | Description |
|------|-------------|
| `ternary_81trit_optimal.gds` | Basic 81-trit (option 8) |
| `ternary_complete_alu.gds` | Single complete ALU (option 10) |
| `ternary_81trit_full.gds` | Full 81-trit with frontend (option 11) |
| `optical_frontend.gds` | Frontend only (option 9→k) |

### 6. KLayout Integration
- Created toggle labels macro: `~/.klayout/macros/toggle_labels.lym`
- Keyboard shortcut: **L** (or Tools → Toggle GDS Labels)
- Labels on layer 100/0 for easy visibility toggle

---

## GDS Layers

| Layer | Purpose |
|-------|---------|
| 1/0 | Waveguide core |
| 2/0 | SFG mixer region (χ²) |
| 3/0 | Photodetector region |
| 4/0 | DFG divider region |
| 5/0 | Kerr nonlinear region |
| 6/0 | AWG body |
| 100/0 | Labels (toggle in KLayout) |

---

## Next Steps

1. ~~**Generate final GDS**~~ ✅ Done - `ternary_81trit_full.gds` with centered layout
2. ~~**Verify wavelengths**~~ ✅ Done - Simulations confirm R+B = G+G (0.2 nm difference)
3. **Update design summary** with new wavelengths (1.550, 1.216, 1.000 μm)
4. **Convert design summary to PDF**
5. **Send inquiry emails** to foundries
6. **Wait for PDK** from chosen foundry
7. **Regenerate GDS** with foundry-specific layers and design rules
8. **Submit for MPW run**

## Simulation Files Generated

| File | Description |
|------|-------------|
| `mixer_data_RED_RED.csv` | R+R → 0.775 μm |
| `mixer_data_RED_GREEN.csv` | R+G → 0.681 μm |
| `mixer_data_RED_BLUE.csv` | R+B → 0.608 μm |
| `mixer_data_GREEN_GREEN.csv` | G+G → 0.608 μm |
| `mixer_data_GREEN_BLUE.csv` | G+B → 0.549 μm |
| `mixer_data_BLUE_BLUE.csv` | B+B → 0.500 μm |

---

## Commands Reference

```bash
# Run chip generator
./launch_chip_generator.sh

# Or manually:
cd /home/jackwayne/Desktop/Optical_computing
source bin/activate_env.sh
python3 Research/programs/ternary_chip_generator.py

# Open GDS in KLayout
klayout Research/data/gds/ternary_81trit_full.gds

# Run SFG mixer simulation for any two wavelengths
python3 Research/programs/universal_mixer.py --wvl1 1.55 --wvl2 1.216 --label1 RED --label2 GREEN
```

---

*Session with Claude Code - Opus 4.5*
