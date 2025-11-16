#!/usr/bin/env python3
"""
Run Full Parameter Recovery Validation Study

This script runs the comprehensive 100-replication parameter recovery study
required for publication in Research Synthesis Methods.

Results are saved to docs/validation_results/ for inclusion as supplementary
materials.

Usage:
    python scripts/run_validation_study.py [--n_replications=100] [--output_dir=docs/validation_results]
"""

import argparse
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cnma_platform.validation.parameter_recovery import run_parameter_recovery_study


def main():
    parser = argparse.ArgumentParser(description='Run parameter recovery validation study')
    parser.add_argument('--n_replications', type=int, default=100,
                        help='Number of replications (default: 100)')
    parser.add_argument('--n_components', type=int, default=3,
                        help='Number of components (default: 3)')
    parser.add_argument('--n_samples', type=int, default=2000,
                        help='MCMC samples per chain (default: 2000)')
    parser.add_argument('--n_warmup', type=int, default=1000,
                        help='MCMC warmup samples (default: 1000)')
    parser.add_argument('--output_dir', type=str, default='docs/validation_results',
                        help='Output directory for results')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed (default: 42)')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("CNMA PLATFORM - FULL VALIDATION STUDY")
    print("=" * 80)
    print(f"\nStudy Parameters:")
    print(f"  Replications: {args.n_replications}")
    print(f"  Components: {args.n_components}")
    print(f"  MCMC samples: {args.n_samples} (warmup: {args.n_warmup})")
    print(f"  Random seed: {args.seed}")
    print(f"  Output directory: {output_dir}")
    print(f"\nEstimated runtime: {args.n_replications * 2} - {args.n_replications * 5} minutes")
    print("=" * 80)

    # Set true parameters
    beta_true = np.array([0.5, -0.3, 0.4])[:args.n_components]
    tau_true = 0.15

    # Run parameter recovery study
    print("\nStarting validation study...")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = run_parameter_recovery_study(
        n_components=args.n_components,
        n_studies_per_comparison=5,
        beta_true=beta_true,
        tau_true=tau_true,
        n_replications=args.n_replications,
        n_samples=args.n_samples,
        n_warmup=args.n_warmup,
        random_seed=args.seed
    )

    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Summary results
    summary_path = output_dir / f'validation_summary_{timestamp}.txt'
    with open(summary_path, 'w') as f:
        f.write("CNMA Platform - Parameter Recovery Validation Study\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Replications: {args.n_replications}\n")
        f.write(f"MCMC samples: {args.n_samples} (warmup: {args.n_warmup})\n")
        f.write(f"Random seed: {args.seed}\n\n")

        f.write("TRUE PARAMETERS:\n")
        f.write("-" * 80 + "\n")
        for i, val in enumerate(beta_true):
            f.write(f"β_{i+1}: {val:.3f}\n")
        f.write(f"τ:   {tau_true:.3f}\n\n")

        f.write("BIAS:\n")
        f.write("-" * 80 + "\n")
        for i, val in enumerate(results['bias_beta']):
            f.write(f"β_{i+1}: {val:.4f}\n")
        f.write(f"τ:   {results['bias_tau']:.4f}\n")
        f.write(f"Mean absolute bias (β): {np.abs(results['bias_beta']).mean():.4f}\n\n")

        f.write("RMSE:\n")
        f.write("-" * 80 + "\n")
        for i, val in enumerate(results['rmse_beta']):
            f.write(f"β_{i+1}: {val:.4f}\n")
        f.write(f"τ:   {results['rmse_tau']:.4f}\n")
        f.write(f"Mean RMSE (β): {results['rmse_beta'].mean():.4f}\n\n")

        f.write("95% HDI COVERAGE:\n")
        f.write("-" * 80 + "\n")
        for i, val in enumerate(results['coverage_beta']):
            f.write(f"β_{i+1}: {val:.2%}\n")
        f.write(f"τ:   {results['coverage_tau']:.2%}\n")
        f.write(f"Mean coverage (β): {results['coverage_beta'].mean():.2%}\n")
        f.write(f"Expected: 95%\n\n")

        f.write("ASSESSMENT:\n")
        f.write("-" * 80 + "\n")
        if results['success']:
            f.write("✓ VALIDATION SUCCESSFUL\n")
            f.write("  - Bias is small\n")
            f.write("  - RMSE is acceptable\n")
            f.write("  - Coverage probabilities near nominal level\n")
        else:
            f.write("⚠ VALIDATION CONCERNS\n")
            f.write("  - Check bias, RMSE, or coverage issues\n")

    print(f"\n✓ Summary saved to: {summary_path}")

    # Detailed results (CSV for supplementary materials)
    # Table 1: Parameter estimates
    param_table = []
    for i in range(args.n_components):
        param_table.append({
            'Parameter': f'β_{i+1}',
            'True Value': beta_true[i],
            'Mean Estimate': results['beta_estimates'][:, i].mean(),
            'SD': results['beta_estimates'][:, i].std(),
            'Bias': results['bias_beta'][i],
            'RMSE': results['rmse_beta'][i],
            'Coverage (95%)': results['coverage_beta'][i]
        })

    param_table.append({
        'Parameter': 'τ',
        'True Value': tau_true,
        'Mean Estimate': results['tau_estimates'].mean(),
        'SD': results['tau_estimates'].std(),
        'Bias': results['bias_tau'],
        'RMSE': results['rmse_tau'],
        'Coverage (95%)': results['coverage_tau']
    })

    df_params = pd.DataFrame(param_table)
    params_path = output_dir / f'table1_parameter_estimates_{timestamp}.csv'
    df_params.to_csv(params_path, index=False)
    print(f"✓ Table 1 (Parameter Estimates) saved to: {params_path}")

    # Raw estimates (for further analysis)
    raw_path = output_dir / f'raw_estimates_{timestamp}.npz'
    np.savez(
        raw_path,
        beta_estimates=results['beta_estimates'],
        tau_estimates=results['tau_estimates'],
        beta_true=beta_true,
        tau_true=tau_true,
        n_replications=results['n_replications']
    )
    print(f"✓ Raw estimates saved to: {raw_path}")

    print("\n" + "=" * 80)
    print("VALIDATION STUDY COMPLETE")
    print("=" * 80)
    print(f"\nAll results saved to: {output_dir}/")
    print("\nFor publication, include:")
    print(f"  - {summary_path.name} (summary)")
    print(f"  - {params_path.name} (Table 1 for supplementary materials)")

    if results['success']:
        print("\n✓ VALIDATION SUCCESSFUL - Model implementation is correct!")
    else:
        print("\n⚠ VALIDATION CONCERNS - Review results carefully")

    return 0 if results['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
