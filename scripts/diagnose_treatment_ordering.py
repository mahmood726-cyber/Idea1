#!/usr/bin/env python3
"""
Quick diagnostic to verify the treatment ordering bug.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from cnma_platform.validation.simulation import simulate_cnma_data

# Simulate data
data, component_matrix, components = simulate_cnma_data(
    n_components=3,
    beta_true=np.array([0.5, -0.3, 0.4]),
    tau_true=0.15,
    n_studies_per_comparison=3,
    include_multi_arm=False,  # Start with 2-arm only for clarity
    random_seed=42
)

print("=" * 70)
print("TREATMENT ORDERING DIAGNOSTIC")
print("=" * 70)

# Extract treatments from simulation
# Simulation creates treatments in this order:
sim_treatments = []
sim_treatments.append(set())  # Control
for i in range(3):
    sim_treatments.append({f"C{i+1}"})
for i in range(3):
    for j in range(i + 1, 3):
        sim_treatments.append({f"C{i+1}", f"C{j+1}"})

sim_treatment_names = ['+'.join(sorted(t)) if t else 'Control' for t in sim_treatments]

print("\n1. SIMULATION TREATMENT ORDER:")
for i, name in enumerate(sim_treatment_names):
    print(f"   {i}: {name}")

# Extract treatments as model does (from data, then sorted)
treatments_base = set(data['treatment_base'].unique())
treatments_comp = set(data['treatment_comp'].unique())
model_treatments = sorted(treatments_base | treatments_comp)

print("\n2. MODEL TREATMENT ORDER (SORTED):")
for i, name in enumerate(model_treatments):
    print(f"   {i}: {name}")

print("\n3. COMPONENT MATRIX (from simulation):")
print("   Rows correspond to simulation treatment order:")
for i, name in enumerate(sim_treatment_names):
    print(f"   {i}: {name:15s} {component_matrix[i]}")

print("\n4. PROBLEM DETECTION:")
if sim_treatment_names != model_treatments:
    print("   ❌ ORDERS DON'T MATCH!")
    print(f"   Simulation: {sim_treatment_names}")
    print(f"   Model:      {model_treatments}")
    print("\n5. IMPACT:")
    print("   When model calculates:")
    print("   comp_diff = component_matrix[comp_idx] - component_matrix[base_idx]")
    print("   It uses model_treatments to find indices,")
    print("   but component_matrix rows are in simulation order!")
    print("   This causes WRONG component differences!")
else:
    print("   ✅ Orders match (should not happen with sorting)")

print("\n6. SOLUTION:")
print("   Need to reorder component_matrix to match sorted treatment names")
print("   OR pass treatment names from simulation to model to preserve order")
