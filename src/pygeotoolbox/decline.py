"""
Geothermal decline curves for reservoir pressure and temperature.

Inspired by pyResToolbox DCA (Decline Curve Analysis), reimplemented for geothermal.
"""
import numpy as np

def exponential_decline(
    y0: float,
    rate: float,
    years: int,
) -> list:
    """
    Exponential decline: y[t] = y0 * exp(-rate * t).
    y0 = initial value (pressure in kPa or temperature in C).
    rate = annual fractional decline.
    Returns list of values for t = 0..years (inclusive).
    """
    return [y0 * np.exp(-rate * t) for t in range(years + 1)]

def hyperbolic_decline(
    y0: float,
    initial_rate: float,
    b: float,
    years: int,
) -> list:
    """
    Hyperbolic decline: y[t] = y0 / (1 + b * initial_rate * t)^(1/b).
    b = 0.5 typical for moderate decline.
    Returns list of values for t = 0..years (inclusive).
    """
    if b <= 0:
        raise ValueError("b must be > 0 for hyperbolic decline")
    return [y0 / ((1.0 + b * initial_rate * t) ** (1.0 / b)) for t in range(years + 1)]

def reinjection_temperature_model(
    extraction_temp_C: float,
    reinjection_temp_C: float,
    fraction_cooled: float,
    years: int,
) -> list:
    """
    Temperature decline due to progressive cold-water reinjection.
    T_res[t] = T_initial - fraction_cooled * (T_initial - T_reinjection) * (1 - exp(-rate * t))
    fraction_cooled = fraction of total produced mass reinjected.
    Returns list of temperatures for t = 0..years.
    """
    # Effective thermal breakthrough rate depends on fraction_cooled
    rate = 0.05 + 0.2 * fraction_cooled  # empirical
    temps = []
    for t in range(years + 1):
        T_t = extraction_temp_C - fraction_cooled * (extraction_temp_C - reinjection_temp_C) * (1.0 - np.exp(-rate * t))
        temps.append(T_t)
    return temps
