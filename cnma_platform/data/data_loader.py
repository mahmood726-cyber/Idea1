"""
Data loading and validation utilities.
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
        Format: 'contrast' (pairwise comparisons) or 'arm' (arm-level data)
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
            required_cols = ['study', 'treatment', 'y', 'se']

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
        Example dataset
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
    Create synthetic smoking cessation CNMA dataset.

    Components:
    - NRT (Nicotine Replacement Therapy)
    - Counseling
    - Group Support
    - Self-help Materials

    Returns
    -------
    data : pd.DataFrame
        Synthetic dataset
    """
    np.random.seed(42)

    # Define treatments and their components
    treatments = {
        'Control': [],
        'NRT': ['NRT'],
        'Counseling': ['Counseling'],
        'Self-help': ['Self-help'],
        'NRT + Counseling': ['NRT', 'Counseling'],
        'NRT + Self-help': ['NRT', 'Self-help'],
        'Counseling + Group': ['Counseling', 'Group Support'],
        'NRT + Counseling + Group': ['NRT', 'Counseling', 'Group Support'],
    }

    # Component effects (log odds ratios)
    beta_true = {
        'NRT': 0.6,
        'Counseling': 0.5,
        'Self-help': 0.3,
        'Group Support': 0.4,
    }

    # Generate synthetic data
    data_records = []
    study_id = 1

    # Generate studies comparing different treatment combinations
    comparisons = [
        ('Control', 'NRT'),
        ('Control', 'Counseling'),
        ('Control', 'NRT + Counseling'),
        ('NRT', 'NRT + Counseling'),
        ('Counseling', 'Counseling + Group'),
        ('Control', 'Self-help'),
        ('NRT', 'NRT + Self-help'),
        ('Control', 'NRT + Counseling + Group'),
        ('NRT + Counseling', 'NRT + Counseling + Group'),
    ]

    for trt1, trt2 in comparisons:
        # Generate 3-5 studies for each comparison
        n_studies = np.random.randint(3, 6)

        for _ in range(n_studies):
            # Calculate true effect based on component differences
            comps1 = set(treatments[trt1])
            comps2 = set(treatments[trt2])
            comp_diff = comps2 - comps1

            true_effect = sum(beta_true.get(c, 0) for c in comp_diff) - \
                         sum(beta_true.get(c, 0) for c in (comps1 - comps2))

            # Add between-study heterogeneity
            tau = 0.15
            study_effect = true_effect + np.random.normal(0, tau)

            # Sampling variance depends on sample size
            n = np.random.randint(100, 500)
            se = np.sqrt(4.0 / n)  # Approximate for log OR

            # Observed effect
            y_obs = study_effect + np.random.normal(0, se)

            data_records.append({
                'study': f'Study_{study_id}',
                'treatment_1': trt1,
                'treatment_2': trt2,
                'y': y_obs,
                'se': se,
                'n': n,
            })

            study_id += 1

    df = pd.DataFrame(data_records)

    # Add component information
    def get_components(row):
        comps1 = treatments[row['treatment_1']]
        comps2 = treatments[row['treatment_2']]
        return ','.join(comps1), ','.join(comps2)

    df[['components_1', 'components_2']] = df.apply(
        get_components, axis=1, result_type='expand'
    )

    # Convert to long format (one row per treatment arm)
    long_data = []
    for idx, row in df.iterrows():
        # Control arm
        long_data.append({
            'study': row['study'],
            'treatment': row['treatment_1'],
            'components': row['components_1'],
            'y': 0,  # Reference
            'se': row['se'],
            'n': row['n'] // 2,
        })

        # Treatment arm
        long_data.append({
            'study': row['study'],
            'treatment': row['treatment_2'],
            'components': row['components_2'],
            'y': row['y'],
            'se': row['se'],
            'n': row['n'] // 2,
        })

    return pd.DataFrame(long_data)


def _create_hypertension_data() -> pd.DataFrame:
    """
    Create synthetic hypertension intervention dataset.

    Returns
    -------
    data : pd.DataFrame
        Synthetic dataset
    """
    np.random.seed(123)

    treatments = {
        'Control': [],
        'Diet': ['Diet'],
        'Exercise': ['Exercise'],
        'Medication': ['Medication'],
        'Diet + Exercise': ['Diet', 'Exercise'],
        'Diet + Medication': ['Diet', 'Medication'],
        'Exercise + Medication': ['Exercise', 'Medication'],
        'Diet + Exercise + Medication': ['Diet', 'Exercise', 'Medication'],
    }

    beta_true = {
        'Diet': -5.0,
        'Exercise': -4.0,
        'Medication': -8.0,
    }

    data_records = []
    study_id = 1

    for trt in treatments.keys():
        if trt == 'Control':
            continue

        n_studies = np.random.randint(4, 8)

        for _ in range(n_studies):
            comps = set(treatments[trt])
            true_effect = sum(beta_true.get(c, 0) for c in comps)

            tau = 2.0
            study_effect = true_effect + np.random.normal(0, tau)

            n = np.random.randint(50, 200)
            se = 15.0 / np.sqrt(n)

            y_obs = study_effect + np.random.normal(0, se)

            data_records.append({
                'study': f'Study_{study_id}',
                'treatment': trt,
                'components': ','.join(treatments[trt]),
                'y': y_obs,
                'se': se,
                'n': n,
            })

            study_id += 1

    return pd.DataFrame(data_records)


def _create_depression_data() -> pd.DataFrame:
    """
    Create synthetic depression intervention dataset.

    Returns
    -------
    data : pd.DataFrame
        Synthetic dataset
    """
    np.random.seed(456)

    treatments = {
        'Waitlist': [],
        'CBT': ['CBT'],
        'Medication': ['Medication'],
        'Exercise': ['Exercise'],
        'CBT + Medication': ['CBT', 'Medication'],
        'CBT + Exercise': ['CBT', 'Exercise'],
    }

    beta_true = {
        'CBT': -0.7,
        'Medication': -0.6,
        'Exercise': -0.4,
    }

    data_records = []
    study_id = 1

    comparisons = [
        ('Waitlist', 'CBT'),
        ('Waitlist', 'Medication'),
        ('Waitlist', 'Exercise'),
        ('Waitlist', 'CBT + Medication'),
        ('CBT', 'CBT + Medication'),
        ('Waitlist', 'CBT + Exercise'),
    ]

    for trt1, trt2 in comparisons:
        n_studies = np.random.randint(3, 6)

        for _ in range(n_studies):
            comps1 = set(treatments[trt1])
            comps2 = set(treatments[trt2])
            comp_diff = comps2 - comps1

            true_effect = sum(beta_true.get(c, 0) for c in comp_diff)

            tau = 0.2
            study_effect = true_effect + np.random.normal(0, tau)

            n = np.random.randint(80, 300)
            se = 1.5 / np.sqrt(n)

            y_obs = study_effect + np.random.normal(0, se)

            for trt, comps in [(trt1, comps1), (trt2, comps2)]:
                data_records.append({
                    'study': f'Study_{study_id}',
                    'treatment': trt,
                    'components': ','.join(treatments[trt]),
                    'y': y_obs if trt == trt2 else 0,
                    'se': se,
                    'n': n // 2,
                })

            study_id += 1

    return pd.DataFrame(data_records)
