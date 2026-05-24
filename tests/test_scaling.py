"""Tests for pygeotoolbox scaling module."""
import pytest
from pygeotoolbox import scaling


def test_ryznar_index_calc():
    rsi = scaling.ryznar_index(150, 200, 300, 7.0)
    assert isinstance(rsi, float)


def test_sio2_risk_categorization():
    result = scaling.sio2_scaling_risk(200, 200)
    assert "risk" in result
    assert "ratio" in result
    assert result["ratio"] > 0


def test_brine_density_higher_than_pure():
    rho_pure = scaling.reservoir_brine_density(200, 0.0)
    rho_brine = scaling.reservoir_brine_density(200, 5.0)
    assert rho_brine > rho_pure


def test_corrosivity_class():
    result = scaling.corrosivity_index(5.5, 60000, 15.0)
    assert "score" in result
    assert "class" in result
    assert result["score"] >= 0
