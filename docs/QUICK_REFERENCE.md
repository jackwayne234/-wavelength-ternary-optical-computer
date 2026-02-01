# Quick Reference: Build Documentation

## I want to...

### Start a new build session
1. Create new file: `docs/build_logs/phase[1-4]/YYYY-MM-DD_brief_description.md`
2. Use template from `docs/README.md`
3. Fill in objectives, work performed, test results
4. Add photos to `docs/media/phase[1-4]/`
5. Commit to git

### Record a test
1. Create new file: `docs/test_results/phase[1-4]/TEST-PH[X]-[NNN]_test_name.md`
2. Use test template from `docs/README.md`
3. Include quantitative data tables
4. Link to raw data files
5. State clear pass/fail conclusion

### Document a design decision
1. Create new file: `docs/decisions/ADR-[NNN]_decision_title.md`
2. Use ADR template from `docs/README.md`
3. Explain context, decision, consequences
4. List alternatives considered
5. Update if decision changes

### Share lessons learned
1. Create new file: `docs/lessons_learned/topic_name.md`
2. Include what worked and what didn't
3. Add specific parameters and settings
4. Include cost analysis if relevant
5. Cross-reference related build logs

### Prepare a presentation
1. Use SMEAC format: `Phase[X]_Fiber_Benchtop/admin_logistics/presentation/`
2. For status updates, use build logs as source material
3. Extract key metrics from test results
4. Include photos from `docs/media/`

## File Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| Build Log | `YYYY-MM-DD_description.md` | `2026-02-01_initial_setup.md` |
| Test Result | `TEST-PH[X]-[NNN]_name.md` | `TEST-PH1-001_laser_power.md` |
| Decision | `ADR-[NNN]_title.md` | `ADR-001_wavelength_selection.md` |
| Lesson | `topic_name.md` | `3d_printing_optical_components.md` |
| Photo | `PH[X]_description_NNN.jpg` | `PH1_laser_alignment_001.jpg` |

## Tags for Searchability

Use these tags in build logs:
- `#phase1`, `#phase2`, `#phase3`, `#phase4`
- `#hardware-assembly`, `#optical-alignment`, `#testing`
- `#laser`, `#sensor`, `#esp32`, `#firmware`
- `#issue`, `#solution`, `#lesson-learned`
- `#day1`, `#week1`, etc.

## Daily Workflow

```bash
# 1. Pull latest changes
git pull origin main

# 2. Create today's build log
cp docs/templates/build_log_template.md docs/build_logs/phase1/2026-02-XX_today_work.md

# 3. Work on hardware, take photos

# 4. Update build log with progress

# 5. Add photos
cp ~/Photos/IMG_*.jpg docs/media/phase1/

# 6. Commit everything
git add docs/
git commit -m "Build log: [date] - [brief description]"
git push origin main
```

## Emergency: Something Broke!

1. **Document immediately** - Take photos before fixing
2. **Create issue** - GitHub issue for tracking
3. **Write lesson learned** - So others don't repeat it
4. **Update build log** - What went wrong, how fixed
5. **Share solution** - Help the community

## SMEAC vs Build Logs

| Use SMEAC When | Use Build Logs When |
|----------------|---------------------|
| Planning a phase | Actually building |
| Presenting to stakeholders | Debugging a problem |
| Writing grant proposals | Testing a component |
| Final reports | Daily progress |
| Mission briefings | Iterating on design |

## Key Locations

- **Templates:** `docs/README.md` (scroll to Templates section)
- **Current build:** `docs/build_logs/phase1/` (Phase 1 in progress)
- **Test data:** `docs/test_results/phase1/`
- **Photos:** `docs/media/phase1/`
- **Decisions:** `docs/decisions/`
- **Lessons:** `docs/lessons_learned/`
- **SMEAC plans:** `Phase[X]_*/admin_logistics/presentation/`

## Need Help?

- **Formatting:** See `docs/README.md` for templates
- **Examples:** See existing files in each directory
- **Questions:** Open a GitHub issue
- **Guidelines:** See `CONTRIBUTING.md`

---

**Remember:** Document for the person building this in 5 years (or yourself next week when you've forgotten the details!)
