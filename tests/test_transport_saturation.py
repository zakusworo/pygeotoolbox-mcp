"""Tests for pygeotoolbox saturation and transport modules."""
import pytest
from pygeotoolbox import siapws_saturation, transport


# --- IAPWS Saturation Tests ---
class TestSaturation:
    def test_triple_point(self):
        T = siapws_saturation.saturation_temperature(0.611657)
        assert T is not None
        assert abs(T - 0.01) < 0.001

    def test_one_atm(self):
        T = siapws_saturation.saturation_temperature(101.325)
        assert T is not None
        assert 99.9 < T < 100.1

    def test_high_pressure(self):
        T = siapws_saturation.saturation_temperature(10000)
        assert T is not None
        assert 310.0 < T < 311.0

    def test_critical_pressure(self):
        T = siapws_saturation.saturation_temperature(22064.0)
        assert T is not None
        assert abs(T - 373.946) < 0.01

    def test_out_of_range_low(self):
        T = siapws_saturation.saturation_temperature(0.1)
        assert T is None

    def test_out_of_range_high(self):
        T = siapws_saturation.saturation_temperature(25000)
        assert T is None

    def test_saturation_pressure_triple(self):
        P = siapws_saturation.saturation_pressure(0.01)
        assert P is not None
        assert abs(P - 0.611657) < 0.001

    def test_saturation_pressure_boiling(self):
        P = siapws_saturation.saturation_pressure(100)
        assert P is not None
        assert 100.0 < P < 102.0

    def test_roundtrip(self):
        """T(P) then P(T) should approximate original."""
        for P_test in [10.0, 500.0, 5000.0, 15000.0]:
            T = siapws_saturation.saturation_temperature(P_test)
            if T:
                P_back = siapws_saturation.saturation_pressure(T)
                assert P_back is not None
                rel_err = abs(P_back - P_test) / P_test
                assert rel_err < 0.01  # <1% relative error

    def test_saturation_properties_structure(self):
        props = siapws_saturation.saturation_properties(101.325)
        assert props["status"] == "valid"
        assert "T_sat_C" in props
        assert "phase" in props


# --- Transport Properties Tests ---
class TestTransport:
    def test_thermal_conductivity_liquid(self):
        k = transport.thermal_conductivity(200, 2000)
        assert k is not None
        assert 0.5 < k < 0.8  # Liquid water ~0.66 W/mK at 200C

    def test_thermal_conductivity_steam(self):
        k = transport.thermal_conductivity(500, 10000)
        assert k is not None
        assert 0.02 < k < 0.15  # Steam much lower

    def test_viscosity_liquid(self):
        mu = transport.dynamic_viscosity(200, 2000)
        assert mu is not None
        assert 1e-4 < mu < 2e-4  # ~0.000135 Pa·s

    def test_viscosity_steam(self):
        mu = transport.dynamic_viscosity(500, 10000)
        assert mu is not None
        assert mu < 5e-5  # Gas ~2-3e-5 Pa·s

    def test_transport_package_keys(self):
        props = transport.transport_properties(200, 2000)
        assert "k_W_mK" in props
        assert "mu_Pas" in props
        assert "nu_m2_s" in props
        assert "Pr" in props
        assert props["Pr"] is not None
        assert 0.5 < props["Pr"] < 10

    def test_prandtl_number_trend(self):
        """Prandtl number should decrease with increasing temperature for liquid."""
        props_cold = transport.transport_properties(50, 500)
        props_hot = transport.transport_properties(200, 500)
        assert props_cold["Pr"] > props_hot["Pr"]

    def test_transport_near_saturation(self):
        """At saturation boundary, values should remain well-defined."""
        T_sat = siapws_saturation.saturation_temperature(2000)
        if T_sat:
            k = transport.thermal_conductivity(T_sat, 2000)
            mu = transport.dynamic_viscosity(T_sat, 2000)
            assert k is not None
            assert mu is not None
