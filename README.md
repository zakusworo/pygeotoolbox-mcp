# pygeotoolbox-mcp

Geothermal engineering toolbox with MCP server for Hermes Agent.

Inspired by [gabrielserrao/pyrestoolbox-mcp](https://github.com/gabrielserrao/pyrestoolbox-mcp), reimplemented from scratch for geothermal engineering using CoolProp + IAPWS-IF97.

## Features

- **Thermodynamic properties** (enthalpy, density, viscosity, cp, conductivity, phase) via CoolProp
- **Saturation curves** (T-P saturation, steam quality) via IAPWS-IF97
- **Wellbore deliverability** (IPR/TPR, operating point, productivity index)
- **Brine & scaling** (Ryznar CaCO3, SiO2 scaling risk, corrosivity)
- **Decline curves** (exponential, hyperbolic, reinjection temperature model)
- **Heat balance** (reservoir heat, thermal recovery, power output NPV)
- **Sensitivity analysis** (one-factor sweep, tornado, Monte Carlo, rank correlation)
- **MCP server** with 15+ tools exposed via FastMCP STDIO/HTTP transport

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
| `wellbore` | IPR/TPR, operating point |
| `scaling` | CaCO3, SiO2, corrosivity |
| `decline` | Exponential, hyperbolic, reinjection temp |
| `heat_balance` | Reservoir heat, power, NPV |
| `sensitivity` | One-factor, tornado, Monte Carlo |
| `mcp_server` | FastMCP tool registry |

## Link to Course

This toolbox powers the exercises in the companion course repo:

**[zakusworo/hermes-geothermal-engineering](https://github.com/zakusworo/hermes-geothermal-engineering)**

Hermes Agent course with 9 exercise modules using this library.

## License

MIT License — Copyright 2026 Zulfikar Aji Kusworo
