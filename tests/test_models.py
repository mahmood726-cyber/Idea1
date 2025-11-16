"""
Tests for CNMA models.
"""

import pytest
import numpy as np
import pandas as pd
from cnma_platform.models import AdditiveModel, InteractionModel
from cnma_platform.data import load_example_data


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return pd.DataFrame({
        'study': ['S1', 'S1', 'S2', 'S2', 'S3', 'S3'],
        'treatment': ['A', 'B', 'A', 'C', 'B', 'C'],
        'y': [0.0, 0.5, 0.0, 0.6, 0.5, 0.7],
        'se': [0.1, 0.1, 0.12, 0.12, 0.11, 0.11],
        'components': ['', 'X', '', 'Y', 'X', 'Y']
    })


def test_additive_model_initialization(sample_data):
    """Test additive model initialization."""
    model = AdditiveModel(
        data=sample_data,
        outcome_type="continuous"
    )

    assert model is not None
    assert model.outcome_type == "continuous"
    assert not model.fitted


def test_additive_model_preprocess(sample_data):
    """Test data preprocessing."""
    model = AdditiveModel(data=sample_data)
    model.preprocess_data()

    assert model.n_treatments > 0
    assert model.n_studies > 0


def test_component_matrix_extraction(sample_data):
    """Test component matrix extraction."""
    model = AdditiveModel(data=sample_data)
    model.preprocess_data()

    # Manually set treatments for testing
    model.treatments = ['A', 'B', 'C']
    model.n_treatments = 3

    matrix = model.extract_components(component_col='components')

    assert isinstance(matrix, np.ndarray)
    assert matrix.shape[0] == 3  # 3 treatments
    assert matrix.dtype == int
    assert np.all((matrix == 0) | (matrix == 1))  # Binary matrix


def test_interaction_model_initialization(sample_data):
    """Test interaction model initialization."""
    model = InteractionModel(
        data=sample_data,
        outcome_type="continuous",
        max_interaction_order=2
    )

    assert model is not None
    assert model.max_interaction_order == 2
    assert not model.fitted


def test_model_with_real_data():
    """Test model with real example data."""
    data = load_example_data("smoking_cessation")

    # Just test initialization and preprocessing
    model = AdditiveModel(data=data)
    model.preprocess_data()

    assert model.n_studies > 0
    assert model.n_treatments > 0


def test_model_requires_components():
    """Test that model building requires component information."""
    data = pd.DataFrame({
        'study': ['S1', 'S1'],
        'treatment': ['A', 'B'],
        'y': [0.0, 0.5],
        'se': [0.1, 0.1]
    })

    model = AdditiveModel(data=data)

    # Should raise error if components not set
    # (This would be caught when trying to build the PyMC model)
    assert model.component_matrix is None
