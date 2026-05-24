"""
IAPWS Advisory Notes: Known Edge Cases and Pitfalls

This module documents IAPWS Advisory Notes (Advise1 through Advise6)
that affect numerical stability and physical correctness in
calculations.  No new code — only warnings and best-practice guidance.

Usage: import this module at the start of a script to log warnings.
Or reference it in CLAUDE.md / AGENTS.md for LLM context.

---
Advisory Note 1: Saturation Boundary Discontinuity
---------------------------------------------------
Problem: At exactly T = 0 C, P = 0.611657 kPa, IAPWS-IF97 switches
from liquid to two-phase.  Forward/backward equations have small
(~1e-6) discontinuity.
Impact: Flash calculations at triple point may oscillate.
Fix: Clamp to liquid if T > T_sat + 1e-6 or vapor if T < T_sat - 1e-6.
Implemented in: siapws_saturation.py (clamping guard)

---
Advisory Note 2: Near-Critical Point Singularity
-------------------------------------------------
Problem: At T = 373.946 C, P = 22.064 MPa, derivatives drho/dP
diverge.  Newton solvers may fail.
Impact: Wellbore calculations near critical point crash.
Fix: Use reduced temperature Tr = T/Tc < 0.999 for liquid calculations.
Implemented in: thermo.py (CoolProp handles this internally)

---
Advisory Note 3: Region 3 (Near-Critical) Equation Sensitivity
--------------------------------------------------------------
Problem: IAPWS-IF97 Region 3 (near-critical) uses iterative
backward equations.  Convergence is slow near boundaries.
Impact: Batch processing millions of points may timeout.
Fix: Use SBTL (sbtl.py) for initial guess, then refine with CoolProp.
Implemented in: sbtl.py (coarse grid as initial guess)

---
Advisory Note 4: Supercooled Water Metastability
-------------------------------------------------
Problem: G12-15 properties describe metastable liquid.  In reality,
water below 0 C crystallizes on nucleation sites.
Impact: Models may overpredict liquid water at −20 C.
Fix: Check for ice nucleation probability (not implemented here).
Guidance: Results valid only for timescales shorter than nucleation lag.
Implemented in: thermo_supercooled.py (documented in docstring)

---
Advisory Note 5: Humid Air at Low Pressure
-------------------------------------------
Problem: Virial formulation for humid air breaks down below 0.1 MPa.
Impact: High-altitude cooling tower calculations inaccurate.
Fix: Use ideal gas approximation for P < 0.05 MPa.
Implemented in: humid_air.py (documented range)

---
Advisory Note 6: Seawater Salinity Range
-----------------------------------------
Problem: IAPWS seawater formulations are calibrated for S = 0–42 psu.
Outside this range, ion pairing effects not captured.
Impact: Brine density for very high salinity (>200 g/kg) may be wrong.
Fix: Use Pitzer equations for extreme salinity (future work).
Implemented in: seawater.py (documented range)
"""

import logging

logger = logging.getLogger(__name__)


def log_advisory_notes():
    """Print a summary of all advisory notes to stdout."""
    notes = [
        "Advise1: Saturation boundary clamping (siapws_saturation.py)",
        "Advise2: Near-critical singularity (thermo.py)",
        "Advise3: Region 3 sensitivity → fallback to SBTL (sbtl.py)",
        "Advise4: Supercooled metastability (thermo_supercooled.py)",
        "Advise5: Humid air low-pressure limit (humid_air.py)",
        "Advise6: Seawater salinity range (seawater.py)",
    ]
    for note in notes:
        logger.info(note)
    return notes


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for n in log_advisory_notes():
        print(n)
