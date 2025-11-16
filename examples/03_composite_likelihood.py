"""
Example 3: Composite Likelihood Approach

This example demonstrates:
- Using composite likelihood for faster inference
- Avoiding within-study correlation assumptions
- Comparing with Bayesian approach
"""

import numpy as np
import matplotlib.pyplot as plt
import time
from cnma_platform import CNMAAnalysis
from cnma_platform.data import load_example_data

print("=" * 70)
print("EXAMPLE 3: Composite Likelihood CNMA")
print("=" * 70)

# Load data
data = load_example_data("depression")
print(f"\nLoaded data: {len(data)} observations from {data['study'].nunique()} studies")

# Fit using COMPOSITE LIKELIHOOD
print("\n" + "=" * 70)
print("FITTING MODEL WITH COMPOSITE LIKELIHOOD")
print("=" * 70)

start_time = time.time()

composite = CNMAAnalysis(
    data=data,
    model_type="additive",
    likelihood="composite",
    outcome_type="continuous"
)

composite.set_components(component_col="components")
composite.build_model()

results_cl = composite.fit()

cl_time = time.time() - start_time

print(f"\nComposite Likelihood fitting completed in {cl_time:.2f} seconds")

# Get results
component_effects_cl = composite.get_component_effects()
print("\nComponent Effects (Composite Likelihood):")
print(component_effects_cl[['component', 'estimate', 'se', 'ci_lower', 'ci_upper', 'p_value']])

# Interpret
print("\nStatistical Significance (α = 0.05):")
for _, row in component_effects_cl.iterrows():
    sig = "***" if row['p_value'] < 0.001 else \
          "**" if row['p_value'] < 0.01 else \
          "*" if row['p_value'] < 0.05 else "ns"
    print(f"  {row['component']:<20} p = {row['p_value']:.4f} {sig}")

# Fit using BAYESIAN (for comparison)
print("\n" + "=" * 70)
print("FITTING MODEL WITH BAYESIAN INFERENCE")
print("=" * 70)

start_time = time.time()

bayesian = CNMAAnalysis(
    data=data,
    model_type="additive",
    likelihood="bayesian",
    outcome_type="continuous"
)

bayesian.set_components(component_col="components")
results_bayes = bayesian.fit(n_samples=1000, n_warmup=500, n_chains=2)

bayes_time = time.time() - start_time

print(f"\nBayesian fitting completed in {bayes_time:.2f} seconds")

component_effects_bayes = bayesian.get_component_effects()
print("\nComponent Effects (Bayesian):")
print(component_effects_bayes[['component', 'mean', 'sd', 'q2.5', 'q97.5']])

# Compare approaches
print("\n" + "=" * 70)
print("COMPARISON: Composite Likelihood vs Bayesian")
print("=" * 70)

print(f"\nComputational Time:")
print(f"  Composite Likelihood: {cl_time:.2f} seconds")
print(f"  Bayesian MCMC:        {bayes_time:.2f} seconds")
print(f"  Speedup:              {bayes_time/cl_time:.1f}x faster")

print(f"\n{'Component':<20} {'CL Estimate':<15} {'Bayes Mean':<15} {'Difference':<15}")
print("-" * 65)

for comp in component_effects_cl['component']:
    cl_row = component_effects_cl[component_effects_cl['component'] == comp].iloc[0]
    bayes_row = component_effects_bayes[component_effects_bayes['component'] == comp].iloc[0]

    diff = abs(cl_row['estimate'] - bayes_row['mean'])

    print(f"{comp:<20} {cl_row['estimate']:>7.3f} ± {cl_row['se']:>5.3f}  "
          f"{bayes_row['mean']:>7.3f} ± {bayes_row['sd']:>5.3f}  "
          f"{diff:>7.4f}")

print("\nNote: Small differences are expected due to different estimation approaches")

# Predictions
print("\n" + "=" * 70)
print("PREDICTIONS")
print("=" * 70)

# Define treatment combinations for prediction
print("\nPredicting effects of treatment combinations:")

test_treatments = [
    ('Waitlist', 'CBT'),
    ('Waitlist', 'Medication'),
    ('Waitlist', 'CBT + Medication'),
    ('CBT', 'CBT + Medication'),
]

print(f"\n{'Comparison':<35} {'CL Estimate':<20} {'Bayes Estimate':<20}")
print("-" * 75)

for t1, t2 in test_treatments:
    try:
        # For composite likelihood, need to compute manually
        # Extract component differences
        comps1 = set(data[data['treatment'] == t1]['components'].iloc[0].split(',')) if t1 != 'Waitlist' else set()
        comps2 = set(data[data['treatment'] == t2]['components'].iloc[0].split(','))

        comp_diff = comps2 - comps1

        # Composite likelihood prediction
        cl_est = sum(component_effects_cl[component_effects_cl['component'] == c]['estimate'].values[0]
                     for c in comp_diff if c in component_effects_cl['component'].values)

        # Bayesian prediction
        pred_bayes = bayesian.predict(t1, t2)

        print(f"{t2 + ' vs ' + t1:<35} "
              f"{cl_est:>7.3f}            "
              f"{pred_bayes['mean']:>7.3f} ± {pred_bayes['sd']:>5.3f}")

    except Exception as e:
        print(f"{t2 + ' vs ' + t1:<35} Error: {str(e)[:40]}")

# Visualization
print("\n" + "=" * 70)
print("GENERATING VISUALIZATIONS")
print("=" * 70)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 1. Compare point estimates
y_pos = range(len(component_effects_cl))
axes[0, 0].errorbar(
    component_effects_cl['estimate'], y_pos,
    xerr=1.96 * component_effects_cl['se'],
    fmt='o', label='Composite Likelihood', alpha=0.7, markersize=8
)
axes[0, 0].errorbar(
    component_effects_bayes['mean'], y_pos,
    xerr=[component_effects_bayes['mean'] - component_effects_bayes['q2.5'],
          component_effects_bayes['q97.5'] - component_effects_bayes['mean']],
    fmt='s', label='Bayesian', alpha=0.7, markersize=8
)
axes[0, 0].set_yticks(y_pos)
axes[0, 0].set_yticklabels(component_effects_cl['component'])
axes[0, 0].axvline(0, color='red', linestyle='--', alpha=0.5)
axes[0, 0].set_xlabel('Effect Size')
axes[0, 0].set_title('Component Effects: CL vs Bayesian')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)

# 2. Composite likelihood estimates only
composite.plot_component_effects(ax=axes[0, 1], title='Composite Likelihood Estimates')

# 3. Network
composite.plot_network(ax=axes[1, 0])

# 4. Computation time comparison
methods = ['Composite\nLikelihood', 'Bayesian\nMCMC']
times = [cl_time, bayes_time]
colors = ['steelblue', 'coral']

axes[1, 1].bar(methods, times, color=colors, alpha=0.7)
axes[1, 1].set_ylabel('Time (seconds)')
axes[1, 1].set_title('Computational Efficiency')
axes[1, 1].grid(axis='y', alpha=0.3)

for i, (method, t) in enumerate(zip(methods, times)):
    axes[1, 1].text(i, t + 0.5, f'{t:.1f}s', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig('examples/output_03_composite_likelihood.png', dpi=300, bbox_inches='tight')
print("\nVisualization saved as 'examples/output_03_composite_likelihood.png'")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE!")
print("=" * 70)
print("\nKey Takeaways:")
print("1. Composite likelihood is much faster than Bayesian MCMC")
print("2. Both approaches give similar point estimates")
print("3. Composite likelihood provides valid frequentist inference")
print("4. Use composite likelihood for large datasets or quick analyses")
print("5. Use Bayesian for full uncertainty quantification and complex models")
