"""
Generate figures for the Synthesis document.

This script creates two publication-ready figures:
1. CNMA Workflow Diagram - Conceptual overview of the methodology
2. Additive vs Interaction Models - Comparison with example results
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import numpy as np
import seaborn as sns

# Set publication style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("colorblind")
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10
plt.rcParams['figure.dpi'] = 300

def create_figure1_workflow():
    """
    Figure 1: CNMA Methodological Workflow

    Shows the complete process from intervention descriptions through
    component extraction, model fitting, validation, and interpretation.
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Define colors
    color_data = '#E8F4F8'
    color_methods = '#FFF4E6'
    color_validation = '#F0F8F0'
    color_output = '#FCE4EC'

    # Title
    ax.text(5, 9.5, 'Component Network Meta-Analysis Workflow',
            ha='center', va='center', fontsize=14, fontweight='bold')

    # Step 1: Data Input
    box1 = FancyBboxPatch((0.5, 7.8), 2, 1, boxstyle="round,pad=0.1",
                          ec='black', fc=color_data, linewidth=1.5)
    ax.add_patch(box1)
    ax.text(1.5, 8.5, 'Step 1: Data Input', ha='center', fontweight='bold', fontsize=9)
    ax.text(1.5, 8.15, 'Trial descriptions\nOutcome data', ha='center', fontsize=8, style='italic')

    # Step 2: Component Extraction
    box2 = FancyBboxPatch((3.5, 7.8), 2.5, 1, boxstyle="round,pad=0.1",
                          ec='black', fc=color_data, linewidth=1.5)
    ax.add_patch(box2)
    ax.text(4.75, 8.5, 'Step 2: Component Extraction', ha='center', fontweight='bold', fontsize=9)
    ax.text(4.75, 8.15, 'NLP-based identification\nStandardization', ha='center', fontsize=8, style='italic')

    # Step 3: Network Construction
    box3 = FancyBboxPatch((7, 7.8), 2.5, 1, boxstyle="round,pad=0.1",
                          ec='black', fc=color_data, linewidth=1.5)
    ax.add_patch(box3)
    ax.text(8.25, 8.5, 'Step 3: Network Building', ha='center', fontweight='bold', fontsize=9)
    ax.text(8.25, 8.15, 'Component matrix\nContrast data', ha='center', fontsize=8, style='italic')

    # Step 4: Model Selection
    box4 = FancyBboxPatch((0.5, 6), 2.8, 1.2, boxstyle="round,pad=0.1",
                          ec='black', fc=color_methods, linewidth=1.5)
    ax.add_patch(box4)
    ax.text(1.9, 6.85, 'Step 4: Model Selection', ha='center', fontweight='bold', fontsize=9)
    ax.text(1.9, 6.5, '• Additive model\n• Interaction model\n• Composite likelihood',
            ha='center', fontsize=7, style='italic')

    # Step 5: Bayesian/Frequentist Estimation
    box5 = FancyBboxPatch((4, 6), 2.5, 1.2, boxstyle="round,pad=0.1",
                          ec='black', fc=color_methods, linewidth=1.5)
    ax.add_patch(box5)
    ax.text(5.25, 6.85, 'Step 5: Estimation', ha='center', fontweight='bold', fontsize=9)
    ax.text(5.25, 6.5, 'MCMC (PyMC)\nComposite MLE', ha='center', fontsize=8, style='italic')

    # Step 6: Diagnostics
    box6 = FancyBboxPatch((7.2, 6), 2.3, 1.2, boxstyle="round,pad=0.1",
                          ec='black', fc=color_validation, linewidth=1.5)
    ax.add_patch(box6)
    ax.text(8.35, 6.85, 'Step 6: Diagnostics', ha='center', fontweight='bold', fontsize=9)
    ax.text(8.35, 6.5, 'Convergence (R̂, ESS)\nNode-splitting', ha='center', fontsize=8, style='italic')

    # Step 7: Validation
    box7 = FancyBboxPatch((1.5, 4.2), 3, 1.2, boxstyle="round,pad=0.1",
                          ec='black', fc=color_validation, linewidth=1.5)
    ax.add_patch(box7)
    ax.text(3, 5.05, 'Step 7: Model Validation', ha='center', fontweight='bold', fontsize=9)
    ax.text(3, 4.7, 'Posterior predictive checks\nConsistency assessment\nModel comparison (DIC/WAIC/LOO)',
            ha='center', fontsize=7, style='italic')

    # Step 8: Interpretation
    box8 = FancyBboxPatch((5.5, 4.2), 3.5, 1.2, boxstyle="round,pad=0.1",
                          ec='black', fc=color_output, linewidth=1.5)
    ax.add_patch(box8)
    ax.text(7.25, 5.05, 'Step 8: Results & Interpretation', ha='center', fontweight='bold', fontsize=9)
    ax.text(7.25, 4.7, 'Component effects & rankings\nIntervention predictions\nUncertainty quantification',
            ha='center', fontsize=7, style='italic')

    # Outputs box
    box9 = FancyBboxPatch((2, 2.3), 6, 1.4, boxstyle="round,pad=0.1",
                          ec='black', fc=color_output, linewidth=2)
    ax.add_patch(box9)
    ax.text(5, 3.4, 'Outputs & Visualizations', ha='center', fontweight='bold', fontsize=10)
    ax.text(5, 2.95, '• Component effect forest plots  • Network diagrams  • SUCRA/Rankograms',
            ha='center', fontsize=8)
    ax.text(5, 2.6, '• Intervention comparison matrices  • Predictive distributions',
            ha='center', fontsize=8)

    # Key assumptions box
    box10 = FancyBboxPatch((0.3, 0.3), 9.4, 1.5, boxstyle="round,pad=0.1",
                           ec='darkred', fc='#FFF9E6', linewidth=1.5, linestyle='--')
    ax.add_patch(box10)
    ax.text(5, 1.5, 'Key Assumptions', ha='center', fontweight='bold', fontsize=9, color='darkred')
    ax.text(5, 1.15, 'Exchangeability • Consistency • Transitivity', ha='center', fontsize=8)
    ax.text(5, 0.85, 'Additivity (additive model) • Positivity • Identifiability', ha='center', fontsize=8)
    ax.text(5, 0.5, 'Assessed via: Node-splitting, posterior predictive checks, sensitivity analyses',
            ha='center', fontsize=7, style='italic')

    # Draw arrows
    arrow_props = dict(arrowstyle='->', lw=2, color='black')

    # Horizontal arrows (top row)
    ax.annotate('', xy=(3.5, 8.3), xytext=(2.5, 8.3), arrowprops=arrow_props)
    ax.annotate('', xy=(7, 8.3), xytext=(6, 8.3), arrowprops=arrow_props)

    # Vertical arrow from step 3 to 4
    ax.annotate('', xy=(1.9, 7.2), xytext=(1.9, 7.8), arrowprops=arrow_props)

    # Horizontal arrows (middle row)
    ax.annotate('', xy=(4, 6.6), xytext=(3.3, 6.6), arrowprops=arrow_props)
    ax.annotate('', xy=(7.2, 6.6), xytext=(6.5, 6.6), arrowprops=arrow_props)

    # Vertical arrows to validation/interpretation
    ax.annotate('', xy=(3, 5.4), xytext=(3, 6), arrowprops=arrow_props)
    ax.annotate('', xy=(7.25, 5.4), xytext=(8, 6), arrowprops=arrow_props)

    # Arrows to outputs
    ax.annotate('', xy=(3.5, 3.7), xytext=(3.5, 4.2), arrowprops=arrow_props)
    ax.annotate('', xy=(6.5, 3.7), xytext=(6.5, 4.2), arrowprops=arrow_props)

    plt.tight_layout()
    plt.savefig('/home/user/Idea1/docs/Figure1_CNMA_Workflow.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('/home/user/Idea1/docs/Figure1_CNMA_Workflow.pdf',
                bbox_inches='tight', facecolor='white')
    print("Figure 1 created: CNMA Workflow")
    plt.close()


def create_figure2_model_comparison():
    """
    Figure 2: Additive vs Interaction Models - Conceptual Comparison

    Illustrates the difference between additive and interaction models
    with example component effects and predictions.
    """
    fig = plt.figure(figsize=(12, 8))

    # Create grid for subplots
    gs = fig.add_gridspec(3, 2, height_ratios=[1.2, 1, 1], hspace=0.4, wspace=0.3)

    # ============ Panel A: Conceptual Models ============
    ax_concept = fig.add_subplot(gs[0, :])
    ax_concept.set_xlim(0, 10)
    ax_concept.set_ylim(0, 3)
    ax_concept.axis('off')

    ax_concept.text(5, 2.7, 'Model Comparison: Additive vs Interaction',
                    ha='center', fontweight='bold', fontsize=12)

    # Additive Model
    ax_concept.text(2.5, 2.2, 'Additive Model', ha='center', fontweight='bold', fontsize=10)
    box_add = FancyBboxPatch((0.5, 0.5), 4, 1.5, boxstyle="round,pad=0.1",
                             ec='steelblue', fc='#E8F4F8', linewidth=2)
    ax_concept.add_patch(box_add)
    ax_concept.text(2.5, 1.6, r'$\theta_{jk} = \sum_{c} \beta_c \cdot (I_{kc} - I_{jc})$',
                    ha='center', fontsize=10, family='monospace')
    ax_concept.text(2.5, 1.2, 'Effects combine linearly', ha='center', fontsize=9, style='italic')
    ax_concept.text(2.5, 0.85, 'Example: A+B = β_A + β_B', ha='center', fontsize=8)
    ax_concept.text(2.5, 0.6, '✓ Maximum power  ✓ Simple interpretation',
                    ha='center', fontsize=7, color='darkgreen')

    # Interaction Model
    ax_concept.text(7.5, 2.2, 'Interaction Model', ha='center', fontweight='bold', fontsize=10)
    box_int = FancyBboxPatch((5.5, 0.5), 4, 1.5, boxstyle="round,pad=0.1",
                             ec='darkorange', fc='#FFF4E6', linewidth=2)
    ax_concept.add_patch(box_int)
    ax_concept.text(7.5, 1.6, r'$\theta_{jk} = \sum_{c} \beta_c \cdot \Delta I_c + \sum_{c<c^{\prime}} \gamma_{cc^{\prime}} \cdot \Delta I_c I_{c^{\prime}}$',
                    ha='center', fontsize=9, family='monospace')
    ax_concept.text(7.5, 1.2, 'Accounts for synergy/antagonism', ha='center', fontsize=9, style='italic')
    ax_concept.text(7.5, 0.85, 'Example: A+B = β_A + β_B + γ_AB', ha='center', fontsize=8)
    ax_concept.text(7.5, 0.6, '✓ Flexible  ⚠ Requires more data',
                    ha='center', fontsize=7, color='darkorange')

    # ============ Panel B: Example Component Effects ============
    ax_effects = fig.add_subplot(gs[1, 0])

    # Simulate component effects
    components = ['Counseling', 'NRT', 'Group\nSupport', 'Digital\nApp']
    beta_additive = [0.45, 0.52, 0.28, 0.35]
    beta_se = [0.08, 0.09, 0.11, 0.10]

    y_pos = np.arange(len(components))

    # Forest plot
    ax_effects.errorbar(beta_additive, y_pos, xerr=[1.96*se for se in beta_se],
                       fmt='o', markersize=8, color='steelblue',
                       elinewidth=2, capsize=5, capthick=2, label='Additive model')

    ax_effects.axvline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax_effects.set_yticks(y_pos)
    ax_effects.set_yticklabels(components)
    ax_effects.set_xlabel('Component Effect (log-OR)', fontweight='bold')
    ax_effects.set_title('Panel B: Component Effect Estimates', fontweight='bold', fontsize=10)
    ax_effects.grid(axis='x', alpha=0.3)
    ax_effects.spines['top'].set_visible(False)
    ax_effects.spines['right'].set_visible(False)

    # Add reference line at 0
    ax_effects.text(0.02, -0.7, 'No effect', fontsize=7, style='italic', color='gray')

    # ============ Panel C: Interaction Effects ============
    ax_interact = fig.add_subplot(gs[1, 1])

    # Interaction effects (heatmap)
    interactions = np.array([
        [0, 0.15, -0.05, 0.08],
        [0.15, 0, 0.12, 0.02],
        [-0.05, 0.12, 0, -0.08],
        [0.08, 0.02, -0.08, 0]
    ])

    im = ax_interact.imshow(interactions, cmap='RdBu_r', vmin=-0.2, vmax=0.2, aspect='auto')

    ax_interact.set_xticks(np.arange(len(components)))
    ax_interact.set_yticks(np.arange(len(components)))
    ax_interact.set_xticklabels([c.replace('\n', ' ') for c in components], rotation=45, ha='right')
    ax_interact.set_yticklabels([c.replace('\n', ' ') for c in components])
    ax_interact.set_title('Panel C: Interaction Effects (γ)', fontweight='bold', fontsize=10)

    # Add values to cells
    for i in range(len(components)):
        for j in range(len(components)):
            if i != j:
                text = ax_interact.text(j, i, f'{interactions[i, j]:.2f}',
                                      ha="center", va="center",
                                      color="black" if abs(interactions[i, j]) < 0.1 else "white",
                                      fontsize=8)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax_interact, fraction=0.046, pad=0.04)
    cbar.set_label('Interaction\neffect', rotation=0, ha='left', fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    # ============ Panel D: Intervention Predictions ============
    ax_pred = fig.add_subplot(gs[2, :])

    # Compare predicted effects for various intervention combinations
    interventions = [
        'Control',
        'Counseling',
        'NRT',
        'Counseling\n+ NRT',
        'Counseling\n+ Group',
        'NRT + Digital',
        'Counseling\n+ NRT + Group',
        'All Four\nComponents'
    ]

    # Additive predictions
    additive_preds = [0, 0.45, 0.52, 0.97, 0.73, 0.87, 1.25, 1.60]
    additive_se = [0, 0.08, 0.09, 0.12, 0.13, 0.13, 0.15, 0.18]

    # Interaction predictions (accounting for synergy/antagonism)
    interaction_preds = [0, 0.45, 0.52, 1.12, 0.68, 0.89, 1.32, 1.63]
    interaction_se = [0, 0.08, 0.09, 0.14, 0.15, 0.15, 0.18, 0.21]

    x_pos = np.arange(len(interventions))
    width = 0.35

    ax_pred.bar(x_pos - width/2, additive_preds, width,
               yerr=[1.96*se for se in additive_se],
               label='Additive model', color='steelblue', alpha=0.7,
               error_kw={'elinewidth': 1.5, 'capsize': 3})

    ax_pred.bar(x_pos + width/2, interaction_preds, width,
               yerr=[1.96*se for se in interaction_se],
               label='Interaction model', color='darkorange', alpha=0.7,
               error_kw={'elinewidth': 1.5, 'capsize': 3})

    ax_pred.set_ylabel('Predicted Effect (log-OR)', fontweight='bold')
    ax_pred.set_xlabel('Intervention Combination', fontweight='bold')
    ax_pred.set_title('Panel D: Predicted Effects for Intervention Combinations',
                     fontweight='bold', fontsize=10)
    ax_pred.set_xticks(x_pos)
    ax_pred.set_xticklabels(interventions, fontsize=8)
    ax_pred.legend(loc='upper left', frameon=True, fontsize=9)
    ax_pred.grid(axis='y', alpha=0.3)
    ax_pred.spines['top'].set_visible(False)
    ax_pred.spines['right'].set_visible(False)

    # Add annotation
    ax_pred.annotate('Note: Differences arise from\ninteraction terms (Panel C)',
                    xy=(6, 1.32), xytext=(5, 1.7),
                    arrowprops=dict(arrowstyle='->', color='black', lw=1),
                    fontsize=7, style='italic',
                    bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.3))

    plt.tight_layout()
    plt.savefig('/home/user/Idea1/docs/Figure2_Model_Comparison.png',
                dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('/home/user/Idea1/docs/Figure2_Model_Comparison.pdf',
                bbox_inches='tight', facecolor='white')
    print("Figure 2 created: Additive vs Interaction Models")
    plt.close()


if __name__ == '__main__':
    print("Generating synthesis figures...")
    print("-" * 50)

    create_figure1_workflow()
    create_figure2_model_comparison()

    print("-" * 50)
    print("All figures created successfully!")
    print("\nGenerated files:")
    print("  • Figure1_CNMA_Workflow.png")
    print("  • Figure1_CNMA_Workflow.pdf")
    print("  • Figure2_Model_Comparison.png")
    print("  • Figure2_Model_Comparison.pdf")
