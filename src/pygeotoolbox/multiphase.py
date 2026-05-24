"""
Multi-phase flow models for geothermal wellbore simulation.

Implements:
- Homogeneous equilibrium model (HEM) — simplest, single velocity
- Drift-flux model — Zuber-Findlay, improved for geothermal applications

These models are simplified but capture the essential physics of
two-phase flow in geothermal wells, improving accuracy over single-phase
IPR/TPR for EGS and liquid-dominated systems.

Author: Zulfikar Aji Kusworo, 2026
"""
import numpy as np

try:
    from .thermo import enthalpy_from_TP, density_from_TP, viscosity_from_TP, saturation_pressure
except ImportError:
    from thermo import enthalpy_from_TP, density_from_TP, viscosity_from_TP, saturation_pressure

# ---------------------------------------------------------------------------
# 1. Homogeneous Equilibrium Model (HEM)
# ---------------------------------------------------------------------------

def hem_density(x: float, rho_l: float, rho_g: float) -> float:
    """Mixture density for homogeneous model. x = quality (mass fraction gas)."""
    if x <= 0:
        return rho_l
    if x >= 1:
        return rho_g
    return 1.0 / (x / rho_g + (1 - x) / rho_l)

def hem_viscosity(x: float, mu_l: float, mu_g: float) -> float:
    """Mixture viscosity (McAdams correlation)."""
    if x <= 0:
        return mu_l
    if x >= 1:
        return mu_g
    return 1.0 / (x / mu_g + (1 - x) / mu_l)

# ---------------------------------------------------------------------------
# 2. Drift-Flux Model (Zuber-Findlay)
# ---------------------------------------------------------------------------

def drift_flux_velocity(x: float, rho_l: float, rho_g: float, j_total: float,
                       C0: float = 1.2, V_d: float = 0.35) -> tuple:
    """
    Drift-flux model for gas velocity and void fraction.
    
    Parameters:
        x: quality (mass fraction gas)
        rho_l, rho_g: liquid and gas density (kg/m³)
        j_total: total superficial velocity (m/s)
        C0: distribution parameter (1.0-1.5)
        V_d: drift velocity (m/s, ~0.2-0.5 for bubbly/slug)
    
    Returns:
        (v_g, alpha) — gas velocity (m/s), void fraction
    """
    if x <= 0:
        return 0.0, 0.0
    if x >= 1:
        return j_total, 1.0
    
    # Void fraction from Zuber-Findlay
    # alpha = j_g / (C0 * j_total + V_d)
    # where j_g = x * j_total * rho_mix / rho_g
    rho_mix = hem_density(x, rho_l, rho_g)
    j_g = x * j_total * rho_mix / rho_g
    
    alpha = j_g / (C0 * j_total + V_d)
    alpha = max(0.0, min(alpha, 1.0))
    
    v_g = j_g / alpha if alpha > 0 else 0.0
    return v_g, alpha

def slip_ratio(x: float, rho_l: float, rho_g: float, C0: float = 1.2, V_d: float = 0.35,
               j_total: float = 1.0) -> float:
    """Slip ratio K = v_g / v_l from drift-flux model."""
    v_g, alpha = drift_flux_velocity(x, rho_l, rho_g, j_total, C0, V_d)
    if alpha >= 1.0 or alpha <= 0:
        return 1.0
    j_l = (1 - x) * hem_density(x, rho_l, rho_g) / rho_l * j_total
    v_l = j_l / (1 - alpha)
    return v_g / v_l if v_l > 0 else 1.0

# ---------------------------------------------------------------------------
# 3. Two-Phase Pressure Drop (Beggs-Brill simplified)
# ---------------------------------------------------------------------------

def beggs_brill_pressure_drop(
    x: float,
    rho_l: float,
    rho_g: float,
    mu_l: float,
    mu_g: float,
    D_m: float,
    v_ms: float,
    L_m: float,
    inclination_deg: float = 90.0,
    g: float = 9.81,
) -> dict:
    """
    Simplified Beggs-Brill two-phase pressure drop.
    
    Parameters:
        x: quality
        rho_l, rho_g: densities (kg/m³)
        mu_l, mu_g: viscosities (Pa·s)
        D_m: pipe diameter (m)
        v_ms: mixture velocity (m/s)
        L_m: pipe length (m)
        inclination_deg: pipe inclination (90 = vertical)
    
    Returns:
        dict with 'friction_Pa', 'hydrostatic_Pa', 'total_Pa', 'regime'
    """
    rho_mix = hem_density(x, rho_l, rho_g)
    mu_mix = hem_viscosity(x, mu_l, mu_g)
    
    # Flow regime (simplified)
    if x < 0.01:
        regime = 'liquid'
    elif x < 0.3:
        regime = 'bubbly/slug'
    elif x < 0.8:
        regime = 'slug/churn'
    else:
        regime = 'annular/mist'
    
    # Reynolds number
    Re = rho_mix * v_ms * D_m / mu_mix
    
    # Friction factor (Colebrook-White approximation)
    if Re < 2300:
        f = 16.0 / Re
    else:
        # Blasius: f = 0.079 / Re^0.25
        f = 0.079 / (Re ** 0.25)
    
    # Hydrostatic (gravitational)
    hydrostatic_Pa = rho_mix * g * L_m * np.sin(np.radians(inclination_deg))
    
    # Frictional
    friction_Pa = f * (L_m / D_m) * (rho_mix * v_ms ** 2) / 2.0
    
    # Acceleration (usually negligible for geothermal wells)
    acceleration_Pa = 0.0
    
    total_Pa = friction_Pa + hydrostatic_Pa + acceleration_Pa
    
    return {
        'friction_Pa': friction_Pa,
        'hydrostatic_Pa': hydrostatic_Pa,
        'acceleration_Pa': acceleration_Pa,
        'total_Pa': total_Pa,
        'regime': regime,
        'Re': Re,
        'f': f,
        'rho_mix': rho_mix,
    }

# ---------------------------------------------------------------------------
# 4. Quality Profile Along Wellbore (energy balance)
# ---------------------------------------------------------------------------

def quality_profile(
    h_inlet: float,
    P_surface_kPa: float,
    P_reservoir_kPa: float,
    depth_m: float,
    mass_flow_kg_s: float,
    D_m: float = 0.2,
    T_reservoir_C: float = 250.0,
) -> list:
    """
    Compute quality profile from reservoir to surface using HEM.
    
    Parameters:
        h_inlet: inlet enthalpy (J/kg)
        P_surface_kPa: surface pressure (kPa)
        P_reservoir_kPa: reservoir pressure (kPa)
        depth_m: well depth (m)
        mass_flow_kg_s: mass flow rate (kg/s)
        D_m: well diameter (m)
        T_reservoir_C: reservoir temperature (°C)
    
    Returns:
        List of dicts with depth, pressure, quality, regime
    """
    n_segments = 20
    dz = depth_m / n_segments
    A = np.pi * (D_m / 2) ** 2  # m²
    
    # Inlet conditions
    P_kPa = P_reservoir_kPa
    h = h_inlet
    
    # Try to get saturation properties
    T_sat = T_reservoir_C  # initialize before try
    P_kPa = P_reservoir_kPa
    h = h_inlet
    
    try:
        # At reservoir P
        h_f = enthalpy_from_TP(T_sat - 5, P_kPa)  # saturated liquid
        h_g = enthalpy_from_TP(T_sat + 5, P_kPa)   # saturated vapor
    except:
        # Fallback
        h_f = 4.18e3 * T_sat  # J/kg
        h_g = 2.675e6 + 1.8e3 * (T_sat - 100)  # J/kg
    
    profile = []
    
    for i in range(n_segments + 1):
        z = i * dz
        
        # Quality from enthalpy
        if h <= h_f:
            x = 0.0
        elif h >= h_g:
            x = 1.0
        else:
            x = (h - h_f) / (h_g - h_f)
        
        # Pressure drop (simplified)
        # Use linear interpolation for P
        P = P_kPa - i * (P_kPa - P_surface_kPa) / n_segments
        
        # Get properties at this P
        try:
            rho_l = density_from_TP(T_sat - 5, P)
            rho_g = density_from_TP(T_sat + 5, P)
            mu_l = viscosity_from_TP(T_sat - 5, P)
            mu_g = viscosity_from_TP(T_sat + 5, P)
        except:
            rho_l = 850.0
            rho_g = 50.0
            mu_l = 1.5e-4
            mu_g = 1.5e-5
        
        # Velocity
        rho_mix = hem_density(x, rho_l, rho_g)
        v_ms = mass_flow_kg_s / (A * rho_mix) if rho_mix > 0 else 0.0
        
        # Pressure drop in segment
        dp = beggs_brill_pressure_drop(x, rho_l, rho_g, mu_l, mu_g, D_m, v_ms, dz)
        
        # Update P
        P_kPa -= dp['total_Pa'] / 1000.0
        
        # Flashing: enthalpy drops as pressure drops
        # For adiabatic flow: h stays constant (first law)
        # But in reality, heat loss to formation occurs
        # Simplified: h constant (isenthalpic)
        
        profile.append({
            'depth_m': z,
            'P_kPa': P,
            'x': x,
            'regime': dp['regime'],
            'rho_mix': rho_mix,
            'v_ms': v_ms,
            'dP_kPa': dp['total_Pa'] / 1000.0,
        })
    
    return profile


if __name__ == '__main__':
    print("=" * 70)
    print("MULTIPHASE FLOW MODEL - DEMONSTRATION")
    print("=" * 70)
    
    # Soultz-like conditions
    x = 0.15  # 15% quality
    rho_l = 850.0
    rho_g = 50.0
    mu_l = 1.5e-4
    mu_g = 1.5e-5
    D = 0.2  # m
    v = 2.0  # m/s
    L = 5000  # m
    
    # Homogeneous model
    rho_mix = hem_density(x, rho_l, rho_g)
    print(f"\nHomogeneous Model:")
    print(f"  Quality: {x:.2f}")
    print(f"  Liquid density: {rho_l:.0f} kg/m³")
    print(f"  Gas density: {rho_g:.0f} kg/m³")
    print(f"  Mixture density: {rho_mix:.1f} kg/m³")
    print(f"  Slip ratio (HEM): 1.0 (by definition)")
    
    # Drift-flux
    v_g, alpha = drift_flux_velocity(x, rho_l, rho_g, v)
    K = slip_ratio(x, rho_l, rho_g, j_total=v)
    print(f"\nDrift-Flux Model (Zuber-Findlay):")
    print(f"  Gas velocity: {v_g:.2f} m/s")
    print(f"  Void fraction: {alpha:.3f}")
    print(f"  Slip ratio: {K:.2f}")
    
    # Pressure drop
    dp = beggs_brill_pressure_drop(x, rho_l, rho_g, mu_l, mu_g, D, v, L)
    print(f"\nBeggs-Brill Pressure Drop (vertical well, L={L} m):")
    print(f"  Regime: {dp['regime']}")
    print(f"  Reynolds: {dp['Re']:.0f}")
    print(f"  Friction factor: {dp['f']:.4f}")
    print(f"  Friction drop: {dp['friction_Pa']/1000:.1f} kPa")
    print(f"  Hydrostatic drop: {dp['hydrostatic_Pa']/1000:.1f} kPa")
    print(f"  Total drop: {dp['total_Pa']/1000:.1f} kPa")
    print(f"  = {dp['total_Pa']/1e6:.2f} MPa")
    
    print("\n" + "=" * 70)
