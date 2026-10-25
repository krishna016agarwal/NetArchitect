"""
test_cli.py — CLI behavior and exit code verification.
Tests:
  - Exit 0 on valid preset run
  - Exit 2 on expected domain errors (distance violation, invalid parameters, exhaustion)
  - Exit 1 on invalid CLI usage
"""
import sys
import subprocess
import json
import pytest


def test_cli_help():
    """CLI prints help when invoked without arguments."""
    res = subprocess.run([sys.executable, "-m", "netarchitect"], capture_output=True, text=True)
    assert res.returncode == 1
    assert "usage:" in res.stdout.lower() or "netarchitect" in res.stderr.lower() or "netarchitect" in res.stdout.lower()


def test_cli_preset_campus_success(tmp_path):
    """Running campus preset exits with code 0."""
    out_dir = str(tmp_path / "out")
    res = subprocess.run(
        [sys.executable, "-m", "netarchitect", "run", "--preset", "campus", "--out", out_dir],
        capture_output=True, text=True
    )
    assert res.returncode == 0
    assert "CAMPUS profile" in res.stdout


def test_cli_invalid_preset_error():
    """Non-existent preset raises argparse error (exit code 2)."""
    res = subprocess.run(
        [sys.executable, "-m", "netarchitect", "run", "--preset", "nonexistent"],
        capture_output=True, text=True
    )
    assert res.returncode == 2


def test_cli_physical_distance_violation_exits_2(tmp_path):
    """Scenario requesting copper over 100m catches PhysicalDistanceViolationError and exits code 2."""
    bad_scenario = {
        "profile": "campus",
        "root_prefix": "10.10.0.0/16",
        "resiliency": False,
        "sites": [
            {"name": "Site1", "devices": [{"name": "SW1", "type": "l3_switch"}]},
            {"name": "Site2", "devices": [{"name": "SW2", "type": "l3_switch"}]},
        ],
        "links": [
            {"a": "Site1", "b": "Site2", "distance_m": 150, "media_request": "copper"}
        ],
        "vlans": [
            {"id": 10, "name": "VLAN10", "hosts": 50, "site": "Site1"}
        ]
    }
    json_path = str(tmp_path / "bad_distance.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(bad_scenario, f)

    res = subprocess.run(
        [sys.executable, "-m", "netarchitect", "run", "--custom", json_path],
        capture_output=True, text=True
    )
    assert res.returncode == 2
    assert "ERROR:" in res.stderr
    assert "exceeds the 100 m maximum" in res.stderr
    assert "Traceback" not in res.stderr  # Clean error message without stack trace


def test_cli_address_space_exhaustion_exits_2(tmp_path):
    """Scenario exhausting address space exits code 2 cleanly."""
    exhaust_scenario = {
        "profile": "campus",
        "root_prefix": "192.168.1.0/24",
        "resiliency": False,
        "sites": [
            {"name": "Site1", "devices": [{"name": "SW1", "type": "l3_switch"}]}
        ],
        "links": [],
        "vlans": [
            {"id": 10, "name": "VLAN10", "hosts": 200, "site": "Site1"},
            {"id": 20, "name": "VLAN20", "hosts": 200, "site": "Site1"}
        ]
    }
    json_path = str(tmp_path / "exhaust.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(exhaust_scenario, f)

    res = subprocess.run(
        [sys.executable, "-m", "netarchitect", "run", "--custom", json_path],
        capture_output=True, text=True
    )
    assert res.returncode == 2
    assert "ERROR: Address space exhausted" in res.stderr
    assert "Traceback" not in res.stderr
