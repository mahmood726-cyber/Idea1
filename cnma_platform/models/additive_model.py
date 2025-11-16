"""
Additive Component Network Meta-Analysis Model.

This model assumes that component effects combine additively without interactions.
"""

from typing import Dict, List, Optional, Any, Union
import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from cnma_platform.models.base_model import BaseCNMAModel


class AdditiveModel(BaseCNMAModel):
    """
    Additive CNMA model.

    The additive model assumes that the relative effect between treatments j and k
    is the sum of the effects of components present in k but not in j:

        θ_jk = Σ β_c × I(component c in treatment k but not j)

    where:
        - θ_jk is the relative effect of treatment k vs j
        - β_c is the effect of component c
        - I() is an indicator function
    """

    def __init__(
        self,
        data: pd.DataFrame,
        outcome_type: str = "continuous",
        reference_treatment: Optional[str] = None,
        prior_sd: float = 2.0,
        heterogeneity_prior: str = "half_normal",
        **kwargs
    ):
        """
        Initialize the additive CNMA model.

        Parameters
        ----------
        data : pd.DataFrame
            Dataset with columns: study, treatment, y (outcome), se (standard error)
        outcome_type : str
            Type of outcome: 'continuous', 'binary', or 'count'
        reference_treatment : str, optional
            Reference treatment for relative effects
        prior_sd : float
            Standard deviation for component effect priors
        heterogeneity_prior : str
            Prior distribution for heterogeneity: 'half_normal', 'half_cauchy', 'uniform'
        """
        super().__init__(data, outcome_type, reference_treatment, **kwargs)
        self.prior_sd = prior_sd
        self.heterogeneity_prior = heterogeneity_prior
        self.model = None

        # Preprocess data
        self.preprocess_data()

    def build_model(self) -> pm.Model:
        """
        Build the PyMC model for additive CNMA.

        Returns
        -------
        model : pm.Model
            The PyMC model object
        """
        # Prepare data structures
        studies = self.data['study'].values
        unique_studies = sorted(self.data['study'].unique())
        study_idx = np.array([unique_studies.index(s) for s in studies])
        n_studies = len(unique_studies)

        # Get treatment indices
        treatment_idx = np.array([
            self.treatments.index(t) for t in self.data['treatment'].values
        ])

        # Observed data
        y_obs = self.data['y'].values
        se_obs = self.data['se'].values

        with pm.Model() as model:
            # Component effect priors
            beta = pm.Normal(
                'beta',
                mu=0,
                sigma=self.prior_sd,
                shape=self.n_components
            )

            # Study-specific baseline effects (nuisance parameters)
            mu_study = pm.Normal(
                'mu_study',
                mu=0,
                sigma=10,
                shape=n_studies
            )

            # Between-study heterogeneity
            if self.heterogeneity_prior == 'half_normal':
                tau = pm.HalfNormal('tau', sigma=1)
            elif self.heterogeneity_prior == 'half_cauchy':
                tau = pm.HalfCauchy('tau', beta=1)
            elif self.heterogeneity_prior == 'uniform':
                tau = pm.Uniform('tau', lower=0, upper=5)
            else:
                tau = pm.HalfNormal('tau', sigma=1)

            # Random effects for each observation
            delta = pm.Normal('delta', mu=0, sigma=tau, shape=len(y_obs))

            # Calculate expected treatment effects
            # For each observation, compute the additive effect based on components
            treatment_effects = pm.Deterministic(
                'treatment_effect',
                pm.math.dot(self.component_matrix[treatment_idx, :], beta)
            )

            # Expected outcome
            mu = mu_study[study_idx] + treatment_effects + delta

            # Likelihood
            if self.outcome_type == 'continuous':
                y = pm.Normal(
                    'y',
                    mu=mu,
                    sigma=se_obs,
                    observed=y_obs
                )
            elif self.outcome_type == 'binary':
                # For binary outcomes (log odds ratios)
                y = pm.Normal(
                    'y',
                    mu=mu,
                    sigma=se_obs,
                    observed=y_obs
                )
            else:
                raise ValueError(f"Outcome type '{self.outcome_type}' not supported")

            # Derived quantities: treatment effects relative to reference
            if self.reference_treatment is None:
                ref_idx = 0  # First treatment alphabetically
            else:
                ref_idx = self.treatments.index(self.reference_treatment)

            # Relative effects for all treatments vs reference
            ref_components = self.component_matrix[ref_idx, :]
            relative_effects = []

            for i in range(self.n_treatments):
                comp_diff = self.component_matrix[i, :] - ref_components
                rel_effect = pm.math.dot(comp_diff, beta)
                relative_effects.append(rel_effect)

            theta = pm.Deterministic(
                'theta',
                pm.math.stack(relative_effects)
            )

        self.model = model
        return model

    def fit(
        self,
        n_samples: int = 2000,
        n_warmup: int = 1000,
        n_chains: int = 4,
        target_accept: float = 0.95,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fit the additive CNMA model using MCMC.

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
        **kwargs : dict
            Additional arguments passed to pm.sample()

        Returns
        -------
        results : dict
            Dictionary containing trace and summary statistics
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
                **kwargs
            )

            # Compute model comparison metrics
            self.trace = az.add_stats(self.trace)

        self.fitted = True

        # Store results
        self.results = {
            'trace': self.trace,
            'summary': az.summary(self.trace),
            'n_samples': n_samples,
            'n_chains': n_chains,
        }

        return self.results

    def get_component_effects(self) -> pd.DataFrame:
        """
        Get estimated effects for each component.

        Returns
        -------
        effects : pd.DataFrame
            DataFrame with component effects and credible intervals
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before extracting component effects")

        # Extract beta (component effects) from trace
        beta_samples = self.trace.posterior['beta'].values.reshape(-1, self.n_components)

        effects = []
        for i, component in enumerate(self.components):
            effects.append({
                'component': component,
                'mean': beta_samples[:, i].mean(),
                'sd': beta_samples[:, i].std(),
                'q2.5': np.percentile(beta_samples[:, i], 2.5),
                'q25': np.percentile(beta_samples[:, i], 25),
                'q50': np.percentile(beta_samples[:, i], 50),
                'q75': np.percentile(beta_samples[:, i], 75),
                'q97.5': np.percentile(beta_samples[:, i], 97.5),
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
            Dictionary with 'mean', 'sd', 'quantiles' and optionally 'samples'
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
            'quantiles': {
                '2.5%': np.percentile(relative_effect, 2.5),
                '25%': np.percentile(relative_effect, 25),
                '50%': np.percentile(relative_effect, 50),
                '75%': np.percentile(relative_effect, 75),
                '97.5%': np.percentile(relative_effect, 97.5),
            }
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
            Summary statistics for all model parameters
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before generating summary")

        return az.summary(self.trace)

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

        # Extract treatment effects (theta) from trace
        theta_samples = self.trace.posterior['theta'].values.reshape(-1, self.n_treatments)

        # Calculate rankings for each sample
        rankings_matrix = np.zeros((theta_samples.shape[0], self.n_treatments))

        for i in range(theta_samples.shape[0]):
            # Higher is better (or adjust based on outcome direction)
            rankings_matrix[i, :] = np.argsort(np.argsort(-theta_samples[i, :]))

        # Calculate SUCRA
        sucra = np.mean(rankings_matrix, axis=0) / (self.n_treatments - 1)

        results = []
        for i, treatment in enumerate(self.treatments):
            results.append({
                'treatment': treatment,
                'mean_effect': theta_samples[:, i].mean(),
                'sd_effect': theta_samples[:, i].std(),
                'mean_rank': rankings_matrix[:, i].mean() + 1,  # 1-indexed
                'sucra': sucra[i],
            })

        df = pd.DataFrame(results)
        return df.sort_values('sucra', ascending=False)
