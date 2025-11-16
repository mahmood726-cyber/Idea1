# Contributing to CNMA Platform

Thank you for your interest in contributing to the Component Network Meta-Analysis Platform!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR-USERNAME/Idea1.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Install dependencies: `pip install -r requirements.txt`
5. Install dev dependencies: `pip install -e ".[dev]"`

## Development Workflow

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes (NumPy style)
- Maximum line length: 100 characters

Format code with:
```bash
black cnma_platform/ tests/
```

Lint with:
```bash
ruff check cnma_platform/ tests/
```

### Testing

Run tests before submitting:
```bash
pytest tests/ -v --cov=cnma_platform
```

Add tests for new features in the `tests/` directory.

### Documentation

- Update README.md if adding major features
- Add docstrings following NumPy documentation style
- Update examples if changing APIs

### Commit Messages

Use clear, descriptive commit messages:
```
Add interaction model for component synergies

- Implement pairwise interaction terms
- Add get_interaction_effects() method
- Include tests and example
```

## Types of Contributions

### Bug Reports

Include:
- Python version
- Package versions (from `pip freeze`)
- Minimal reproducible example
- Expected vs actual behavior

### Feature Requests

Describe:
- Use case and motivation
- Proposed API/interface
- Relevant literature/methodology

### Code Contributions

1. Check existing issues and PRs to avoid duplication
2. Discuss major changes in an issue first
3. Write tests for new features
4. Update documentation
5. Ensure all tests pass
6. Submit pull request

## Areas for Contribution

### High Priority

- Additional CNMA model variants
- More example datasets
- Performance optimization
- Documentation improvements
- Tutorial notebooks

### Statistical Methods

- Alternative priors
- Model diagnostics
- Sensitivity analyses
- Meta-regression extensions

### NLP Enhancements

- Pre-trained component extractors
- Multi-language support
- Improved standardization
- Active learning for component labeling

### Visualization

- Interactive plots with Plotly
- Dashboard/web interface
- Additional plot types
- Customization options

### Infrastructure

- Continuous integration
- Performance benchmarks
- Code coverage improvements
- Type checking with mypy

## Review Process

1. Automated tests must pass
2. Code review by maintainer(s)
3. Documentation check
4. Merge to main branch

## Questions?

Open an issue or discussion on GitHub.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
