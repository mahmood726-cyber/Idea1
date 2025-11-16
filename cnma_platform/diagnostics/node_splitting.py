"""
Node-splitting for assessing consistency in CNMA.

Node-splitting (Dias et al., 2010) compares direct and indirect evidence
for specific treatment comparisons to assess network consistency.

References:
    Dias, S., et al. (2010). Checking consistency in mixed treatment comparison
    meta-analysis. Statistics in Medicine, 29(7-8), 932-944.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from cnma_platform.models.additive_model import AdditiveModel


class NodeSplittingAnalysis:
    """
    Perform node-splitting analysis to assess consistency.

    For each comparison with both direct and indirect evidence, this fits two models:
    1. Consistency model: assumes consistency between direct and indirect evidence
    2. Inconsistency model: allows different estimates for direct vs indirect evidence

    The difference (inconsistency factor) indicates potential inconsistency.
    """

    def __init__(self, data: pd.DataFrame, component_matrix: np.ndarray, components: List[str]):
        """
        Initialize node-splitting analysis.

        Parameters
        ----------
        data : pd.DataFrame
            Contrast-based dataset
        component_matrix : np.ndarray
            Component presence matrix
        components : list
            List of component names
        """
        self.data = data
        self.component_matrix = component_matrix
        self.components = components

        # Identify comparisons with direct evidence
        self.direct_comparisons = self._identify_direct_comparisons()

    def _identify_direct_comparisons(self) -> List[Tuple[str, str]]:
        """
        Identify treatment comparisons with direct evidence.

        Returns
        -------
        comparisons : list
            List of (treatment_base, treatment_comp) tuples with direct evidence
        """
        comparisons = []

        for _, row in self.data.iterrows():
            comp = (row['treatment_base'], row['treatment_comp'])
            if comp not in comparisons:
                comparisons.append(comp)

        return comparisons

    def run_node_splitting(
        self,
        comparison: Tuple[str, str],
        n_samples: int = 2000,
        n_warmup: int = 1000,
        n_chains: int = 4
    ) -> Dict:
        """
        Perform node-splitting for a specific comparison.

        Parameters
        ----------
        comparison : tuple
            (treatment_base, treatment_comp) to test
        n_samples : int
            MCMC samples
        n_warmup : int
            Warmup samples
        n_chains : int
            Number of chains

        Returns
        -------
        results : dict
            Node-splitting results including direct, indirect estimates and inconsistency factor
        """
        base_trt, comp_trt = comparison

        # Split data into direct and indirect
        direct_mask = (self.data['treatment_base'] == base_trt) & (self.data['treatment_comp'] == comp_trt)
        direct_data = self.data[direct_mask].copy()
        indirect_data = self.data[~direct_mask].copy()

        if len(direct_data) == 0:
            raise ValueError(f"No direct evidence for comparison {comparison}")

        if len(indirect_data) == 0:
            raise ValueError(f"No indirect evidence for comparison {comparison}")

        # Fit model using only indirect evidence
        print(f"\nFitting indirect evidence model for {comp_trt} vs {base_trt}...")
        indirect_model = AdditiveModel(
            data=indirect_data,
            data_format="contrast"
        )
        indirect_model.components = self.components
        indirect_model.component_matrix = self.component_matrix
        indirect_model.n_components = len(self.components)

        indirect_results = indirect_model.fit(
            n_samples=n_samples,
            n_warmup=n_warmup,
            n_chains=n_chains
        )

        # Get indirect estimate
        indirect_est = indirect_model.predict(base_trt, comp_trt)

        # Fit model using only direct evidence
        print(f"\nFitting direct evidence model...")
        # Direct evidence: just meta-analyze the direct comparisons
        direct_y = direct_data['y'].values
        direct_se = direct_data['se'].values

        with pm.Model() as direct_model_pm:
            # Pooled direct effect
            theta_direct = pm.Normal('theta_direct', mu=0, sigma=2)

            # Between-study heterogeneity
            tau = pm.HalfNormal('tau', sigma=1)

            # Study-specific effects
            delta = pm.Normal('delta', mu=theta_direct, sigma=tau, shape=len(direct_y))

            # Likelihood
            y = pm.Normal('y', mu=delta, sigma=direct_se, observed=direct_y)

            # Sample
            direct_trace = pm.sample(
                draws=n_samples,
                tune=n_warmup,
                chains=n_chains,
                return_inferencedata=True
            )

        direct_samples = direct_trace.posterior['theta_direct'].values.flatten()
        direct_est = {
            'mean': direct_samples.mean(),
            'sd': direct_samples.std(),
            'hdi_2.5': np.percentile(direct_samples, 2.5),
            'hdi_97.5': np.percentile(direct_samples, 97.5),
        }

        # Calculate inconsistency factor (difference between direct and indirect)
        # Use samples from both models
        indirect_samples = indirect_model.predict(base_trt, comp_trt, return_samples=True)['samples']

        # Match sample sizes
        n_min = min(len(direct_samples), len(indirect_samples))
        direct_samples = direct_samples[:n_min]
        indirect_samples = indirect_samples[:n_min]

        inconsistency_samples = direct_samples - indirect_samples

        inconsistency = {
            'mean': inconsistency_samples.mean(),
            'sd': inconsistency_samples.std(),
            'hdi_2.5': np.percentile(inconsistency_samples, 2.5),
            'hdi_97.5': np.percentile(inconsistency_samples, 97.5),
            'prob_inconsistent': (np.abs(inconsistency_samples) > 0.1).mean(),
        }

        # P-value for inconsistency (two-sided test)
        p_value = 2 * min(
            (inconsistency_samples > 0).mean(),
            (inconsistency_samples < 0).mean()
        )

        return {
            'comparison': comparison,
            'direct': direct_est,
            'indirect': indirect_est,
            'inconsistency': inconsistency,
            'p_value': p_value,
            'n_direct_studies': len(direct_data),
            'n_indirect_studies': len(indirect_data),
        }

    def run_all_comparisons(
        self,
        min_indirect_studies: int = 2,
        **kwargs
    ) -> pd.DataFrame:
        """
        Run node-splitting for all eligible comparisons.

        Parameters
        ----------
        min_indirect_studies : int
            Minimum number of studies in indirect network to perform node-splitting
        **kwargs : dict
            Arguments for run_node_splitting()

        Returns
        -------
        results : pd.DataFrame
            Node-splitting results for all comparisons
        """
        results = []

        for comparison in self.direct_comparisons:
            base_trt, comp_trt = comparison

            # Check if enough indirect evidence
            direct_mask = (self.data['treatment_base'] == base_trt) & (self.data['treatment_comp'] == comp_trt)
            indirect_data = self.data[~direct_mask]

            if len(indirect_data) < min_indirect_studies:
                print(f"\nSkipping {comp_trt} vs {base_trt}: insufficient indirect evidence")
                continue

            try:
                result = self.run_node_splitting(comparison, **kwargs)

                results.append({
                    'comparison': f"{comp_trt} vs {base_trt}",
                    'direct_mean': result['direct']['mean'],
                    'direct_hdi_low': result['direct']['hdi_2.5'],
                    'direct_hdi_high': result['direct']['hdi_97.5'],
                    'indirect_mean': result['indirect']['mean'],
                    'indirect_hdi_low': result['indirect']['hdi_2.5'],
                    'indirect_hdi_high': result['indirect']['hdi_97.5'],
                    'inconsistency_mean': result['inconsistency']['mean'],
                    'inconsistency_hdi_low': result['inconsistency']['hdi_2.5'],
                    'inconsistency_hdi_high': result['inconsistency']['hdi_97.5'],
                    'p_value': result['p_value'],
                    'n_direct': result['n_direct_studies'],
                    'n_indirect': result['n_indirect_studies'],
                })

            except Exception as e:
                print(f"\nError in node-splitting for {comp_trt} vs {base_trt}: {e}")
                continue

        return pd.DataFrame(results)
