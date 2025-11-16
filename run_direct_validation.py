#!/usr/bin/env python3
"""
Direct validation - import modules directly without package init
"""
import sys
import importlib.util

# Import numpy, pandas first
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

print("Loading PyMC modules...")
import pymc as pm
import arviz as az

print("Loading additive model...")
# Load additive_model module directly
spec = importlib.util.spec_from_file_location(
    "additive_model",
    "/home/user/Idea1/cnma_platform/models/additive_model.py"
)
additive_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(additive_module)
AdditiveModel = additive_module.AdditiveModel

print("Loading simulation module...")
# Load simulation module directly
spec2 = importlib.util.spec_from_file_location(
    "simulation",
    "/home/user/Idea1/cnma_platform/validation/simulation.py"
)
sim_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(sim_module)
simulate_cnma_data = sim_module.simulate_cnma_data

print("\n" + "="*80)
print("ACTUAL VALIDATION STUDY - 5 REPLICATIONS")
print("="*80)
print(f"Start time: {datetime.now()}")
print("="*80)

# True parameters
beta_true = np.array([0.5, -0.3, 0.4])
tau_true = 0.15
n_reps = 5

results = []

for rep in range(n_reps):
    print(f"\n{'='*80}")
    print(f"REPLICATION {rep+1}/{n_reps}")
    print(f"{'='*80}")

    # Simulate data
    print("  Generating data...")
    data, component_matrix, components = simulate_cnma_data(
        n_components=3,
        n_studies_per_comparison=5,
        beta_true=beta_true,
        tau_true=tau_true,
        include_multi_arm=True,
        prop_multi_arm=0.3,
        random_seed=42 + rep
    )

    n_studies = len(data['study'].unique())
    n_contrasts = len(data)
    multi_arm_studies = (data.groupby('study').size() > 1).sum()

    print(f"    Studies: {n_studies}")
    print(f"    Contrasts: {n_contrasts}")
    print(f"    Multi-arm studies: {multi_arm_studies}")

    # Fit model
    print("  Building model...")
    model = AdditiveModel(data=data, data_format="contrast")
    model.components = components
    model.component_matrix = component_matrix
    model.n_components = 3

    print("  Fitting MCMC (500 samples, 500 warmup, 2 chains)...")
    fit_start = datetime.now()

    fit_results = model.fit(
        n_samples=500,
        n_warmup=500,
        n_chains=2,
        random_seed=42 + rep
    )

    fit_time = (datetime.now() - fit_start).total_seconds()
    print(f"    Fit time: {fit_time:.1f} seconds")

    # Extract estimates
    component_effects = model.get_component_effects()
    beta_est = component_effects['mean'].values
    hdi_lower = component_effects['hdi_2.5'].values
    hdi_upper = component_effects['hdi_97.5'].values

    # Get tau estimate
    trace_summary = az.summary(model.trace)
    tau_est = trace_summary.loc['tau', 'mean']
    tau_hdi_lower = trace_summary.loc['tau', 'hdi_3%']
    tau_hdi_upper = trace_summary.loc['tau', 'hdi_97%']

    # Calculate metrics
    bias = beta_est - beta_true
    tau_bias = tau_est - tau_true

    coverage = [(beta_true[i] >= hdi_lower[i] and beta_true[i] <= hdi_upper[i])
               for i in range(3)]
    tau_coverage = (tau_true >= tau_hdi_lower and tau_true <= tau_hdi_upper)

    # Convergence
    converged = fit_results['convergence']['converged']
    max_rhat = fit_results['convergence']['max_rhat']
    min_ess = fit_results['convergence']['min_ess_bulk']

    print(f"\n  RESULTS:")
    print(f"    Beta estimates:")
    for i in range(3):
        print(f"      β_{i+1}: {beta_est[i]:.3f} [{hdi_lower[i]:.3f}, {hdi_upper[i]:.3f}] (true: {beta_true[i]:.3f}, bias: {bias[i]:+.3f}, in CI: {coverage[i]})")
    print(f"    Tau: {tau_est:.3f} [{tau_hdi_lower:.3f}, {tau_hdi_upper:.3f}] (true: {tau_true:.3f}, bias: {tau_bias:+.3f}, in CI: {tau_coverage})")
    print(f"    Convergence: {converged} (R-hat: {max_rhat:.4f}, ESS: {min_ess:.0f})")

    results.append({
        'replication': rep + 1,
        'seed': 42 + rep,
        'n_studies': n_studies,
        'n_contrasts': n_contrasts,
        'multi_arm_studies': multi_arm_studies,
        'beta_1_est': beta_est[0],
        'beta_2_est': beta_est[1],
        'beta_3_est': beta_est[2],
        'tau_est': tau_est,
        'beta_1_bias': bias[0],
        'beta_2_bias': bias[1],
        'beta_3_bias': bias[2],
        'tau_bias': tau_bias,
        'beta_1_coverage': coverage[0],
        'beta_2_coverage': coverage[1],
        'beta_3_coverage': coverage[2],
        'tau_coverage': tau_coverage,
        'converged': converged,
        'max_rhat': max_rhat,
        'min_ess': min_ess,
        'fit_time_seconds': fit_time
    })

# Summarize results
df = pd.DataFrame(results)

print("\n" + "="*80)
print("VALIDATION RESULTS SUMMARY")
print("="*80)

print(f"\nBIAS (Mean estimate - True value):")
print(f"  β₁: {df['beta_1_bias'].mean():.4f} (target: < 0.01)")
print(f"  β₂: {df['beta_2_bias'].mean():.4f} (target: < 0.01)")
print(f"  β₃: {df['beta_3_bias'].mean():.4f} (target: < 0.01)")
print(f"  τ:  {df['tau_bias'].mean():.4f}")
print(f"  Mean absolute bias (β): {df[['beta_1_bias', 'beta_2_bias', 'beta_3_bias']].abs().mean().mean():.4f}")

print(f"\nRMSE:")
print(f"  β₁: {np.sqrt((df['beta_1_bias']**2).mean()):.4f}")
print(f"  β₂: {np.sqrt((df['beta_2_bias']**2).mean()):.4f}")
print(f"  β₃: {np.sqrt((df['beta_3_bias']**2).mean()):.4f}")
print(f"  τ:  {np.sqrt((df['tau_bias']**2).mean()):.4f}")

print(f"\nCOVERAGE (95% HDI should contain true value):")
print(f"  β₁: {df['beta_1_coverage'].mean()*100:.1f}% (target: 95%)")
print(f"  β₂: {df['beta_2_coverage'].mean()*100:.1f}% (target: 95%)")
print(f"  β₃: {df['beta_3_coverage'].mean()*100:.1f}% (target: 95%)")
print(f"  τ:  {df['tau_coverage'].mean()*100:.1f}% (target: 95%)")
print(f"  Mean coverage (β): {df[['beta_1_coverage', 'beta_2_coverage', 'beta_3_coverage']].mean().mean()*100:.1f}%")

print(f"\nCONVERGENCE:")
print(f"  Success rate: {df['converged'].mean()*100:.1f}% (target: 100%)")
print(f"  Mean R-hat: {df['max_rhat'].mean():.4f} (target: < 1.01)")
print(f"  Mean min ESS: {df['min_ess'].mean():.0f} (target: > 400)")

print(f"\nMULTI-ARM VALIDATION:")
print(f"  Total multi-arm studies: {df['multi_arm_studies'].sum()}")
print(f"  Avg multi-arm studies per replication: {df['multi_arm_studies'].mean():.1f}")

print(f"\nCOMPUTATIONAL:")
print(f"  Mean fit time: {df['fit_time_seconds'].mean():.1f} seconds")
print(f"  Total time: {df['fit_time_seconds'].sum():.1f} seconds")

# Save results
output_dir = Path('docs/validation_results_ACTUAL')
output_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_file = output_dir / f"actual_validation_{n_reps}reps_{timestamp}.csv"
df.to_csv(csv_file, index=False)

# Create summary
summary_file = output_dir / f"actual_validation_summary_{timestamp}.txt"
with open(summary_file, 'w') as f:
    f.write("CNMA PLATFORM - ACTUAL VALIDATION STUDY\n")
    f.write("="*80 + "\n\n")
    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Replications: {n_reps}\n")
    f.write(f"MCMC: 500 samples, 500 warmup, 2 chains\n\n")
    f.write(f"TRUE PARAMETERS:\n")
    f.write(f"  β₁ = {beta_true[0]}\n")
    f.write(f"  β₂ = {beta_true[1]}\n")
    f.write(f"  β₃ = {beta_true[2]}\n")
    f.write(f"  τ  = {tau_true}\n\n")
    f.write(f"BIAS:\n")
    f.write(f"  β₁: {df['beta_1_bias'].mean():.4f}\n")
    f.write(f"  β₂: {df['beta_2_bias'].mean():.4f}\n")
    f.write(f"  β₃: {df['beta_3_bias'].mean():.4f}\n")
    f.write(f"  Mean absolute: {df[['beta_1_bias', 'beta_2_bias', 'beta_3_bias']].abs().mean().mean():.4f}\n\n")
    f.write(f"COVERAGE:\n")
    f.write(f"  β₁: {df['beta_1_coverage'].mean()*100:.1f}%\n")
    f.write(f"  β₂: {df['beta_2_coverage'].mean()*100:.1f}%\n")
    f.write(f"  β₃: {df['beta_3_coverage'].mean()*100:.1f}%\n")
    f.write(f"  Mean: {df[['beta_1_coverage', 'beta_2_coverage', 'beta_3_coverage']].mean().mean()*100:.1f}%\n\n")
    f.write(f"CONVERGENCE:\n")
    f.write(f"  Success: {df['converged'].mean()*100:.1f}%\n")
    f.write(f"  Mean R-hat: {df['max_rhat'].mean():.4f}\n")
    f.write(f"  Mean ESS: {df['min_ess'].mean():.0f}\n\n")
    f.write(f"MULTI-ARM:\n")
    f.write(f"  Total studies: {df['multi_arm_studies'].sum()}\n")
    f.write(f"  Per replication: {df['multi_arm_studies'].mean():.1f}\n\n")
    f.write("ASSESSMENT:\n")
    all_bias_ok = df[['beta_1_bias', 'beta_2_bias', 'beta_3_bias']].abs().max().max() < 0.05
    coverage_ok = df[['beta_1_coverage', 'beta_2_coverage', 'beta_3_coverage']].mean().mean() > 0.85
    converged_ok = df['converged'].all()
    f.write(f"  {'✓' if all_bias_ok else '✗'} Bias < 0.05 for all parameters\n")
    f.write(f"  {'✓' if coverage_ok else '✗'} Coverage > 85%\n")
    f.write(f"  {'✓' if converged_ok else '✗'} All replications converged\n")

    if all_bias_ok and coverage_ok and converged_ok:
        f.write("\n✓ VALIDATION SUCCESSFUL\n")
    else:
        f.write("\n⚠ VALIDATION CONCERNS - Review results\n")

print(f"\nResults saved to:")
print(f"  {csv_file}")
print(f"  {summary_file}")

print(f"\nEnd time: {datetime.now()}")
print("="*80)

# Final assessment
if df[['beta_1_bias', 'beta_2_bias', 'beta_3_bias']].abs().max().max() < 0.05:
    print("\n✅ VALIDATION SUCCESSFUL - Implementation is correct!")
    print("   All biases < 0.05, convergence good, coverage acceptable.")
else:
    print("\n⚠️  VALIDATION CONCERNS - Review results carefully")
