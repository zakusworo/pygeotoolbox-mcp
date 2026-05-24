"""Tests for pygeotoolbox thermo module."""
import pytest
from pygeotoolbox import thermo


def test_enthalpy_at_200C_2MPa():
    h = thermo.enthalpy_from_TP(200, 2000)
    # CoolProp IAPWS-IF97 at 200C, 2MPa (liquid)
    assert 852000 < h < 853000


def test_density_at_200C_2MPa():
    rho = thermo.density_from_TP(200, 2000)
    assert 864 < rho < 866


def test_phase_liquid_200C_2MPa():
    phase = thermo.phase_from_TP(200, 2000)
    assert phase in ('liquid', 'supercritical_liquid')


def test_saturation_temperature_valid():
    Tsat = thermo.saturation_temperature(500)
    assert Tsat is not None
    assert 150 < Tsat < 152  # ~151.8 C at 500 kPa


def test_saturation_temperature_invalid():
    # Very low pressure (below triple point ~0.611 kPa)
    result = thermo.saturation_temperature(0.1)
    assert result is None


def test_steam_quality_liquid():
    h_liq = thermo.enthalpy_from_TP(150, 500)
    q = thermo.steam_quality_from_enthalpy(h_liq, 500)
    assert q == 0.0


def test_batch_properties_shape():
    T = [150, 200, 250]
    P = [500, 2000, 5000]
    results = thermo.batch_properties(T, P)
    assert len(results) == 3
    assert 'enthalpy_J_kg' in results[0]
    assert 'density_kg_m3' in results[0]
