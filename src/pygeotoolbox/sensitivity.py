"""
Geothermal sensitivity analysis and parameter sweep.

Inspired by pyResToolbox sensitivity module, reimplemented for geothermal.
"""
import numpy as np
from typing import Callable, Any

def one_factor_sweep(
    func: Callable,
    param_name: str,
    param_values: list,
    base_kwargs: dict,
) -> list:
    """
    Run single-factor sensitivity: vary one parameter while keeping others constant.
    Returns list of (param_value, result).
    """
    results = []
    for val in param_values:
        kwargs = dict(base_kwargs)
        kwargs[param_name] = val
        try:
            result = func(**{k: v for k, v in kwargs.items()})
        except Exception:
            result = None
        results.append((val, result))
    return results

def tornado_pairs(
    base_kwargs: dict,
    perturbation_fraction: float = 0.2,
) -> dict:
    """
    Determine parameter swing ranges for tornado chart.
    Returns dict of param_name -> (low_value, high_value, midpoint).
    """
    tornado = {}
    for key, val in base_kwargs.items():
        if isinstance(val, (int, float)) and val != 0:
            low = val * (1.0 - perturbation_fraction)
            high = val * (1.0 + perturbation_fraction)
            tornado[key] = (low, high, val)
    return tornado

def monte_carlo_geothermal(
    func: Callable,
    param_distributions: dict,  # param_name -> (mean, std)
    n_samples: int = 1000,
    seed: int | None = None,
) -> dict:
    """
    Simple Monte Carlo: draw parameters from normal distributions.
    Returns dict with results list, mean, p10, p50, p90.
    """
    if seed is not None:
        np.random.seed(seed)
    results = []
    for _ in range(n_samples):
        kwargs = {}
        for k, (mu, sigma) in param_distributions.items():
            kwargs[k] = np.random.normal(mu, sigma)
        try:
            result = func(**kwargs)
        except Exception:
            result = None
        results.append(result)
    valid = [r for r in results if r is not None and np.isfinite(r)]
    if not valid:
        return {"results": results, "mean": None, "p10": None, "p50": None, "p90": None}
    valid_s = sorted(valid)
    return {
        "results": results,
        "mean": np.mean(valid),
        "p10": np.percentile(valid_s, 10),
        "p50": np.percentile(valid_s, 50),
        "p90": np.percentile(valid_s, 90),
    }

def rank_correlation_sensitivity(
    func: Callable,
    param_distributions: dict,
    n_samples: int = 500,
    seed: int | None = None,
) -> list:
    """
    Rank correlation sensitivity: compute Spearman rank correlation
    between each parameter and output.
    Returns list of (param_name, correlation).
    """
    try:
        from scipy.stats import spearmanr
    except ImportError:
        return [(k, None) for k in param_distributions]
    if seed is not None:
        np.random.seed(seed)
    params_matrix = []
    outputs = []
    for _ in range(n_samples):
        row = {}
        for k, (mu, sigma) in param_distributions.items():
            row[k] = np.random.normal(mu, sigma)
        params_matrix.append(row)
        try:
            result = func(**row)
        except Exception:
            result = float('nan')
        outputs.append(result)
    corrs = []
    for k in param_distributions:
        vals = [r[k] for r in params_matrix]
        if all(np.isfinite(v) for v in vals) and all(np.isfinite(o) for o in outputs):
            corr, _ = spearmanr(vals, outputs)
            corrs.append((k, corr))
        else:
            corrs.append((k, None))
    return corrs
