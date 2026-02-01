# Research Literature Search Tool

A unified search interface for finding academic literature across multiple repositories.

**Live Demo:** https://research-search-tool.onrender.com (deployed on Render.com free tier)

## Overview

This web application provides a single search interface to query three major academic databases simultaneously:
- **arXiv** - Open-access preprints (physics, CS, math)
- **IEEE Xplore** - Engineering and technology papers
- **Zenodo** - Open research data and publications (CERN repository)

## Features

- ✅ Single search interface
- ✅ Results from 3 major repositories
- ✅ Direct links to papers
- ✅ No login required
- ✅ Mobile-friendly interface
- ✅ **FREE hosting** on Render.com

## Quick Start

### Option 1: Use the Live Demo
Visit: https://research-search-tool.onrender.com

*Note: Free tier sleeps after 15 min inactivity. First load may take 30 seconds to wake up.*

### Option 2: Run Locally
```bash
git clone https://github.com/jackwayne234/-wavelength-ternary-optical-computer.git
cd -wavelength-ternary-optical-computer/tools/research_search
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000 in your browser.

### Option 3: Deploy Your Own (Free)
See [DEPLOY.md](DEPLOY.md) for step-by-step instructions to deploy on Render.com.

## How to Use

1. **Enter search terms** in the search bar
   - Example: `"optical computing ternary logic"`
   - Example: `"wavelength division multiplexing"`
   - Example: `"radix economy photonics"`
2. **Review results** from all three sources
3. **Click on papers** to access full text (when available)

## Search Tips

### Effective Keywords
- Use technical terms: "photonic integrated circuits", "sum frequency generation"
- Include author names: "Smith optical computing"
- Try synonyms: "trit" vs "ternary digit"

### For Ternary Optical Computing Research
Try these searches:
- `"balanced ternary" optical`
- `"radix economy" computing`
- `Setun computer optical`
- `wavelength multiplexing logic`
- `photonic logic gates`
- `optical arithmetic ternary`

## Data Sources

| Source | Coverage | Access | API |
|--------|----------|--------|-----|
| **arXiv** | Physics, CS, math, engineering | Free, open | Public |
| **IEEE Xplore** | Engineering, electronics | Mixed (some free) | Requires key |
| **Zenodo** | All research fields | Free, open (CERN) | REST API |

## Technical Stack

- **Backend:** Python/Flask
- **Frontend:** HTML/CSS/JavaScript
- **APIs:** arXiv API, IEEE Xplore API, Zenodo API
- **Hosting:** Render.com (free tier)

## Architecture

```
User Query → Flask App → Parallel API Calls → Aggregated Results → HTML Display
                ↓              ↓                    ↓
            arXiv API    IEEE Xplore API      Zenodo API
```

## Files

- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies
- `templates/index.html` - Web interface
- `static/style.css` - Styling
- `render.yaml` - Render deployment configuration
- `DEPLOY.md` - Deployment instructions

## Deployment

### Render.com (Free - Recommended)

**Cost:** $0/month (free tier)  
**Limitation:** Sleeps after 15 min inactivity (wakes automatically)  
**Perfect for:** Research tools, low-traffic apps

See [DEPLOY.md](DEPLOY.md) for detailed instructions.

### Alternative Platforms

**PythonAnywhere** (Free, always-on but limited)  
**Heroku** (Free tier available)  
**Self-host** (Raspberry Pi, old computer)

## Limitations

- Subject to each repository's API rate limits
- Some IEEE papers require institutional access
- Free tier sleeps after inactivity (30-sec wake delay)
- Search syntax varies between sources

## Contributing

**Created by:** Christopher Riner  
**Part of:** Wavelength-Division Ternary Optical Computer Project

**Feedback welcome:**
- Feature requests
- Bug reports  
- Additional data sources
- UI improvements

Contact: chrisriner45@gmail.com

## Future Enhancements

- [ ] Add Google Scholar integration
- [ ] Export results to BibTeX/EndNote
- [ ] Save search history
- [ ] Advanced filters (date, author, subject)
- [ ] Citation count display
- [ ] Full-text preview

## Related Resources

- **Main Project:** https://github.com/jackwayne234/-wavelength-ternary-optical-computer
- **Paper (Zenodo):** https://doi.org/10.5281/zenodo.18437600
- **arXiv:** https://arxiv.org/
- **IEEE Xplore:** https://ieeexplore.ieee.org/
- **Zenodo:** https://zenodo.org/

## License

MIT License - See [LICENSE](../../LICENSE)

Data sources retain their respective terms:
- arXiv: Open access
- IEEE: Mixed access
- Zenodo: Open access (Creative Commons)

---

**Created:** February 2026  
**Maintainer:** Christopher Riner  
**Contact:** chrisriner45@gmail.com  
**Hosted on:** Render.com (Free Tier)
