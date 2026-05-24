"""Tests for IAPWS G12-15 Supercooled Water module."""
import pytest
from pygeotoolbox import thermo_supercooled


class TestSupercooled:
    def test_density_decreases_with_cooling(self):
        """Density should decrease as T decreases below 0 C."""
        rho_0 = thermo_supercooled.density(0, 0.1)
        rho_m5 = thermo_supercooled.density(-5, 0.1)
        rho_m15 = thermo_supercooled.density(-15, 0.1)
        assert rho_0 > rho_m5 > rho_m15

    def test_density_range(self):
        """Density should stay within realistic bounds for supercooled water."""
        rho = thermo_supercooled.density(-10, 0.1)
        assert 995 < rho < 1005

    def test_pressure_increases_density(self):
        """Higher pressure should give higher density."""
        rho_lowP = thermo_supercooled.density(-10, 0.1)
        rho_highP = thermo_supercooled.density(-10, 10.0)
        assert rho_highP > rho_lowP

    def test_enthalpy_negative_below_zero(self):
        """Enthalpy below 0 C should be negative (relative to 0 C reference)."""
        h = thermo_supercooled.enthalpy(-10, 0.1)
        assert h < 0

    def test_enthalpy_decreases_with_cooling(self):
        """Enthalpy should decrease as T decreases."""
        h_0 = thermo_supercooled.enthalpy(0, 0.1)
        h_m10 = thermo_supercooled.enthalpy(-10, 0.1)
        h_m20 = thermo_supercooled.enthalpy(-20, 0.1)
        assert h_0 > h_m10 > h_m20

    def test_specific_heat_positive(self):
        cp = thermo_supercooled.specific_heat_pressure(-10, 0.1)
        assert cp > 4000

    def test_thermal_expansion_negative(self):
        """Alpha is negative for T < 4 C (water contracts on heating)."""
        alpha = thermo_supercooled.thermal_expansion(-10, 0.1)
        assert alpha < 0

    def test_package_keys(self):
        pkg = thermo_supercooled.transport_properties_supercooled(-5, 0.1)
        assert set(pkg.keys()) == {"rho_kg_m3", "h_J_kg", "cp_J_kg_K", "alpha_1_K"}

    def test_boundary_min(self):
        """T = -22 C should be valid."""
        rho = thermo_supercooled.density(-22, 0.1)
        assert 990 < rho < 1000

    def test_boundary_max(self):
        """T = 0 C at P=50 MPa should be valid."""
        rho = thermo_supercooled.density(0, 50.0)
        # At 50 MPa water is compressed; rho ~1020 kg/m3
        assert 1010 < rho < 1030

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            thermo_supercooled.density(-30, 0.1)
        with pytest.raises(ValueError):
            thermo_supercooled.density(0, 60.0)
