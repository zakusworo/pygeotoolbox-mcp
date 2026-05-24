"""
Parasitic load accounting for geothermal power plants.

Models all auxiliary power consumers to compute NET power from GROSS power.
Author: Zulfikar Aji Kusworo, 2026
"""
import numpy as np

def parasitic_loads(
    gross_power_MW: float,
    m_steam_kg_s: float,
    m_brine_kg_s: float,
    cooling_type: str = 'air',  # 'air' or 'water'
    has_ncg: bool = True,
    has_reinjection_pumps: bool = True,
    has_cooling_tower_fans: bool = True,
    has_working_fluid_pump: bool = True,
    has_control_systems: bool = True,
) -> dict:
    """
    Compute all parasitic loads as fractions of gross power.
    
    Based on DiPippo [2016] and typical geothermal plant data:
    - Cooling: 2-5% (air-cooled higher than water)
    - NCG compression: 3-8% (if present)
    - Reinjection pumps: 1-3%
    - Working fluid pump (binary): 0.5-1%
    - Controls/misc: 0.5-1%
    """
    loads = {}
    
    # Cooling system
    if cooling_type == 'air':
        loads['cooling'] = gross_power_MW * 0.04  # 4% for air-cooled
    else:
        loads['cooling'] = gross_power_MW * 0.02  # 2% for water-cooled
    
    # NCG compression
    if has_ncg:
        # Scale with steam flow and NCG fraction
        ncg_fraction = 0.025  # typical 2.5% NCG
        loads['ncg_compression'] = gross_power_MW * 0.05 * (ncg_fraction / 0.02)
    else:
        loads['ncg_compression'] = 0.0
    
    # Reinjection pumps
    if has_reinjection_pumps:
        # Pump brine from condenser pressure to reservoir pressure
        # Power ~ m_dot * g * h / efficiency
        # h ~ 1000-3000 m, efficiency ~ 0.7
        h_lift_m = 2000  # typical
        eta_pump = 0.7
        g = 9.81
        rho_brine = 1000  # kg/m³
        
        # P = m_dot * g * h / (eta * 1e6)  # MW
        pump_power = m_brine_kg_s * g * h_lift_m / (eta_pump * 1e6)
        loads['reinjection_pumps'] = pump_power
    else:
        loads['reinjection_pumps'] = 0.0
    
    # Working fluid pump (binary only)
    if has_working_fluid_pump:
        # Small fraction for circulating working fluid
        loads['working_fluid_pump'] = gross_power_MW * 0.005
    else:
        loads['working_fluid_pump'] = 0.0
    
    # Control systems
    if has_control_systems:
        loads['controls'] = gross_power_MW * 0.005
    else:
        loads['controls'] = 0.0
    
    # Total parasitic
    total_parasitic_MW = sum(loads.values())
    net_power_MW = gross_power_MW - total_parasitic_MW
    parasitic_fraction = total_parasitic_MW / gross_power_MW * 100 if gross_power_MW > 0 else 0
    
    return {
        'gross_power_MW': gross_power_MW,
        'net_power_MW': net_power_MW,
        'total_parasitic_MW': total_parasitic_MW,
        'parasitic_fraction_percent': parasitic_fraction,
        'by_component': loads,
    }

def net_power_from_gross(
    gross_power_MW: float,
    plant_type: str = 'flash',  # 'flash', 'binary', 'egs'
    m_steam_kg_s: float = 100.0,
    m_brine_kg_s: float = 200.0,
    ncg_fraction: float = 0.0,
    cooling_type: str = 'air',
) -> dict:
    """
    Quick estimate of net power from gross power and plant type.
    
    Typical parasitic fractions:
    - Flash plant: 10-15% (cooling + NCG + reinjection)
    - Binary plant: 8-12% (cooling + working fluid pump)
    - EGS: 20-30% (injection pumps + cooling)
    """
    if plant_type == 'flash':
        parasitic_frac = 0.12 + ncg_fraction * 2.0  # NCG adds significantly
    elif plant_type == 'binary':
        parasitic_frac = 0.10
    elif plant_type == 'egs':
        parasitic_frac = 0.25
    else:
        parasitic_frac = 0.15
    
    total_parasitic_MW = gross_power_MW * parasitic_frac
    net_power_MW = gross_power_MW - total_parasitic_MW
    
    return {
        'gross_power_MW': gross_power_MW,
        'net_power_MW': net_power_MW,
        'parasitic_MW': total_parasitic_MW,
        'parasitic_fraction': parasitic_frac,
        'plant_type': plant_type,
    }


if __name__ == '__main__':
    print("=" * 70)
    print("PARASITIC LOADS - DEMONSTRATION")
    print("=" * 70)
    
    # Hellisheidi-like flash plant
    gross = 303  # MW
    m_steam = 100  # kg/s
    m_brine = 300  # kg/s
    
    result = parasitic_loads(gross, m_steam, m_brine, cooling_type='air', has_ncg=False)
    
    print(f"\nFlash Plant (Hellisheidi-like, air-cooled):")
    print(f"  Gross power: {gross} MW")
    print(f"  Net power: {result['net_power_MW']:.1f} MW")
    print(f"  Parasitic: {result['parasitic_fraction_percent']:.1f}%")
    print(f"  Breakdown:")
    for comp, val in result['by_component'].items():
        print(f"    {comp}: {val:.1f} MW")
    
    # Wairakei with NCG
    result2 = parasitic_loads(161, 150, 200, cooling_type='water', has_ncg=True)
    print(f"\nFlash Plant (Wairakei-like, water-cooled, with NCG):")
    print(f"  Gross power: 161 MW")
    print(f"  Net power: {result2['net_power_MW']:.1f} MW")
    print(f"  Parasitic: {result2['parasitic_fraction_percent']:.1f}%")
    
    # Quick estimate
    quick = net_power_from_gross(60, 'binary', ncg_fraction=0.0)
    print(f"\nBinary Plant (Krafla-like):")
    print(f"  Gross: 60 MW → Net: {quick['net_power_MW']:.1f} MW")
    print(f"  Parasitic fraction: {quick['parasitic_fraction']:.1%}")
    
    print("\n" + "=" * 70)
