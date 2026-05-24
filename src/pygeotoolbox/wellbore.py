"""
Geothermal wellbore deliverability: IPR + TPR.

Inspired by pyResToolbox nodal analysis, reimplemented for geothermal SI units.
"""
import numpy as np

def ipr_mass_flow(P_res_kPa: float, P_wf_kPa: float, J_kg_s_kPa: float) -> float:
    """Linear productivity index IPR: q = J * (P_res - P_wf), capped at >= 0."""
    q = J_kg_s_kPa * max(P_res_kPa - P_wf_kPa, 0.0)
    return q

def tpr_wellhead_pressure(
    P_wf_kPa: float,
    rho_avg_kg_m3: float,
    TVD_m: float,
    L_m: float,
    D_m: float,
    f_Darcy: float,
    v_ms: float,
    g: float = 9.81,
) -> float:
    """
    Simplified TPR: P_wh = P_wf - hydrostatic - friction.
    All SI units. Result in kPa.
    """
    hydrostatic_Pa = rho_avg_kg_m3 * g * TVD_m
    friction_Pa = f_Darcy * (L_m / max(D_m, 1e-6)) * (rho_avg_kg_m3 * v_ms ** 2) / 2.0
    return P_wf_kPa - (hydrostatic_Pa + friction_Pa) / 1000.0

def operating_point(
    P_res_kPa: float,
    J_kg_s_kPa: float,
    rho_avg_kg_m3: float,
    TVD_m: float,
    L_m: float,
    D_m: float,
    f_Darcy: float,
    v_ms: float,
    num_points: int = 200,
) -> tuple:
    """
    Approximate operating point where IPR and TPR intersect.
    Returns (q_op, P_wf_op, P_wh_op, ipr_curve, tpr_curve).
    """
    ipr_curve = []
    tpr_curve = []
    best = (0.0, P_res_kPa, P_res_kPa)
    best_err = float('inf')
    for i in range(1, num_points):
        frac = i / num_points
        P_wf = P_res_kPa * (1.0 - frac)
        q = ipr_mass_flow(P_res_kPa, P_wf, J_kg_s_kPa)
        P_wh = tpr_wellhead_pressure(P_wf, rho_avg_kg_m3, TVD_m, L_m, D_m, f_Darcy, v_ms)
        ipr_curve.append((P_wf, q))
        tpr_curve.append((P_wf, P_wh))
        err = abs(P_wf - P_wh)
        if err < best_err:
            best_err = err
            best = (q, P_wf, P_wh)
    return (*best, ipr_curve, tpr_curve)

def productivity_index_from_test(
    P_res_kPa: float,
    P_wf_kPa: float,
    q_kg_s: float,
) -> float:
    """Back-calculate productivity index J = q / (P_res - P_wf)."""
    dP = P_res_kPa - P_wf_kPa
    if dP <= 0:
        return 0.0
    return q_kg_s / dP
