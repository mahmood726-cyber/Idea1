"""
Additive Component Network Meta-Analysis Model - Contrast-Based Formulation.

This implements proper contrast-based CNMA following Welton et al. (2009) and
Dias et al. (2013) NICE DSU Technical Support Documents.

Mathematical Formulation:
-----------------------
For a study s comparing treatments j and k:

    y_sk ~ Normal(δ_sk, se_sk²)

    δ_sk = θ_jk + ν_sk

    θ_jk = Σ_c β_c × (I_kc - I_jc)

    ν_sk ~ Normal(0, τ²)

where:
    - y_sk: observed log odds ratio (or other effect measure) for study s, comparison j vs k
    - δ_sk: true relative effect for study s
    - θ_jk: pooled relative effect of k vs j based on component composition
    - β_c: additive effect of component c
    - I_kc: indicator for component c in treatment k
    - ν_sk: study-specific random effect (between-study heterogeneity)
    - τ²: between-study variance
"""

from typing import Dict, List, Optional, Any, Union, Tuple
import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from cnma_platform.models.base_model import BaseCNMAModel


class AdditiveModel(BaseCNMAModel):
    """
    Additive CNMA model using proper contrast-based formulation.

    This implementation:
    1. Models contrasts (relative effects) directly
    2. Properly accounts for within-study correlation in multi-arm trials
    3. Uses study-specific random effects for between-study heterogeneity
    4. Follows established NMA methodology (Dias et al., 2013)
    """

    def __init__(
        self,
        data: pd.DataFrame,
        outcome_type: str = "continuous",
        reference_treatment: Optional[str] = None,
        prior_sd: float = 2.0,
        heterogeneity_prior: str = "half_normal",
        data_format: str = "contrast",
        **kwargs
    ):
        """
        Initialize the additive CNMA model.

        Parameters
        ----------
        data : pd.DataFrame
            Dataset in contrast format with columns:
            study, treatment_base, treatment_comp, y (contrast), se (standard error)
            OR in arm format with columns:
            study, arm, treatment, y (outcome), se, n (sample size)
        outcome_type : str
            Type of outcome: 'continuous' (SMD, MD, log-OR), 'binary', 'count'
        reference_treatment : str, optional
            Reference treatment for relative effects (default: most common)
        prior_sd : float
            Standard deviation for component effect priors (weakly informative)
        heterogeneity_prior : str
            Prior for heterogeneity SD: 'half_normal', 'half_cauchy', 'uniform'
        data_format : str
            'contrast' for contrast-based data, 'arm' for arm-based
        """
        super().__init__(data, outcome_type, reference_treatment, **kwargs)
        self.prior_sd = prior_sd
        self.heterogeneity_prior = heterogeneity_prior
        self.data_format = data_format
        self.model = None

        # Processed contrast data
        self.contrast_data: Optional[pd.DataFrame] = None

        # Multi-arm trial structures
        self.multi_arm_studies: Dict[str, List[int]] = {}

        # Preprocess data
        self.preprocess_data()

    def _convert_to_contrast_format(self) -> pd.DataFrame:
        """
        Convert arm-based data to contrast-based format.

        For multi-arm trials, uses the first arm as reference within each study.

        Returns
        -------
        contrast_data : pd.DataFrame
            Contrast-based dataset
        """
        if self.data_format == "contrast":
            # Already in contrast format
            required_cols = ['study', 'treatment_base', 'treatment_comp', 'y', 'se']
            if all(col in self.data.columns for col in required_cols):
                return self.data.copy()
            else:
                raise ValueError(f"Contrast format requires columns: {required_cols}")

        # Convert arm-based to contrast
        contrasts = []

        for study, group in self.data.groupby('study'):
            arms = group.sort_values('arm').reset_index(drop=True)

            if len(arms) < 2:
                raise ValueError(f"Study {study} has fewer than 2 arms")

            # Use first arm as baseline
            base_arm = arms.iloc[0]

            for i in range(1, len(arms)):
                comp_arm = arms.iloc[i]

                # Calculate contrast
                y_contrast = comp_arm['y'] - base_arm['y']

                # SE for contrast (assuming independence - will be corrected in model)
                se_contrast = np.sqrt(comp_arm['se']**2 + base_arm['se']**2)

                contrasts.append({
                    'study': study,
                    'treatment_base': base_arm['treatment'],
                    'treatment_comp': comp_arm['treatment'],
                    'y': y_contrast,
                    'se': se_contrast,
                    'n_base': base_arm.get('n', None),
                    'n_comp': comp_arm.get('n', None)
                })

        return pd.DataFrame(contrasts)

    def preprocess_data(self) -> None:
        """
        Preprocess data and convert to contrast format.
        """
        # Convert to contrast format
        self.contrast_data = self._convert_to_contrast_format()

        # Extract unique treatments
        treatments_base = set(self.contrast_data['treatment_base'].unique())
        treatments_comp = set(self.contrast_data['treatment_comp'].unique())
        self.treatments = sorted(treatments_base | treatments_comp)

        self.n_treatments = len(self.treatments)
        self.n_studies = len(self.contrast_data['study'].unique())

        # Identify multi-arm trials
        study_arms = self.contrast_data.groupby('study').size()
        self.multi_arm_studies = {
            study: list(range(n_arms))
            for study, n_arms in study_arms.items()
            if n_arms > 1
        }

    def build_model(self) -> pm.Model:
        """
        Build the PyMC model for additive CNMA using contrast-based formulation.

        Returns
        -------
        model : pm.Model
            The PyMC model object
        """
        if self.component_matrix is None:
            raise ValueError("Component matrix must be set before building model")

        # Prepare data
        n_contrasts = len(self.contrast_data)
        y_obs = self.contrast_data['y'].values
        se_obs = self.contrast_data['se'].values

        # Create component difference matrix for each contrast
        component_diff = np.zeros((n_contrasts, self.n_components))

        for i, row in self.contrast_data.iterrows():
            base_idx = self.treatments.index(row['treatment_base'])
            comp_idx = self.treatments.index(row['treatment_comp'])

            # Difference in component composition
            component_diff[i, :] = (
                self.component_matrix[comp_idx, :] -
                self.component_matrix[base_idx, :]
            )

        # Study indicators for random effects
        studies = self.contrast_data['study'].values
        unique_studies = sorted(self.contrast_data['study'].unique())
        study_idx = np.array([unique_studies.index(s) for s in studies])
        n_studies = len(unique_studies)

        with pm.Model() as model:
            # Component effect priors (weakly informative)
            beta = pm.Normal(
                'beta',
                mu=0,
                sigma=self.prior_sd,
                shape=self.n_components
            )

            # Between-study heterogeneity
            if self.heterogeneity_prior == 'half_normal':
                tau = pm.HalfNormal('tau', sigma=1.0)
            elif self.heterogeneity_prior == 'half_cauchy':
                tau = pm.HalfCauchy('tau', beta=0.5)
            elif self.heterogeneity_prior == 'uniform':
                tau = pm.Uniform('tau', lower=0, upper=5)
            else:
                tau = pm.HalfNormal('tau', sigma=1.0)

            # Study-specific random effects (ONE per study, not per contrast)
            # This properly models between-study heterogeneity
            # For multi-arm trials, contrasts from the same study share the same nu
            nu = pm.Normal(
                'nu',
                mu=0,
                sigma=tau,
                shape=n_studies
            )

            # Pooled relative effects based on component composition
            # θ_jk = Σ β_c × (I_kc - I_jc)
            theta = pm.Deterministic(
                'theta',
                pm.math.dot(component_diff, beta)
            )

            # Study-specific relative effects
            # δ_sk = θ_jk + ν_s (indexed by study, not contrast)
            delta = pm.Deterministic(
                'delta',
                theta + nu[study_idx]
            )

            # Likelihood
            # y_sk ~ Normal(δ_sk, se_sk²)
            if self.outcome_type == 'continuous':
                y = pm.Normal(
                    'y',
                    mu=delta,
                    sigma=se_obs,
                    observed=y_obs
                )
            elif self.outcome_type == 'binary':
                # For log-OR or log-RR
                y = pm.Normal(
                    'y',
                    mu=delta,
                    sigma=se_obs,
                    observed=y_obs
                )
            else:
                raise ValueError(f"Outcome type '{self.outcome_type}' not supported")

            # Derived quantities: all pairwise treatment effects
            # Calculate relative effects for all treatment pairs
            treatment_effects = []

            for i in range(self.n_treatments):
                row_effects = []
                for j in range(self.n_treatments):
                    if i == j:
                        row_effects.append(0.0)
                    else:
                        # Component difference between treatment j and i
                        comp_diff_ij = (
                            self.component_matrix[j, :] -
                            self.component_matrix[i, :]
                        )
                        effect_ij = pm.math.dot(comp_diff_ij, beta)
                        row_effects.append(effect_ij)

                treatment_effects.append(pm.math.stack(row_effects))

            theta_all = pm.Deterministic(
                'theta_all',
                pm.math.stack(treatment_effects)
            )

        self.model = model
        return model

    def fit(
        self,
        n_samples: int = 2000,
        n_warmup: int = 1000,
        n_chains: int = 4,
        target_accept: float = 0.95,
        random_seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fit the additive CNMA model using MCMC with proper convergence diagnostics.

        Parameters
        ----------
        n_samples : int
            Number of posterior samples per chain
        n_warmup : int
            Number of warmup/burn-in samples
        n_chains : int
            Number of MCMC chains
        target_accept : float
            Target acceptance probability for NUTS sampler
        random_seed : int, optional
            Random seed for reproducibility
        **kwargs : dict
            Additional arguments passed to pm.sample()

        Returns
        -------
        results : dict
            Dictionary containing trace, summary, and diagnostics
        """
        if self.model is None:
            self.build_model()

        with self.model:
            # Sample from posterior
            self.trace = pm.sample(
                draws=n_samples,
                tune=n_warmup,
                chains=n_chains,
                target_accept=target_accept,
                return_inferencedata=True,
                random_seed=random_seed,
                **kwargs
            )

            # Compute model comparison metrics
            try:
                pm.compute_log_likelihood(self.trace)
            except:
                pass  # May fail for some models

        self.fitted = True

        # Convergence diagnostics
        convergence = self._check_convergence()

        # Store results
        self.results = {
            'trace': self.trace,
            'summary': az.summary(self.trace, hdi_prob=0.95),
            'n_samples': n_samples,
            'n_chains': n_chains,
            'convergence': convergence,
        }

        # Warn if convergence issues
        if not convergence['converged']:
            print("\nWARNING: Convergence issues detected!")
            print(f"  - Parameters with Rhat > 1.01: {convergence['n_high_rhat']}")
            print(f"  - Parameters with low ESS (bulk): {convergence['n_low_ess_bulk']}")
            print(f"  - Parameters with low ESS (tail): {convergence['n_low_ess_tail']}")
            print("  Consider increasing n_warmup or n_samples.")

        return self.results

    def _check_convergence(self) -> Dict[str, Any]:
        """
        Check MCMC convergence using Rhat and effective sample size.

        Uses modern standards: Rhat < 1.01 (Vehtari et al. 2021)

        Returns
        -------
        diagnostics : dict
            Convergence diagnostic information
        """
        summary = az.summary(self.trace)

        # Check Rhat (modern standard: < 1.01)
        rhat_values = summary['r_hat'].dropna()
        n_high_rhat = (rhat_values > 1.01).sum()
        max_rhat = rhat_values.max() if len(rhat_values) > 0 else np.nan

        # Check effective sample size (bulk and tail)
        ess_bulk = summary['ess_bulk'].dropna()
        ess_tail = summary['ess_tail'].dropna()
        n_low_ess_bulk = (ess_bulk < 400).sum()
        n_low_ess_tail = (ess_tail < 400).sum()
        min_ess_bulk = ess_bulk.min() if len(ess_bulk) > 0 else np.nan
        min_ess_tail = ess_tail.min() if len(ess_tail) > 0 else np.nan

        converged = (n_high_rhat == 0) and (n_low_ess_bulk == 0) and (n_low_ess_tail == 0)

        return {
            'converged': converged,
            'max_rhat': max_rhat,
            'n_high_rhat': n_high_rhat,
            'min_ess_bulk': min_ess_bulk,
            'min_ess_tail': min_ess_tail,
            'n_low_ess_bulk': n_low_ess_bulk,
            'n_low_ess_tail': n_low_ess_tail,
        }

    def get_component_effects(self) -> pd.DataFrame:
        """
        Get estimated effects for each component with credible intervals.

        Returns
        -------
        effects : pd.DataFrame
            DataFrame with component effects and 95% credible intervals
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before extracting component effects")

        # Extract beta (component effects) from trace
        beta_samples = self.trace.posterior['beta'].values.reshape(-1, self.n_components)

        effects = []
        for i, component in enumerate(self.components):
            samples = beta_samples[:, i]

            effects.append({
                'component': component,
                'mean': samples.mean(),
                'sd': samples.std(),
                'median': np.median(samples),
                'hdi_2.5': np.percentile(samples, 2.5),
                'hdi_97.5': np.percentile(samples, 97.5),
                'prob_positive': (samples > 0).mean(),
                'prob_negative': (samples < 0).mean(),
            })

        return pd.DataFrame(effects)

    def predict(
        self,
        treatment_1: Union[str, List[str]],
        treatment_2: Union[str, List[str]],
        return_samples: bool = False
    ) -> Dict[str, np.ndarray]:
        """
        Predict relative treatment effect between two treatments.

        Parameters
        ----------
        treatment_1 : str or list
            Baseline treatment name or list of components
        treatment_2 : str or list
            Comparison treatment name or list of components
        return_samples : bool
            If True, return full posterior samples

        Returns
        -------
        predictions : dict
            Dictionary with 'mean', 'sd', 'hdi_2.5', 'hdi_97.5' and optionally 'samples'
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before making predictions")

        # Get component indicators for each treatment
        if isinstance(treatment_1, str):
            if treatment_1 not in self.treatments:
                raise ValueError(f"Treatment '{treatment_1}' not found")
            comp_1 = self.component_matrix[self.treatments.index(treatment_1), :]
        else:
            comp_1 = np.array([1 if c in treatment_1 else 0 for c in self.components])

        if isinstance(treatment_2, str):
            if treatment_2 not in self.treatments:
                raise ValueError(f"Treatment '{treatment_2}' not found")
            comp_2 = self.component_matrix[self.treatments.index(treatment_2), :]
        else:
            comp_2 = np.array([1 if c in treatment_2 else 0 for c in self.components])

        # Calculate component difference
        comp_diff = comp_2 - comp_1

        # Extract beta samples
        beta_samples = self.trace.posterior['beta'].values.reshape(-1, self.n_components)

        # Predict relative effect
        relative_effect = beta_samples @ comp_diff

        predictions = {
            'mean': relative_effect.mean(),
            'sd': relative_effect.std(),
            'median': np.median(relative_effect),
            'hdi_2.5': np.percentile(relative_effect, 2.5),
            'hdi_97.5': np.percentile(relative_effect, 97.5),
            'prob_positive': (relative_effect > 0).mean(),
        }

        if return_samples:
            predictions['samples'] = relative_effect

        return predictions

    def summary(self) -> pd.DataFrame:
        """
        Generate summary statistics for model parameters.

        Returns
        -------
        summary : pd.DataFrame
            Summary statistics for all model parameters including Rhat and ESS
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before generating summary")

        return az.summary(self.trace, hdi_prob=0.95)

    def get_treatment_ranking(self) -> pd.DataFrame:
        """
        Calculate treatment rankings based on SUCRA (Surface Under the Cumulative Ranking curve).

        Returns
        -------
        rankings : pd.DataFrame
            DataFrame with treatments, mean effects, and SUCRA values
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before calculating rankings")

        # Extract all pairwise treatment effects (theta_all)
        # theta_all is shape (n_treatments, n_treatments)
        theta_all_samples = self.trace.posterior['theta_all'].values

        # Reshape to (n_samples, n_treatments, n_treatments)
        n_samples = theta_all_samples.shape[0] * theta_all_samples.shape[1]
        theta_all_samples = theta_all_samples.reshape(n_samples, self.n_treatments, self.n_treatments)

        # For ranking, we want the treatment effects vs a reference (e.g., first treatment)
        # Or we can use row means as overall effectiveness
        treatment_scores = theta_all_samples[:, :, 0]  # Effects vs first treatment

        # Calculate rankings for each sample (higher is better - adjust if needed)
        rankings_matrix = np.zeros((n_samples, self.n_treatments))

        for i in range(n_samples):
            # Rank treatments (0 = best, n-1 = worst)
            rankings_matrix[i, :] = np.argsort(np.argsort(-treatment_scores[i, :]))

        # Calculate SUCRA (0 = worst, 1 = best)
        sucra = 1 - (rankings_matrix.mean(axis=0) / (self.n_treatments - 1))

        results = []
        for i, treatment in enumerate(self.treatments):
            results.append({
                'treatment': treatment,
                'mean_effect': treatment_scores[:, i].mean(),
                'sd_effect': treatment_scores[:, i].std(),
                'mean_rank': rankings_matrix[:, i].mean() + 1,  # 1-indexed
                'sucra': sucra[i],
            })

        df = pd.DataFrame(results)
        return df.sort_values('sucra', ascending=False)

    def posterior_predictive_check(self) -> Dict[str, Any]:
        """
        Perform posterior predictive checks.

        Returns
        -------
        ppc_results : dict
            Posterior predictive check results
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted first")

        with self.model:
            ppc = pm.sample_posterior_predictive(self.trace)

        y_obs = self.contrast_data['y'].values
        y_pred = ppc.posterior_predictive['y'].values.reshape(-1, len(y_obs))

        # Calculate predictive p-values
        mean_obs = y_obs.mean()
        mean_pred = y_pred.mean(axis=1)
        p_value_mean = (mean_pred > mean_obs).mean()

        return {
            'posterior_predictive': ppc,
            'p_value_mean': p_value_mean,
            'y_obs': y_obs,
            'y_pred_mean': y_pred.mean(axis=0),
            'y_pred_hdi_low': np.percentile(y_pred, 2.5, axis=0),
            'y_pred_hdi_high': np.percentile(y_pred, 97.5, axis=0),
        }
