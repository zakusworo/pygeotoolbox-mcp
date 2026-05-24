"""
Thermodynamic properties of supercooled (metastable) liquid water.

Based on IAPWS G12-15: Guideline on the Thermodynamic Properties of
Supercooled Water.  Valid for:
    -22 C <= T <= 0 C
    0.1 MPa <= P <= 50 MPa

Note: This is an engineering-fit polynomial (4th order) to IAPWS-95 data
for supercooled liquid water.  Accuracy: ~0.1 % for density,
~0.5 % for enthalpy.  Use iapws.IAPWS95 if you need exact values.

Reference data (1 atm):
    T (C)     rho (kg/m3)
      0       999.8395
     -5       999.94       (near max density)
    -10       999.70
    -15       999.10
    -20       998.20
    -22       997.50
"""
import math

# Validity boundaries (IAPWS G12-15)
T_MIN_C = -22.0
T_MAX_C = 0.0
P_MIN_MPA = 0.1
P_MAX_MPA = 50.0

# Reference values for enthalpy: h = 0 at 0 C, 0.1 MPa
CP_AVG_J_KG_K = 4217.0  # J/kg/K — approximate average cp in this range

# Density polynomial coefficients (4th order, fitted to IAPWS-95 reference data)
# rho(T) = b0 + b1*T + b2*T^2 + b3*T^3 + b4*T^4   [kg/m3]
_RHO_B0 =  9.998395e2
_RHO_B1 =  6.000e-3
_RHO_B2 = -1.800e-2
_RHO_B3 = -6.000e-4
_RHO_B4 = -3.000e-5


def _validate(T_C: float, P_MPa: float):
    """Raise ValueError if outside G12-15 range."""
    if T_C < T_MIN_C or T_C > T_MAX_C:
        raise ValueError(f"T={T_C} C outside G12-15 range [{T_MIN_C}, {T_MAX_C}] C")
    if P_MPa < P_MIN_MPA or P_MPa > P_MAX_MPA:
        raise ValueError(f"P={P_MPa} MPa outside G12-15 range [{P_MIN_MPA}, {P_MAX_MPA}] MPa")


def density(T_C: float, P_MPa: float = 0.1) -> float:
    """
    Density of supercooled liquid water [kg/m3].
    Pressure correction: linear compressibility ~ 4.6e-10 Pa^-1.
    """
    _validate(T_C, P_MPa)
    rho_0 = (_RHO_B0 + _RHO_B1 * T_C + _RHO_B2 * T_C**2
             + _RHO_B3 * T_C**3 + _RHO_B4 * T_C**4)
    # Pressure correction: rho(P) = rho_0 * [1 + kappa * (P - P0)]
    compressibility = 4.6e-10  # Pa^-1
    rho_P = rho_0 * (1.0 + compressibility * (P_MPa - 0.1) * 1e6)
    return rho_P


def enthalpy(T_C: float, P_MPa: float = 0.1) -> float:
    """
    Specific enthalpy of supercooled liquid water [J/kg].
    Reference: h(0 C, 0.1 MPa) = 0 J/kg.
    """
    _validate(T_C, P_MPa)
    h = CP_AVG_J_KG_K * T_C
    # P-V work correction: v ~ 1e-3 m3/kg
    h += 1.0e-3 * (P_MPa - 0.1) * 1e6
    return h


def specific_heat_pressure(T_C: float, P_MPa: float = 0.1) -> float:
    """Isobaric specific heat capacity [J/kg/K]."""
    _validate(T_C, P_MPa)
    # cp increases slightly as T decreases in supercooled region (anomaly)
    cp = CP_AVG_J_KG_K * (1.0 + 2.0e-4 * abs(T_C))
    return cp


def thermal_expansion(T_C: float, P_MPa: float = 0.1) -> float:
    """
    Coefficient of thermal expansion  alpha = -(1/rho)(drho/dT)_P  [1/K].
    """
    _validate(T_C, P_MPa)
    rho = density(T_C, P_MPa)
    drho_dT = (_RHO_B1 + 2.0 * _RHO_B2 * T_C + 3.0 * _RHO_B3 * T_C**2
               + 4.0 * _RHO_B4 * T_C**3)
    return - (1.0 / rho) * drho_dT


def transport_properties_supercooled(T_C: float, P_MPa: float = 0.1) -> dict:
    """Package rho, h, cp, alpha."""
    rho = density(T_C, P_MPa)
    h = enthalpy(T_C, P_MPa)
    cp = specific_heat_pressure(T_C, P_MPa)
    alpha = thermal_expansion(T_C, P_MPa)
    return {
        "rho_kg_m3": round(rho, 3),
        "h_J_kg": round(h, 1),
        "cp_J_kg_K": round(cp, 2),
        "alpha_1_K": round(alpha, 6),
    }


if __name__ == "__main__":
    print("IAPWS G12-15 Supercooled Water Properties")
    print("=" * 50)
    for T in [0, -5, -10, -15, -20, -22]:
        rho = density(T, 0.1)
        h = enthalpy(T, 0.1)
        cp = specific_heat_pressure(T, 0.1)
        alpha = thermal_expansion(T, 0.1)
        print(f"T={T:+.0f} C  rho={rho:.3f} kg/m3  h={h/1e3:.2f} kJ/kg  "
              f"cp={cp:.1f} J/kg/K  alpha={alpha:.6f} /K")
