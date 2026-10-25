"""
exporter.py — File exporter for NetArchitect output.
"""
import os
import json
from netarchitect.explain import build_rationale, build_allocation_csv, build_summary_json_data


def export_all(out_dir: str, scenario, device_configs: dict,
               decisions: list, allocations: list, media_results: list):
    """Export all output files for a scenario.

    Creates:
        out/<profile>/
            <profile>_full_config.txt
            configs/<device>.txt
            rationale.md
            allocation.csv
            summary.json
    """
    profile = scenario.profile
    profile_dir = os.path.join(out_dir, profile)
    configs_dir = os.path.join(profile_dir, "configs")
    os.makedirs(configs_dir, exist_ok=True)

    # Full config (all devices)
    full_config_lines = []
    for dev_name, config_text in device_configs.items():
        full_config_lines.append(config_text)
        full_config_lines.append("")

    full_config_path = os.path.join(profile_dir, f"{profile}_full_config.txt")
    with open(full_config_path, "w", encoding="utf-8") as f:
        f.write("\n".join(full_config_lines))

    # Per-device configs
    for dev_name, config_text in device_configs.items():
        dev_path = os.path.join(configs_dir, f"{dev_name}.txt")
        with open(dev_path, "w", encoding="utf-8") as f:
            f.write(config_text)

    # Rationale
    rationale = build_rationale(decisions, allocations)
    rationale_path = os.path.join(profile_dir, "rationale.md")
    with open(rationale_path, "w", encoding="utf-8") as f:
        f.write(rationale)

    # Allocation CSV
    csv_content = build_allocation_csv(allocations)
    csv_path = os.path.join(profile_dir, "allocation.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(csv_content)

    # Summary JSON
    summary_data = build_summary_json_data(scenario, decisions, allocations, media_results)
    summary_path = os.path.join(profile_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)

    return profile_dir
