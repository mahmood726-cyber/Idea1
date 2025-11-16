"""
Consistency checking utilities for CNMA.
"""

from typing import Dict, Any
import numpy as np
import pandas as pd


def check_consistency(
    data: pd.DataFrame,
    fitted_model: Any,
    threshold: float = 0.05
) -> Dict[str, Any]:
    """
    Perform basic consistency checks on CNMA results.

    Parameters
    ----------
    data : pd.DataFrame
        Original data
    fitted_model : AdditiveModel or InteractionModel
        Fitted CNMA model
    threshold : float
        Significance threshold for inconsistency

    Returns
    -------
    results : dict
        Consistency check results
    """
    # Get posterior predictive checks
    ppc = fitted_model.posterior_predictive_check()

    # Check if observations fall within credible intervals
    y_obs = ppc['y_obs']
    y_pred_low = ppc['y_pred_hdi_low']
    y_pred_high = ppc['y_pred_hdi_high']

    # Count observations outside 95% HDI
    outside_hdi = ((y_obs < y_pred_low) | (y_obs > y_pred_high)).sum()
    prop_outside = outside_hdi / len(y_obs)

    # Expected proportion outside 95% HDI is 0.05
    potential_inconsistency = prop_outside > 0.15  # More than 3x expected

    results = {
        'n_observations': len(y_obs),
        'n_outside_hdi': int(outside_hdi),
        'proportion_outside_hdi': prop_outside,
        'expected_proportion': 0.05,
        'potential_inconsistency': potential_inconsistency,
        'p_value_mean': ppc['p_value_mean'],
    }

    if potential_inconsistency:
        results['warning'] = (
            f"Potential inconsistency detected: {prop_outside:.1%} of observations "
            f"fall outside 95% credible intervals (expected ~5%). "
            f"Consider node-splitting analysis."
        )

    return results
