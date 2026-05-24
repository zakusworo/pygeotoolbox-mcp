"""Tests for niche IAPWS modules: humid air (G11-15) and SBTL (G13-15)."""
import pytest
import math
from pygeotoolbox import humid_air, sbtl


class TestHumidAir:
    def test_humidity_ratio_zero_rh(self):
        w = humid_air.humidity_ratio(20, 101.325, 0.0)
        assert w == 0.0

    def test_humidity_ratio_increases_with_rh(self):
        w1 = humid_air.humidity_ratio(20, 101.325, 0.3)
        w2 = humid_air.humidity_ratio(20, 101.325, 0.6)
        assert 0 < w1 < w2

    def test_density_decreases_with_humidity(self):
        """Humid air is less dense than dry air (molar mass of water < air)."""
        rho_dry = humid_air.density_humid_air(30, 101.325, 0.0)
        rho_wet = humid_air.density_humid_air(30, 101.325, 0.8)
        assert rho_wet < rho_dry

    def test_enthalpy_increases_with_humidity(self):
        h_dry = humid_air.enthalpy_humid_air(30, 0.0)
        h_wet = humid_air.enthalpy_humid_air(30, 0.8)
        assert h_wet > h_dry

    def test_dew_point_below_temperature(self):
        T_dp = humid_air.dew_point(40, 101.325, 0.5)
        assert T_dp is not None
        assert T_dp < 40

    def test_dew_point_hundred_percent_equals_temperature(self):
        # At 100% RH, dew point equals temperature (approximately)
        T_dp = humid_air.dew_point(25, 101.325, 1.0)
        assert abs(T_dp - 25.0) < 0.5

    def test_package_keys(self):
        pkg = humid_air.humid_air_properties(20, 101.325, 0.5)
        assert set(pkg.keys()) == {"humidity_ratio_kg_wv_kg_da", "density_kg_m3", "enthalpy_J_kg_da", "dew_point_C"}

    def test_invalid_rh_raises(self):
        with pytest.raises(ValueError):
            humid_air.humidity_ratio(20, 101.325, -0.1)
        with pytest.raises(ValueError):
            humid_air.humidity_ratio(20, 101.325, 1.1)


class TestSBTL:
    def test_lookup_rho_positive(self):
        rho = sbtl.lookup(200, 2.0, "rho")
        assert float(rho) > 0

    def test_lookup_h_increases_with_T(self):
        h1 = float(sbtl.lookup(100, 2.0, "h"))
        h2 = float(sbtl.lookup(200, 2.0, "h"))
        assert h2 > h1

    def test_lookup_phase_liquid_at_high_P(self):
        phase = sbtl.lookup(100, 10.0, "phase")
        assert phase == "liquid"

    def test_lookup_package_keys(self):
        pkg = sbtl.lookup_package(150, 1.0)
        assert set(pkg.keys()) == {"rho_kg_m3", "h_kJ_kg", "phase"}

    def test_invalid_quantity_raises(self):
        with pytest.raises(ValueError):
            sbtl.lookup(100, 1.0, "entropy")

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            sbtl.lookup(900, 1.0, "rho")
        with pytest.raises(ValueError):
            sbtl.lookup(100, 200.0, "rho")
