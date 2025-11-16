# Component Network Meta-Analysis (CNMA) Platform

A comprehensive Python platform for Component Network Meta-Analysis, implementing state-of-the-art methods for analyzing multi-component interventions in systematic reviews and meta-analyses.

## Features

### Core Statistical Models
- **Additive CNMA Model**: Assumes component effects combine additively
- **Interaction CNMA Model**: Models synergistic/antagonistic effects between components (planned future work)

### Automated Component Identification
- NLP-based extraction of intervention components from text descriptions
- Intelligent component standardization and matching
- Support for complex multi-component interventions

### Advanced Analytics
- Bayesian inference using PyMC
- Frequentist composite likelihood estimation
- Model comparison and selection (DIC, WAIC, LOO)
- Component importance ranking
- Intervention ranking and clustering

### Visualization
- Interactive network plots
- Component effect forest plots
- Intervention comparison matrices
- SUCRA plots and rankograms

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from cnma_platform import CNMAAnalysis
from cnma_platform.data import load_example_data

# Load data
data = load_example_data("smoking_cessation")

# Run additive CNMA
analysis = CNMAAnalysis(
    data=data,
    model_type="additive"
)

# Fit model
results = analysis.fit(
    n_samples=2000,
    n_warmup=1000,
    n_chains=4
)

# Visualize results
results.plot_component_effects()
results.plot_network()
results.summary()
```

## Methodology

### Component Network Meta-Analysis

CNMA extends standard network meta-analysis (NMA) to interventions with multiple components. Instead of treating each unique combination as a separate intervention, CNMA:

1. **Decomposes interventions** into their constituent components
2. **Estimates component-level effects** using all available evidence
3. **Predicts effects** of new component combinations not directly studied

### Models Implemented

#### 1. Additive Model
```
θ_jk = Σ β_c × I(component c in intervention k but not j)
```

#### 2. Interaction Model (Planned)
```
θ_jk = Σ β_c × I_c + Σ γ_cd × I_c × I_d
```
Models synergistic or antagonistic interactions between components.

### References

- **Welton NJ, Caldwell DM, Adamopoulos E, Vedhara K. (2009)**. Mixed treatment comparison meta-analysis of complex interventions: psychological interventions in coronary heart disease. *American Journal of Epidemiology*, 169(9):1158-1165.
- **Dias S, Sutton AJ, Ades AE, Welton NJ. (2013)**. Evidence synthesis for decision making 2: a generalized linear modeling framework for pairwise and network meta-analysis of randomized controlled trials. *Medical Decision Making*, 33(5):607-617.
- **Rücker G, Petropoulou M, Schwarzer G. (2020)**. Component network meta-analysis compared to a matching method in a disconnected network: a case study. *Biometrical Journal*, 62(2):447-461.

## Project Structure

```
cnma_platform/
├── models/           # Statistical models (additive, interaction, composite likelihood)
├── nlp/             # Component extraction and NLP utilities
├── data/            # Data loading, validation, network construction
├── inference/       # Bayesian and frequentist inference engines
├── visualization/   # Plotting and visualization tools
├── utils/           # Helper functions and utilities
└── examples/        # Example datasets and analyses
```

## Examples

See the `examples/` directory for comprehensive tutorials:
- `01_basic_additive_cnma.py` - Basic additive model
- `02_interaction_model.py` - Modeling component interactions (planned)
- `03_composite_likelihood.py` - Composite likelihood approach (planned)
- `04_automated_component_extraction.py` - Automated component identification

## Requirements

- Python >= 3.9
- NumPy, SciPy, Pandas
- PyMC >= 5.0 (Bayesian inference)
- scikit-learn (component extraction)
- NetworkX (network analysis)
- Matplotlib, Seaborn, Plotly (visualization)
- spaCy (NLP)

## License

MIT License

## Citation

If you use this platform in your research, please cite:

```bibtex
@software{cnma_platform,
  title={Component Network Meta-Analysis Platform},
  author={},
  year={2025},
  url={https://github.com/mahmood726-cyber/Idea1}
}
```

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## Support

For questions and support, please open an issue on GitHub.
