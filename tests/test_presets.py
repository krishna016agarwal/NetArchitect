"""
test_presets.py — End-to-end integration tests for all 3 built-in presets:
  - campus (1600 hosts, 3 sites, single-area OSPF)
  - metro (550 hosts, 3 sites, QoS < 5ms, EVPL subinterfaces)
  - wan (2000 IoT + servers/mgmt, 4 cities, hierarchical VLSM, OSPF + eBGP + IPsec)
"""
import os
import ipaddress
import pytest
from netarchitect.inputs import load_preset
from netarchitect.cli import run_scenario


@pytest.mark.parametrize("preset_name,expected_dev_count,min_alloc_count", [
    ("campus", 3, 11),
    ("metro", 3, 7),
    ("wan", 4, 15),
])
def test_preset_end_to_end_and_no_overlaps(tmp_path, preset_name, expected_dev_count, min_alloc_count):
    """Run each preset end-to-end through the pipeline.
    Verify:
      1. Pipeline exits with 0.
      2. All output files are generated.
      3. No allocated subnets overlap.
      4. Every allocated subnet is inside the root prefix.
    """
    scenario = load_preset(preset_name)
    out_dir = str(tmp_path / "out")

    exit_code = run_scenario(scenario, out_dir)
    assert exit_code == 0

    profile_dir = os.path.join(out_dir, preset_name)
    assert os.path.isdir(profile_dir)

    # Check output files
    assert os.path.isfile(os.path.join(profile_dir, f"{preset_name}_full_config.txt"))
    assert os.path.isfile(os.path.join(profile_dir, "rationale.md"))
    assert os.path.isfile(os.path.join(profile_dir, "allocation.csv"))
    assert os.path.isfile(os.path.join(profile_dir, "summary.json"))

    configs_dir = os.path.join(profile_dir, "configs")
    assert os.path.isdir(configs_dir)
    dev_files = os.listdir(configs_dir)
    assert len(dev_files) == expected_dev_count

    # Check CSV allocations for overlaps
    csv_file = os.path.join(profile_dir, "allocation.csv")
    with open(csv_file, "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]  # skip header

    subnets = []
    root_net = ipaddress.IPv4Network(scenario.root_prefix)
    for line in lines:
        parts = line.strip().split(",")
        if len(parts) >= 4:
            net_str = parts[2]
            plen_str = parts[3]
            subnet = ipaddress.IPv4Network(f"{net_str}/{plen_str}")
            subnets.append(subnet)
            assert subnet.subnet_of(root_net), f"Subnet {subnet} not inside root {root_net}"

    assert len(subnets) >= min_alloc_count

    # Check pairwise non-overlap
    for i in range(len(subnets)):
        for j in range(i + 1, len(subnets)):
            assert not subnets[i].overlaps(subnets[j]), (
                f"Overlap detected in {preset_name}: {subnets[i]} and {subnets[j]}"
            )
