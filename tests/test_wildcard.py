"""
test_wildcard.py — Test bitwise subnet mask and wildcard calculations
against Python's ipaddress module as an independent ground-truth oracle.
"""
import ipaddress
import pytest
from netarchitect.vlsm import (
    ip_to_int,
    int_to_ip,
    prefix_to_mask_int,
    mask_to_wildcard_int,
)


def test_all_33_prefixes_against_ipaddress_oracle():
    """Verify prefix lengths 0 through 32 against ipaddress netmask and hostmask."""
    for prefix_len in range(33):
        # Bitwise engine calculations
        mask_int = prefix_to_mask_int(prefix_len)
        wildcard_int = mask_to_wildcard_int(mask_int)
        mask_str = int_to_ip(mask_int)
        wildcard_str = int_to_ip(wildcard_int)

        # Oracle calculations using ipaddress
        oracle_net = ipaddress.IPv4Network(f"0.0.0.0/{prefix_len}")
        expected_mask = str(oracle_net.netmask)
        expected_wildcard = str(oracle_net.hostmask)

        assert mask_str == expected_mask, (
            f"Prefix /{prefix_len}: expected mask {expected_mask}, got {mask_str}"
        )
        assert wildcard_str == expected_wildcard, (
            f"Prefix /{prefix_len}: expected wildcard {expected_wildcard}, got {wildcard_str}"
        )


def test_ip_to_int_and_int_to_ip_roundtrip():
    """Verify bitwise serialization/deserialization for various IPv4 addresses."""
    test_ips = [
        "0.0.0.0",
        "10.0.0.1",
        "172.16.254.1",
        "192.168.1.254",
        "255.255.255.255",
        "10.100.128.5",
    ]
    for ip in test_ips:
        as_int = ip_to_int(ip)
        assert as_int == int(ipaddress.IPv4Address(ip))
        as_str = int_to_ip(as_int)
        assert as_str == ip


def test_wildcard_is_bitwise_inverse_of_mask():
    """Ensure mask ^ wildcard == 0xFFFFFFFF for all prefixes."""
    for plen in range(33):
        m = prefix_to_mask_int(plen)
        w = mask_to_wildcard_int(m)
        assert (m ^ w) == 0xFFFFFFFF
        assert (m & w) == 0
        assert (m | w) == 0xFFFFFFFF
