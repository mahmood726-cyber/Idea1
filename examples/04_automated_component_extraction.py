"""
Example 4: Automated Component Extraction

This example demonstrates:
- Automated extraction of intervention components from text descriptions
- Using NLP to identify components
- Standardizing similar components
- Creating component matrix automatically
"""

import pandas as pd
import matplotlib.pyplot as plt
from cnma_platform import CNMAAnalysis
from cnma_platform.nlp import ComponentExtractor

print("=" * 70)
print("EXAMPLE 4: Automated Component Extraction with NLP")
print("=" * 70)

# Create synthetic dataset with text descriptions
print("\nCreating synthetic dataset with intervention descriptions...")

data = pd.DataFrame({
    'study': ['S1', 'S1', 'S2', 'S2', 'S3', 'S3', 'S4', 'S4', 'S5', 'S5',
              'S6', 'S6', 'S7', 'S7', 'S8', 'S8'],
    'treatment': [
        'Control', 'CBT + Exercise',
        'Control', 'CBT',
        'Control', 'Exercise + Diet',
        'Medication', 'CBT + Medication',
        'Control', 'CBT + Group Support',
        'Exercise', 'CBT + Exercise + Diet',
        'Control', 'Medication + Counseling',
        'CBT', 'CBT + Medication + Exercise'
    ],
    'description': [
        'Usual care with no active intervention',
        'Cognitive behavioral therapy sessions plus supervised exercise program',
        'Waitlist control',
        'Weekly cognitive-behavioral therapy for depression',
        'No treatment',
        'Aerobic exercise three times weekly with dietary counseling',
        'Standard pharmacological treatment with antidepressants',
        'Cognitive behavioral therapy combined with medication management',
        'Treatment as usual',
        'CBT in group format with peer support component',
        'Moderate intensity exercise program',
        'Combined intervention: CBT, exercise, and nutrition counseling',
        'Standard care',
        'Antidepressant medication with supportive counseling sessions',
        'Individual cognitive behavioral therapy',
        'Integrated treatment: CBT plus medication plus exercise training'
    ],
    'y': [0, -0.65, 0, -0.58, 0, -0.42, 0, -0.85,
          0, -0.72, 0, -0.95, 0, -0.71, -0.58, -1.12],
    'se': [0.15, 0.15, 0.12, 0.12, 0.18, 0.18, 0.14, 0.14,
           0.16, 0.16, 0.17, 0.17, 0.13, 0.13, 0.11, 0.11]
})

print(f"\nCreated dataset with {len(data)} observations")
print("\nSample intervention descriptions:")
for i in range(0, 8, 2):
    print(f"\n  {data.iloc[i+1]['treatment']}:")
    print(f"    '{data.iloc[i+1]['description']}'")

# Extract components using NLP
print("\n" + "=" * 70)
print("EXTRACTING COMPONENTS USING NLP")
print("=" * 70)

extractor = ComponentExtractor(
    domain="behavioral",
    min_component_freq=1,
    similarity_threshold=0.8
)

print("\nMethod 1: KEYWORD-based extraction")
print("-" * 70)

descriptions = data['description'].tolist()
intervention_comps_kw, all_comps_kw = extractor.extract_components(
    descriptions, method="keyword"
)

print(f"\nExtracted {len(all_comps_kw)} unique components:")
for comp in all_comps_kw:
    print(f"  - {comp}")

print("\n\nMethod 2: TF-IDF-based extraction")
print("-" * 70)

extractor2 = ComponentExtractor(
    domain="behavioral",
    min_component_freq=1
)

intervention_comps_tfidf, all_comps_tfidf = extractor2.extract_components(
    descriptions, method="tfidf"
)

print(f"\nExtracted {len(all_comps_tfidf)} unique components:")
for comp in all_comps_tfidf:
    print(f"  - {comp}")

print("\n\nMethod 3: HYBRID extraction (recommended)")
print("-" * 70)

extractor3 = ComponentExtractor(
    domain="behavioral",
    min_component_freq=1,
    similarity_threshold=0.85
)

intervention_comps_hybrid, all_comps_hybrid = extractor3.extract_components(
    descriptions, method="hybrid"
)

print(f"\nExtracted {len(all_comps_hybrid)} unique components (after standardization):")
for comp in all_comps_hybrid:
    print(f"  - {comp}")

# Create component matrix
print("\n" + "=" * 70)
print("CREATING COMPONENT MATRIX")
print("=" * 70)

component_matrix = extractor3.create_component_matrix(
    intervention_comps_hybrid,
    all_comps_hybrid
)

print("\nComponent Matrix (rows=interventions, columns=components):")
print(component_matrix)

# Add extracted components to data
data['components_extracted'] = [
    ','.join(sorted(comps)) for comps in intervention_comps_hybrid
]

print("\n\nInterventions with extracted components:")
for i, row in data.iterrows():
    if row['components_extracted']:
        print(f"  {row['treatment']:<30} → {row['components_extracted']}")

# Analyze component co-occurrence
print("\n" + "=" * 70)
print("COMPONENT CO-OCCURRENCE ANALYSIS")
print("=" * 70)

from cnma_platform.data import NetworkBuilder

# Create a temporary data subset for analysis
data_subset = data[data['components_extracted'] != ''].copy()

builder = NetworkBuilder(data_subset)

# Build component network
import networkx as nx

G = nx.Graph()
for comp in all_comps_hybrid:
    G.add_node(comp)

# Add edges for co-occurrence
matrix = component_matrix.values
for i in range(len(all_comps_hybrid)):
    for j in range(i+1, len(all_comps_hybrid)):
        co_occur = (matrix[:, i] * matrix[:, j]).sum()
        if co_occur > 0:
            G.add_edge(all_comps_hybrid[i], all_comps_hybrid[j], weight=int(co_occur))

print(f"\nComponent network:")
print(f"  Components: {G.number_of_nodes()}")
print(f"  Co-occurrences: {G.number_of_edges()}")

print("\n\nMost frequently co-occurring components:")
edges_sorted = sorted(G.edges(data=True), key=lambda x: x[2]['weight'], reverse=True)
for u, v, data in edges_sorted[:5]:
    print(f"  {u} + {v}: {data['weight']} interventions")

# Fit CNMA model with extracted components
print("\n" + "=" * 70)
print("FITTING CNMA MODEL WITH EXTRACTED COMPONENTS")
print("=" * 70)

# Prepare data for CNMA
cnma_data = data.copy()
cnma_data['components'] = cnma_data['components_extracted']

# Remove rows with no components (controls)
cnma_data = cnma_data[cnma_data['components'] != ''].copy()

# Add control rows
control_data = pd.DataFrame({
    'study': data['study'].unique(),
    'treatment': 'Control',
    'components': '',
    'y': 0,
    'se': 0.15
})

cnma_data = pd.concat([cnma_data, control_data], ignore_index=True)

print(f"\nPrepared {len(cnma_data)} observations for CNMA")

# Initialize and fit
analysis = CNMAAnalysis(
    data=cnma_data,
    model_type="additive",
    likelihood="bayesian",
    outcome_type="continuous"
)

analysis.set_components(component_col="components")

print("\nFitting model...")
results = analysis.fit(n_samples=800, n_warmup=400, n_chains=2)

# Results
print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

component_effects = analysis.get_component_effects()
print("\nEstimated Component Effects:")
print(component_effects[['component', 'mean', 'sd', 'q2.5', 'q97.5']])

print("\n\nInterpretation (effect on depression, negative = improvement):")
for _, row in component_effects.sort_values('mean').iterrows():
    comp = row['component']
    mean = row['mean']
    ci = f"[{row['q2.5']:.2f}, {row['q97.5']:.2f}]"

    effectiveness = "Highly effective" if mean < -0.5 else \
                   "Moderately effective" if mean < -0.3 else \
                   "Mildly effective" if mean < 0 else \
                   "No benefit"

    print(f"  {comp:<30} Effect: {mean:>6.3f} (95% CrI: {ci})  →  {effectiveness}")

# Visualization
print("\n" + "=" * 70)
print("GENERATING VISUALIZATIONS")
print("=" * 70)

fig = plt.figure(figsize=(18, 12))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# 1. Component extraction comparison
ax1 = fig.add_subplot(gs[0, :])
methods = ['Keyword', 'TF-IDF', 'Hybrid']
n_components = [len(all_comps_kw), len(all_comps_tfidf), len(all_comps_hybrid)]
colors = ['skyblue', 'lightcoral', 'lightgreen']

bars = ax1.bar(methods, n_components, color=colors, alpha=0.7, edgecolor='black', linewidth=2)
ax1.set_ylabel('Number of Components', fontsize=12)
ax1.set_title('Component Extraction: Method Comparison', fontsize=14, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)

for bar, n in zip(bars, n_components):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.3,
             f'{n}', ha='center', va='bottom', fontweight='bold', fontsize=12)

# 2. Component matrix heatmap
ax2 = fig.add_subplot(gs[1, :2])
import seaborn as sns

# Create labeled matrix
matrix_labeled = component_matrix.copy()
matrix_labeled.index = [f"I{i+1}" for i in range(len(matrix_labeled))]

sns.heatmap(
    matrix_labeled,
    cmap='Blues',
    cbar_kws={'label': 'Component Present'},
    linewidths=0.5,
    linecolor='gray',
    ax=ax2
)
ax2.set_title('Component Matrix (Interventions × Components)', fontsize=12, fontweight='bold')
ax2.set_xlabel('Components', fontsize=10)
ax2.set_ylabel('Interventions', fontsize=10)

# 3. Component network
ax3 = fig.add_subplot(gs[1, 2])
from cnma_platform.visualization.plots import plot_network

plot_network(
    G,
    layout='circular',
    node_size=800,
    font_size=8,
    title='Component Co-occurrence Network',
    ax=ax3
)

# 4. Component effects
ax4 = fig.add_subplot(gs[2, :])
analysis.plot_component_effects(ax=ax4, title='Estimated Component Effects (Automated Extraction)')

plt.savefig('examples/output_04_component_extraction.png', dpi=300, bbox_inches='tight')
print("\nVisualization saved as 'examples/output_04_component_extraction.png'")

print("\n" + "=" * 70)
print("ANALYSIS COMPLETE!")
print("=" * 70)

print("\nKey Takeaways:")
print("1. Automated component extraction can identify intervention components from text")
print("2. Hybrid approach combines keyword matching with TF-IDF for best results")
print("3. Component standardization merges similar components")
print("4. Extracted components can be directly used in CNMA models")
print("5. This approach scales to large systematic reviews with many interventions")
