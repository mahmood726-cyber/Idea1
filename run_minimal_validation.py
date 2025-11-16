#!/usr/bin/env python3
"""
Minimal validation test - bypasses full import chain
"""
import sys
sys.path.insert(0, '/home/user/Idea1')

import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

# Import only what we need
from cnma_platform.models.additive_model import AdditiveModel
from cnma_platform.validation.simulation import simulate_cnma_data

def minimal_validation(n_replications=5, output_dir='docs/validation_results_ACTUAL'):
    """Run minimal parameter recovery validation"""

    print("="*80)
    print("MINIMAL VALIDATION STUDY")
    print("="*80)
    print(f"Replications: {n_replications}")
    print(f"Start time: {datetime.now()}")
    print("="*80)

    # True parameters
    beta_true = np.array([0.5, -0.3, 0.4])
    tau_true = 0.15

    results = []

    for rep in range(n_replications):
        print(f"\n--- Replication {rep+1}/{n_replications} ---")

        # Simulate data
        data, component_matrix, components = simulate_cnma_data(
            n_components=3,
            n_studies_per_comparison=5,
            beta_true=beta_true,
            tau_true=tau_true,
            include_multi_arm=True,
            prop_multi_arm=0.3,
            random_seed=42 + rep
        )

        print(f"  Simulated {len(data)} contrasts from {len(data['study'].unique())} studies")

        # Fit model
        model = AdditiveModel(data=data, data_format="contrast")
        model.components = components
        model.component_matrix = component_matrix
        model.n_components = 3

        print("  Fitting MCMC...")
        fit_results = model.fit(
            n_samples=500,
            n_warmup=500,
            n_chains=2,
            random_seed=42 + rep
        )

        # Extract estimates
        component_effects = model.get_component_effects()
        beta_est = component_effects['mean'].values

        # Get tau estimate
        import arviz as az
        trace_summary = az.summary(model.trace)
        tau_est = trace_summary.loc['tau', 'mean']

        # Calculate bias
        bias = beta_est - beta_true

        # Check coverage
        hdi_lower = component_effects['hdi_2.5'].values
        hdi_upper = component_effects['hdi_97.5'].values
        coverage = [(beta_true[i] >= hdi_lower[i]) and (beta_true[i] <= hdi_upper[i])
                   for i in range(3)]

        print(f"  Beta estimates: {beta_est}")
        print(f"  Bias: {bias}")
        print(f"  Coverage: {coverage}")
        print(f"  Tau estimate: {tau_est:.3f} (true: {tau_true})")
        print(f"  Converged: {fit_results['convergence']['converged']}")
        print(f"  Max R-hat: {fit_results['convergence']['max_rhat']:.4f}")

        results.append({
            'replication': rep + 1,
            'beta_1_est': beta_est[0],
            'beta_2_est': beta_est[1],
            'beta_3_est': beta_est[2],
            'tau_est': tau_est,
            'bias_1': bias[0],
            'bias_2': bias[1],
            'bias_3': bias[2],
            'coverage_1': coverage[0],
            'coverage_2': coverage[1],
            'coverage_3': coverage[2],
            'converged': fit_results['convergence']['converged'],
            'max_rhat': fit_results['convergence']['max_rhat']
        })

    # Summarize results
    df = pd.DataFrame(results)

    print("\n" + "="*80)
    print("VALIDATION RESULTS SUMMARY")
    print("="*80)

    print(f"\nMean bias:")
    print(f"  Beta 1: {df['bias_1'].mean():.4f}")
    print(f"  Beta 2: {df['bias_2'].mean():.4f}")
    print(f"  Beta 3: {df['bias_3'].mean():.4f}")

    print(f"\nRMSE:")
    print(f"  Beta 1: {np.sqrt((df['bias_1']**2).mean()):.4f}")
    print(f"  Beta 2: {np.sqrt((df['bias_2']**2).mean()):.4f}")
    print(f"  Beta 3: {np.sqrt((df['bias_3']**2).mean()):.4f}")

    print(f"\nCoverage:")
    print(f"  Beta 1: {df['coverage_1'].mean()*100:.1f}%")
    print(f"  Beta 2: {df['coverage_2'].mean()*100:.1f}%")
    print(f"  Beta 3: {df['coverage_3'].mean()*100:.1f}%")

    print(f"\nConvergence:")
    print(f"  Success rate: {df['converged'].mean()*100:.1f}%")
    print(f"  Mean max R-hat: {df['max_rhat'].mean():.4f}")

    # Save results
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_file = Path(output_dir) / f"minimal_validation_{n_replications}reps.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")

    print(f"\nEnd time: {datetime.now()}")
    print("="*80)

    return df

if __name__ == '__main__':
    minimal_validation(n_replications=5)
