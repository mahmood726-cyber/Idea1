# Mathematical Specification of CNMA Models

This document provides formal mathematical specifications for all models implemented in the CNMA platform.

## Table of Contents

1. [Notation](#notation)
2. [Additive CNMA Model](#additive-cnma-model)
3. [Interaction CNMA Model](#interaction-cnma-model)
4. [Composite Likelihood](#composite-likelihood)
5. [Prior Specifications](#prior-specifications)
6. [Assumptions](#assumptions)
7. [References](#references)

---

## Notation

### Data Structure

**Contrast-based format** (recommended):
- $s = 1, \ldots, S$: studies
- $j_s, k_s$: treatments compared in study $s$ (where $j_s$ = baseline, $k_s$ = comparison)
- $y_s$: observed relative effect comparing $k_s$ vs $j_s$ (log-OR, SMD, MD, log-RR, etc.)
- $\text{SE}_s$: standard error of $y_s$

**Arm-based format**:
- $s = 1, \ldots, S$: studies
- $a = 1, \ldots, A_s$: arms within study $s$
- $y_{sa}$: outcome in arm $a$ of study $s$
- $\text{SE}_{sa}$: standard error of $y_{sa}$

### Parameters

- $C = \\{c_1, \ldots, c_K\\}$: set of $K$ intervention components
- $\mathbf{I}_j = (I_{j1}, \ldots, I_{jK})$: binary indicator vector for treatment $j$
  - $I_{jc} = 1$ if component $c$ is in treatment $j$, else $I_{jc} = 0$
- $\boldsymbol{\beta} = (\beta_1, \ldots, \beta_K)$: component effect parameters
- $\boldsymbol{\gamma}$: interaction effect parameters (interaction model only)
- $\tau$: between-study heterogeneity standard deviation
- $\nu_s$: study-specific random effect
- $\delta_s$: true study-specific relative effect for comparison $(j_s, k_s)$ in study $s$
  - More explicitly: $\delta_{s,j_sk_s}$ or $\delta_{s}^{(j_s,k_s)}$, abbreviated as $\delta_s$ when context is clear

---

## Additive CNMA Model

### Model Specification

For study $s$ comparing treatments $j_s$ (baseline) and $k_s$ (comparison):

$$
\begin{aligned}
y_s &\sim \mathcal{N}(\delta_s, \text{SE}_s^2) \\
\delta_s &= \theta_{j_s k_s} + \nu_s \\
\theta_{j_s k_s} &= \sum_{c=1}^K \beta_c (I_{k_s c} - I_{j_s c}) \\
\nu_s &\sim \mathcal{N}(0, \tau^2)
\end{aligned}
$$

**Interpretation**:
- $y_s$: observed relative effect in study $s$ (comparing $k_s$ vs $j_s$)
- $\delta_s$: true study-specific relative effect for comparison $(j_s, k_s)$
- $\theta_{j_s k_s}$: pooled relative effect of $k_s$ vs $j_s$ based on component composition
- $\beta_c$: additive effect of component $c$
- $\nu_s$: study-specific deviation from pooled effect
- $\tau$: standard deviation of between-study effects

### Component Effect

The relative effect between any two treatments $j$ (baseline) and $k$ (comparison) is:

$$
\theta_{jk} = \sum_{c \in C} \beta_c \cdot \Delta I_{jkc}
$$

where $\Delta I_{jkc} = I_{kc} - I_{jc}$ is the component difference (comparison minus baseline).

### Additivity Assumption

The model assumes **additive combination** of component effects:

$$
\mathbb{E}[Y | \text{components } \\{c_1, c_2\\}] = \mathbb{E}[Y | \text{component } c_1] + \mathbb{E}[Y | \text{component } c_2]
$$

This implies no synergistic or antagonistic interactions between components.

---

## Interaction CNMA Model

### Model Specification

Extends the additive model to include pairwise interactions:

$$
\begin{aligned}
y_s &\sim \mathcal{N}(\delta_s, \text{SE}_s^2) \\
\delta_s &= \theta_{j_s k_s} + \nu_s \\
\theta_{j_s k_s} &= \sum_{c=1}^K \beta_c (I_{k_s c} - I_{j_s c}) + \sum_{c < c'} \gamma_{cc'} (\mathcal{I}_{k_s}^{cc'} - \mathcal{I}_{j_s}^{cc'}) \\
\mathcal{I}_{j}^{cc'} &= I_{jc} \times I_{jc'} \\
\nu_s &\sim \mathcal{N}(0, \tau^2)
\end{aligned}
$$

where:
- $\gamma_{cc'}$: interaction effect between components $c$ and $c'$
- $\mathcal{I}_{j}^{cc'} = 1$ if both components $c$ and $c'$ are in treatment $j$, else 0
- Indexing follows same convention as additive model: $k_s$ (comparison) minus $j_s$ (baseline)

### Interpretation of Interaction Terms

- $\gamma_{cc'} > 0$: **Synergistic interaction** (combined effect exceeds sum of individual effects)
- $\gamma_{cc'} < 0$: **Antagonistic interaction** (combined effect less than sum)
- $\gamma_{cc'} = 0$: **No interaction** (reduces to additive model)

### Higher-Order Interactions

The model can be extended to three-way and higher-order interactions. For the pooled effect comparing treatment $k$ (comparison) vs $j$ (baseline):

$$
\theta_{jk} = \sum_c \beta_c \Delta I_{jkc} + \sum_{c < c'} \gamma_{cc'} \Delta \mathcal{I}_{jk}^{cc'} + \sum_{c < c' < c''} \gamma_{cc'c''} \Delta \mathcal{I}_{jk}^{cc'c''} + \ldots
$$

where $\Delta \mathcal{I}_{jk}^{cc'} = \mathcal{I}_{k}^{cc'} - \mathcal{I}_{j}^{cc'}$ follows the same indexing convention (comparison minus baseline).

However, higher-order terms are rarely estimable and should be used sparingly.

---

## Composite Likelihood

### Motivation

Standard likelihood for multi-arm trials requires specifying within-study correlation structure.
The composite likelihood avoids this by using arm-level (marginal) likelihoods.

### Composite Likelihood Function

$$
CL(\boldsymbol{\beta}, \tau | \mathbf{y}) = \prod_{s=1}^S \prod_{(j,k) \in \mathcal{C}_s} L(\boldsymbol{\beta}, \tau | y_{s,jk})
$$

where:
- $\mathcal{C}_s$: set of all pairwise contrasts in study $s$
- $L(\cdot | y_{s,jk})$: marginal likelihood for contrast $(j,k)$ in study $s$

### Arm-Level Likelihood

For each contrast $(j,k)$ in study $s$:

$$
L(\boldsymbol{\beta}, \tau | y_{s,jk}) = \int \mathcal{N}(y_{s,jk} | \theta_{jk} + \nu_s, \text{SE}_{s,jk}^2) \mathcal{N}(\nu_s | 0, \tau^2) d\nu_s
$$

Marginalizing over $\nu_s$:

$$
y_{s,jk} \sim \mathcal{N}(\theta_{jk}, \text{SE}_{s,jk}^2 + \tau^2)
$$

### Maximum Composite Likelihood Estimation

Estimate parameters by maximizing:

$$
\hat{\boldsymbol{\beta}}, \hat{\tau} = \arg\max_{\boldsymbol{\beta}, \tau} \log CL(\boldsymbol{\beta}, \tau | \mathbf{y})
$$

### Sandwich Variance Estimator

Standard errors require the **sandwich estimator** (Varin et al., 2011):

$$
\text{Var}(\hat{\boldsymbol{\theta}}) = H^{-1} J H^{-1}
$$

where:
- $H = -\mathbb{E}[\nabla^2 \log CL]$: negative Hessian (model-based information)
- $J = \text{Var}[\nabla \log CL]$: variance of score function (empirical information)

**Why needed**: Composite likelihood treats correlated observations as independent,
so standard Fisher information underestimates variance.

---

## Prior Specifications

### Bayesian Inference

**Component effects** ($\beta_c$):
$$
\beta_c \sim \mathcal{N}(0, \sigma_\beta^2), \quad c = 1, \ldots, K
$$

Default: $\sigma_\beta = 2$ (weakly informative for log-OR scale)

**Interaction effects** ($\gamma_{cc'}$):
$$
\gamma_{cc'} \sim \mathcal{N}(0, \sigma_\gamma^2)
$$

Default: $\sigma_\gamma = 1$ (interactions typically smaller than main effects)

**Between-study heterogeneity** ($\tau$):

*Option 1: Half-Normal*
$$
\tau \sim \text{HalfNormal}(\sigma_\tau)
$$
Default: $\sigma_\tau = 1$

*Option 2: Half-Cauchy* (recommended for small $K$)
$$
\tau \sim \text{HalfCauchy}(\beta_\tau)
$$
Default: $\beta_\tau = 0.5$

*Option 3: Uniform* (non-informative)
$$
\tau \sim \text{Uniform}(0, U)
$$
Default: $U = 5$

### Prior Sensitivity

Recommendations:
1. **Always check prior sensitivity** for small datasets ($S < 10$)
2. Use **weakly informative priors** (default)
3. Consider **informative priors** when external evidence available
4. Avoid **improper priors** for variance parameters

---

## Assumptions

### Exchangeability

**Assumption**: Studies are exchangeable with respect to the true relative effects.

**Implications**:
- Same underlying component effects $\boldsymbol{\beta}$ across studies
- Study-specific deviations $\nu_s$ are random draws from common distribution
- Violations occur with: different populations, settings, outcome measures

**Assessment**: Check for effect modification (meta-regression)

### Similarity/Transitivity

**Assumption**: Indirect comparisons are valid (A vs B via C is similar to direct A vs B).

**Implications**:
- Treatment distributions are similar across studies
- Effect modifiers are balanced
- Component effects are consistent

**Assessment**:
- Check study/population characteristics
- Node-splitting analysis
- Design-by-treatment interaction tests

### Consistency

**Assumption**: Direct and indirect evidence agree.

**Implications**:
- No systematic differences between evidence types
- Network is internally consistent

**Assessment**:
- Node-splitting
- Posterior predictive checks
- Design-by-treatment models (Higgins et al., 2012)

### Additivity (Additive Model Only)

**Assumption**: Component effects combine additively without interactions.

**Implications**:
- $\theta_{j \cup k} = \theta_j + \theta_k$ for disjoint component sets
- No synergy or antagonism between components

**Assessment**:
- Fit interaction model and test $\gamma_{cc'} = 0$
- Expert knowledge
- Biological mechanisms

### Positivity

**Assumption**: All component combinations are theoretically possible.

**Implications**:
- Can extrapolate to unstudied combinations
- Predictions are within support of data

**Violations**: Structural zeros (impossible combinations)

---

## Identifiability

### Component Effects

For the additive model, component effects $\boldsymbol{\beta}$ are **identifiable** if:

1. The component matrix has **full column rank**: $\text{rank}(\mathbf{I}) = K$
2. There is **sufficient contrast** in component combinations

**Non-identifiable case**: If component $c_1$ always appears with $c_2$, cannot separate their effects.

### Baseline Effects

In arm-based formulation, study-specific baselines $\mu_s$ are **nuisance parameters** and
do not affect relative effects $\theta_{jk}$.

In contrast-based formulation, baselines are eliminated by differencing.

---

## Computational Implementation

### MCMC Sampling (Bayesian)

**Algorithm**: No-U-Turn Sampler (NUTS) via PyMC

**Convergence Diagnostics**:
- $\hat{R} < 1.01$ (Gelman-Rubin statistic)
- $\text{ESS}_{\text{bulk}} > 400$ (effective sample size)
- Visual inspection of trace plots

**Recommendations**:
- Chains: $\geq 4$
- Warmup: $\geq 1000$
- Samples: $\geq 2000$ per chain
- Target accept: 0.95 (for complex geometries)

### Optimization (Composite Likelihood)

**Algorithm**: L-BFGS-B with multiple starting values

**Convergence**: Check gradient norm and Hessian positive-definiteness

---

## Model Comparison

### Deviance Information Criterion (DIC)

$$
\text{DIC} = \bar{D} + p_D
$$

where:
- $\bar{D}$: posterior mean deviance
- $p_D$: effective number of parameters

**Lower is better**. $\Delta \text{DIC} > 5$ suggests meaningful difference.

### Widely Applicable Information Criterion (WAIC)

$$
\text{WAIC} = -2(\text{lppd} - p_{\text{WAIC}})
$$

**Advantages**: Fully Bayesian, handles singular models

### Leave-One-Out Cross-Validation (LOO)

Uses Pareto-smoothed importance sampling (PSIS).

**Preferred** for model comparison (more robust than DIC/WAIC).

---

## References

### Core CNMA Papers

1. **Welton, N. J., et al. (2009)**. Mixed treatment comparison meta-analysis of complex interventions: psychological interventions in coronary heart disease. *American Journal of Epidemiology*, 169(9), 1158-1165.
   - Original CNMA methodology

2. **Rücker, G., et al. (2020)**. Component network meta-analysis compared to a matching method in a disconnected network: a case study. *Biometrical Journal*, 62(2), 447-461.
   - Component selection and methodological extensions

3. **Pompoli, A., et al. (2018)**. Psychological therapies for panic disorder with or without agoraphobia in adults: a network meta-analysis. *Cochrane Database of Systematic Reviews*, 4.
   - Applied example with component analysis

### Network Meta-Analysis Foundations

4. **Dias, S., et al. (2013)**. Evidence synthesis for decision making 2: a generalized linear modeling framework for pairwise and network meta-analysis of randomized controlled trials. *Medical Decision Making*, 33(5), 607-617.
   - Standard NMA methodology (NICE DSU TSD 2)

5. **Dias, S., et al. (2010)**. Checking consistency in mixed treatment comparison meta-analysis. *Statistics in Medicine*, 29(7-8), 932-944.
   - Node-splitting and consistency assessment

6. **Higgins, J. P. T., et al. (2012)**. Consistency and inconsistency in network meta-analysis: concepts and models for multi-arm studies. *Research Synthesis Methods*, 3(2), 98-110.
   - Design-by-treatment interaction models

### Composite Likelihood

7. **Varin, C., et al. (2011)**. An overview of composite likelihood methods. *Statistica Sinica*, 21(1), 5-42.
   - Comprehensive review of composite likelihood theory

8. **Xu, X., & Reid, N. (2011)**. On the robustness of maximum composite likelihood estimate. *Journal of Statistical Planning and Inference*, 141(9), 3047-3054.
   - Finite-sample corrections for sandwich estimator

### Prior Specification

9. **Gelman, A. (2006)**. Prior distributions for variance parameters in hierarchical models. *Bayesian Analysis*, 1(3), 515-534.
   - Recommendations for $\tau$ priors

10. **Turner, R. M., et al. (2015)**. Predictive distributions for between-study heterogeneity and simple methods for their application in Bayesian meta-analysis. *Statistics in Medicine*, 34(6), 984-998.
    - Empirically-based heterogeneity priors

---

## Appendix: Derivations

### A.1 Marginal Likelihood for Composite Likelihood

Starting from:
$$
y_s | \nu_s \sim \mathcal{N}(\theta + \nu_s, \sigma^2)
$$
$$
\nu_s \sim \mathcal{N}(0, \tau^2)
$$

The marginal distribution is:
$$
\begin{aligned}
p(y_s | \theta, \tau) &= \int p(y_s | \nu_s, \theta) p(\nu_s | \tau) d\nu_s \\
&= \int \mathcal{N}(y_s | \theta + \nu_s, \sigma^2) \mathcal{N}(\nu_s | 0, \tau^2) d\nu_s \\
&= \mathcal{N}(y_s | \theta, \sigma^2 + \tau^2)
\end{aligned}
$$

by properties of normal distributions.

### A.2 Posterior for Additive Model (Conjugate Case)

With conjugate priors:
$$
\beta_c \sim \mathcal{N}(0, \sigma_\beta^2)
$$

And known $\tau$, the posterior is:
$$
\boldsymbol{\beta} | \mathbf{y}, \tau \sim \mathcal{N}(\boldsymbol{\mu}_{\text{post}}, \boldsymbol{\Sigma}_{\text{post}})
$$

where:
$$
\begin{aligned}
\boldsymbol{\Sigma}_{\text{post}}^{-1} &= \sigma_\beta^{-2} \mathbf{I} + \mathbf{X}^T \boldsymbol{\Omega}^{-1} \mathbf{X} \\
\boldsymbol{\mu}_{\text{post}} &= \boldsymbol{\Sigma}_{\text{post}} \mathbf{X}^T \boldsymbol{\Omega}^{-1} \mathbf{y}
\end{aligned}
$$

with $\mathbf{X}$ the component difference matrix and $\boldsymbol{\Omega} = \text{diag}(\text{SE}_s^2 + \tau^2)$.

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Authors**: CNMA Platform Development Team
