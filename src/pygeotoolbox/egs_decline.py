"""
EGS temporal decline and sustainability models.

Implements:
- Exponential thermal drawdown
- Harmonic decline (common for geothermal)
- Recovery time after shut-in

Author: Zulfikar Aji Kusworo, 2026
"""
import numpy as np

def exponential_decline(
    P_initial_MW: float,
    t_years: float,
    half_life_years: float = 10.0,
) -> float:
    """
    Exponential decline: P(t) = P0 * exp(-λt)
    λ = ln(2) / t_half
    """
    if half_life_years <= 0 or t_years < 0:
        return P_initial_MW
    lam = np.log(2) / half_life_years
    return P_initial_MW * np.exp(-lam * t_years)

def harmonic_decline(
    P_initial_MW: float,
    t_years: float,
    decline_rate_per_year: float = 0.1,
) -> float:
    """
    Harmonic decline: P(t) = P0 / (1 + b*D*t)
    Common for geothermal (b=1 for harmonic).
    """
    if decline_rate_per_year <= 0 or t_years < 0:
        return P_initial_MW
    return P_initial_MW / (1.0 + decline_rate_per_year * t_years)

def hyperbolic_decline(
    P_initial_MW: float,
    t_years: float,
    decline_rate_per_year: float = 0.1,
    b: float = 0.5,
) -> float:
    """
    Hyperbolic decline: P(t) = P0 / (1 + b*D*t)^(1/b)
    b=0.5 common for EGS fracture-dominated systems.
    """
    if decline_rate_per_year <= 0 or t_years < 0:
        return P_initial_MW
    return P_initial_MW / ((1.0 + b * decline_rate_per_year * t_years) ** (1.0 / b))

def average_power_over_lifetime(
    P_initial_MW: float,
    lifetime_years: float,
    decline_model: str = 'harmonic',
    decline_rate: float = 0.1,
    half_life: float = 10.0,
) -> float:
    """Average power over plant lifetime using numerical integration."""
    n_points = 100
    dt = lifetime_years / n_points
    powers = []
    
    for i in range(n_points):
        t = i * dt
        if decline_model == 'exponential':
            P = exponential_decline(P_initial_MW, t, half_life)
        elif decline_model == 'harmonic':
            P = harmonic_decline(P_initial_MW, t, decline_rate)
        elif decline_model == 'hyperbolic':
            P = hyperbolic_decline(P_initial_MW, t, decline_rate)
        else:
            P = P_initial_MW
        powers.append(P)
    
    return np.mean(powers)

def egs_lifetime_profile(
    P_initial_MW: float,
    lifetime_years: float = 30.0,
    decline_model: str = 'harmonic',
    decline_rate: float = 0.1,
) -> list:
    """Generate year-by-year power profile for EGS plant."""
    profile = []
    for year in range(int(lifetime_years) + 1):
        if decline_model == 'harmonic':
            P = harmonic_decline(P_initial_MW, year, decline_rate)
        elif decline_model == 'exponential':
            P = exponential_decline(P_initial_MW, year, 1.0 / decline_rate)
        else:
            P = P_initial_MW
        profile.append({'year': year, 'power_MW': P})
    return profile


if __name__ == '__main__':
    print("="*70)
    print("EGS DECLINE MODELS - DEMONSTRATION")
    print("="*70)
    
    P0 = 10.0  # MW initial
    
    print(f"\nInitial power: {P0} MW")
    print(f"\nYear-by-year decline (harmonic, D=10%/year):")
    print(f"{'Year':<6} {'Harmonic':<12} {'Exponential':<12} {'Hyperbolic':<12}")
    print("-"*50)
    
    for year in [0, 1, 5, 10, 20, 30]:
        h = harmonic_decline(P0, year, 0.10)
        e = exponential_decline(P0, year, 7.0)
        hy = hyperbolic_decline(P0, year, 0.10, 0.5)
        print(f"{year:<6} {h:<12.2f} {e:<12.2f} {hy:<12.2f}")
    
    print(f"\nAverage power over 30 years:")
    avg_h = average_power_over_lifetime(P0, 30, 'harmonic', 0.10)
    avg_e = average_power_over_lifetime(P0, 30, 'exponential', half_life=7.0)
    print(f"  Harmonic:    {avg_h:.2f} MW ({avg_h/P0*100:.1f}% of initial)")
    print(f"  Exponential: {avg_e:.2f} MW ({avg_e/P0*100:.1f}% of initial)")
    
    print("\n" + "="*70)
