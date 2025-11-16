"""
Example 1: Basic Additive CNMA Analysis

This example demonstrates:
- Loading example data
- Setting up components
- Fitting an additive CNMA model
- Extracting and visualizing results
"""

import numpy as np
import matplotlib.pyplot as plt
from cnma_platform import CNMAAnalysis
from cnma_platform.data import load_example_data

# Load example smoking cessation dataset
print("=" * 70)
print("EXAMPLE 1: Basic Additive CNMA")
print("=" * 70)

data = load_example_data("smoking_cessation")
print(f"\nLoaded {len(data)} observations from {data['study'].nunique()} studies")
print(f"Treatments: {data['treatment'].nunique()} unique treatments")

# Display sample data
print("\nSample data:")
print(data.head(10))

# Initialize CNMA analysis
analysis = CNMAAnalysis(
    data=data,
    model_type="additive",
    likelihood="bayesian",
    outcome_type="continuous",
    prior_sd=2.0
)

# Set components from data
analysis.set_components(component_col="components")

# Build and fit model
print("\nBuilding additive CNMA model...")
analysis.build_model()

print("\nFitting model using MCMC...")
print("This may take a few minutes...")

# Fit with reduced samples for faster execution
results = analysis.fit(
    n_samples=1000,
    n_warmup=500,
    n_chains=2
)

# View summary
print("\n" + "=" * 70)
print("MODEL RESULTS")
print("=" * 70)

summary = analysis.summary()
print("\nParameter Summary:")
print(summary)

# Get component effects
print("\n" + "=" * 70)
print("COMPONENT EFFECTS")
print("=" * 70)

component_effects = analysis.get_component_effects()
print("\nEstimated Component Effects:")
print(component_effects)

# Interpret results
print("\nInterpretation:")
for _, row in component_effects.iterrows():
    comp = row['component']
    mean = row['mean']
    ci_lower = row['q2.5']
    ci_upper = row['q97.5']

    direction = "increases" if mean > 0 else "decreases"
    print(f"  - {comp}: {direction} odds of success by {abs(mean):.3f}")
    print(f"    (95% CrI: [{ci_lower:.3f}, {ci_upper:.3f}])")

# Make predictions for new treatment combinations
print("\n" + "=" * 70)
print("PREDICTIONS")
print("=" * 70)

# Predict effect of NRT vs Control
pred_nrt = analysis.predict('Control', 'NRT')
print(f"\nNRT vs Control:")
print(f"  Effect: {pred_nrt['mean']:.3f} (95% CrI: [{pred_nrt['quantiles']['2.5%']:.3f}, {pred_nrt['quantiles']['97.5%']:.3f}])")

# Predict effect of combined intervention
pred_combo = analysis.predict('Control', 'NRT + Counseling')
print(f"\nNRT + Counseling vs Control:")
print(f"  Effect: {pred_combo['mean']:.3f} (95% CrI: [{pred_combo['quantiles']['2.5%']:.3f}, {pred_combo['quantiles']['97.5%']:.3f}])")

# Network statistics
print("\n" + "=" * 70)
print("NETWORK STATISTICS")
print("=" * 70)

network_stats = analysis.get_network_stats()
print(f"\nTreatment Network:")
print(f"  Nodes (treatments): {network_stats['n_nodes']}")
print(f"  Edges (direct comparisons): {network_stats['n_edges']}")
print(f"  Network density: {network_stats['density']:.3f}")
print(f"  Connected: {network_stats['connected']}")

# Visualization
print("\n" + "=" * 70)
print("GENERATING VISUALIZATIONS")
print("=" * 70)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1. Treatment network
print("\n1. Plotting treatment network...")
analysis.plot_network(ax=axes[0, 0], title="Treatment Comparison Network")

# 2. Component effects
print("2. Plotting component effects...")
analysis.plot_component_effects(ax=axes[0, 1], title="Component Effect Estimates")

# 3. Treatment rankings
print("3. Plotting treatment rankings...")
try:
    analysis.plot_rankings(ax=axes[1, 0], title="Treatment Rankings (SUCRA)")
except Exception as e:
    print(f"   Could not plot rankings: {e}")
    axes[1, 0].text(0.5, 0.5, 'Rankings not available', ha='center', va='center')
    axes[1, 0].axis('off')

# 4. Forest plot of component effects
print("4. Creating forest plot...")
from cnma_platform.visualization.plots import plot_forest
plot_forest(
    component_effects,
    group_col='component',
    effect_col='mean',
    se_col='sd',
    ax=axes[1, 1],
    title="Component Effects (Forest Plot)"
)

plt.tight_layout()
plt.savefig('examples/output_01_basic_cnma.png', dpi=300, bbox_inches='tight')
print("\nVisualization saved as 'examples/output_01_basic_cnma.png'")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE!")
print("=" * 70)
