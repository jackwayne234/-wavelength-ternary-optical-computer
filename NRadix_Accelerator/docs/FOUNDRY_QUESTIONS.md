# N-Radix Foundry Questions & Packaging Notes

## Target Configuration
- **Chip:** 243x243 systolic array
- **Wavelengths:** MVP = 1 triplet (1550/1310/1064 nm), full = 6 triplets
- **Performance:** ~1.6 PFLOPS (MVP) / ~9.4 PFLOPS (full)
- **Fiber channels:** 243 input + 243 output = 486 total

---

## Questions for Foundry

### Fabrication
1. What PDK/process do you recommend for silicon photonics at 1550/1310/1064 nm?
2. What's the minimum waveguide spacing you support?
3. Do you have ring resonators and AWG demux in your PDK?
4. What's the MPW (multi-project wafer) schedule and cost?
5. What's the typical die size limit?

### Fiber Coupling & Packaging
1. Do you offer fiber array attach in-house or through a partner?
2. Edge coupling or grating couplers - which do you support/recommend?
3. What's the coupling loss spec for edge coupling at our wavelengths?
4. Can you do 243-channel fiber arrays, or do we need to split into smaller blocks?
5. What alignment tolerance do you achieve (active vs passive alignment)?
6. What's the MOQ for packaged parts?
7. What's the lead time: bare die vs packaged?

### Pricing (Ballpark Estimates to Validate)
| Item | Estimated Range |
|------|-----------------|
| MPW slot (bare die) | $5-20k |
| Fiber array attach | $10-50k |
| Full turnkey package | $50-100k+ |

### Thermal & Reliability
1. What's the recommended operating temperature range?
2. Do you provide thermal management options (TEC integration)?
3. What reliability testing do you offer (temp cycling, humidity)?

---

## Foundries to Contact

### Tier 1 - Silicon Photonics Foundries
- **AIM Photonics** (US) - Albany, NY - Good for US-based prototyping
- **IMEC** (Belgium) - Leading-edge process, expensive
- **GlobalFoundries** (US) - 45nm/90nm photonics platform
- **TSMC** (Taiwan) - Has photonics offering, higher volume focus

### Tier 2 - Specialized / Packaging
- **PHIX** (Netherlands) - Photonic packaging specialist
- **Tyndall Institute** (Ireland) - Research-friendly, good for prototypes
- **LioniX International** (Netherlands) - TriPleX platform, good for prototypes
- **Applied Nanotools** (Canada) - Quick-turn prototyping

---

## Packaging Houses (If Using Bare Die)
- **PHIX Photonics Assembly** - Netherlands
- **Tyndall National Institute** - Ireland
- **Fraunhofer HHI** - Germany
- **ficonTEC** - Germany (equipment + services)

---

## Notes

### PE Architecture: Simple = Higher Yield

**BREAKTHROUGH:** PEs are now dramatically simplified.

| Component | Old Design | New Design |
|-----------|-----------|------------|
| PE complexity | Mixer + bistable Kerr resonator | **Mixer + routing only** |
| Weight storage | Per-PE (exotic, tight tolerances) | **Centralized optical RAM** |
| Fabrication risk | Every PE needs working memory | **Simple passive optics** |

**Why this matters for foundry:**
- **Higher yield** - PEs are just passive optics (mixers + waveguides). No exotic per-PE memory.
- **Easier fab** - The hard part (optical memory) is centralized in CPU's optical RAM, not distributed across thousands of PEs.
- **Better scaling** - 6,561 simple PEs is much more manufacturable than 6,561 PEs-with-integrated-memory.

**Questions for foundry:**
1. What's your typical yield for passive photonic circuits vs. active memory elements?
2. Can you characterize our simple PE design (just mixer + routing) for yield estimation?

### Edge Coupling vs Grating Couplers
| Aspect | Edge Coupling | Grating Couplers |
|--------|--------------|------------------|
| Loss | ~1-2 dB | ~2-3 dB |
| Alignment tolerance | ~1 µm | ~2-3 µm |
| Wavelength sensitivity | Low | High (need different gratings per λ) |
| Recommendation | **Preferred for N-Radix** | Backup option |

### Fiber Array Options
- Standard V-groove arrays come in 8, 12, 16, 32 channels
- 243 channels = likely need custom array or multiple blocks
- Companies: OZ Optics, Chiral Photonics, PHIX

---

## MVP Path
1. Get bare die from foundry MPW run
2. Package with 1 triplet (3 wavelengths) initially
3. Validate with simpler fiber setup (maybe just corners + center for testing)
4. Scale to full 243-channel array once proven

---

*Last updated: 2026-02-05*
