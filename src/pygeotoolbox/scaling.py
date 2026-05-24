"""
Geothermal scaling and brine chemistry analysis.

Inspired by pyResToolbox brine module, reimplemented for geothermal scaling.
"""
import math

# ---------------------------------------------------------------------------
# Scaling indices
# ---------------------------------------------------------------------------

def ryznar_index(T_C: float, Ca_mg_L: float, HCO3_mg_L: float, pH: float) -> float:
    """
    Ryznar Stability Index (RSI) for CaCO3 scaling tendency.
    RSI < 6: scaling likely. RSI > 7: corrosive. 6-7: stable.
    Ca in mg/L as CaCO3. HCO3 in mg/L.
    """
    # Simplified saturation pH for CaCO3
    pHs = 9.3 + math.log10(Ca_mg_L / 1000.0) + math.log10(HCO3_mg_L / 1000.0) - 0.01 * (T_C - 25)
    return 2.0 * pHs - pH

def sio2_scaling_risk(SiO2_mg_L: float, T_C: float) -> dict:
    """
    Amorphous silica scaling risk at temperature.
    Above 150 C, amorphous silica solubility ~ 120 mg/L (conservative).
    Returns risk classification and limiting concentration.
    """
    # Simplified temperature-dependent solubility curve
    if T_C <= 0:
        return {"risk": "invalid", "limit_mg_L": None, "ratio": None}
    solubility = 300.0 * math.exp(-0.01 * T_C)  # approximate
    ratio = SiO2_mg_L / solubility
    if ratio < 0.8:
        risk = "low"
    elif ratio < 1.0:
        risk = "medium"
    elif ratio < 1.2:
        risk = "high"
    else:
        risk = "critical"
    return {"risk": risk, "limit_mg_L": solubility, "ratio": ratio}

def reservoir_brine_density(T_C: float, salinity_wt_percent: float = 0.0) -> float:
    """
    Approximate brine density using pure-water density scaled with salinity.
    Returns density in kg/m3.
    """
    try:
        from CoolProp.CoolProp import PropsSI
        rho_pure = PropsSI('D', 'T', T_C + 273.15, 'P', 101325, 'Water')
    except Exception:
        # fallback approximation
        rho_pure = 1000.0 - 0.4 * T_C
    # NaCl solution: each wt% adds ~7 kg/m3
    rho_brine = rho_pure + salinity_wt_percent * 7.0
    return rho_brine

# ---------------------------------------------------------------------------
# Reinjection chemistry
# ---------------------------------------------------------------------------

def corrosivity_index(pH: float, Cl_mg_L: float, H2S_mg_L: float = 0.0) -> dict:
    """
    Rough corrosivity score for geothermal brine.
    pH < 6 = acidic, Cl > 50000 mg/L = highly corrosive.
    Returns score 0-10 and classification.
    """
    score = 0.0
    if pH < 6:
        score += 3.0
    if Cl_mg_L > 50000:
        score += 3.0
    elif Cl_mg_L > 20000:
        score += 2.0
    else:
        score += 1.0
    if H2S_mg_L > 10:
        score += 2.0
    elif H2S_mg_L > 1:
        score += 1.0
    score = min(score, 10.0)
    if score >= 7:
        cls = "highly_corrosive"
    elif score >= 4:
        cls = "moderately_corrosive"
    else:
        cls = "mild"
    return {"score": score, "class": cls}
