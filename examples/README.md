# CNMA Platform Examples

This directory contains comprehensive examples demonstrating the capabilities of the Component Network Meta-Analysis Platform.

## Examples Overview

### 01_basic_additive_cnma.py
**Basic Additive CNMA Analysis**

Demonstrates:
- Loading example datasets
- Setting up intervention components
- Fitting an additive CNMA model using Bayesian inference
- Extracting component effects with credible intervals
- Making predictions for new treatment combinations
- Visualizing results (network plots, forest plots, rankings)

**Run with:**
```bash
python examples/01_basic_additive_cnma.py
```

### 02_interaction_model.py
**Interaction CNMA Model**

Demonstrates:
- Fitting models with component interactions
- Detecting synergistic and antagonistic effects
- Comparing additive vs interaction models
- Identifying significant pairwise interactions
- Model selection using DIC/WAIC

**Run with:**
```bash
python examples/02_interaction_model.py
```

### 03_composite_likelihood.py
**Composite Likelihood Approach**

Demonstrates:
- Using composite likelihood for fast inference
- Avoiding within-study correlation assumptions
- Comparing computational efficiency with Bayesian MCMC
- Frequentist inference with valid standard errors
- When to use composite likelihood vs Bayesian

**Run with:**
```bash
python examples/03_composite_likelihood.py
```

### 04_automated_component_extraction.py
**Automated Component Extraction with NLP**

Demonstrates:
- Extracting intervention components from text descriptions
- Comparing extraction methods (keyword, TF-IDF, hybrid)
- Standardizing similar components
- Creating component matrices automatically
- Analyzing component co-occurrence
- End-to-end workflow from text to CNMA results

**Run with:**
```bash
python examples/04_automated_component_extraction.py
```

## Prerequisites

Install all requirements:
```bash
pip install -r requirements.txt
```

For NLP features:
```bash
pip install spacy sentence-transformers
python -m spacy download en_core_web_sm
```

## Example Datasets

The platform includes three built-in example datasets:

1. **smoking_cessation**: Multi-component smoking cessation interventions
   - Components: NRT, Counseling, Group Support, Self-help
   - ~40 studies, continuous outcome (log odds ratios)

2. **hypertension**: Blood pressure reduction interventions
   - Components: Diet, Exercise, Medication
   - ~30 studies, continuous outcome (mmHg reduction)

3. **depression**: Depression treatment interventions
   - Components: CBT, Medication, Exercise
   - ~25 studies, continuous outcome (standardized mean difference)

## Output

Each example generates:
- Console output with analysis results
- High-resolution visualization (PNG format)
- Statistical summaries and interpretations

Output files are saved as:
- `output_01_basic_cnma.png`
- `output_02_interaction_model.png`
- `output_03_composite_likelihood.png`
- `output_04_component_extraction.png`

## Running All Examples

To run all examples sequentially:

```bash
for script in examples/0*.py; do
    echo "Running $script..."
    python $script
    echo "---"
done
```

## Customization

Each example can be customized by modifying:
- Number of MCMC samples (`n_samples`, `n_warmup`, `n_chains`)
- Prior distributions (`prior_sd`, `heterogeneity_prior`)
- Component extraction parameters (`method`, `domain`, `similarity_threshold`)
- Visualization parameters (`figsize`, `layout`, `colors`)

## Support

For questions or issues with examples:
1. Check the main README.md for platform documentation
2. Review the API documentation in each module
3. Open an issue on GitHub

## Citation

If you use these examples in your research, please cite:

```bibtex
@software{cnma_platform,
  title={Component Network Meta-Analysis Platform},
  author={},
  year={2025},
  url={https://github.com/mahmood726-cyber/Idea1}
}
```
