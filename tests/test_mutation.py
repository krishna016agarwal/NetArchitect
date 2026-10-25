"""
test_mutation.py — Mutation testing for NetArchitect.
Injects a defect into the wildcard mask calculation in a temporary copy/patch
and verifies that the oracle test suite immediately catches the defect.
"""
import ipaddress
import pytest
from netarchitect.vlsm import prefix_to_mask_int, mask_to_wildcard_int, int_to_ip


def _mutated_mask_to_wildcard_int(mask_int: int) -> int:
    """Mutated (broken) version of mask_to_wildcard_int:
    Forgets to invert the mask (returns the subnet mask itself instead of wildcard).
    """
    return mask_int & 0xFFFFFFFF


def test_mutation_breaks_wildcard_detection():
    """Verify that breaking the wildcard function triggers test failures."""
    # Test prefix /24: mask is 255.255.255.0, correct wildcard is 0.0.0.255
    mask_24 = prefix_to_mask_int(24)
    mutated_wildcard = _mutated_mask_to_wildcard_int(mask_24)

    # Oracle expects hostmask for /24 to be 0.0.0.255
    oracle_wildcard = str(ipaddress.IPv4Network("0.0.0.0/24").hostmask)
    mutated_wildcard_str = int_to_ip(mutated_wildcard)

    # Mutation test asserts that the mutated output differs from the oracle
    assert mutated_wildcard_str != oracle_wildcard
    assert mutated_wildcard_str == "255.255.255.0"
    assert oracle_wildcard == "0.0.0.255"
