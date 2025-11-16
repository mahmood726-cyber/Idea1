"""
Data management and utilities for CNMA.
"""

from cnma_platform.data.data_loader import load_example_data, validate_data
from cnma_platform.data.network_builder import NetworkBuilder

__all__ = [
    "load_example_data",
    "validate_data",
    "NetworkBuilder",
]
