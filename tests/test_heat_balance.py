"""Tests for pygeotoolbox heat_balance module."""
import pytest
from pygeotoolbox import heat_balance


def test_heat_in_reservoir_positive():
    H = heat_balance.heat_in_reservoir(1e9, 0.15, 2650, 900, 250)
    assert H > 0


def test_thermal_recovery_factor_range():
    R = heat_balance.thermal_recovery_factor(250, 100, 0, 0.3)
    assert 0 < R < 1


def test_power_output_positive():
    W = heat_balance.power_output_from_mass_flow(100, 1200, 400, 0.12)
    assert W > 0


def test_npv_has_keys():
    npv = heat_balance.net_present_value_geothermal(
        annual_energy_MWh=[100000] * 10,
        electricity_price_per_MWh=50,
        opex_per_MWh=10,
        capex_MUSD=50,
    )
    assert "NPV_MUSD" in npv
    assert "LCOE_USD_MWh" in npv
    assert npv["NPV_MUSD"] is not None
