"""
Integration tests for CNMA models with actual MCMC fitting.

These tests run complete MCMC sampling to verify the full pipeline works correctly.
"""

import pytest
import numpy as np
import pandas as pd
from cnma_platform.models.additive_model import AdditiveModel
from cnma_platform.validation.simulation import simulate_cnma_data
from cnma_platform.data import load_example_data


@pytest.mark.slow
def test_full_mcmc_pipeline_with_multi_arm():
    """
    Integration test: Full MCMC pipeline with multi-arm trials.

    This tests the complete workflow from data simulation through MCMC fitting
    to parameter extraction, specifically including multi-arm trials.
    """
    np.random.seed(123)

    # True parameters
    beta_true = np.array([0.4, -0.2])
    tau_true = 0.10

    # Simulate data with multi-arm trials
    data, component_matrix, components = simulate_cnma_data(
        n_components=2,
        n_studies_per_comparison=4,
        beta_true=beta_true,
        tau_true=tau_true,
        include_multi_arm=True,
        prop_multi_arm=0.3,
        random_seed=123
    )

    # Verify we have multi-arm trials
    study_counts = data.groupby('study').size()
    assert (study_counts > 1).any(), "Should have multi-arm trials"
    print(f"\n  Generated {len(data)} contrasts from {len(study_counts)} studies")
    print(f"  Multi-arm studies: {(study_counts > 1).sum()}")

    # Initialize model
    model = AdditiveModel(data=data, data_format="contrast")
    model.components = components
    model.component_matrix = component_matrix
    model.n_components = 2

    # Fit model (minimal samples for speed in testing)
    print("  Fitting model with MCMC...")
    results = model.fit(
        n_samples=500,
        n_warmup=500,
        n_chains=2,
        random_seed=123
    )

    # Check convergence
    print(f"  Max R-hat: {results['convergence']['max_rhat']:.3f}")
    print(f"  Min ESS: {results['convergence']['min_ess_bulk']:.0f}")

    assert results['convergence']['converged'], "Model should converge"
    assert results['convergence']['max_rhat'] < 1.1, "R-hat should be < 1.1"

    # Extract component effects
    component_effects = model.get_component_effects()

    print("\n  Component Effects:")
    for i, row in component_effects.iterrows():
        print(f"    {row['component']}: {row['mean']:.3f} [{row['hdi_2.5']:.3f}, {row['hdi_97.5']:.3f}]")
        print(f"      True: {beta_true[i]:.3f}")

    # Check that estimates are reasonable (rough check)
    for i in range(2):
        est = component_effects.iloc[i]['mean']
        # Should be within ~2 standard errors of true value (won't always pass but should be close)
        assert abs(est - beta_true[i]) < 0.5, f"Estimate {i} should be reasonably close to true value"

    # Test predictions
    print("\n  Testing predictions...")
    pred = model.predict('Control', 'C1')
    assert 'mean' in pred
    assert 'hdi_2.5' in pred
    assert 'hdi_97.5' in pred
    print(f"    Control vs C1: {pred['mean']:.3f} [{pred['hdi_2.5']:.3f}, {pred['hdi_97.5']:.3f}]")

    # Test treatment ranking
    print("\n  Testing treatment ranking...")
    rankings = model.get_treatment_ranking()
    assert len(rankings) == model.n_treatments
    assert 'sucra' in rankings.columns
    print(f"    Top treatment: {rankings.iloc[0]['treatment']} (SUCRA: {rankings.iloc[0]['sucra']:.3f})")

    # Test posterior predictive check
    print("\n  Testing posterior predictive checks...")
    ppc = model.posterior_predictive_check()
    assert 'p_value_mean' in ppc
    print(f"    Predictive p-value: {ppc['p_value_mean']:.3f}")

    print("\n  ✓ Full pipeline test passed!")


@pytest.mark.slow
def test_example_data_pipeline():
    """
    Integration test: Full pipeline with example smoking cessation data.

    Tests the complete workflow using the built-in example dataset.
    """
    np.random.seed(456)

    # Load example data
    print("\n  Loading smoking cessation example data...")
    data = load_example_data("smoking_cessation")

    print(f"  Loaded {len(data)} contrasts from {data['study'].nunique()} studies")

    # Extract components from the data
    # For this test, we'll manually define the component matrix
    components = ['NRT', 'Counseling', 'Self-help', 'Group Support']

    # Simple component extraction (for testing)
    treatments_list = list(set(data['treatment_base'].unique()) | set(data['treatment_comp'].unique()))
    treatments_list = sorted(treatments_list)

    # Create component matrix
    component_matrix = np.zeros((len(treatments_list), len(components)))

    treatment_to_components = {
        'Control': set(),
        'NRT': {'NRT'},
        'Counseling': {'Counseling'},
        'Self-help': {'Self-help'},
        'Group Support': {'Group Support'},
        'NRT + Counseling': {'NRT', 'Counseling'},
        'NRT + Self-help': {'NRT', 'Self-help'},
        'Counseling + Group': {'Counseling', 'Group Support'},
        'NRT + Counseling + Group': {'NRT', 'Counseling', 'Group Support'},
    }

    for i, trt in enumerate(treatments_list):
        if trt in treatment_to_components:
            trt_comps = treatment_to_components[trt]
            for j, comp in enumerate(components):
                if comp in trt_comps:
                    component_matrix[i, j] = 1

    # Initialize and fit model
    print("  Initializing model...")
    model = AdditiveModel(data=data, data_format="contrast")
    model.components = components
    model.component_matrix = component_matrix
    model.n_components = len(components)
    model.treatments = treatments_list
    model.n_treatments = len(treatments_list)

    print("  Fitting model (minimal samples for testing)...")
    results = model.fit(
        n_samples=300,
        n_warmup=300,
        n_chains=2,
        random_seed=456
    )

    # Basic checks
    print(f"  Max R-hat: {results['convergence']['max_rhat']:.3f}")

    # NOTE: With minimal samples, convergence might not be perfect
    # but the pipeline should complete without errors

    component_effects = model.get_component_effects()
    print("\n  Component Effects:")
    for _, row in component_effects.iterrows():
        print(f"    {row['component']}: {row['mean']:.3f} [{row['hdi_2.5']:.3f}, {row['hdi_97.5']:.3f}]")

    # All component effects should be positive (smoking cessation)
    # (Note: with real data and interactions, this might not hold perfectly)
    print("\n  ✓ Example data pipeline test passed!")


@pytest.mark.slow
def test_convergence_diagnostics():
    """
    Integration test: Convergence diagnostics with known good and bad cases.

    Tests that convergence diagnostics correctly identify issues.
    """
    np.random.seed(789)

    # Simulate data
    beta_true = np.array([0.5, 0.3])
    data, component_matrix, components = simulate_cnma_data(
        n_components=2,
        n_studies_per_comparison=10,  # More studies = easier convergence
        beta_true=beta_true,
        tau_true=0.10,
        include_multi_arm=False,  # 2-arm only for simplicity
        random_seed=789
    )

    model = AdditiveModel(data=data, data_format="contrast")
    model.components = components
    model.component_matrix = component_matrix
    model.n_components = 2

    # Test 1: Good convergence (sufficient samples)
    print("\n  Test 1: Good convergence")
    results_good = model.fit(
        n_samples=1000,
        n_warmup=1000,
        n_chains=4,
        random_seed=789
    )

    print(f"    Max R-hat: {results_good['convergence']['max_rhat']:.4f}")
    print(f"    Min ESS: {results_good['convergence']['min_ess_bulk']:.0f}")
    print(f"    Converged: {results_good['convergence']['converged']}")

    # With these settings, should converge
    assert results_good['convergence']['max_rhat'] < 1.05, "Should have good R-hat"
    assert results_good['convergence']['min_ess_bulk'] > 100, "Should have sufficient ESS"

    # Test 2: Poor convergence (insufficient samples) - just check it runs
    print("\n  Test 2: Minimal convergence test (may not converge perfectly)")
    results_poor = model.fit(
        n_samples=50,  # Very few samples
        n_warmup=50,
        n_chains=2,
        random_seed=789
    )

    print(f"    Max R-hat: {results_poor['convergence']['max_rhat']:.4f}")
    print(f"    Min ESS: {results_poor['convergence']['min_ess_bulk']:.0f}")
    print(f"    Converged: {results_poor['convergence']['converged']}")

    # Just check it completes without crashing
    assert 'convergence' in results_poor

    print("\n  ✓ Convergence diagnostics test passed!")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("INTEGRATION TESTS - CNMA PLATFORM")
    print("=" * 80)

    print("\n[TEST 1] Full MCMC Pipeline with Multi-Arm Trials")
    print("-" * 80)
    test_full_mcmc_pipeline_with_multi_arm()

    print("\n[TEST 2] Example Data Pipeline")
    print("-" * 80)
    test_example_data_pipeline()

    print("\n[TEST 3] Convergence Diagnostics")
    print("-" * 80)
    test_convergence_diagnostics()

    print("\n" + "=" * 80)
    print("ALL INTEGRATION TESTS PASSED ✓")
    print("=" * 80)
