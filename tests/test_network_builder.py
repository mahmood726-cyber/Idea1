"""
Tests for network construction.
"""

import pytest
import pandas as pd
import networkx as nx
from cnma_platform.data import NetworkBuilder


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    return pd.DataFrame({
        'study': ['S1', 'S1', 'S2', 'S2', 'S3', 'S3'],
        'treatment': ['A', 'B', 'A', 'C', 'B', 'C'],
        'y': [0.0, 0.5, 0.0, 0.6, 0.5, 0.7],
        'se': [0.1, 0.1, 0.12, 0.12, 0.11, 0.11]
    })


def test_network_builder_initialization(sample_data):
    """Test network builder initialization."""
    builder = NetworkBuilder(sample_data)

    assert builder is not None
    assert builder.data is not None


def test_build_treatment_network(sample_data):
    """Test building treatment network."""
    builder = NetworkBuilder(sample_data)
    network = builder.build_treatment_network()

    assert isinstance(network, nx.Graph)
    assert network.number_of_nodes() == 3  # A, B, C
    assert network.number_of_edges() > 0


def test_network_stats(sample_data):
    """Test network statistics calculation."""
    builder = NetworkBuilder(sample_data)
    network = builder.build_treatment_network()
    stats = builder.get_network_stats(network)

    assert 'n_nodes' in stats
    assert 'n_edges' in stats
    assert 'density' in stats
    assert stats['n_nodes'] == 3
    assert stats['density'] >= 0 and stats['density'] <= 1


def test_check_connectivity(sample_data):
    """Test network connectivity check."""
    builder = NetworkBuilder(sample_data)
    builder.build_treatment_network()

    connectivity = builder.check_network_connectivity()

    assert 'connected' in connectivity
    assert 'n_nodes' in connectivity
    assert 'n_edges' in connectivity


def test_component_network():
    """Test building component network."""
    component_matrix = pd.DataFrame({
        'X': [1, 0, 1],
        'Y': [0, 1, 1],
        'Z': [0, 1, 0]
    })

    builder = NetworkBuilder(pd.DataFrame())
    network = builder.build_component_network(component_matrix)

    assert isinstance(network, nx.Graph)
    assert network.number_of_nodes() == 3  # X, Y, Z
    # X and Y co-occur in treatment 3
    assert network.has_edge('X', 'Y')


def test_treatment_complexity():
    """Test treatment complexity calculation."""
    component_matrix = pd.DataFrame({
        'X': [1, 0, 1],
        'Y': [0, 1, 1],
        'Z': [0, 1, 1]
    }, index=['T1', 'T2', 'T3'])

    builder = NetworkBuilder(pd.DataFrame())
    complexity = builder.calculate_treatment_complexity(component_matrix)

    assert isinstance(complexity, pd.DataFrame)
    assert 'treatment' in complexity.columns
    assert 'n_components' in complexity.columns
    assert 'complexity' in complexity.columns
    assert len(complexity) == 3
