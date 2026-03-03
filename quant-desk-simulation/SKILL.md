---
name: quant-desk-simulation
description: Use when building quantitative simulation models for prediction markets, binary contracts, or correlated event portfolios — covers Monte Carlo, importance sampling, particle filters, copulas, and agent-based models.
---

# Quant Desk Simulation

## Overview

A prediction market contract embedded in a portfolio of correlated events — with time-varying information flow, order book dynamics, and execution risk — has dozens of parameters. A coin flip has one: `p`. This stack of techniques handles the difference.

Read in order. Each layer builds on the last.

> Source: "How to Simulate Like a Quant Desk" by @gemchange_ltd (Feb 28, 2026)

---

## Part I — Monte Carlo: The Foundation

Every simulation reduces to: draw samples from a distribution, compute a statistic, repeat.

**Estimator:** `p̂_N = (1/N) Σ 1_A(X_i)`
**Convergence:** `O(N^{-1/2})`, variance maximized at `p = 0.5`
**Precision target:** ±0.01 at 95% confidence when `p = 0.50` → ~9,604 samples

```python
import numpy as np

def simulate_binary_contract(S0, K, mu, sigma, T, N_paths=100_000):
    """Monte Carlo for a binary contract (e.g., 'Will AAPL close > $200?')"""
    Z = np.random.standard_normal(N_paths)
    S_T = S0 * np.exp((mu - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)
    payoffs = (S_T > K).astype(float)
    p_hat = payoffs.mean()
    se = payoffs.std() / np.sqrt(N_paths)
    return {'probability': p_hat, 'std_error': se, 'ci_95': (p_hat - 1.96*se, p_hat + 1.96*se)}
```

**Calibration — Brier Score:** `BS = (1/N) Σ (p_i - o_i)²`
- < 0.20 → good | < 0.10 → excellent | Top forecasters (538): 0.06–0.12

---

## Part II — Importance Sampling: Tail-Risk Contracts

Crude MC on a contract trading at $0.003 ("S&P drops 20% in a week") gives 0 or 1 hit at 100k samples — useless. Importance sampling fixes this.

**Exponential tilting:** Shift the distribution toward the rare region, correct bias with a likelihood ratio.

```python
def rare_event_IS(K_crash, mu_original, sigma, T, N_paths=5000):
    """IS estimator for extreme downside contracts."""
    log_threshold = np.log(K_crash)
    mu_tilt = log_threshold / T - 0.5 * sigma**2   # center on crash
    log_returns_tilted = np.random.normal(mu_tilt * T, sigma * np.sqrt(T), N_paths)
    S_T_tilted = np.exp(log_returns_tilted)
    # Likelihood ratio correction
    log_LR = ((mu_original - mu_tilt) * log_returns_tilted / (sigma**2) -
              0.5 * (mu_original**2 - mu_tilt**2) * T / sigma**2)
    LR = np.exp(log_LR)
    is_estimates = (S_T_tilted < K_crash).astype(float) * LR
    return {'p_IS': is_estimates.mean(), 'se_IS': is_estimates.std() / np.sqrt(N_paths)}
```

**Variance reduction:** 100–10,000x over crude MC. 100 IS samples > 1,000,000 crude samples for extreme events.

---

## Part III — Sequential Monte Carlo: Real-Time Updating

Election night. New data arrives every minute. The particle filter updates probability estimates in real time without rerunning the full simulation.

**State-space model:**
- Hidden state `x_t`: true probability (unobserved), evolves as logit random walk
- Observation `y_t`: market prices, polls, vote counts

**Bootstrap Particle Filter algorithm:**
1. INITIALIZE: `x_0^(i) ~ Prior` for i = 1,...,N; weights `w_0^(i) = 1/N`
2. For each new observation `y_t`:
   - PROPAGATE: `x_t^(i) ~ f(·|x_{t-1}^(i))`
   - REWEIGHT: `w_t^(i) ∝ g(y_t | x_t^(i))`
   - NORMALIZE: `w̃_t^(i) = w_t^(i) / Σ_j w_t^(j)`
   - RESAMPLE if `ESS = 1/Σ(w̃_t^(i))² < N/2`

```python
from scipy.special import expit, logit
import numpy as np

class PredictionMarketParticleFilter:
    def __init__(self, N_particles=1000, prior_prob=0.50, process_vol=0.05, obs_noise=0.03):
        self.N = N_particles
        logit_prior = logit(prior_prob)
        self.logit_particles = np.random.normal(logit_prior, process_vol, N_particles)
        self.weights = np.ones(N_particles) / N_particles

    def update(self, observed_price):
        # Propagate
        self.logit_particles += np.random.normal(0, 0.05, self.N)
        prob_particles = expit(self.logit_particles)
        # Reweight
        log_likelihood = -0.5 * ((observed_price - prob_particles) / 0.03)**2
        self.weights = np.exp(log_likelihood - log_likelihood.max())
        self.weights /= self.weights.sum()
        # Resample if ESS low
        ess = 1.0 / np.sum(self.weights**2)
        if ess < self.N / 2:
            indices = np.searchsorted(np.cumsum(self.weights),
                                      np.random.uniform(0, 1, self.N) / self.N + np.arange(self.N) / self.N)
            self.logit_particles = self.logit_particles[indices]
            self.weights = np.ones(self.N) / self.N

    def estimate(self):
        return np.average(expit(self.logit_particles), weights=self.weights)
```

**Why better than raw market price?** Smooths noise — when price spikes on a single trade, the filter tempers the update based on historical observation volatility.

---

## Part IV — Variance Reduction (Stack All Three)

These combine multiplicatively. Together: **100–500x** variance reduction.

| Technique | How | Reduction |
|-----------|-----|-----------|
| **Antithetic variates** | Use `(Z, -Z)` pairs | 50–75%, zero cost |
| **Control variates** | Use Black-Scholes digital price as baseline | Depends on correlation |
| **Stratified sampling** | Partition space into J strata, sample within each | Always ≤ crude MC |

```python
def stratified_binary_mc(S0, K, mu, sigma, T, J=10, N_total=10_000):
    """Stratified MC: partition price space into J strata."""
    n_per_stratum = N_total // J
    estimates = []
    for j in range(J):
        U = np.random.uniform(j/J, (j+1)/J, n_per_stratum)
        Z = scipy.stats.norm.ppf(U)
        S_T = S0 * np.exp((mu - 0.5*sigma**2)*T + sigma*np.sqrt(T)*Z)
        estimates.append((S_T > K).mean())
    return np.mean(estimates), np.std(estimates) / np.sqrt(J)
```

---

## Part V — Copulas: Tail Dependence

Linear correlation matrices fail to model extreme co-movements. In 2008, the Gaussian copula's failure caused the global financial crisis. In prediction markets: when one swing state surprises, the probability all flip together is far higher than Gaussian predicts.

**Sklar's Theorem:** `F(x₁,...,xd) = C(F₁(x₁),...,Fd(xd))`

| Copula | Tail Dependence | When to Use |
|--------|----------------|-------------|
| Gaussian | `λU = λL = 0` | Never for correlated prediction markets |
| Student-t (ν=4) | `λU = λL ≈ 0.18` | Default for symmetric tail risk |
| Clayton | Lower only | One market crashing drags others |
| Gumbel | Upper only | Correlated positive resolutions |
| **Vine copula** | Flexible | d > 5 contracts |

```python
from scipy import stats

def simulate_correlated_outcomes_t(probs, corr_matrix, nu=4, N=500_000):
    """Student-t copula: symmetric tail dependence."""
    d = len(probs)
    L = np.linalg.cholesky(corr_matrix)
    Z = np.random.normal(size=(N, d)) @ L.T
    S = np.random.chisquare(nu, N)
    T = Z / np.sqrt(S[:, None] / nu)
    U = stats.t.cdf(T, df=nu)
    return (U < np.array(probs)).astype(int)
```

**t-copula routinely shows 2–5x higher probability of extreme joint outcomes** vs Gaussian.

For `d > 5`: use vine copulas (`pyvinecopulib` in Python, `VineCopula` in R).

---

## Part VI — Agent-Based Simulation

When you don't know the data-generating process, simulate the agents instead.

**Key insight (Gode & Sunder, 1993):** Zero-intelligence agents — random orders subject only to budget constraints — achieve near-100% allocative efficiency. Farmer et al. (2005) explained 96% of spread variation on the London Stock Exchange with one parameter.

**Agent types:**
- **Informed:** Trade toward true probability with noisy signal
- **Noise:** Random buy/sell
- **Market maker:** Tighten spread, provide liquidity

Price impact (Kyle, 1985): `λ = σ_v / (2σ_u)` where `σ_v` = informed vol, `σ_u` = noise vol.

---

## Part VII — Production Stack

```
LAYER 1: DATA INGESTION
  WebSocket → Polymarket CLOB API (real-time prices, volumes)
  News/poll feeds → NLP → probability signals
  On-chain event data (Polygon)

LAYER 2: PROBABILITY ENGINE
  Hierarchical Bayesian model (Stan/PyMC) → state-level posteriors
  Particle filter → real-time updating
  Jump-diffusion SDE → path simulation for risk
  Ensemble → weighted average of model outputs

LAYER 3: DEPENDENCY MODELING
  Vine copula → pairwise dependencies
  Factor model → shared national/global risk factors
  Tail dependence → t-copula

LAYER 4: RISK MANAGEMENT
  EVT-based VaR and Expected Shortfall
  Reverse stress testing → worst-case scenarios
  Correlation stress → spike in state correlations
  Liquidity risk → order book depth monitoring

LAYER 5: MONITORING
  Brier score tracking (calibrated?)
  P&L attribution (which model component added value?)
  Drawdown alerts
  Model drift detection
```

---

## Quick Reference

| Problem | Tool |
|---------|------|
| Single binary contract | Monte Carlo (GBM) |
| Calibration check | Brier Score |
| Rare/tail event pricing | Importance Sampling (exponential tilting) |
| Real-time updating | Particle Filter (SMC) |
| Variance too high | Antithetic + control variate + stratification |
| Correlated contracts | Student-t or Clayton copula |
| d > 5 correlated contracts | Vine copula |
| Unknown market dynamics | Agent-based simulation |

## References

- Dalen (2025). "Toward Black-Scholes for Prediction Markets." arXiv:2510.15205
- Farmer, Patelli & Zovko (2005). "The Predictive Power of Zero Intelligence." PNAS
- Gode & Sunder (1993). "Allocative Efficiency of Markets with Zero-Intelligence Traders." JPE
- Kyle (1985). "Continuous Auctions and Insider Trading." Econometrica
- Aas et al. (2009). "Pair-Copula Constructions of Multiple Dependence." Insurance: Mathematics and Economics
