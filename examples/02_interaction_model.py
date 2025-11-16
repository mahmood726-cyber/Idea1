"""
Example 2: Interaction CNMA Model

This example demonstrates:
- Fitting an interaction model to detect component synergies
- Comparing additive vs interaction models
- Identifying significant interactions
"""

import numpy as np
import matplotlib.pyplot as plt
from cnma_platform import CNMAAnalysis
from cnma_platform.data import load_example_data

print("=" * 70)
print("EXAMPLE 2: Interaction CNMA Model")
print("=" * 70)

# Load data
data = load_example_data("smoking_cessation")
print(f"\nLoaded data: {len(data)} observations")

# Fit ADDITIVE model first (for comparison)
print("\n" + "=" * 70)
print("FITTING ADDITIVE MODEL (BASELINE)")
print("=" * 70)

additive = CNMAAnalysis(
    data=data,
    model_type="additive",
    likelihood="bayesian",
    outcome_type="continuous"
)

additive.set_components(component_col="components")
additive.fit(n_samples=1000, n_warmup=500, n_chains=2)

additive_effects = additive.get_component_effects()
print("\nAdditive Model - Component Effects:")
print(additive_effects[['component', 'mean', 'sd', 'q2.5', 'q97.5']])

# Fit INTERACTION model
print("\n" + "=" * 70)
print("FITTING INTERACTION MODEL")
print("=" * 70)

interaction = CNMAAnalysis(
    data=data,
    model_type="interaction",
    likelihood="bayesian",
    outcome_type="continuous",
    max_interaction_order=2  # Pairwise interactions only
)

interaction.set_components(component_col="components")
interaction.fit(n_samples=1000, n_warmup=500, n_chains=2)

# Get main effects
main_effects = interaction.get_component_effects()
print("\nInteraction Model - Main Effects:")
print(main_effects[['component', 'mean', 'sd', 'q2.5', 'q97.5']])

# Get interaction effects
interaction_effects = interaction.get_interaction_effects()
print("\nInteraction Effects:")
print(interaction_effects[['interaction', 'mean', 'sd', 'q2.5', 'q97.5', 'prob_positive']])

# Identify significant interactions
print("\n" + "=" * 70)
print("SIGNIFICANT INTERACTIONS")
print("=" * 70)

# Significant if 95% CrI doesn't include 0
significant = interaction_effects[
    ~((interaction_effects['q2.5'] < 0) & (interaction_effects['q97.5'] > 0))
]

if len(significant) > 0:
    print(f"\nFound {len(significant)} significant interactions:")
    for _, row in significant.iterrows():
        direction = "synergistic" if row['mean'] > 0 else "antagonistic"
        print(f"\n  {row['interaction']}")
        print(f"    Effect: {row['mean']:.3f} (95% CrI: [{row['q2.5']:.3f}, {row['q97.5']:.3f}])")
        print(f"    Interpretation: {direction} interaction")
else:
    print("\nNo significant interactions detected at 95% credibility level")

# Compare predictions
print("\n" + "=" * 70)
print("COMPARING PREDICTIONS: Additive vs Interaction")
print("=" * 70)

test_comparisons = [
    ('Control', 'NRT'),
    ('Control', 'Counseling'),
    ('Control', 'NRT + Counseling'),
]

print("\nPredicted Effects:")
print(f"{'Comparison':<30} {'Additive':<15} {'Interaction':<15} {'Difference':<15}")
print("-" * 75)

for t1, t2 in test_comparisons:
    try:
        pred_add = additive.predict(t1, t2)
        pred_int = interaction.predict(t1, t2)

        diff = pred_int['mean'] - pred_add['mean']

        print(f"{t2 + ' vs ' + t1:<30} "
              f"{pred_add['mean']:>7.3f} ({pred_add['sd']:>5.3f})  "
              f"{pred_int['mean']:>7.3f} ({pred_int['sd']:>5.3f})  "
              f"{diff:>7.3f}")
    except Exception as e:
        print(f"{t2 + ' vs ' + t1:<30} Error: {e}")

# Model comparison using DIC/WAIC
print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)

try:
    import arviz as az

    additive_trace = additive.model.trace
    interaction_trace = interaction.model.trace

    # Compute model comparison metrics
    comparison = az.compare({
        'additive': additive_trace,
        'interaction': interaction_trace
    })

    print("\nModel Comparison (lower is better):")
    print(comparison)

    best_model = comparison.index[0]
    print(f"\nBest model: {best_model}")

except Exception as e:
    print(f"Could not perform model comparison: {e}")

# Visualization
print("\n" + "=" * 70)
print("GENERATING VISUALIZATIONS")
print("=" * 70)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1. Compare main effects
axes[0, 0].errorbar(
    additive_effects['mean'],
    range(len(additive_effects)),
    xerr=[additive_effects['mean'] - additive_effects['q2.5'],
          additive_effects['q97.5'] - additive_effects['mean']],
    fmt='o', label='Additive', alpha=0.7
)
axes[0, 0].errorbar(
    main_effects['mean'],
    range(len(main_effects)),
    xerr=[main_effects['mean'] - main_effects['q2.5'],
          main_effects['q97.5'] - main_effects['mean']],
    fmt='s', label='Interaction (main)', alpha=0.7
)
axes[0, 0].set_yticks(range(len(additive_effects)))
axes[0, 0].set_yticklabels(additive_effects['component'])
axes[0, 0].axvline(0, color='red', linestyle='--', alpha=0.5)
axes[0, 0].set_xlabel('Effect Size')
axes[0, 0].set_title('Main Effects: Additive vs Interaction Model')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)

# 2. Interaction effects
interaction.plot_interaction_effects(ax=axes[0, 1])

# 3. Component effects from interaction model
interaction.plot_component_effects(ax=axes[1, 0])

# 4. Network
interaction.plot_network(ax=axes[1, 1])

plt.tight_layout()
plt.savefig('examples/output_02_interaction_model.png', dpi=300, bbox_inches='tight')
print("\nVisualization saved as 'examples/output_02_interaction_model.png'")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE!")
print("=" * 70)
