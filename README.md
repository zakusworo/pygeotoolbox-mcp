# pygeotoolbox-mcp

Geothermal engineering toolbox with MCP server for Hermes Agent.

Inspired by [gabrielserrao/pyrestoolbox-mcp](https://github.com/gabrielserrao/pyrestoolbox-mcp), reimplemented from scratch for geothermal engineering using CoolProp + 11 IAPWS formulations (IF97, Supp-sat, ThCond, Viscosity, G11-15, G12-15, G13-15, G14-19, Electrical Conductivity, NaCl Critical, Advisory Notes).

## Features

- **Thermodynamic properties** (enthalpy, density, viscosity, cp, conductivity, phase) via CoolProp + IAPWS-IF97
- **IAPWS Saturation** (backward T(p), P(T), saturation properties) — triple point to critical point
- **Transport properties** (thermal conductivity, dynamic viscosity, kinematic viscosity, Prandtl)
- **Seawater properties** (density, surface tension, thermal conductivity)
- **Geophysics** (brine electrical conductivity, resistivity → salinity)
- **Supercooled water** (IAPWS G12-15: −22 to 0 °C)
- **Humid air** (IAPWS G11-15: cooling tower, gas extraction)
- **SBTL fast lookup** (IAPWS G13-15: real-time / Monte Carlo)
- **Wellbore deliverability** (IPR/TPR, operating point, productivity index)
- **Brine & scaling** (Ryznar CaCO3, SiO2 scaling risk, corrosivity, NaCl critical)
- **Decline curves** (exponential, hyperbolic, reinjection temperature model)
- **Heat balance** (reservoir heat, power, NPV)
- **Sensitivity analysis** (one-factor sweep, tornado, Monte Carlo, rank correlation)
- **MCP server** with 29 tools exposed via FastMCP STDIO/HTTP transport

## Install

```bash
pip install -e .
```

Or requirements only:
```bash
pip install -r requirements.txt
```

## Usage

### Python library

```python
from pygeotoolbox import thermo, wellbore

# Thermo
h = thermo.enthalpy_from_TP(200, 2000)       # J/kg
rho = thermo.density_from_TP(200, 2000)        # kg/m3
phase = thermo.phase_from_TP(200, 2000)        # 'liquid'

# Wellbore
q = wellbore.ipr_mass_flow(20000, 19000, 0.5)  # kg/s
P_wh = wellbore.tpr_wellhead_pressure(18000, 900, 1200, 1500, 0.2, 0.02, 2.5)  # kPa
q_op, P_wf, P_wh, _, _ = wellbore.operating_point(20000, 0.5, 900, 1200, 1500, 0.2, 0.02, 2.5)
```

### MCP Server

```bash
# STDIO (for Hermes Agent integration)
fastmcp run src/pygeotoolbox/mcp_server.py

# HTTP
fastmcp run src/pygeotoolbox/mcp_server.py --transport http --port 8000
```

## Modules

| Module | Description |
|--------|-------------|
| `thermo` | IAPWS-IF97 properties via CoolProp |
| `siapws_saturation` | IAPWS saturation T(p), P(T), properties |
| `transport` | Thermal conductivity, viscosity, Prandtl |
| `seawater` | Seawater density, surface tension, thermal conductivity |
| `geophysics` | Brine conductivity, resistivity ↔ salinity |
| `thermo_supercooled` | IAPWS G12-15: supercooled water −22 to 0 °C |
| `humid_air` | IAPWS G11-15: humid air / cooling tower properties |
| `sbtl` | IAPWS G13-15: fast lookup for Monte Carlo / real-time |
| `advisory_notes` | IAPWS Advisory Notes 1–6: documented pitfalls |
| `wellbore` | IPR/TPR, operating point |
| `scaling` | CaCO3, SiO2, corrosivity, NaCl critical |
| `decline` | Exponential, hyperbolic, reinjection temp |
| `heat_balance` | Reservoir heat, power, NPV |
| `sensitivity` | One-factor, tornado, Monte Carlo |
| `mcp_server` | FastMCP tool registry (29 tools)

## IAPWS Standards Implemented

| IAPWS Release | Module | Geothermal Use |
|---------------|--------|----------------|
| IAPWS-IF97 (base) | `thermo`, `transport` | All thermo + transport properties |
| Supplementary Saturation | `siapws_saturation` | T(P), P(T), flash calculations |
| Thermal Conductivity | `transport` | k(T, P) for heat exchanger sizing |
| Viscosity | `transport` | μ(T, P) for pressure drop |
| G11-15 Humid Air | `humid_air` | Cooling towers, gas extraction |
| G12-15 Supercooled | `thermo_supercooled` | Cold reinjection, EGS, −22 to 0 C |
| G13-15 SBTL | `sbtl` | Fast Monte Carlo / real-time lookup |
| G14-19 Seawater | `seawater` | Coastal/offshore, OTEC |
| Electrical Conductivity | `geophysics` | Resistivity log → salinity |
| NaCl Critical Point | `scaling` | High-salinity brine systems |
| Advisory Notes 1–6 | `advisory_notes` | Documented edge cases and best practices |

## Link to Course

This toolbox powers the exercises in the companion course repo:

**[zakusworo/hermes-geothermal-engineering](https://github.com/zakusworo/hermes-geothermal-engineering)**

Hermes Agent course with 14 exercise modules using this library.

## License

MIT License — Copyright 2026 Zulfikar Aji Kusworo
