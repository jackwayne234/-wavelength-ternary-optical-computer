# Build Documentation System

This directory contains the day-to-day engineering logs, test results, and build progress for the Wavelength-Division Ternary Optical Computer project.

## Documentation Philosophy

**SMEAC** = For planning missions and presenting to stakeholders  
**Engineering Logs** = For documenting the messy reality of building hardware

## Directory Structure

```
docs/
├── build_logs/           # Daily/weekly build progress
│   ├── phase1/
│   │   ├── 2026-02-01_laser_alignment.md
│   │   ├── 2026-02-03_sensor_calibration.md
│   │   └── photos/
│   ├── phase2/
│   └── phase3/
├── test_results/         # Formal test data and analysis
│   ├── phase1/
│   │   ├── test_001_power_on.md
│   │   ├── test_002_logic_verification.md
│   │   └── data/
│   ├── phase2/
│   └── phase3/
├── lessons_learned/      # What went wrong and how we fixed it
│   ├── fabrication_mistakes.md
│   ├── optical_alignment_tips.md
│   └── component_selection.md
├── decisions/            # Design decision records (ADRs)
│   ├── 001_wavelength_selection.md
│   ├── 002_sensor_choice.md
│   └── 003_mixer_design.md
└── media/                # Photos, videos, diagrams
    ├── phase1/
    ├── phase2/
    └── phase3/
```

## Documentation Templates

### Build Log Entry Template

```markdown
# Build Log: [Date] - [Short Description]

**Phase:** [1/2/3/4]  
**Builder:** [Name]  
**Duration:** [Hours spent]  
**Status:** [In Progress / Complete / Blocked]

## Objectives
- [ ] Objective 1
- [ ] Objective 2

## What Was Built
Describe what you physically built or modified today.

## Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Test 1 | X | Y | ✅/❌ |

## Issues Encountered
1. **Issue:** Description
   - **Impact:** How it affected the build
   - **Solution:** How you fixed it (or plan to)
   - **Lesson:** What to remember for next time

## Photos/Videos
- [Link to photo 1]
- [Link to video]

## Next Steps
- [ ] What to do next
- [ ] Blockers to resolve

## Resources Used
- Components consumed
- Tools used
- References consulted

## Notes & Observations
Any other thoughts, ideas, or observations.

---
**Tags:** #phase1 #optical-alignment #laser #esp32
```

### Test Results Template

```markdown
# Test Report: [Test ID] - [Test Name]

**Date:** [YYYY-MM-DD]  
**Phase:** [1/2/3/4]  
**Tester:** [Name]  
**Test Environment:** [Temperature, humidity, conditions]

## Purpose
What are we testing and why?

## Setup
- Equipment used
- Configuration
- Calibration status

## Procedure
Step-by-step test procedure.

## Results
### Quantitative Data
| Parameter | Expected | Measured | Unit | Status |
|-----------|----------|----------|------|--------|
| Param 1 | X | Y | Unit | ✅/❌ |

### Qualitative Observations
- Visual observations
- Audio observations
- Behavioral notes

## Analysis
Interpretation of results.

## Conclusions
- Pass/Fail status
- Whether we can proceed
- Recommendations

## Raw Data
Links to CSV files, oscilloscope captures, logs, etc.

---
**Test ID:** TEST-PH1-001  
**Related Build Log:** [Link to build log]
```

### Decision Record Template (ADR)

```markdown
# ADR [Number]: [Decision Title]

**Date:** [YYYY-MM-DD]  
**Status:** [Proposed / Accepted / Deprecated / Superseded]  
**Phase:** [1/2/3/4]

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing or have agreed to implement?

## Consequences
What becomes easier or more difficult to do and any risks introduced by the change that will need to be mitigated.

## Alternatives Considered
- Alternative 1: Why rejected
- Alternative 2: Why rejected

## References
- Links to research
- Related issues
- External sources

---
**Decision ID:** ADR-001  
**Supersedes:** [Previous ADR if applicable]  
**Superseded By:** [Newer ADR if applicable]
```

## Best Practices

### 1. **Document in Real-Time**
- Don't wait until the end of the day
- Take photos as you go
- Write down measurements immediately
- Note problems while they're happening

### 2. **Be Honest About Failures**
- Failed tests are valuable data
- Document what didn't work
- Share mistakes so others don't repeat them
- "This didn't work because..." is gold

### 3. **Use Version Control**
- Commit build logs to git
- Tag major milestones
- Branch for experimental approaches
- Never lose work

### 4. **Make It Searchable**
- Use consistent tags
- Cross-reference related documents
- Include dates in filenames
- Use descriptive titles

### 5. **Include Context**
- Why did you make this choice?
- What were you trying to achieve?
- What constraints were you working under?
- Future builders need the full picture

### 6. **Media is Critical**
- Photos of every step
- Videos of tests running
- Screenshots of data
- Diagrams of setups

## Naming Conventions

### Files
- `YYYY-MM-DD_brief_description.md` for logs
- `TEST-[PHASE]-[NUMBER]_test_name.md` for tests
- `ADR-[NUMBER]_decision_title.md` for decisions
- `PH[X]_[description]_[NNN].jpg` for photos

### Directories
- `phase1/`, `phase2/`, etc. for phase-specific docs
- `photos/`, `videos/`, `data/` for media
- Date-based subdirectories if volume is high

## When to Use SMEAC vs Build Logs

| Scenario | Use SMEAC | Use Build Log |
|----------|-----------|---------------|
| Planning a phase | ✅ | ❌ |
| Presenting to stakeholders | ✅ | ❌ |
| Grant applications | ✅ | ❌ |
| Daily build progress | ❌ | ✅ |
| Testing a component | ❌ | ✅ |
| Debugging a problem | ❌ | ✅ |
| Design decisions | ❌ | ✅ (ADR) |
| Lessons learned | ❌ | ✅ |
| Final reports | ✅ | ❌ |

## Integration with GitHub

### Issues for Problems
- Create GitHub issues for blockers
- Link to build logs
- Track resolution
- Close when fixed

### Pull Requests for Changes
- Document changes in PR description
- Reference build logs
- Include test results
- Before/after photos

### Discussions for Questions
- Use GitHub Discussions for Q&A
- Link to relevant documentation
- Build community knowledge base

## Example Workflow

1. **Morning Planning** (5 min)
   - Review yesterday's log
   - Check open issues
   - Plan today's objectives

2. **During Build** (Continuous)
   - Take photos every 30 min
   - Note measurements immediately
   - Record problems as they happen
   - Save data files

3. **End of Session** (15 min)
   - Write build log entry
   - Upload photos
   - Update test results
   - Create issues for blockers
   - Commit everything

4. **Weekly Review** (30 min)
   - Review week's progress
   - Update project status
   - Plan next week
   - Share highlights

## Tools

### Recommended
- **Markdown**: For all documentation
- **Git**: For version control
- **GitHub**: For hosting and collaboration
- **Phone/Camera**: For photos/videos
- **Spreadsheets**: For structured data
- **Oscilloscope/Logic Analyzer**: For test data capture

### Optional
- **CAD Software**: For design documentation
- **Simulation Tools**: For virtual testing
- **Video Editing**: For build montages
- **Drawing Tools**: For diagrams

## Remember

**The goal is to enable someone else (or future you) to:**
1. Understand what was built
2. Reproduce the results
3. Learn from your mistakes
4. Improve upon your work
5. Build something new based on your foundation

**Open source hardware lives or dies by its documentation.**

---

*This system ensures your ternary optical computer research is fully documented, reproducible, and accessible to the global open source community.*
