"""
Working fluid properties for ORC binary cycle calculations.

Uses CoolProp when available, falls back to polynomial fits for:
- R134a (most common geothermal ORC working fluid)
- Isobutane (R600a) - high-temperature ORC
- Propane (R290) - low-temperature ORC
- Ammonia (R717) - high efficiency, toxic

Author: Zulfikar Aji Kusworo, 2026
"""
import numpy as np

try:
    from CoolProp.CoolProp import PropsSI
    HAS_COOLPROP = True
except ImportError:
    HAS_COOLPROP = False

# Working fluid polynomial coefficients (simplified fits)
# h(T) = a0 + a1*T + a2*T^2 + a3*T^3 [kJ/kg, T in °C]
# Valid for saturated liquid and vapor

FLUID_FITS = {
    'R134a': {
        'h_f': [200.0, 1.20, 0.001, 0.0],      # saturated liquid
        'h_g': [380.0, 0.80, -0.001, 0.0],      # saturated vapor
        'T_critical_C': 101.1,
        'T_min_C': -26.0,
        'P_critical_MPa': 4.06,
    },
    'R600a': {
        'h_f': [150.0, 1.80, 0.001, 0.0],
        'h_g': [420.0, 0.60, -0.001, 0.0],
        'T_critical_C': 134.7,
        'T_min_C': -11.7,
        'P_critical_MPa': 3.64,
    },
    'R290': {
        'h_f': [100.0, 2.00, 0.001, 0.0],
        'h_g': [400.0, 0.70, -0.001, 0.0],
        'T_critical_C': 96.7,
        'T_min_C': -42.0,
        'P_critical_MPa': 4.25,
    },
    'R717': {
        'h_f': [200.0, 4.80, 0.001, 0.0],
        'h_g': [1300.0, 1.50, -0.001, 0.0],
        'T_critical_C': 132.4,
        'T_min_C': -33.3,
        'P_critical_MPa': 11.3,
    },
}

def enthalpy_sat_liquid(T_C: float, fluid: str = 'R134a', method: str = 'auto') -> float:
    """Saturated liquid enthalpy [kJ/kg]."""
    if method == 'auto' and HAS_COOLPROP:
        try:
            return PropsSI('H', 'T', T_C + 273.15, 'Q', 0.0, fluid) / 1000.0
        except:
            pass
    
    # Fallback to polynomial
    coeffs = FLUID_FITS[fluid]['h_f']
    h = coeffs[0] + coeffs[1]*T_C + coeffs[2]*T_C**2 + coeffs[3]*T_C**3
    return h

def enthalpy_sat_vapor(T_C: float, fluid: str = 'R134a', method: str = 'auto') -> float:
    """Saturated vapor enthalpy [kJ/kg]."""
    if method == 'auto' and HAS_COOLPROP:
        try:
            return PropsSI('H', 'T', T_C + 273.15, 'Q', 1.0, fluid) / 1000.0
        except:
            pass
    
    coeffs = FLUID_FITS[fluid]['h_g']
    h = coeffs[0] + coeffs[1]*T_C + coeffs[2]*T_C**2 + coeffs[3]*T_C**3
    return h

def entropy_sat_liquid(T_C: float, fluid: str = 'R134a', method: str = 'auto') -> float:
    """Saturated liquid entropy [kJ/kg/K]."""
    if method == 'auto' and HAS_COOLPROP:
        try:
            return PropsSI('S', 'T', T_C + 273.15, 'Q', 0.0, fluid) / 1000.0
        except:
            pass
    
    # Approximate from h and T
    h = enthalpy_sat_liquid(T_C, fluid, 'poly')
    # s ≈ h/T for rough estimate
    return h / (T_C + 273.15)

def entropy_sat_vapor(T_C: float, fluid: str = 'R134a', method: str = 'auto') -> float:
    """Saturated vapor entropy [kJ/kg/K]."""
    if method == 'auto' and HAS_COOLPROP:
        try:
            return PropsSI('S', 'T', T_C + 273.15, 'Q', 1.0, fluid) / 1000.0
        except:
            pass
    
    h = enthalpy_sat_vapor(T_C, fluid, 'poly')
    return h / (T_C + 273.15)

def critical_temperature_C(fluid: str = 'R134a') -> float:
    """Critical temperature [°C] of the working fluid (CoolProp, else fit table)."""
    if HAS_COOLPROP:
        try:
            return PropsSI('Tcrit', fluid) - 273.15
        except Exception:
            pass
    return FLUID_FITS.get(fluid, {}).get('T_critical_C', float('nan'))


def orc_cycle_efficiency(
    T_evap_C: float,
    T_cond_C: float,
    fluid: str = 'R134a',
    eta_turbine: float = 0.85,
    eta_pump: float = 0.75,
    method: str = 'auto',
) -> dict:
    """
    Compute subcritical ORC cycle efficiency using working-fluid properties.

    States: 1 = condenser liquid out / pump in, 2 = pump out, 3 = evaporator
    vapor out / turbine in, 4 = turbine out / condenser in.

    Physical guards (added v0.5.2):
    - Raises ValueError if T_evap_C >= critical temperature of the fluid; a
      subcritical ORC cannot evaporate the fluid above its critical point.
      (This previously caused CoolProp to fail silently and fall back to a
      crude polynomial for h3 only, mixing reference scales and producing
      eta_thermal > eta_carnot — a second-law violation.)
    - Uses ONE consistent property source for every state. If CoolProp is
      requested but cannot serve the requested states, all properties fall
      back to the polynomial fits together (never mixed).
    """
    Tcrit = critical_temperature_C(fluid)
    if T_cond_C >= T_evap_C:
        raise ValueError(
            f"T_cond_C ({T_cond_C}°C) must be below T_evap_C ({T_evap_C}°C)."
        )
    if Tcrit == Tcrit and T_evap_C >= Tcrit - 0.5:  # NaN-safe
        raise ValueError(
            f"T_evap_C={T_evap_C}°C is at/above the critical temperature of "
            f"{fluid} (Tcrit={Tcrit:.1f}°C). A subcritical ORC cannot evaporate "
            f"the working fluid above its critical point. Choose a lower "
            f"evaporator temperature or a fluid with a higher critical "
            f"temperature."
        )

    # --- Choose a single, consistent property source ---
    src = 'auto' if (method == 'auto' and HAS_COOLPROP) else 'poly'
    if src == 'auto':
        try:
            PropsSI('H', 'T', T_evap_C + 273.15, 'Q', 1.0, fluid)
            PropsSI('H', 'T', T_cond_C + 273.15, 'Q', 0.0, fluid)
        except Exception:
            src = 'poly'  # degrade ALL states together, never mix

    # State enthalpies / entropies (all from the same source)
    h1 = enthalpy_sat_liquid(T_cond_C, fluid, src)   # pump inlet
    h3 = enthalpy_sat_vapor(T_evap_C, fluid, src)    # turbine inlet
    s3 = entropy_sat_vapor(T_evap_C, fluid, src)

    # Isentropic turbine outlet at condenser pressure
    if src == 'auto':
        P_cond = PropsSI('P', 'T', T_cond_C + 273.15, 'Q', 0.0, fluid)
        try:
            h4_isen = PropsSI('H', 'P', P_cond, 'S', s3 * 1000.0, fluid) / 1000.0
        except Exception:
            h4_isen = h1
        P_evap = PropsSI('P', 'T', T_evap_C + 273.15, 'Q', 1.0, fluid)
        v_f = 1.0 / PropsSI('D', 'T', T_cond_C + 273.15, 'Q', 0.0, fluid)
        w_pump = v_f * (P_evap - P_cond) / eta_pump / 1000.0  # J -> kJ/kg
    else:
        # Polynomial path: wet-steam quality from entropy balance at condenser
        h4_liquid = enthalpy_sat_liquid(T_cond_C, fluid, src)
        h4_vapor = enthalpy_sat_vapor(T_cond_C, fluid, src)
        s4_liquid = entropy_sat_liquid(T_cond_C, fluid, src)
        s4_vapor = entropy_sat_vapor(T_cond_C, fluid, src)
        if abs(s4_vapor - s4_liquid) > 1e-6:
            x4 = max(0.0, min((s3 - s4_liquid) / (s4_vapor - s4_liquid), 1.0))
            h4_isen = h4_liquid + x4 * (h4_vapor - h4_liquid)
        else:
            h4_isen = h4_liquid
        v_f = 0.0008  # m³/kg approximate
        w_pump = v_f * 1000.0 / eta_pump  # crude fallback

    # Actual turbine outlet, works, heat input
    h4_actual = h3 - eta_turbine * (h3 - h4_isen)
    h2_actual = h1 + w_pump
    w_turbine = h3 - h4_actual
    w_net = w_turbine - w_pump
    q_in = h3 - h2_actual

    eta_thermal = w_net / q_in * 100 if q_in > 0 else 0.0

    # Carnot upper bound (cycle reference)
    T_hot_K = T_evap_C + 273.15
    T_cold_K = T_cond_C + 273.15
    eta_carnot = (1 - T_cold_K / T_hot_K) * 100

    # Second-law self-check (should always hold after the guards above)
    second_law_ok = eta_thermal <= eta_carnot + 1e-6

    return {
        'h1_kJ_kg': h1,
        'h2_kJ_kg': h2_actual,
        'h3_kJ_kg': h3,
        'h4_kJ_kg': h4_actual,
        'w_turbine_kJ_kg': w_turbine,
        'w_pump_kJ_kg': w_pump,
        'w_net_kJ_kg': w_net,
        'q_in_kJ_kg': q_in,
        'eta_thermal_percent': eta_thermal,
        'eta_carnot_percent': eta_carnot,
        'eta_ratio_percent': eta_thermal / eta_carnot * 100 if eta_carnot > 0 else 0,
        'second_law_ok': second_law_ok,
        'property_source': src,
        'T_critical_C': Tcrit,
        'fluid': fluid,
    }


def compare_fluids(
    T_evap_C: float = 165.0,
    T_cond_C: float = 35.0,
    fluids: list = None,
) -> dict:
    """Compare ORC efficiency for multiple working fluids."""
    if fluids is None:
        fluids = ['R134a', 'R600a', 'R290', 'R717']
    
    results = {}
    for fluid in fluids:
        try:
            results[fluid] = orc_cycle_efficiency(T_evap_C, T_cond_C, fluid)
        except Exception as e:
            results[fluid] = {'error': str(e)}
    
    return results


if __name__ == '__main__':
    print("=" * 70)
    print("WORKING FLUID PROPERTIES - DEMONSTRATION")
    print("=" * 70)
    
    # Krafla-like conditions
    T_evap = 165
    T_cond = 35
    
    print(f"\nORC Cycle at T_evap={T_evap}°C, T_cond={T_cond}°C")
    print(f"CoolProp available: {HAS_COOLPROP}")
    
    # Single fluid
    result = orc_cycle_efficiency(T_evap, T_cond, 'R134a')
    print(f"\nR134a Results:")
    print(f"  h_evap_in: {result['h1_kJ_kg']:.1f} kJ/kg")
    print(f"  h_evap_out: {result['h3_kJ_kg']:.1f} kJ/kg")
    print(f"  w_turbine: {result['w_turbine_kJ_kg']:.1f} kJ/kg")
    print(f"  w_pump: {result['w_pump_kJ_kg']:.1f} kJ/kg")
    print(f"  w_net: {result['w_net_kJ_kg']:.1f} kJ/kg")
    print(f"  η_thermal: {result['eta_thermal_percent']:.1f}%")
    print(f"  η_Carnot: {result['eta_carnot_percent']:.1f}%")
    print(f"  Ratio: {result['eta_ratio_percent']:.1f}%")
    
    # Compare all fluids
    print(f"\nComparison of Working Fluids:")
    comparison = compare_fluids(T_evap, T_cond)
    print(f"{'Fluid':<10} {'η_thermal':<12} {'w_net':<10} {'Status'}")
    print("-" * 50)
    for fluid, res in comparison.items():
        if 'error' in res:
            print(f"{fluid:<10} {'ERROR':<12} {'':<10} {res['error']}")
        else:
            print(f"{fluid:<10} {res['eta_thermal_percent']:<12.1f} {res['w_net_kJ_kg']:<10.1f} OK")
    
    print("\n" + "=" * 70)
