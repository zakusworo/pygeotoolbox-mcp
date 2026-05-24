"""
Non-Condensable Gas (NCG) handling for geothermal power plants.

Models gas compression power and separation efficiency for common
geothermal NCG species: CO2, H2S, CH4, NH3.

Author: Zulfikar Aji Kusworo, 2026
"""
import numpy as np

# NCG properties (molar masses, typical concentrations)
NCG_SPECIES = {
    'CO2': {'M_g_mol': 44.01, 'wt_fraction': 0.02, 'gamma': 1.3, 'compressor_eff': 0.75},
    'H2S': {'M_g_mol': 34.08, 'wt_fraction': 0.005, 'gamma': 1.32, 'compressor_eff': 0.75},
    'CH4': {'M_g_mol': 16.04, 'wt_fraction': 0.001, 'gamma': 1.31, 'compressor_eff': 0.75},
    'NH3': {'M_g_mol': 17.03, 'wt_fraction': 0.0005, 'gamma': 1.4, 'compressor_eff': 0.75},
}

def ncg_mass_fraction(species_dict: dict = None) -> float:
    """Total NCG mass fraction from species composition."""
    if species_dict is None:
        species_dict = NCG_SPECIES
    return sum(s['wt_fraction'] for s in species_dict.values())

def compressor_power_mw(
    m_gas_kg_s: float,
    P_in_kPa: float,
    P_out_kPa: float,
    T_in_K: float,
    gamma: float = 1.3,
    eta_comp: float = 0.75,
    R: float = 8.314,
) -> float:
    """
    Isentropic compression power for NCG removal.
    
    P_out/P_in = (n stages) for typical geothermal gas compressors.
    
    Returns power in MW.
    """
    if P_out_kPa <= P_in_kPa or m_gas_kg_s <= 0:
        return 0.0
    
    # Isentropic work per kg
    ratio = P_out_kPa / P_in_kPa
    n = (gamma - 1) / gamma
    
    # w_isen = (gamma / (gamma - 1)) * R_specific * T_in * (ratio^n - 1)
    # For simplicity, use average molecular mass ~44 g/mol (CO2-dominated)
    M_avg = 0.044  # kg/mol
    R_specific = R / M_avg  # J/kg/K
    
    w_isen = (gamma / (gamma - 1)) * R_specific * T_in_K * (ratio ** n - 1)
    w_actual = w_isen / eta_comp
    
    # Power = m_dot * w_actual
    power_MW = m_gas_kg_s * w_actual / 1e6
    return power_MW

def ncg_removal_system(
    m_total_kg_s: float,
    ncg_fraction: float,
    P_condenser_kPa: float,
    P_discharge_kPa: float = 300.0,  # Typical discharge pressure
    T_condenser_C: float = 40.0,
    species: str = 'CO2',
) -> dict:
    """
    Model NCG removal system (gas compressor after condenser).
    
    Typical: condenser at 40°C, 7-15 kPa → compress to 300 kPa for discharge.
    
    Returns dict with gas flow, compressor power, and net penalty.
    """
    m_gas_kg_s = m_total_kg_s * ncg_fraction
    T_in_K = T_condenser_C + 273.15
    
    # Compression ratio
    ratio = P_discharge_kPa / P_condenser_kPa
    
    # Power
    gamma = NCG_SPECIES.get(species, NCG_SPECIES['CO2'])['gamma']
    eta = NCG_SPECIES.get(species, NCG_SPECIES['CO2'])['compressor_eff']
    
    power_MW = compressor_power_mw(m_gas_kg_s, P_condenser_kPa, P_discharge_kPa, T_in_K, gamma, eta)
    
    # Net penalty = compressor power / gross power
    # Assume gross power ~ 100 MW per 100 kg/s steam for scaling
    gross_power_MW = m_total_kg_s * 0.5  # rough scaling
    penalty_percent = power_MW / gross_power_MW * 100 if gross_power_MW > 0 else 0
    
    return {
        'm_gas_kg_s': m_gas_kg_s,
        'compressor_power_MW': power_MW,
        'gross_power_MW': gross_power_MW,
        'penalty_percent': penalty_percent,
        'compression_ratio': ratio,
        'species': species,
    }

def total_ncg_penalty(
    m_steam_kg_s: float,
    ncg_species_dict: dict = None,
    P_condenser_kPa: float = 10.0,
    P_discharge_kPa: float = 300.0,
    T_condenser_C: float = 40.0,
) -> dict:
    """
    Compute total NCG penalty from all species.
    
    Returns total compressor power and percentage of gross power lost.
    """
    if ncg_species_dict is None:
        ncg_species_dict = NCG_SPECIES
    
    total_power_MW = 0.0
    total_gas_kg_s = 0.0
    
    results_by_species = {}
    
    for species, props in ncg_species_dict.items():
        result = ncg_removal_system(
            m_steam_kg_s,
            props['wt_fraction'],
            P_condenser_kPa,
            P_discharge_kPa,
            T_condenser_C,
            species,
        )
        results_by_species[species] = result
        total_power_MW += result['compressor_power_MW']
        total_gas_kg_s += result['m_gas_kg_s']
    
    # Total penalty
    gross_power_MW = m_steam_kg_s * 0.5  # rough
    total_penalty_percent = total_power_MW / gross_power_MW * 100 if gross_power_MW > 0 else 0
    
    return {
        'total_compressor_power_MW': total_power_MW,
        'total_gas_flow_kg_s': total_gas_kg_s,
        'gross_power_MW': gross_power_MW,
        'total_penalty_percent': total_penalty_percent,
        'by_species': results_by_species,
    }


if __name__ == '__main__':
    print("=" * 70)
    print("NCG REMOVAL SYSTEM - DEMONSTRATION")
    print("=" * 70)
    
    # Wairakei-like conditions
    m_steam = 100  # kg/s
    
    print(f"\nWairakei-like conditions:")
    print(f"  Steam flow: {m_steam} kg/s")
    print(f"  NCG species: CO2 dominant (~2% wt)")
    
    result = total_ncg_penalty(m_steam)
    
    print(f"\nTotal NCG Penalty:")
    print(f"  Total gas flow: {result['total_gas_flow_kg_s']:.2f} kg/s")
    print(f"  Total compressor power: {result['total_compressor_power_MW']:.2f} MW")
    print(f"  Gross power (estimated): {result['gross_power_MW']:.1f} MW")
    print(f"  Penalty: {result['total_penalty_percent']:.1f}% of gross")
    
    print(f"\nBy Species:")
    for species, res in result['by_species'].items():
        print(f"  {species}: {res['compressor_power_MW']:.2f} MW ({res['m_gas_kg_s']:.2f} kg/s)")
    
    # Compare with published data
    print(f"\nPublished NCG penalty for Wairakei: ~5-10%")
    print(f"Calculated NCG penalty: {result['total_penalty_percent']:.1f}%")
    
    print("\n" + "=" * 70)
