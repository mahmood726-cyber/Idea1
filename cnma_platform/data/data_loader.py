"""
Data loading and validation utilities.

This module provides functions for loading example datasets and validating
CNMA data formats. Data can be in contrast-based or arm-based format.
"""

from typing import Dict, Optional, List
import pandas as pd
import numpy as np


def validate_data(
    data: pd.DataFrame,
    data_format: str = "contrast",
    required_cols: Optional[List[str]] = None
) -> bool:
    """
    Validate CNMA dataset format.

    Parameters
    ----------
    data : pd.DataFrame
        Dataset to validate
    data_format : str
        Format: 'contrast' (pairwise comparisons) or 'arm' (arm-based data)
    required_cols : list, optional
        Required column names

    Returns
    -------
    valid : bool
        Whether data is valid

    Raises
    ------
    ValueError
        If data is invalid
    """
    if data_format == "contrast":
        if required_cols is None:
            required_cols = ['study', 'treatment_base', 'treatment_comp', 'y', 'se']

        missing = [col for col in required_cols if col not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Check for missing values
        for col in required_cols:
            if data[col].isna().any():
                raise ValueError(f"Column '{col}' contains missing values")

        # Check standard errors are positive
        if 'se' in data.columns:
            if (data['se'] <= 0).any():
                raise ValueError("Standard errors must be positive")

    elif data_format == "arm":
        if required_cols is None:
            required_cols = ['study', 'arm', 'treatment', 'y', 'se']

        missing = [col for col in required_cols if col not in data.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Check each study has at least 2 arms
        arms_per_study = data.groupby('study')['arm'].nunique()
        if (arms_per_study < 2).any():
            invalid_studies = arms_per_study[arms_per_study < 2].index.tolist()
            raise ValueError(f"Studies with < 2 arms: {invalid_studies}")

    else:
        raise ValueError(f"Unknown data format: {data_format}")

    return True


def load_example_data(dataset: str = "smoking_cessation") -> pd.DataFrame:
    """
    Load example dataset for CNMA.

    Parameters
    ----------
    dataset : str
        Dataset name: 'smoking_cessation', 'hypertension', 'depression'

    Returns
    -------
    data : pd.DataFrame
        Example dataset in contrast-based format
    """
    if dataset == "smoking_cessation":
        return _create_smoking_cessation_data()
    elif dataset == "hypertension":
        return _create_hypertension_data()
    elif dataset == "depression":
        return _create_depression_data()
    else:
        raise ValueError(f"Unknown dataset: {dataset}")


def _create_smoking_cessation_data() -> pd.DataFrame:
    """
    Create synthetic smoking cessation CNMA dataset with realistic features.

    Components:
    - NRT (Nicotine Replacement Therapy)
    - Counseling
    - Group Support
    - Self-help Materials

    This includes:
    - Additive AND interaction effects
    - Multi-arm trials
    - Between-study heterogeneity
    - Realistic sample sizes

    Returns
    -------
    data : pd.DataFrame
        Synthetic dataset in contrast-based format
    """
    np.random.seed(42)

    # Define treatments and their components
    treatments = {
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

    # TRUE parameter values for simulation
    # Main (additive) component effects (log odds ratios)
    beta_true = {
        'NRT': 0.55,
        'Counseling': 0.48,
        'Self-help': 0.25,
        'Group Support': 0.38,
    }

    # Interaction effects (synergies/antagonisms)
    # NOTE: These interaction effects are INTENTIONALLY included to test
    # robustness of the additive model to violations of the additivity assumption.
    # When fitting an additive model to this data:
    # - Component effects (β) will be estimated with slight bias
    # - This demonstrates real-world scenario where additivity may not hold perfectly
    # - For analyses where strong interactions are expected, use InteractionModel instead
    # - This serves as a model misspecification test in validation studies
    gamma_true = {
        ('NRT', 'Counseling'): 0.15,  # Positive synergy
        ('Counseling', 'Group Support'): -0.08,  # Slight antagonism
    }

    # Between-study heterogeneity
    tau_true = 0.12

    # Generate studies
    data_records = []
    study_id = 1

    # Two-arm studies (most common)
    two_arm_comparisons = [
        ('Control', 'NRT'),
        ('Control', 'Counseling'),
        ('Control', 'NRT + Counseling'),
        ('Control', 'Self-help'),
        ('NRT', 'NRT + Counseling'),
        ('Counseling', 'Counseling + Group'),
        ('NRT', 'NRT + Self-help'),
        ('Control', 'Group Support'),
        ('Control', 'Counseling + Group'),
    ]

    for base_trt, comp_trt in two_arm_comparisons:
        # Generate 4-7 studies for each comparison
        n_studies = np.random.randint(4, 8)

        for _ in range(n_studies):
            # Calculate true effect
            effect = _calculate_true_effect(
                treatments[base_trt],
                treatments[comp_trt],
                beta_true,
                gamma_true
            )

            # Add between-study heterogeneity
            study_effect = effect + np.random.normal(0, tau_true)

            # Sample size varies
            n_total = np.random.randint(100, 600)
            se = np.sqrt(4.0 / n_total)  # Approximate SE for log OR

            # Observed effect
            y_obs = study_effect + np.random.normal(0, se)

            data_records.append({
                'study': f'Study_{study_id}',
                'treatment_base': base_trt,
                'treatment_comp': comp_trt,
                'components_base': ','.join(sorted(treatments[base_trt])) if treatments[base_trt] else '',
                'components_comp': ','.join(sorted(treatments[comp_trt])) if treatments[comp_trt] else '',
                'y': y_obs,
                'se': se,
                'n': n_total,
            })

            study_id += 1

    # Multi-arm studies (3-arm)
    three_arm_studies = [
        ('Control', 'NRT', 'Counseling'),
        ('Control', 'NRT', 'NRT + Counseling'),
        ('NRT', 'Counseling', 'NRT + Counseling'),
        ('Control', 'Counseling', 'Counseling + Group'),
        ('Control', 'NRT + Counseling', 'NRT + Counseling + Group'),
    ]

    for arms in three_arm_studies:
        # Generate 2-3 three-arm studies for each combination
        n_studies = np.random.randint(2, 4)

        for _ in range(n_studies):
            base_trt = arms[0]  # First arm is baseline

            n_total = np.random.randint(150, 500)
            se_base = np.sqrt(4.0 / (n_total / 3))

            for comp_trt in arms[1:]:
                # Calculate effect
                effect = _calculate_true_effect(
                    treatments[base_trt],
                    treatments[comp_trt],
                    beta_true,
                    gamma_true
                )

                study_effect = effect + np.random.normal(0, tau_true)
                se = se_base
                y_obs = study_effect + np.random.normal(0, se)

                data_records.append({
                    'study': f'Study_{study_id}',
                    'treatment_base': base_trt,
                    'treatment_comp': comp_trt,
                    'components_base': ','.join(sorted(treatments[base_trt])) if treatments[base_trt] else '',
                    'components_comp': ','.join(sorted(treatments[comp_trt])) if treatments[comp_trt] else '',
                    'y': y_obs,
                    'se': se,
                    'n': n_total // 3,
                })

            study_id += 1

    df = pd.DataFrame(data_records)

    # Add true parameters as metadata (for validation)
    df.attrs['beta_true'] = beta_true
    df.attrs['gamma_true'] = gamma_true
    df.attrs['tau_true'] = tau_true

    return df


def _calculate_true_effect(
    components_base: set,
    components_comp: set,
    beta: Dict[str, float],
    gamma: Dict[tuple, float]
) -> float:
    """
    Calculate true treatment effect including additive and interaction terms.

    Parameters
    ----------
    components_base : set
        Components in baseline treatment
    components_comp : set
        Components in comparison treatment
    beta : dict
        Additive component effects
    gamma : dict
        Interaction effects (keyed by component pairs)

    Returns
    -------
    effect : float
        True treatment effect (comparison vs baseline)
    """
    effect = 0.0

    # Additive effects
    comp_diff = components_comp - components_base
    for comp in comp_diff:
        effect += beta.get(comp, 0)

    # Interaction effects (only for components present together in comparison)
    for (c1, c2), interaction in gamma.items():
        # Interaction is active if both components are in comparison
        in_comp = (c1 in components_comp) and (c2 in components_comp)
        in_base = (c1 in components_base) and (c2 in components_base)

        if in_comp and not in_base:
            effect += interaction
        elif in_base and not in_comp:
            effect -= interaction

    return effect


def _create_hypertension_data() -> pd.DataFrame:
    """
    Create synthetic hypertension intervention dataset.

    Components: Diet, Exercise, Medication
    Outcome: Blood pressure reduction (mmHg)

    Returns
    -------
    data : pd.DataFrame
        Synthetic dataset in contrast format
    """
    np.random.seed(123)

    treatments = {
        'Control': set(),
        'Diet': {'Diet'},
        'Exercise': {'Exercise'},
        'Medication': {'Medication'},
        'Diet + Exercise': {'Diet', 'Exercise'},
        'Diet + Medication': {'Diet', 'Medication'},
        'Exercise + Medication': {'Exercise', 'Medication'},
        'Diet + Exercise + Medication': {'Diet', 'Exercise', 'Medication'},
    }

    # True effects (mmHg reduction)
    beta_true = {
        'Diet': -4.5,
        'Exercise': -3.8,
        'Medication': -8.2,
    }

    # Interaction effect (intentional - see smoking_cessation for explanation)
    gamma_true = {
        ('Diet', 'Exercise'): -1.2,  # Small synergy
    }

    tau_true = 1.5

    data_records = []
    study_id = 1

    comparisons = [
        ('Control', 'Diet'),
        ('Control', 'Exercise'),
        ('Control', 'Medication'),
        ('Control', 'Diet + Exercise'),
        ('Control', 'Diet + Medication'),
        ('Control', 'Exercise + Medication'),
        ('Diet', 'Diet + Exercise'),
        ('Exercise', 'Exercise + Medication'),
        ('Medication', 'Diet + Medication'),
        ('Control', 'Diet + Exercise + Medication'),
    ]

    for base_trt, comp_trt in comparisons:
        n_studies = np.random.randint(3, 7)

        for _ in range(n_studies):
            effect = _calculate_true_effect(
                treatments[base_trt],
                treatments[comp_trt],
                beta_true,
                gamma_true
            )

            study_effect = effect + np.random.normal(0, tau_true)

            n = np.random.randint(50, 200)
            se = 12.0 / np.sqrt(n)  # SE for blood pressure
            y_obs = study_effect + np.random.normal(0, se)

            data_records.append({
                'study': f'HTN_Study_{study_id}',
                'treatment_base': base_trt,
                'treatment_comp': comp_trt,
                'components_base': ','.join(sorted(treatments[base_trt])) if treatments[base_trt] else '',
                'components_comp': ','.join(sorted(treatments[comp_trt])) if treatments[comp_trt] else '',
                'y': y_obs,
                'se': se,
                'n': n,
            })

            study_id += 1

    df = pd.DataFrame(data_records)
    df.attrs['beta_true'] = beta_true
    df.attrs['gamma_true'] = gamma_true
    df.attrs['tau_true'] = tau_true

    return df


def _create_depression_data() -> pd.DataFrame:
    """
    Create synthetic depression intervention dataset.

    Components: CBT, Medication, Exercise
    Outcome: Standardized mean difference in depression scores

    Returns
    -------
    data : pd.DataFrame
        Synthetic dataset in contrast format
    """
    np.random.seed(456)

    treatments = {
        'Waitlist': set(),
        'CBT': {'CBT'},
        'Medication': {'Medication'},
        'Exercise': {'Exercise'},
        'CBT + Medication': {'CBT', 'Medication'},
        'CBT + Exercise': {'CBT', 'Exercise'},
        'Medication + Exercise': {'Medication', 'Exercise'},
    }

    # True effects (negative = improvement)
    beta_true = {
        'CBT': -0.68,
        'Medication': -0.62,
        'Exercise': -0.42,
    }

    # Interaction effect (intentional - see smoking_cessation for explanation)
    gamma_true = {
        ('CBT', 'Medication'): -0.10,  # Small synergy
    }

    tau_true = 0.18

    data_records = []
    study_id = 1

    comparisons = [
        ('Waitlist', 'CBT'),
        ('Waitlist', 'Medication'),
        ('Waitlist', 'Exercise'),
        ('Waitlist', 'CBT + Medication'),
        ('Waitlist', 'CBT + Exercise'),
        ('Waitlist', 'Medication + Exercise'),
        ('CBT', 'CBT + Medication'),
        ('CBT', 'CBT + Exercise'),
        ('Medication', 'CBT + Medication'),
    ]

    for base_trt, comp_trt in comparisons:
        n_studies = np.random.randint(4, 8)

        for _ in range(n_studies):
            effect = _calculate_true_effect(
                treatments[base_trt],
                treatments[comp_trt],
                beta_true,
                gamma_true
            )

            study_effect = effect + np.random.normal(0, tau_true)

            n = np.random.randint(80, 300)
            se = 1.4 / np.sqrt(n)  # SE for SMD
            y_obs = study_effect + np.random.normal(0, se)

            data_records.append({
                'study': f'DEP_Study_{study_id}',
                'treatment_base': base_trt,
                'treatment_comp': comp_trt,
                'components_base': ','.join(sorted(treatments[base_trt])) if treatments[base_trt] else '',
                'components_comp': ','.join(sorted(treatments[comp_trt])) if treatments[comp_trt] else '',
                'y': y_obs,
                'se': se,
                'n': n,
            })

            study_id += 1

    # Add some 3-arm trials
    three_arm_combos = [
        ('Waitlist', 'CBT', 'Medication'),
        ('Waitlist', 'CBT', 'CBT + Medication'),
        ('Waitlist', 'Exercise', 'CBT + Exercise'),
    ]

    for arms in three_arm_combos:
        n_studies = 2

        for _ in range(n_studies):
            base_trt = arms[0]
            n_total = np.random.randint(150, 400)

            for comp_trt in arms[1:]:
                effect = _calculate_true_effect(
                    treatments[base_trt],
                    treatments[comp_trt],
                    beta_true,
                    gamma_true
                )

                study_effect = effect + np.random.normal(0, tau_true)
                se = 1.4 / np.sqrt(n_total / 3)
                y_obs = study_effect + np.random.normal(0, se)

                data_records.append({
                    'study': f'DEP_Study_{study_id}',
                    'treatment_base': base_trt,
                    'treatment_comp': comp_trt,
                    'components_base': ','.join(sorted(treatments[base_trt])) if treatments[base_trt] else '',
                    'components_comp': ','.join(sorted(treatments[comp_trt])) if treatments[comp_trt] else '',
                    'y': y_obs,
                    'se': se,
                    'n': n_total // 3,
                })

            study_id += 1

    df = pd.DataFrame(data_records)
    df.attrs['beta_true'] = beta_true
    df.attrs['gamma_true'] = gamma_true
    df.attrs['tau_true'] = tau_true

    return df
