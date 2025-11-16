"""
Network construction and analysis for CNMA.
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
import networkx as nx


class NetworkBuilder:
    """
    Build and analyze component networks.

    Creates treatment networks and component networks for visualization
    and network analysis.
    """

    def __init__(self, data: pd.DataFrame):
        """
        Initialize network builder.

        Parameters
        ----------
        data : pd.DataFrame
            CNMA dataset
        """
        self.data = data
        self.treatment_network: Optional[nx.Graph] = None
        self.component_network: Optional[nx.Graph] = None

    def build_treatment_network(self) -> nx.Graph:
        """
        Build treatment comparison network.

        Each node is a treatment, edges represent direct comparisons.

        Returns
        -------
        network : nx.Graph
            Treatment network
        """
        G = nx.Graph()

        # Get unique treatments
        treatments = set()
        if 'treatment' in self.data.columns:
            treatments.update(self.data['treatment'].unique())
        if 'treatment_1' in self.data.columns:
            treatments.update(self.data['treatment_1'].unique())
            treatments.update(self.data['treatment_2'].unique())

        # Add nodes
        for treatment in treatments:
            G.add_node(treatment)

        # Add edges (direct comparisons)
        if 'treatment_1' in self.data.columns:
            # Contrast format
            for _, row in self.data.iterrows():
                t1 = row['treatment_1']
                t2 = row['treatment_2']
                if G.has_edge(t1, t2):
                    G[t1][t2]['weight'] += 1
                else:
                    G.add_edge(t1, t2, weight=1)
        else:
            # Arm format - group by study
            for study, group in self.data.groupby('study'):
                treatments_in_study = group['treatment'].unique()
                # Add edge for each pairwise comparison in study
                for i, t1 in enumerate(treatments_in_study):
                    for t2 in treatments_in_study[i+1:]:
                        if G.has_edge(t1, t2):
                            G[t1][t2]['weight'] += 1
                        else:
                            G.add_edge(t1, t2, weight=1)

        self.treatment_network = G
        return G

    def build_component_network(
        self,
        component_matrix: pd.DataFrame
    ) -> nx.Graph:
        """
        Build component co-occurrence network.

        Each node is a component, edges represent co-occurrence in treatments.

        Parameters
        ----------
        component_matrix : pd.DataFrame
            Binary matrix of components × treatments

        Returns
        -------
        network : nx.Graph
            Component network
        """
        G = nx.Graph()

        # Add component nodes
        components = component_matrix.columns.tolist()
        for comp in components:
            G.add_node(comp)

        # Add edges based on co-occurrence
        matrix = component_matrix.values

        for i in range(len(components)):
            for j in range(i + 1, len(components)):
                # Count co-occurrence
                co_occur = np.sum(matrix[:, i] * matrix[:, j])

                if co_occur > 0:
                    G.add_edge(
                        components[i],
                        components[j],
                        weight=int(co_occur)
                    )

        self.component_network = G
        return G

    def get_network_stats(self, network: nx.Graph) -> Dict:
        """
        Calculate network statistics.

        Parameters
        ----------
        network : nx.Graph
            Network to analyze

        Returns
        -------
        stats : dict
            Dictionary of network statistics
        """
        stats = {
            'n_nodes': network.number_of_nodes(),
            'n_edges': network.number_of_edges(),
            'density': nx.density(network),
            'connected': nx.is_connected(network),
        }

        if nx.is_connected(network):
            stats['diameter'] = nx.diameter(network)
            stats['avg_path_length'] = nx.average_shortest_path_length(network)
        else:
            stats['n_components'] = nx.number_connected_components(network)

        # Degree statistics
        degrees = [d for n, d in network.degree()]
        stats['avg_degree'] = np.mean(degrees)
        stats['max_degree'] = np.max(degrees)
        stats['min_degree'] = np.min(degrees)

        return stats

    def identify_treatment_clusters(
        self,
        component_matrix: pd.DataFrame,
        n_clusters: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Cluster treatments based on component similarity.

        Parameters
        ----------
        component_matrix : pd.DataFrame
            Binary component matrix
        n_clusters : int, optional
            Number of clusters (auto-determined if None)

        Returns
        -------
        clusters : pd.DataFrame
            Treatment cluster assignments
        """
        from sklearn.cluster import AgglomerativeClustering
        from scipy.cluster.hierarchy import dendrogram, linkage

        matrix = component_matrix.values

        if n_clusters is None:
            # Auto-determine using silhouette score
            from sklearn.metrics import silhouette_score

            best_score = -1
            best_k = 2

            for k in range(2, min(10, len(matrix) - 1)):
                clusterer = AgglomerativeClustering(n_clusters=k)
                labels = clusterer.fit_predict(matrix)

                if len(np.unique(labels)) > 1:
                    score = silhouette_score(matrix, labels)
                    if score > best_score:
                        best_score = score
                        best_k = k

            n_clusters = best_k

        # Perform clustering
        clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        labels = clusterer.fit_predict(matrix)

        results = pd.DataFrame({
            'treatment': component_matrix.index,
            'cluster': labels,
        })

        return results

    def calculate_treatment_complexity(
        self,
        component_matrix: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate complexity metrics for each treatment.

        Parameters
        ----------
        component_matrix : pd.DataFrame
            Binary component matrix

        Returns
        -------
        complexity : pd.DataFrame
            Complexity metrics for each treatment
        """
        results = []

        for treatment in component_matrix.index:
            n_components = component_matrix.loc[treatment].sum()

            results.append({
                'treatment': treatment,
                'n_components': int(n_components),
                'complexity': 'simple' if n_components <= 1 else
                             'moderate' if n_components <= 2 else
                             'complex',
            })

        return pd.DataFrame(results)

    def check_network_connectivity(self) -> Dict[str, any]:
        """
        Check if treatment network is connected and identify disconnected components.

        Returns
        -------
        connectivity : dict
            Network connectivity information
        """
        if self.treatment_network is None:
            self.build_treatment_network()

        G = self.treatment_network

        is_connected = nx.is_connected(G)

        connectivity = {
            'connected': is_connected,
            'n_nodes': G.number_of_nodes(),
            'n_edges': G.number_of_edges(),
        }

        if not is_connected:
            # Identify connected components
            components = list(nx.connected_components(G))
            connectivity['n_components'] = len(components)
            connectivity['component_sizes'] = [len(c) for c in components]
            connectivity['components'] = components
        else:
            connectivity['n_components'] = 1

        return connectivity

    def get_indirect_comparisons(self) -> pd.DataFrame:
        """
        Identify pairs of treatments with only indirect comparisons.

        Returns
        -------
        indirect : pd.DataFrame
            Pairs of treatments with indirect comparisons only
        """
        if self.treatment_network is None:
            self.build_treatment_network()

        G = self.treatment_network
        treatments = list(G.nodes())

        indirect_pairs = []

        for i, t1 in enumerate(treatments):
            for t2 in treatments[i+1:]:
                if not G.has_edge(t1, t2):
                    # Check if there's an indirect path
                    if nx.has_path(G, t1, t2):
                        path_length = nx.shortest_path_length(G, t1, t2)
                        indirect_pairs.append({
                            'treatment_1': t1,
                            'treatment_2': t2,
                            'path_length': path_length,
                        })

        return pd.DataFrame(indirect_pairs)
