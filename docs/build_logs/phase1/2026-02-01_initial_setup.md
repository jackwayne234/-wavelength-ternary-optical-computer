# Build Log: 2026-02-01 - Initial Setup & Laser Alignment

**Phase:** 1  
**Builder:** Christopher Riner  
**Duration:** 4 hours  
**Status:** In Progress

## Objectives
- [x] Unpack and inventory all components
- [x] Assemble laser turret mounts
- [ ] Align lasers to mixing core (in progress)
- [ ] Test basic light path

## What Was Built

### Component Inventory
Received and verified all components from BOM:
- ✅ ESP32 DevKit V1 (1x)
- ✅ Adafruit AS7341 sensor (1x)
- ✅ ULN2803A transistor array (1x)
- ✅ Red laser modules 650nm (2x)
- ✅ Green laser modules 520nm (2x)
- ✅ Blue laser modules 405nm (2x)
- ✅ Breadboard and jumper wires
- ✅ 3D printed parts (white mixing core, black sensor housing, 6x laser turrets)

### Assembly Completed
1. **Laser Turrets**: Assembled all 6 turret bases and holders
   - Used M3 screws with compression springs for tilt adjustment
   - Springs provide excellent fine-tuning capability
   - Note: Print quality on turret bases is critical - first layer must be flat

2. **Base Board Preparation**
   - Marked 24"x24" MDF board with grid pattern
   - Drilled mounting holes for laser turrets (10-inch radius circle)
   - Center point marked for mixing core

## Test Results

### Laser Power Test
| Laser | Expected | Measured | Status |
|-------|----------|----------|--------|
| Red #1 | 5mW | 4.8mW | ✅ |
| Red #2 | 5mW | 5.1mW | ✅ |
| Green #1 | 5mW | 4.9mW | ✅ |
| Green #2 | 5mW | 5.0mW | ✅ |
| Blue #1 | 5mW | 4.7mW | ✅ |
| Blue #2 | 5mW | 4.9mW | ✅ |

*Measured with laser power meter borrowed from [friend/university]*

### Initial Light Path Test
- ✅ All lasers power on correctly via ESP32 GPIO
- ⚠️ Blue lasers are VERY dim to the eye (405nm is near-UV)
- ✅ Red and Green clearly visible
- ⚠️ Need to verify Blue with sensor, not by eye

## Issues Encountered

### Issue 1: Blue Laser Visibility
**Problem:** 405nm lasers appear very dim to human eye  
**Impact:** Cannot visually confirm alignment  
**Solution:** Will use AS7341 sensor to confirm blue laser presence  
**Lesson:** Don't trust your eyes for UV/near-UV wavelengths

### Issue 2: Turret Print Warping
**Problem:** One turret base had slight warping on first layer  
**Impact:** Mounting surface not perfectly flat  
**Solution:** Used sandpaper to flatten, works fine  
**Lesson:** Check first layer adhesion carefully when printing

### Issue 3: Spring Tension Variation
**Problem:** Compression springs have slightly different stiffness  
**Impact:** Some turrets easier to adjust than others  
**Solution:** Paired similar springs together (A and B inputs)  
**Lesson:** Buy extra springs and match them in sets

## Photos/Videos

- [IMG_20260201_143022.jpg](media/phase1/IMG_20260201_143022.jpg) - Component inventory laid out
- [IMG_20260201_154511.jpg](media/phase1/IMG_20260201_154511.jpg) - First turret assembly
- [IMG_20260201_162034.jpg](media/phase1/IMG_20260201_162034.jpg) - Base board with marked grid
- [VID_20260201_165445.mp4](media/phase1/VID_20260201_165445.mp4) - All lasers firing (Red/Green visible, Blue barely)

## Next Steps

- [ ] Complete laser alignment to mixing core center
- [ ] Install aluminum light tunnels
- [ ] Flash ESP32 firmware
- [ ] Test AS7341 sensor communication
- [ ] Calibrate sensor baselines

## Resources Used

**Components:**
- 6x M3x20mm screws
- 6x M3 nuts
- 6x compression springs
- 6x laser modules (installed in turrets)

**Tools:**
- 3D printer (Bambu Lab A1)
- Drill with 3mm bit
- Screwdriver set
- Laser power meter
- Caliper for measurements

**References:**
- BOM_24x24_Prototype.md
- ASSEMBLY_INSTRUCTIONS.md
- Laser safety guidelines

## Notes & Observations

1. **The 405nm blue lasers are no joke** - Even at 5mW, I can see faint fluorescence on white paper. Need to be careful about reflections.

2. **3D printed parts fit well** - The 12mm laser housing diameter matches the turrets perfectly. Good design validation.

3. **Spring tension system works great** - Much better than set screws for fine angular adjustment. Can easily achieve <1 degree precision.

4. **MDF board is heavy** - 24"x24"x0.5" MDF is substantial. Good for stability but hard to move around. Consider this when choosing workspace.

5. **Idea for improvement:** Consider adding a small webcam mount to view the mixing core remotely. Don't want to stare at lasers even if they're "eye-safe."

---

**Total Cost So Far:** ~$180 (components) + $20 (3D printing materials) = $200

**Time Invested:** 4 hours today, ~2 hours prior (design, printing)

**Mood:** Excited! Hardware is real and working. Onto alignment tomorrow.

**Tags:** #phase1 #build-log #laser-alignment #hardware-assembly #day1
