"""
Tests for data loading and validation.
"""

import pytest
import pandas as pd
import numpy as np
from cnma_platform.data import load_example_data, validate_data


def test_load_smoking_cessation_data():
    """Test loading smoking cessation example data."""
    data = load_example_data("smoking_cessation")

    assert isinstance(data, pd.DataFrame)
    assert len(data) > 0
    assert 'study' in data.columns
    assert 'treatment' in data.columns
    assert 'y' in data.columns
    assert 'se' in data.columns
    assert 'components' in data.columns


def test_load_hypertension_data():
    """Test loading hypertension example data."""
    data = load_example_data("hypertension")

    assert isinstance(data, pd.DataFrame)
    assert len(data) > 0
    assert data['study'].nunique() > 5


def test_load_depression_data():
    """Test loading depression example data."""
    data = load_example_data("depression")

    assert isinstance(data, pd.DataFrame)
    assert len(data) > 0


def test_load_invalid_dataset():
    """Test that invalid dataset name raises error."""
    with pytest.raises(ValueError):
        load_example_data("invalid_dataset")


def test_validate_data_valid():
    """Test data validation with valid data."""
    data = pd.DataFrame({
        'study': ['S1', 'S1', 'S2', 'S2'],
        'treatment': ['A', 'B', 'A', 'C'],
        'y': [0.0, 0.5, 0.0, 0.3],
        'se': [0.1, 0.1, 0.15, 0.15]
    })

    assert validate_data(data, data_format="contrast")


def test_validate_data_missing_columns():
    """Test that validation fails with missing columns."""
    data = pd.DataFrame({
        'study': ['S1', 'S1'],
        'treatment': ['A', 'B'],
        'y': [0.0, 0.5],
        # Missing 'se' column
    })

    with pytest.raises(ValueError):
        validate_data(data, data_format="contrast")


def test_validate_data_negative_se():
    """Test that validation fails with negative standard errors."""
    data = pd.DataFrame({
        'study': ['S1', 'S1'],
        'treatment': ['A', 'B'],
        'y': [0.0, 0.5],
        'se': [0.1, -0.1]  # Negative SE
    })

    with pytest.raises(ValueError):
        validate_data(data, data_format="contrast")


def test_data_structure():
    """Test that loaded data has expected structure."""
    data = load_example_data("smoking_cessation")

    # Check all standard errors are positive
    assert (data['se'] > 0).all()

    # Check no missing values in required columns
    required_cols = ['study', 'treatment', 'y', 'se']
    for col in required_cols:
        assert not data[col].isna().any()
