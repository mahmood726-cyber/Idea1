"""
Base class for CNMA models.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
import numpy as np
import pandas as pd


class BaseCNMAModel(ABC):
    """
    Abstract base class for Component Network Meta-Analysis models.

    All CNMA models should inherit from this class and implement the required methods.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        outcome_type: str = "continuous",
        reference_treatment: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the base CNMA model.

        Parameters
        ----------
        data : pd.DataFrame
            Dataset containing study information, treatments, and outcomes
        outcome_type : str
            Type of outcome: 'continuous', 'binary', or 'count'
        reference_treatment : str, optional
            Reference treatment for relative effects (default: treatment with most studies)
        **kwargs : dict
            Additional model-specific parameters
        """
        self.data = data.copy()
        self.outcome_type = outcome_type
        self.reference_treatment = reference_treatment
        self.kwargs = kwargs

        # Will be populated during preprocessing
        self.components: List[str] = []
        self.treatments: List[str] = []
        self.component_matrix: np.ndarray = None
        self.n_components: int = 0
        self.n_treatments: int = 0
        self.n_studies: int = 0

        # Model results
        self.fitted = False
        self.trace = None
        self.results: Dict[str, Any] = {}

    @abstractmethod
    def build_model(self) -> Any:
        """
        Build the statistical model.

        Returns
        -------
        model
            The built statistical model (e.g., PyMC model)
        """
        pass

    @abstractmethod
    def fit(
        self,
        n_samples: int = 2000,
        n_warmup: int = 1000,
        n_chains: int = 4,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Fit the CNMA model.

        Parameters
        ----------
        n_samples : int
            Number of posterior samples per chain
        n_warmup : int
            Number of warmup samples
        n_chains : int
            Number of MCMC chains
        **kwargs : dict
            Additional sampling parameters

        Returns
        -------
        results : dict
            Dictionary containing fitted parameters and diagnostics
        """
        pass

    def preprocess_data(self) -> None:
        """
        Preprocess the data and extract component information.
        """
        # Extract unique treatments
        if 'treatment' in self.data.columns:
            self.treatments = sorted(self.data['treatment'].unique())
        elif 'treatment_1' in self.data.columns:
            # Handle arm-based format
            treatments = set()
            for col in self.data.columns:
                if col.startswith('treatment_'):
                    treatments.update(self.data[col].dropna().unique())
            self.treatments = sorted(treatments)

        self.n_treatments = len(self.treatments)
        self.n_studies = len(self.data['study'].unique()) if 'study' in self.data.columns else len(self.data)

    def extract_components(self, component_col: str = 'components') -> np.ndarray:
        """
        Extract component matrix from treatment descriptions.

        Parameters
        ----------
        component_col : str
            Column name containing component information

        Returns
        -------
        component_matrix : np.ndarray
            Binary matrix of shape (n_treatments, n_components)
        """
        if component_col not in self.data.columns:
            raise ValueError(f"Column '{component_col}' not found in data")

        # Get unique components across all treatments
        all_components = set()
        treatment_components = {}

        for treatment in self.treatments:
            mask = self.data['treatment'] == treatment
            if mask.any():
                comp_str = self.data.loc[mask, component_col].iloc[0]
                if pd.notna(comp_str):
                    if isinstance(comp_str, str):
                        components = [c.strip() for c in comp_str.split(',')]
                    else:
                        components = list(comp_str)
                    treatment_components[treatment] = components
                    all_components.update(components)
                else:
                    treatment_components[treatment] = []
            else:
                treatment_components[treatment] = []

        self.components = sorted(all_components)
        self.n_components = len(self.components)

        # Build component matrix
        component_matrix = np.zeros((self.n_treatments, self.n_components), dtype=int)
        for i, treatment in enumerate(self.treatments):
            for j, component in enumerate(self.components):
                if component in treatment_components.get(treatment, []):
                    component_matrix[i, j] = 1

        self.component_matrix = component_matrix
        return component_matrix

    def predict(
        self,
        treatment_1: Union[str, List[str]],
        treatment_2: Union[str, List[str]],
        **kwargs
    ) -> Dict[str, np.ndarray]:
        """
        Predict relative treatment effect.

        Parameters
        ----------
        treatment_1 : str or list
            First treatment (baseline) or list of components
        treatment_2 : str or list
            Second treatment (comparison) or list of components
        **kwargs : dict
            Additional prediction parameters

        Returns
        -------
        predictions : dict
            Dictionary with 'mean', 'sd', 'quantiles' for the relative effect
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before making predictions")

        # Implementation will be model-specific
        raise NotImplementedError("Subclasses must implement predict()")

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

        raise NotImplementedError("Subclasses must implement get_component_effects()")

    def summary(self) -> pd.DataFrame:
        """
        Generate summary statistics for model parameters.

        Returns
        -------
        summary : pd.DataFrame
            Summary statistics including means, SDs, and credible intervals
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted before generating summary")

        raise NotImplementedError("Subclasses must implement summary()")
