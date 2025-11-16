"""
Simplified consistency checks for CNMA using posterior predictive checks.

This module provides basic consistency assessment without the complexity of
full node-splitting. It checks whether observed data are consistent with
posterior predictions from the fitted model.

References:
    Gelman A, et al. (2013). Bayesian Data Analysis, 3rd ed. Chapter 6.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from cnma_platform.models.additive_model import AdditiveModel


class ConsistencyChecker:
    """
    Perform consistency checks using posterior predictive distributions.

    This is a simpler alternative to full node-splitting that checks whether:
    1. Observed effects fall within posterior predictive intervals
    2. Posterior predictive p-values indicate good model fit
    3. No systematic outliers suggesting inconsistency
    """

    def __init__(self, model: AdditiveModel):
        """
        Initialize consistency checker.

        Parameters
        ----------
        model : AdditiveModel
            Fitted CNMA model
        """
        if not model.fitted:
            raise ValueError("Model must be fitted before running consistency checks")

        self.model = model

    def run_posterior_predictive_checks(self) -> Dict:
        """
        Run posterior predictive checks for model consistency.

        Returns
        -------
        results : dict
            Dictionary containing:
            - outliers: DataFrame of observations outside 95% predictive interval
            - p_values: Posterior predictive p-values
            - summary: Overall assessment
        """
        # Get posterior predictive samples
        ppc_results = self.model.posterior_predictive_check()

        y_obs = ppc_results['y_obs']
        y_pred_mean = ppc_results['y_pred_mean']
        y_pred_low = ppc_results['y_pred_hdi_low']
        y_pred_high = ppc_results['y_pred_hdi_high']

        # Identify outliers (observations outside 95% predictive interval)
        outlier_mask = (y_obs < y_pred_low) | (y_obs > y_pred_high)
        n_outliers = outlier_mask.sum()
        outlier_rate = n_outliers / len(y_obs)

        # Create outlier DataFrame
        outlier_data = []
        for idx in np.where(outlier_mask)[0]:
            study = self.model.contrast_data.iloc[idx]['study']
            base_trt = self.model.contrast_data.iloc[idx]['treatment_base']
            comp_trt = self.model.contrast_data.iloc[idx]['treatment_comp']

            # Calculate standardized residual
            residual = y_obs[idx] - y_pred_mean[idx]
            pred_se = (y_pred_high[idx] - y_pred_low[idx]) / 3.92  # Approx SE from 95% CI
            std_residual = residual / pred_se if pred_se > 0 else np.nan

            outlier_data.append({
                'study': study,
                'comparison': f'{comp_trt} vs {base_trt}',
                'observed': y_obs[idx],
                'predicted': y_pred_mean[idx],
                'pred_95_low': y_pred_low[idx],
                'pred_95_high': y_pred_high[idx],
                'std_residual': std_residual,
            })

        outliers_df = pd.DataFrame(outlier_data)

        # Overall assessment
        # Expected outlier rate is ~5% under consistency
        consistency_issue = outlier_rate > 0.10  # More than 10% is concerning

        assessment = {
            'n_observations': len(y_obs),
            'n_outliers': n_outliers,
            'outlier_rate': outlier_rate,
            'expected_rate': 0.05,
            'p_value_mean': ppc_results['p_value_mean'],
            'consistent': not consistency_issue,
        }

        # Print summary
        print("\n" + "=" * 70)
        print("POSTERIOR PREDICTIVE CONSISTENCY CHECKS")
        print("=" * 70)
        print(f"\nTotal observations: {assessment['n_observations']}")
        print(f"Outliers (outside 95% PI): {assessment['n_outliers']} ({outlier_rate*100:.1f}%)")
        print(f"Expected under consistency: ~{assessment['expected_rate']*100:.1f}%")

        if consistency_issue:
            print("\n⚠ WARNING: High outlier rate suggests potential inconsistency")
            print("  Possible causes:")
            print("  - Study heterogeneity not fully captured")
            print("  - Violations of additivity assumption")
            print("  - Effect modification or interactions")
            print("  - Data quality issues")
        else:
            print("\n✓ Consistency check passed")
            print("  Outlier rate is within expected range")

        if len(outliers_df) > 0:
            print("\nOutlying observations:")
            print(outliers_df.to_string())

        return {
            'outliers': outliers_df,
            'assessment': assessment,
            'ppc_results': ppc_results,
        }

    def check_comparison_consistency(
        self,
        treatment_base: str,
        treatment_comp: str
    ) -> Dict:
        """
        Check consistency for a specific treatment comparison.

        Parameters
        ----------
        treatment_base : str
            Baseline treatment
        treatment_comp : str
            Comparison treatment

        Returns
        -------
        results : dict
            Consistency results for this comparison
        """
        # Filter to this comparison
        mask = (
            (self.model.contrast_data['treatment_base'] == treatment_base) &
            (self.model.contrast_data['treatment_comp'] == treatment_comp)
        )

        if mask.sum() == 0:
            raise ValueError(f"No direct evidence for {treatment_comp} vs {treatment_base}")

        # Get observed values
        y_obs = self.model.contrast_data.loc[mask, 'y'].values

        # Get model prediction
        pred = self.model.predict(treatment_base, treatment_comp, return_samples=True)

        # Calculate consistency
        samples = pred['samples']
        pred_mean = pred['mean']
        pred_low = np.percentile(samples, 2.5)
        pred_high = np.percentile(samples, 97.5)

        # Check if observed values are consistent with prediction
        consistent_obs = []
        for y in y_obs:
            # Posterior predictive probability
            prob_more_extreme = np.minimum(
                (samples >= y).mean(),
                (samples <= y).mean()
            ) * 2
            consistent_obs.append(prob_more_extreme > 0.05)

        results = {
            'comparison': f'{treatment_comp} vs {treatment_base}',
            'n_studies': len(y_obs),
            'observed_mean': y_obs.mean(),
            'predicted_mean': pred_mean,
            'predicted_95_ci': (pred_low, pred_high),
            'all_consistent': all(consistent_obs),
            'n_consistent': sum(consistent_obs),
        }

        print(f"\nConsistency check: {treatment_comp} vs {treatment_base}")
        print(f"  Direct evidence: {results['n_studies']} studies")
        print(f"  Observed mean: {results['observed_mean']:.3f}")
        print(f"  Model prediction: {results['predicted_mean']:.3f} ({pred_low:.3f}, {pred_high:.3f})")
        print(f"  Consistent: {results['n_consistent']}/{results['n_studies']}")

        return results


def run_basic_consistency_checks(model: AdditiveModel) -> Dict:
    """
    Run basic consistency checks on a fitted CNMA model.

    This is a simplified alternative to full node-splitting analysis.

    Parameters
    ----------
    model : AdditiveModel
        Fitted additive CNMA model

    Returns
    -------
    results : dict
        Consistency check results
    """
    checker = ConsistencyChecker(model)
    results = checker.run_posterior_predictive_checks()

    print("\n" + "=" * 70)
    print("CONSISTENCY ASSESSMENT")
    print("=" * 70)

    if results['assessment']['consistent']:
        print("\n✓ Model shows good consistency with observed data")
        print("\nNo major concerns identified.")
    else:
        print("\n⚠ Potential consistency issues detected")
        print("\nRecommendations:")
        print("  1. Review outlying studies for data quality")
        print("  2. Consider interaction model if components may interact")
        print("  3. Check for effect modifiers (study characteristics)")
        print("  4. Assess heterogeneity and consider meta-regression")

    return results
