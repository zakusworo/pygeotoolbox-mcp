"""Tests for Tier 2: seawater, geophysics, and NaCl critical properties."""
import pytest
import math
from pygeotoolbox import seawater, geophysics, scaling


# --- Seawater Tests ---
class TestSeawater:
    def test_seawater_density_increases_with_salinity(self):
        d35 = seawater.seawater_density(20, 35)["rho_kg_m3"]
        d0 = seawater.seawater_density(20, 0)["rho_kg_m3"]
        assert d35 > d0
        assert d35 > 1020  # kg/m3 for seawater at 20C

    def test_seawater_decreases_with_temperature(self):
        d20 = seawater.seawater_density(20, 35)["rho_kg_m3"]
        d30 = seawater.seawater_density(30, 35)["rho_kg_m3"]
        assert d30 < d20

    def test_seawater_density_invalid_temp(self):
        r = seawater.seawater_density(50, 35)
        assert r["status"] == "error"

    def test_surface_tension_decreases_with_temp(self):
        s0 = seawater.seawater_surface_tension(0, 35)["sigma_N_m"]
        s25 = seawater.seawater_surface_tension(25, 35)["sigma_N_m"]
        assert s25 < s0

    def test_surface_tension_salinity_effect(self):
        s35 = seawater.seawater_surface_tension(25, 35)["sigma_N_m"]
        s0 = seawater.seawater_surface_tension(25, 0)["sigma_N_m"]
        assert s35 < s0  # Salinity lowers surface tension

    def test_thermal_conductivity_salinity_depression(self):
        k35 = seawater.seawater_thermal_conductivity(20, 35)["k_W_mK"]
        k0 = seawater.seawater_thermal_conductivity(20, 0)["k_W_mK"]
        assert k35 < k0

    def test_full_package(self):
        pkg = seawater.seawater_properties(15, 35, 0.1)
        assert pkg["status"] == "ok"
        assert "rho_kg_m3" in pkg
        assert "sigma_N_m" in pkg
        assert "k_W_mK" in pkg


# --- Geophysics Tests ---
class TestGeophysics:
    def test_pure_water_conductivity_low(self):
        k = geophysics.pure_water_conductivity(25)
        assert k < 1e-4  # S/m

    def test_brine_conductivity_increases_with_salinity(self):
        r1 = geophysics.brine_electrical_conductivity(25, salinity_psu=35)
        r2 = geophysics.brine_electrical_conductivity(25, salinity_psu=5)
        assert r1["conductivity_S_m"] > r2["conductivity_S_m"]

    def test_brine_conductivity_increases_with_temp(self):
        r_cold = geophysics.brine_electrical_conductivity(25, salinity_psu=35)
        r_hot = geophysics.brine_electrical_conductivity(80, salinity_psu=35)
        assert r_hot["conductivity_S_m"] > r_cold["conductivity_S_m"]

    def test_resistivity_from_conductivity(self):
        rho = geophysics.resistivity_from_conductivity(10.0)
        assert abs(rho - 0.1) < 1e-6

    def test_resistivity_zero_returns_inf(self):
        rho = geophysics.resistivity_from_conductivity(0)
        assert rho == float('inf')

    def test_salinity_from_resistivity_range(self):
        high = geophysics.salinity_from_resistivity(0.2, 25)
        low = geophysics.salinity_from_resistivity(20.0, 25)
        assert high["salinity_estimated_psu"] > low["salinity_estimated_psu"]


# --- NaCl Critical Tests ---
class TestNaClCritical:
    def test_pure_water_critical(self):
        r = scaling.nacl_critical_properties(0.0)
        assert r["status"] == "ok"
        assert abs(r["T_critical_C"] - 373.946) < 0.01
        assert abs(r["P_critical_kPa"] - 22064.0) < 1

    def test_brine_critical_higher_than_pure(self):
        r1 = scaling.nacl_critical_properties(0.0)
        r2 = scaling.nacl_critical_properties(2.0)
        assert r2["T_critical_C"] > r1["T_critical_C"]
        assert r2["P_critical_kPa"] > r1["P_critical_kPa"]

    def test_salinity_molality_roundtrip(self):
        original = 5.0  # wt%
        m = scaling.salinity_to_molality(original)
        back = scaling.molality_to_salinity(m)
        assert abs(back - original) < 0.01

    def test_molality_increases_with_salinity(self):
        m1 = scaling.salinity_to_molality(1.0)
        m2 = scaling.salinity_to_molality(10.0)
        assert m2 > m1

    def test_invalid_molality(self):
        assert math.isnan(scaling.salinity_to_molality(-1.0))
