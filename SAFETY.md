# ⚠️ SAFETY FIRST: Read Before Building

## ⚡ DANGER: Class 3R Laser Equipment

This project involves ** Class 3R laser diodes** (up to 5mW output). These can cause **permanent eye damage** if mishandled. 

**You MUST complete an ORM assessment before beginning construction.**

---

## 🛑 STOP: Mandatory Safety Requirements

### Before You Start
- [ ] Read this entire safety document
- [ ] Complete the ORM Assessment below
- [ ] Purchase appropriate laser safety equipment
- [ ] Set up a safe workspace
- [ ] Have a safety buddy (someone who knows what you're doing)

### You MUST Have
| Item | Purpose | Cost |
|------|---------|------|
| **Laser Safety Glasses** | Protect eyes from specific wavelengths | $20-50 |
| **Interlock system** | Auto-shutoff if enclosure opened | DIY |
| **Warning signs** | Alert others to laser hazard | $5-10 |
| **Fire extinguisher** | Class C for electrical fires | $20-30 |
| **First aid kit** | Basic medical supplies | $15-25 |

### Laser Safety Glasses Requirements

**CRITICAL:** Regular sunglasses or welding glasses will NOT protect you.

You need **wavelength-specific laser safety glasses**:

| Laser | Wavelength | Glasses Required |
|-------|------------|------------------|
| Red | 650nm | Red/Orange tinted (blocks 600-700nm) |
| Green | 520nm | Red tinted (blocks 500-550nm) |
| Blue | 405nm | Yellow/Amber tinted (blocks 400-450nm) |

**Recommendation:** Purchase glasses that block ALL THREE wavelengths:
- **Multi-wavelength glasses** (~$40-60)
- Look for OD (Optical Density) rating of 3+ for each wavelength
- CE certified or ANSI Z136.1 compliant

**Sources:**
- Amazon: "Laser Safety Glasses 405nm 520nm 650nm"
- ThorLabs (professional grade)
- Edmund Optics

---

## 🎯 Operational Risk Management (ORM) Assessment

**Complete this assessment BEFORE touching any laser equipment.**

### Step 1: Hazard Identification

**Severity (1-5):** How bad could this get?
- 1 = Minor (small scratch)
- 3 = Moderate (medical attention needed)
- 5 = Catastrophic (permanent blindness, fire, death)

**Probability (1-5):** How likely is this?
- 1 = Rare (unlikely to happen)
- 3 = Possible (could happen)
- 5 = Frequent (likely to happen)

**Risk Score = Severity × Probability**
- 1-5: Low risk (acceptable with controls)
- 6-15: Medium risk (controls required)
- 16-25: High risk (unacceptable - redesign needed)

### ORM Worksheet

**Copy this template and fill it out:**

```markdown
## ORM Assessment: [Your Name] - [Date]

### Hazard 1: Direct Eye Exposure to Laser Beam
- **Severity:** 5 (Permanent blindness)
- **Probability:** 3 (Possible if careless)
- **Risk Score:** 15 (HIGH)
- **Controls:**
  - [ ] Wear laser safety glasses at ALL times
  - [ ] Use beam blocks to stop stray reflections
  - [ ] Never look directly into beam or specular reflections
  - [ ] Set up laser barriers/enclosure
  - [ ] Use remote viewing (camera) when possible
- **Residual Risk:** 5 (Low with controls)

### Hazard 2: Reflected Laser Light
- **Severity:** 4 (Eye damage from reflections)
- **Probability:** 4 (Common with shiny surfaces)
- **Risk Score:** 16 (HIGH)
- **Controls:**
  - [ ] Remove/mask reflective surfaces in workspace
  - [ ] Use matte black materials
  - [ ] Cover watches, jewelry, glasses frames
  - [ ] Beam blocks at all reflection points
  - [ ] Enclosed workspace with non-reflective interior
- **Residual Risk:** 4 (Low with controls)

### Hazard 3: Electrical Shock from Power Supplies
- **Severity:** 3 (Electrical injury)
- **Probability:** 2 (Unlikely with care)
- **Risk Score:** 6 (MEDIUM)
- **Controls:**
  - [ ] Use GFCI outlets
  - [ ] Check wiring before powering on
  - [ ] No liquids near electronics
  - [ ] Insulated tools
  - [ ] Power off when making connections
- **Residual Risk:** 2 (Low with controls)

### Hazard 4: Fire from Laser Heating
- **Severity:** 4 (Fire, property damage, injury)
- **Probability:** 2 (Unlikely with 5mW lasers)
- **Risk Score:** 8 (MEDIUM)
- **Controls:**
  - [ ] Fire extinguisher accessible
  - [ ] No flammable materials in beam path
  - [ ] Beam blocks made of metal/ceramic (not plastic)
  - [ ] Never leave lasers unattended when powered
  - [ ] Smoke detector in workspace
- **Residual Risk:** 2 (Low with controls)

### Hazard 5: UV Exposure (405nm Blue Laser)
- **Severity:** 3 (Skin/eye damage, fluorescence hazards)
- **Probability:** 3 (Possible)
- **Risk Score:** 9 (MEDIUM)
- **Controls:**
  - [ ] 405nm-specific safety glasses
  - [ ] Skin protection (long sleeves)
  - [ ] Check for fluorescent materials in workspace
  - [ ] Minimize exposure time
- **Residual Risk:** 3 (Low with controls)

### Overall Assessment
- **Highest Risk:** Direct eye exposure (15) and reflections (16)
- **Mitigation Status:** All hazards controlled
- **Residual Risk Level:** LOW (Acceptable)
- **Approval:** [Your signature/date]
```

---

## 🏗️ Safe Workspace Setup

### Physical Layout
```
┌─────────────────────────────────────┐
│      LASER WORKSPACE                │
│  ┌─────────────────────────────┐    │
│  │    ENCLOSURE (if possible)  │    │
│  │  ┌─────────────────────┐    │    │
│  │  │   LASER SETUP       │    │    │
│  │  │                     │    │    │
│  │  │  [MIXING CORE]      │    │    │
│  │  │       ↑             │    │    │
│  │  │   BEAM PATH         │    │    │
│  │  │       ↓             │    │    │
│  │  │  [LASER TURRETS]    │    │    │
│  │  └─────────────────────┘    │    │
│  │         ↑                   │    │
│  │    INTERLOCK SWITCH         │    │
│  └─────────────────────────────┘    │
│                                     │
│  [OPERATOR POSITION]                │
│  - Seated/standing here             │
│  - Wearing safety glasses           │
│  - Emergency stop within reach      │
│                                     │
│  ⚠️ WARNING SIGNS ON DOOR           │
└─────────────────────────────────────┘
```

### Required Safety Equipment

**Personal Protective Equipment (PPE):**
- [ ] Laser safety glasses (ON before entering workspace)
- [ ] Closed-toe shoes
- [ ] Long sleeves (for 405nm UV protection)
- [ ] Remove reflective jewelry

**Workspace Safety:**
- [ ] Interlock system (door switch kills power)
- [ ] Emergency stop button (big red button)
- [ ] Beam blocks at all exit points
- [ ] Non-reflective surfaces (matte black paint)
- [ ] Warning signs on door
- [ ] Fire extinguisher (Class C)
- [ ] First aid kit
- [ ] Phone/emergency numbers posted

---

## ⚡ Safe Operating Procedures (SOP)

### Pre-Operation Checklist

**Before powering on ANY laser:**

1. **Safety Glasses Check**
   - [ ] Wearing appropriate laser safety glasses
   - [ ] Glasses clean and undamaged
   - [ ] Correct wavelength rating verified

2. **Workspace Check**
   - [ ] No unauthorized personnel in area
   - [ ] Door closed and locked/interlocked
   - [ ] Warning signs visible
   - [ ] Reflective surfaces covered/removed
   - [ ] Beam blocks in place
   - [ ] Fire extinguisher accessible

3. **Equipment Check**
   - [ ] All wiring inspected (no bare wires)
   - [ ] Power supply properly rated
   - [ ] Emergency stop functional
   - [ ] Interlock system tested
   - [ ] No flammable materials in beam path

4. **Personal Check**
   - [ ] No reflective jewelry (watches, rings)
   - [ ] Long sleeves (for UV lasers)
   - [ ] Safety buddy knows you're working
   - [ ] Phone accessible for emergencies

### During Operation

**NEVER:**
- ❌ Look directly into the laser beam
- ❌ Look at specular (mirror-like) reflections
- ❌ Aim laser at people or animals
- ❌ Leave powered lasers unattended
- ❌ Work without safety glasses
- ❌ Use damaged or modified lasers
- ❌ Remove interlocks or safety features

**ALWAYS:**
- ✅ Keep safety glasses on
- ✅ Use beam blocks to stop stray beams
- ✅ Work with a buddy when possible
- ✅ Keep exposure time minimal
- ✅ Use remote viewing (camera) when possible
- ✅ Stay aware of beam path at all times

### Emergency Procedures

**If someone is exposed to laser light:**
1. **IMMEDIATELY** turn off all lasers (emergency stop)
2. Do NOT let person rub their eyes
3. Flush eyes with clean water for 15 minutes
4. **Seek medical attention IMMEDIATELY** (ER or ophthalmologist)
5. Document the incident (wavelength, power, exposure time)

**If fire starts:**
1. Turn off all power (emergency stop)
2. Use Class C fire extinguisher (CO2 or dry chemical)
3. Evacuate if fire cannot be controlled immediately
4. Call 911

**If electrical shock occurs:**
1. Do NOT touch the person if still in contact with electricity
2. Turn off power at breaker
3. Use non-conductive object to separate person from source
4. Call 911 and begin CPR if needed
5. Do NOT move person unless in immediate danger

---

## 👥 Safety Responsibilities

### As the Builder/Operator
- You are responsible for your own safety
- You are responsible for the safety of others in the area
- You must complete ORM assessment before starting
- You must maintain safety equipment
- You must follow all procedures in this document

### As a Safety Buddy
- Know what the operator is doing
- Know the emergency procedures
- Be ready to hit emergency stop
- Call for help if needed
- Do NOT distract the operator during critical operations

### As a Visitor/Bystander
- Do NOT enter laser workspace without permission
- Do NOT enter without safety glasses
- Obey all warning signs
- Ask before touching anything
- Leave immediately if asked

---

## 🎓 Training Requirements

**Before operating lasers, you should understand:**

1. **Laser Fundamentals**
   - How lasers work
   - Why they're dangerous to eyes
   - Difference between direct and reflected beams
   - Why sunglasses don't protect you

2. **Safety Equipment**
   - How to select proper safety glasses
   - How to test interlock systems
   - How to use fire extinguisher
   - How to perform emergency stop

3. **Your Specific Setup**
   - Wavelengths you're using
   - Power levels
   - Beam paths
   - Emergency procedures

**Resources:**
- [Laser Safety Guide (OSHA)](https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.54)
- [ANSI Z136.1 Standard](https://www.lia.org/resources/laser-safety-information/ansi-z136-standards)
- [Laser Institute of America](https://www.lia.org/)

---

## 🚫 When to STOP

**STOP work immediately if:**
- Safety glasses are damaged or missing
- You feel unsafe or unsure
- Someone enters the workspace unexpectedly
- Equipment is malfunctioning
- You cannot control the beam path
- You are tired, distracted, or under the influence
- Interlock system is not working
- Emergency stop is not accessible

**There is no shame in stopping to reassess safety.**

---

## 📋 Safety Documentation

**You MUST document:**
- ORM assessment completion
- Safety equipment inventory
- Any incidents or near-misses
- Safety training completed
- Modifications to safety systems

**Keep records for:**
- Your own reference
- Future builders
- Insurance purposes
- Legal protection

---

## ⚖️ Legal Disclaimer

**By building this project, you acknowledge that:**

1. You understand the risks involved with laser equipment
2. You take full responsibility for your safety
3. You will follow all safety procedures in this document
4. You will not hold the project authors liable for injuries
5. You will not operate lasers without proper safety equipment
6. You will complete an ORM assessment before starting

**This is an open source research project. We share this information for educational purposes. You are responsible for your own safety.**

---

## ✅ Pre-Build Safety Checklist

**Complete ALL items before starting:**

- [ ] Read this entire SAFETY.md document
- [ ] Complete ORM Assessment (template above)
- [ ] Purchase laser safety glasses (wavelength-specific)
- [ ] Set up safe workspace (enclosure, interlocks, signs)
- [ ] Obtain fire extinguisher (Class C)
- [ ] Obtain first aid kit
- [ ] Post emergency numbers
- [ ] Identify safety buddy
- [ ] Test emergency stop button
- [ ] Test interlock system
- [ ] Remove/mask reflective surfaces
- [ ] Install beam blocks
- [ ] Review emergency procedures
- [ ] Have medical facility identified (ophthalmologist/ER)

**Date Completed:** _______________  
**Signature:** _______________

---

## 🆘 Emergency Contacts

**Post these numbers in your workspace:**

- **Poison Control:** 1-800-222-1222
- **Emergency Services:** 911
- **Nearest ER:** ___________________
- **Ophthalmologist:** ___________________
- **Safety Buddy:** ___________________
- **Your Phone:** ___________________

---

## 📚 Additional Safety Resources

### Required Reading
- [OSHA Laser Safety](https://www.osha.gov/laws-regs/regulations/standardnumber/1926/1926.54)
- [ANSI Z136.1 - Safe Use of Lasers](https://www.lia.org/resources/laser-safety-information/ansi-z136-standards)

### Recommended Reading
- Laser Safety: Practical Guide (Laser Institute of America)
- IEC 60825-1 (International laser safety standard)

### Training
- [Laser Safety Certification](https://www.lia.org/education-certification/laser-safety-certification)
- Many universities offer laser safety courses

---

**Remember: You only get one set of eyes. Protect them.**

**Safety is not optional. It is mandatory.**

---

*This safety document is part of the Wavelength-Division Ternary Optical Computer open source project. We share this to help others build safely. You are responsible for your own safety.*

**Last Updated:** February 2026  
**Maintainer:** Christopher Riner  
**Contact:** chrisriner45@gmail.com
