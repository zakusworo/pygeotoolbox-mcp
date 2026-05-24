"""
MCP (Model Context Protocol) server for pygeotoolbox.

Inspired by gabrielserrao/pyrestoolbox-mcp.
Exposes geothermal engineering tools to Hermes Agent via STDIO transport.
"""
try:
    import fastmcp
    from fastmcp import FastMCP
except ImportError:
    raise RuntimeError("fastmcp not installed. Run: pip install fastmcp")

import math

from . import thermo
from . import transport
from . import seawater
from . import geophysics
from . import wellbore
from . import decline
from . import heat_balance
from . import sensitivity
from . import scaling
from . import siapws_saturation

mcp = FastMCP("pygeotoolbox-mcp")

# ---------------------------------------------------------------------------
# Thermo tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_enthalpy(T_C: float, P_kPa: float) -> dict:
    """Get water enthalpy (kJ/kg) at T (C) and P (kPa)."""
    try:
        h = thermo.enthalpy_from_TP(T_C, P_kPa)
        return {"status": "ok", "enthalpy_kJ_kg": round(h / 1000.0, 2), "phase": thermo.phase_from_TP(T_C, P_kPa)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_density(T_C: float, P_kPa: float) -> dict:
    """Get water density (kg/m3) at T (C) and P (kPa)."""
    try:
        rho = thermo.density_from_TP(T_C, P_kPa)
        return {"status": "ok", "density_kg_m3": round(rho, 1)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_saturation_temperature(P_kPa: float) -> dict:
    """Get saturation temperature (C) for given pressure (kPa)."""
    try:
        Tsat = thermo.saturation_temperature(P_kPa)
        if Tsat is None:
            return {"status": "error", "message": "Pressure out of IAPWS range"}
        return {"status": "ok", "saturation_T_C": round(Tsat, 2)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_batch_properties(T_C: list, P_kPa: list, outputs: list = None) -> dict:
    """Batch compute properties from lists of T (C) and P (kPa)."""
    try:
        if outputs is None:
            outputs = ["H", "D", "V", "C"]
        results = thermo.batch_properties(T_C, P_kPa, outputs)
        return {"status": "ok", "count": len(results), "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Wellbore tools
# ---------------------------------------------------------------------------

@mcp.tool()
def calculate_ipr(P_res_kPa: float, P_wf_kPa: float, J_kg_s_kPa: float) -> dict:
    """Calculate mass flow rate using IPR: q = J * (P_res - P_wf)."""
    try:
        q = wellbore.ipr_mass_flow(P_res_kPa, P_wf_kPa, J_kg_s_kPa)
        return {"status": "ok", "q_kg_s": round(q, 2)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def calculate_tpr(P_wf_kPa: float, rho_avg_kg_m3: float, TVD_m: float, L_m: float, D_m: float, f_Darcy: float, v_ms: float) -> dict:
    """Calculate wellhead pressure using TPR."""
    try:
        P_wh = wellbore.tpr_wellhead_pressure(P_wf_kPa, rho_avg_kg_m3, TVD_m, L_m, D_m, f_Darcy, v_ms)
        return {"status": "ok", "P_wh_kPa": round(P_wh, 2)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def find_operating_point(P_res_kPa: float, J_kg_s_kPa: float, rho_avg_kg_m3: float, TVD_m: float, L_m: float, D_m: float, f_Darcy: float, v_ms: float) -> dict:
    """Find IPR-TPR operating point."""
    try:
        q, P_wf, P_wh, _, _ = wellbore.operating_point(P_res_kPa, J_kg_s_kPa, rho_avg_kg_m3, TVD_m, L_m, D_m, f_Darcy, v_ms, num_points=200)
        return {"status": "ok", "q_kg_s": round(q, 2), "P_wf_kPa": round(P_wf, 2), "P_wh_kPa": round(P_wh, 2)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Scaling tools
# ---------------------------------------------------------------------------

@mcp.tool()
def check_caco3_scaling(T_C: float, Ca_mg_L: float, HCO3_mg_L: float, pH: float) -> dict:
    """Check CaCO3 scaling risk using Ryznar Index."""
    try:
        rsi = scaling.ryznar_index(T_C, Ca_mg_L, HCO3_mg_L, pH)
        if rsi < 6:
            risk = "high"
        elif rsi < 7:
            risk = "moderate"
        else:
            risk = "low"
        return {"status": "ok", "RSI": round(rsi, 2), "risk": risk}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def check_sio2_scaling(SiO2_mg_L: float, T_C: float) -> dict:
    """Check amorphous silica scaling risk."""
    try:
        result = scaling.sio2_scaling_risk(SiO2_mg_L, T_C)
        return {"status": "ok", **{k: round(v, 3) if isinstance(v, float) else v for k, v in result.items()}}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def check_corrosivity(pH: float, Cl_mg_L: float, H2S_mg_L: float = 0.0) -> dict:
    """Assess brine corrosivity."""
    try:
        result = scaling.corrosivity_index(pH, Cl_mg_L, H2S_mg_L)
        return {"status": "ok", "score": result["score"], "class": result["class"]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Decline tools
# ---------------------------------------------------------------------------

@mcp.tool()
def simulate_decline(model: str, y0: float, rate: float, years: int, b: float = 0.5, initial_rate: float = 0.0) -> dict:
    """
    Simulate decline curve. model = 'exponential' or 'hyperbolic'.
    For exponential: rate = decline rate per year.
    For hyperbolic: initial_rate = initial decline fraction, b = hyperbolic exponent.
    """
    try:
        if model == "exponential":
            vals = decline.exponential_decline(y0, rate, years)
        elif model == "hyperbolic":
            vals = decline.hyperbolic_decline(y0, initial_rate, b, years)
        else:
            return {"status": "error", "message": f"Unknown model: {model}"}
        return {"status": "ok", "values": vals}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def simulate_reinjection_temperature(extraction_temp_C: float, reinjection_temp_C: float, fraction_cooled: float, years: int) -> dict:
    """Simulate reservoir temperature decline from cold reinjection."""
    try:
        temps = decline.reinjection_temperature_model(extraction_temp_C, reinjection_temp_C, fraction_cooled, years)
        return {"status": "ok", "temps_C": temps}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Heat balance tools
# ---------------------------------------------------------------------------

@mcp.tool()
def calculate_heat_in_reservoir(volume_m3: float, porosity: float, rho_rock_kg_m3: float, rho_water_kg_m3: float, T_C: float) -> dict:
    """Calculate total sensible heat stored in reservoir (MJ)."""
    try:
        H = heat_balance.heat_in_reservoir(volume_m3, porosity, rho_rock_kg_m3, rho_water_kg_m3, T_C)
        return {"status": "ok", "heat_MJ": round(H, 1)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def calculate_power_output(mass_flow_kg_s: float, h_in_kJ_kg: float, h_out_kJ_kg: float, efficiency: float = 0.12) -> dict:
    """Calculate gross power output (MW) from brine enthalpy drop."""
    try:
        W = heat_balance.power_output_from_mass_flow(mass_flow_kg_s, h_in_kJ_kg, h_out_kJ_kg, efficiency)
        return {"status": "ok", "power_MW": round(W, 2)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Sensitivity tools
# ---------------------------------------------------------------------------

@mcp.tool()
def run_monte_carlo(func_name: str, param_distributions: dict, n_samples: int = 500, seed: int = 42) -> dict:
    """
    Run Monte Carlo on a pygeotoolbox function.
    Available func_name: 'power_output', 'ipr', 'heat_in_reservoir'.
    param_distributions: dict of {param: [mean, std]}.
    """
    try:
        func_map = {
            "power_output": lambda **kw: heat_balance.power_output_from_mass_flow(kw["m_dot"], kw["h_in"], kw["h_out"], kw.get("eta", 0.12)),
            "ipr": lambda **kw: wellbore.ipr_mass_flow(kw["P_res"], kw["P_wf"], kw["J"]),
            "heat_in_reservoir": lambda **kw: heat_balance.heat_in_reservoir(kw["V"], kw["phi"], kw["rho_r"], kw["rho_w"], kw["T"]),
        }
        func = func_map.get(func_name)
        if not func:
            return {"status": "error", "message": f"Unknown func_name: {func_name}"}
        import numpy as np
        if seed is not None:
            np.random.seed(seed)
        results = []
        for _ in range(n_samples):
            kwargs = {}
            for k, (mu, sigma) in param_distributions.items():
                kwargs[k] = np.random.normal(mu, sigma)
            try:
                r = func(**kwargs)
                results.append(r)
            except Exception:
                results.append(None)
        valid = [r for r in results if r is not None and np.isfinite(r)]
        if not valid:
            return {"status": "error", "message": "No valid results from Monte Carlo"}
        return {"status": "ok", "mean": round(np.mean(valid), 3), "p10": round(np.percentile(valid, 10), 3), "p50": round(np.percentile(valid, 50), 3), "p90": round(np.percentile(valid, 90), 3)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Transport properties tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_thermal_conductivity(T_C: float, P_kPa: float) -> dict:
    """Get thermal conductivity W/(m·K) at T (C) and P (kPa). Uses IAPWS priority."""
    try:
        k = transport.thermal_conductivity(T_C, P_kPa)
        if k is None:
            return {"status": "error", "message": "Outside IAPWS range or no backend available"}
        return {"status": "ok", "k_W_mK": round(k, 6)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_dynamic_viscosity(T_C: float, P_kPa: float) -> dict:
    """Get dynamic viscosity Pa·s at T (C) and P (kPa). Uses IAPWS priority."""
    try:
        mu = transport.dynamic_viscosity(T_C, P_kPa)
        if mu is None:
            return {"status": "error", "message": "Outside IAPWS range or no backend available"}
        return {"status": "ok", "mu_Pas": round(mu, 9)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_transport_package(T_C: float, P_kPa: float) -> dict:
    """Get complete transport properties: k, mu, nu, Pr."""
    try:
        props = transport.transport_properties(T_C, P_kPa)
        return {"status": "ok", **props}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# IAPWS saturation tools
# ---------------------------------------------------------------------------

@mcp.tool()
def iapws_saturation_temperature(P_kPa: float) -> dict:
    """Get IAPWS saturation temperature (C) from pressure (kPa)."""
    try:
        T = siapws_saturation.saturation_temperature(P_kPa)
        if T is None:
            return {"status": "error", "message": "Pressure outside IAPWS range (0.611657 - 22064 kPa)"}
        return {"status": "ok", "T_sat_C": round(T, 6)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def iapws_saturation_pressure(T_C: float) -> dict:
    """Get IAPWS saturation pressure (kPa) from temperature (C)."""
    try:
        P = siapws_saturation.saturation_pressure(T_C)
        if P is None:
            return {"status": "error", "message": "Temperature outside IAPWS range (0.01 - 373.946 C)"}
        return {"status": "ok", "P_sat_kPa": round(P, 6)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def iapws_saturation_properties(P_kPa: float) -> dict:
    """Get saturation properties including T, P, phase, status."""
    try:
        result = siapws_saturation.saturation_properties(P_kPa)
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Tier 2: Seawater tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_seawater_density(T_C: float, salinity_psu: float, P_MPa: float = 0.1) -> dict:
    """Get seawater density in kg/m3 at T (C), salinity (psu), optional P (MPa)."""
    try:
        result = seawater.seawater_density(T_C, salinity_psu, P_MPa)
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_seawater_surface_tension(T_C: float, salinity_psu: float = 35.0) -> dict:
    """Get seawater surface tension in N/m at T (C) and salinity (psu)."""
    try:
        result = seawater.seawater_surface_tension(T_C, salinity_psu)
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_seawater_thermal_conductivity(T_C: float, salinity_psu: float) -> dict:
    """Get seawater thermal conductivity in W/(m·K)."""
    try:
        result = seawater.seawater_thermal_conductivity(T_C, salinity_psu)
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Tier 2: Geophysics tools
# ---------------------------------------------------------------------------

@mcp.tool()
def get_brine_conductivity(T_C: float, Na_mg_L: float = 0.0, Cl_mg_L: float = 0.0,
                           Ca_mg_L: float = 0.0, HCO3_mg_L: float = 0.0,
                           salinity_psu: float | None = None) -> dict:
    """Estimate brine electrical conductivity in S/m from ions or salinity."""
    try:
        if salinity_psu is not None:
            result = geophysics.brine_electrical_conductivity(T_C, salinity_psu=salinity_psu)
        else:
            result = geophysics.brine_electrical_conductivity(T_C, Na_mg_L=Na_mg_L, Cl_mg_L=Cl_mg_L,
                                                              Ca_mg_L=Ca_mg_L, HCO3_mg_L=HCO3_mg_L)
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_resistivity_from_conductivity(conductivity_S_m: float) -> dict:
    """Convert conductivity S/m to resistivity ohm·m."""
    try:
        rho = geophysics.resistivity_from_conductivity(conductivity_S_m)
        return {"status": "ok", "resistivity_ohm_m": round(rho, 6)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def estimate_salinity_from_resistivity(resistivity_ohm_m: float, T_C: float = 25.0) -> dict:
    """Estimate salinity from resistivity (empirical approximation)."""
    try:
        result = geophysics.salinity_from_resistivity(resistivity_ohm_m, T_C)
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Tier 2: NaCl Critical Point
# ---------------------------------------------------------------------------

@mcp.tool()
def get_nacl_critical(molality: float) -> dict:
    """Estimate critical T (C) and P (kPa) for NaCl-H2O solution."""
    try:
        result = scaling.nacl_critical_properties(molality)
        return {"status": "ok", **result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def convert_salinity_to_molality(salinity_wt_percent: float) -> dict:
    """Convert wt% NaCl to molality (mol/kg water)."""
    try:
        m = scaling.salinity_to_molality(salinity_wt_percent)
        if math.isnan(m):
            return {"status": "error", "message": "Invalid salinity range"}
        return {"status": "ok", "molality": round(m, 4)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
def convert_molality_to_salinity(molality: float) -> dict:
    """Convert molality back to approximate wt% NaCl."""
    try:
        s = scaling.molality_to_salinity(molality)
        return {"status": "ok", "salinity_wt_percent": round(s, 4)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def main():
    mcp.run()

if __name__ == "__main__":
    main()
