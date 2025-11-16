"""
Composite Likelihood Approach for CNMA.

The composite likelihood approach constructs a likelihood as the product of arm-level
likelihoods, avoiding the need to specify within-study correlation structures.

This is particularly useful for multi-arm trials where the correlation structure
may be complex or unknown.

References:
    Welton et al. (2022, 2025) - Composite likelihood methods for CNMA
"""

from typing import Dict, List, Optional, Any, Union, Tuple
import numpy as np
import pandas as pd
from scipy import optimize
from scipy.stats import norm, multivariate_normal
import pymc as pm
import arviz as az


class CompositeLikelihood:
    """
    Composite likelihood estimation for CNMA models.

    Instead of modeling the full multivariate likelihood for multi-arm studies,
    the composite likelihood uses the product of marginal (arm-level) likelihoods.

    This approach:
    1. Avoids specifying within-study correlations
    2. Provides consistent parameter estimates
    3. Requires sandwich variance estimator for valid inference
    """

    def __init__(
        self,
        data: pd.DataFrame,
        component_matrix: np.ndarray,
        model_type: str = "additive",
        outcome_type: str = "continuous"
    ):
        """
        Initialize composite likelihood estimator.

        Parameters
        ----------
        data : pd.DataFrame
            Arm-level data with columns: study, arm, treatment, y, se
        component_matrix : np.ndarray
            Binary matrix indicating component presence (n_treatments × n_components)
        model_type : str
            Type of model: 'additive' or 'interaction'
        outcome_type : str
            Type of outcome: 'continuous' or 'binary'
        """
        self.data = data.copy()
        self.component_matrix = component_matrix
        self.model_type = model_type
        self.outcome_type = outcome_type

        self.n_components = component_matrix.shape[1]
        self.fitted = False
        self.estimates = None
        self.vcov = None

    def _additive_linear_predictor(
        self,
        params: np.ndarray,
        treatment_idx: int
    ) -> float:
        """
        Calculate linear predictor for additive model.

        Parameters
        ----------
        params : np.ndarray
            Parameter vector [beta (components), mu_study (baselines), tau (heterogeneity)]
        treatment_idx : int
            Index of treatment

        Returns
        -------
        linear_pred : float
            Linear predictor value
        """
        beta = params[:self.n_components]
        components = self.component_matrix[treatment_idx, :]
        return np.dot(components, beta)

    def _composite_log_likelihood(
        self,
        params: np.ndarray
    ) -> float:
        """
        Compute composite log-likelihood.

        The composite likelihood is the product of arm-level likelihoods:
            CL = ∏_i L(θ | y_i)

        Parameters
        ----------
        params : np.ndarray
            Parameter vector

        Returns
        -------
        log_lik : float
            Composite log-likelihood value
        """
        beta = params[:self.n_components]

        # Get unique studies
        studies = self.data['study'].unique()
        n_studies = len(studies)

        # Study-specific baseline parameters
        mu_study = params[self.n_components:self.n_components + n_studies]

        # Between-study heterogeneity
        tau = params[-1]

        log_lik = 0.0

        # Iterate over all arms (composite likelihood)
        for idx, row in self.data.iterrows():
            study = row['study']
            study_idx = list(studies).index(study)
            treatment = row['treatment']
            y_obs = row['y']
            se_obs = row['se']

            # Find treatment index (assuming treatments are ordered)
            # This needs treatment mapping
            treatment_names = self.data['treatment'].unique()
            treatment_idx = list(treatment_names).index(treatment)

            # Linear predictor
            if self.model_type == 'additive':
                eta = mu_study[study_idx] + self._additive_linear_predictor(params, treatment_idx)
            else:
                raise NotImplementedError("Interaction model not yet implemented for composite likelihood")

            # Arm-level likelihood contribution
            # Incorporate both sampling variance and between-study heterogeneity
            total_var = se_obs**2 + tau**2

            if self.outcome_type == 'continuous':
                # Normal likelihood
                log_lik += norm.logpdf(y_obs, loc=eta, scale=np.sqrt(total_var))
            else:
                raise NotImplementedError(f"Outcome type {self.outcome_type} not implemented")

        return log_lik

    def _composite_neg_log_likelihood(self, params: np.ndarray) -> float:
        """
        Negative composite log-likelihood for minimization.

        Parameters
        ----------
        params : np.ndarray
            Parameter vector

        Returns
        -------
        neg_log_lik : float
            Negative composite log-likelihood
        """
        # Add bounds to prevent numerical issues
        tau = params[-1]
        if tau < 0:
            return 1e10

        try:
            return -self._composite_log_likelihood(params)
        except:
            return 1e10

    def fit(
        self,
        initial_params: Optional[np.ndarray] = None,
        method: str = 'L-BFGS-B',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fit model using composite likelihood estimation.

        Parameters
        ----------
        initial_params : np.ndarray, optional
            Initial parameter values
        method : str
            Optimization method
        **kwargs : dict
            Additional arguments for scipy.optimize.minimize

        Returns
        -------
        results : dict
            Estimation results including parameter estimates and standard errors
        """
        n_studies = len(self.data['study'].unique())
        n_params = self.n_components + n_studies + 1  # beta + mu_study + tau

        # Initialize parameters
        if initial_params is None:
            initial_params = np.zeros(n_params)
            initial_params[-1] = 0.5  # Initial tau

        # Set bounds
        bounds = [(None, None)] * (n_params - 1) + [(0.001, 10)]  # tau > 0

        # Optimize
        result = optimize.minimize(
            self._composite_neg_log_likelihood,
            initial_params,
            method=method,
            bounds=bounds,
            **kwargs
        )

        if not result.success:
            print(f"Warning: Optimization did not converge. Message: {result.message}")

        self.estimates = result.x

        # Compute variance-covariance matrix using sandwich estimator
        self.vcov = self._compute_sandwich_variance(self.estimates)

        self.fitted = True

        # Store results
        results = {
            'estimates': self.estimates,
            'vcov': self.vcov,
            'se': np.sqrt(np.diag(self.vcov)),
            'success': result.success,
            'message': result.message,
            'log_likelihood': -result.fun,
        }

        return results

    def _compute_sandwich_variance(
        self,
        params: np.ndarray,
        epsilon: float = 1e-5
    ) -> np.ndarray:
        """
        Compute sandwich variance estimator for composite likelihood.

        The sandwich variance estimator accounts for the fact that the composite
        likelihood uses marginal likelihoods rather than the full likelihood.

        V = H^{-1} J H^{-1}

        where H is the Hessian and J is the variance of the score.

        Parameters
        ----------
        params : np.ndarray
            Parameter estimates
        epsilon : float
            Step size for numerical derivatives

        Returns
        -------
        vcov : np.ndarray
            Variance-covariance matrix
        """
        n_params = len(params)

        # Compute Hessian numerically
        hessian = self._numerical_hessian(params, epsilon)

        # Compute J matrix (outer product of scores)
        scores = self._compute_arm_scores(params)
        J = scores.T @ scores

        try:
            # Sandwich: H^{-1} J H^{-1}
            H_inv = np.linalg.inv(hessian)
            vcov = H_inv @ J @ H_inv
        except np.linalg.LinAlgError:
            # If Hessian is singular, use pseudo-inverse
            H_inv = np.linalg.pinv(hessian)
            vcov = H_inv @ J @ H_inv

        return vcov

    def _numerical_hessian(
        self,
        params: np.ndarray,
        epsilon: float = 1e-5
    ) -> np.ndarray:
        """
        Compute numerical Hessian of negative log-likelihood.

        Parameters
        ----------
        params : np.ndarray
            Parameter values
        epsilon : float
            Step size

        Returns
        -------
        hessian : np.ndarray
            Hessian matrix
        """
        n = len(params)
        hessian = np.zeros((n, n))

        for i in range(n):
            for j in range(n):
                if i <= j:
                    # Compute second derivative
                    params_pp = params.copy()
                    params_pm = params.copy()
                    params_mp = params.copy()
                    params_mm = params.copy()

                    params_pp[i] += epsilon
                    params_pp[j] += epsilon

                    params_pm[i] += epsilon
                    params_pm[j] -= epsilon

                    params_mp[i] -= epsilon
                    params_mp[j] += epsilon

                    params_mm[i] -= epsilon
                    params_mm[j] -= epsilon

                    f_pp = self._composite_neg_log_likelihood(params_pp)
                    f_pm = self._composite_neg_log_likelihood(params_pm)
                    f_mp = self._composite_neg_log_likelihood(params_mp)
                    f_mm = self._composite_neg_log_likelihood(params_mm)

                    hessian[i, j] = (f_pp - f_pm - f_mp + f_mm) / (4 * epsilon**2)
                    hessian[j, i] = hessian[i, j]

        return hessian

    def _compute_arm_scores(self, params: np.ndarray) -> np.ndarray:
        """
        Compute score (gradient) for each arm.

        Parameters
        ----------
        params : np.ndarray
            Parameter values

        Returns
        -------
        scores : np.ndarray
            Score matrix (n_arms × n_params)
        """
        n_arms = len(self.data)
        n_params = len(params)
        scores = np.zeros((n_arms, n_params))

        epsilon = 1e-6

        for arm_idx in range(n_arms):
            for param_idx in range(n_params):
                params_plus = params.copy()
                params_minus = params.copy()

                params_plus[param_idx] += epsilon
                params_minus[param_idx] -= epsilon

                # Compute arm-specific log-likelihood contribution
                ll_plus = self._arm_log_likelihood(arm_idx, params_plus)
                ll_minus = self._arm_log_likelihood(arm_idx, params_minus)

                scores[arm_idx, param_idx] = (ll_plus - ll_minus) / (2 * epsilon)

        return scores

    def _arm_log_likelihood(self, arm_idx: int, params: np.ndarray) -> float:
        """
        Compute log-likelihood contribution for a single arm.

        Parameters
        ----------
        arm_idx : int
            Index of arm in data
        params : np.ndarray
            Parameter values

        Returns
        -------
        log_lik : float
            Log-likelihood contribution
        """
        beta = params[:self.n_components]
        studies = self.data['study'].unique()
        n_studies = len(studies)
        mu_study = params[self.n_components:self.n_components + n_studies]
        tau = params[-1]

        row = self.data.iloc[arm_idx]
        study = row['study']
        study_idx = list(studies).index(study)
        treatment = row['treatment']
        y_obs = row['y']
        se_obs = row['se']

        treatment_names = self.data['treatment'].unique()
        treatment_idx = list(treatment_names).index(treatment)

        if self.model_type == 'additive':
            eta = mu_study[study_idx] + self._additive_linear_predictor(params, treatment_idx)
        else:
            raise NotImplementedError()

        total_var = se_obs**2 + tau**2

        if self.outcome_type == 'continuous':
            return norm.logpdf(y_obs, loc=eta, scale=np.sqrt(total_var))
        else:
            raise NotImplementedError()

    def get_component_effects(self, components: List[str]) -> pd.DataFrame:
        """
        Extract component effect estimates with confidence intervals.

        Parameters
        ----------
        components : list
            List of component names

        Returns
        -------
        effects : pd.DataFrame
            Component effects with confidence intervals
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted first")

        beta = self.estimates[:self.n_components]
        se = np.sqrt(np.diag(self.vcov))[:self.n_components]

        effects = []
        for i, component in enumerate(components):
            effects.append({
                'component': component,
                'estimate': beta[i],
                'se': se[i],
                'ci_lower': beta[i] - 1.96 * se[i],
                'ci_upper': beta[i] + 1.96 * se[i],
                'z_score': beta[i] / se[i],
                'p_value': 2 * (1 - norm.cdf(np.abs(beta[i] / se[i]))),
            })

        return pd.DataFrame(effects)

    def predict(
        self,
        component_vector: np.ndarray,
        confidence_level: float = 0.95
    ) -> Dict[str, float]:
        """
        Predict treatment effect for a given component combination.

        Parameters
        ----------
        component_vector : np.ndarray
            Binary vector indicating component presence
        confidence_level : float
            Confidence level for interval

        Returns
        -------
        prediction : dict
            Point estimate and confidence interval
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted first")

        beta = self.estimates[:self.n_components]
        vcov_beta = self.vcov[:self.n_components, :self.n_components]

        # Point prediction
        pred = np.dot(component_vector, beta)

        # Standard error
        se = np.sqrt(component_vector @ vcov_beta @ component_vector)

        # Confidence interval
        z = norm.ppf((1 + confidence_level) / 2)
        ci_lower = pred - z * se
        ci_upper = pred + z * se

        return {
            'estimate': pred,
            'se': se,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'confidence_level': confidence_level,
        }
