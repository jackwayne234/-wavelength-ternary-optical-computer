# ADR 001: Wavelength Selection for Phase 1 Prototype

**Date:** 2026-01-15  
**Status:** Accepted  
**Phase:** 1

## Context

We need to select three distinct wavelengths for the balanced ternary logic states (-1, 0, +1) in the Phase 1 visible-light prototype. The selection must:
- Be clearly distinguishable by the AS7341 spectral sensor
- Be safe for human exposure (Class 2 or lower)
- Be cost-effective and readily available
- Map intuitively to ternary states

## Decision

We will use:
- **Red (650nm)** = Logic -1
- **Green (520nm)** = Logic 0  
- **Blue (405nm)** = Logic +1

## Consequences

### Positive
- **Sensor compatibility:** AS7341 has dedicated channels for 630nm (F7), 515nm (F4), and 445nm (F2)
- **Intuitive mapping:** Red/Blue as opposites (-1/+1), Green as neutral (0)
- **Cost:** 650nm, 520nm, and 405nm laser diodes are mass-produced and inexpensive
- **Safety:** All wavelengths visible (405nm borderline but acceptable), easy to avoid accidental exposure
- **Availability:** Readily available from multiple suppliers (Amazon, eBay, AliExpress)

### Negative
- **Blue visibility:** 405nm is near-UV and appears very dim to human eye
- **Green cost:** 520nm diodes are 2-3x more expensive than red/blue
- **Wavelength precision:** Consumer lasers may vary ±10nm from nominal
- **Temperature drift:** Laser wavelength shifts with temperature (0.2-0.3nm/°C)

### Risks and Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Blue laser not detected by sensor | Low | High | Verify with sensor before finalizing; use 445nm channel |
| Wavelength overlap causing crosstalk | Low | Medium | Use narrowband filters if needed; sensor has 10 channels |
| Green laser instability | Medium | Medium | Use direct diode (520nm) not DPSS (532nm); add heatsink |
| Eye safety with blue laser | Medium | High | Use Class 2 (<1mW) or Class 3R (<5mW) max; add warning labels |

## Alternatives Considered

### Alternative 1: RGB LEDs instead of lasers
- **Rejected:** LEDs have broad spectrum, poor collimation, hard to align
- **Pros:** Cheaper, safer, no coherence issues
- **Cons:** Would need filters, poor intensity, mixing would be messy

### Alternative 2: 450nm Blue instead of 405nm
- **Rejected:** 450nm is brighter to eye but less distinct from 520nm green
- **Pros:** Better visibility, cheaper diodes
- **Cons:** Closer to green wavelength, potential crosstalk

### Alternative 3: IR wavelengths (780nm, 850nm, 940nm)
- **Rejected:** Invisible, safety concerns, harder to align
- **Pros:** Very cheap, very safe (invisible)
- **Cons:** Cannot visually align, requires IR camera, safety risk (invisible = more dangerous)

### Alternative 4: Telecom wavelengths (1550nm, 1310nm, 850nm)
- **Rejected:** These are for Phase 2 (fiber benchtop)
- **Pros:** Industry standard, proven technology
- **Cons:** Invisible, expensive equipment, overkill for Phase 1

## References

- AS7341 datasheet: Spectral response curves
- Laser safety classification: IEC 60825-1
- "Wavelength-Division Ternary Logic" paper: Section 3.2
- Supplier research: Amazon, DigiKey, Mouser pricing and availability

## Related Decisions

- **ADR 002:** Sensor Selection (AS7341 chosen partly due to wavelength match)
- **ADR 003:** Mixer Design (X-cube prism selected for RGB combination)

---

**Decision ID:** ADR-001  
**Supersedes:** N/A  
**Superseded By:** N/A (still valid)

**Decision Makers:** Christopher Riner  
**Stakeholders:** Future builders, safety reviewers
