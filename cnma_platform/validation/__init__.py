"""
Validation and simulation studies for CNMA.
"""

from cnma_platform.validation.parameter_recovery import run_parameter_recovery_study
from cnma_platform.validation.simulation import simulate_cnma_data

__all__ = [
    "run_parameter_recovery_study",
    "simulate_cnma_data",
]
