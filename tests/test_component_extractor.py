"""
Tests for NLP component extraction.
"""

import pytest
import numpy as np
import pandas as pd
from cnma_platform.nlp import ComponentExtractor, TextPreprocessor


def test_text_preprocessor_clean():
    """Test text cleaning."""
    preprocessor = TextPreprocessor(lowercase=True)

    text = "  This is   a TEST  "
    cleaned = preprocessor.clean_text(text)

    assert cleaned == "this is a test"
    assert not cleaned.startswith(" ")
    assert not cleaned.endswith(" ")


def test_text_preprocessor_tokenize():
    """Test tokenization."""
    preprocessor = TextPreprocessor()

    text = "cognitive behavioral therapy"
    tokens = preprocessor.tokenize(text)

    assert isinstance(tokens, list)
    assert len(tokens) > 0
    assert "cognitive" in tokens
    assert "behavioral" in tokens


def test_component_extractor_keyword():
    """Test keyword-based component extraction."""
    extractor = ComponentExtractor(domain="behavioral", min_component_freq=1)

    descriptions = [
        "cognitive behavioral therapy with exercise",
        "medication management",
        "cbt plus group support",
    ]

    intervention_comps, all_comps = extractor.extract_components(
        descriptions, method="keyword"
    )

    assert isinstance(intervention_comps, list)
    assert isinstance(all_comps, list)
    assert len(intervention_comps) == len(descriptions)
    assert len(all_comps) > 0


def test_component_extractor_tfidf():
    """Test TF-IDF component extraction."""
    extractor = ComponentExtractor(domain="general", min_component_freq=1)

    descriptions = [
        "therapy with medication",
        "exercise program",
        "therapy plus exercise",
    ]

    intervention_comps, all_comps = extractor.extract_components(
        descriptions, method="tfidf"
    )

    assert len(intervention_comps) == len(descriptions)
    assert len(all_comps) > 0


def test_component_extractor_hybrid():
    """Test hybrid component extraction."""
    extractor = ComponentExtractor(domain="behavioral", min_component_freq=1)

    descriptions = [
        "cognitive behavioral therapy",
        "cbt with medication",
        "exercise and diet",
    ]

    intervention_comps, all_comps = extractor.extract_components(
        descriptions, method="hybrid"
    )

    assert len(intervention_comps) == len(descriptions)
    assert all(isinstance(comps, set) for comps in intervention_comps)


def test_create_component_matrix():
    """Test creation of component matrix."""
    extractor = ComponentExtractor(domain="general")

    intervention_comps = [
        {'A', 'B'},
        {'A'},
        {'B', 'C'},
    ]
    all_comps = ['A', 'B', 'C']

    matrix = extractor.create_component_matrix(intervention_comps, all_comps)

    assert isinstance(matrix, pd.DataFrame)
    assert matrix.shape == (3, 3)
    assert matrix.iloc[0, 0] == 1  # Intervention 1 has component A
    assert matrix.iloc[0, 1] == 1  # Intervention 1 has component B
    assert matrix.iloc[1, 1] == 0  # Intervention 2 doesn't have component B


def test_normalize_component_name():
    """Test component name normalization."""
    preprocessor = TextPreprocessor()

    # Test various normalizations
    assert preprocessor.normalize_component_name("CBT") == "cbt"
    assert preprocessor.normalize_component_name("  exercise  ") == "exercise"
