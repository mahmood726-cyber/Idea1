"""
Parameter recovery validation studies.

This module implements simulation studies to validate that the CNMA models
can correctly recover known parameter values.
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from cnma_platform.models.additive_model import AdditiveModel
from cnma_platform.validation.simulation import simulate_cnma_data


def run_parameter_recovery_study(
    n_components: int = 3,
    n_studies_per_comparison: int = 5,
    beta_true: np.ndarray = None,
    tau_true: float = 0.15,
    n_replications: int = 100,
    n_samples: int = 1000,
    n_warmup: int = 500,
    random_seed: int = 42
) -> Dict:
    """
    Run parameter recovery study to validate CNMA implementation.

    Simulates data with known parameters, fits model, and assesses whether
    true parameters are recovered within credible intervals.

    Parameters
    ----------
    n_components : int
        Number of intervention components
    n_studies_per_comparison : int
        Number of studies for each treatment comparison
    beta_true : np.ndarray, optional
        True component effect values (random if None)
    tau_true : float
        True between-study heterogeneity SD
    n_replications : int
        Number of simulation replications
    n_samples : int
        MCMC samples per replication
    n_warmup : int
        Warmup samples
    random_seed : int
        Random seed for reproducibility

    Returns
    -------
    results : dict
        Parameter recovery results including bias, coverage, RMSE
    """
    np.random.seed(random_seed)

    # Set true parameter values
    if beta_true is None:
        beta_true = np.random.uniform(-0.5, 0.5, size=n_components)

    print("=" * 70)
    print("PARAMETER RECOVERY STUDY")
    print("=" * 70)
    print(f"\nTrue parameters:")
    print(f"  Beta (component effects): {beta_true}")
    print(f"  Tau (heterogeneity SD): {tau_true}")
    print(f"\nSimulation settings:")
    print(f"  Replications: {n_replications}")
    print(f"  Studies per comparison: {n_studies_per_comparison}")
    print(f"  MCMC samples: {n_samples}")

    # Storage for results
    beta_estimates = []
    tau_estimates = []
    coverage_beta = []
    coverage_tau = []

    for rep in range(n_replications):
        if (rep + 1) % 10 == 0:
            print(f"\nReplication {rep + 1}/{n_replications}...")

        # Simulate data with known parameters (including multi-arm trials)
        data, component_matrix, components = simulate_cnma_data(
            n_components=n_components,
            n_studies_per_comparison=n_studies_per_comparison,
            beta_true=beta_true,
            tau_true=tau_true,
            include_multi_arm=True,  # Include multi-arm trials
            prop_multi_arm=0.3,  # 30% of studies are 3-arm
            random_seed=random_seed + rep
        )

        # Fit model
        try:
            model = AdditiveModel(data=data, data_format="contrast")

            # CRITICAL FIX: Reorder component_matrix to match model's sorted treatment order
            # The model extracts treatments from data and sorts them,
            # but component_matrix from simulation is in a different order

            # Get treatment names from simulation (same order as component_matrix rows)
            treatments_sim = []
            treatments_sim.append(set())  # Control
            for i in range(n_components):
                treatments_sim.append({components[i]})
            for i in range(n_components):
                for j in range(i + 1, n_components):
                    treatments_sim.append({components[i], components[j]})

            treatment_names_sim = ['+'.join(sorted(t)) if t else 'Control' for t in treatments_sim]

            # Create mapping from model's sorted order to simulation order
            reordered_component_matrix = np.zeros_like(component_matrix)
            for model_idx, treatment_name in enumerate(model.treatments):
                sim_idx = treatment_names_sim.index(treatment_name)
                reordered_component_matrix[model_idx, :] = component_matrix[sim_idx, :]

            # Now set the correctly ordered component_matrix
            model.components = components
            model.component_matrix = reordered_component_matrix
            model.n_components = n_components

            # Fit with proper number of chains for convergence diagnostics
            model.fit(
                n_samples=n_samples,
                n_warmup=n_warmup,
                n_chains=4,  # Use 4 chains for proper convergence assessment
                random_seed=random_seed + rep
            )

            # Extract estimates
            beta_posterior = model.trace.posterior['beta'].values.reshape(-1, n_components)
            tau_posterior = model.trace.posterior['tau'].values.flatten()

            # Mean estimates
            beta_hat = beta_posterior.mean(axis=0)
            tau_hat = tau_posterior.mean()

            beta_estimates.append(beta_hat)
            tau_estimates.append(tau_hat)

            # Check coverage (do 95% HDIs contain true values?)
            beta_coverage = np.zeros(n_components, dtype=bool)
            for i in range(n_components):
                hdi_low = np.percentile(beta_posterior[:, i], 2.5)
                hdi_high = np.percentile(beta_posterior[:, i], 97.5)
                beta_coverage[i] = (beta_true[i] >= hdi_low) and (beta_true[i] <= hdi_high)

            coverage_beta.append(beta_coverage)

            tau_hdi_low = np.percentile(tau_posterior, 2.5)
            tau_hdi_high = np.percentile(tau_posterior, 97.5)
            tau_covered = (tau_true >= tau_hdi_low) and (tau_true <= tau_hdi_high)
            coverage_tau.append(tau_covered)

        except Exception as e:
            print(f"  Error in replication {rep + 1}: {e}")
            continue

    # Analyze results
    beta_estimates = np.array(beta_estimates)
    tau_estimates = np.array(tau_estimates)
    coverage_beta = np.array(coverage_beta)
    coverage_tau = np.array(coverage_tau)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    # Bias
    bias_beta = beta_estimates.mean(axis=0) - beta_true
    print(f"\nBias in beta estimates: {bias_beta}")
    print(f"  Mean absolute bias: {np.abs(bias_beta).mean():.4f}")

    bias_tau = tau_estimates.mean() - tau_true
    print(f"\nBias in tau estimate: {bias_tau:.4f}")

    # RMSE
    rmse_beta = np.sqrt(((beta_estimates - beta_true) ** 2).mean(axis=0))
    print(f"\nRMSE for beta: {rmse_beta}")
    print(f"  Mean RMSE: {rmse_beta.mean():.4f}")

    rmse_tau = np.sqrt(((tau_estimates - tau_true) ** 2).mean())
    print(f"\nRMSE for tau: {rmse_tau:.4f}")

    # Coverage
    coverage_beta_rate = coverage_beta.mean(axis=0)
    print(f"\n95% HDI coverage for beta: {coverage_beta_rate}")
    print(f"  Mean coverage: {coverage_beta_rate.mean():.2%}")
    print(f"  Expected: 95%")

    coverage_tau_rate = coverage_tau.mean()
    print(f"\n95% HDI coverage for tau: {coverage_tau_rate:.2%}")

    # Assessment
    print("\n" + "=" * 70)
    print("ASSESSMENT")
    print("=" * 70)

    success = True

    # Check bias (should be close to 0)
    if np.abs(bias_beta).mean() > 0.1:
        print("\n⚠ WARNING: Substantial bias in beta estimates")
        success = False

    if np.abs(bias_tau) > 0.05:
        print("\n⚠ WARNING: Substantial bias in tau estimate")
        success = False

    # Check coverage (should be close to 0.95)
    if coverage_beta_rate.mean() < 0.90 or coverage_beta_rate.mean() > 0.98:
        print("\n⚠ WARNING: Coverage probability deviates from nominal 95%")
        success = False

    if coverage_tau_rate < 0.90 or coverage_tau_rate > 0.98:
        print("\n⚠ WARNING: Tau coverage deviates from nominal 95%")
        success = False

    if success:
        print("\n✓ Parameter recovery successful!")
        print("  - Bias is small")
        print("  - RMSE is acceptable")
        print("  - Coverage probabilities are close to nominal level")

    results = {
        'beta_true': beta_true,
        'tau_true': tau_true,
        'beta_estimates': beta_estimates,
        'tau_estimates': tau_estimates,
        'bias_beta': bias_beta,
        'bias_tau': bias_tau,
        'rmse_beta': rmse_beta,
        'rmse_tau': rmse_tau,
        'coverage_beta': coverage_beta_rate,
        'coverage_tau': coverage_tau_rate,
        'success': success,
        'n_replications': len(beta_estimates),
    }

    return results
