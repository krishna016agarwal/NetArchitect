"""
media.py — L1 media engine for NetArchitect.
Selects cable type, fiber optic transceiver, and computes optical budget.
Does NOT import ipaddress.
"""
import math
from netarchitect.constants import (
    COPPER_MAX_DISTANCE_M, MMF_OM4_MAX_DISTANCE_M, MAX_OWNED_FIBER_KM,
    ATTENUATION_1310_DB_PER_KM, ATTENUATION_1550_DB_PER_KM,
    CONNECTOR_LOSS_DB, NUM_CONNECTORS, SPLICE_LOSS_DB, SAFETY_MARGIN_DB,
    TRANSCEIVERS, TRANSCEIVER_COST_ORDER, PROPAGATION_DELAY_US_PER_KM,
    METRO_MAX_ONE_WAY_DELAY_MS, EQUIPMENT_DELAY_ALLOWANCE_MS,
)
from netarchitect.models import MediaSelection, Decision
from netarchitect.errors import PhysicalDistanceViolationError, OpticalBudgetError


def _compute_optical_budget(transceiver_name: str, distance_km: float) -> dict:
    """Compute optical power budget for a given transceiver and distance.

    Budget = Tx_min - Rx_sens
    Loss = km * attenuation + NUM_CONNECTORS * CONNECTOR_LOSS + floor(km/2) * SPLICE_LOSS + SAFETY_MARGIN
    Margin = Budget - Loss
    """
    spec = TRANSCEIVERS[transceiver_name]
    budget = spec["tx_min_dbm"] - spec["rx_sens_dbm"]

    att_per_km = (ATTENUATION_1310_DB_PER_KM
                  if spec["wavelength_nm"] == 1310
                  else ATTENUATION_1550_DB_PER_KM)

    fiber_loss = distance_km * att_per_km
    connector_loss = NUM_CONNECTORS * CONNECTOR_LOSS_DB
    splice_loss = math.floor(distance_km / 2) * SPLICE_LOSS_DB
    total_loss = fiber_loss + connector_loss + splice_loss + SAFETY_MARGIN_DB
    margin = budget - total_loss

    return {
        "budget_db": round(budget, 2),
        "fiber_loss_db": round(fiber_loss, 2),
        "connector_loss_db": round(connector_loss, 2),
        "splice_loss_db": round(splice_loss, 2),
        "safety_db": SAFETY_MARGIN_DB,
        "total_loss_db": round(total_loss, 2),
        "margin_db": round(margin, 2),
    }


def select_media(link_a: str, link_b: str, distance_m: float,
                 media_request: str = None, profile: str = "campus") -> tuple:
    """Select L1 media for a link.

    Returns (MediaSelection, list[Decision]).
    """
    decisions = []
    distance_km = distance_m / 1000.0
    link_name = f"{link_a}-{link_b}"

    # ── Copper requested but distance > 100 m ──
    if media_request == "copper" and distance_m > COPPER_MAX_DISTANCE_M:
        raise PhysicalDistanceViolationError(link_name, distance_m)

    # ── <= 100 m: Cat6a copper ──
    if distance_m <= COPPER_MAX_DISTANCE_M:
        prop_delay = distance_km * PROPAGATION_DELAY_US_PER_KM
        decisions.append(Decision(
            rule_id="MEDIA-001",
            domain="media",
            subject=f"Link {link_name} ({distance_m} m)",
            choice="Cat6a UTP, 10GBASE-T",
            reason=(
                f"Selected Cat6a UTP (10GBASE-T) because link {link_name} "
                f"distance ({distance_m} m) is within the {COPPER_MAX_DISTANCE_M} m "
                f"maximum channel length for copper cabling (IEEE 802.3an)."
            ),
            references=["IEEE 802.3an"],
        ))
        return MediaSelection(
            link_a=link_a, link_b=link_b, distance_m=distance_m,
            media_type="Cat6a UTP", standard="10GBASE-T",
            propagation_delay_us=round(prop_delay, 2),
        ), decisions

    # ── 101-400 m: OM4 MMF ──
    if distance_m <= MMF_OM4_MAX_DISTANCE_M:
        prop_delay = distance_km * PROPAGATION_DELAY_US_PER_KM
        decisions.append(Decision(
            rule_id="MEDIA-002",
            domain="media",
            subject=f"Link {link_name} ({distance_m} m)",
            choice="OM4 MMF, 10GBASE-SR",
            reason=(
                f"Selected OM4 Multi-Mode Fiber (10GBASE-SR, 850 nm) because link "
                f"{link_name} distance ({distance_m} m) exceeds the "
                f"{COPPER_MAX_DISTANCE_M} m copper limit (IEEE 802.3an) but is within "
                f"the {MMF_OM4_MAX_DISTANCE_M} m modal bandwidth limit of OM4 MMF "
                f"(IEEE 802.3ae). Note: modal dispersion limits OM4 MMF to "
                f"{MMF_OM4_MAX_DISTANCE_M} m at 10 Gbps."
            ),
            references=["IEEE 802.3ae"],
        ))
        return MediaSelection(
            link_a=link_a, link_b=link_b, distance_m=distance_m,
            media_type="OM4 MMF", standard="10GBASE-SR",
            wavelength_nm=850,
            propagation_delay_us=round(prop_delay, 2),
        ), decisions

    # ── > 80 km: Exceeds owned fiber limit -> Recommend carrier WAN circuit ──
    if distance_km > MAX_OWNED_FIBER_KM:
        prop_delay = distance_km * PROPAGATION_DELAY_US_PER_KM
        decisions.append(Decision(
            rule_id="MEDIA-003",
            domain="media",
            subject=f"Link {link_name} ({distance_km} km)",
            choice="Carrier WAN circuit (IPsec secured)",
            reason=(
                f"Selected Carrier WAN circuit because link {link_name} distance "
                f"({distance_km} km) exceeds the {MAX_OWNED_FIBER_KM} km limit for owned "
                f"fiber. Recommend a carrier WAN circuit secured with IPsec instead of "
                f"owned fiber."
            ),
            references=["RFC 4301"],
        ))
        return MediaSelection(
            link_a=link_a, link_b=link_b, distance_m=distance_m,
            media_type="Carrier WAN Circuit",
            standard="Carrier Ethernet / IPsec",
            propagation_delay_us=round(prop_delay, 2),
            wan_circuit=True,
        ), decisions

    # ── > 400 m to 80 km: OS2 SMF — select cheapest transceiver with margin >= 0 ──
    prop_delay = distance_km * PROPAGATION_DELAY_US_PER_KM

    best_xcvr = None
    best_budget = None
    best_margin = -999.0

    for xcvr_name in TRANSCEIVER_COST_ORDER:
        spec = TRANSCEIVERS[xcvr_name]
        if spec["reach_km"] < distance_km:
            budget_info = _compute_optical_budget(xcvr_name, distance_km)
            if budget_info["margin_db"] > best_margin:
                best_margin = budget_info["margin_db"]
            continue
        budget_info = _compute_optical_budget(xcvr_name, distance_km)
        if budget_info["margin_db"] >= 0:
            best_xcvr = xcvr_name
            best_budget = budget_info
            break
        if budget_info["margin_db"] > best_margin:
            best_margin = budget_info["margin_db"]
            best_xcvr = xcvr_name
            best_budget = budget_info

    if best_xcvr is None or best_budget is None or best_budget["margin_db"] < 0:
        raise OpticalBudgetError(link_name, distance_km, best_margin)

    spec = TRANSCEIVERS[best_xcvr]
    reason_parts = [
        f"Selected OS2 Single-Mode Fiber ({spec['description']}) because link "
        f"{link_name} distance ({distance_m} m = {distance_km} km) exceeds the "
        f"{MMF_OM4_MAX_DISTANCE_M} m limit of OM4 MMF.",
        f"Optical budget: {best_budget['budget_db']} dB "
        f"(Tx_min {spec['tx_min_dbm']} dBm - Rx_sens {spec['rx_sens_dbm']} dBm).",
        f"Total loss: {best_budget['total_loss_db']} dB "
        f"(fiber {best_budget['fiber_loss_db']} + connectors "
        f"{best_budget['connector_loss_db']} + splices "
        f"{best_budget['splice_loss_db']} + safety {best_budget['safety_db']}).",
        f"Margin: {best_budget['margin_db']} dB.",
    ]

    decisions.append(Decision(
        rule_id="MEDIA-003",
        domain="media",
        subject=f"Link {link_name} ({distance_m} m)",
        choice=f"OS2 SMF, {spec['description']}",
        reason=" ".join(reason_parts),
        references=[spec["standard"]],
    ))

    # Metro delay check
    if profile == "metro":
        one_way_ms = prop_delay / 1000.0 + EQUIPMENT_DELAY_ALLOWANCE_MS
        meets_target = one_way_ms < METRO_MAX_ONE_WAY_DELAY_MS
        decisions.append(Decision(
            rule_id="MEDIA-004",
            domain="qos",
            subject=f"Link {link_name} delay",
            choice=f"{'PASS' if meets_target else 'FAIL'}: {one_way_ms:.2f} ms",
            reason=(
                f"One-way delay for link {link_name}: propagation "
                f"{prop_delay:.1f} µs ({distance_km} km x "
                f"{PROPAGATION_DELAY_US_PER_KM} µs/km) = "
                f"{prop_delay / 1000.0:.2f} ms + {EQUIPMENT_DELAY_ALLOWANCE_MS} ms "
                f"equipment allowance = {one_way_ms:.2f} ms. "
                f"Target < {METRO_MAX_ONE_WAY_DELAY_MS} ms: "
                f"{'MET' if meets_target else 'NOT MET'}."
            ),
            references=["IEEE 802.3ae"],
        ))

    return MediaSelection(
        link_a=link_a, link_b=link_b, distance_m=distance_m,
        media_type="OS2 SMF", standard=spec["description"],
        transceiver=best_xcvr,
        wavelength_nm=spec["wavelength_nm"],
        budget_db=best_budget["budget_db"],
        loss_db=best_budget["total_loss_db"],
        margin_db=best_budget["margin_db"],
        propagation_delay_us=round(prop_delay, 2),
        wan_circuit=False,
    ), decisions
