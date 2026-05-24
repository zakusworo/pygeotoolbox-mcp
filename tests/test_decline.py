"""Tests for pygeotoolbox decline module."""
import pytest
from pygeotoolbox import decline


def test_exponential_decline_shape():
    vals = decline.exponential_decline(200, 0.05, 10)
    assert len(vals) == 11
    assert vals[0] == pytest.approx(200)
    assert vals[-1] < vals[0]


def test_hyperbolic_decline_shape():
    vals = decline.hyperbolic_decline(200, 0.1, 0.5, 10)
    assert len(vals) == 11
    assert vals[-1] < vals[0]


def test_reinjection_temperature_declines():
    temps = decline.reinjection_temperature_model(250, 80, 0.3, 20)
    assert len(temps) == 21
    assert temps[0] == pytest.approx(250)
    assert temps[-1] < temps[0]
    assert temps[-1] > 80  # should not go below reinjection temp entirely
