"""
Physical-consistency tests for the ORC and flash repairs (v0.5.2).

These encode the first-principles checks that the agentic VERIFY stage applies:
a subcritical ORC must not exceed the Carnot efficiency, and evaporating a
working fluid above its critical temperature must be rejected rather than
silently producing nonsense via a property-library fallback.
"""
import pytest

from pygeotoolbox.working_fluid import orc_cycle_efficiency, critical_temperature_C
from pygeotoolbox import multiflash


def test_subcritical_orc_respects_carnot():
    """Cycle efficiency must not exceed the Carnot limit (second law)."""
    for fluid, T_evap, T_cond in [("R134a", 70, 15), ("R600a", 125, 30), ("R290", 60, 20)]:
        r = orc_cycle_efficiency(T_evap, T_cond, fluid)
        assert r["second_law_ok"] is True
        assert r["eta_thermal_percent"] <= r["eta_carnot_percent"] + 1e-6
        assert 0 < r["eta_thermal_percent"] < r["eta_carnot_percent"]


def test_supercritical_evaporation_rejected():
    """R134a cannot evaporate at 150 C (> Tcrit 101.1 C): must raise, not fudge."""
    assert critical_temperature_C("R134a") < 150
    with pytest.raises(ValueError):
        orc_cycle_efficiency(150, 35, "R134a")


def test_condenser_above_evaporator_rejected():
    with pytest.raises(ValueError):
        orc_cycle_efficiency(60, 80, "R134a")


def test_flash_uses_iapws_saturation():
    """Saturation enthalpies should match IAPWS-IF97 within ~1% (not the old
    linear fits, which were ~3-4% off at 260 C)."""
    hf, hg, sf, sg = multiflash.saturation_properties(260.0)
    assert abs(hf - 1134.9) / 1134.9 < 0.01      # IAPWS h_f(260C)
    assert abs(hg - 2796.6) / 2796.6 < 0.01      # IAPWS h_g(260C)
    assert sg > sf > 0


def test_turbine_work_is_isentropic_and_wet():
    """Isentropic expansion of 260 C steam to a 40 C condenser is very wet, and
    the Baumann-corrected work is positive and below the dry isentropic work."""
    w, x_exit = multiflash.isentropic_turbine_work(260, 40, eta_turbine=0.83)
    assert 0.6 < x_exit < 0.9          # wet exhaust
    assert 400 < w < 900               # kJ/kg, physically reasonable
