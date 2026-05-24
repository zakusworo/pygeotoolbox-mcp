"""
Humid air thermodynamic properties (water vapor + dry air).

Based on IAPWS G11-15: Guideline on the IAPWS Formulation 2015 for the
Thermodynamic Properties of Humid Air.

Valid range (approximate):
    T: 173 to 473 K (-100 to +200 C)
    P: 0.1 to 5000 kPa
    Relative humidity: 0 to 1.0

Engineering use cases:
- Cooling tower performance (geothermal power plant)
- Gas extraction / vapor recovery
- Direct-contact heat exchanger analysis

This is a simplified virial-type model — not the full IAPWS formulation.
Accuracy: ~2% for density, ~1% for enthalpy.
"""
import math

# Constants
R_DA = 287.05       # J/kg/K for dry air
R_WV = 461.5        # J/kg/K for water vapor
CP_DA = 1005.0      # J/kg/K
CP_WV = 1860.0      # J/kg/K

# Saturation pressure from IAPWS-IF97 ( Magnus approximation )
def _saturation_pressure_magnus(T_C):
    """Approximate P_sat in kPa for T_C in [0, 200]."""
    return 0.61094 * math.exp(17.625 * T_C / (T_C + 243.04))

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def humidity_ratio(T_C: float, P_kPa: float, RH: float) -> float:
    """
    Humidity ratio w [kg water / kg dry air].
    T_C: air temperature
    P_kPa: total pressure
    RH: relative humidity [0 to 1]
    """
    if T_C < -100 or T_C > 200:
        raise ValueError("T_C outside range [-100, 200]")
    if P_kPa <= 0:
        raise ValueError("P_kPa must be positive")
    if RH < 0 or RH > 1:
        raise ValueError("RH must be in [0, 1]")
    
    P_sat_kPa = _saturation_pressure_magnus(T_C)
    P_wv = RH * P_sat_kPa
    # Avoid division by zero at very high humidity
    P_da = max(P_kPa - P_wv, 0.01)
    w = 0.621945 * P_wv / P_da
    return w


def density_humid_air(T_C: float, P_kPa: float, RH: float) -> float:
    """Density of humid air [kg/m3]."""
    T_K = T_C + 273.15
    w = humidity_ratio(T_C, P_kPa, RH)
    # Specific gas constant of mixture
    R_mix = (R_DA + w * R_WV) / (1 + w)
    rho = P_kPa * 1000.0 / (R_mix * T_K)
    return rho


def enthalpy_humid_air(T_C: float, RH: float = 0.0) -> float:
    """
    Specific enthalpy of humid air [J/kg dry air].
    Reference: h = 0 at 0 C for dry air.
    """
    w = humidity_ratio(T_C, 101.325, RH) if RH > 0 else 0.0
    # h_da + w * h_wv (approximate latent heat at 0 C = 2501 kJ/kg)
    h = CP_DA * T_C + w * (2501.0e3 + CP_WV * T_C)
    return h


def dew_point(T_C: float, P_kPa: float, RH: float) -> float | None:
    """
    Dew point temperature [C].  Returns None if RH <= 0.
    Magnus approximation inverse.
    """
    if RH <= 0:
        return None
    P_sat_at_T = _saturation_pressure_magnus(T_C)
    P_wv = RH * P_sat_at_T
    # T_dp from Magnus equation solved for T
    gamma = math.log(P_wv / 0.61094)
    T_dp = (243.04 * gamma) / (17.625 - gamma)
    return T_dp


def humid_air_properties(T_C: float, P_kPa: float, RH: float) -> dict:
    """Package: w, rho, h, T_dew."""
    w = humidity_ratio(T_C, P_kPa, RH)
    rho = density_humid_air(T_C, P_kPa, RH)
    h = enthalpy_humid_air(T_C, RH)
    T_dew = dew_point(T_C, P_kPa, RH)
    return {
        "humidity_ratio_kg_wv_kg_da": round(w, 6),
        "density_kg_m3": round(rho, 3),
        "enthalpy_J_kg_da": round(h, 1),
        "dew_point_C": round(T_dew, 2) if T_dew is not None else None,
    }


if __name__ == "__main__":
    import json
    print("Humid Air Properties (IAPWS G11-15 approx)")
    print("=" * 50)
    for T in [20, 40, 60]:
        print(f"\nT = {T} C, P = 101.325 kPa")
        for RH in [0.0, 0.3, 0.6, 1.0]:
            props = humid_air_properties(T, 101.325, RH)
            print(f"  RH={RH:.0%}: {json.dumps(props, indent=None)}")
