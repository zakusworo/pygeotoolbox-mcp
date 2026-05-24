"""Tests for pygeotoolbox wellbore module."""
import pytest
from pygeotoolbox import wellbore


def test_ipr_positive():
    # Realistic geothermal parameters
    q = wellbore.ipr_mass_flow(20000, 19000, 0.5)
    assert q == 500.0


def test_ipr_zero_at_equal():
    q = wellbore.ipr_mass_flow(20000, 20000, 0.5)
    assert q == 0.0


def test_ipr_no_backflow():
    q = wellbore.ipr_mass_flow(20000, 21000, 0.5)
    assert q == 0.0


def test_tpr_wellhead_less_than_bottomhole():
    P_wh = wellbore.tpr_wellhead_pressure(18000, 900, 1200, 1500, 0.2, 0.02, 2.5)
    assert P_wh < 18000
    assert P_wh > 0


def test_operating_point_found():
    q, P_wf, P_wh, _, _ = wellbore.operating_point(20000, 0.5, 900, 1200, 1500, 0.2, 0.02, 2.5)
    assert q > 0
    assert 0 < P_wf < 20000
    assert P_wh > 0


def test_productivity_index_backcalc():
    J = wellbore.productivity_index_from_test(20000, 19000, 500.0)
    assert abs(J - 0.5) < 1e-6
