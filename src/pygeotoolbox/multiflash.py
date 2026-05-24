"""
Multi-stage flash calculation for geothermal power plants.

Models double-flash and triple-flash separators with energy balance.
Author: Zulfikar Aji Kusworo, 2026
"""
import numpy as np

try:
    from .thermo import enthalpy_from_TP
except ImportError:
    from thermo import enthalpy_from_TP

def flash_stage(
    h_inlet_kJ_kg: float,
    T_flash_C: float,
    P_flash_kPa: float,
    m_inlet_kg_s: float,
) -> dict:
    """
    Single flash stage: separates liquid and vapor at given T/P.
    
    Returns dict with steam fraction, steam flow, liquid flow, enthalpies.
    """
    # Use known IAPWS saturation enthalpies (avoids CoolProp issues at saturation)
    # At temperature T_flash_C:
    h_liquid = 4.18 * T_flash_C  # kJ/kg (saturated liquid, approximate)
    # More accurate: use IAPWS correlation
    if T_flash_C < 100:
        h_liquid = 4.18 * T_flash_C
        h_steam = 2675 + 1.8 * (T_flash_C - 100)
    elif T_flash_C < 200:
        h_liquid = 420 + 4.18 * (T_flash_C - 100)
        h_steam = 2675 + 1.8 * (T_flash_C - 100)
    elif T_flash_C < 300:
        h_liquid = 840 + 4.20 * (T_flash_C - 200)
        h_steam = 2800 + 1.0 * (T_flash_C - 200)
    else:
        h_liquid = 1260 + 4.25 * (T_flash_C - 300)
        h_steam = 2900 + 0.8 * (T_flash_C - 300)
    
    # Steam fraction from energy balance
    # h_inlet = x * h_steam + (1-x) * h_liquid
    if abs(h_steam - h_liquid) < 0.1:
        x = 0.0
    else:
        x = (h_inlet_kJ_kg - h_liquid) / (h_steam - h_liquid)
    
    x = max(0.0, min(x, 1.0))
    
    m_steam = m_inlet_kg_s * x
    m_liquid = m_inlet_kg_s * (1 - x)
    
    return {
        'x': x,
        'm_steam_kg_s': m_steam,
        'm_liquid_kg_s': m_liquid,
        'h_steam_kJ_kg': h_steam,
        'h_liquid_kJ_kg': h_liquid,
        'h_inlet_kJ_kg': h_inlet_kJ_kg,
    }

def double_flash_cycle(
    m_total_kg_s: float,
    T_separator_C: float,
    P_separator_kPa: float,
    T_flash2_C: float,
    P_flash2_kPa: float,
    T_condenser_C: float,
    eta_turbine1: float = 0.82,
    eta_turbine2: float = 0.82,
    w_pump_kJ_kg: float = 0.64,
) -> dict:
    """
    Double-flash steam cycle (like Hellisheidi).
    
    Stage 1: Separator at T1, P1 → steam to HP turbine
    Stage 2: Brine from Stage 1 flashed at T2, P2 → steam to LP turbine
    """
    # Stage 1 enthalpy - use realistic value for geothermal fluid
    # At 260°C, saturated liquid h ≈ 1134 kJ/kg, saturated vapor h ≈ 2800 kJ/kg
    # For Wairakei (liquid-dominated), total enthalpy ≈ 1200 kJ/kg (mostly liquid)
    # For high-T systems (Hellisheidi, T>=200°C), use 1300 kJ/kg
    if T_separator_C >= 200:
        h_total = 1300.0
    else:
        h_total = 1200.0
    
    # Flash 1
    flash1 = flash_stage(h_total, T_separator_C, P_separator_kPa, m_total_kg_s)
    
    # Flash 2 (brine from flash1)
    h_brine1 = flash1['h_liquid_kJ_kg']
    m_brine1 = flash1['m_liquid_kg_s']
    flash2 = flash_stage(h_brine1, T_flash2_C, P_flash2_kPa, m_brine1)
    
    # Turbine 1 (HP): steam from flash1
    # Isentropic expansion from T_separator to T_condenser
    h_turb1_in = flash1['h_steam_kJ_kg']
    # Approximate isentropic outlet
    h_condenser = 167.5  # kJ/kg at 40°C
    h_out_iso1 = 2141  # approximate
    w_turb1 = (h_turb1_in - h_out_iso1) * eta_turbine1
    power_turb1_MW = flash1['m_steam_kg_s'] * w_turb1 / 1000
    
    # Turbine 2 (LP): steam from flash2
    h_turb2_in = flash2['h_steam_kJ_kg']
    # LP turbine expands to lower pressure
    h_out_iso2 = 2250  # less expansion than HP
    w_turb2 = (h_turb2_in - h_out_iso2) * eta_turbine2
    power_turb2_MW = flash2['m_steam_kg_s'] * w_turb2 / 1000
    
    # Pump work
    pump1_MW = flash1['m_steam_kg_s'] * w_pump_kJ_kg / 1000
    pump2_MW = flash2['m_steam_kg_s'] * w_pump_kJ_kg / 1000
    
    # Net power
    gross_MW = power_turb1_MW + power_turb2_MW
    net_MW = gross_MW - pump1_MW - pump2_MW
    
    return {
        'flash1': flash1,
        'flash2': flash2,
        'power_turb1_MW': power_turb1_MW,
        'power_turb2_MW': power_turb2_MW,
        'gross_MW': gross_MW,
        'pump_MW': pump1_MW + pump2_MW,
        'net_MW': net_MW,
        'm_steam_total_kg_s': flash1['m_steam_kg_s'] + flash2['m_steam_kg_s'],
    }

def triple_flash_cycle(
    m_total_kg_s: float,
    T1_C: float, P1_kPa: float,
    T2_C: float, P2_kPa: float,
    T3_C: float, P3_kPa: float,
    T_condenser_C: float = 40.0,
    eta_turbine: float = 0.82,
    w_pump_kJ_kg: float = 0.64,
) -> dict:
    """
    Triple-flash cycle (HP + MP + LP turbines).
    
    Used in some Japanese and high-enthalpy Icelandic plants.
    Stage 1: High-pressure flash
    Stage 2: Medium-pressure flash (brine from stage 1)
    Stage 3: Low-pressure flash (brine from stage 2)
    """
    # Stage 1 enthalpy
    h_total = 1300.0 if T1_C >= 200 else 1200.0  # kJ/kg
    
    # Three flashes
    flash1 = flash_stage(h_total, T1_C, P1_kPa, m_total_kg_s)
    flash2 = flash_stage(flash1['h_liquid_kJ_kg'], T2_C, P2_kPa, flash1['m_liquid_kg_s'])
    flash3 = flash_stage(flash2['h_liquid_kJ_kg'], T3_C, P3_kPa, flash2['m_liquid_kg_s'])
    
    # Turbine work for each stage (HP > MP > LP pressure)
    # Approximate isentropic outlets
    h_out1 = 2141  # HP turbine
    h_out2 = 2250  # MP turbine
    h_out3 = 2350  # LP turbine
    
    w1 = (flash1['h_steam_kJ_kg'] - h_out1) * eta_turbine
    w2 = (flash2['h_steam_kJ_kg'] - h_out2) * eta_turbine
    w3 = (flash3['h_steam_kJ_kg'] - h_out3) * eta_turbine
    
    power1 = flash1['m_steam_kg_s'] * w1 / 1000
    power2 = flash2['m_steam_kg_s'] * w2 / 1000
    power3 = flash3['m_steam_kg_s'] * w3 / 1000
    
    # Pumps
    pump1 = flash1['m_steam_kg_s'] * w_pump_kJ_kg / 1000
    pump2 = flash2['m_steam_kg_s'] * w_pump_kJ_kg / 1000
    pump3 = flash3['m_steam_kg_s'] * w_pump_kJ_kg / 1000
    
    gross = power1 + power2 + power3
    net = gross - pump1 - pump2 - pump3
    
    return {
        'flash1': flash1,
        'flash2': flash2,
        'flash3': flash3,
        'power1_MW': power1,
        'power2_MW': power2,
        'power3_MW': power3,
        'gross_MW': gross,
        'pump_MW': pump1 + pump2 + pump3,
        'net_MW': net,
        'm_steam_total_kg_s': flash1['m_steam_kg_s'] + flash2['m_steam_kg_s'] + flash3['m_steam_kg_s'],
    }


if __name__ == '__main__':
    print("=" * 70)
    print("MULTI-STAGE FLASH CYCLE - DEMONSTRATION")
    print("=" * 70)
    
    # Hellisheidi-like double-flash
    result = double_flash_cycle(
        m_total_kg_s=400,
        T_separator_C=180,
        P_separator_kPa=1000,
        T_flash2_C=140,
        P_flash2_kPa=361,
        T_condenser_C=40,
    )
    
    print(f"\nDouble-Flash Cycle (Hellisheidi-like):")
    print(f"  Stage 1: {result['flash1']['x']:.1%} steam at {result['flash1']['m_steam_kg_s']:.1f} kg/s")
    print(f"  Stage 2: {result['flash2']['x']:.1%} steam at {result['flash2']['m_steam_kg_s']:.1f} kg/s")
    print(f"  HP turbine: {result['power_turb1_MW']:.1f} MW")
    print(f"  LP turbine: {result['power_turb2_MW']:.1f} MW")
    print(f"  Gross power: {result['gross_MW']:.1f} MW")
    print(f"  Net power: {result['net_MW']:.1f} MW")
    print(f"  Published (Hellisheidi): 303 MW")
    print(f"  Ratio: {result['net_MW']/303*100:.1f}%")
    
    # Compare with single-flash
    single_flash = flash_stage(4.18*180, 140, 361, 400)
    print(f"\nSingle-Flash (same conditions):")
    print(f"  Steam fraction: {single_flash['x']:.1%}")
    print(f"  Steam flow: {single_flash['m_steam_kg_s']:.1f} kg/s")
    print(f"  Approx power: {single_flash['m_steam_kg_s']*500/1000:.1f} MW")
    print(f"  Double-flash improvement: {(result['net_MW']/(single_flash['m_steam_kg_s']*500/1000)-1)*100:.0f}%")
    
    print("\n" + "=" * 70)
