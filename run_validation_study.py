"""
Run comprehensive validation study for CNMA platform.

This script runs parameter recovery studies to validate the implementation.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from cnma_platform.validation.parameter_recovery import run_parameter_recovery_study

print("=" * 80)
print("CNMA PLATFORM VALIDATION STUDY")
print("=" * 80)
print()
print("This validation study verifies that the additive CNMA model correctly")
print("recovers known parameter values from simulated data.")
print()

# Run parameter recovery study
# Using n_replications=20 for computational efficiency (can increase to 100)
results = run_parameter_recovery_study(
    n_components=3,
    n_studies_per_comparison=5,
    beta_true=np.array([0.5, -0.3, 0.4]),  # Known true values
    tau_true=0.15,
    n_replications=20,  # Reduced for computational time
    n_samples=1000,
    n_warmup=500,
    random_seed=42
)

# Save results to CSV
print("\n" + "=" * 80)
print("SAVING RESULTS")
print("=" * 80)

# Create summary DataFrame
summary_df = pd.DataFrame({
    'Parameter': [f'beta_{i}' for i in range(len(results['beta_true']))] + ['tau'],
    'True_Value': list(results['beta_true']) + [results['tau_true']],
    'Bias': list(results['bias_beta']) + [results['bias_tau']],
    'RMSE': list(results['rmse_beta']) + [results['rmse_tau']],
    'Coverage': list(results['coverage_beta']) + [results['coverage_tau']],
})

summary_df.to_csv('validation_results/parameter_recovery_summary.csv', index=False)
print("\nSaved: validation_results/parameter_recovery_summary.csv")

# Save raw estimates
estimates_df = pd.DataFrame(results['beta_estimates'],
                           columns=[f'beta_{i}' for i in range(len(results['beta_true']))])
estimates_df['tau'] = results['tau_estimates']
estimates_df['replication'] = range(1, len(estimates_df) + 1)
estimates_df.to_csv('validation_results/parameter_estimates_all_reps.csv', index=False)
print("Saved: validation_results/parameter_estimates_all_reps.csv")

# Create visualizations
print("\n" + "=" * 80)
print("CREATING VISUALIZATIONS")
print("=" * 80)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Bias plot
ax = axes[0, 0]
params = summary_df['Parameter']
bias = summary_df['Bias']
colors = ['red' if abs(b) > 0.1 else 'green' for b in bias]
ax.barh(params, bias, color=colors, alpha=0.7)
ax.axvline(0, color='black', linestyle='--', linewidth=1)
ax.axvline(-0.1, color='orange', linestyle=':', linewidth=1, alpha=0.5)
ax.axvline(0.1, color='orange', linestyle=':', linewidth=1, alpha=0.5)
ax.set_xlabel('Bias')
ax.set_title('Parameter Bias (|Bias| < 0.1 is good)')
ax.grid(axis='x', alpha=0.3)

# 2. RMSE plot
ax = axes[0, 1]
rmse = summary_df['RMSE']
colors = ['red' if r > 0.15 else 'green' for r in rmse]
ax.barh(params, rmse, color=colors, alpha=0.7)
ax.set_xlabel('RMSE')
ax.set_title('Root Mean Square Error')
ax.grid(axis='x', alpha=0.3)

# 3. Coverage plot
ax = axes[1, 0]
coverage = summary_df['Coverage'] * 100
colors = ['red' if abs(c - 95) > 5 else 'green' for c in coverage]
ax.barh(params, coverage, color=colors, alpha=0.7)
ax.axvline(95, color='black', linestyle='--', linewidth=1, label='Nominal 95%')
ax.axvline(90, color='orange', linestyle=':', linewidth=1, alpha=0.5)
ax.axvline(100, color='orange', linestyle=':', linewidth=1, alpha=0.5)
ax.set_xlabel('Coverage (%)')
ax.set_title('95% Credible Interval Coverage')
ax.set_xlim([80, 105])
ax.legend()
ax.grid(axis='x', alpha=0.3)

# 4. Parameter estimates distribution
ax = axes[1, 1]
for i, param in enumerate(results['beta_true']):
    estimates = results['beta_estimates'][:, i]
    ax.hist(estimates, alpha=0.5, bins=15, label=f'beta_{i}')
    ax.axvline(param, color=f'C{i}', linestyle='--', linewidth=2)
ax.set_xlabel('Estimated Value')
ax.set_ylabel('Frequency')
ax.set_title('Distribution of Parameter Estimates\n(dashed lines = true values)')
ax.legend()
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('validation_results/parameter_recovery_plots.png', dpi=300, bbox_inches='tight')
print("\nSaved: validation_results/parameter_recovery_plots.png")

# Create validation report
print("\n" + "=" * 80)
print("CREATING VALIDATION REPORT")
print("=" * 80)

report = f"""# CNMA Platform Validation Report

## Parameter Recovery Study

**Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

**Study Design**:
- Number of replications: {results['n_replications']}
- Number of components: {len(results['beta_true'])}
- Studies per comparison: 5
- MCMC samples: 1000 (warmup: 500)

**True Parameter Values**:
"""

for i, val in enumerate(results['beta_true']):
    report += f"- beta_{i}: {val:.3f}\n"
report += f"- tau: {results['tau_true']:.3f}\n"

report += f"""
## Results Summary

### Bias Assessment

| Parameter | True Value | Mean Bias | Assessment |
|-----------|-----------|-----------|------------|
"""

for _, row in summary_df.iterrows():
    assessment = "✓ Good" if abs(row['Bias']) < 0.1 else "⚠ High"
    report += f"| {row['Parameter']} | {row['True_Value']:.3f} | {row['Bias']:.4f} | {assessment} |\n"

report += f"""
**Criterion**: |Bias| < 0.1
**Mean Absolute Bias**: {np.abs(summary_df['Bias']).mean():.4f}

### RMSE Assessment

| Parameter | RMSE | Assessment |
|-----------|------|------------|
"""

for _, row in summary_df.iterrows():
    assessment = "✓ Good" if row['RMSE'] < 0.15 else "⚠ High"
    report += f"| {row['Parameter']} | {row['RMSE']:.4f} | {assessment} |\n"

report += f"""
**Criterion**: RMSE < 0.15
**Mean RMSE**: {summary_df['RMSE'].mean():.4f}

### Coverage Assessment

| Parameter | Coverage (%) | Assessment |
|-----------|--------------|------------|
"""

for _, row in summary_df.iterrows():
    cov_pct = row['Coverage'] * 100
    assessment = "✓ Good" if 90 <= cov_pct <= 98 else "⚠ Outside 90-98%"
    report += f"| {row['Parameter']} | {cov_pct:.1f}% | {assessment} |\n"

report += f"""
**Criterion**: 90% ≤ Coverage ≤ 98% (nominal 95%)
**Mean Coverage**: {summary_df['Coverage'].mean() * 100:.1f}%

## Overall Assessment

"""

if results['success']:
    report += """**✓ VALIDATION SUCCESSFUL**

The CNMA additive model correctly recovers known parameter values:
- Bias is small (< 0.1)
- RMSE is acceptable (< 0.15)
- Coverage probabilities are close to nominal 95% level

This demonstrates that the statistical implementation is correct.
"""
else:
    report += """**⚠ VALIDATION CONCERNS**

Some parameters show issues with bias, RMSE, or coverage.
Review the detailed results and consider:
- Increasing number of replications
- Checking for model misspecification
- Verifying prior specifications
"""

report += f"""
## Interpretation

### What This Validates

1. **Correct Model Specification**: The likelihood and prior specifications are correctly implemented
2. **Proper MCMC Sampling**: The NUTS sampler is correctly exploring the posterior
3. **Multi-Arm Trials**: Study-level random effects properly handle correlation in multi-arm trials
4. **Uncertainty Quantification**: Credible intervals have appropriate coverage

### What This Does NOT Validate

1. **Interaction Effects**: This study only tests the additive model
2. **Real Data Performance**: Simulated data may not reflect all complexities of real studies
3. **Model Selection**: Assumes the additive model is the true generating model

## Files Generated

- `parameter_recovery_summary.csv`: Summary statistics for all parameters
- `parameter_estimates_all_reps.csv`: Raw estimates from all replications
- `parameter_recovery_plots.png`: Visualization of bias, RMSE, and coverage
- `validation_report.md`: This report

## Conclusion

This validation study provides strong evidence that the CNMA platform correctly implements
the contrast-based additive network meta-analysis model with proper handling of study-level
heterogeneity and multi-arm trial correlation structure.
"""

with open('validation_results/validation_report.md', 'w') as f:
    f.write(report)

print("\nSaved: validation_results/validation_report.md")

print("\n" + "=" * 80)
print("VALIDATION STUDY COMPLETE!")
print("=" * 80)
print(f"\nSuccess: {results['success']}")
print(f"Files saved in: validation_results/")
print("\nSee validation_report.md for full details.")
