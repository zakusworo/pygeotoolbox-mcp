"""
Saturation properties for water/steam using IAPWS97.

Wrapper around iapws package for explicit saturation T(P) and P(T).
Valid from triple point (0.611657 kPa, 0.01 C) to critical point (22.064 MPa, 373.946 C).
"""
try:
    from iapws import IAPWS97
except ImportError:
    IAPWS97 = None


def ensure_iapws():
    if IAPWS97 is None:
        raise RuntimeError(
            "iapws package required. Install: pip install iapws"
        )


def saturation_temperature(P_kPa: float) -> float | None:
    """Saturation temperature in C for given pressure (kPa).
    Returns None if pressure is outside valid range.
    """
    ensure_iapws()
    P_MPa = P_kPa / 1000.0
    try:
        sat = IAPWS97(P=P_MPa, x=0)
        return float(sat.T - 273.15)
    except (ValueError, Exception):
        return None


def saturation_pressure(T_C: float) -> float | None:
    """Saturation pressure in kPa for given temperature (C).
    Returns None if temperature is outside valid range.
    """
    ensure_iapws()
    T_K = T_C + 273.15
    try:
        sat = IAPWS97(T=T_K, x=0)
        return float(sat.P * 1000.0)  # kPa
    except (ValueError, Exception):
        return None


def saturation_properties(P_kPa: float) -> dict:
    """Saturation properties at given pressure.
    Returns dict with T_sat_C, P_sat_kPa, phase, status.
    """
    T_sat = saturation_temperature(P_kPa)
    if T_sat is None:
        return {
            "T_sat_C": None, "P_sat_kPa": round(P_kPa, 6),
            "phase": "out_of_range", "status": "invalid"
        }
    return {
        "T_sat_C": round(T_sat, 6),
        "P_sat_kPa": round(P_kPa, 6),
        "phase": "saturated_vapor_liquid",
        "status": "valid"
    }


if __name__ == "__main__":
    test_cases = [
        (0.611657, 0.01),       # Triple point
        (101.325, 99.9743),     # 1 atm
        (1000.0, 179.8856),     # 1 MPa
        (10000.0, 310.9995),    # 10 MPa
        (22064.0, 373.946),     # Critical point
    ]
    for P_kPa, T_exp in test_cases:
        T_calc = saturation_temperature(P_kPa)
        status = "✅" if T_calc and abs(T_calc - T_exp) < 0.01 else "❌"
        print(f"{status} P={P_kPa:10.3f} kPa → T_sat={T_calc:.6f} C (expected {T_exp})")
    # Test reverse
    for T_C, P_exp in [(0.01, 0.611657), (99.9743, 101.325)]:
        P_calc = saturation_pressure(T_C)
        print(f"T={T_C} C → P_sat={P_calc:.6f} kPa (expected {P_exp})")
