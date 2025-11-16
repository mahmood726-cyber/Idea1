"""
Plotting functions for CNMA visualization.
"""

from typing import Optional, Tuple, Dict, List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from matplotlib.patches import Rectangle


def plot_network(
    network: nx.Graph,
    layout: str = "spring",
    node_size: int = 1000,
    font_size: int = 10,
    figsize: Tuple[int, int] = (12, 8),
    title: str = "Treatment Network",
    show_weights: bool = True,
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """
    Plot treatment or component network.

    Parameters
    ----------
    network : nx.Graph
        Network to plot
    layout : str
        Layout algorithm: 'spring', 'circular', 'kamada_kawai'
    node_size : int
        Size of nodes
    font_size : int
        Font size for labels
    figsize : tuple
        Figure size
    title : str
        Plot title
    show_weights : bool
        Show edge weights
    ax : plt.Axes, optional
        Axes to plot on

    Returns
    -------
    ax : plt.Axes
        Matplotlib axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    # Choose layout
    if layout == "spring":
        pos = nx.spring_layout(network, seed=42, k=2)
    elif layout == "circular":
        pos = nx.circular_layout(network)
    elif layout == "kamada_kawai":
        pos = nx.kamada_kawai_layout(network)
    else:
        pos = nx.spring_layout(network, seed=42)

    # Draw network
    nx.draw_networkx_nodes(
        network, pos,
        node_color='lightblue',
        node_size=node_size,
        ax=ax
    )

    # Draw edges with varying width based on weight
    edges = network.edges()
    if show_weights and nx.get_edge_attributes(network, 'weight'):
        weights = [network[u][v].get('weight', 1) for u, v in edges]
        max_weight = max(weights) if weights else 1

        nx.draw_networkx_edges(
            network, pos,
            width=[3 * w / max_weight for w in weights],
            alpha=0.6,
            ax=ax
        )

        # Draw edge labels
        edge_labels = {(u, v): network[u][v]['weight'] for u, v in edges}
        nx.draw_networkx_edge_labels(
            network, pos,
            edge_labels,
            font_size=font_size - 2,
            ax=ax
        )
    else:
        nx.draw_networkx_edges(network, pos, alpha=0.6, ax=ax)

    # Draw labels
    nx.draw_networkx_labels(
        network, pos,
        font_size=font_size,
        font_weight='bold',
        ax=ax
    )

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.axis('off')

    return ax


def plot_component_effects(
    effects: pd.DataFrame,
    figsize: Tuple[int, int] = (10, 6),
    title: str = "Component Effects",
    xlabel: str = "Effect Size",
    sort_by: str = "mean",
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """
    Plot component effects with credible intervals.

    Parameters
    ----------
    effects : pd.DataFrame
        DataFrame with component effects (from model.get_component_effects())
    figsize : tuple
        Figure size
    title : str
        Plot title
    xlabel : str
        X-axis label
    sort_by : str
        Sort components by: 'mean', 'name'
    ax : plt.Axes, optional
        Axes to plot on

    Returns
    -------
    ax : plt.Axes
        Matplotlib axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    # Sort effects
    if sort_by == "mean":
        effects = effects.sort_values('mean')
    elif sort_by == "name":
        effects = effects.sort_values('component')

    components = effects['component'].values
    means = effects['mean'].values
    lower = effects['q2.5'].values if 'q2.5' in effects.columns else effects.get('ci_lower', means)
    upper = effects['q97.5'].values if 'q97.5' in effects.columns else effects.get('ci_upper', means)

    y_pos = np.arange(len(components))

    # Plot
    ax.errorbar(
        means, y_pos,
        xerr=[means - lower, upper - means],
        fmt='o',
        markersize=8,
        capsize=5,
        capthick=2,
        linewidth=2,
        color='navy',
        ecolor='steelblue'
    )

    # Add zero line
    ax.axvline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(components)
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel('Component', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    return ax


def plot_forest(
    data: pd.DataFrame,
    group_col: str = "study",
    effect_col: str = "y",
    se_col: str = "se",
    label_col: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 8),
    title: str = "Forest Plot",
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """
    Create forest plot for meta-analysis.

    Parameters
    ----------
    data : pd.DataFrame
        Data to plot
    group_col : str
        Column for grouping (e.g., study names)
    effect_col : str
        Column with effect sizes
    se_col : str
        Column with standard errors
    label_col : str, optional
        Column for custom labels
    figsize : tuple
        Figure size
    title : str
        Plot title
    ax : plt.Axes, optional
        Axes to plot on

    Returns
    -------
    ax : plt.Axes
        Matplotlib axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    effects = data[effect_col].values
    se = data[se_col].values

    if label_col:
        labels = data[label_col].values
    else:
        labels = data[group_col].values

    y_pos = np.arange(len(labels))

    # Calculate confidence intervals
    lower = effects - 1.96 * se
    upper = effects + 1.96 * se

    # Plot
    ax.errorbar(
        effects, y_pos,
        xerr=[effects - lower, upper - effects],
        fmt='s',
        markersize=6,
        capsize=4,
        linewidth=1.5,
        color='darkgreen',
        ecolor='green',
        alpha=0.7
    )

    # Zero line
    ax.axvline(0, color='black', linestyle='--', linewidth=1)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel('Effect Size (95% CI)', fontsize=11)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    return ax


def plot_rankogram(
    rankings: pd.DataFrame,
    figsize: Tuple[int, int] = (12, 6),
    title: str = "Treatment Rankings (SUCRA)",
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """
    Plot treatment rankings with SUCRA values.

    Parameters
    ----------
    rankings : pd.DataFrame
        DataFrame with treatment rankings (from model.get_treatment_ranking())
    figsize : tuple
        Figure size
    title : str
        Plot title
    ax : plt.Axes, optional
        Axes to plot on

    Returns
    -------
    ax : plt.Axes
        Matplotlib axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    # Sort by SUCRA
    rankings = rankings.sort_values('sucra', ascending=False)

    treatments = rankings['treatment'].values
    sucra = rankings['sucra'].values

    y_pos = np.arange(len(treatments))

    # Create bar plot
    bars = ax.barh(y_pos, sucra, color='steelblue', alpha=0.7)

    # Color bars by SUCRA value
    colors = plt.cm.RdYlGn(sucra)
    for bar, color in zip(bars, colors):
        bar.set_color(color)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(treatments)
    ax.set_xlabel('SUCRA', fontsize=12)
    ax.set_xlim(0, 1)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    # Add value labels
    for i, (pos, val) in enumerate(zip(y_pos, sucra)):
        ax.text(val + 0.02, pos, f'{val:.2f}', va='center', fontsize=9)

    return ax


def plot_comparison_matrix(
    predictions: pd.DataFrame,
    value_col: str = "mean",
    figsize: Tuple[int, int] = (10, 10),
    title: str = "Treatment Comparison Matrix",
    cmap: str = "RdBu_r",
    annot: bool = True,
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """
    Plot heatmap of all pairwise treatment comparisons.

    Parameters
    ----------
    predictions : pd.DataFrame
        DataFrame with treatment_1, treatment_2, and effect estimates
    value_col : str
        Column with values to plot
    figsize : tuple
        Figure size
    title : str
        Plot title
    cmap : str
        Colormap name
    annot : bool
        Annotate cells with values
    ax : plt.Axes, optional
        Axes to plot on

    Returns
    -------
    ax : plt.Axes
        Matplotlib axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    # Create matrix
    treatments = sorted(set(predictions['treatment_1'].unique()) |
                       set(predictions['treatment_2'].unique()))

    n = len(treatments)
    matrix = np.zeros((n, n))

    for _, row in predictions.iterrows():
        i = treatments.index(row['treatment_1'])
        j = treatments.index(row['treatment_2'])
        matrix[i, j] = row[value_col]
        matrix[j, i] = -row[value_col]  # Reverse direction

    # Plot heatmap
    sns.heatmap(
        matrix,
        xticklabels=treatments,
        yticklabels=treatments,
        cmap=cmap,
        center=0,
        annot=annot,
        fmt='.2f' if annot else '',
        cbar_kws={'label': 'Effect Size'},
        ax=ax
    )

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Treatment', fontsize=12)
    ax.set_ylabel('Treatment', fontsize=12)

    return ax


def plot_interaction_effects(
    interactions: pd.DataFrame,
    figsize: Tuple[int, int] = (12, 8),
    title: str = "Component Interaction Effects",
    significance_level: float = 0.05,
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """
    Plot component interaction effects.

    Parameters
    ----------
    interactions : pd.DataFrame
        DataFrame with interaction effects (from InteractionModel.get_interaction_effects())
    figsize : tuple
        Figure size
    title : str
        Plot title
    significance_level : float
        Significance level for highlighting
    ax : plt.Axes, optional
        Axes to plot on

    Returns
    -------
    ax : plt.Axes
        Matplotlib axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    # Sort by absolute effect size
    interactions = interactions.copy()
    interactions['abs_mean'] = np.abs(interactions['mean'])
    interactions = interactions.sort_values('abs_mean')

    interaction_names = interactions['interaction'].values
    means = interactions['mean'].values
    lower = interactions['q2.5'].values
    upper = interactions['q97.5'].values

    # Determine significance (CI doesn't include 0)
    significant = ~((lower < 0) & (upper > 0))

    y_pos = np.arange(len(interaction_names))

    # Plot
    colors = ['red' if sig else 'gray' for sig in significant]

    for i, (m, l, u, c) in enumerate(zip(means, lower, upper, colors)):
        ax.plot([l, u], [i, i], color=c, linewidth=2, alpha=0.6)
        ax.plot(m, i, 'o', color=c, markersize=8)

    # Zero line
    ax.axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(interaction_names, fontsize=9)
    ax.set_xlabel('Interaction Effect', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)

    # Add legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color='red', lw=2, label='Significant'),
        Line2D([0], [0], color='gray', lw=2, label='Not Significant')
    ]
    ax.legend(handles=legend_elements, loc='best')

    return ax


def plot_component_network_graph(
    component_matrix: pd.DataFrame,
    effects: Optional[pd.DataFrame] = None,
    figsize: Tuple[int, int] = (12, 10),
    title: str = "Component Network",
    ax: Optional[plt.Axes] = None
) -> plt.Axes:
    """
    Plot component network with effect sizes.

    Parameters
    ----------
    component_matrix : pd.DataFrame
        Binary component matrix
    effects : pd.DataFrame, optional
        Component effects for node sizing/coloring
    figsize : tuple
        Figure size
    title : str
        Plot title
    ax : plt.Axes, optional
        Axes to plot on

    Returns
    -------
    ax : plt.Axes
        Matplotlib axes
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    # Build network
    G = nx.Graph()
    components = component_matrix.columns.tolist()

    for comp in components:
        G.add_node(comp)

    # Add edges for components that co-occur
    matrix = component_matrix.values
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            co_occur = np.sum(matrix[:, i] * matrix[:, j])
            if co_occur > 0:
                G.add_edge(components[i], components[j], weight=co_occur)

    # Layout
    pos = nx.spring_layout(G, seed=42, k=1.5)

    # Node sizes and colors based on effects
    if effects is not None:
        effect_dict = dict(zip(effects['component'], effects['mean']))
        node_sizes = [1000 + 500 * abs(effect_dict.get(node, 0)) for node in G.nodes()]
        node_colors = [effect_dict.get(node, 0) for node in G.nodes()]

        nx.draw_networkx_nodes(
            G, pos,
            node_size=node_sizes,
            node_color=node_colors,
            cmap='RdBu_r',
            vmin=-max(abs(e) for e in node_colors),
            vmax=max(abs(e) for e in node_colors),
            ax=ax
        )
    else:
        nx.draw_networkx_nodes(
            G, pos,
            node_size=1000,
            node_color='lightblue',
            ax=ax
        )

    # Draw edges
    weights = [G[u][v]['weight'] for u, v in G.edges()]
    if weights:
        max_weight = max(weights)
        nx.draw_networkx_edges(
            G, pos,
            width=[3 * w / max_weight for w in weights],
            alpha=0.5,
            ax=ax
        )

    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.axis('off')

    return ax
