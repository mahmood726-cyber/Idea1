"""
Component Network Meta-Analysis Platform

A comprehensive Python platform for analyzing multi-component interventions
using Component Network Meta-Analysis (CNMA) methods.
"""

__version__ = "0.1.0"

from cnma_platform.models.additive_model import AdditiveModel
from cnma_platform.models.interaction_model import InteractionModel
from cnma_platform.analysis import CNMAAnalysis

__all__ = [
    "AdditiveModel",
    "InteractionModel",
    "CNMAAnalysis",
    "__version__",
]
