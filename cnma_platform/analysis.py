"""
Main CNMA analysis class that integrates all components.
"""

from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from cnma_platform.models.additive_model import AdditiveModel
from cnma_platform.models.interaction_model import InteractionModel
from cnma_platform.models.composite_likelihood import CompositeLikelihood
from cnma_platform.nlp.component_extractor import ComponentExtractor
from cnma_platform.data.network_builder import NetworkBuilder
from cnma_platform.visualization import plots


class CNMAAnalysis:
    """
    Main class for conducting Component Network Meta-Analysis.

    This class provides a high-level interface for:
    - Loading and validating data
    - Extracting components from intervention descriptions
    - Fitting CNMA models (additive, interaction, composite likelihood)
    - Visualizing results
    - Making predictions
    """

    def __init__(
        self,
        data: pd.DataFrame,
        model_type: str = "additive",
        likelihood: str = "bayesian",
        outcome_type: str = "continuous",
        reference_treatment: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize CNMA analysis.

        Parameters
        ----------
        data : pd.DataFrame
            Dataset with study information and outcomes
        model_type : str
            Type of model: 'additive' or 'interaction'
        likelihood : str
            Likelihood approach: 'bayesian' or 'composite'
        outcome_type : str
            Type of outcome: 'continuous', 'binary', or 'count'
        reference_treatment : str, optional
            Reference treatment for relative effects
        **kwargs : dict
            Additional model parameters
        """
        self.data = data
        self.model_type = model_type
        self.likelihood = likelihood
        self.outcome_type = outcome_type
        self.reference_treatment = reference_treatment
        self.kwargs = kwargs

        # Components
        self.component_extractor: Optional[ComponentExtractor] = None
        self.components: List[str] = []
        self.component_matrix: Optional[np.ndarray] = None

        # Model
        self.model = None
        self.fitted = False

        # Network
        self.network_builder = NetworkBuilder(data)

        # Results
        self.results: Dict[str, Any] = {}

    def extract_components(
        self,
        description_col: str = "description",
        method: str = "hybrid",
        domain: str = "general",
        **extractor_kwargs
    ) -> pd.DataFrame:
        """
        Extract components from intervention descriptions.

        Parameters
        ----------
        description_col : str
            Column containing intervention descriptions
        method : str
            Extraction method: 'keyword', 'tfidf', 'hybrid'
        domain : str
            Intervention domain
        **extractor_kwargs : dict
            Additional arguments for ComponentExtractor

        Returns
        -------
        component_matrix : pd.DataFrame
            Binary component matrix
        """
        if description_col not in self.data.columns:
            raise ValueError(f"Column '{description_col}' not found in data")

        # Initialize extractor
        self.component_extractor = ComponentExtractor(
            domain=domain,
            **extractor_kwargs
        )

        # Extract components
        descriptions = self.data[description_col].tolist()
        intervention_components, all_components = self.component_extractor.extract_components(
            descriptions, method=method
        )

        self.components = all_components

        # Create component matrix
        component_df = self.component_extractor.create_component_matrix(
            intervention_components, all_components
        )

        self.component_matrix = component_df.values

        # Add components to data
        for i, comp in enumerate(all_components):
            self.data[f'comp_{comp}'] = self.component_matrix[:, i]

        print(f"Extracted {len(all_components)} components:")
        for comp in all_components:
            print(f"  - {comp}")

        return component_df

    def set_components(
        self,
        component_col: str = "components",
        separator: str = ","
    ) -> None:
        """
        Set components from existing column in data.

        Parameters
        ----------
        component_col : str
            Column containing component information
        separator : str
            Separator for component strings
        """
        if component_col not in self.data.columns:
            raise ValueError(f"Column '{component_col}' not found in data")

        # Extract unique components
        all_components = set()
        treatment_components = {}

        for idx, row in self.data.iterrows():
            comp_str = row[component_col]
            if pd.notna(comp_str) and comp_str != '':
                if isinstance(comp_str, str):
                    components = [c.strip() for c in comp_str.split(separator)]
                else:
                    components = list(comp_str)
                treatment_components[idx] = components
                all_components.update(components)
            else:
                treatment_components[idx] = []

        self.components = sorted(all_components)

        # Build component matrix
        n_obs = len(self.data)
        n_components = len(self.components)
        self.component_matrix = np.zeros((n_obs, n_components), dtype=int)

        for idx, components in treatment_components.items():
            for comp in components:
                if comp in self.components:
                    j = self.components.index(comp)
                    self.component_matrix[idx, j] = 1

        print(f"Identified {n_components} components:")
        for comp in self.components:
            print(f"  - {comp}")

    def build_model(self) -> Any:
        """
        Build the CNMA model.

        Returns
        -------
        model
            The built model object
        """
        if self.component_matrix is None:
            raise RuntimeError("Components not set. Call extract_components() or set_components() first.")

        # Prepare data with component information
        model_data = self.data.copy()

        if self.likelihood == "bayesian":
            if self.model_type == "additive":
                self.model = AdditiveModel(
                    data=model_data,
                    outcome_type=self.outcome_type,
                    reference_treatment=self.reference_treatment,
                    **self.kwargs
                )
            elif self.model_type == "interaction":
                self.model = InteractionModel(
                    data=model_data,
                    outcome_type=self.outcome_type,
                    reference_treatment=self.reference_treatment,
                    **self.kwargs
                )
            else:
                raise ValueError(f"Unknown model type: {self.model_type}")

            # Set component matrix
            self.model.components = self.components
            self.model.component_matrix = self.component_matrix
            self.model.n_components = len(self.components)

            # Build PyMC model
            self.model.build_model()

        elif self.likelihood == "composite":
            self.model = CompositeLikelihood(
                data=model_data,
                component_matrix=self.component_matrix,
                model_type=self.model_type,
                outcome_type=self.outcome_type
            )
        else:
            raise ValueError(f"Unknown likelihood: {self.likelihood}")

        return self.model

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
            Number of posterior samples (for Bayesian)
        n_warmup : int
            Number of warmup samples (for Bayesian)
        n_chains : int
            Number of MCMC chains (for Bayesian)
        **kwargs : dict
            Additional fitting parameters

        Returns
        -------
        results : dict
            Model fitting results
        """
        if self.model is None:
            self.build_model()

        print(f"Fitting {self.model_type} CNMA model with {self.likelihood} inference...")

        if self.likelihood == "bayesian":
            self.results = self.model.fit(
                n_samples=n_samples,
                n_warmup=n_warmup,
                n_chains=n_chains,
                **kwargs
            )
        else:
            self.results = self.model.fit(**kwargs)

        self.fitted = True
        print("Model fitting complete!")

        return self.results

    def summary(self) -> pd.DataFrame:
        """
        Generate summary of model results.

        Returns
        -------
        summary : pd.DataFrame
            Summary statistics
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted first")

        return self.model.summary()

    def get_component_effects(self) -> pd.DataFrame:
        """
        Get estimated component effects.

        Returns
        -------
        effects : pd.DataFrame
            Component effect estimates
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted first")

        if self.likelihood == "composite":
            return self.model.get_component_effects(self.components)
        else:
            return self.model.get_component_effects()

    def get_interaction_effects(self) -> pd.DataFrame:
        """
        Get interaction effects (for interaction model only).

        Returns
        -------
        interactions : pd.DataFrame
            Interaction effect estimates
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted first")

        if self.model_type != "interaction":
            raise ValueError("Interaction effects only available for interaction model")

        return self.model.get_interaction_effects()

    def predict(
        self,
        treatment_1: str,
        treatment_2: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Predict relative effect between two treatments.

        Parameters
        ----------
        treatment_1 : str
            First treatment (baseline)
        treatment_2 : str
            Second treatment (comparison)
        **kwargs : dict
            Additional prediction parameters

        Returns
        -------
        prediction : dict
            Predicted effect with uncertainty
        """
        if not self.fitted:
            raise RuntimeError("Model must be fitted first")

        return self.model.predict(treatment_1, treatment_2, **kwargs)

    def plot_network(self, **kwargs) -> plt.Axes:
        """
        Plot treatment network.

        Parameters
        ----------
        **kwargs : dict
            Arguments for plot_network()

        Returns
        -------
        ax : plt.Axes
            Matplotlib axes
        """
        network = self.network_builder.build_treatment_network()
        return plots.plot_network(network, **kwargs)

    def plot_component_effects(self, **kwargs) -> plt.Axes:
        """
        Plot component effects.

        Parameters
        ----------
        **kwargs : dict
            Arguments for plot_component_effects()

        Returns
        -------
        ax : plt.Axes
            Matplotlib axes
        """
        effects = self.get_component_effects()
        return plots.plot_component_effects(effects, **kwargs)

    def plot_rankings(self, **kwargs) -> plt.Axes:
        """
        Plot treatment rankings.

        Parameters
        ----------
        **kwargs : dict
            Arguments for plot_rankogram()

        Returns
        -------
        ax : plt.Axes
            Matplotlib axes
        """
        if self.likelihood != "bayesian":
            raise ValueError("Rankings only available for Bayesian models")

        rankings = self.model.get_treatment_ranking()
        return plots.plot_rankogram(rankings, **kwargs)

    def plot_interaction_effects(self, **kwargs) -> plt.Axes:
        """
        Plot interaction effects.

        Parameters
        ----------
        **kwargs : dict
            Arguments for plot_interaction_effects()

        Returns
        -------
        ax : plt.Axes
            Matplotlib axes
        """
        interactions = self.get_interaction_effects()
        return plots.plot_interaction_effects(interactions, **kwargs)

    def get_network_stats(self) -> Dict:
        """
        Get network statistics.

        Returns
        -------
        stats : dict
            Network statistics
        """
        network = self.network_builder.build_treatment_network()
        return self.network_builder.get_network_stats(network)
