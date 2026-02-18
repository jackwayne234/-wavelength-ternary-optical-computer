# N-Radix Optical Accelerator — Funding & Fabrication Guide

### What you have

- Ternary optical accelerator design, validated up to 81x81 (6,561 PEs)
- GDS layouts and DRC rules ready
- Published papers on Zenodo (DOIs: 10.5281/zenodo.18501296, 10.5281/zenodo.18437600)
- GitHub repo: https://github.com/jackwayne234/-wavelength-ternary-optical-computer
- 148 PFLOPS/chip matrix multiply benchmark (59x NVIDIA B200)

### What you need

- ~$50K for a foundry prototype run
- Foundry to handle 243x243 optical connections (can't be done manually)

---

## Path 1: AIM Photonics (Start Here)

**What it is:** A US Department of Defense-funded institute created specifically
to help American photonic chip designers get from design to fabrication. They
offer subsidized multi-project wafer (MPW) runs, design support, and foundry
access. This is literally what they were built for.

**Cost:** Subsidized — could reduce your $50K down to $5K-$15K for shared wafer
space.

**What to do:**

1. Go to https://www.aimphotonics.com
2. Look for "MPW Access," "Submit a Design," or "Photonic Integrated Circuit
   Fabrication" — or just go to their Contact page
3. Send an email with this template:

---

**Subject:** MPW Access Request — Ternary Optical AI Accelerator (GDS Ready)

Hi,

My name is Christopher Riner. I've designed a wavelength-division ternary
optical accelerator for AI matrix multiplication workloads. The design uses
three standard wavelengths (1550nm, 1310nm, 1064nm) to encode ternary logic
states, achieving ~148 PFLOPS/chip in simulation — approximately 59x NVIDIA's
B200 for matrix multiply.

The design has passed simulation validation up to 81x81 systolic arrays
(6,561 processing elements). GDS layouts and DRC rules are complete. I'm
looking for MPW access to fabricate a prototype.

Published papers:
- Architecture: https://doi.org/10.5281/zenodo.18501296
- Theory: https://doi.org/10.5281/zenodo.18437600

GitHub (full design, simulations, GDS):
https://github.com/jackwayne234/-wavelength-ternary-optical-computer

I'm an independent researcher based in Chesapeake, Virginia. Happy to discuss
technical details or provide additional documentation.

Best,
Christopher Riner
chrisriner45@gmail.com

---

**Timeline:** Response within 1-2 weeks. MPW runs typically schedule quarterly.

**Why this is first:** Lowest barrier to entry. They're funded to help people
exactly like you. No company required. No lengthy application process.

---

## Path 2: NSF SBIR Phase I Grant

**What it is:** A federal grant program for small businesses / sole proprietors
developing innovative technology. Phase I awards $50K-$275K for prototyping
and feasibility. You don't need employees or a big company — a sole
proprietorship works.

**Cost:** Free to apply. They give YOU money.

**What to do:**

1. Go to https://seedfund.nsf.gov
2. Read the "How to Apply" section
3. If you don't already have a sole proprietorship or LLC, set one up in
   Virginia (costs ~$100, takes a day online at the SCC website:
   https://www.scc.virginia.gov)
4. Get a DUNS number (free) and register in SAM.gov (free, takes ~1 week)
5. Write the proposal — it's basically:
   - What: Ternary optical accelerator for AI inference
   - Why: 59x performance over current GPUs, low power, enables edge AI/robotics
   - How: Wavelength-division ternary logic (your papers explain this)
   - What you need: $50K-$100K for foundry tape-out and testing
   - What you've done: Simulation validation through 81x81, GDS ready
   - Attach your Zenodo papers as supporting documents

**Application template structure:**

```
1. Cover page (name, title, amount requested)
2. Project summary (1 page — what and why)
3. Project description (5-6 pages)
   a. The problem: AI inference is power-limited by electronic GPUs
   b. The innovation: Wavelength-encoded ternary logic
   c. Technical objectives: Fabricate prototype, validate performance
   d. Work plan: Foundry selection → tape-out → testing → benchmarking
   e. Commercial potential: Edge AI, robotics, data centers
4. Budget ($50K-$100K: foundry run + testing equipment + travel)
5. Bio/CV (your publications, GitHub, technical background)
```

**Timeline:** Applications accepted on a rolling basis. Review takes ~4-6
months. If awarded, money arrives ~2 months after that.

**Why this is worth it:** Even if it takes 6 months, you get free money AND
the NSF stamp of approval, which opens every other door.

---

## Path 3: CHIPS Act Funding

**What it is:** The CHIPS and Science Act (2022) allocated $52 billion for
domestic semiconductor R&D and manufacturing. Photonic chips qualify.

**What to do:**

1. Go to https://www.chips.gov
2. Look for "CHIPS R&D" funding opportunities
3. Also check NIST's Chips for America page for smaller grants
4. The application process is similar to NSF but more industry-focused

**Why it matters:** Your project is an American-designed photonic chip. That's
exactly what this funding was created for. Mention "domestic photonic
manufacturing" and "reducing dependence on foreign semiconductor supply
chains" in any application.

---

## Path 4: Cold Email to Industry Research Labs

**Who to contact (pick 1-2):**

- **NVIDIA Research** — photonic computing / optical interconnects group
- **Google DeepMind** — they designed TPUs, your systolic array is the same
  architecture in photonics
- **Intel Labs** — they have an active silicon photonics program
- **Lightmatter** — photonic AI accelerator startup, direct competitor/potential
  acquirer
- **Ayar Labs** — optical I/O company, could be interested in your WDM approach

**How to find the right person:**

1. Go to LinkedIn
2. Search "[Company] photonic computing researcher" or "optical accelerator"
3. Find someone with "Research Scientist" or "Principal Engineer" in their title
4. Send a connection request with this note (or email if you can find it):

---

Hi [Name],

I'm an independent researcher who designed a wavelength-division ternary
optical accelerator. It benchmarks at ~148 PFLOPS/chip for matrix multiply
(~59x B200) using three standard wavelengths for ternary encoding. Validated
in simulation through 6,561 processing elements, GDS layouts complete.

Published: https://doi.org/10.5281/zenodo.18501296
Design: https://github.com/jackwayne234/-wavelength-ternary-optical-computer

I'm looking for a fabrication partner. Would you be open to a brief
conversation?

— Chris Riner

---

**Timeline:** Some will never reply. Some will reply in a day. Send 5, expect
1-2 responses.

**Why this matters:** If a company funds your prototype, you skip the grant
process entirely and go straight to fabrication. And they have foundry
relationships already.

---

## Path 5: Crowdfunding / Community

**What:** GoFundMe, Kickstarter, or Experiment.com (specifically for science)

**Why it could work:** "Independent researcher designs optical chip 59x faster
than NVIDIA's best GPU, needs $50K to build the prototype" is a headline
people will share. Your GitHub and published papers give you credibility.

**What to do:**

1. Go to https://experiment.com (science-specific crowdfunding)
2. Create a project page with your GitHub, Zenodo DOIs, and a simple
   explanation of what the chip does and why it matters
3. Share on Reddit (r/hardware, r/photonics, r/MachineLearning, r/chipdesign),
   Hacker News, and Twitter/X

**Timeline:** Campaigns typically run 30-60 days.

---

## Priority Order

| Priority | Path | Effort | Timeline | Likelihood |
|----------|------|--------|----------|------------|
| 1 | AIM Photonics | One email | 1-2 weeks for response | High |
| 2 | Industry cold emails | 5 emails | Days to weeks | Medium |
| 3 | NSF SBIR Phase I | Application (~2 weeks writing) | 6-8 months | Medium |
| 4 | CHIPS Act | Application | 6-12 months | Medium |
| 5 | Crowdfunding | Campaign setup (~1 week) | 1-2 months | Variable |

**Do #1 this week. Do #2 this week. Start #3 this month. The rest in parallel.**

---

## Administrative Setup Checklist

If you don't have these yet, get them in order:

- [ ] Virginia sole proprietorship or LLC (https://www.scc.virginia.gov, ~$100)
- [ ] EIN number from IRS (free, instant online: https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online)
- [ ] DUNS number (free: https://www.dnb.com/duns-number.html)
- [ ] SAM.gov registration (free, required for federal grants: https://sam.gov)
- [ ] ORCID (free, links your publications: https://orcid.org)

These take a few days total and unlock all federal funding programs.

---

## Your Elevator Pitch

Memorize this. Use it in emails, calls, and applications:

> "I designed an optical AI accelerator that uses wavelength-encoded ternary
> logic to achieve 59x the matrix multiply performance of NVIDIA's B200 GPU.
> The design is validated in simulation, GDS layouts are complete, and papers
> are published. I need a fabrication partner or $50K for a prototype run."

That's it. Four sentences. Everything else is details.

---

*Last updated: February 7, 2026*
