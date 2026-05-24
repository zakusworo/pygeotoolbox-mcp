"""
Geophysical properties: electrical conductivity for brine monitoring.

Based on IAPWS Release on the Electrical Conductivity of Water and Steam.
For geothermal: used in resistivity tomography, salinity estimation, and
flow-path tracing.

Typical range:
- Pure water (25 C): ~5.5e-6 S/m
- Brine (~0.1 M NaCl, 25 C): ~1 S/m
- Geothermal brine (high salinity, high T): 1-100 S/m
"""
import math

# Standard molar conductivities at 25 C (S·cm2/mol)
LAMBDA_0_NA = 50.11
LAMBDA_0_CL = 76.35
LAMBDA_0_CA = 59.50
LAMBDA_0_HCO3 = 44.48


def pure_water_conductivity(T_C: float) -> float:
    """
    Pure water intrinsic conductivity S/m at T (C).
    Valid: 0 to 100 C.
    """
    # Temperature dependence: exponential Arrhenius-like
    T_K = T_C + 273.15
    # k = A * exp(-Ea / RT), fitted for ionic product of water
    A = 0.0055  # S/m
    Ea_R = 1800.0  # K
    return A * math.exp(-Ea_R / T_K)


def brine_electrical_conductivity(
    T_C: float,
    Na_mg_L: float = 0.0,
    Cl_mg_L: float = 0.0,
    Ca_mg_L: float = 0.0,
    HCO3_mg_L: float = 0.0,
    salinity_psu: float | None = None,
) -> dict:
    """
    Estimate brine bulk electrical conductivity S/m from ion concentrations.
    Uses individual ions if provided; falls back to salinity_psu approximation.
    Valid: 0 to 150 C.

    Args:
        T_C: Temperature in C
        Na_mg_L: Sodium concentration mg/L
        Cl_mg_L: Chloride concentration mg/L
        Ca_mg_L: Calcium concentration mg/L
        HCO3_mg_L: Bicarbonate concentration mg/L
        salinity_psu: Salinity in practical salinity units (alternative input)
    Returns:
        dict with conductivity_S_m, estimated ions, method, T_C
    """
    if T_C < 0 or T_C > 150:
        return {"status": "error", "message": "T must be 0 to 150 C"}
    
    # If salinity given instead of ions, estimate TDS & major ions
    method = "direct"
    if salinity_psu is not None and salinity_psu > 0:
        # Typical seawater ratios (mass)
        Na_mg_L = salinity_psu * 0.306  # ~10.8 g/kg Na
        Cl_mg_L = salinity_psu * 0.550   # ~19.4 g/kg Cl
        Ca_mg_L = salinity_psu * 0.012   # ~0.42 g/kg Ca
        HCO3_mg_L = salinity_psu * 0.0025
        method = "salinity_approximation"
    
    # Convert mg/L to mol/L (molarity)
    MW_NA = 22.99
    MW_CL = 35.45
    MW_CA = 40.08
    MW_HCO3 = 61.02
    
    c_Na = Na_mg_L / 1000.0 / MW_NA
    c_Cl = Cl_mg_L / 1000.0 / MW_CL
    c_Ca = Ca_mg_L / 1000.0 / MW_CA
    c_HCO3 = HCO3_mg_L / 1000.0 / MW_HCO3
    
    # Total concentration (for activity correction)
    c_total = c_Na + c_Cl + c_Ca + c_HCO3  # mol/L
    
    # Temperature-adjusted ionic conductivity (S·cm2/mol)
    # Kohlrausch law with temperature correction ~2%/C
    T_ref = 25.0
    temp_factor = 1.0 + 0.02 * (T_C - T_ref)
    
    lambda_Na = LAMBDA_0_NA * temp_factor
    lambda_Cl = LAMBDA_0_CL * temp_factor
    lambda_Ca = LAMBDA_0_CA * temp_factor
    lambda_HCO3 = LAMBDA_0_HCO3 * temp_factor
    
    # Kohlrausch: k = SUM(ci * lambdai)
    # ci dalam mol/L, lambdai dalam S·cm2/mol -> k dalam S/cm
    k_S_cm = (c_Na * lambda_Na + c_Cl * lambda_Cl + c_Ca * lambda_Ca + c_HCO3 * lambda_HCO3)
    
    # Convert S/cm -> S/m
    k_S_m = k_S_cm * 100.0
    
    # Add pure water background
    k_pure = pure_water_conductivity(T_C)
    k_total = k_S_m + k_pure
    
    return {
        "status": "ok",
        "conductivity_S_m": round(k_total, 6),
        "conductivity_mS_m": round(k_total * 1000, 3),
        "T_C": T_C,
        "method": method,
        "c_total_mol_L": round(c_total, 6),
        "estimated_ions": {
            "Na_mg_L": round(Na_mg_L, 3),
            "Cl_mg_L": round(Cl_mg_L, 3),
            "Ca_mg_L": round(Ca_mg_L, 3),
            "HCO3_mg_L": round(HCO3_mg_L, 3),
        } if method == "salinity_approximation" else None,
    }


def resistivity_from_conductivity(conductivity_S_m: float) -> float:
    """Convert conductivity S/m to resistivity ohm·m."""
    if conductivity_S_m <= 0:
        return float('inf')
    return 1.0 / conductivity_S_m


def salinity_from_resistivity(resistivity_ohm_m: float, T_C: float = 25.0) -> dict:
    """
    Estimate salinity from resistivity (inverse problem).
    Uses empirical relation: k ≈ 0.1 * S^0.9 at 25 C (S in psu, k in S/m).
    Very approximate — for order-of-magnitude only.
    """
    if resistivity_ohm_m <= 0:
        return {"status": "error", "message": "Resistivity must be > 0"}
    
    k_S_m = 1.0 / resistivity_ohm_m
    # Calibrate: at 35 psu, ~5 S/m at 25 C (highly variable)
    # Back-calculate: S ≈ (k / 0.14)^(1/0.9)
    S_est = (k_S_m / 0.14) ** (1.0 / 0.9)
    
    return {
        "status": "ok",
        "salinity_estimated_psu": round(min(S_est, 100), 2),
        "resistivity_ohm_m": round(resistivity_ohm_m, 4),
        "conductivity_S_m": round(k_S_m, 6),
        "T_C": T_C,
        "note": "Empirical approximation — use with caution",
    }


if __name__ == "__main__":
    # Quick sanity checks
    print("=== Brine Conductivity ===")
    for T in [25, 50, 100, 150]:
        r = brine_electrical_conductivity(T, Na_mg_L=10000, Cl_mg_L=15000, Ca_mg_L=500, HCO3_mg_L=200)
        print(f"T={T}C -> {r['conductivity_S_m']:.3f} S/m")
    
    print("\n=== Salinity Approximation ===")
    for S in [5, 15, 35, 40]:
        r = brine_electrical_conductivity(25, salinity_psu=S)
        print(f"S={S} psu -> {r['conductivity_S_m']:.3f} S/m")
    
    print("\n=== Resistivity Conversion ===")
    for k in [0.1, 1.0, 10.0, 50.0]:
        rho = resistivity_from_conductivity(k)
        print(f"k={k} S/m -> rho={rho:.4f} ohm·m")
    
    print("\n=== Salinity from Resistivity ===")
    for rho in [0.2, 1.0, 5.0, 20.0]:
        r = salinity_from_resistivity(rho, 25)
        print(f"rho={rho} ohm·m -> S~={r['salinity_estimated_psu']} psu")
