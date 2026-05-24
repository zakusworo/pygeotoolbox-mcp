"""Example: Geothermal brine power output calculation using pygeotoolbox."""
from pygeotoolbox import thermo, wellbore, heat_balance, sensitivity, scaling

print("=== Geothermal Toolbox Demo ===")

# Thermo properties
T_C = 200
P_kPa = 2000
h_kJ_kg = thermo.enthalpy_from_TP(T_C, P_kPa) / 1000.0
rho = thermo.density_from_TP(T_C, P_kPa)
phase = thermo.phase_from_TP(T_C, P_kPa)
print(f"T={T_C}C P={P_kPa}kPa -> h={h_kJ_kg:.1f} kJ/kg, rho={rho:.1f} kg/m3, phase={phase}")

# Saturation
Tsat = thermo.saturation_temperature(P_kPa)
if Tsat:
    print(f"Saturation temperature at {P_kPa}kPa = {Tsat:.1f}C")

# Wellbore operating point
q, P_wf, P_wh, _, _ = wellbore.operating_point(20000, 0.5, 900, 1200, 1500, 0.2, 0.02, 2.5)
print(f"Operating point: q={q:.1f} kg/s, P_wf={P_wf:.1f} kPa, P_wh={P_wh:.1f} kPa")

# Power output
W = heat_balance.power_output_from_mass_flow(q, 1200, 400, 0.12)
print(f"Gross power output: {W:.2f} MW")

# Scaling risk
CaCO3 = scaling.ryznar_index(T_C, 150, 250, 7.2)
SiO2 = scaling.sio2_scaling_risk(80, T_C)
print(f"CaCO3 RSI: {CaCO3:.2f} | SiO2 risk: {SiO2['risk']} (ratio={SiO2['ratio']:.2f})")

# Sensitivity
sweep = sensitivity.one_factor_sweep(
    lambda **kw: heat_balance.power_output_from_mass_flow(kw["m_dot"], 1200, 400, 0.12),
    "m_dot",
    [50, 100, 150, 200, 250],
    {"m_dot": 100, "h_in": 1200, "h_out": 400, "eta": 0.12},
)
print(f"Power sensitivity to mass flow: {[f'{x[0]:.0f}kg/s->{x[1]:.2f}MW' for x in sweep]}")
