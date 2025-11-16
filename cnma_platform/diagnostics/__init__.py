"""
Model diagnostics and inconsistency checking for CNMA.
"""

from cnma_platform.diagnostics.node_splitting import NodeSplittingAnalysis
from cnma_platform.diagnostics.consistency import check_consistency

__all__ = [
    "NodeSplittingAnalysis",
    "check_consistency",
]
