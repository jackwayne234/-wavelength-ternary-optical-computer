# Lessons Learned: 3D Printing for Optical Components

**Date:** 2026-02-01  
**Phase:** 1  
**Author:** Christopher Riner

## Overview

3D printing optical component housings requires different considerations than typical mechanical parts. Light leakage, surface finish, and dimensional accuracy are critical.

## What Worked

### White PLA for Mixing Core
- **Result:** Excellent reflectivity and light diffusion
- **Settings:** 100% infill, 0.2mm layer height, white PLA
- **Why it works:** White pigment reflects all visible wavelengths; 100% infill prevents light leakage through layer gaps
- **Tip:** Use fresh, dry filament - moisture causes bubbles that scatter light unpredictably

### Black PLA for Sensor Housing
- **Result:** Effective ambient light blocking
- **Settings:** 100% infill, matte black PLA
- **Why it works:** Black absorbs stray light; matte finish prevents reflections
- **Tip:** Paint interior with matte black paint for extra light absorption

### Spring-Loaded Turret Design
- **Result:** Excellent fine adjustment capability
- **Mechanism:** M3 screws with compression springs provide 3-point tilt adjustment
- **Why it works:** Springs allow smooth, continuous adjustment with good holding force
- **Tip:** Match spring stiffness across all turrets for consistent feel

## What Didn't Work

### Transparent/Clear Filament for Light Guides
- **Attempt:** Printed light tunnels in clear PETG
- **Problem:** Layer lines scatter light, poor optical quality
- **Solution:** Switched to aluminum tubing (1/2" OD)
- **Lesson:** FDM printing cannot achieve optical clarity; use machined materials for light paths

### Standard Infill (20%) for Mixing Core
- **Attempt:** Initial print with 20% gyroid infill
- **Problem:** Light leaked through infill gaps, uneven mixing
- **Solution:** Re-printed at 100% infill
- **Lesson:** Optical components need solid construction

### Glossy/ Silk Filament
- **Attempt:** Used silk PLA for aesthetic finish
- **Problem:** Shiny surface caused specular reflections, hard to photograph
- **Solution:** Switched to matte PLA
- **Lesson:** Function over form for optical parts

## Key Parameters

### Critical Settings
| Parameter | Mixing Core | Sensor Housing | Turrets |
|-----------|-------------|----------------|---------|
| Infill | 100% | 100% | 30-50% |
| Layer Height | 0.2mm | 0.2mm | 0.3mm |
| Wall Count | 4+ | 4+ | 3 |
| Color | White | Black | Any |
| Material | PLA | PLA | PLA/PETG |

### Post-Processing
- **Mixing Core:** No post-processing needed
- **Sensor Housing:** Paint interior matte black
- **Turrets:** Check hole diameter (12mm), sand if needed

## Design Tips

### For Light-Tight Components
1. **Minimum 3mm wall thickness** - Prevents light leakage
2. **100% infill** - No gaps for light to pass through
3. **Avoid thin features** - Prone to warping and light leaks
4. **Test with flashlight** - Shine light through to check for leaks

### For Precision Fits
1. **Design for tolerance** - Holes 0.2mm larger than part
2. **First layer quality critical** - Must be flat for mounting surfaces
3. **Orientation matters** - Print cylindrical features vertically when possible
4. **Test fit early** - Print one part before committing to full batch

### For Optical Surfaces
1. **Layer height ≤ 0.2mm** - Smoother surface finish
2. **Avoid overhangs on optical paths** - Cause rough surfaces
3. **Consider vapor smoothing** - For ABS (not recommended for PLA)
4. **Accept limitations** - FDM cannot achieve optical polish

## Cost Analysis

| Component | Quantity | Print Time | Material Cost | Notes |
|-----------|----------|------------|---------------|-------|
| Mixing Core | 1 | 4 hours | $3 | Critical part, print slowly |
| Sensor Housing | 1 | 2 hours | $1.50 | Use matte black |
| Turret Base | 6 | 30 min each | $0.50 each | Can use any rigid material |
| Turret Holder | 6 | 20 min each | $0.30 each | Must fit 12mm laser |
| **Total** | - | ~10 hours | **~$10** | Plus failed prints |

**Failed Print Cost:** Budget 20-30% extra for failed prints, especially for mixing core.

## Recommended Printers

### Tested and Working
- **Bambu Lab A1:** Excellent results, fast, reliable
- **Prusa i3 MK3S:** Good results, slower but reliable
- **Ender 3 (modded):** Adequate with upgrades (direct drive, better cooling)

### Settings to Avoid
- Draft/ fast mode (poor quality)
- Low infill (light leaks)
- Large layer heights (>0.3mm for optical parts)
- Wet/ old filament (bubbles, poor layer adhesion)

## Supplier Recommendations

### Filament
- **Hatchbox White PLA:** Good, consistent white
- **eSun Matte Black PLA:** Excellent light absorption
- **Prusament:** Premium quality, worth the cost for critical parts

### Avoid
- Cheap no-name filament (inconsistent diameter, poor quality)
- Transparent/ clear filament (cannot achieve optical quality)
- Glow-in-the-dark filament (phosphors interfere with light measurements)

## Future Improvements

### Design Iterations
1. **Add light baffles** - Internal ribs to block stray light
2. **Integrated cable management** - Channels for laser wires
3. **Magnetic mounting** - For quick component swaps
4. **Adjustable sensor height** - Fine-tune distance to mixing core

### Alternative Manufacturing
- **Resin printing (SLA):** Better surface finish, but more expensive and smaller build volume
- **CNC machining:** Best precision, but costly for one-offs
- **Laser cutting:** Good for 2D parts (mounting plates, brackets)

## Safety Notes

- **Ventilation:** PLA is generally safe, but always print in ventilated area
- **Laser safety:** 3D printed parts can melt or burn if exposed to high-power lasers
- **Fire risk:** Never leave printer unattended for long prints
- **Post-processing:** Sanding PLA creates fine dust - wear mask

## Conclusion

3D printing is excellent for prototyping optical component housings, but requires careful attention to:
- **100% infill** for light-tightness
- **White/Black colors** for reflectivity/absorption
- **Quality filament** for consistency
- **Proper design** for printability

For production or high-precision applications, consider machined aluminum or resin-printed parts.

---

**Related Build Logs:**
- [2026-02-01_initial_setup.md](../build_logs/phase1/2026-02-01_initial_setup.md)

**Related Files:**
- `module_mixing_core.scad`
- `module_sensor_housing.scad`
- `module_laser_turret.scad`

**Tags:** #3d-printing #lessons-learned #optical-design #phase1 #fabrication
