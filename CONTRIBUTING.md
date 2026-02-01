# Contributing to Wavelength-Division Ternary Optical Computer

Thank you for your interest in contributing to this open source research project! This document provides guidelines for contributing to help make the process smooth and effective for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Workflow](#development-workflow)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Licensing](#licensing)
- [Questions?](#questions)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive criticism
- Accept responsibility and apologize when mistakes happen

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/-wavelength-ternary-optical-computer.git
   cd -wavelength-ternary-optical-computer
   ```
3. **Set up the development environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Create a branch** for your contribution:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, please:
- Check if the issue already exists
- Use the latest version of the code
- Collect information about the bug (error messages, steps to reproduce)

**Submit a bug report** by opening an issue with:
- A clear, descriptive title
- Steps to reproduce the behavior
- Expected vs actual behavior
- Your environment (OS, Python version, hardware specs if relevant)
- Any error messages or logs

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:
- Use a clear, descriptive title
- Provide a detailed description of the proposed enhancement
- Explain why this enhancement would be useful
- List any potential drawbacks or challenges

### Contributing Code

We welcome contributions in these areas:

#### Hardware
- 3D print improvements and optimizations
- Optical alignment techniques and tips
- Alternative component suggestions
- Assembly documentation improvements
- Test results from hardware builds

#### Software
- Simulation optimizations
- New simulation scripts
- Firmware improvements
- Analysis and visualization tools
- Bug fixes

#### Theory & Research
- Mathematical analysis
- Alternative architectures
- Literature reviews
- Peer review of methodology

#### Documentation
- Better explanations and tutorials
- Translations to other languages
- Video demonstrations
- Educational materials

## Development Workflow

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/description
   ```

2. **Make your changes** following our style guidelines

3. **Test your changes**:
   ```bash
   # Run tests
   pytest
   
   # Check code style
   ruff check .
   ruff format .
   ```

4. **Commit your changes** with a clear message

5. **Push to your fork**:
   ```bash
   git push origin feature/description
   ```

6. **Open a Pull Request** against the `main` branch

## Style Guidelines

### Python Code

- Follow [PEP 8](https://pep8.org/)
- Use 4 spaces for indentation
- Maximum line length: 100 characters
- Use type hints where appropriate
- Write docstrings for functions and classes

Example:
```python
def calculate_transmission(flux: np.ndarray, incident: float) -> float:
    """
    Calculate transmission efficiency.
    
    Args:
        flux: Measured flux array
        incident: Incident power
        
    Returns:
        Transmission efficiency as a float
    """
    return np.mean(flux) / incident
```

### Arduino/C++ Code

- Use clear, descriptive variable names
- Comment complex logic
- Follow the existing code style
- Keep functions focused and modular

### Documentation

- Use Markdown for documentation
- Include code examples where helpful
- Keep language clear and accessible
- Update the README if adding major features

### Hardware Designs

- Document all parameters clearly
- Include units in variable names (e.g., `width_um`)
- Provide clear assembly instructions
- Include safety warnings where appropriate

## Commit Messages

Write clear, meaningful commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add ring resonator simulation for 1550nm

- Implements ring resonator selector logic
- Adds visualization of resonance peaks
- Includes test coverage

Fixes #123
```

## Pull Request Process

1. **Update the README.md** with details of changes if applicable
2. **Update documentation** to reflect any API or interface changes
3. **Ensure all tests pass** and code meets style guidelines
4. **Fill out the PR template** with:
   - Description of changes
   - Motivation for changes
   - Testing performed
   - Screenshots (if applicable)
5. **Request review** from maintainers
6. **Address review feedback** promptly

### PR Review Criteria

- Code follows style guidelines
- Tests pass and coverage is adequate
- Documentation is updated
- Commit messages are clear
- No breaking changes without discussion

## Licensing

By contributing to this project, you agree that your contributions will be licensed under:

- **Code**: [MIT License](LICENSE)
- **Documentation**: [CC BY 4.0](LICENSE-CC-BY-4.0)
- **Hardware Designs**: [CERN OHL](LICENSE-CERN-OHL)

You retain copyright to your contributions, but grant the project the rights to use them under these licenses.

### Contributor License Agreement

By submitting a pull request, you certify that:

1. You have the right to submit the contribution under the specified licenses
2. The contribution is your original work or you have permission to submit it
3. You understand the contribution will be publicly available under open source licenses

## Questions?

- **Technical questions**: Open an issue with the "question" label
- **General discussion**: Use GitHub Discussions
- **Direct contact**: chrisriner45@gmail.com

## Recognition

Contributors will be recognized in our README and future publications. We believe in giving credit where credit is due!

Thank you for helping advance open source optical computing research!

---

*This project is part of the Wavelength-Division Ternary Optical Computer research.*
*DOI: 10.5281/zenodo.18437600*
