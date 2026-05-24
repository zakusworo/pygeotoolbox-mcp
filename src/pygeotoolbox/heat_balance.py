"""
Geothermal heat balance and energy calculations.

Inspired by pyResToolbox material balance concepts, reimplemented for geothermal.
"""
import numpy as np

def heat_in_reservoir(
    volume_m3: float,
    porosity: float,
    rho_rock_kg_m3: float,
    rho_water_kg_m3: float,
    T_C: float,
    cp_rock_J_kg_K: float = 800.0,
    cp_water_J_kg_K: float | None = None,
) -> float:
    """
    Total heat stored in reservoir (sensible heat) in MJ.
    H = (1-phi) * V * rho_r * c_pr * T + phi * V * rho_w * c_pw * T
    """
    if cp_water_J_kg_K is None:
        cp_water_J_kg_K = 4200.0
    T_K = T_C + 273.15
    rock_term = (1.0 - porosity) * volume_m3 * rho_rock_kg_m3 * cp_rock_J_kg_K * T_K
    water_term = porosity * volume_m3 * rho_water_kg_m3 * cp_water_J_kg_K * T_K
    total_J = rock_term + water_term
    return total_J / 1e6  # convert to MJ

def thermal_recovery_factor(
    T_initial_C: float,
    T_abandon_C: float,
    T_reinjection_C: float = 0.0,
    sweep_efficiency: float = 0.3,
) -> float:
    """
    Geothermal thermal recovery factor.
    R_th = sweep_efficiency * (T_initial - T_abandon) / (T_initial - T_reinjection).
    Typical sweep_efficiency = 0.2-0.4.
    Returns fraction (0-1).
    """
    denom = T_initial_C - T_reinjection_C
    if denom <= 0:
        return 0.0
    return sweep_efficiency * (T_initial_C - T_abandon_C) / denom

def power_output_from_mass_flow(
    mass_flow_kg_s: float,
    h_in_kJ_kg: float,
    h_out_kJ_kg: float,
    efficiency: float = 0.12,
) -> float:
    """
    Gross power output from brine enthalpy drop.
    W = m_dot * (h_in - h_out) * eta
    Returns power in MW.
    """
    delta_h_kJ_kg = h_in_kJ_kg - h_out_kJ_kg
    if delta_h_kJ_kg <= 0:
        return 0.0
    W_MW = mass_flow_kg_s * delta_h_kJ_kg * efficiency / 1e3
    return W_MW

def net_present_value_geothermal(
    annual_energy_MWh: list,
    electricity_price_per_MWh: float,
    opex_per_MWh: float,
    capex_MUSD: float,
    discount_rate: float = 0.08,
) -> dict:
    """
    Simple NPV for geothermal project.
    Returns dict with NPV, IRR, LCOE approximations.
    """
    n_years = len(annual_energy_MWh)
    cash_flows = []
    for i, E in enumerate(annual_energy_MWh):
        revenue = E * electricity_price_per_MWh
        opex = E * opex_per_MWh
        cf = (revenue - opex) / 1e6  # convert to MUSD
        cash_flows.append(cf / ((1 + discount_rate) ** (i + 1)))
    npv = sum(cash_flows) - capex_MUSD
    total_energy_MWh = sum(annual_energy_MWh)
    lcoe = (capex_MUSD * 1e6 + sum([E * opex_per_MWh for E in annual_energy_MWh])) / total_energy_MWh if total_energy_MWh > 0 else float('inf')
    return {
        "NPV_MUSD": npv,
        "LCOE_USD_MWh": lcoe,
        "payback_years": n_years if npv > 0 else None,
    }
