"""
Seawater properties: density, surface tension, thermal conductivity.

Based on IAPWS Documents:
- G14-19: Guideline on the Surface Tension of Seawater
- IAPWS Release on Thermodynamic Properties of Seawater (density)
- Additional formulations for thermal conductivity of saline liquids.

Valid for T = -2 to 40 C, salinity S = 0 to 40 g/kg (psu).
All returned in SI units.
"""
import math

# --- Density of Seawater (IOC SCOR IAPSO formulation) ---

def _pure_water_density(T_C):
    """Pure water density kg/m3 (Poling approximation, 0-40 C)."""
    return 999.842594 + 6.793952e-2 * T_C - 9.095290e-3 * T_C**2 + 1.001685e-4 * T_C**3 - 1.120083e-6 * T_C**4 + 6.536332e-9 * T_C**5


def seawater_density(T_C: float, salinity_psu: float, P_MPa: float = 0.1) -> dict:
    """
    Seawater density in kg/m3 at T (C), salinity (psu), and optional P (MPa).
    Uses IOC SCOR IAPSO / Millero formula.
    Valid: T from -2 to 40 C, S from 0 to 40 psu.
    """
    if T_C < -2.0 or T_C > 40:
        return {"status": "error", "message": "T must be -2 to 40 C"}
    if salinity_psu < 0 or salinity_psu > 40:
        return {"status": "error", "message": "Salinity must be 0 to 40 psu"}
    
    T = T_C
    S = salinity_psu
    
    # Density of pure water (kg/m3) — Millero & Poisson (1981)
    rho0 = (999.842594
            + 6.793952e-2 * T
            - 9.095290e-3 * T**2
            + 1.001685e-4 * T**3
            - 1.120083e-6 * T**4
            + 6.536332e-9 * T**5)
    
    # Salinity corrections (kg/m3)
    A = 8.24493e-1 - 4.0899e-3 * T + 7.6438e-5 * T**2 - 8.2467e-7 * T**3 + 5.3875e-9 * T**4
    B = -5.72466e-3 + 1.0227e-4 * T - 1.6546e-6 * T**2
    C = 4.8314e-4
    
    rho_kg_m3 = rho0 + A * S + B * S**1.5 + C * S**2
    
    # Very approximate pressure correction (not critical for course, but present)
    # Compressibility factor: ~1 + P/2e3 for pressure in MPa
    if P_MPa != 0.1:
        # Simplified compressibility
        K = 2.2e9  # Pa, bulk modulus rough estimate
        P_Pa = P_MPa * 1e6
        rho_kg_m3 *= (1 + P_Pa / K)
    
    return {
        "status": "ok",
        "rho_kg_m3": round(rho_kg_m3, 3),
        "T_C": T_C,
        "salinity_psu": salinity_psu,
        "P_MPa": P_MPa,
    }


def seawater_surface_tension(T_C: float, salinity_psu: float = 35.0) -> dict:
    """
    Seawater surface tension in N/m at T (C) and salinity (psu).
    Based on IAPWS G14-19 formulation.
    Valid: T from -2 to 40 C, S from 0 to 42 psu.
    """
    if T_C < -2.0 or T_C > 40:
        return {"status": "error", "message": "T must be -2 to 40 C"}
    if salinity_psu < 0 or salinity_psu > 42:
        return {"status": "error", "message": "Salinity must be 0 to 42 psu"}
    
    T = T_C
    S = salinity_psu
    
    # Pure water surface tension (N/m) — IAPWS
    sigma_pure = 0.2358 * (1 - (T + 273.15) / 647.096)**1.256 * (1 - 0.625 * (1 - (T + 273.15) / 647.096))
    
    # Salinity correction (simple linear approximation from IAPWS G14-19)
    # d_sigma/dS ~ -1.5e-4 N/m per psu at 25 C
    delta = -1.5e-4 * S
    
    sigma = sigma_pure + delta
    if sigma < 0:
        sigma = 0.0
    
    return {
        "status": "ok",
        "sigma_N_m": round(sigma, 6),
        "T_C": T_C,
        "salinity_psu": salinity_psu,
    }


def seawater_thermal_conductivity(T_C: float, salinity_psu: float) -> dict:
    """
    Seawater thermal conductivity in W/(m·K).
    Approximate formulation: pure water k corrected for salinity.
    Valid: T from -2 to 40 C, S from 0 to 40 psu.
    """
    if T_C < -2.0 or T_C > 40:
        return {"status": "error", "message": "T must be -2 to 40 C"}
    if salinity_psu < 0 or salinity_psu > 40:
        return {"status": "error", "message": "Salinity must be 0 to 40 psu"}
    
    # Pure water thermal conductivity (simplified polynomial 0-40C)
    k_pure = 0.5715 + 1.75e-3 * T_C - 6.5e-6 * T_C**2
    
    # Salinity depression (~ -2% per 10 psu)
    k_sw = k_pure * (1 - 0.0016 * salinity_psu)
    
    return {
        "status": "ok",
        "k_W_mK": round(k_sw, 5),
        "T_C": T_C,
        "salinity_psu": salinity_psu,
    }


def seawater_properties(T_C: float, salinity_psu: float, P_MPa: float = 0.1) -> dict:
    """Complete seawater property package."""
    dens = seawater_density(T_C, salinity_psu, P_MPa)
    surf = seawater_surface_tension(T_C, salinity_psu)
    cond = seawater_thermal_conductivity(T_C, salinity_psu)
    
    pkg = {
        "T_C": T_C,
        "salinity_psu": salinity_psu,
        "P_MPa": P_MPa,
    }
    
    if dens.get("status") == "ok":
        pkg["rho_kg_m3"] = dens["rho_kg_m3"]
    if surf.get("status") == "ok":
        pkg["sigma_N_m"] = surf["sigma_N_m"]
    if cond.get("status") == "ok":
        pkg["k_W_mK"] = cond["k_W_mK"]
    pkg["status"] = "ok"
    
    return pkg


if __name__ == "__main__":
    print("Seawater Density:")
    for T in [0, 10, 20, 25, 30]:
        print(f"  T={T}C S=35 -> {seawater_density(T, 35)}")
    print("\nSeawater Surface Tension:")
    for T in [0, 10, 20, 25, 30]:
        print(f"  T={T}C S=35 -> {seawater_surface_tension(T, 35)}")
    print("\nSeawater Thermal Conductivity:")
    for T in [0, 10, 20, 25, 30]:
        print(f"  T={T}C S=35 -> {seawater_thermal_conductivity(T, 35)}")
