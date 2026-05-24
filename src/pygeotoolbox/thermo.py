"""
Geothermal thermodynamic properties via CoolProp + IAPWS-IF97.

Inspired by pyResToolbox PVT module, reimplemented for geothermal water/steam.
"""
import numpy as np
try:
    from CoolProp.CoolProp import PropsSI
except ImportError:
    PropsSI = None

def ensure_coolprop():
    if PropsSI is None:
        raise RuntimeError("CoolProp not installed. Install with: pip install CoolProp")

# ---------------------------------------------------------------------------
# IAPWS-IF97 via CoolProp (single-phase)
# ---------------------------------------------------------------------------

def enthalpy_from_TP(T_C: float, P_kPa: float) -> float:
    """Returns enthalpy in J/kg."""
    ensure_coolprop()
    return PropsSI('H', 'T', T_C + 273.15, 'P', P_kPa * 1e3, 'Water')

def density_from_TP(T_C: float, P_kPa: float) -> float:
    """Returns density in kg/m3."""
    ensure_coolprop()
    return PropsSI('D', 'T', T_C + 273.15, 'P', P_kPa * 1e3, 'Water')

def viscosity_from_TP(T_C: float, P_kPa: float) -> float:
    """Returns dynamic viscosity in Pa*s."""
    ensure_coolprop()
    return PropsSI('V', 'T', T_C + 273.15, 'P', P_kPa * 1e3, 'Water')

def specific_heat_from_TP(T_C: float, P_kPa: float) -> float:
    """Returns cp in J/kg/K."""
    ensure_coolprop()
    return PropsSI('C', 'T', T_C + 273.15, 'P', P_kPa * 1e3, 'Water')

def thermal_conductivity_from_TP(T_C: float, P_kPa: float) -> float:
    """Returns thermal conductivity in W/m/K."""
    ensure_coolprop()
    return PropsSI('L', 'T', T_C + 273.15, 'P', P_kPa * 1e3, 'Water')

def phase_from_TP(T_C: float, P_kPa: float) -> str:
    """Returns 'liquid', 'gas', 'twophase', or 'supercritical'."""
    ensure_coolprop()
    phase_idx = PropsSI('Phase', 'T', T_C + 273.15, 'P', P_kPa * 1e3, 'Water')
    mapping = {
        0: 'liquid',
        1: 'gas',
        2: 'twophase',
        3: 'supercritical',
        5: 'supercritical_liquid',
        6: 'supercritical_gas',
    }
    return mapping.get(phase_idx, 'unknown')

# ---------------------------------------------------------------------------
# Saturation temperature (IAPWS-IF97 via iapws library)
# ---------------------------------------------------------------------------

def saturation_temperature(P_kPa: float) -> float | None:
    """Returns saturation temperature in C for given pressure (kPa), or None if invalid."""
    try:
        from iapws import IAPWS97
        sat = IAPWS97(P=P_kPa / 1e3, x=0)  # saturation liquid
        T = getattr(sat, 'T', None)
        if T is None:
            return None
        return T - 273.15
    except Exception:
        return None

def saturation_pressure(T_C: float) -> float | None:
    """Returns saturation pressure in kPa for given temperature (C), or None."""
    try:
        from iapws import IAPWS97
        sat = IAPWS97(T=T_C + 273.15, x=0)
        P = getattr(sat, 'P', None)
        if P is None:
            return None
        return P * 1e3
    except Exception:
        return None

def steam_quality_from_enthalpy(h_J_kg: float, P_kPa: float) -> float:
    """Returns steam quality (0-1) for given enthalpy at pressure.
    For single-phase liquid: returns 0.0, single-phase gas: returns 1.0."""
    ensure_coolprop()
    P_Pa = P_kPa * 1e3
    try:
        # Try direct CoolProp quality lookup
        q = PropsSI('Q', 'H', h_J_kg, 'P', P_Pa, 'Water')
        if q is not None and q >= 0:  # valid quality
            return q
        elif q == -1:
            # Below saturation: liquid
            return 0.0
        else:
            return float('nan')
    except Exception:
        pass
    # Fallback: compare enthalpy to saturation values
    try:
        h_liq = PropsSI('H', 'Q', 0, 'P', P_Pa, 'Water')
        h_vap = PropsSI('H', 'Q', 1, 'P', P_Pa, 'Water')
        if h_J_kg <= h_liq:
            return 0.0
        if h_J_kg >= h_vap:
            return 1.0
        return (h_J_kg - h_liq) / (h_vap - h_liq)
    except Exception:
        return float('nan')

# ---------------------------------------------------------------------------
# Convenience batch methods
# ---------------------------------------------------------------------------

def batch_properties(T_C_list, P_kPa_list, outputs=None):
    """Batch compute properties. Returns list of dicts."""
    if outputs is None:
        outputs = ['H', 'D', 'V', 'C', 'L']
    prop_map = {
        'H': ('enthalpy_J_kg', 'J/kg'),
        'D': ('density_kg_m3', 'kg/m3'),
        'V': ('viscosity_Pa_s', 'Pa*s'),
        'C': ('cp_J_kg_K', 'J/kg/K'),
        'L': ('thermal_cond_W_m_K', 'W/m/K'),
    }
    results = []
    for T, P in zip(T_C_list, P_kPa_list):
        row = {'T_C': T, 'P_kPa': P}
        for code, (key, _) in prop_map.items():
            if code in outputs:
                try:
                    row[key] = PropsSI(code, 'T', T + 273.15, 'P', P * 1e3, 'Water')
                except Exception:
                    row[key] = float('nan')
        results.append(row)
    return results
