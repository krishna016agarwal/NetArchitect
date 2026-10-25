"""
test_media.py — Independent unit and edge tests for L1 Media Engine.
All expected values are calculated independently using physical standards
and optical budget equations:
  Budget = Tx_min - Rx_sens
  Loss = (km * attenuation) + (4 * 0.5) + (floor(km/2) * 0.1) + 2.0
"""
import pytest
from netarchitect.media import select_media
from netarchitect.errors import PhysicalDistanceViolationError, OpticalBudgetError


def test_copper_boundary_100m():
    """At 100 m, Cat6a copper 10GBASE-T is selected."""
    sel, decs = select_media("SW1", "SW2", 100.0)
    assert sel.media_type == "Cat6a UTP"
    assert sel.standard == "10GBASE-T"
    assert sel.propagation_delay_us == pytest.approx(0.5, rel=1e-2)


def test_mmf_boundary_101m():
    """At 101 m, OM4 MMF 10GBASE-SR is selected (copper exceeds 100 m)."""
    sel, decs = select_media("SW1", "SW2", 101.0)
    assert sel.media_type == "OM4 MMF"
    assert sel.standard == "10GBASE-SR"
    assert sel.wavelength_nm == 850


def test_mmf_boundary_400m():
    """At 400 m, OM4 MMF 10GBASE-SR is selected."""
    sel, decs = select_media("SW1", "SW2", 400.0)
    assert sel.media_type == "OM4 MMF"
    assert sel.standard == "10GBASE-SR"


def test_smf_boundary_401m():
    """At 401 m, OM4 modal bandwidth is exceeded; OS2 SMF is selected."""
    sel, decs = select_media("SW1", "SW2", 401.0)
    assert sel.media_type == "OS2 SMF"
    assert sel.transceiver in ("LR", "ER", "ZR")
    assert sel.margin_db >= 0


def test_optical_budget_10km():
    """At 10 km, LR reach is 10 km but LR optical margin is negative:
       Tx_min (-8.2) - Rx_sens (-14.4) = 6.2 dB
       Loss = 10*0.35 + 2.0 + 0.5 + 2.0 = 8.0 dB (Margin = -1.8 dB).
       Therefore ER is selected.
    """
    sel, decs = select_media("SiteA", "SiteB", 10000.0)
    assert sel.media_type == "OS2 SMF"
    assert sel.transceiver == "ER"
    assert sel.margin_db >= 0


def test_optical_budget_10_01km():
    """At 10.01 km, LR reach (10 km) is exceeded, selecting ER."""
    sel, decs = select_media("SiteA", "SiteB", 10010.0)
    assert sel.media_type == "OS2 SMF"
    assert sel.transceiver == "ER"


def test_optical_budget_35km():
    """At 35 km, ER budget (11.1 dB) is less than loss (14.45 dB).
       ZR is selected (Budget 24 dB, Loss 14.45 dB, Margin +9.55 dB).
    """
    sel, decs = select_media("HQ", "R2", 35000.0)
    assert sel.media_type == "OS2 SMF"
    assert sel.transceiver == "ZR"
    assert sel.margin_db == pytest.approx(9.55, abs=0.1)


def test_optical_budget_failure_80km():
    """At 80 km, ZR has reach 80 km but loss is 28.0 dB vs 24 dB budget.
       Since margin is -4.0 dB, it raises OpticalBudgetError.
    """
    with pytest.raises(OpticalBudgetError) as exc_info:
        select_media("SiteA", "SiteB", 80000.0)
    assert "80.0 km" in str(exc_info.value)
    assert "amplification" in str(exc_info.value)


def test_wan_circuit_recommendation_81km():
    """Beyond 80 km (e.g. 81 km), system recommends Carrier WAN circuit secured with IPsec."""
    sel, decs = select_media("CityA", "CityB", 81000.0)
    assert sel.media_type == "Carrier WAN Circuit"
    assert sel.wan_circuit is True
    assert any("Recommend a carrier WAN circuit" in d.reason for d in decs)


def test_copper_requested_over_100m_raises():
    """Requesting copper media beyond 100 m raises PhysicalDistanceViolationError."""
    with pytest.raises(PhysicalDistanceViolationError) as exc_info:
        select_media("SW1", "SW2", 120.0, media_request="copper")
    assert "exceeds the 100 m maximum" in str(exc_info.value)
    assert "IEEE 802.3an" in str(exc_info.value)


def test_metro_delay_calculation():
    """Metro profile checks propagation delay + equipment allowance < 5 ms."""
    sel, decs = select_media("HQ", "R1", 15000.0, profile="metro")
    # 15 km * 5 us/km = 75 us = 0.075 ms + 1.0 ms = 1.075 ms < 5 ms
    assert sel.propagation_delay_us == pytest.approx(75.0, abs=1.0)
    delay_decs = [d for d in decs if d.domain == "qos"]
    assert len(delay_decs) == 1
    assert "PASS" in delay_decs[0].choice
