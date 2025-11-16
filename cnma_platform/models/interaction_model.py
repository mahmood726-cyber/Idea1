"""
Interaction Component Network Meta-Analysis Model.

This model extends the additive model to include pairwise interactions between components.
"""

from typing import Dict, List, Optional, Any, Union
import numpy as np
import pandas as pd
import pymc as pm
import arviz as az
from itertools import combinations
from cnma_platform.models.base_model import BaseCNMAModel


class InteractionModel(BaseCNMAModel):
    """
    Interaction CNMA model.

    The interaction model extends the additive model to include pairwise interactions:

        θ_jk = Σ β_c × I_c + Σ γ_cd × I_c × I_d

    where:
        - β_c are main (additive) component effects
        - γ_cd are pairwise interaction effects
        - I_c, I_d are indicators for components c and d
    """

    def __init__(
        self,
        data: pd.DataFrame,
        outcome_type: str = "continuous",
        reference_treatment: Optional[str] = None,
        prior_sd: float = 2.0,
        interaction_prior_sd: float = 1.0,
        heterogeneity_prior: str = "half_normal",
        max_interaction_order: int = 2,
        **kwargs
    ):
        """
        Initialize the interaction CNMA model.

        Parameters
        ----------
        data : pd.DataFrame
            Dataset with columns: study, treatment, y (outcome), se (standard error)
        outcome_type : str
            Type of outcome: 'continuous', 'binary', or 'count'
        reference_treatment : str, optional
            Reference treatment for relative effects
        prior_sd : float
            Standard deviation for main component effect priors
        interaction_prior_sd : float
            Standard deviation for interaction effect priors
        heterogeneity_prior : str
            Prior distribution for heterogeneity
        max_interaction_order : int
            Maximum order of interactions (2 = pairwise, 3 = three-way, etc.)
        """
        super().__init__(data, outcome_type, reference_treatment, **kwargs)
        self.prior_sd = prior_sd
        self.interaction_prior_sd = interaction_prior_sd
        self.heterogeneity_prior = heterogeneity_prior
        self.max_interaction_order = max_interaction_order
        self.model = None

        # Interaction pairs/tuples
        self.interactions: List[tuple] = []
        self.interaction_matrix: np.ndarray = None

        # Preprocess data
        self.preprocess_data()

    def _build_interaction_matrix(self) -> np.ndarray:
        """
        Build interaction matrix for all treatment combinations.

        Returns
        -------
        interaction_matrix : np.ndarray
            Matrix of shape (n_treatments, n_interactions)
        """
        # Generate all pairwise (and higher-order) interactions
        self.interactions = []

        for order in range(2, self.max_interaction_order + 1):
            for interaction in combinations(range(self.n_components), order):
                self.interactions.append(interaction)

        n_interactions = len(self.interactions)

        # Build interaction matrix
        interaction_matrix = np.zeros((self.n_treatments, n_interactions))

        for i in range(self.n_treatments):
            for j, interaction in enumerate(self.interactions):
                # Interaction is present if all components in the interaction are present
                if all(self.component_matrix[i, comp_idx] == 1 for comp_idx in interaction):
                    interaction_matrix[i, j] = 1

        self.interaction_matrix = interaction_matrix
        return interaction_matrix

    def build_model(self) -> pm.Model:
        """
        Build the PyMC model for interaction CNMA.

        Returns
        -------
        model : pm.Model
            The PyMC model object
        """
        # Build interaction matrix
        self._build_interaction_matrix()

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

        n_interactions = len(self.interactions)

        with pm.Model() as model:
            # Main component effect priors
            beta = pm.Normal(
                'beta',
                mu=0,
                sigma=self.prior_sd,
                shape=self.n_components
            )

            # Interaction effect priors
            gamma = pm.Normal(
                'gamma',
                mu=0,
                sigma=self.interaction_prior_sd,
                shape=n_interactions
            )

            # Study-specific baseline effects
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

            # Random effects
            delta = pm.Normal('delta', mu=0, sigma=tau, shape=len(y_obs))

            # Calculate expected treatment effects
            # Main effects
            main_effects = pm.math.dot(self.component_matrix[treatment_idx, :], beta)

            # Interaction effects
            interaction_effects = pm.math.dot(self.interaction_matrix[treatment_idx, :], gamma)

            # Total treatment effects
            treatment_effects = pm.Deterministic(
                'treatment_effect',
                main_effects + interaction_effects
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
                ref_idx = 0
            else:
                ref_idx = self.treatments.index(self.reference_treatment)

            # Relative effects for all treatments vs reference
            ref_components = self.component_matrix[ref_idx, :]
            ref_interactions = self.interaction_matrix[ref_idx, :]
            relative_effects = []

            for i in range(self.n_treatments):
                comp_diff = self.component_matrix[i, :] - ref_components
                int_diff = self.interaction_matrix[i, :] - ref_interactions
                rel_effect = pm.math.dot(comp_diff, beta) + pm.math.dot(int_diff, gamma)
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
        Fit the interaction CNMA model using MCMC.

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
        Get estimated main effects for each component.

        Returns
        -------
        effects : pd.DataFrame
            DataFrame with component main effects and credible intervals
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before extracting component effects")

        beta_samples = self.trace.posterior['beta'].values.reshape(-1, self.n_components)

        effects = []
        for i, component in enumerate(self.components):
            effects.append({
                'component': component,
                'effect_type': 'main',
                'mean': beta_samples[:, i].mean(),
                'sd': beta_samples[:, i].std(),
                'q2.5': np.percentile(beta_samples[:, i], 2.5),
                'q50': np.percentile(beta_samples[:, i], 50),
                'q97.5': np.percentile(beta_samples[:, i], 97.5),
            })

        return pd.DataFrame(effects)

    def get_interaction_effects(self) -> pd.DataFrame:
        """
        Get estimated interaction effects.

        Returns
        -------
        interactions : pd.DataFrame
            DataFrame with interaction effects and credible intervals
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before extracting interaction effects")

        gamma_samples = self.trace.posterior['gamma'].values.reshape(-1, len(self.interactions))

        effects = []
        for i, interaction in enumerate(self.interactions):
            component_names = [self.components[idx] for idx in interaction]
            interaction_name = ' × '.join(component_names)

            effects.append({
                'interaction': interaction_name,
                'components': component_names,
                'order': len(interaction),
                'mean': gamma_samples[:, i].mean(),
                'sd': gamma_samples[:, i].std(),
                'q2.5': np.percentile(gamma_samples[:, i], 2.5),
                'q50': np.percentile(gamma_samples[:, i], 50),
                'q97.5': np.percentile(gamma_samples[:, i], 97.5),
                'prob_positive': (gamma_samples[:, i] > 0).mean(),
                'prob_negative': (gamma_samples[:, i] < 0).mean(),
            })

        return pd.DataFrame(effects)

    def predict(
        self,
        treatment_1: Union[str, List[str]],
        treatment_2: Union[str, List[str]],
        return_samples: bool = False
    ) -> Dict[str, np.ndarray]:
        """
        Predict relative treatment effect including interactions.

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

        # Get component indicators
        if isinstance(treatment_1, str):
            comp_1 = self.component_matrix[self.treatments.index(treatment_1), :]
            int_1 = self.interaction_matrix[self.treatments.index(treatment_1), :]
        else:
            comp_1 = np.array([1 if c in treatment_1 else 0 for c in self.components])
            # Calculate interactions for custom component list
            int_1 = np.zeros(len(self.interactions))
            for j, interaction in enumerate(self.interactions):
                if all(self.components[idx] in treatment_1 for idx in interaction):
                    int_1[j] = 1

        if isinstance(treatment_2, str):
            comp_2 = self.component_matrix[self.treatments.index(treatment_2), :]
            int_2 = self.interaction_matrix[self.treatments.index(treatment_2), :]
        else:
            comp_2 = np.array([1 if c in treatment_2 else 0 for c in self.components])
            int_2 = np.zeros(len(self.interactions))
            for j, interaction in enumerate(self.interactions):
                if all(self.components[idx] in treatment_2 for idx in interaction):
                    int_2[j] = 1

        # Calculate differences
        comp_diff = comp_2 - comp_1
        int_diff = int_2 - int_1

        # Extract samples
        beta_samples = self.trace.posterior['beta'].values.reshape(-1, self.n_components)
        gamma_samples = self.trace.posterior['gamma'].values.reshape(-1, len(self.interactions))

        # Predict relative effect
        main_effect = beta_samples @ comp_diff
        interaction_effect = gamma_samples @ int_diff
        relative_effect = main_effect + interaction_effect

        predictions = {
            'mean': relative_effect.mean(),
            'sd': relative_effect.std(),
            'main_effect_mean': main_effect.mean(),
            'interaction_effect_mean': interaction_effect.mean(),
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
            predictions['main_effect_samples'] = main_effect
            predictions['interaction_effect_samples'] = interaction_effect

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
