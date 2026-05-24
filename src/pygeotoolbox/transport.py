"""
Transport properties: thermal conductivity and dynamic viscosity.

Based on IAPWS Releases:
- IAPWS-IF97 for thermodynamic state (T, P, rho)
- IAPWS Release on Thermal Conductivity of Water and Steam
- IAPWS Release on Viscosity of Water and Steam

For geothermal: valid from 0 C to 800 C, 0.1 MPa to 100 MPa.
Uses iapws package if available; falls back to CoolProp.
"""
import math

try:
    from iapws import IAPWS97
    _HAS_IAPWS = True
except ImportError:
    IAPWS97 = None
    _HAS_IAPWS = False

try:
    from CoolProp.CoolProp import PropsSI
    _HAS_COOLPROP = True
except ImportError:
    _HAS_COOLPROP = False


# --------------------------------------------------
# Thermal Conductivity (IAPWS formulation)
# --------------------------------------------------

def _iapws_thermal_conductivity(T_C, P_kPa):
    """IAPWS thermal conductivity W/(m·K) using iapws package."""
    if not _HAS_IAPWS:
        return None
    P_MPa = P_kPa / 1000.0
    T_K = T_C + 273.15
    try:
        w = IAPWS97(P=P_MPa, T=T_K)
        # iapws97 memiliki properti k (thermal conductivity)
        if hasattr(w, 'k'):
            return float(w.k)
        return None
    except Exception:
        return None


# --------------------------------------------------
# Dynamic Viscosity (IAPWS formulation)
# --------------------------------------------------

def _iapws_viscosity(T_C, P_kPa):
    """Dynamic viscosity Pa·s menggunakan iapws package."""
    if not _HAS_IAPWS:
        return None
    P_MPa = P_kPa / 1000.0
    T_K = T_C + 273.15
    try:
        w = IAPWS97(P=P_MPa, T=T_K)
        # iapws97 memiliki properti mu (dynamic viscosity)
        if hasattr(w, 'mu'):
            return float(w.mu)
        return None
    except Exception:
        return None


# --------------------------------------------------
# CoolProp Fallback
# --------------------------------------------------

def _coolprop_thermal_conductivity(T_C, P_kPa):
    """Thermal conductivity via CoolProp."""
    if not _HAS_COOLPROP:
        return None
    try:
        return PropsSI('L', 'T', T_C + 273.15, 'P', P_kPa * 1000, 'Water')
    except Exception:
        return None


def _coolprop_viscosity(T_C, P_kPa):
    """Dynamic viscosity via CoolProp."""
    if not _HAS_COOLPROP:
        return None
    try:
        return PropsSI('V', 'T', T_C + 273.15, 'P', P_kPa * 1000, 'Water')
    except Exception:
        return None


# --------------------------------------------------
# Public API
# --------------------------------------------------

def thermal_conductivity(T_C: float, P_kPa: float) -> float | None:
    """Thermal conductivity in W/(m·K) at T (C) and P (kPa).
    Priority: IAPWS -> CoolProp.
    Returns None if out of range or no backend available.
    """
    val = _iapws_thermal_conductivity(T_C, P_kPa)
    if val is not None:
        return val
    return _coolprop_thermal_conductivity(T_C, P_kPa)


def dynamic_viscosity(T_C: float, P_kPa: float) -> float | None:
    """Dynamic viscosity in Pa·s (kg/(m·s)) at T (C) and P (kPa).
    Priority: IAPWS -> CoolProp.
    Returns None if out of range or no backend available.
    """
    val = _iapws_viscosity(T_C, P_kPa)
    if val is not None:
        return val
    return _coolprop_viscosity(T_C, P_kPa)


def transport_properties(T_C: float, P_kPa: float) -> dict:
    """Complete transport property package at given state.
    Returns dict with k, mu, nu (kinematic viscosity), Pr (Prandtl number).
    """
    k = thermal_conductivity(T_C, P_kPa)
    mu = dynamic_viscosity(T_C, P_kPa)
    
    # Need density for kinematic viscosity and Pr
    rho = None
    if _HAS_IAPWS:
        try:
            w = IAPWS97(P=P_kPa/1000.0, T=T_C+273.15)
            rho = w.rho
        except Exception:
            pass
    elif _HAS_COOLPROP:
        try:
            rho = PropsSI('D', 'T', T_C+273.15, 'P', P_kPa*1000, 'Water')
        except Exception:
            pass
    
    result = {
        "T_C": round(T_C, 6),
        "P_kPa": round(P_kPa, 6),
        "k_W_mK": round(k, 9) if k else None,
        "mu_Pas": round(mu, 9) if mu else None,
    }
    
    if rho and mu:
        nu = mu / rho
        result["nu_m2_s"] = round(nu, 9)
        # Need cp for Pr
        cp = None
        if _HAS_COOLPROP:
            try:
                cp = PropsSI('C', 'T', T_C+273.15, 'P', P_kPa*1000, 'Water')
            except Exception:
                pass
        if cp and k and cp > 0:
            Pr = mu * cp / k
            result["Pr"] = round(Pr, 6)
    
    return result


if __name__ == "__main__":
    print("=== Transport Properties at Standard States ===")
    states = [
        (25, 101.325),    # Liquid at ambient
        (200, 2000),      # Geothermal liquid
        (300, 10000),     # Supercritical
        (500, 20000),     # Superheated steam
    ]
    for T, P in states:
        k = thermal_conductivity(T, P)
        mu = dynamic_viscosity(T, P)
        print(f"T={T} C, P={P} kPa → k={k:.4f} W/mK, mu={mu:.6e} Pa·s")
    
    print("\n=== Transport Properties Package ===")
    for T, P in states:
        props = transport_properties(T, P)
        print(f"T={T} C, P={P} kPa → {props}")
