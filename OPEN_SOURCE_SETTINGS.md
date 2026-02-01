# Open Source Repository Settings Guide

This document outlines the recommended GitHub repository settings to ensure the Wavelength-Division Ternary Optical Computer project remains properly open source and accessible to the community.

## Repository Visibility

**Status**: ✅ Public (Required for open source)

The repository must remain public to fulfill open source principles. This allows:
- Anyone to view, fork, and contribute
- Search engines to index the content
- Academic citations to link directly to the code
- Other researchers to build upon your work

## Essential Settings to Configure

### 1. Repository Details

**Location**: Settings → General → Repository Details

- [ ] **Description**: "Building a ternary computer using light instead of transistors"
- [ ] **Website**: https://doi.org/10.5281/zenodo.18437600
- [ ] **Topics**: Add relevant tags:
  - `optical-computing`
  - `ternary-logic`
  - `photonics`
  - `open-hardware`
  - `meep-fdtd`
  - `research`
  - `open-science`

### 2. Social Preview

**Location**: Settings → General → Social Preview

Upload an image (1280×640px recommended) that will display when the repo is shared on social media. Consider using:
- The architecture diagram from your paper
- A photo of the prototype
- A visualization of the ternary logic concept

### 3. Features

**Location**: Settings → General → Features

Enable these features:
- [x] **Issues** - For bug reports and feature requests
- [x] **Discussions** - For community Q&A and general discussion
- [x] **Projects** - For tracking development tasks
- [x] **Wiki** - Optional, for extended documentation
- [ ] **Sponsorships** - If you want to accept donations (optional)

### 4. Pull Requests

**Location**: Settings → General → Pull Requests

- [x] **Allow merge commits** - Standard merge
- [x] **Allow squash merging** - Clean history for small changes
- [x] **Allow rebase merging** - Linear history option
- [x] **Automatically delete head branches** - Keep repo clean

### 5. Branch Protection Rules

**Location**: Settings → Branches → Add rule

Protect the `main` branch with these settings:
- [x] **Require a pull request before merging**
  - [x] Require approvals (1 minimum)
  - [x] Dismiss stale PR approvals when new commits are pushed
  - [x] Require review from code owners (if applicable)
- [x] **Require status checks to pass before merging**
  - [ ] Require branches to be up to date before merging
- [ ] **Require conversation resolution before merging**
- [x] **Require signed commits** (recommended for research integrity)
- [x] **Include administrators** (rules apply to everyone)
- [x] **Restrict pushes that create files larger than 100MB**

### 6. Security Settings

**Location**: Settings → Security → Security Overview

- [x] **Private vulnerability reporting** - Allow security researchers to report issues privately
- [x] **Dependabot alerts** - Get notified of vulnerable dependencies
- [x] **Dependabot security updates** - Automatic PRs for security fixes

### 7. Access Settings

**Location**: Settings → Access

**Collaborators**:
- Add trusted collaborators with appropriate permissions:
  - **Admin**: Full control (you)
  - **Maintain**: Can push to protected branches
  - **Write**: Can push and create PRs
  - **Triage**: Can manage issues and PRs
  - **Read**: Can view and fork

### 8. GitHub Pages (Optional)

**Location**: Settings → Pages

If you want a project website:
- Source: Deploy from a branch → `main` → `/docs` folder
- This creates a website at: `https://jackwayne234.github.io/-wavelength-ternary-optical-computer`

## Community Health Files

Ensure these files exist in the repository root (already created):

- ✅ `LICENSE` - MIT License for code
- ✅ `LICENSE-CC-BY-4.0` - CC BY 4.0 for documentation
- ✅ `LICENSE-CERN-OHL` - CERN OHL for hardware
- ✅ `CONTRIBUTING.md` - Contribution guidelines
- ✅ `CODE_OF_CONDUCT.md` - Community standards
- ✅ `README.md` - Project overview
- ✅ `.gitignore` - Files to exclude from version control

## Issue Templates

**Location**: Settings → General → Features → Issues → Set up templates

Create these templates in `.github/ISSUE_TEMPLATE/`:

### Bug Report Template
```markdown
---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear description of what you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python version: [e.g. 3.12]
 - Hardware phase: [e.g. Phase 1, Phase 2]
 - Commit hash: [e.g. abc123]

**Additional context**
Add any other context about the problem.
```

### Feature Request Template
```markdown
---
name: Feature request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
A clear description of any alternative solutions or features.

**Additional context**
Add any other context or screenshots about the feature request.
```

## Pull Request Template

Create `.github/pull_request_template.md`:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Hardware design change
- [ ] Simulation improvement
- [ ] Breaking change

## Testing
Describe the testing you performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] License headers added to new files
- [ ] README updated if needed

## Related Issues
Fixes #(issue number)
```

## Automation (Optional)

### GitHub Actions

Consider adding workflows in `.github/workflows/`:

1. **CI/CD Pipeline** - Run tests on PRs
2. **Code Quality** - Lint and format checks
3. **Documentation** - Build and deploy docs

Example `.github/workflows/ci.yml`:
```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Run tests
      run: pytest
    - name: Check code style
      run: |
        pip install ruff
        ruff check .
```

## Archival & Preservation

### Zenodo Integration

Already configured! The repository is linked to Zenodo DOI: 10.5281/zenodo.18437600

Each GitHub release will automatically create a new Zenodo version.

### Software Heritage

Software Heritage automatically archives public GitHub repositories. Your code is already being preserved for future generations!

## Monitoring & Analytics

**Location**: Insights tab

Monitor:
- Traffic (clones, views)
- Contributors
- Community (new issues/PRs)
- Dependency graph
- Code frequency

## Best Practices Checklist

- [ ] Repository is public
- [ ] Clear description and topics set
- [ ] All 3 LICENSE files present
- [ ] CONTRIBUTING.md exists
- [ ] CODE_OF_CONDUCT.md exists
- [ ] README is comprehensive
- [ ] Branch protection rules configured
- [ ] Issue templates created
- [ ] PR template created
- [ ] Dependabot enabled
- [ ] Vulnerability reporting enabled
- [ ] Social preview image set
- [ ] Zenodo integration active

## Questions?

For questions about repository settings, contact: chrisriner45@gmail.com

---

*This guide ensures the Wavelength-Division Ternary Optical Computer project follows open source best practices and remains accessible to the global research community.*
