"""
Data simulation utilities for validation studies.
"""

from typing import Tuple, List
import numpy as np
import pandas as pd


def simulate_cnma_data(
    n_components: int = 3,
    n_studies_per_comparison: int = 5,
    beta_true: np.ndarray = None,
    tau_true: float = 0.15,
    sample_size_range: Tuple[int, int] = (100, 400),
    include_multi_arm: bool = True,
    prop_multi_arm: float = 0.3,
    random_seed: int = None
) -> Tuple[pd.DataFrame, np.ndarray, List[str]]:
    """
    Simulate CNMA data with known parameters, including multi-arm trials.

    Parameters
    ----------
    n_components : int
        Number of intervention components
    n_studies_per_comparison : int
        Number of studies for each comparison
    beta_true : np.ndarray, optional
        True component effects (random if None)
    tau_true : float
        Between-study heterogeneity SD
    sample_size_range : tuple
        Range for study sample sizes
    include_multi_arm : bool
        Whether to include multi-arm trials (default: True)
    prop_multi_arm : float
        Proportion of studies that are multi-arm (default: 0.3)
    random_seed : int, optional
        Random seed

    Returns
    -------
    data : pd.DataFrame
        Simulated contrast-based data
    component_matrix : np.ndarray
        Component presence matrix
    components : list
        Component names
    """
    if random_seed is not None:
        np.random.seed(random_seed)

    # Component names
    components = [f"C{i+1}" for i in range(n_components)]

    # Generate all possible treatment combinations (up to 2 components)
    treatments = [set()]  # Control (no components)

    # Single components
    for i in range(n_components):
        treatments.append({components[i]})

    # Pairs of components
    for i in range(n_components):
        for j in range(i + 1, n_components):
            treatments.append({components[i], components[j]})

    n_treatments = len(treatments)

    # Create component matrix
    component_matrix = np.zeros((n_treatments, n_components), dtype=int)
    for i, trt in enumerate(treatments):
        for j, comp in enumerate(components):
            if comp in trt:
                component_matrix[i, j] = 1

    # Set true parameters
    if beta_true is None:
        beta_true = np.random.uniform(-0.5, 0.5, size=n_components)

    # Generate studies comparing different treatments
    data_records = []
    study_id = 1

    # Determine which studies should be multi-arm
    n_total_studies = sum(1 for _ in range(n_treatments) for _ in range(n_treatments) if _ > 0) * n_studies_per_comparison
    n_multi_arm = int(n_total_studies * prop_multi_arm) if include_multi_arm else 0

    # Generate 2-arm comparisons (most studies)
    for base_idx in range(n_treatments):
        for comp_idx in range(base_idx + 1, n_treatments):
            # Skip if no component difference
            if np.array_equal(component_matrix[base_idx], component_matrix[comp_idx]):
                continue

            # Generate multiple studies for this comparison
            n_studies_this_comp = max(1, n_studies_per_comparison - int(n_multi_arm / 10))
            for _ in range(n_studies_this_comp):
                # Calculate true effect
                comp_diff = component_matrix[comp_idx] - component_matrix[base_idx]
                true_effect = np.dot(comp_diff, beta_true)

                # Add heterogeneity (ONE random effect per study)
                study_random_effect = np.random.normal(0, tau_true)
                study_effect = true_effect + study_random_effect

                # Sample size
                n = np.random.randint(sample_size_range[0], sample_size_range[1])
                se = np.sqrt(4.0 / n)  # Approximate SE

                # Observed effect
                y_obs = study_effect + np.random.normal(0, se)

                # Treatment names
                base_name = '+'.join(sorted(treatments[base_idx])) if treatments[base_idx] else 'Control'
                comp_name = '+'.join(sorted(treatments[comp_idx])) if treatments[comp_idx] else 'Control'

                data_records.append({
                    'study': f'Study_{study_id}',
                    'treatment_base': base_name,
                    'treatment_comp': comp_name,
                    'components_base': ','.join(sorted(treatments[base_idx])),
                    'components_comp': ','.join(sorted(treatments[comp_idx])),
                    'y': y_obs,
                    'se': se,
                    'n': n,
                })

                study_id += 1

    # Generate multi-arm trials (3-arm)
    if include_multi_arm and n_multi_arm > 0:
        for _ in range(n_multi_arm):
            # Select 3 random treatments
            selected_indices = np.random.choice(n_treatments, size=min(3, n_treatments), replace=False)
            selected_indices = sorted(selected_indices)

            if len(selected_indices) < 3:
                continue

            base_idx = selected_indices[0]

            # CRITICAL: One random effect for the entire study
            study_random_effect = np.random.normal(0, tau_true)

            # Sample size for the study (divided among arms)
            n_total = np.random.randint(sample_size_range[0] * 2, sample_size_range[1] * 2)
            n_per_arm = n_total // 3
            se_arm = np.sqrt(4.0 / n_per_arm)

            base_name = '+'.join(sorted(treatments[base_idx])) if treatments[base_idx] else 'Control'

            # Generate contrasts for arms 2 and 3 vs arm 1 (baseline)
            for comp_idx in selected_indices[1:]:
                # Calculate true effect
                comp_diff = component_matrix[comp_idx] - component_matrix[base_idx]
                true_effect = np.dot(comp_diff, beta_true)

                # SAME study random effect for all contrasts in this study
                study_effect = true_effect + study_random_effect

                # Observed effect
                y_obs = study_effect + np.random.normal(0, se_arm)

                comp_name = '+'.join(sorted(treatments[comp_idx])) if treatments[comp_idx] else 'Control'

                data_records.append({
                    'study': f'Study_{study_id}',  # Same study ID for all contrasts
                    'treatment_base': base_name,
                    'treatment_comp': comp_name,
                    'components_base': ','.join(sorted(treatments[base_idx])),
                    'components_comp': ','.join(sorted(treatments[comp_idx])),
                    'y': y_obs,
                    'se': se_arm,
                    'n': n_per_arm,
                })

            study_id += 1  # Increment once per multi-arm study

    df = pd.DataFrame(data_records)
    return df, component_matrix, components
